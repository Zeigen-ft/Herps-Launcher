"""Owned files and real native content packages; never simulated gameplay."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from herps_launcher.core import Launcher, atomic, digest, pairs
from herps_launcher.modpacks import flint, chainmail


class FlintTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="owned-flint-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.launcher = Launcher(self.root / "support")
        self.launcher.add_profile("disposable")
        self.package = self.root / flint.PACKAGE_NAME
        if getattr(sys, "frozen", False):
            data = flint.bundled_package().read_bytes()
        else:
            from tools.build_rlcraft_flint import package_bytes
            data = package_bytes()
        self.package.write_bytes(data)
        self.enterContext(patch.object(flint, "bundled_package", return_value=self.package))

    def install(self):
        return flint.install(self.launcher, self.launcher.config["profile"],
            disposable_confirmed=True, games_closed=True)

    def mod(self):
        return next(m for m in self.launcher.mods() if m.id == flint.MOD_ID)

    def world(self):
        saved = self.launcher.game / "saves/Owned/level.dat"
        atomic(saved, b"owned preservation fixture; not a real world")
        return saved

    def test_package_defines_four_items_five_recipes_and_finite_native_tools(self):
        data = flint.validate_package(self.package)
        self.assertEqual(hashlib.sha256(data).hexdigest(), flint.PACKAGE_SHA256)
        with ZipFile(self.package) as zipped:
            names = zipped.namelist()
            self.assertEqual(len([n for n in names if "/horizon/item/" in n]), 4)
            self.assertEqual(len([n for n in names if "/recipe/" in n]), 5)
            for name, template, durability in [("flint_knife", "wooden_sword", 32), ("flint_hatchet", "wooden_axe", 48)]:
                item = json.loads(zipped.read(f"data/{flint.MOD_ID}/horizon/item/{name}.json"))
                self.assertEqual(item["template"], f"minecraft:{template}")
                self.assertEqual(item["components"]["minecraft:max_damage"], durability)
                self.assertIn("!minecraft:repairable", item["components"])
            self.assertFalse(any(n.startswith("data/minecraft/") for n in names))
            self.assertFalse(any(n.endswith((".jar", ".class", ".wasm", ".png", ".exe")) for n in names))
            self.assertIn(b"independently authored", zipped.read("NOTICE.txt"))
            self.assertIn(b"GNU GENERAL PUBLIC LICENSE", zipped.read("LICENSE-HERPS.txt"))

    def test_line_endings_do_not_change_the_reviewed_package(self):
        from tools.build_rlcraft_flint import ROOT, package_bytes
        copied = self.root / "crlf"
        for path in (ROOT / "content/rlcraft_flint").rglob("*"):
            if path.is_file():
                target = copied / path.relative_to(ROOT / "content/rlcraft_flint")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertEqual(package_bytes(copied), self.package.read_bytes())

    def test_install_off_and_full_support_preservation(self):
        paths = [self.launcher.support / "game/saves/Existing/level.dat",
                 self.launcher.state / "targeted-backups/funcraft/existing/worlds.zip",
                 self.launcher.state / "profiles/other/saves/Existing/level.dat"]
        for path in paths: atomic(path, b"owned existing data")
        original = {p: digest(p) for p in paths}
        settings = self.launcher.game / "horizon-mods.txt"
        atomic(settings, f"unknown:keep\nmod.{flint.MOD_ID}:true\n".encode())
        result = self.install()
        self.assertTrue(result["installed"])
        self.assertFalse(result["enabled"])
        self.assertFalse(result["gameplay_verified"])
        self.assertEqual(pairs(settings)["unknown"], "keep")
        self.assertEqual({p: digest(p) for p in paths}, original)
        self.assertFalse((self.launcher.support / "game/horizon-mods").exists())

    def test_existing_saves_and_missing_consent_refuse_without_writes(self):
        with self.assertRaisesRegex(ValueError, "Explicitly confirm"):
            flint.install(self.launcher, "disposable")
        self.launcher.config["profile"] = "default"
        with self.assertRaisesRegex(ValueError, "default profile"):
            self.install()
        self.launcher.config["profile"] = "disposable"
        saved = self.world(); original = digest(saved)
        with self.assertRaisesRegex(ValueError, "existing saves"):
            self.install()
        self.assertEqual(digest(saved), original)
        self.assertFalse(flint._path(self.launcher).exists())

    def test_save_guard_missing_tampered_disabled_blocks_launch(self):
        self.install(); mod = self.mod()
        self.launcher.set_enabled(mod, True)
        saved = self.world(); original = digest(saved)
        for action in (lambda: self.launcher.set_enabled(mod, False), lambda: self.launcher.remove_mod(mod)):
            with self.assertRaisesRegex(ValueError, "saves"):
                action()
        flint.protect_launch(self.launcher)
        atomic(self.launcher.game / "horizon-mods.txt", f"mod.{flint.MOD_ID}:false\n".encode())
        with self.assertRaisesRegex(ValueError, "enable"):
            self.launcher.command()
        flint._path(self.launcher).unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.launcher.command()
        atomic(flint._path(self.launcher), b"edited")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.launcher.command()
        self.assertEqual(digest(saved), original)

    def test_removal_moves_only_owned_content_and_receipt(self):
        self.install(); mod = self.mod()
        self.launcher.set_enabled(mod, True)
        self.launcher.set_enabled(mod, False)
        backup = self.launcher.remove_mod(mod)
        self.assertFalse(flint.status(self.launcher)["installed"])
        self.assertEqual(digest(backup / flint.PACKAGE_NAME), flint.PACKAGE_SHA256)
        self.assertTrue((backup / "receipt.json").is_file())
        self.install()

    def test_generic_import_duplicate_and_namespace_collision_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Modpacks"):
            self.launcher.install_mod(self.package)
        collision = self.launcher.game / "horizon-mods/owned/horizon-mod.toml"
        atomic(collision, f'id="owned"\nname="Owned"\nversion="1"\napi="0.2"\ncapabilities=["registries"]\nnamespaces=["{flint.MOD_ID}"]\n'.encode())
        before = digest(collision)
        with self.assertRaisesRegex(ValueError, "namespace"):
            self.install()
        self.assertEqual(digest(collision), before)
        collision.unlink(); collision.parent.rmdir()
        self.install(); before = digest(flint._path(self.launcher))
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.install()
        self.assertEqual(digest(flint._path(self.launcher)), before)

    def test_malformed_and_wrong_profile_receipts_fail_closed(self):
        self.install()
        receipt = flint._receipt(self.launcher)
        original = receipt.read_text()
        for raw in ("[]", "null", "0", '"text"', "{"):
            receipt.write_text(raw)
            with self.assertRaises(ValueError): flint.status(self.launcher)
        data = json.loads(original); data["profile"] = "other"
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "receipt changed"):
            self.launcher.set_enabled(self.mod(), True)

    def test_running_pending_and_locked_sessions_cannot_install(self):
        self.launcher.pending_file.write_text("{}")
        with self.assertRaisesRegex(ValueError, "pending"): self.install()
        self.launcher.pending_file.unlink()
        with patch.object(self.launcher, "child") as child:
            child.poll.return_value = None
            with self.assertRaises(ValueError): self.install()
        self.launcher.acquire()
        try:
            with self.assertRaises(ValueError): self.install()
        finally:
            self.launcher.release()
        self.assertFalse(flint._path(self.launcher).exists())

    def test_receipt_write_failure_rolls_back_only_new_package_and_settings(self):
        settings = self.launcher.game / "horizon-mods.txt"
        atomic(settings, b"unknown:keep\n")
        original_open = Path.open; receipt = flint._receipt(self.launcher)
        def failing(path, *args, **kwargs):
            if path == receipt and args and args[0] == "xb": raise OSError("owned injected write failure")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", failing), self.assertRaises(OSError): self.install()
        self.assertEqual(settings.read_bytes(), b"unknown:keep\n")
        self.assertFalse(flint._path(self.launcher).exists())
        self.assertFalse(receipt.exists())

    def test_existing_chainmail_package_and_profile_stay_unchanged(self):
        if not getattr(sys, "frozen", False):
            from tools.build_rlcraft_chainmail import package_bytes
            package = self.root / chainmail.PACKAGE_NAME
            package.write_bytes(package_bytes())
        else:
            package = chainmail.bundled_package()
        with patch.object(chainmail, "bundled_package", return_value=package):
            chainmail.install(self.launcher, "disposable", disposable_confirmed=True, games_closed=True)
        mod = next(m for m in self.launcher.mods() if m.id == chainmail.MOD_ID)
        self.launcher.set_enabled(mod, True)
        original = digest(chainmail._path(self.launcher))
        self.install()
        self.assertEqual(digest(chainmail._path(self.launcher)), original)
        self.assertEqual(original, chainmail.PACKAGE_SHA256)
        self.assertTrue(chainmail.status(self.launcher)["enabled"])
        self.assertFalse(flint.status(self.launcher)["enabled"])

    @unittest.skipIf(sys.platform == "win32", "POSIX symlink fixture; Windows junction case is separate")
    def test_linked_mod_folder_and_receipt_cannot_redirect_install(self):
        outside = self.root / "outside"; outside.mkdir()
        self.launcher.game.mkdir(parents=True, exist_ok=True)
        (self.launcher.game / "horizon-mods").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(sys.platform == "win32", "Windows junction behavior requires Windows")
    def test_windows_junction_cannot_redirect_flint_install(self):
        import subprocess
        outside = self.root / "outside"; outside.mkdir()
        self.launcher.game.mkdir(parents=True, exist_ok=True)
        junction = self.launcher.game / "horizon-mods"
        subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], check=True, capture_output=True)
        self.addCleanup(lambda: junction.rmdir() if junction.is_junction() else None)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(list(outside.iterdir()), [])
