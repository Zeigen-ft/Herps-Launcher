"""Owned metadata fixtures exercise frozen-helper smoke without claiming native OS testing."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from herps_launcher.core import Launcher, REVISION, digest, pairs

SPEC = importlib.util.spec_from_file_location(
    "herps_entry", Path(__file__).resolve().parents[1] / "packaging/herps_entry.py")
entry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entry)
BINARY = Path(os.environ["HERPS_TEST_PORT_PACK"]) if os.environ.get("HERPS_TEST_PORT_PACK") else None


class BundledEntrySmokeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps entry with spaces ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bundle = self.root / "Herps Launcher" / "_internal"
        self.bundle.mkdir(parents=True)
        self.launcher = Launcher(self.root / "support")

    def test_source_smoke_cannot_claim_bundled_execution(self):
        evidence = {}
        with patch.object(entry.sys, "frozen", False, create=True):
            with self.assertRaisesRegex(ValueError, "requires a frozen"):
                entry.port_pack_smoke(self.launcher, self.root, evidence)
        self.assertEqual(evidence, {"status": "failed", "bundled": False})

    def test_missing_bundled_helper_fails_before_a_success_claim(self):
        evidence = {}
        with patch.object(entry.sys, "frozen", True, create=True), \
                patch.object(entry.sys, "_MEIPASS", str(self.bundle), create=True), \
                patch.object(entry.sys, "executable", str(self.bundle.parent / "Herps Launcher")), \
                patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "[Mm]issing|missing"):
                entry.port_pack_smoke(self.launcher, self.root, evidence)
        self.assertEqual(evidence["status"], "failed")
        self.assertFalse(evidence["bundled"])

    def test_missing_java_helper_leaves_existing_mods_shaders_and_saves_functional(self):
        world = self.launcher.game / "saves/Existing/level.dat"
        world.parent.mkdir(parents=True)
        world.write_bytes(b"owned existing save sentinel")
        packages = {
            "owned.hmod": {"horizon-mod.toml": 'id="owned_runtime"\nname="Owned"\nversion="1"\napi="0.1"\n',
                           "mod.wasm": b"\0asm\x0d\0\x01\0"},
            "owned.hnmod": {"horizon-native.json": json.dumps({"schema": 1, "id": "owned_native",
                "version": "1", "game": "26.3", "horizon": REVISION, "mixins": "b" * 40}),
                "mixins/owned_native/horizon-mixin.toml": f'[mod]\nid="owned_native"\nversion="1"\n[compatibility]\nhorizon_revision="{REVISION}"\n',
                "mixins/owned_native/hook.rs": "// owned passive source fixture\n"},
            "owned.hshader": {"shaders/final.fsh": "// owned passive shader fixture\n"},
        }
        with patch.object(entry.sys, "frozen", True, create=True), \
                patch.object(entry.sys, "_MEIPASS", str(self.bundle), create=True), \
                patch.object(entry.sys, "executable", str(self.bundle.parent / "Herps Launcher")), \
                patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                entry.port_pack_smoke(self.launcher, self.root, {})
            for name, files in packages.items():
                path = self.root / name
                with zipfile.ZipFile(path, "w") as archive:
                    for relative, contents in files.items():
                        archive.writestr(relative, contents)
                if path.suffix == ".hshader":
                    self.launcher.install_shader(path)
                else:
                    self.launcher.install_mod(path)
            for mod in self.launcher.mods():
                self.assertFalse(self.launcher.enabled(mod))
                self.launcher.set_enabled(mod, True)
                self.assertTrue(self.launcher.enabled(mod))
                self.launcher.remove_mod(mod)
            self.launcher.select_shader("owned.hshader")
            self.assertEqual(pairs(self.launcher.game / "horizon-graphics.txt")["pickedShaderPack"], "owned.hshader")
            self.launcher.select_shader("")
            self.launcher.add_profile("other")
        self.assertEqual(world.read_bytes(), b"owned existing save sentinel")
        self.assertEqual({path.suffix for path in (self.launcher.state / "removed").iterdir()}, {".hmod", ".hnmod"})

    @unittest.skipUnless(BINARY and BINARY.is_file(), "Set HERPS_TEST_PORT_PACK to the pinned executable")
    def test_external_override_cannot_satisfy_bundled_smoke(self):
        evidence = {}
        with patch.object(entry.sys, "frozen", True, create=True), \
                patch.object(entry.sys, "_MEIPASS", str(self.bundle), create=True), \
                patch.dict(os.environ, {"HERPS_PORT_PACK": str(BINARY)}, clear=True):
            with self.assertRaisesRegex(ValueError, "external port-pack"):
                entry.port_pack_smoke(self.launcher, self.root, evidence)
        self.assertEqual(evidence["status"], "failed")
        self.assertFalse(evidence["bundled"])
        self.assertFalse(list(self.root.glob("*.jar")))

    @unittest.skipUnless(BINARY and BINARY.is_file(), "Set HERPS_TEST_PORT_PACK to the pinned executable")
    def test_real_bundled_helper_checks_data_and_rejects_false_positive_works(self):
        name = "horizon-port-pack.exe" if os.name == "nt" else "horizon-port-pack"
        helper = self.bundle / name
        shutil.copy2(BINARY, helper)
        evidence = {}
        with patch.object(entry.sys, "frozen", True, create=True), \
                patch.object(entry.sys, "_MEIPASS", str(self.bundle), create=True), \
                patch.dict(os.environ, {}, clear=True):
            entry.port_pack_smoke(self.launcher, self.root, evidence)
        self.assertEqual(evidence["status"], "passed")
        self.assertTrue(evidence["bundled"])
        self.assertEqual(evidence["sha256"], digest(helper))
        self.assertEqual(evidence["path"], str(helper))
        self.assertEqual([check["adapter_status"] for check in evidence["checks"]],
                         ["Requires porting", "Unsupported"])
        for check in evidence["checks"]:
            self.assertEqual(check["original_verdict"], "works")
            self.assertIsNone(check["test_execution"])
            self.assertEqual(check["original_check"]["verdict"], "works")
            self.assertTrue(check["commands"])
            self.assertTrue(all(command["exit_code"] == 0 for command in check["commands"]))
        self.assertFalse(evidence["gameplay_verified"])
        self.assertFalse(evidence["java_bridge_available"])
        json.dumps(evidence)  # All raw process evidence can be retained in the smoke report.


if __name__ == "__main__":
    unittest.main()
