"""Profile/inventory-package safeguards with owned fixtures, never gameplay."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from herps_launcher.core import Launcher, atomic, digest, pairs
from herps_launcher.modpacks import flint, gathering


class GatheringTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="owned-gathering-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.launcher = Launcher(self.root / "support")
        self.launcher.add_profile("disposable")
        self.engine = SimpleNamespace(metadata={"engine_source": {"native_features": [gathering.ENGINE_FEATURE]}})
        self.enterContext(patch.object(self.launcher, "installation", return_value=self.engine))
        for module, name in [(flint, "flint"), (gathering, "gathering")]:
            package = self.root / module.PACKAGE_NAME
            if getattr(sys, "frozen", False):
                data = module.bundled_package().read_bytes()
            else:
                from tools.build_rlcraft_chainmail import package_bytes
                data = package_bytes(Path(__file__).resolve().parents[1] / f"content/rlcraft_{name}")
            package.write_bytes(data)
            self.enterContext(patch.object(module, "bundled_package", return_value=package))

    def starter(self):
        flint.install(self.launcher, "disposable", disposable_confirmed=True, games_closed=True)
        self.launcher.set_enabled(self.mod(flint), True)

    def mod(self, module=gathering):
        return next(m for m in self.launcher.mods() if m.id == module.MOD_ID)

    def install(self):
        return gathering.install(self.launcher, self.launcher.config["profile"],
            disposable_confirmed=True, games_closed=True)

    def test_package_is_a_separate_opt_in_tag_and_old_items_are_unchanged(self):
        data = gathering.validate_package(gathering.bundled_package())
        self.assertEqual(hashlib.sha256(data).hexdigest(), gathering.PACKAGE_SHA256)
        with ZipFile(gathering.bundled_package()) as z:
            tag = json.loads(z.read(f"data/{gathering.MOD_ID}/tags/item/enabled.json"))
            self.assertEqual(tag["values"], [f"{flint.MOD_ID}:{n}" for n in ("flint_shard", "plant_fiber", "flint_knife")])
            self.assertFalse(any(n.startswith("data/minecraft/") or n.endswith((".jar", ".class", ".wasm", ".exe")) for n in z.namelist()))
        self.assertEqual(digest(flint.bundled_package()), flint.PACKAGE_SHA256)

    def test_install_disabled_preserves_starter_other_profiles_and_backups(self):
        self.starter()
        paths = [flint._path(self.launcher), self.launcher.support / "game/saves/Existing/level.dat",
            self.launcher.state / "targeted-backups/funcraft/owned/worlds.zip",
            self.launcher.state / "profiles/other/saves/Owned/level.dat"]
        for p in paths[1:]: atomic(p, b"owned preservation sentinel")
        before = {p: digest(p) for p in paths}
        self.assertFalse(self.install()["enabled"])
        self.assertTrue(flint.status(self.launcher)["enabled"])
        self.assertEqual({p: digest(p) for p in paths}, before)

    def test_dependency_and_old_engine_are_rejected_without_installing(self):
        with self.assertRaisesRegex(ValueError, "Starter"): self.install()
        self.starter()
        self.engine.metadata = {"engine_source": {}}
        before = (self.launcher.game / "horizon-mods.txt").read_bytes()
        with self.assertRaisesRegex(ValueError, "stage-2 native client"): self.install()
        self.assertFalse(gathering._path(self.launcher).exists())
        self.assertEqual((self.launcher.game / "horizon-mods.txt").read_bytes(), before)

    def test_enable_and_launch_require_enabled_unchanged_starter(self):
        self.starter(); self.install()
        self.launcher.set_enabled(self.mod(flint), False)
        with self.assertRaisesRegex(ValueError, "Starter"): self.launcher.set_enabled(self.mod(), True)
        self.launcher.set_enabled(self.mod(flint), True)
        self.launcher.set_enabled(self.mod(), True)
        gathering.protect_launch(self.launcher)
        self.launcher.set_enabled(self.mod(flint), False)
        with self.assertRaisesRegex(ValueError, "Starter"): gathering.protect_launch(self.launcher)

    def test_saved_profiles_cannot_disable_remove_or_launch_missing_content(self):
        self.starter(); self.install(); mod = self.mod()
        self.launcher.set_enabled(mod, True)
        saved = self.launcher.game / "saves/Owned/level.dat"; atomic(saved, b"owned sentinel")
        before = digest(saved)
        for action in [lambda: self.launcher.set_enabled(mod, False), lambda: self.launcher.remove_mod(mod)]:
            with self.assertRaisesRegex(ValueError, "saves"): action()
        gathering.protect_launch(self.launcher)
        gathering._path(self.launcher).unlink()
        with self.assertRaises(ValueError): gathering.protect_launch(self.launcher)
        self.assertEqual(digest(saved), before)

    def test_default_consent_saves_and_busy_sessions_are_protected(self):
        self.starter()
        with self.assertRaisesRegex(ValueError, "Explicitly confirm"):
            gathering.install(self.launcher, "disposable")
        self.launcher.config["profile"] = "default"
        with self.assertRaisesRegex(ValueError, "default profile"): self.install()
        self.launcher.config["profile"] = "disposable"
        self.launcher.acquire()
        try:
            with self.assertRaises(ValueError): self.install()
        finally: self.launcher.release()
        atomic(self.launcher.game / "saves/Owned/level.dat", b"owned sentinel")
        with self.assertRaisesRegex(ValueError, "existing saves"): self.install()
        self.assertFalse(gathering._path(self.launcher).exists())

    def test_generic_import_and_tampered_receipts_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Modpacks"):
            self.launcher.install_mod(gathering.bundled_package())
        self.starter(); self.install()
        receipt = gathering._receipt(self.launcher)
        value = json.loads(receipt.read_text()); value["profile"] = "other"
        receipt.write_text(json.dumps(value))
        with self.assertRaises(ValueError): self.launcher.set_enabled(self.mod(), True)

    def test_failed_receipt_write_rolls_back_new_files_and_preserves_settings(self):
        self.starter()
        settings = self.launcher.game / "horizon-mods.txt"; before = settings.read_bytes()
        receipt = gathering._receipt(self.launcher); original = Path.open
        def fail(path, *args, **kwargs):
            if path == receipt and args and args[0] == "xb": raise OSError("owned write failure")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", fail), self.assertRaises(OSError): self.install()
        self.assertFalse(gathering._path(self.launcher).exists())
        self.assertFalse(receipt.exists()); self.assertEqual(settings.read_bytes(), before)

    def test_remove_empty_profile_moves_only_addon_and_receipt(self):
        self.starter(); before = digest(flint._path(self.launcher)); self.install()
        backup = self.launcher.remove_mod(self.mod())
        self.assertEqual(digest(backup / gathering.PACKAGE_NAME), gathering.PACKAGE_SHA256)
        self.assertTrue((backup / "receipt.json").is_file())
        self.assertEqual(digest(flint._path(self.launcher)), before)
        self.assertTrue(flint.status(self.launcher)["enabled"])

    @unittest.skipUnless(sys.platform == "win32", "Windows junction behavior requires Windows")
    def test_windows_junction_cannot_redirect_addon_install(self):
        import subprocess
        self.starter()
        receipt_parent = gathering._receipt(self.launcher).parent
        receipt_parent.parent.mkdir(parents=True)
        outside = self.root / "outside"; outside.mkdir()
        subprocess.run(["cmd", "/c", "mklink", "/J", str(receipt_parent), str(outside)], check=True, capture_output=True)
        self.addCleanup(lambda: receipt_parent.rmdir() if receipt_parent.is_junction() else None)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(list(outside.iterdir()), [])
