import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("fetch_upstream", Path(__file__).resolve().parents[1] / "tools/fetch_upstream.py")
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "source.tar.gz"

    def archive_with(self, name="source/Cargo.lock", link=None):
        with tarfile.open(self.archive, "w:gz") as t:
            info = tarfile.TarInfo(name)
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = link
                t.addfile(info)
            else:
                info.size = 4
                t.addfile(info, io.BytesIO(b"lock"))
        return {"commit": "a" * 40, "archive_root": "source", "archive_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest()}

    def test_verified_source_and_repeatability(self):
        lock = self.archive_with()
        source = fetcher.fetch(lock, self.root / "cache", self.archive)
        self.assertEqual((source / "Cargo.lock").read_text(), "lock")
        self.assertEqual(fetcher.fetch(lock, self.root / "cache", self.archive), source)

    def test_checksum_failure_does_not_extract(self):
        lock = self.archive_with()
        lock["archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checksum"):
            fetcher.fetch(lock, self.root / "cache", self.archive)
        self.assertFalse((self.root / "cache" / lock["commit"]).exists())

    def test_reject_traversal_absolute_path_and_links(self):
        for name, link in [("source/../../escape", None), ("/source/absolute", None), ("elsewhere/file", None), ("source/link", "/tmp")]:
            with self.subTest(name=name):
                lock = self.archive_with(name, link)
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    fetcher.fetch(lock, self.root / "cache", self.archive)
                self.assertFalse((self.root / "escape").exists())

    def test_does_not_overwrite_unknown_cache(self):
        lock = self.archive_with()
        source = self.root / "cache" / lock["commit"]
        source.mkdir(parents=True)
        (source / "mine").write_text("preserve")
        with self.assertRaisesRegex(ValueError, "preserve"):
            fetcher.fetch(lock, self.root / "cache", self.archive)
        self.assertEqual((source / "mine").read_text(), "preserve")

    def test_materializes_sibling_file_link_without_creating_symlink(self):
        lock = self.archive_with("source/AGENTS.md")
        with tarfile.open(self.archive, "w:gz") as t:
            regular = tarfile.TarInfo("source/AGENTS.md")
            regular.size = 4
            t.addfile(regular, io.BytesIO(b"docs"))
            link = tarfile.TarInfo("source/CLAUDE.md")
            link.type, link.linkname = tarfile.SYMTYPE, "AGENTS.md"
            t.addfile(link)
        lock["archive_sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        source = fetcher.fetch(lock, self.root / "cache", self.archive)
        self.assertEqual((source / "CLAUDE.md").read_bytes(), b"docs")
        self.assertFalse((source / "CLAUDE.md").is_symlink())


if __name__ == "__main__":
    unittest.main()
