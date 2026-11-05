"""Untrusted ZIP handling and actual export/reassembly; owned fixtures only."""
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo, ZIP_STORED

from tools import inspect_rlcraft_293 as inspector


class RLCraftInspectorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rlcraft-inspector-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "RLCraft 1.12.2 - Release v2.9.3.zip"
        self.output = self.root / "inspection output"

    def make_zip(self, *, version="Release v2.9.3", extra=(), minecraft="1.12.2", manifest=None):
        value = {"name": "RLCraft", "version": version, "manifestVersion": 1,
            "minecraft": {"version": minecraft, "modLoaders": [{"id": "forge-14.23.5.2860", "primary": True}]},
            "files": [{"projectID": 123, "fileID": 456, "required": True}]}
        with ZipFile(self.source, "w", compression=ZIP_STORED) as zipped:
            if manifest is not False:
                zipped.writestr("manifest.json", json.dumps(value) if manifest is None else manifest)
            zipped.writestr("modlist.html", '<a href="https://example.invalid/mc-mods/123">Owned fixture</a>')
            zipped.writestr("overrides/config/owned.cfg", "enabled=true\n")
            for name, content in extra:
                if isinstance(name, str):
                    raw = ZipInfo(name)
                    # ZipInfo's constructor normalizes host separators on
                    # Windows. Preserve the malicious raw central-directory
                    # spelling so this is a real malformed-archive regression.
                    raw.filename = raw.orig_filename = name
                    name = raw
                zipped.writestr(name, content)
        return value

    def inspect(self, **kwargs):
        return inspector.inspect_archive(self.source, self.output, progress=lambda _: None, **kwargs)

    def jar(self, entries):
        value = io.BytesIO()
        with ZipFile(value, "w") as zipped:
            for name, content in entries: zipped.writestr(name, content)
        return value.getvalue()

    def test_inventory_hashes_every_member_and_roundtrips_original_and_metadata_parts(self):
        self.make_zip(extra=[("overrides/assets/owned.bin", bytes(range(256)) * 24),
            ("overrides/DO_NOT_RUN.cmd", "echo This file must never execute > outside.txt"), ("overrides/empty/", b"")])
        before = inspector.sha256(self.source)
        report = self.inspect(part_bytes=1024)
        self.assertEqual(report["status"], "inspected")
        self.assertTrue(report["file_inventory_complete"])
        self.assertFalse(report["java_executed"])
        self.assertFalse(report["gameplay_verified"])
        listing = [json.loads(line) for line in (self.output / "files.jsonl").read_text().splitlines()]
        with ZipFile(self.source) as zipped:
            self.assertEqual(len(listing), len(zipped.infolist()))
            for row in listing:
                if not row["directory"]:
                    self.assertEqual(row["sha256"], __import__('hashlib').sha256(zipped.read(row["path"])).hexdigest())
        self.assertGreater(len(report["export_parts"]), 2)
        for part in report["export_parts"]:
            self.assertEqual(part["zip_bytes"], (self.output / part["file"]).stat().st_size)
            self.assertGreater(part["zip_bytes"], part["bytes"])
        for path in self.output.glob("*.zip"):
            self.assertLess(path.stat().st_size, inspector.TRANSFER_LIMIT)
        restored = self.root / "reassembled.zip"
        inspector.assemble_parts(self.output, restored)
        self.assertEqual(inspector.sha256(restored), before)
        metadata = self.root / "metadata.zip"
        inspector.assemble_parts(self.output, metadata, "metadata")
        with ZipFile(metadata) as zipped:
            dependencies = json.loads(zipped.read("dependency-inventory.json"))
        self.assertEqual(dependencies["manifest_requirements"][0]["project_label"]["name"], "Owned fixture")
        self.assertIsNone(dependencies["manifest_requirements"][0]["dependencies"])
        self.assertFalse(dependencies["dependency_closure_verified"])
        self.assertEqual(inspector.sha256(self.source), before)
        self.assertFalse((self.root / "outside.txt").exists())

    def test_actual_default_chunks_are_strictly_under_32_mib(self):
        self.make_zip(extra=[("overrides/assets/owned.bin", b"X" * (inspector.PART_BYTES + 257))])
        report = self.inspect()
        archive_parts = [p for p in report["export_parts"] if p["dataset"] == "archive"]
        self.assertEqual(len(archive_parts), 2)
        self.assertTrue(all(p["zip_bytes"] < 32 * inspector.MIB for p in archive_parts))
        inspector.assemble_parts(self.output, self.root / "roundtrip.zip")
        self.assertEqual(inspector.sha256(self.source), inspector.sha256(self.root / "roundtrip.zip"))

    def test_282_reference_cannot_be_relabelled_by_a_293_filename(self):
        self.make_zip(version="2.8.2")
        original = inspector.sha256(self.source)
        with self.assertRaisesRegex(ValueError, "Target mismatch"):
            self.inspect()
        failure = json.loads((self.output / "inspection-failed.json").read_text())
        self.assertEqual(failure["identity"]["version"], "2.8.2")
        self.assertFalse(failure["identity"]["matches_rlcraft_2_9_3"])
        self.assertEqual(failure["status"], "failed")
        self.assertFalse(list(self.output.glob("*.zip")))
        self.assertFalse((self.output / "inspection.json").exists())
        self.assertEqual(inspector.sha256(self.source), original)

    def test_deceptive_versions_wrong_game_and_duplicate_identity_keys_are_rejected(self):
        for version in ("2.9.30", "2.9.3-reference-2.8.2", "2.9.3d"):
            value = self.make_zip(version=version)
            self.assertFalse(inspector.target_identity(value)["matches_rlcraft_2_9_3"])
        value = self.make_zip(minecraft="26.3")
        self.assertFalse(inspector.target_identity(value)["matches_rlcraft_2_9_3"])
        self.make_zip(manifest='{"name":"RLCraft","version":"2.8.2","version":"2.9.3"}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.inspect()

    def test_no_manifest_does_not_invent_identity(self):
        self.make_zip(manifest=False)
        with self.assertRaisesRegex(ValueError, "manifest.json is missing"):
            self.inspect()
        self.assertFalse(list(self.output.glob("*.zip")))

    def test_traversal_and_links_are_rejected_without_extracting(self):
        link = ZipInfo("overrides/link")
        link.external_attr = 0o120777 << 16
        for name in ("../outside.txt", "/outside.txt", "C:/outside.txt", "overrides\\outside.txt", link):
            with self.subTest(name=str(name)):
                self.make_zip(extra=[(name, b"owned malformed fixture")])
                output = self.root / ("failure-" + str(len(list(self.root.iterdir()))))
                with self.assertRaises(ValueError):
                    inspector.inspect_archive(self.source, output, progress=lambda _: None)
        self.assertFalse((self.root.parent / "outside.txt").exists())

    def test_encrypted_member_flag_is_rejected_before_reading_payloads(self):
        self.make_zip()
        data=bytearray(self.source.read_bytes())
        local=data.index(b'PK\x03\x04')
        central=data.index(b'PK\x01\x02')
        data[local+6] |= 1
        data[central+8] |= 1
        self.source.write_bytes(data)
        with self.assertRaisesRegex(ValueError,'encrypted'):self.inspect()
        self.assertFalse(list(self.output.glob('*.zip')))

    def test_case_collisions_and_file_directory_aliases_are_rejected(self):
        for entries in [[("overrides/A", b"a"), ("overrides/a", b"b")], [("overrides/dir", b"x"), ("overrides/dir/", b"")]]:
            self.make_zip(extra=entries)
            with self.assertRaisesRegex(ValueError, "colliding"):
                inspector.inspect_archive(self.source, self.root / f"bad-{len(list(self.root.iterdir()))}", progress=lambda _: None)

    def test_bounds_stop_before_large_member_reads(self):
        self.make_zip()
        for constant in ("MAX_ENTRIES", "MAX_CENTRAL", "MAX_EXPANDED"):
            with self.subTest(bound=constant), patch.object(inspector, constant, 1):
                with self.assertRaises(ValueError):
                    inspector.inspect_archive(self.source, self.root / constant, progress=lambda _: None)

    def test_legacy_jar_dependencies_hooks_and_licence_scopes_remain_evidence_only(self):
        def utf(value):
            data = value.encode();return b"\x01" + len(data).to_bytes(2,"big") + data
        code = b"\xca\xfe\xba\xbe\0\0\0\x34\0\x03" + utf("Lnet/minecraftforge/fml/common/Mod;") + utf("required-after:ownedlib@[1,)")
        directory = ZipInfo("META-INF/maven/")
        directory.external_attr = 0o177777 << 16
        jar = self.jar([(directory,b""),("mcmod.info", '[{"modid":"owned","version":"1","dependencies":["ownedlib"]}]'),
            ("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\r\nFMLCorePlugin: owned.Core\r\n\r\n"),
            ("owned/Entry.class",code),("mixins.owned.json", "{}"),("META-INF/owned_at.cfg", "# owned"),
            ("shaded/LICENSE.txt", "Owned notice"),("META-INF/libraries/nested.jar", b"inert nested bytes")])
        self.make_zip(extra=[("overrides/mods/owned.jar",jar)])
        self.inspect()
        data=json.loads((self.output/'dependency-inventory.json').read_text())["physical_jars"][0]
        self.assertEqual(data['metadata'][0]['modid'],'owned')
        self.assertEqual(data['manifest_hooks']['fmlcoreplugin'],'owned.Core')
        self.assertEqual(data['entrypoint_candidates'],['owned/Entry.class'])
        self.assertIn('required-after:ownedlib',data['dependency_string_candidates'][0]['strings'][0])
        self.assertTrue(data['mixin_configs'] and data['access_changes'] and data['licenses'] and data['nested_jars'])
        self.assertFalse(data['compatible'])
        self.assertFalse(data['dependency_closure_verified'])

    def test_unreadable_jar_and_xml_entities_remain_visible_as_blocked_scans(self):
        jar = self.jar([('META-INF/maven/owned/pom.xml', '<!DOCTYPE project [<!ENTITY x SYSTEM "file:///not-to-be-read">]><project>&x;</project>')])
        self.make_zip(extra=[('overrides/mods/invalid.jar',b'not a zip'),('overrides/mods/xml.jar',jar)])
        self.inspect()
        jars=json.loads((self.output/'dependency-inventory.json').read_text())['physical_jars']
        self.assertEqual(len(jars),2)
        self.assertTrue(all('metadata_scan_blocked' in j for j in jars))
        self.assertTrue(any('entity' in j['metadata_scan_blocked'] for j in jars))

    def test_existing_output_and_existing_reassembly_are_never_overwritten(self):
        self.make_zip();self.output.mkdir(); sentinel=self.output/'keep.txt';sentinel.write_text('owned')
        with self.assertRaisesRegex(ValueError,'never overwritten'):self.inspect()
        self.assertEqual(sentinel.read_text(),'owned')
        output=self.root/'assembled.zip';output.write_bytes(b'owned existing')
        with self.assertRaisesRegex(ValueError,'already exists'):inspector.assemble_parts(self.output,output)
        self.assertEqual(output.read_bytes(),b'owned existing')

    def test_missing_corrupt_or_mixed_export_parts_cannot_publish_output(self):
        self.make_zip(extra=[('overrides/data.bin',b'x'*5000)]);self.inspect(part_bytes=1024)
        first=next(self.output.glob('archive-0001-*.zip'))
        with ZipFile(first) as z: claim=z.read('part.json');data=z.read('payload.bin')
        with ZipFile(first,'w') as z:z.writestr('part.json',claim);z.writestr('payload.bin',bytes([data[0]^1])+data[1:])
        output=self.root/'corrupt.zip'
        with self.assertRaisesRegex(ValueError,'Corrupt'):inspector.assemble_parts(self.output,output)
        self.assertFalse(output.exists())
        mixed=json.loads(claim);mixed['source_sha256']='0'*64
        with ZipFile(first,'w') as z:z.writestr('part.json',json.dumps(mixed));z.writestr('payload.bin',data)
        with self.assertRaisesRegex(ValueError,'Mixed'):inspector.assemble_parts(self.output,output)
        self.assertFalse(output.exists())
        first.unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):inspector.assemble_parts(self.output,output)
        self.assertFalse(output.exists())

    def test_reassembly_rechecks_actual_target_instead_of_trusting_packet_label(self):
        self.make_zip(version='2.8.2')
        self.output.mkdir()
        inspector.write_parts(self.source,self.output,'archive',part_bytes=1024)
        output=self.root/'not-293.zip'
        with self.assertRaisesRegex(ValueError,'not declared RLCraft 2.9.3'):
            inspector.assemble_parts(self.output,output)
        self.assertFalse(output.exists())

    def test_injected_export_failure_has_no_completed_summary_or_bundles(self):
        self.make_zip()
        with patch.object(inspector,'write_parts',side_effect=OSError('injected disk full')):
            with self.assertRaises(OSError):self.inspect()
        self.assertFalse((self.output/'inspection.json').exists())
        self.assertFalse(list(self.output.glob('*.zip')))
        self.assertEqual(json.loads((self.output/'inspection-failed.json').read_text())['status'],'failed')

    def test_reassembly_write_failure_removes_only_its_new_partial_output(self):
        self.make_zip();self.inspect(part_bytes=1024)
        output=self.root/'partial.zip'
        def fail(source,destination,length):
            destination.write(b'owned injected partial write')
            raise OSError('injected disk full')
        with patch.object(inspector.shutil,'copyfileobj',side_effect=fail):
            with self.assertRaises(OSError):inspector.assemble_parts(self.output,output)
        self.assertFalse(output.exists())
        self.assertTrue(self.source.exists())

    def test_script_runs_standalone_in_isolated_python_without_repo_imports(self):
        self.make_zip()
        script=Path(inspector.__file__).resolve()
        result=subprocess.run([sys.executable,'-I',str(script),str(self.source),'--output',str(self.output)],cwd=self.root,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((self.output/'00-summary.zip').is_file())
