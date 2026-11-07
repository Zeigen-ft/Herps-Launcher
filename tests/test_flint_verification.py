"""Native-probe source guards reject edited caches and unrelated patch sets."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.prepare_upstream import tree_digest
from tools.verify_rlcraft_flint import verified_source


class FlintSourceGuardTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="owned-flint-source-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"; self.source.mkdir()
        (self.source / "owned.rs").write_text("// owned fixture; never compiled\n")
        patches = self.root / "patches"; patches.mkdir()
        (patches / "owned.patch").write_bytes(b"owned patch payload")
        manifest = {"upstream_commit": "a"*40, "files": [{"patch": "owned.patch"}]}
        raw = json.dumps(manifest).encode()
        (patches / "upstream.json").write_bytes(raw)
        lock = {"commit": "a"*40, "rust_toolchain": "1.95.0"}
        (self.root / "upstream.lock.json").write_text(json.dumps(lock))
        fingerprint = hashlib.sha256(raw)
        patch = (patches / "owned.patch").read_bytes()
        fingerprint.update(len(patch).to_bytes(8, "big") + patch)
        stamp = {"upstream": lock, "patches_sha256": fingerprint.hexdigest(),
                 "tree_sha256": tree_digest(self.source)}
        (self.source / ".herspers-prepared.json").write_text(json.dumps(stamp))

    def test_matching_prepared_tree_and_complete_patch_fingerprint_are_accepted(self):
        self.assertEqual(verified_source(self.source, self.root), self.source)

    def test_edited_source_and_edited_patch_are_both_refused(self):
        path = self.source / "owned.rs"; before = path.read_text()
        path.write_text("changed")
        with self.assertRaisesRegex(ValueError, "pinned"): verified_source(self.source, self.root)
        path.write_text(before)
        (self.root / "patches/owned.patch").write_text("changed patch")
        with self.assertRaisesRegex(ValueError, "pinned"): verified_source(self.source, self.root)

    def test_unrelated_source_lock_and_manifest_only_fingerprint_are_refused(self):
        path = self.source / ".herspers-prepared.json"
        original = json.loads(path.read_text()); changed = json.loads(path.read_text())
        changed["upstream"]["commit"] = "b"*40; path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, "pinned"): verified_source(self.source, self.root)
        original["patches_sha256"] = hashlib.sha256((self.root / "patches/upstream.json").read_bytes()).hexdigest()
        path.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, "pinned"): verified_source(self.source, self.root)
