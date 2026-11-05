"""Passive inspection safety using original, non-executable fixture archives."""
from pathlib import Path
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

from herps_launcher.core import archive
from tools.inspect_targeted_packs import (FUNCRAFT_NAME, FUNCRAFT_SHA256,
    FUNCRAFT_VERSION, inspect_funcraft, jar_inventory)


class TargetedInspectionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def jar(self, entries):
        stream = io.BytesIO()
        with ZipFile(stream, "w") as zipped:
            for name, value in entries:
                zipped.writestr(name, value)
        return stream.getvalue()

    def test_target_archive_hash_is_required_before_inspecting_claimed_identity(self):
        path = self.root / "FunCraft.zip"
        path.write_bytes(b"not the uploaded pack")
        with self.assertRaisesRegex(ValueError, "exact SHA-256"):
            inspect_funcraft(path)

    def test_html_names_are_joined_by_project_id_not_display_order(self):
        path = self.root / "owned.zip"
        manifest = {"name": FUNCRAFT_NAME, "version": FUNCRAFT_VERSION, "minecraft": {},
            "files": [{"projectID": 1, "fileID": 11}, {"projectID": 2, "fileID": 22}]}
        with ZipFile(path, "w") as zipped:
            zipped.writestr("manifest.json", json.dumps(manifest))
            zipped.writestr("modlist.html", '<a href="https://example.org/mc-mods/2">Second</a><a href="https://example.org/mc-mods/1">First</a>')
        # Only synthetic unit input bypasses the production exact-input guard.
        with patch("tools.inspect_targeted_packs.digest", return_value=FUNCRAFT_SHA256):
            report = inspect_funcraft(path)
        self.assertEqual([r["name"] for r in report["manifest_entries"]], ["First", "Second"])
        self.assertTrue(all(r["classification"] == "BLOCKED" for r in report["manifest_entries"]))
        self.assertFalse(report["java_executed"])

    def test_invalid_directory_mode_is_recorded_without_relaxing_import(self):
        directory = ZipInfo("META-INF/maven/")
        directory.external_attr = 0o177777 << 16
        data = self.jar([(directory, b""), ("mcmod.info", '[{"modid":"owned","version":"1"}]')])
        report = jar_inventory(data, "owned.jar", self.root)
        self.assertEqual(report["directory_mode_anomalies"][0]["path"], "META-INF/maven/")
        self.assertEqual(report["classification"], "BLOCKED")
        path = self.root / "runtime.jar"
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "Unsafe archive"):
            archive(path)

    def test_traversal_and_link_members_are_never_extracted(self):
        link = ZipInfo("link")
        link.external_attr = 0o120777 << 16
        for name, value in [("../outside.txt", b"private"), (link, b"../outside.txt")]:
            with self.subTest(name=str(name)):
                with self.assertRaises(ValueError):
                    jar_inventory(self.jar([(name, value)]), "owned.jar", self.root)
        self.assertFalse((self.root.parent / "outside.txt").exists())

    def test_pom_dependency_and_notice_scope_are_preserved_without_success_claim(self):
        pom = '''<project xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>owned</artifactId>
        <licenses><license><name>MIT</name></license></licenses><dependencies>
        <dependency><groupId>other</groupId><artifactId>required</artifactId><version>2</version></dependency>
        </dependencies></project>'''
        data = self.jar([("META-INF/maven/owned/pom.xml", pom),
            ("shaded/LICENSE.txt", "Fixture notice"), ("owned/Entry.class", b"not executable net/minecraftforge/fml/common/Mod;")])
        report = jar_inventory(data, "owned.jar", self.root)
        self.assertEqual(report["maven"][0]["dependencies"][0]["artifactId"], "required")
        self.assertEqual(report["notice_files"][0]["path"], "shaded/LICENSE.txt")
        self.assertEqual(report["annotation_candidates"], ["owned/Entry.class"])
        self.assertEqual(report["classification"], "BLOCKED")
