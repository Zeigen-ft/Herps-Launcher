"""Untrusted ZIP, dependency closure and non-destructive data-pack rebuilding."""
import io
import json
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
import zipfile
from tools import build_better_leaves as leaves


class BetterLeavesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="owned-leaves-")
        self.addCleanup(temp.cleanup); self.root = Path(temp.name)

    def archive(self, names):
        path = self.root / "input.zip"
        with zipfile.ZipFile(path, "w") as z:
            for name, raw in names: z.writestr(name, raw)
        return path

    def test_curated_assets_have_complete_closed_dependencies_and_upstream_pins(self):
        files, record, graph = leaves.payload()
        self.assertEqual(graph, {"blocks": 14, "models": 64, "textures": 14,
            "blockstate_variants": 224, "external_parent": "minecraft:block/block"})
        self.assertEqual(len(files), 97)
        self.assertEqual(record["archive_sha256"], leaves.SOURCE_SHA256)
        for name, expected in record["source_files"].items():
            self.assertEqual(leaves.digest(files[name]), expected)
        self.assertIn(b"2024 Motschen", files["LICENSE"])
        self.assertFalse(any(n.startswith("data/") or n.endswith((".jar", ".wasm", ".class", ".exe")) for n in files))

    def test_rebuild_is_deterministic_and_does_not_touch_other_files(self):
        output = self.root / "out"; sentinel = self.root / "profile/saves/Owned/level.dat"
        sentinel.parent.mkdir(parents=True); sentinel.write_bytes(b"owned fixture; not a world")
        first = leaves.build(output); before = (output / leaves.PACKAGE_NAME).read_bytes()
        second = leaves.build(output)
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(before, leaves.package_bytes())
        self.assertEqual(sentinel.read_bytes(), b"owned fixture; not a world")
        with zipfile.ZipFile(io.BytesIO(before)) as z:
            self.assertIn("pack.mcmeta", z.namelist())
            self.assertFalse(any(n.startswith("assets/cobblemon/") for n in z.namelist()))

    def test_original_sha_mismatch_is_refused_without_output(self):
        original = self.archive([("pack.mcmeta", b"{}")])
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            leaves.build(self.root / "out", original=original)
        self.assertFalse((self.root / "out").exists())

    def test_archive_traversal_absolute_and_windows_paths_are_refused(self):
        for name in ["../outside", "/outside", "assets/../../outside", "C:/outside", "assets\\outside", "./hidden"]:
            with self.subTest(name=name):
                path = self.archive([(name, b"owned")])
                with self.assertRaises(ValueError): leaves.read_archive(path, expected_sha=None)
        self.assertFalse((self.root.parent / "outside").exists())

    def test_archive_duplicate_and_case_collision_are_refused(self):
        for names in [[("same", b"1"), ("same", b"2")], [("Asset", b"1"), ("asset", b"2")]]:
            with self.subTest(names=names):
                path = self.archive(names)
                with self.assertRaisesRegex(ValueError, "Duplicate|case-colliding"):
                    leaves.read_archive(path, expected_sha=None)

    def test_archive_symlink_is_refused(self):
        path = self.root / "link.zip"
        with zipfile.ZipFile(path, "w") as z:
            info = zipfile.ZipInfo("assets/link"); info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16; z.writestr(info, "../owned")
        with self.assertRaisesRegex(ValueError, "linked"):
            leaves.read_archive(path, expected_sha=None)

    def test_archive_expansion_and_file_limits_are_enforced(self):
        path = self.archive([("assets/large", b"x" * (leaves.MAX_FILE + 1))])
        with self.assertRaisesRegex(ValueError, "oversized"):
            leaves.read_archive(path, expected_sha=None)

    def test_changed_existing_pack_is_preserved(self):
        output = self.root / "out"; output.mkdir()
        path = output / leaves.PACKAGE_NAME; path.write_bytes(b"existing user pack")
        with self.assertRaisesRegex(ValueError, "Preserve"):
            leaves.build(output)
        self.assertEqual(path.read_bytes(), b"existing user pack")

    def test_source_tampering_is_rejected(self):
        copied = self.root / "source"; shutil.copytree(leaves.SOURCE, copied)
        p = copied / "source/assets/minecraft/models/block/oak_leaves1.json"; p.write_text("{}")
        with self.assertRaisesRegex(ValueError, "checksum"):
            leaves.package_bytes(copied)

    def test_parent_cycle_missing_parent_and_missing_texture_are_rejected(self):
        original, record, _ = leaves.payload()
        name = "assets/minecraft/models/block/oak_leaves1.json"
        for value in [{"parent":"minecraft:block/oak_leaves1"}, {"parent":"missing:block/none"},
                {"parent":"betterleaves:block/leaves1","textures":{"all":"minecraft:block/nonexistent"}}]:
            with self.subTest(value=value):
                files = dict(original); files[name] = json.dumps(value).encode()
                with self.assertRaises(ValueError): leaves.validate_graph(files, record["target_blocks"])

    def test_json_duplicates_and_nonfinite_values_are_rejected(self):
        for raw in ['{"model":1,"model":2}', '{"from":NaN}', '{"to":Infinity}']:
            with self.assertRaises(ValueError): leaves.strict_json(raw)

    def test_texture_aliases_bind_to_child_overrides_after_parent_resolution(self):
        files, record, _ = leaves.payload()
        # Every parent has #all but the leaf child supplies the actual material.
        # Validating the parent before merging child slots would reject the pack.
        stats = leaves.validate_graph(files, record["target_blocks"])
        self.assertEqual(stats["textures"], 14)
