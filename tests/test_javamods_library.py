"""Profile/file preservation checks for managed, data-only Java ports."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from herps_launcher.core import Launcher, digest, pairs
from herps_launcher.javamods.adapter import PortPackAdapter
from herps_launcher.javamods.library import JavaModLibrary
from tools.make_javamods_fixtures import make_jar

BINARY = Path(os.environ["HERPS_TEST_PORT_PACK"]) if os.environ.get("HERPS_TEST_PORT_PACK") else None


class LibraryHarness(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps-java-library-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.launcher = Launcher(self.root / "support")
        self.library = JavaModLibrary(self.launcher)

    def imported(self, **kwargs):
        source = make_jar(self.root / "owned.jar", **kwargs)
        return self.library.import_jar(source)


class LibraryImportTests(LibraryHarness):
    def test_import_three_loaders_copies_owned_archives_without_subprocesses(self):
        with patch("subprocess.run") as run:
            for loader in ("fabric", "forge", "neoforge"):
                source = make_jar(self.root / (loader + ".jar"), loader=loader, mod_id=loader)
                original = source.read_bytes()
                entry = self.library.import_jar(source)
                self.assertEqual(entry.loader, loader)
                self.assertEqual(entry.path.read_bytes(), original)
                self.assertEqual(source.read_bytes(), original)
                self.assertTrue(entry.path.is_relative_to(self.launcher.game))
        run.assert_not_called()
        self.assertEqual(len(self.library.imports()), 3)

    def test_changed_import_is_detected_and_preserved(self):
        entry = self.imported()
        entry.path.chmod(0o600)
        entry.path.write_bytes(b"changed owned fixture")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.library.imports()
        self.assertEqual(entry.path.read_bytes(), b"changed owned fixture")

    def test_profiles_have_independent_imports_and_dependency_selections(self):
        first = self.imported()
        folder = self.root / "user dependencies"
        folder.mkdir()
        selected = self.library.set_dependencies(first.token, folder)
        self.assertEqual(selected.dependencies, folder)
        self.launcher.add_profile("other")
        self.assertEqual(self.library.imports(), [])
        with self.assertRaises(ValueError):
            self.library.set_dependencies(first.token, folder)
        second = self.imported()
        self.assertNotEqual(first.path, second.path)
        self.assertTrue(first.path.exists())

    def test_symlinked_profile_ancestor_cannot_redirect_mutations(self):
        destination = self.root / "outside"
        destination.mkdir()
        try:
            (self.launcher.state / "profiles").symlink_to(destination, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(str(error))
        self.launcher.add_profile("other")
        with self.assertRaisesRegex(ValueError, "linked"):
            self.imported()
        self.assertEqual(list(destination.iterdir()), [])

    def test_system_style_link_above_support_root_is_allowed(self):
        real = self.root / "real"
        real.mkdir()
        alias = self.root / "system-alias"
        try:
            alias.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(str(error))
        library = JavaModLibrary(Launcher(alias / "support"))
        entry = library.import_jar(make_jar(self.root / "owned.jar"))
        self.assertEqual(entry.metadata.mod_id, "demo")

    def test_import_cannot_race_existing_game_operation_lock(self):
        self.launcher.acquire()
        try:
            with self.assertRaisesRegex(ValueError, "operation"):
                self.imported()
            self.assertTrue(self.launcher.operation_lock.is_file())
        finally:
            self.launcher.release()
        self.assertEqual(self.library.imports(), [])


@unittest.skipUnless(BINARY is not None and BINARY.is_file(), "Set HERPS_TEST_PORT_PACK for real data-port tests")
class LibraryPortTests(LibraryHarness):
    def prepared(self, **kwargs):
        entry = self.imported(**kwargs)
        report = PortPackAdapter(self.launcher, executable=BINARY).port(entry.path)
        self.library.save_report(entry.token, report)
        return entry, report

    def test_real_data_folder_uses_engine_setting_starts_disabled_and_backs_up(self):
        entry, report = self.prepared()
        save = self.launcher.game / "saves/Owned/level.dat"
        save.parent.mkdir(parents=True)
        save.write_bytes(b"owned world sentinel")
        settings = self.launcher.game / "horizon-mods.txt"
        settings.write_text("key.old.toggle:R\nmod.other:true\n")
        port = self.library.install_port(entry.token, report)
        self.assertTrue((port.path / "horizon-mod.toml").is_file())
        self.assertFalse(port.enabled)
        self.library.enable_port(port, True)
        self.assertEqual(pairs(settings)["mod.demo"], "true")
        self.assertTrue(self.library.ports()[0].enabled)
        self.library.enable_port(port, False)
        backup = self.library.remove_port(port)
        self.assertTrue((backup / "content/horizon-mod.toml").is_file())
        self.assertTrue((backup / "receipt.json").is_file())
        self.assertFalse(port.path.exists())
        self.assertEqual(self.library.ports(), [])
        self.assertEqual(save.read_bytes(), b"owned world sentinel")
        self.assertEqual(pairs(settings)["mod.other"], "true")
        self.assertEqual(pairs(settings)["key.old.toggle"], "R")
        self.assertEqual(digest(entry.path), entry.sha256)

    def test_false_positive_works_cannot_install_an_unsupported_port(self):
        entry, report = self.prepared(depends={"missinglib": "*"}, invalid_class=True)
        self.assertEqual(report.mods[0].check.verdict, "works")
        self.assertEqual(report.status, "Unsupported")
        with self.assertRaisesRegex(ValueError, "recorded|supported"):
            self.library.install_port(entry.token, report)
        self.assertFalse((self.launcher.game / "horizon-mods/demo").exists())

    def test_changed_generated_data_is_refused_after_report_receipt(self):
        entry, report = self.prepared()
        source = Path(report.mods[0].port_path)
        data = next((source / "data").rglob("*.json"))
        data.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError, "changed"):
            self.library.install_port(entry.token, report)
        self.assertFalse((self.launcher.game / "horizon-mods/demo").exists())
        self.assertEqual(data.read_text(), '{"changed":true}')

    def test_changed_saved_report_cannot_install(self):
        entry, report = self.prepared()
        path = report.workspace / "report.json"
        data = json.loads(path.read_text())
        data["status"] = "Native compatibility"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "changed|disagree"):
            self.library.install_port(entry.token, report)

    def test_existing_folder_id_is_never_overwritten(self):
        entry, report = self.prepared()
        existing = self.launcher.game / "horizon-mods/other-name"
        existing.mkdir(parents=True)
        manifest = 'id="demo"\nname="Existing"\nversion="1"\napi="0.2"\nside="both"\ncapabilities=["registries"]\n'
        (existing / "horizon-mod.toml").write_text(manifest)
        with self.assertRaisesRegex(ValueError, "already installed"):
            self.library.install_port(entry.token, report)
        self.assertEqual((existing / "horizon-mod.toml").read_text(), manifest)

    def test_installed_data_edits_are_preserved_and_not_managed_blindly(self):
        entry, report = self.prepared()
        port = self.library.install_port(entry.token, report)
        data = next((port.path / "data").rglob("*.json"))
        data.write_text("owned edit")
        for operation in (lambda: self.library.enable_port(port, True), lambda: self.library.remove_port(port)):
            with self.assertRaisesRegex(ValueError, "changed"):
                operation()
        self.assertEqual(data.read_text(), "owned edit")

    def test_cross_profile_port_selection_cannot_affect_original(self):
        entry, report = self.prepared()
        port = self.library.install_port(entry.token, report)
        self.launcher.add_profile("other")
        with self.assertRaises(ValueError):
            self.library.enable_port(port, True)
        self.assertTrue(port.path.exists())

    def test_receipt_write_failure_rolls_back_only_new_installation(self):
        from herps_launcher.javamods import library as module
        entry, report = self.prepared()
        real_write = module.json_write

        def fail_receipt(path, data):
            if path.parent == self.library.root / "ports":
                raise OSError("owned disk write failure")
            return real_write(path, data)
        with patch.object(module, "json_write", side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, "disk write"):
                self.library.install_port(entry.token, report)
        self.assertFalse((self.launcher.game / "horizon-mods/demo").exists())
        self.assertTrue(Path(report.mods[0].port_path).exists())
        self.assertTrue(entry.path.exists())


if __name__ == "__main__":
    unittest.main()
