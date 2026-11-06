"""Adapter regressions use owned local JARs; Java and mod code are never run."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from herps_launcher.core import Launcher
from herps_launcher.javamods.adapter import PortPackAdapter
from tools.make_javamods_fixtures import make_jar


SUCCESS_STATUSES = {"Native compatibility", "Tested successfully", "Compatible through Java bridge"}
BINARY = Path(os.environ["HERPS_TEST_PORT_PACK"]) if os.environ.get("HERPS_TEST_PORT_PACK") else None


def codes(result):
    return {d.code for d in result.diagnostics}


class AdapterFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="herps-adapter-unit-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.launcher = Launcher(self.root / "support")
        self.jar = make_jar(self.root / "owned.jar")
        self.executable = self.root / "owned-port-pack-fixture"
        self.executable.write_text("owned executable path; subprocess is mocked", encoding="utf-8")
        self.executable.chmod(0o700)

    def adapter(self):
        return PortPackAdapter(self.launcher, executable=self.executable, timeout=1)

    def test_missing_binary_is_unsupported_with_insufficient_evidence(self):
        adapter = PortPackAdapter(self.launcher, executable=self.root / "missing-tool")
        result = adapter.check(self.jar)
        self.assertEqual(result.status, "Unsupported")
        self.assertIn("insufficient_evidence", codes(result) | codes(result.mods[0]))
        self.assertFalse(result.commands)
        self.assertNotIn(result.status, SUCCESS_STATUSES)

    def test_malformed_json_cannot_become_a_successful_status(self):
        def malformed(argv, **kwargs):
            out = Path(argv[3])
            out.mkdir(parents=True, exist_ok=True)
            (out / "check.json").write_text('{"verdict":', encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "fixture says Works", "")

        with patch("herps_launcher.javamods.adapter.subprocess.run", side_effect=malformed):
            result = self.adapter().check(self.jar)
        self.assertEqual(result.status, "Unsupported")
        self.assertIn("insufficient_evidence", codes(result) | codes(result.mods[0]))
        self.assertEqual(result.commands[-1].exit_code, 0)
        self.assertIn("fixture says Works", result.commands[-1].stdout)

    def test_nonzero_subprocess_exit_retains_stdout_stderr_and_exit_code(self):
        with patch("herps_launcher.javamods.adapter.subprocess.run", return_value=
                   subprocess.CompletedProcess(["fixture"], 7, "partial output", "owned failure")):
            result = self.adapter().check(self.jar)
        self.assertEqual(result.status, "Unsupported")
        command = result.commands[-1]
        self.assertEqual(command.exit_code, 7)
        self.assertIn("partial output", command.stdout)
        self.assertIn("owned failure", command.stderr)
        self.assertIn("insufficient_evidence", codes(result) | codes(result.mods[0]))

    def test_zero_exit_without_json_is_insufficient_evidence(self):
        with patch("herps_launcher.javamods.adapter.subprocess.run", return_value=
                   subprocess.CompletedProcess(["fixture"], 0, "Works", "")):
            result = self.adapter().check(self.jar)
        self.assertEqual(result.status, "Unsupported")
        self.assertIn("insufficient_evidence", codes(result) | codes(result.mods[0]))
        self.assertIsNone(result.mods[0].check)

    def test_contradictory_works_identity_cannot_become_a_successful_status(self):
        check = {
            "mod_id": "othermod", "name": "Unrelated fixture", "version": "999",
            "loader": "fabric", "license": "MIT", "verdict": "works",
            "summary": "Content only: 1 recipe port.", "ports": ["1 recipe"],
            "skipped": [], "depends": [], "namespaces": ["othermod"],
            "code": {"classes": 0, "features": {}, "events": [], "examples": {}},
        }

        def contradictory(argv, **kwargs):
            out = Path(argv[3])
            out.mkdir(parents=True, exist_ok=True)
            (out / "check.json").write_text(json.dumps(check), encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "Works", "")

        with patch("herps_launcher.javamods.adapter.subprocess.run", side_effect=contradictory):
            result = self.adapter().check(self.jar)
        self.assertEqual(result.status, "Unsupported")
        self.assertIn("insufficient_evidence", codes(result) | codes(result.mods[0]))
        self.assertEqual(result.mods[0].check.mod_id, "othermod")

    def test_timeout_cannot_be_reported_as_compatibility_or_test_success(self):
        timeout = subprocess.TimeoutExpired(["fixture"], 1, output=b"partial stdout", stderr=b"partial stderr")
        with patch("herps_launcher.javamods.adapter.subprocess.run", side_effect=timeout):
            result = self.adapter().check(self.jar)
        self.assertEqual(result.status, "Unsupported")
        self.assertTrue(result.commands)
        self.assertIn("partial stdout", result.commands[-1].stdout)
        self.assertIn("insufficient_evidence", codes(result) | codes(result.mods[0]))

    def test_restricted_licence_requires_acknowledgement_before_carrying_check(self):
        jar = make_jar(self.root / "restricted.jar", license="CC-BY-NC-ND-4.0")
        with patch("herps_launcher.javamods.adapter.subprocess.run") as run:
            result = self.adapter().check(jar)
        run.assert_not_called()
        self.assertEqual(result.status, "Unsupported")
        self.assertFalse(result.commands)
        self.assertTrue(any("licen" in d.message.lower() or "restricted" in d.message.lower()
                            for d in result.mods[0].diagnostics + result.diagnostics))


@unittest.skipUnless(BINARY is not None and BINARY.is_file(),
                     "Set HERPS_TEST_PORT_PACK to the built pinned executable for real CLI regressions")
class PortPackIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="herps-adapter-real-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.launcher = Launcher(self.root / "support with spaces")
        self.adapter = PortPackAdapter(self.launcher, executable=BINARY, timeout=30)

    def mrpack(self, filename, sha1):
        source = self.root / "owned.mrpack"
        index = {
            "formatVersion": 1, "game": "minecraft", "versionId": "1", "name": "Owned local fixture",
            "dependencies": {"minecraft": "26.3"},
            "files": [{"path": f"mods/{filename}", "hashes": {"sha1": sha1},
                       "downloads": [], "fileSize": 1}],
        }
        with zipfile.ZipFile(source, "w") as zipped:
            zipped.writestr("modrinth.index.json", json.dumps(index))
        return source

    def assert_works_is_not_success(self, result):
        self.assertEqual(result.status, "Unsupported")
        mod = result.mods[0]
        self.assertEqual(mod.status, "Unsupported")
        self.assertNotIn(mod.status, SUCCESS_STATUSES)
        self.assertIsNotNone(mod.check, "Regression must retain the actual Rust finding")
        self.assertEqual(mod.check.verdict, "works")
        self.assertIn("insufficient_evidence", codes(result) | codes(mod))
        serialized = result.to_dict()
        self.assertIn('"verdict": "works"', json.dumps(serialized["raw_evidence"]))
        self.assertIsNone(serialized["test_execution"])
        self.assertFalse(serialized["java_bridge_available"])
        return mod

    def test_actual_works_with_missing_dependency_stays_unsupported(self):
        jar = make_jar(self.root / "missingdep.jar", depends={"missinglib": ">=2"})
        result = self.adapter.check(jar)
        mod = self.assert_works_is_not_success(result)
        self.assertIn("missing_dependency", codes(mod))
        self.assertTrue(any("missinglib" in d.message for d in mod.diagnostics))

    def test_actual_works_with_unreadable_class_stays_unsupported(self):
        jar = make_jar(self.root / "badclass.jar", invalid_class=True)
        result = self.adapter.check(jar)
        mod = self.assert_works_is_not_success(result)
        self.assertIn("unreadable_classes", codes(mod))
        self.assertEqual(mod.check.code.classes, 0)
        self.assertEqual(mod.metadata.class_count, 1)
        self.assertTrue(mod.metadata.unreadable_classes)

    def test_actual_works_with_required_mixins_stays_unsupported(self):
        jar = make_jar(self.root / "mixins.jar", mixins=True)
        mod = self.assert_works_is_not_success(self.adapter.check(jar))
        self.assertIn("required_mixins", codes(mod))

    def test_actual_works_with_access_widener_stays_unsupported(self):
        jar = make_jar(self.root / "access.jar", access=True)
        mod = self.assert_works_is_not_success(self.adapter.check(jar))
        self.assertIn("unsupported_feature", codes(mod))

    def test_actual_works_with_minecraft_version_mismatch_stays_unsupported(self):
        jar = make_jar(self.root / "wrong-version.jar", minecraft="1.20.1")
        mod = self.assert_works_is_not_success(self.adapter.check(jar))
        self.assertIn("version_mismatch", codes(mod))

    def test_user_dependency_wrong_version_is_not_accepted_by_id_alone(self):
        dependencies = self.root / "dependencies"
        make_jar(dependencies / "lib.jar", mod_id="library", version="1")
        jar = make_jar(self.root / "requires-lib.jar", depends={"library": ">=2"})
        result = self.adapter.check(jar, dependencies=dependencies)
        mod = self.assert_works_is_not_success(result)
        self.assertIn("version_mismatch", codes(mod))

    def test_pure_content_requires_porting_but_never_claims_native_or_tested(self):
        jar = make_jar(self.root / "content.jar")
        result = self.adapter.check(jar)
        self.assertEqual(result.status, "Requires porting")
        self.assertEqual(result.mods[0].status, "Requires porting")
        self.assertEqual(result.mods[0].check.verdict, "works")
        self.assertIsNone(result.to_dict()["test_execution"])
        self.assertFalse(result.to_dict()["java_bridge_available"])

    def test_profile_and_each_run_have_separate_workspaces(self):
        jar = make_jar(self.root / "owned.jar")
        first_game = self.launcher.game
        first = self.adapter.check(jar)
        repeated = self.adapter.check(jar)
        self.launcher.add_profile("separate")
        second_game = self.launcher.game
        second = self.adapter.check(jar)
        self.assertNotEqual(first.workspace, repeated.workspace)
        self.assertNotEqual(first.workspace, second.workspace)
        self.assertTrue(first.workspace.is_relative_to(first_game))
        self.assertTrue(second.workspace.is_relative_to(second_game))
        self.assertFalse(second.workspace.is_relative_to(first_game))

    def test_local_port_retains_data_carry_without_successful_gameplay_claim(self):
        jar = make_jar(self.root / "owned.jar")
        result = self.adapter.port(jar)
        self.assertEqual(result.status, "Requires porting")
        self.assertTrue(list(result.workspace.rglob("horizon-mod.toml")))
        self.assertNotIn(result.status, SUCCESS_STATUSES)
        self.assertIsNone(result.to_dict()["test_execution"])
        self.assertFalse((self.launcher.game / "horizon-mods").exists())

    def test_instance_analysis_preserves_every_mod_and_missing_dependencies(self):
        instance = self.root / "instance"
        make_jar(instance / "mods" / "good.jar", mod_id="good")
        make_jar(instance / "mods" / "bad.jar", mod_id="bad", depends={"absent": "*"})
        result = self.adapter.analyze_pack(instance)
        self.assertEqual(len(result.mods), 2)
        self.assertEqual(result.status, "Unsupported")
        self.assertTrue(any("missing_dependency" in codes(mod) for mod in result.mods))
        raw = result.to_dict()["raw_evidence"]
        self.assertIn("inventory", json.dumps(raw))
        self.assertIn("coverage", json.dumps(raw))

    def test_missing_pack_jar_remains_an_unsupported_record_without_download(self):
        source = self.root / "owned.mrpack"
        index = {
            "formatVersion": 1, "game": "minecraft", "versionId": "1", "name": "Owned missing fixture",
            "dependencies": {"minecraft": "26.3", "fabric-loader": "0.16"},
            "files": [{"path": "mods/missing.jar", "hashes": {"sha1": "0" * 40},
                       "downloads": [], "fileSize": 1}],
        }
        with zipfile.ZipFile(source, "w") as zipped:
            zipped.writestr("modrinth.index.json", json.dumps(index))
        result = self.adapter.analyze_pack(source)
        self.assertEqual(result.status, "Unsupported")
        self.assertEqual(len(result.mods), 1)
        self.assertEqual(result.mods[0].status, "Unsupported")
        self.assertIsNone(result.mods[0].metadata)
        self.assertIn("insufficient_evidence", codes(result) | codes(result.mods[0]))
        self.assertFalse(any(command.argv[1] in {"fetch", "port"} for command in result.commands))

    def test_mrpack_resolves_user_file_by_declared_hash_with_different_filename(self):
        dependency_dir = self.root / "user files"
        jar = make_jar(dependency_dir / "download-renamed.jar")
        source = self.mrpack("original-name.jar", hashlib.sha1(jar.read_bytes()).hexdigest())
        result = self.adapter.analyze_pack(source, dependencies=dependency_dir)
        self.assertEqual(result.status, "Requires porting")
        self.assertEqual(len(result.mods), 1)
        self.assertEqual(result.mods[0].metadata.mod_id, "demo")
        self.assertEqual(result.mods[0].metadata.sha256, hashlib.sha256(jar.read_bytes()).hexdigest())
        self.assertFalse(any(command.argv[1] in {"fetch", "port"} for command in result.commands))

    def test_mrpack_same_filename_with_wrong_hash_is_not_accepted(self):
        dependency_dir = self.root / "user files"
        make_jar(dependency_dir / "required.jar")
        source = self.mrpack("required.jar", "0" * 40)
        result = self.adapter.analyze_pack(source, dependencies=dependency_dir)
        self.assertEqual(result.status, "Unsupported")
        self.assertEqual(len(result.mods), 1)
        self.assertIn("hash_mismatch", codes(result) | codes(result.mods[0]))
        self.assertIsNone(result.mods[0].metadata)
        self.assertFalse(any(command.argv[1] in {"fetch", "port"} for command in result.commands))

    def test_uppercase_declared_sha1_matches_the_same_local_file(self):
        dependency_dir = self.root / "user files"
        jar = make_jar(dependency_dir / "renamed.jar")
        source = self.mrpack("owned.jar", hashlib.sha1(jar.read_bytes()).hexdigest().upper())
        result = self.adapter.analyze_pack(source, dependencies=dependency_dir)
        self.assertEqual(len(result.mods), 1)
        self.assertIsNotNone(result.mods[0].metadata)
        self.assertNotIn("hash_mismatch", codes(result) | codes(result.mods[0]))
        self.assertEqual(result.mods[0].metadata.sha256, hashlib.sha256(jar.read_bytes()).hexdigest())

    def test_fully_local_pack_port_uses_real_carry_without_claiming_playability(self):
        dependency_dir = self.root / "user files"
        jar = make_jar(dependency_dir / "owned.jar")
        source = self.mrpack("owned.jar", hashlib.sha1(jar.read_bytes()).hexdigest())
        result = self.adapter.port(source, dependencies=dependency_dir)
        self.assertEqual(result.status, "Requires porting")
        self.assertEqual(len(result.mods), 1)
        port_path = result.mods[0].port_path
        self.assertIsNotNone(port_path)
        self.assertTrue((Path(port_path) / "horizon-mod.toml").is_file())
        self.assertTrue(Path(port_path).is_relative_to(result.workspace))
        subcommands = [command.argv[1] for command in result.commands]
        self.assertIn("carry", subcommands)
        self.assertNotIn("fetch", subcommands)
        self.assertNotIn("port", subcommands)
        self.assertFalse(result.to_dict()["playable_verified"])
        self.assertIsNone(result.to_dict()["test_execution"])

    def test_standalone_port_cannot_prove_carry_of_satisfied_dependency_ensemble(self):
        dependency_dir = self.root / "dependencies"
        make_jar(dependency_dir / "library.jar", mod_id="library")
        jar = make_jar(self.root / "parent.jar", depends={"library": "*"})
        result = self.adapter.port(jar, dependencies=dependency_dir)
        mod = self.assert_works_is_not_success(result)
        self.assertIsNone(mod.port_path)
        self.assertTrue(any("isolation" in d.message.lower() and "pack" in d.message.lower()
                            for d in mod.diagnostics))

    def test_works_cannot_hide_kept_custom_recipes_or_unreadable_carry_files(self):
        jar = make_jar(self.root / "owned.jar")
        original_run = subprocess.run
        for field, value in (("recipes_kept", ["owned:custom"]),
                             ("unreadable", {"data/demo/recipe/custom.json": "cannot decode"})):
            with self.subTest(field=field):
                def inject_carry_gap(argv, **kwargs):
                    completed = original_run(argv, **kwargs)
                    if argv[1] == "check" and completed.returncode == 0:
                        artifact = Path(argv[3]) / "carry-report.json"
                        carry = json.loads(artifact.read_text(encoding="utf-8"))
                        carry[field] = value
                        artifact.write_text(json.dumps(carry), encoding="utf-8")
                    return completed
                with patch("herps_launcher.javamods.adapter.subprocess.run", side_effect=inject_carry_gap):
                    result = self.adapter.check(jar)
                mod = self.assert_works_is_not_success(result)
                self.assertIn("unsupported_feature", codes(mod))
                self.assertEqual(mod.raw_evidence["carry"][field], value)

    def test_unknown_inventory_class_or_confidence_cannot_hide_behind_works(self):
        instance = self.root / "instance"
        make_jar(instance / "mods" / "owned.jar")
        original_run = subprocess.run
        for field in ("class", "confidence"):
            with self.subTest(field=field):
                def inject_unknown_inventory(argv, **kwargs):
                    completed = original_run(argv, **kwargs)
                    if argv[1] == "inventory" and completed.returncode == 0:
                        artifact = Path(argv[2]) / "inventory.json"
                        inventory = json.loads(artifact.read_text(encoding="utf-8"))
                        inventory[0][field] = "unknown"
                        artifact.write_text(json.dumps(inventory), encoding="utf-8")
                    return completed
                with patch("herps_launcher.javamods.adapter.subprocess.run", side_effect=inject_unknown_inventory):
                    result = self.adapter.analyze_pack(instance)
                mod = self.assert_works_is_not_success(result)
                self.assertEqual(mod.raw_evidence["inventory"][field], "unknown")

    def test_unreadable_dependency_blocks_apparently_successful_parent(self):
        dependency_dir = self.root / "dependencies"
        make_jar(dependency_dir / "library.jar", mod_id="library", invalid_class=True)
        jar = make_jar(self.root / "parent.jar", depends={"library": "*"})
        result = self.adapter.check(jar, dependencies=dependency_dir)
        self.assert_works_is_not_success(result)
        self.assertTrue(any("library" in d.message for d in result.mods[0].diagnostics))

    def test_readable_java_class_in_dependency_is_not_treated_as_data_only(self):
        dependency_dir = self.root / "dependencies"
        jar = make_jar(dependency_dir / "library.jar", mod_id="library")
        # Owned class-file structural metadata, no methods or executable bodies.
        pool = b"\x01\x00\x05Owned\x07\x00\x01\x01\x00\x10java/lang/Object\x07\x00\x03"
        header = b"\xca\xfe\xba\xbe" + struct.pack(">HHH", 0, 69, 5) + pool
        with zipfile.ZipFile(jar, "a") as zipped:
            zipped.writestr("library/Owned.class", header + struct.pack(">HHHHHHH", 0x21, 2, 4, 0, 0, 0, 0))
        parent = make_jar(self.root / "parent.jar", depends={"library": "*"})
        result = self.adapter.check(parent, dependencies=dependency_dir)
        self.assert_works_is_not_success(result)
        self.assertTrue(any("library" in d.message for d in result.mods[0].diagnostics))

    def test_required_mixins_in_dependency_block_apparently_successful_parent(self):
        dependency_dir = self.root / "dependencies"
        make_jar(dependency_dir / "library.jar", mod_id="library", mixins=True)
        jar = make_jar(self.root / "parent.jar", depends={"library": "*"})
        result = self.adapter.check(jar, dependencies=dependency_dir)
        self.assert_works_is_not_success(result)
        self.assertTrue(any("library" in d.message for d in result.mods[0].diagnostics))

    def test_missing_transitive_dependency_blocks_apparently_successful_parent(self):
        dependency_dir = self.root / "dependencies"
        make_jar(dependency_dir / "library.jar", mod_id="library", depends={"missingtransitive": "*"})
        jar = make_jar(self.root / "parent.jar", depends={"library": "*"})
        result = self.adapter.check(jar, dependencies=dependency_dir)
        self.assert_works_is_not_success(result)
        self.assertTrue(any("missingtransitive" in d.message for d in result.mods[0].diagnostics))

    def test_duplicate_dependency_ids_are_ambiguous_not_silently_selected(self):
        dependency_dir = self.root / "dependencies"
        make_jar(dependency_dir / "first.jar", mod_id="library", version="1")
        make_jar(dependency_dir / "second.jar", mod_id="library", version="2")
        jar = make_jar(self.root / "parent.jar", depends={"library": "*"})
        result = self.adapter.check(jar, dependencies=dependency_dir)
        self.assertEqual(result.status, "Unsupported")
        self.assertIn("insufficient_evidence", codes(result))
        self.assertTrue(any("duplicate" in d.message.lower() and "library" in d.message
                            for d in result.diagnostics))

    def test_pack_archive_path_traversal_is_refused_before_backend(self):
        source = self.mrpack("owned.jar", "0" * 40)
        with zipfile.ZipFile(source, "a") as zipped:
            zipped.writestr("../escaped.txt", "owned fixture")
        result = self.adapter.analyze_pack(source)
        self.assertEqual(result.status, "Unsupported")
        self.assertFalse(result.commands)
        self.assertFalse((self.root / "escaped.txt").exists())
        self.assertIn("insufficient_evidence", codes(result))

    def test_symlinked_profile_workspace_cannot_escape_profile(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.launcher.game.mkdir(parents=True, exist_ok=True)
        link = self.launcher.game / "java-mods"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Host cannot create directory symlinks: {error}")
        jar = make_jar(self.root / "owned.jar")
        with self.assertRaisesRegex(ValueError, "[Ll]ink"):
            self.adapter.check(jar)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_profile_ancestor_cannot_escape_profile(self):
        outside = self.root / "outside"
        outside.mkdir()
        profiles = self.launcher.state / "profiles"
        try:
            profiles.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Host cannot create directory symlinks: {error}")
        self.launcher.add_profile("separate")
        jar = make_jar(self.root / "owned.jar")
        with self.assertRaisesRegex(ValueError, "[Ll]ink"):
            self.adapter.check(jar)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
