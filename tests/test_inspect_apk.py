"""Malformed-input coverage and optional supplied-APK integration check."""
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile

SPEC = importlib.util.spec_from_file_location("inspect_apk", Path(__file__).resolve().parents[1] / "tools" / "inspect_apk.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def elf32():
    # One mapped segment containing a dynamic table and its string table.
    data = bytearray(256)
    data[:16] = b"\x7fELF\x01\x01\x01" + bytes(9)
    struct.pack_into("<HHIIIIIHHHHHH", data, 16, 3, 40, 1, 0, 52, 0, 0, 52, 32, 2, 0, 0, 0)
    struct.pack_into("<IIIIIIII", data, 52, 1, 0, 0x1000, 0, len(data), len(data), 4, 4)
    struct.pack_into("<IIIIIIII", data, 84, 2, 128, 0x1080, 0, 32, 32, 4, 4)
    struct.pack_into("<iIiIiIiI", data, 128, 1, 1, 5, 0x10c0, 10, 16, 0, 0)
    data[192:208] = b"\0libandroid.so\0\0"
    return bytes(data)


class ElfTests(unittest.TestCase):
    def test_arm_dynamic_dependency(self):
        parsed = audit.inspect_elf(elf32())
        self.assertEqual(parsed["machine"], "ARM")
        self.assertEqual(parsed["bits"], 32)
        self.assertEqual(parsed["needed_libraries"], ["libandroid.so"])

    def test_invalid_and_truncated_headers(self):
        for payload in (b"not an ELF", b"\x7fELF", elf32()[:80]):
            with self.subTest(size=len(payload)), self.assertRaises(audit.AuditError):
                audit.inspect_elf(payload)

    def test_unmapped_string_table(self):
        data = bytearray(elf32())
        struct.pack_into("<I", data, 140, 0x9000)
        with self.assertRaisesRegex(audit.AuditError, "not file-backed"):
            audit.inspect_elf(bytes(data))

    def test_dependency_name_out_of_bounds(self):
        data = bytearray(elf32())
        struct.pack_into("<I", data, 132, 100)
        with self.assertRaisesRegex(audit.AuditError, "out of bounds"):
            audit.inspect_elf(bytes(data))


class ApkTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "fixture.apk"

    def test_nested_resource_metadata(self):
        nested = io.BytesIO()
        with ZipFile(nested, "w") as z:
            z.writestr("horizon-resources.json", json.dumps({"minecraft": "test-version", "schema": 7, "data_version": 42}))
        with ZipFile(self.path, "w") as z:
            z.writestr("lib/test/libfixture.so", elf32())
            z.writestr("assets/engine-data.zip", nested.getvalue())
            z.writestr("classes.dex", b"fixture")
        result = audit.audit_apk(self.path)
        self.assertEqual(result["entry_count"], 3)
        self.assertEqual(result["engine_archive"]["resource_metadata"]["minecraft"], "test-version")
        self.assertEqual(result["native_libraries"][0]["needed_libraries"], ["libandroid.so"])

    def test_rejects_path_traversal(self):
        with ZipFile(self.path, "w") as z:
            z.writestr("../escape", b"unsafe")
        with self.assertRaisesRegex(audit.AuditError, "unsafe member"):
            audit.audit_apk(self.path)

    def test_rejects_oversized_member_before_read(self):
        with ZipFile(self.path, "w") as z:
            z.writestr("oversized", b"123456")
        old = audit.MAX_MEMBER
        self.addCleanup(setattr, audit, "MAX_MEMBER", old)
        audit.MAX_MEMBER = 5
        with self.assertRaisesRegex(audit.AuditError, "member exceeds"):
            audit.audit_apk(self.path)

    @unittest.skipUnless(os.environ.get("HORIZON_TEST_APK"), "Set HORIZON_TEST_APK to run supplied-APK integration")
    def test_supplied_apk(self):
        result = audit.audit_apk(Path(os.environ["HORIZON_TEST_APK"]))
        self.assertEqual(result["sha256"], "f432e75cffb7f8ca147fe325e51aa410038c8257c38a822277ed9762ba3127db")
        self.assertEqual(result["engine_archive"]["resource_metadata"]["minecraft"], "26.3")
        library, = result["native_libraries"]
        self.assertEqual((library["bits"], library["machine"]), (32, "ARM"))
        self.assertIn("libaaudio.so", library["needed_libraries"])
        self.assertEqual(library["embedded_diagnostic"]["source_commit_prefix"], "7301f6fdd7f4")


if __name__ == "__main__":
    unittest.main()
