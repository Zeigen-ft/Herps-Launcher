"""Passive preflight regression fixtures are generated locally, never executed."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from herps_launcher.javamods.metadata import (
    JarMetadata, _class_metadata_readable, assess_dependencies, inspect_jar,
    version_matches,
)
from tools.make_javamods_fixtures import make_jar


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def codes(self, diagnostics):
        return {diagnostic.code for diagnostic in diagnostics}

    def test_supported_loader_metadata_preserves_identity_and_raw_constraints(self):
        for loader in ("fabric", "forge", "neoforge"):
            with self.subTest(loader=loader):
                jar = make_jar(self.root / f"{loader}.jar", loader=loader, depends={"library": ">=2"})
                result = inspect_jar(jar)
                self.assertEqual(result.mod_id, "demo")
                self.assertEqual(result.loader, loader)
                self.assertEqual(result.required_dependencies["library"], ">=2")
                self.assertEqual(result.required_dependencies["minecraft"], "26.3")
                self.assertEqual(result.diagnostics, [])
                self.assertEqual(len(result.sha256), 64)
                self.assertIn("archive_entries", result.raw)

    def test_false_positive_works_fixture_exposes_all_suppressed_evidence(self):
        result = inspect_jar(make_jar(self.root / "false-positive.jar", depends={"missinglib": ">=2"},
                                      mixins=True, access=True, invalid_class=True))
        self.assertEqual(result.class_count, 1)
        self.assertEqual(result.unreadable_classes, ("demo/Owned.class",))
        self.assertIn("owned.mixins.json", result.mixins)
        self.assertIn("owned.accesswidener", result.access_changes)
        codes = self.codes(result.diagnostics + assess_dependencies(result, {}))
        self.assertTrue({"unreadable_classes", "required_mixins", "unsupported_feature", "missing_dependency"} <= codes)

    def test_missing_dependency_and_version_mismatch_are_separate(self):
        result = inspect_jar(make_jar(self.root / "deps.jar", depends={"present": ">=2", "missing": "*"}, minecraft="1.21.1"))
        diagnostics = assess_dependencies(result, {"present": JarMetadata(mod_id="present", version="1")})
        self.assertIn("missing_dependency", self.codes(diagnostics))
        self.assertEqual(sum(d.code == "version_mismatch" for d in diagnostics), 2)

    def test_unknown_version_constraint_is_insufficient_evidence(self):
        result = inspect_jar(make_jar(self.root / "unknown.jar", depends={"library": "~2.0"}))
        diagnostics = assess_dependencies(result, {"library": JarMetadata(mod_id="library", version="2.1")})
        self.assertIn("insufficient_evidence", self.codes(diagnostics))

    def test_required_loader_never_becomes_a_working_java_bridge(self):
        result = inspect_jar(make_jar(self.root / "loader.jar", depends={"fabricloader": ">=0.16"}))
        diagnostics = assess_dependencies(result, {"fabricloader": JarMetadata(version="0.16")})
        self.assertIn("unsupported_feature", self.codes(diagnostics))
        self.assertIn("no working Java bridge", diagnostics[0].message)

    def test_manifest_mixins_and_forge_access_transformer_are_detected(self):
        path = make_jar(self.root / "manifest.jar", loader="forge", access=True)
        with zipfile.ZipFile(path, "a") as zipped:
            zipped.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\r\nMixinConfigs: one.json,\r\n two.json\r\n")
        result = inspect_jar(path)
        self.assertEqual(result.mixins, ("one.json", "two.json"))
        self.assertIn("META-INF/accesstransformer.cfg", result.access_changes)

    def test_nested_jar_needs_separate_evidence(self):
        path = make_jar(self.root / "nested.jar")
        with zipfile.ZipFile(path, "a") as zipped:
            zipped.writestr("META-INF/jars/nested.jar", b"never run")
        self.assertIn("unsupported_feature", self.codes(inspect_jar(path).diagnostics))

    def test_java_entrypoints_and_coremods_cannot_hide_in_data_archives(self):
        path = self.root / "hooks.jar"
        with zipfile.ZipFile(path, "w") as zipped:
            zipped.writestr("fabric.mod.json", json.dumps({"id": "demo", "version": "1", "entrypoints": {"main": ["example.Owned"]}}))
            zipped.writestr("META-INF/coremods.json", '{"owned":"owned.js"}')
        diagnostics = inspect_jar(path).diagnostics
        self.assertEqual(sum(d.code == "unsupported_feature" for d in diagnostics), 2)

    def test_missing_malformed_and_ambiguous_metadata_fail_closed(self):
        fixtures = ({}, {"fabric.mod.json": "[]"}, {"fabric.mod.json": "{"},
                    {"fabric.mod.json": json.dumps({"id": "demo", "version": "1"}), "META-INF/mods.toml": "[[mods]]"})
        for index, files in enumerate(fixtures):
            path = self.root / f"bad-{index}.jar"
            with zipfile.ZipFile(path, "w") as zipped:
                for name, data in files.items():
                    zipped.writestr(name, data)
            self.assertIn("insufficient_evidence", self.codes(inspect_jar(path).diagnostics))

    def test_archive_traversal_is_refused_before_metadata_analysis(self):
        path = self.root / "traversal.jar"
        with zipfile.ZipFile(path, "w") as zipped:
            zipped.writestr("../escape", "never extracted")
        self.assertIn("insufficient_evidence", self.codes(inspect_jar(path).diagnostics))
        self.assertFalse((self.root.parent / "escape").exists())

    def test_missing_or_corrupt_jar_does_not_raise_a_success_result(self):
        path = self.root / "corrupt.jar"
        path.write_bytes(b"not a zip")
        for jar in (path, self.root / "absent.jar"):
            self.assertIn("insufficient_evidence", self.codes(inspect_jar(jar).diagnostics))

    def test_missing_minecraft_range_remains_unknown(self):
        metadata = JarMetadata(mod_id="demo", version="1")
        self.assertIn("insufficient_evidence", self.codes(assess_dependencies(metadata, {})))

    def test_multiple_forge_mod_records_do_not_silently_ignore_extra_mods(self):
        path = self.root / "multiple.jar"
        with zipfile.ZipFile(path, "w") as zipped:
            zipped.writestr("META-INF/mods.toml", 'license="MIT"\n[[mods]]\nmodId="one"\nversion="1"\n[[mods]]\nmodId="two"\nversion="1"\n')
        self.assertIn("insufficient_evidence", self.codes(inspect_jar(path).diagnostics))

    def test_duplicate_dependency_keys_cannot_hide_a_missing_dependency(self):
        path = self.root / "duplicate.json.jar"
        with zipfile.ZipFile(path, "w") as zipped:
            zipped.writestr("fabric.mod.json", '{"id":"demo","version":"1","depends":{"missing":"*"},"depends":{"minecraft":"26.3"}}')
        result = inspect_jar(path)
        self.assertIn("insufficient_evidence", self.codes(result.diagnostics))
        self.assertIn("Duplicate JSON key", result.diagnostics[0].message)
        self.assertIn("fabric.mod.json", result.raw["metadata_text"])

    def test_forge_optional_dependency_is_not_required(self):
        path = self.root / "optional.jar"
        with zipfile.ZipFile(path, "w") as zipped:
            zipped.writestr("META-INF/mods.toml", 'license="MIT"\n[[mods]]\nmodId="demo"\nversion="1"\n[[dependencies.demo]]\nmodId="optional"\nmandatory=false\nversionRange="*"\n')
        self.assertNotIn("optional", inspect_jar(path).required_dependencies)

    def test_empty_dependency_constraint_is_incomplete_evidence(self):
        result = inspect_jar(make_jar(self.root / "empty-range.jar", minecraft=""))
        self.assertIn("insufficient_evidence", self.codes(result.diagnostics))


class VersionTests(unittest.TestCase):
    def test_numeric_exact_comparators_wildcard_and_maven_intervals(self):
        for version, expression, expected in (
            ("26.3", "26.3", True), ("26.3", "26.3.0", True), ("26.3", "1.21.1", False),
            ("2.1", ">=2 <3", True), ("3", ">=2 <3", False), ("2.1", "[2,3)", True),
            ("3", "[2,3)", False), ("2", "(,2]", True), ("2", "[2]", True),
            ("2.1", "2.x", True), ("3", "2.*", False), ("26.3", "1.21 || 26.3", True),
            ("1", ["2", "1"], True), ("1", ["2", "3"], False),
            ("2.1", "^2", None), ("2.1-SNAPSHOT", ">=2", None), ("1", "nonsense", None),
        ):
            with self.subTest(version=version, expression=expression):
                self.assertIs(version_matches(version, expression), expected)


class ClassStructureTests(unittest.TestCase):
    @staticmethod
    def minimal():
        # Headers + constant pool only; no methods or Code attributes.
        pool = b"\x01\x00\x05Owned\x07\x00\x01\x01\x00\x10java/lang/Object\x07\x00\x03"
        return b"\xca\xfe\xba\xbe" + struct.pack(">HHH", 0, 69, 5) + pool + struct.pack(">HHHHHHH", 0x21, 2, 4, 0, 0, 0, 0)

    def test_structural_metadata_can_be_read_without_executing_code(self):
        self.assertTrue(_class_metadata_readable(self.minimal()))

    def test_truncated_invalid_and_future_class_metadata_is_unreadable(self):
        valid = self.minimal()
        self.assertFalse(_class_metadata_readable(valid[:-1]))
        self.assertFalse(_class_metadata_readable(b"invalid"))
        self.assertFalse(_class_metadata_readable(valid[:6] + struct.pack(">H", 70) + valid[8:]))


if __name__ == "__main__":
    unittest.main()
