"""Actual file/ZIP round trips; fixture bytes are not Minecraft/gameplay proof."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

from herps_launcher.core import Launcher, digest, json_write
from herps_launcher.modpacks.service import ModpackLibrary
from herps_launcher.modpacks import targeted_backup as backup


class TargetedBackupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps-targeted-backup-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.launcher = Launcher(self.root / "support with spaces")
        self.launcher.add_profile("accept_a")
        self.library = ModpackLibrary(self.launcher)
        self.token = "a" * 32
        self.source = self.library.root / "imports" / self.token / "input.zip"
        self.receipt = self.source.parent / "import.json"
        self.source.parent.mkdir(parents=True)
        self.make_import()
        self.save = self.launcher.game / "saves" / "World α" / "level.dat"
        self.save.parent.mkdir(parents=True)
        self.save.write_bytes(b"owned binary fixture\0\xff; not a real world")
        (self.save.parent / "empty").mkdir()
        self.sentinels = [self.save, self.launcher.config_file,
            self.launcher.support / "game/saves/Unopened/level.dat",
            self.launcher.state / "profiles/accept_b/saves/Other/level.dat",
            self.launcher.game / "options.txt", self.launcher.game / "horizon-mod-data/owned.txt"]
        for path in self.sentinels[2:]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"owned preservation sentinel " + path.name.encode())
        self.original = {path: digest(path) for path in self.sentinels}

    def make_import(self, files=None):
        self.source = self.library.root / "imports" / self.token / "input.zip"
        self.receipt = self.source.parent / "import.json"
        self.source.parent.mkdir(parents=True, exist_ok=True)
        manifest = {"name": backup.FUNCRAFT_NAME, "version": backup.FUNCRAFT_VERSION,
            "files": files if files is not None else [{"projectID": 314904, "fileID": 2749104}]}
        with ZipFile(self.source, "w") as zipped:
            zipped.writestr("manifest.json", json.dumps(manifest))
        json_write(self.receipt, {"schema": 1, "token": self.token, "name": manifest["name"],
            "format": "curseforge", "source": str(self.source), "source_hashes": {".": digest(self.source)}})
        # Only synthetic owned unit inputs use this override. A real-input
        # smoke separately exercises the production hash without any patch.
        self.enterContext(patch.object(backup, "FUNCRAFT_SHA256", digest(self.source)))

    @property
    def destination(self):
        return self.launcher.state / "targeted-backups"

    def create(self):
        return backup.create_backup(self.library, self.token, external_processes_closed=True)

    def assert_unchanged(self):
        self.assertEqual(self.original, {path: digest(path) for path in self.sentinels})
        self.assertFalse(self.launcher.operation_lock.exists())
        self.assertIsNone(self.launcher.lock_fd)

    def test_verified_archive_round_trips_unicode_binary_and_empty_directories(self):
        result = self.create()
        self.assertTrue(result["verified"])
        self.assertFalse(result["gameplay_verified"])
        self.assertEqual(result["archive_sha256"], digest(Path(result["path"])))
        restored = self.root / "separate scratch restore"
        # The production verifier never extracts. This owned-file test checks
        # that a standard unzip actually recreates the expected filesystem.
        with ZipFile(result["path"]) as zipped:
            zipped.extractall(restored)
        self.assertEqual((restored / "saves/World α/level.dat").read_bytes(), self.save.read_bytes())
        self.assertTrue((restored / "saves/World α/empty").is_dir())
        self.assertEqual(backup.verify_backup(Path(result["path"]))["profile"], "accept_a")
        self.assert_unchanged()

    def test_successive_backups_never_replace_a_previous_archive(self):
        first = self.create()
        second = self.create()
        self.assertNotEqual(first["path"], second["path"])
        self.assertEqual(digest(Path(first["path"])), first["archive_sha256"])
        self.assert_unchanged()

    def test_original_default_profile_is_supported_without_switching_or_touching_named_data(self):
        self.launcher.config["profile"] = "default"
        self.make_import()
        result = self.create()
        self.assertEqual(result["profile"], "default")
        with ZipFile(result["path"]) as zipped:
            self.assertIn("saves/Unopened/level.dat", zipped.namelist())
            self.assertNotIn("saves/World α/level.dat", zipped.namelist())
        self.assert_unchanged()

    def test_user_must_confirm_external_processes_are_closed(self):
        with self.assertRaisesRegex(ValueError, "Confirm"):
            backup.create_backup(self.library, self.token)
        self.assertFalse(self.destination.exists())
        self.assert_unchanged()

    def test_unknown_pack_or_missing_ftb_requirement_cannot_unlock_feature(self):
        with patch.object(backup, "FUNCRAFT_SHA256", "0" * 64):
            self.assertFalse(backup.eligibility(self.library, self.token)["available"])
            with self.assertRaisesRegex(ValueError, "Only the exact"):
                self.create()
        self.make_import(files=[])
        with self.assertRaisesRegex(ValueError, "identity or FTB"):
            self.create()
        self.assertFalse(self.destination.exists())
        self.assert_unchanged()

    def test_tampered_import_and_cross_profile_tokens_are_rejected(self):
        self.source.write_bytes(b"edited input")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            self.create()
        self.launcher.add_profile("another")
        with self.assertRaises(ValueError):
            self.create()
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.launcher.operation_lock.exists())

    def test_running_owned_child_process_blocks_backup(self):
        process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.addCleanup(lambda: process.poll() is None and (process.terminate(), process.wait(timeout=10)))
        self.launcher.child = process
        with self.assertRaisesRegex(ValueError, "running game"):
            self.create()
        self.assertFalse(self.destination.exists())
        self.assert_unchanged()

    def test_another_controller_lock_and_pending_session_are_preserved(self):
        other = Launcher(self.launcher.support)
        other.acquire()
        try:
            with self.assertRaisesRegex(ValueError, "Another launcher"):
                self.create()
            self.assertTrue(other.operation_lock.exists())
        finally:
            other.release()
        self.launcher.pending_file.write_text('{"pid":123}')
        with self.assertRaisesRegex(ValueError, "unfinished game"):
            self.create()
        self.assertTrue(self.launcher.pending_file.exists())
        self.assert_unchanged()

    def test_current_owned_lock_is_not_released_by_a_rejected_backup(self):
        self.launcher.acquire()
        try:
            with self.assertRaisesRegex(ValueError, "operation"):
                self.create()
            self.assertIsNotNone(self.launcher.lock_fd)
            self.assertTrue(self.launcher.operation_lock.exists())
        finally:
            self.launcher.release()

    def test_empty_profiles_do_not_produce_successful_empty_backups(self):
        self.save.unlink()
        with self.assertRaisesRegex(ValueError, "no saved files"):
            self.create()
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.launcher.operation_lock.exists())

    def test_linked_save_and_linked_backup_destination_are_rejected(self):
        outside = self.root / "outside.txt"
        outside.write_text("outside untouched")
        linked = self.save.parent / "linked.dat"
        try:
            linked.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"Symlink construction unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "linked"):
            self.create()
        linked.unlink()
        self.destination.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "linked"):
            self.create()
        self.assertEqual(outside.read_text(), "outside untouched")
        self.assert_unchanged()

    def test_size_and_entry_limits_fail_before_publishing(self):
        for name, limit in [("MAX_FILE_BYTES", 1), ("MAX_BYTES", 1), ("MAX_ENTRIES", 1)]:
            with self.subTest(limit=name), patch.object(backup, name, limit):
                with self.assertRaises(ValueError):
                    self.create()
                self.assertFalse(self.destination.exists())
                self.assert_unchanged()

    def test_depth_boundary_counts_source_components_without_the_zip_container(self):
        deep = self.launcher.game / "saves" / Path(*(["d"] * 31)) / "owned.dat"
        deep.parent.mkdir(parents=True)
        deep.write_bytes(b"owned depth boundary")
        first = self.create()
        self.assertTrue(backup.verify_backup(Path(first["path"]))["verified"])
        deeper = deep.parent / "d" / "too-deep.dat"
        deeper.parent.mkdir()
        deeper.write_bytes(b"owned out-of-scope depth")
        with self.assertRaisesRegex(ValueError, "Invalid backup path"):
            self.create()
        self.assertEqual(list(self.destination.rglob("worlds.zip")), [Path(first["path"])])
        self.assert_unchanged()

    def test_observed_concurrent_save_change_discards_only_new_output(self):
        previous = self.create()
        copy = backup._copy_file
        def change(library, source, relative, expected, zipped):
            copy(library, source, relative, expected, zipped)
            self.save.write_bytes(b"external test writer changed the save")
        with patch.object(backup, "_copy_file", side_effect=change):
            with self.assertRaisesRegex(ValueError, "changed"):
                self.create()
        self.assertEqual(list(self.destination.rglob("worlds.zip")), [Path(previous["path"])])
        self.assertEqual(digest(Path(previous["path"])), previous["archive_sha256"])
        self.assertFalse(self.launcher.operation_lock.exists())
        self.assertFalse(list(self.destination.rglob("*.partial")))

    def test_write_or_verification_failure_leaves_no_success_and_allows_retry(self):
        for target, failure in [("_copy_file", OSError("injected disk full")), ("verify_backup", ValueError("injected verification failure")), ("os.replace", OSError("injected publication failure"))]:
            with self.subTest(target=target), patch("herps_launcher.modpacks.targeted_backup." + target, side_effect=failure):
                with self.assertRaises(type(failure)):
                    self.create()
                self.assertFalse(list(self.destination.rglob("worlds.zip")))
                self.assertFalse(list(self.destination.rglob("*.partial")))
                self.assert_unchanged()
        self.assertTrue(self.create()["verified"])

    def test_cleanup_failure_still_releases_the_shared_lock(self):
        with patch.object(backup, "_copy_file", side_effect=OSError("write failed")), patch.object(backup.shutil, "rmtree", side_effect=OSError("cleanup failed")):
            with self.assertRaisesRegex(OSError, "cleanup failed"):
                self.create()
        self.assertFalse(self.launcher.operation_lock.exists())
        self.assertFalse(list(self.destination.rglob("worlds.zip")))
        self.assert_unchanged()

    def rewritten(self, path, transform):
        with ZipFile(path) as zipped:
            values = [(i, zipped.read(i)) for i in zipped.infolist()]
        output = self.root / "tampered.zip"
        with ZipFile(output, "w") as zipped:
            for name, data in transform(values):
                zipped.writestr(name, data)
        return output

    def test_checksum_tampering_never_repairs_or_overwrites_a_save(self):
        result = self.create()
        tampered = self.rewritten(result["path"], lambda values: [(i, b"X" * len(data) if i.filename.endswith("level.dat") else data) for i, data in values])
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            backup.verify_backup(tampered)
        self.assert_unchanged()

    def test_duplicate_manifest_keys_and_changed_archive_fail_closed(self):
        result = self.create()
        duplicate = self.rewritten(result["path"], lambda values: [(i, data.replace(b'"schema": 1,', b'"schema": 1, "schema": 1,') if i.filename == "backup-manifest.json" else data) for i, data in values])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            backup.verify_backup(duplicate)
        actual_digest = backup.digest
        def change(path):
            path.write_bytes(b"external test writer changed the archive")
            return actual_digest(path)
        with patch.object(backup, "digest", side_effect=change):
            with self.assertRaisesRegex(ValueError, "changed during verification"):
                backup.verify_backup(Path(result["path"]))
        self.assert_unchanged()

    def test_injected_gameplay_claims_in_a_backup_never_become_acceptance(self):
        result = self.create()
        def claim(values):
            for item, data in values:
                if item.filename == "backup-manifest.json":
                    manifest = json.loads(data)
                    manifest.update(gameplay_verified=True, java_bridge_available=True, playable_verified=True)
                    data = json.dumps(manifest).encode()
                yield item, data
        edited = self.rewritten(result["path"], claim)
        checked = backup.verify_backup(edited)
        self.assertTrue(checked["verified"])
        self.assertFalse(checked["gameplay_verified"])
        self.assertNotIn("java_bridge_available", checked)
        self.assertNotIn("playable_verified", checked)
        self.assert_unchanged()

    def test_unsafe_or_undeclared_zip_members_and_links_are_rejected(self):
        result = self.create()
        symlink = ZipInfo("saves/link")
        symlink.external_attr = 0o120777 << 16
        for name in ["../escape", "saves/CON", "unexpected.class", symlink]:
            with self.subTest(member=str(name)):
                tampered = self.rewritten(result["path"], lambda values: values + [(name, b"untrusted")])
                with self.assertRaises(ValueError):
                    backup.verify_backup(tampered)
        self.assertFalse((self.root.parent / "escape").exists())
        self.assert_unchanged()

    def test_duplicate_and_file_directory_case_collision_zip_members_are_rejected(self):
        result = self.create()
        for name in ["saves/World α", "saves/world α/", "saves/World α/level.dat/"]:
            with self.subTest(member=name):
                tampered = self.rewritten(result["path"], lambda values: values + [(name, b"")])
                with self.assertRaisesRegex(ValueError, "Ambiguous"):
                    backup.verify_backup(tampered)
        self.assert_unchanged()
