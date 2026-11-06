"""Compile and exercise the independent launcher without running a game."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "engine/cinnabar.exe", "engine/cinnabar-updater.exe", "engine/bedrock-core.exe",
    "engine/bedrock-local-server.exe", "engine/cinnabar-cxb.exe", "engine/dxcompiler.dll",
    "engine/resources/prep-kit/bin/assetc.exe",
)


class BedrockLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cargo = shutil.which("cargo")
        if cargo is None:
            raise unittest.SkipTest("Cargo is unavailable; native launcher tests need the pinned Rust toolchain")
        cls.cargo = cargo
        cls.manifest = PROJECT / "bedrock/launcher/Cargo.toml"
        cls.environment = dict(os.environ)
        cls.target = PROJECT / ".cache/bedrock-launcher-tests"
        cls.environment["CARGO_TARGET_DIR"] = str(cls.target)
        cls.environment["CARGO_TERM_COLOR"] = "never"
        result = cls.cargo_command("build")
        if result.returncode:
            raise AssertionError("Bedrock launcher compilation failed:\n" + result.stdout + result.stderr)
        cls.executable = cls.target / "debug" / ("Herspers-Bedrock.exe" if os.name == "nt" else "Herspers-Bedrock")

    @classmethod
    def cargo_command(cls, command):
        return subprocess.run(
            [cls.cargo, "+1.95.0", command, "--locked", "--manifest-path", str(cls.manifest)],
            env=cls.environment, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=180,
        )

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herspers-bedrock-cli-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self):
        bundle = self.root / "bundle with spaces"
        bundle.mkdir()
        launcher = bundle / self.executable.name
        shutil.copy2(self.executable, launcher)
        files = {}
        for name in REQUIRED:
            path = bundle / name
            path.parent.mkdir(parents=True, exist_ok=True)
            content = ("fixture, never executed: " + name).encode()
            path.write_bytes(content)
            files[name] = hashlib.sha256(content).hexdigest()
        manifest = {
            "product_version": "0.3.0", "engine": "cinnabar", "engine_version": "0.1.31",
            "bedrock_version": "1.26.60", "wire_protocol": 2225,
            "in_app_resource_downloads": True, "game_assets_included": False, "files": files,
        }
        (bundle / "bedrock-client.json").write_text(json.dumps(manifest))
        return bundle, launcher, manifest

    def run_launcher(self, launcher, *arguments):
        environment = dict(self.environment)
        environment["LOCALAPPDATA"] = str(self.root / "unused player data")
        return subprocess.run([str(launcher), *arguments], env=environment,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)

    def test_native_unit_suite_executes(self):
        result = self.cargo_command("test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        count = re.search(r"running (\d+) tests", result.stdout)
        self.assertIsNotNone(count, result.stdout)
        self.assertGreater(int(count.group(1)), 0)
        self.assertIn("test result: ok", result.stdout)

    def test_help_and_product_version_need_no_engine_or_game_data(self):
        help_result = self.run_launcher(self.executable, "--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("in-app setup", help_result.stdout)
        self.assertIn("PolyForm Noncommercial", help_result.stdout)
        self.assertIn("No Java", help_result.stdout)
        version = self.run_launcher(self.executable, "--version")
        self.assertEqual(version.returncode, 0, version.stderr)
        self.assertEqual(version.stdout.strip(), "Herspers Bedrock 0.3.0")
        self.assertFalse((self.root / "unused player data").exists())

    def test_verify_install_hashes_payload_without_launch_or_user_data(self):
        _, launcher, _ = self.fixture()
        result = self.run_launcher(launcher, "--verify-install")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["bedrock_version"], "1.26.60")
        self.assertEqual(report["wire_protocol"], 2225)
        self.assertEqual(report["payload_file_count"], len(REQUIRED))
        self.assertTrue(report["payload_hashes_verified"])
        self.assertTrue(report["in_app_resource_downloads"])
        self.assertFalse(report["game_assets_included"])
        self.assertFalse(report["gameplay_tested"])
        self.assertFalse((self.root / "unused player data").exists())

    def test_corrupt_payload_fails_before_engine_launch(self):
        bundle, launcher, _ = self.fixture()
        (bundle / REQUIRED[0]).write_bytes(b"tampered")
        result = self.run_launcher(launcher, "--verify-install")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SHA-256", result.stderr)
        self.assertFalse((self.root / "unused player data").exists())

    def test_verify_reports_runtime_prerequisites_without_loading_them(self):
        bundle, launcher, manifest = self.fixture()
        manifest["required_vc_runtime_dlls"] = ["vcruntime140.dll"]
        metadata = bundle / "bedrock-client.json"
        metadata.write_text(json.dumps(manifest))
        result = self.run_launcher(launcher, "--verify-install")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["required_vc_runtime_dlls"], ["vcruntime140.dll"])
        self.assertFalse((self.root / "unused player data").exists())
        for invalid in [None, "vcruntime140.dll", ["../vcruntime140.dll"],
                        ["arbitrary.dll"], ["vcruntime140d.dll"],
                        ["vcruntime140.dll", "vcruntime140.dll"]]:
            with self.subTest(prerequisites=invalid):
                manifest["required_vc_runtime_dlls"] = invalid
                metadata.write_text(json.dumps(manifest))
                result = self.run_launcher(launcher, "--verify-install")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("runtime prerequisite", result.stderr)
                self.assertNotIn("panicked", result.stderr)

    def test_manifest_cannot_traverse_outside_engine(self):
        bundle, launcher, manifest = self.fixture()
        manifest["files"]["engine/../../outside.exe"] = "0" * 64
        (bundle / "bedrock-client.json").write_text(json.dumps(manifest))
        result = self.run_launcher(launcher, "--verify-install")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unsafe", result.stderr)

    def test_malformed_manifest_is_reported_without_a_panic(self):
        bundle, launcher, _ = self.fixture()
        (bundle / "bedrock-client.json").write_bytes(b"{not JSON")
        result = self.run_launcher(launcher, "--verify-install")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid engine manifest JSON", result.stderr)
        self.assertNotIn("panicked", result.stderr)


if __name__ == "__main__":
    unittest.main()
