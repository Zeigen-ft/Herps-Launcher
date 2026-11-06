"""Real pinned port-pack regressions using only locally generated archives."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from herps_launcher.core import Launcher, digest
from herps_launcher.modpacks.service import ModpackLibrary
from tools.make_javamods_fixtures import make_jar
from tools.make_modpack_fixtures import mrpack, curseforge, instance, local_cf_instance, packwiz

BINARY = Path(os.environ["HERPS_TEST_PORT_PACK"]) if os.environ.get("HERPS_TEST_PORT_PACK") else None
FORBIDDEN = {"Native compatibility", "Tested successfully", "Compatible through Java bridge"}


@unittest.skipUnless(BINARY is not None and BINARY.is_file(), "Set HERPS_TEST_PORT_PACK for real modpack integration")
class ModpackServiceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps-pack-service-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.launcher = Launcher(self.root / "support with spaces")
        self.library = ModpackLibrary(self.launcher, executable=BINARY)
        self.user = self.root / "user mods"
        self.good = make_jar(self.user / "good.jar", mod_id="good")

    def analyze(self, source, dependencies=None):
        entry = self.library.import_pack(source)
        return entry, self.library.analyze(entry.token, dependencies=dependencies)

    def assert_unplayable(self, report):
        self.assertNotIn(report.status, FORBIDDEN)
        data = report.to_dict()
        self.assertFalse(data["playable_verified"])
        self.assertIsNone(data.get("test_execution"))
        for row in report.rows:
            self.assertNotIn(row.status, FORBIDDEN)

    def test_modrinth_import_resolves_owned_files_and_retains_every_coverage_column(self):
        source = mrpack(self.root / "owned.mrpack", [self.good])
        entry, report = self.analyze(source, self.user)
        self.assertEqual(entry.format, "mrpack")
        self.assertEqual(len(report.rows), 1)
        row = report.rows[0]
        self.assertEqual(row.id, "good")
        self.assertEqual(row.version, "1")
        self.assertEqual(row.license, "MIT")
        self.assertTrue(row.name)
        self.assertTrue(row.tier)
        self.assertTrue(row.reason)
        self.assertIsInstance(row.missing_dependencies, list)
        self.assertTrue(report.analysis)
        self.assertTrue(report.analysis.commands)
        self.assertIn("inventory", json.dumps(report.to_dict()))
        self.assert_unplayable(report)

    def test_prism_multimc_instance_uses_real_backend_import(self):
        source = instance(self.root / "Prism owned", [self.good])
        entry, report = self.analyze(source)
        self.assertIn(entry.format, ("instance", "prism", "multimc"))
        self.assertEqual([row.id for row in report.rows], ["good"])
        self.assertTrue(any(command.argv[1] == "import" for command in report.analysis.commands))
        self.assert_unplayable(report)

    def test_embedded_modrinth_mod_is_inspected_without_network_or_user_folder(self):
        source = mrpack(self.root / "embedded.mrpack", [self.good], embedded=True)
        _, report = self.analyze(source)
        self.assertEqual(len(report.rows), 1)
        self.assertEqual(report.rows[0].id, "good")
        self.assertIn("works", json.dumps(report.to_dict()).lower())
        self.assertFalse(any(command.argv[1] in ("fetch", "port") for command in report.analysis.commands))
        self.assert_unplayable(report)

    def test_curseforge_manifest_ids_resolve_from_user_instance_without_api_key(self):
        source = curseforge(self.root / "owned-cf.zip", [self.good])
        local = local_cf_instance(self.root / "owned CF instance", [self.good])
        entry, unresolved = self.analyze(source)
        self.assertEqual(entry.format, "curseforge")
        self.assertGreaterEqual(len(unresolved.rows), 1)
        self.assertTrue(any(row.status == "Unsupported" for row in unresolved.rows))
        resolved = self.library.analyze(entry.token, dependencies=local)
        self.assertTrue(any(row.id == "good" for row in resolved.rows))
        self.assertFalse(any(command.argv[1] in ("fetch", "port") for command in resolved.analysis.commands))
        self.assert_unplayable(resolved)

    def test_curseforge_modlist_cannot_silently_remove_manifest_only_entries(self):
        source = curseforge(self.root / "incomplete-cf.zip", [self.good], include_modlist=True, omitted_manifest=1)
        local = local_cf_instance(self.root / "owned instance", [self.good])
        _, report = self.analyze(source, local)
        self.assertGreaterEqual(len(report.rows), 2)
        self.assertTrue(any(row.status == "Unsupported" for row in report.rows))
        self.assertIn("101", json.dumps(report.to_dict()))
        self.assertIn("201", json.dumps(report.to_dict()))
        self.assert_unplayable(report)

    def test_renaming_an_unrelated_jar_to_a_curseforge_placeholder_cannot_prove_identity(self):
        source = curseforge(self.root / "opaque-cf.zip", [self.good])
        self.good.rename(self.user / "curseforge-100-200.jar")
        _, report = self.analyze(source, self.user)
        self.assertEqual(len(report.rows), 1)
        self.assertEqual(report.rows[0].status, "Unsupported")
        self.assertIn("missing-identity-mapping", json.dumps(report.to_dict()))
        self.assertFalse(any(mod.check for mod in report.analysis.mods))
        self.assert_unplayable(report)

    def test_missing_modrinth_files_remain_visible_as_unsupported_rows(self):
        source = mrpack(self.root / "missing.mrpack", [self.good], missing=2)
        _, report = self.analyze(source, self.user)
        self.assertEqual(len(report.rows), 3)
        missing = [row for row in report.rows if "missing-" in row.id or "missing-" in row.source or "missing-" in row.name]
        self.assertEqual(len(missing), 2)
        self.assertTrue(all(row.status == "Unsupported" for row in missing))
        self.assert_unplayable(report)

    def test_declared_hash_mismatch_does_not_accept_same_filename(self):
        source = mrpack(self.root / "wrong-hash.mrpack", [self.good], bad_hash=True)
        _, report = self.analyze(source, self.user)
        self.assertEqual(report.status, "Unsupported")
        self.assertEqual(len(report.rows), 1)
        self.assertEqual(report.rows[0].status, "Unsupported")
        self.assertIn("hash", json.dumps(report.to_dict()).lower())
        self.assert_unplayable(report)

    def test_sha512_only_index_resolves_renamed_local_file_without_losing_hash_evidence(self):
        source = mrpack(self.root / "sha512.mrpack", [self.good], hash_algorithm="sha512")
        self.good.rename(self.user / "renamed-download.jar")
        _, report = self.analyze(source, self.user)
        self.assertEqual(len(report.rows), 1)
        self.assertEqual(report.rows[0].id, "good")
        self.assertEqual(report.rows[0].status, "Requires porting")
        self.assertIn("sha512", json.dumps(report.to_dict()).lower())
        self.assert_unplayable(report)

    def test_sha512_mismatch_does_not_accept_same_filename(self):
        source = mrpack(self.root / "wrong-sha512.mrpack", [self.good], hash_algorithm="sha512", bad_hash=True)
        _, report = self.analyze(source, self.user)
        self.assertEqual(report.rows[0].status, "Unsupported")
        self.assertIn("hash", json.dumps(report.to_dict()).lower())
        self.assert_unplayable(report)

    def test_correct_sha1_cannot_hide_a_conflicting_known_sha512(self):
        source = mrpack(self.root / "conflicting.mrpack", [self.good], conflicting_hash=True)
        _, report = self.analyze(source, self.user)
        self.assertEqual(report.rows[0].status, "Unsupported")
        self.assertIn("hash", json.dumps(report.to_dict()).lower())
        self.assert_unplayable(report)

    def test_original_works_false_positive_retains_missing_dependency_and_unsupported_features(self):
        bad = make_jar(self.user / "bad.jar", mod_id="bad", depends={"missinglib": ">=2"},
                       mixins=True, invalid_class=True)
        source = mrpack(self.root / "unsafe.mrpack", [bad])
        _, report = self.analyze(source, self.user)
        row = report.rows[0]
        self.assertEqual(row.status, "Unsupported")
        self.assertIn("missinglib", row.missing_dependencies)
        self.assertEqual(report.analysis.mods[0].check.verdict, "works")
        self.assertIn("insufficient_evidence", json.dumps(report.to_dict()))
        self.assert_unplayable(report)

    def test_partial_data_carry_preserves_unsupported_rows_and_never_becomes_playable(self):
        bad = make_jar(self.user / "bad.jar", mod_id="bad", depends={"missinglib": "*"}, mixins=True)
        source = mrpack(self.root / "partial.mrpack", [self.good, bad])
        entry = self.library.import_pack(source)
        report = self.library.port(entry.token, dependencies=self.user)
        self.assertEqual(len(report.rows), 2)
        supported = next(row for row in report.rows if row.id == "good")
        unsupported = next(row for row in report.rows if row.id == "bad")
        self.assertTrue(supported.carried)
        self.assertTrue(Path(supported.output_path).is_dir())
        self.assertTrue(Path(supported.output_path).is_relative_to(self.launcher.game))
        self.assertEqual(unsupported.status, "Unsupported")
        self.assertFalse(unsupported.carried)
        self.assertIn("partial", report.summary.lower())
        self.assertFalse((self.launcher.game / "horizon-mods").exists())
        self.assert_unplayable(report)

    def test_packwiz_is_explicitly_unsupported_without_inventing_a_parser(self):
        entry, report = self.analyze(packwiz(self.root / "packwiz"))
        self.assertEqual(entry.format, "packwiz")
        self.assertEqual(report.status, "Unsupported")
        self.assertTrue(report.rows)
        self.assertIn("packwiz", json.dumps(report.to_dict()).lower())
        self.assertTrue(all(row.status == "Unsupported" for row in report.rows))
        self.assert_unplayable(report)

    def test_analysis_and_port_only_invoke_allowlisted_passive_rust_commands(self):
        source = mrpack(self.root / "owned.mrpack", [self.good])
        real_run = subprocess.run
        observed = []
        def capture(argv, *args, **kwargs):
            observed.append(tuple(map(str, argv)))
            return real_run(argv, *args, **kwargs)
        with patch("subprocess.run", side_effect=capture):
            entry = self.library.import_pack(source)
            report = self.library.port(entry.token, dependencies=self.user)
        self.assertTrue(observed)
        self.assertTrue(all(Path(argv[0]).name.startswith("horizon-port-pack") for argv in observed))
        self.assertTrue(all(argv[1] in ("import", "inventory", "check", "carry", "report") for argv in observed))
        self.assert_unplayable(report)

    def test_pack_storage_is_profile_isolated_and_existing_game_files_are_untouched(self):
        paths = [self.launcher.game / "saves/Owned/level.dat", self.launcher.game / "shaderpacks/existing.zip",
                 self.launcher.game / "horizon-mods/existing.hmod", self.launcher.game / "horizon-mods.txt"]
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"owned existing sentinel: " + path.name.encode())
        before = {path: digest(path) for path in paths}
        source = mrpack(self.root / "owned.mrpack", [self.good])
        entry = self.library.import_pack(source)
        report = self.library.port(entry.token, dependencies=self.user)
        first_source = entry.source
        self.launcher.add_profile("separate")
        self.assertEqual(self.library.imports(), [])
        with self.assertRaises(ValueError):
            self.library.analyze(entry.token)
        self.assertTrue(first_source.exists())
        self.assertEqual(before, {path: digest(path) for path in paths})
        self.assert_unplayable(report)

    def test_imported_pack_snapshot_survives_original_removal_and_detects_snapshot_edits(self):
        source = mrpack(self.root / "owned.mrpack", [self.good])
        entry = self.library.import_pack(source)
        self.assertNotEqual(entry.source, source)
        source.unlink()
        report = self.library.analyze(entry.token, dependencies=self.user)
        self.assertEqual(report.rows[0].id, "good")
        entry.source.write_bytes(entry.source.read_bytes() + b"owned snapshot edit")
        with self.assertRaises(ValueError):
            self.library.imports()

    def test_changed_generated_port_tree_is_demoted_on_load_and_export(self):
        entry = self.library.import_pack(mrpack(self.root / "owned.mrpack", [self.good]))
        report = self.library.port(entry.token, dependencies=self.user)
        self.assertTrue(report.rows[0].carried)
        output = Path(report.rows[0].output_path)
        data_file = next((output / "data").rglob("*.json"))
        data_file.write_text('{"owned":"changed data"}', encoding="utf-8")
        loaded = self.library.load_report(entry.token)
        self.assertEqual(loaded["rows"][0]["status"], "Unsupported")
        self.assertFalse(loaded["rows"][0]["carried"])
        self.assertFalse(loaded["playable_verified"])
        exported_path = self.root / "changed-export.json"
        self.library.export_report(entry.token, exported_path)
        exported = json.loads(exported_path.read_text(encoding="utf-8"))
        self.assertEqual(exported["rows"][0]["status"], "Unsupported")
        self.assertFalse(exported["rows"][0]["carried"])
        self.assertEqual(data_file.read_text(), '{"owned":"changed data"}')

    def test_symlinked_profile_parent_cannot_redirect_pack_import(self):
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.launcher.state / "profiles").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(str(error))
        self.launcher.add_profile("separate")
        with self.assertRaisesRegex(ValueError, "link|Link"):
            self.library.import_pack(mrpack(self.root / "owned.mrpack", [self.good]))
        self.assertEqual(list(outside.iterdir()), [])

    def test_partial_port_prunes_mod_whose_dependency_is_only_an_external_file(self):
        parent = make_jar(self.user / "parent.jar", mod_id="parent", depends={"external": "*"})
        make_jar(self.user / "external.jar", mod_id="external")
        entry = self.library.import_pack(mrpack(self.root / "missing-ensemble.mrpack", [parent]))
        report = self.library.port(entry.token, dependencies=self.user)
        self.assertEqual(len(report.rows), 1)
        row = report.rows[0]
        self.assertEqual(row.id, "parent")
        self.assertEqual(row.status, "Unsupported")
        self.assertFalse(row.carried)
        self.assertIn("external", row.missing_dependencies)
        self.assertNotIn("set", row.missing_dependencies)
        self.assert_unplayable(report)

    def test_export_json_and_text_preserve_original_evidence_and_unplayable_summary(self):
        source = mrpack(self.root / "missing.mrpack", [self.good], missing=1)
        entry, report = self.analyze(source, self.user)
        for format in ("json", "text"):
            output = self.root / ("report." + format)
            self.library.export_report(entry.token, output, format)
            content = output.read_text(encoding="utf-8")
            self.assertIn("good", content)
            self.assertIn("missing-0", content)
            self.assertIn("Unsupported", content)
            if format == "json":
                exported = json.loads(content)
                self.assertFalse(exported["playable_verified"])
                self.assertEqual(len(exported["rows"]), len(report.rows))

    def test_saved_pack_report_cannot_forge_playable_or_tested_success(self):
        entry, report = self.analyze(mrpack(self.root / "owned.mrpack", [self.good]), self.user)
        saved = report.report_file
        data = json.loads(saved.read_text(encoding="utf-8"))
        data["status"] = "Tested successfully"
        data["playable_verified"] = True
        data["play_enabled"] = True
        for row in data["rows"]:
            row["status"] = "Native compatibility"
        saved.write_text(json.dumps(data), encoding="utf-8")
        try:
            loaded = self.library.load_report(entry.token)
        except ValueError:
            return  # A rejected tampered receipt is an explicit safe outcome.
        self.assertFalse(loaded["playable_verified"])
        self.assertFalse(loaded.get("play_enabled", False))
        self.assertNotIn(loaded["status"], FORBIDDEN)
        self.assertTrue(all(row["status"] not in FORBIDDEN for row in loaded["rows"]))


if __name__ == "__main__":
    unittest.main()
