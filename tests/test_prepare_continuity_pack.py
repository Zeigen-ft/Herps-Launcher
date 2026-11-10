import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

spec = importlib.util.spec_from_file_location(
    "prepare_continuity_pack", Path(__file__).resolve().parents[1] / "tools/prepare_continuity_pack.py")
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


class ContinuityPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "continuity.jar"
        self.output = self.root / "packs/continuity.zip"

    def jar(self, extra=(), method="ctm", version=pack.VERSION, omit=()):
        entries = [
            ("fabric.mod.json", json.dumps({"id": "continuity", "version": version,
                                          "license": "LGPL-3.0-only", "authors": ["Fixture author"]})),
            (pack.PREFIX + "pack.mcmeta", '{"pack":{"description":{"translate":"old"},"min_format":97.1}}'),
            ("LICENSE_continuity", "Synthetic test license text; no third-party artwork"),
            (pack.PREFIX + "assets/continuity/optifine/ctm/default/glass/glass.properties",
             f"method={method}\nmatchBlocks=glass\ntiles=0-46\n"),
            (pack.PREFIX + "assets/continuity/optifine/ctm/default/glass/0.png", b"own fixture image"),
            (pack.PREFIX + "assets/continuity/optifine/ctm/programmer_art/glass/glass.properties",
             "method=ctm\nresourceCondition=textures/block/glass.png@programmer_art\n"),
            (pack.PREFIX + "assets/continuity/optifine/ctm/programmer_art/glass/0.png", b"other own image"),
            ("resourcepacks/glass_pane_culling_fix/assets/minecraft/models/block/post.json", "{}"),
            ("me/author/Runtime.class", b"not executable in this test"),
        ]
        result = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as z:
                for name, data in [*entries, *extra]:
                    if name not in omit:
                        z.writestr(name, data)
        self.source.write_bytes(result.getvalue())
        return result.getvalue()

    def test_extracts_only_default_resources_preserving_license_and_provenance(self):
        raw = self.jar()
        report = pack.prepare(self.source, self.output)
        with zipfile.ZipFile(self.output) as z:
            names = z.namelist()
            self.assertIsNone(z.testzip())
            self.assertFalse(any(n.endswith(".class") for n in names))
            self.assertFalse(any("programmer_art" in n or "culling_fix" in n for n in names))
            self.assertEqual(z.read("LICENSE_continuity"), b"Synthetic test license text; no third-party artwork")
            meta = json.loads(z.read("pack.mcmeta"))["pack"]
            self.assertEqual(meta["min_format"], [97, 1])
            self.assertEqual(meta["max_format"], [97, 1])
            self.assertIn("PepperCode1", meta["description"])
            self.assertEqual(json.loads(z.read("herps-continuity-provenance.json"))["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["connection_rules"], {"ctm": 1})
        self.assertEqual(report["output_sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertFalse(report["gameplay_verified"])
        self.assertEqual(report, pack.prepare(self.source, self.output))

    def test_existing_differing_output_is_preserved(self):
        self.jar()
        self.output.parent.mkdir()
        self.output.write_bytes(b"user file")
        with self.assertRaisesRegex(ValueError, "preserve"):
            pack.prepare(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), b"user file")

    def test_refuses_unsafe_paths_even_in_unused_java_entries(self):
        for name in ("../bad", "/bad", "a/../../bad", "a\\bad", "a//bad", "C:/bad"):
            with self.subTest(name=name):
                self.jar(extra=[(name, b"x")])
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    pack.prepare(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_refuses_duplicates_case_collisions_and_symlinks(self):
        for extra in [("fabric.mod.json", "{}"), ("FABRIC.MOD.JSON", "{}")]:
            with self.subTest(extra=extra):
                self.jar(extra=[extra])
                with self.assertRaisesRegex(ValueError, "Duplicate"):
                    pack.prepare(self.source, self.output)
        link = zipfile.ZipInfo("unused/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.jar(extra=[(link, "../target")])
        with self.assertRaisesRegex(ValueError, "links"):
            pack.prepare(self.source, self.output)

    def test_refuses_wrong_version_missing_license_and_unsupported_methods(self):
        for args in ({"version": "new-unknown"}, {"omit": ["LICENSE_continuity"]}, {"method": "overlay"}):
            with self.subTest(args=args):
                self.jar(**args)
                with self.assertRaises(ValueError):
                    pack.prepare(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_bounded_input_entry_count_and_expansion(self):
        raw = self.jar()
        for setting, value, pattern in (("MAX_ARCHIVE_BYTES", 10, "bounded|size"),
                                        ("MAX_ENTRIES", 1, "expansion"),
                                        ("MAX_EXPANDED_BYTES", 1, "expansion"),
                                        ("MAX_FILE_BYTES", 1, "oversized")):
            with self.subTest(setting=setting), patch.object(pack, setting, value):
                with self.assertRaisesRegex(ValueError, pattern):
                    pack.build(raw)

    def test_output_link_and_linked_parent_are_refused(self):
        self.jar()
        target = self.root / "target"
        target.mkdir()
        self.output.parent.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            pack.prepare(self.source, self.output)
        self.assertFalse(list(target.iterdir()))


if __name__ == "__main__":
    unittest.main()
