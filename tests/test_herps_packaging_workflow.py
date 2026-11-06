"""Exercise the native CI build hand-off without a native compiler or network."""
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from herps_launcher import core
from tools import package_herps


ROOT = Path(__file__).resolve().parents[1]


def backend_build_script():
    workflow = (ROOT / ".github/workflows/herps-launcher.yml").read_text(encoding="utf-8")
    step = re.search(
        r"      - name: Build pinned port-pack for the native runner\n"
        r"        shell: python\n        run: \|\n(.*?)(?=      - name:)",
        workflow, re.S)
    if not step:
        raise AssertionError("Native backend build step is missing")
    return textwrap.dedent(step.group(1))


class PackagingWorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps CI owned fixture ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.environment = self.root / "github-env"
        self.environment.write_text("EXISTING_SETTING=preserved\n", encoding="utf-8")
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        original_path = sys.path[:]
        self.addCleanup(setattr, sys, "path", original_path)

    def test_native_backend_handoff_preserves_literal_paths_and_build_evidence(self):
        for target, filename in (
            ("x86_64-pc-windows-msvc", "horizon-port-pack.exe"),
            ("aarch64-apple-darwin", "horizon-port-pack"),
            ("x86_64-apple-darwin", "horizon-port-pack"),
        ):
            with self.subTest(target=target):
                binary = self.root / "target cache with spaces" / target / filename
                evidence = {"target": target, "sha256": "a" * 64}
                with patch.object(core, "target", return_value=target), \
                     patch.object(package_herps, "build_port_pack", return_value=(binary, evidence)) as build, \
                     patch.dict(os.environ, {"GITHUB_ENV": str(self.environment)}):
                    exec(compile(backend_build_script(), "native-ci-backend-step", "exec"), {})
                build.assert_called_once_with(target)
                self.assertIn(f"HERPS_TEST_PORT_PACK={binary}\n", self.environment.read_text(encoding="utf-8"))
                self.assertTrue(self.environment.read_text(encoding="utf-8").startswith("EXISTING_SETTING=preserved\n"))
                self.assertEqual(json.loads((self.root / "herps-port-pack-build.json").read_text(encoding="utf-8")), evidence)

    def test_failed_native_backend_build_cannot_export_a_successful_handoff(self):
        with patch.object(core, "target", return_value="x86_64-pc-windows-msvc"), \
             patch.object(package_herps, "build_port_pack", side_effect=RuntimeError("owned build failure")), \
             patch.dict(os.environ, {"GITHUB_ENV": str(self.environment)}):
            with self.assertRaisesRegex(RuntimeError, "owned build failure"):
                exec(compile(backend_build_script(), "native-ci-backend-step", "exec"), {})
        self.assertEqual(self.environment.read_text(encoding="utf-8"), "EXISTING_SETTING=preserved\n")
        self.assertFalse((self.root / "herps-port-pack-build.json").exists())


if __name__ == "__main__":
    unittest.main()
