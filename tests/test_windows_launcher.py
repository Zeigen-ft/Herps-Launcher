"""Compile and exercise the dependency-free launcher without player game data."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class WindowsLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("rustc")
        if compiler is None:
            raise unittest.SkipTest("Rust is not on PATH; native launcher tests require rustc")
        cls.temporary = tempfile.TemporaryDirectory(prefix="herspers-launcher-native-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        extension = ".exe" if os.name == "nt" else ""
        cls.executable = Path(cls.temporary.name) / ("launcher" + extension)
        cls.unit_tests = Path(cls.temporary.name) / ("launcher-unit-tests" + extension)
        source = PROJECT / "packaging/launcher_windows.rs"
        for output, options in [(cls.executable, []), (cls.unit_tests, ["--test"])]:
            result = subprocess.run(
                [compiler, "--edition=2021", "-D", "warnings", *options, str(source), "-o", str(output)],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode != 0:
                raise AssertionError("Native launcher compilation failed:\n" + result.stdout + result.stderr)

    def test_native_unit_suite_executes(self):
        result = subprocess.run([str(self.unit_tests)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        match = re.search(r"running (\d+) tests", result.stdout)
        self.assertIsNotNone(match, result.stdout)
        self.assertGreater(int(match.group(1)), 0)
        self.assertIn("test result: ok", result.stdout)

    def test_help_is_available_without_game_assets(self):
        result = subprocess.run([str(self.executable), "--help"], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--setup", result.stdout)
        self.assertIn("JDK 25", result.stdout)
        self.assertIn("%LOCALAPPDATA%", result.stdout)
        self.assertIn("--host-tailscale", result.stdout)
        self.assertIn("--join-tailscale", result.stdout)

    def test_project_version_is_available_without_game_assets(self):
        result = subprocess.run([str(self.executable), "--version"], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Herspers Minecraft 0.2.3")

    def test_private_helpers_reject_public_addresses_and_invalid_names_before_starting(self):
        for arguments in (["--join-tailscale", "8.8.8.8"],
                          ["--join-tailscale", "100.64.1.2", "--name", "name with spaces"],
                          ["--host-tailscale", "--port", "0"]):
            with self.subTest(arguments=arguments):
                result = subprocess.run([str(self.executable), *arguments], capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
