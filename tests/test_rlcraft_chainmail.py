"""Real package/filesystem safeguards; these tests do not run a game/world."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import subprocess
import tomllib
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from herps_launcher.core import Launcher, atomic, digest, inspect_mod, pairs
from herps_launcher.modpacks import chainmail as feature
from tools.build_rlcraft_chainmail import package_bytes, ROOT
from tools.verify_rlcraft_chainmail import probe_manifest


class ChainmailTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="chainmail-owned-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.launcher = Launcher(self.root / "support")
        self.launcher.add_profile("disposable")
        self.package = self.root / feature.PACKAGE_NAME
        self.package.write_bytes(package_bytes())
        self.enterContext(patch.object(feature, "bundled_package", return_value=self.package))

    def install(self, **kwargs):
        return feature.install(self.launcher, self.launcher.config["profile"],
            disposable_confirmed=True, games_closed=True, **kwargs)

    def mod(self):
        return next(mod for mod in self.launcher.mods() if mod.id == feature.MOD_ID)

    def world(self):
        saved = self.launcher.game / "saves/Owned/level.dat"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"owned preservation fixture; not a real world")
        return saved

    def test_package_exact_scope_modern_recipe_ids_and_notices(self):
        data = feature.validate_package(self.package)
        self.assertEqual(hashlib.sha256(data).hexdigest(), feature.PACKAGE_SHA256)
        with ZipFile(self.package) as zipped:
            recipes = [name for name in zipped.namelist() if "/recipe/" in name]
            self.assertEqual(len(recipes), 2)
            plate = json.loads(zipped.read(f"data/{feature.MOD_ID}/recipe/chainmail_plate.json"))
            boots = json.loads(zipped.read(f"data/{feature.MOD_ID}/recipe/chainmail_boots.json"))
            self.assertEqual(plate["pattern"], ["nn", "nn"])
            self.assertEqual(plate["key"], {"n": "minecraft:iron_nugget"})
            self.assertEqual(plate["result"], {"id": feature.MOD_ID + ":chainmail_plate", "count": 1})
            self.assertEqual(boots["pattern"], ["p p", "p p"])
            self.assertEqual(boots["result"], {"id": "minecraft:chainmail_boots", "count": 1})
            self.assertIn(b"2019 Kfir Awad", zipped.read("LICENSE-CraftableChainmail.txt"))
            self.assertIn(b"GNU GENERAL PUBLIC LICENSE", zipped.read("LICENSE-HERPS.txt"))
            self.assertFalse(any(name.endswith((".jar", ".wasm", ".png")) for name in zipped.namelist()))

    def test_deterministic_across_checkout_line_endings(self):
        source = ROOT / "content/rlcraft_chainmail"
        copy = self.root / "crlf"
        for path in source.rglob("*"):
            if path.is_file():
                target = copy / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertEqual(package_bytes(copy), self.package.read_bytes())

    def test_native_probe_keeps_workspace_vendor_overrides_and_resolver(self):
        source = self.root / "pinned source"
        (source / "third_party/winit").mkdir(parents=True)
        (source / "third_party/wgpu-hal").mkdir()
        (source / "Cargo.toml").write_text('[patch.crates-io]\nwinit={path="third_party/winit"}\nwgpu-hal={path="third_party/wgpu-hal"}\n')
        manifest = tomllib.loads(probe_manifest(source, True))
        self.assertEqual(manifest["workspace"]["resolver"], "2")
        for name in ("winit", "wgpu-hal"):
            self.assertEqual(Path(manifest["patch"]["crates-io"][name]["path"]), (source / "third_party" / name).resolve())
        (source / "Cargo.toml").write_text('[patch.crates-io]\nwinit={path="../outside"}\n')
        with self.assertRaisesRegex(ValueError, "escaped"):
            probe_manifest(source, True)

    def test_default_profile_and_missing_consent_are_rejected_without_install(self):
        with self.assertRaisesRegex(ValueError, "Explicitly confirm"):
            feature.install(self.launcher, "disposable")
        self.launcher.config["profile"] = "default"
        with self.assertRaisesRegex(ValueError, "default profile"):
            self.install()
        self.assertFalse((self.launcher.game / "horizon-mods").exists())

    def test_profile_change_and_running_or_pending_sessions_fail_closed(self):
        with self.assertRaises(ValueError):
            feature.install(self.launcher, "other", disposable_confirmed=True, games_closed=True)
        self.launcher.pending_file.write_text("{}")
        with self.assertRaisesRegex(ValueError, "pending"):
            self.install()
        self.launcher.pending_file.unlink()
        with patch.object(self.launcher, "child") as child:
            child.poll.return_value = None
            with self.assertRaisesRegex(ValueError, "running game"):
                self.install()
        self.launcher.acquire()
        try:
            with self.assertRaises(ValueError):
                self.install()
        finally:
            self.launcher.release()
        self.assertFalse(feature._path(self.launcher).exists())

    def test_existing_saves_are_never_installed_into(self):
        saved = self.world()
        before = digest(saved)
        with self.assertRaisesRegex(ValueError, "existing saves"):
            self.install()
        self.assertEqual(digest(saved), before)
        self.assertFalse(feature._path(self.launcher).exists())

    def test_install_disabled_preserves_other_profiles_imports_and_backup(self):
        other = self.launcher.support / "game/saves/Existing/level.dat"
        backup = self.launcher.state / "targeted-backups/funcraft/existing/worlds.zip"
        imported = self.launcher.game / "modpacks/imports/owned/source.zip"
        for path in (other, backup, imported):
            atomic(path, b"owned unchanged sentinel")
        before = {path: digest(path) for path in (other, backup, imported)}
        settings = self.launcher.game / "horizon-mods.txt"
        settings.write_text(f"unknown:keep\nmod.{feature.MOD_ID}:true\n")
        result = self.install()
        self.assertFalse(result["enabled"])
        self.assertFalse(result["gameplay_verified"])
        self.assertEqual(digest(feature._path(self.launcher)), feature.PACKAGE_SHA256)
        self.assertEqual(pairs(settings)["unknown"], "keep")
        self.assertEqual({path: digest(path) for path in before}, before)
        self.assertFalse((self.launcher.support / "game/horizon-mods").exists())

    def test_duplicate_install_does_not_overwrite_owned_files(self):
        self.install()
        before = digest(feature._path(self.launcher))
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.install()
        self.assertEqual(digest(feature._path(self.launcher)), before)

    def test_generic_import_cannot_bypass_disposable_consent(self):
        with self.assertRaisesRegex(ValueError, "Modpacks"):
            self.launcher.install_mod(self.package)
        self.assertFalse(feature._path(self.launcher).exists())

    def test_folder_namespace_collision_preserves_existing_mod(self):
        manifest = self.launcher.game / "horizon-mods/another/horizon-mod.toml"
        atomic(manifest, f'id="another"\napi="0.2"\nname="Owned"\nversion="1"\ncapabilities=["registries"]\nnamespaces=["{feature.MOD_ID}"]\n'.encode())
        original = digest(manifest)
        with self.assertRaisesRegex(ValueError, "namespace"):
            self.install()
        self.assertEqual(digest(manifest), original)

    def test_archive_id_collision_preserves_existing_mod(self):
        duplicate = self.launcher.game / "horizon-mods/another.hmod"
        atomic(duplicate, self.package.read_bytes())
        with self.assertRaisesRegex(ValueError, "namespace"):
            self.install()
        self.assertEqual(digest(duplicate), feature.PACKAGE_SHA256)

    def test_tampered_bundle_is_rejected(self):
        self.package.write_bytes(self.package.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.install()
        self.assertFalse(feature._path(self.launcher).exists())

    def test_publication_failure_rolls_back_only_owned_package_and_settings(self):
        settings = self.launcher.game / "horizon-mods.txt"
        atomic(settings, b"unknown:keep\n")
        receipt = feature._receipt(self.launcher)
        original_open = Path.open
        def fail(path, *args, **kwargs):
            if path == receipt and args and args[0] == "xb":
                raise OSError("owned injected receipt failure")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", fail), self.assertRaisesRegex(OSError, "receipt failure"):
            self.install()
        self.assertFalse(feature._path(self.launcher).exists())
        self.assertFalse(receipt.exists())
        self.assertEqual(settings.read_bytes(), b"unknown:keep\n")

    def test_empty_profile_enable_disable_and_removal_retains_backup(self):
        self.install()
        mod = self.mod()
        self.launcher.set_enabled(mod, True)
        self.assertTrue(self.launcher.enabled(mod))
        self.launcher.set_enabled(mod, False)
        backup = self.launcher.remove_mod(mod)
        self.assertFalse(feature._path(self.launcher).exists())
        self.assertEqual(digest(backup / feature.PACKAGE_NAME), feature.PACKAGE_SHA256)
        self.assertTrue((backup / "receipt.json").is_file())
        self.assertFalse(feature.status(self.launcher)["installed"])
        self.install()

    def test_saves_block_disable_remove_and_disabled_launch(self):
        self.install()
        mod = self.mod()
        self.launcher.set_enabled(mod, True)
        saved = self.world()
        before = digest(saved)
        for operation in (lambda: self.launcher.set_enabled(mod, False), lambda: self.launcher.remove_mod(mod)):
            with self.assertRaises(ValueError):
                operation()
        feature.protect_launch(self.launcher)
        settings = self.launcher.game / "horizon-mods.txt"
        settings.write_text(f"mod.{feature.MOD_ID}:false\n")
        with self.assertRaisesRegex(ValueError, "enable"):
            self.launcher.command()
        self.assertEqual(digest(saved), before)

    def test_missing_or_tampered_content_blocks_profile_launch(self):
        self.install()
        self.launcher.set_enabled(self.mod(), True)
        self.world()
        feature._path(self.launcher).unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.launcher.command()
        feature._path(self.launcher).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.launcher.command()

    def test_wrong_profile_receipt_and_settings_links_rejected(self):
        self.install()
        receipt = feature._receipt(self.launcher)
        data = json.loads(receipt.read_text())
        data["profile"] = "different"
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "receipt changed"):
            self.launcher.set_enabled(self.mod(), True)

    def test_malformed_receipt_is_a_preservation_error_not_a_status_crash(self):
        self.install()
        before = digest(feature._path(self.launcher))
        for value in ("[]", "null", "0", '"text"', "{"):
            with self.subTest(receipt=value):
                feature._receipt(self.launcher).write_text(value)
                with self.assertRaises(ValueError):
                    feature.status(self.launcher)
                self.assertEqual(digest(feature._path(self.launcher)), before)

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior requires Windows")
    def test_windows_junction_cannot_redirect_installation(self):
        external = self.root / "outside"
        external.mkdir()
        self.launcher.game.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(self.launcher.game), str(external)], check=True, capture_output=True)
        try:
            with self.assertRaisesRegex(ValueError, "linked"):
                self.install()
            self.assertEqual(list(external.iterdir()), [])
        finally:
            self.launcher.game.rmdir()

    @unittest.skipIf(os.name == "nt", "Windows link guards are exercised with junctions separately")
    def test_linked_profile_and_settings_preserve_external_files(self):
        external = self.root / "external"
        external.mkdir()
        self.launcher.game.parent.mkdir(parents=True, exist_ok=True)
        self.launcher.game.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "linked"):
            self.install()
        self.assertEqual(list(external.iterdir()), [])
        self.launcher.game.unlink()
        self.launcher.game.mkdir()
        setting = external / "settings"
        setting.write_text("owned:preserve\n")
        (self.launcher.game / "horizon-mods.txt").symlink_to(setting)
        with self.assertRaisesRegex(ValueError, "linked"):
            self.install()
        self.assertEqual(setting.read_text(), "owned:preserve\n")
