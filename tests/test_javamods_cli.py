"""Headless command regressions with local generated archives and saved evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from herps_launcher.core import Launcher
from herps_launcher.javamods.adapter import PortPackAdapter
from tools.make_javamods_fixtures import make_jar


PROJECT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ["HERPS_TEST_PORT_PACK"]) if os.environ.get("HERPS_TEST_PORT_PACK") else None


class CliHelpers:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="herps-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.support = self.root / "support with spaces"
        self.launcher = Launcher(self.support)
        self.jar = make_jar(self.root / "owned.jar")

    def command(self, command, *arguments, module="herps_launcher", binary=False):
        args = [sys.executable, "-m", module, command, "--support-dir", str(self.support)]
        if binary:
            args += ["--port-pack", str(BINARY)]
        return subprocess.run([*args, *map(str, arguments)], cwd=PROJECT,
                              capture_output=True, text=True, timeout=60)

    def parse(self, process, expected_exit):
        self.assertEqual(process.returncode, expected_exit, process.stdout + process.stderr)
        return json.loads(process.stdout)

    def unsupported_report(self):
        result = PortPackAdapter(self.launcher, executable=self.root / "missing-tool").check(self.jar)
        return result.workspace / "report.json"


class CliTests(CliHelpers, unittest.TestCase):
    def test_both_module_entrypoints_document_all_four_commands(self):
        for module in ("herps_launcher", "herps_launcher.javamods"):
            with self.subTest(module=module):
                process = subprocess.run([sys.executable, "-m", module, "--help"], cwd=PROJECT,
                                         capture_output=True, text=True, timeout=30)
                self.assertEqual(process.returncode, 0, process.stderr)
                for command in ("check", "analyze-pack", "port", "export-report"):
                    self.assertIn(command, process.stdout)

    def test_cli_dispatch_never_imports_qt_or_the_gui(self):
        script = '''
import builtins, runpy, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith("PySide6") or name == "herps_launcher.app":
        raise AssertionError("Headless command imported Qt/GUI")
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
sys.argv = ["herps_launcher", "check", "--support-dir", sys.argv[1], "absent.jar"]
runpy.run_module("herps_launcher", run_name="__main__")
'''
        process = subprocess.run([sys.executable, "-c", script, str(self.support)], cwd=PROJECT,
                                 capture_output=True, text=True, timeout=30)
        result = self.parse(process, 1)
        self.assertEqual(result["status"], "Unsupported")
        self.assertNotIn("Headless command imported", process.stderr)

    def test_missing_input_is_a_json_unsupported_result(self):
        result = self.parse(self.command("check", self.root / "absent.jar"), 1)
        self.assertEqual(result["status"], "Unsupported")
        self.assertIsNone(result["test_execution"])
        self.assertFalse(result["java_bridge_available"])
        self.assertIn("insufficient_evidence", {d["code"] for d in result["diagnostics"]})

    def test_nonpositive_timeout_is_a_structured_cli_error(self):
        result = self.parse(self.command("check", self.jar, "--timeout", "0"), 1)
        self.assertEqual(result["status"], "Unsupported")
        self.assertIn("Timeout", result["diagnostics"][0]["message"])

    def test_explicit_profile_does_not_change_saved_selection(self):
        self.launcher.add_profile("audit")
        self.launcher.config["profile"] = "default"
        self.launcher.save()
        settings_before = self.launcher.config_file.read_bytes()
        result = self.parse(self.command("check", self.jar, "--profile", "audit", "--port-pack", self.root / "missing-tool"), 1)
        self.assertEqual(result["profile"], "audit")
        self.assertTrue(Path(result["workspace"]).is_relative_to(self.launcher.state / "profiles/audit"))
        self.assertEqual(self.launcher.config_file.read_bytes(), settings_before)

    def test_unknown_profile_is_a_json_cli_error(self):
        result = self.parse(self.command("check", self.jar, "--profile", "unknown"), 1)
        self.assertIn("existing launcher profile", result["diagnostics"][0]["message"])

    def test_export_rejects_report_from_another_profile(self):
        report = self.unsupported_report()
        self.launcher.add_profile("separate")
        output = self.root / "outside.json"
        result = self.parse(self.command("export-report", report, output, "--profile", "separate"), 1)
        self.assertEqual(result["status"], "Unsupported")
        self.assertFalse(output.exists())

    def test_export_rejects_malformed_rows_as_json_cli_errors(self):
        report = self.unsupported_report()
        data = json.loads(report.read_text())
        data["mods"] = ["not a report row"]
        report.write_text(json.dumps(data))
        output = self.root / "malformed.json"
        result = self.parse(self.command("export-report", report, output), 1)
        self.assertEqual(result["status"], "Unsupported")
        self.assertFalse(output.exists())

    def test_export_rejects_duplicate_and_nonfinite_json_evidence(self):
        report = self.unsupported_report()
        data = json.loads(report.read_text())
        payloads = ['{"schema":1,' + json.dumps(data)[1:], json.dumps({**data, "created_at": float("nan")})]
        for index, payload in enumerate(payloads):
            with self.subTest(index=index):
                report.write_text(payload)
                output = self.root / f"invalid-{index}.json"
                result = self.parse(self.command("export-report", report, output), 1)
                self.assertEqual(result["status"], "Unsupported")
                self.assertFalse(output.exists())


@unittest.skipUnless(BINARY is not None and BINARY.is_file(),
                     "Set HERPS_TEST_PORT_PACK to the pinned executable for command integration")
class RealCliTests(CliHelpers, unittest.TestCase):
    def test_actual_check_and_both_report_export_formats(self):
        checked = self.parse(self.command("check", self.jar, binary=True), 0)
        self.assertEqual(checked["status"], "Requires porting")
        self.assertEqual(checked["mods"][0]["raw_evidence"]["check"]["verdict"], "works")
        report = Path(checked["workspace"]) / "report.json"
        for format in ("json", "text"):
            with self.subTest(format=format):
                output = self.root / f"export.{format}"
                self.parse(self.command("export-report", report, output, "--format", format), 0)
                self.assertTrue(output.is_file())
                if format == "json":
                    exported = json.loads(output.read_text())
                    self.assertEqual(exported["status"], "Requires porting")
                    self.assertFalse(exported["java_bridge_available"])
                    self.assertFalse(exported["playable_verified"])
                    self.assertIsNone(exported["test_execution"])
                else:
                    self.assertIn("Requires porting", output.read_text())
                    self.assertIn("Raw evidence", output.read_text())

    def test_actual_false_positive_works_cli_retains_raw_but_returns_unsupported(self):
        jar = make_jar(self.root / "missing-dependency.jar", depends={"missinglib": ">=2"})
        result = self.parse(self.command("check", jar, binary=True), 1)
        mod = result["mods"][0]
        self.assertEqual(result["status"], "Unsupported")
        self.assertEqual(mod["status"], "Unsupported")
        self.assertEqual(mod["raw_evidence"]["check"]["verdict"], "works")
        self.assertIn("missing_dependency", {d["code"] for d in mod["diagnostics"]})
        self.assertIn("insufficient_evidence", {d["code"] for d in mod["diagnostics"]})
        self.assertIsNone(result["test_execution"])

    def test_actual_analyze_pack_and_local_jar_port_commands(self):
        instance = self.root / "instance"
        make_jar(instance / "mods/owned.jar")
        analyzed = self.parse(self.command("analyze-pack", instance, binary=True), 0)
        self.assertEqual(analyzed["operation"], "analyze-pack")
        self.assertEqual(len(analyzed["mods"]), 1)
        ported = self.parse(self.command("port", self.jar, binary=True), 0)
        self.assertEqual(ported["operation"], "port")
        self.assertEqual(ported["status"], "Requires porting")
        self.assertTrue(Path(ported["mods"][0]["port_path"]).is_dir())
        self.assertIsNone(ported["test_execution"])
        self.assertFalse(ported["playable_verified"])

    def test_actual_package_module_executes_a_headless_check(self):
        result = self.parse(self.command("check", self.jar, module="herps_launcher.javamods", binary=True), 0)
        self.assertEqual(result["status"], "Requires porting")

    def test_export_demotes_forged_native_tested_and_missing_check_claims(self):
        checked = self.parse(self.command("check", self.jar, binary=True), 0)
        report = Path(checked["workspace"]) / "report.json"
        baseline = json.loads(report.read_text())
        for claimed in ("Native compatibility", "Tested successfully", "missing-check"):
            with self.subTest(claimed=claimed):
                data = json.loads(json.dumps(baseline))
                if claimed == "missing-check":
                    data["mods"][0]["raw_evidence"].pop("check")
                else:
                    data["status"] = claimed
                    data["mods"][0]["status"] = claimed
                    data["mods"][0]["test_execution"] = {"status": "passed", "exit_code": 0}
                data["java_bridge_available"] = True
                data["playable_verified"] = True
                report.write_text(json.dumps(data))
                output = self.root / f"demoted-{claimed}.json"
                self.parse(self.command("export-report", report, output), 0)
                exported = json.loads(output.read_text())
                self.assertEqual(exported["status"], "Unsupported")
                self.assertEqual(exported["mods"][0]["status"], "Unsupported")
                self.assertIn("insufficient_evidence", {d["code"] for d in exported["mods"][0]["diagnostics"]})
                self.assertIsNone(exported["test_execution"])
                self.assertIsNone(exported["mods"][0]["test_execution"])
                self.assertFalse(exported["java_bridge_available"])
                self.assertFalse(exported["playable_verified"])

    def test_export_revalidates_dependencies_after_diagnostics_and_status_are_forged(self):
        jar = make_jar(self.root / "requires-missing.jar", depends={"missinglib": ">=2"})
        checked = self.parse(self.command("check", jar, binary=True), 1)
        self.assertEqual(checked["mods"][0]["raw_evidence"]["check"]["verdict"], "works")
        report = Path(checked["workspace"]) / "report.json"
        data = json.loads(report.read_text())
        data["status"] = "Requires porting"
        data["diagnostics"] = []
        for row in data["mods"]:
            row["status"] = "Requires porting"
            row["diagnostics"] = []
            row["metadata"]["diagnostics"] = []
            # Forge the lossy saved metadata too. The retained JAR snapshot
            # remains the authority for the required missinglib dependency.
            row["metadata"]["required_dependencies"] = {"minecraft": "26.3"}
        report.write_text(json.dumps(data))
        output = self.root / "dependency-revalidated.json"
        self.parse(self.command("export-report", report, output), 0)
        exported = json.loads(output.read_text())
        self.assertEqual(exported["status"], "Unsupported")
        self.assertEqual(exported["mods"][0]["status"], "Unsupported")
        self.assertIn("insufficient_evidence", {d["code"] for d in exported["mods"][0]["diagnostics"]})
        self.assertIsNone(exported["test_execution"])

    def test_export_rejects_changed_or_missing_input_snapshot_as_insufficient(self):
        for changed in (True, False):
            with self.subTest(changed=changed):
                checked = self.parse(self.command("check", self.jar, binary=True), 0)
                report = Path(checked["workspace"]) / "report.json"
                snapshot = Path(checked["mods"][0]["raw_evidence"]["snapshot_path"])
                self.assertTrue(snapshot.is_file())
                if changed:
                    snapshot.write_bytes(snapshot.read_bytes() + b"owned mutation after analysis")
                else:
                    snapshot.unlink()
                output = self.root / f"snapshot-revalidated-{changed}.json"
                self.parse(self.command("export-report", report, output), 0)
                exported = json.loads(output.read_text())
                self.assertEqual(exported["status"], "Unsupported")
                self.assertEqual(exported["mods"][0]["status"], "Unsupported")
                self.assertIn("insufficient_evidence", {d["code"] for d in exported["mods"][0]["diagnostics"]})
                self.assertIsNone(exported["mods"][0]["test_execution"])


if __name__ == "__main__":
    unittest.main()
