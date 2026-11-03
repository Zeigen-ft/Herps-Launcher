"""Resource-location regressions; owned files stand in for native helpers.

These tests exercise discovery on any host. They do not assert Windows/macOS
execution, and no placeholder executable or imported Java code is run.
"""
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from herps_launcher.core import Launcher, REVISION
from herps_launcher.javamods.adapter import (
    AnalysisReport, PortPackAdapter, bundled_port_pack_candidates,
)
from tools.make_javamods_fixtures import make_jar


class PortPackDiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps-discovery-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.launcher = Launcher(self.root / "support with spaces")
        self.adapter = PortPackAdapter(self.launcher)
        self.report = AnalysisReport("discovery", "default", self.root / "work")

    def helper(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"Owned helper placeholder; never executed")
        path.chmod(0o700)
        return path

    def process(self, *, frozen=False, system="Linux", executable=None, resources=None, env=None):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.dict(os.environ, env or {}, clear=True))
        stack.enter_context(patch("herps_launcher.javamods.adapter.sys.frozen", frozen, create=True))
        stack.enter_context(patch("herps_launcher.javamods.adapter.sys._MEIPASS", resources, create=True))
        stack.enter_context(patch("herps_launcher.javamods.adapter.sys.executable", str(executable or self.root / "python")))
        stack.enter_context(patch("herps_launcher.javamods.adapter.platform.system", return_value=system))
        return stack

    def test_windows_meipass_executable_with_spaces_records_actual_backend_hash(self):
        resources = self.root / "Installed Launcher/_internal"
        helper = self.helper(resources / "horizon-port-pack.exe")
        self.process(frozen=True, system="Windows", resources=resources,
                     executable=self.root / "Installed Launcher/Herps Launcher.exe")
        self.assertEqual(self.adapter._binary(self.report), helper)
        backend = self.report.raw_evidence["backend"]
        self.assertEqual(backend["sha256"], hashlib.sha256(helper.read_bytes()).hexdigest())
        self.assertEqual(backend["audited_engine_revision"], REVISION)
        self.assertIn("no version protocol", backend["note"])

    def test_windows_onedir_internal_directory_without_meipass_is_discovered(self):
        folder = self.root / "Installed Launcher"
        helper = self.helper(folder / "_internal/horizon-port-pack.exe")
        self.process(frozen=True, system="Windows", executable=folder / "Herps Launcher.exe")
        self.assertEqual(self.adapter._binary(self.report), helper)

    def test_windows_executable_sibling_uses_exe_name(self):
        folder = self.root / "Portable Launcher"
        helper = self.helper(folder / "horizon-port-pack.exe")
        self.helper(folder / "horizon-port-pack")
        self.process(frozen=True, system="Windows", executable=folder / "Herps Launcher.exe")
        self.assertEqual(self.adapter._binary(self.report), helper)

    def test_macos_application_frameworks_resources_and_macos_layouts(self):
        for directory in ("Frameworks", "Resources", "MacOS"):
            with self.subTest(directory=directory):
                contents = self.root / directory / "Herps Launcher.app/Contents"
                helper = self.helper(contents / directory / "horizon-port-pack")
                with self.process(frozen=True, system="Darwin", executable=contents / "MacOS/Herps Launcher"):
                    self.assertEqual(self.adapter._binary(self.report), helper)

    def test_meipass_resource_is_preferred_to_executable_relative_fallback(self):
        contents = self.root / "Herps Launcher.app/Contents"
        helper = self.helper(contents / "Frameworks/horizon-port-pack")
        self.helper(contents / "MacOS/horizon-port-pack")
        self.process(frozen=True, system="Darwin", resources=contents / "Frameworks",
                     executable=contents / "MacOS/Herps Launcher")
        self.assertEqual(self.adapter._binary(self.report), helper)

    def test_missing_bundled_helper_does_not_use_unrelated_cargo_or_path_binary(self):
        cargo = self.root / "developer-only-target"
        self.helper(cargo / "release/horizon-port-pack")
        unrelated = self.helper(self.root / "unrelated/bin/horizon-port-pack")
        self.process(frozen=True, env={"CARGO_TARGET_DIR": str(cargo), "PATH": str(unrelated.parent)})
        with patch("herps_launcher.javamods.adapter.shutil.which") as which:
            with self.assertRaisesRegex(ValueError, "Bundled horizon-port-pack executable is missing"):
                self.adapter._binary(self.report)
        which.assert_not_called()
        self.assertNotIn("backend", self.report.raw_evidence)

    def test_nonexecutable_bundle_helper_returns_actionable_error(self):
        helper = self.helper(self.root / "_internal/horizon-port-pack")
        self.process(frozen=True, resources=helper.parent)
        with patch("herps_launcher.javamods.adapter.os.access", return_value=False):
            with self.assertRaisesRegex(ValueError, "Cargo/Rust is not required"):
                self.adapter._binary(self.report)

    def test_explicit_selected_path_can_override_bundle_but_missing_selection_cannot_fall_back(self):
        resources = self.root / "_internal"
        bundled = self.helper(resources / "horizon-port-pack")
        selected = self.helper(self.root / "trusted custom tool")
        self.process(frozen=True, resources=resources)
        self.launcher.config["port_pack_binary"] = str(selected)
        self.assertEqual(self.adapter._binary(self.report), selected)
        selected.unlink()
        with self.assertRaisesRegex(ValueError, "Selected horizon-port-pack executable is missing"):
            self.adapter._binary(self.report)
        self.assertTrue(bundled.is_file())

    def test_source_environment_override_works_without_cargo_or_path(self):
        helper = self.helper(self.root / "custom build/horizon-port-pack")
        self.process(env={"HERPS_PORT_PACK": str(helper)})
        self.assertEqual(self.adapter._binary(self.report), helper)
        self.assertEqual(bundled_port_pack_candidates(), ())

    def test_source_cargo_release_and_debug_fallbacks(self):
        for mode in ("release", "debug"):
            with self.subTest(mode=mode):
                cargo = self.root / mode / "target with spaces"
                helper = self.helper(cargo / mode / "horizon-port-pack")
                with self.process(env={"CARGO_TARGET_DIR": str(cargo)}):
                    self.assertEqual(self.adapter._binary(self.report), helper)

    def test_source_path_fallback_uses_windows_executable_name(self):
        helper = self.helper(self.root / "bin/horizon-port-pack.exe")
        self.process(system="Windows")
        with patch("herps_launcher.javamods.adapter.shutil.which", return_value=str(helper)) as which:
            self.assertEqual(self.adapter._binary(self.report), helper)
        which.assert_called_once_with("horizon-port-pack.exe")

    def test_explicit_argument_precedes_saved_config_and_environment(self):
        explicit = self.helper(self.root / "explicit tool")
        configured = self.helper(self.root / "configured tool")
        environment = self.helper(self.root / "environment tool")
        self.launcher.config["port_pack_binary"] = str(configured)
        self.process(env={"HERPS_PORT_PACK": str(environment)})
        self.assertEqual(PortPackAdapter(self.launcher, executable=explicit)._binary(self.report), explicit)
        self.assertEqual(self.adapter._binary(self.report), configured)

    def test_missing_packaged_backend_keeps_imported_mod_unsupported_without_subprocess(self):
        jar = make_jar(self.root / "owned.jar")
        self.process(frozen=True)
        with patch("herps_launcher.javamods.adapter.subprocess.run") as run:
            result = self.adapter.check(jar)
        run.assert_not_called()
        self.assertEqual(result.status, "Unsupported")
        self.assertIn("insufficient_evidence", {d.code for d in result.diagnostics})
        diagnostics = [*result.diagnostics, *(d for mod in result.mods for d in mod.diagnostics)]
        self.assertTrue(any("Bundled horizon-port-pack" in d.message for d in diagnostics))
        self.assertFalse(result.commands)
        self.assertFalse(result.to_dict()["playable_verified"])
        self.assertIsNone(result.to_dict()["test_execution"])


if __name__ == "__main__":
    unittest.main()
