import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
from pathlib import Path
import tarfile
import tempfile
import unittest
import zlib

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


@unittest.skipUnless(shutil.which("git"), "Git is required for verified source exports")
class GitSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        self.git("init", "-q")
        (self.source / "src").mkdir()
        (self.source / "src/main.rs").write_bytes(b"original source\n")
        (self.source / "Cargo.lock").write_bytes(b"locked\n")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.lock = {"commit": self.git("rev-parse", "HEAD").decode().strip()}
        self.destination = self.root / "export"
        self.destination.mkdir()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args], stderr=subprocess.PIPE)

    def export(self):
        return fetcher.export_git(self.lock, self.source, self.destination)

    def test_verified_objects_export_without_git_metadata(self):
        provenance = self.export()
        self.assertEqual(provenance["method"], "git-object-hash")
        self.assertEqual(provenance["commit"], self.lock["commit"])
        self.assertEqual(provenance["tree"], self.git("rev-parse", "HEAD^{tree}").decode().strip())
        self.assertEqual((self.destination / "src/main.rs").read_bytes(), b"original source\n")
        self.assertFalse((self.destination / ".git").exists())

    def test_wrong_commit_is_refused(self):
        self.lock["commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "pinned commit"):
            self.export()
        self.assertFalse(list(self.destination.iterdir()))

    def test_edited_missing_untracked_and_ignored_files_are_refused(self):
        target = self.source / "src/main.rs"
        original = target.read_bytes()
        for change in ("edited", "missing", "untracked", "ignored"):
            if change == "edited":
                target.write_bytes(b"edits")
            elif change == "missing":
                target.unlink()
            elif change == "untracked":
                (self.source / "extra.rs").write_bytes(b"extra")
            else:
                (self.source / ".git/info/exclude").write_text("extra.rs\n")
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "local changes or extra files"):
                self.export()
            target.write_bytes(original)
        self.assertFalse(list(self.destination.iterdir()))

    def test_assume_unchanged_cannot_hide_modified_bytes(self):
        self.git("update-index", "--assume-unchanged", "src/main.rs")
        (self.source / "src/main.rs").write_bytes(b"hidden edit")
        with self.assertRaisesRegex(ValueError, "committed blob"):
            self.export()
        self.assertFalse(list(self.destination.iterdir()))

    def test_corrupt_git_blob_is_refused_without_trusting_its_filename(self):
        oid = self.git("rev-parse", "HEAD:src/main.rs").decode().strip()
        loose = self.source / ".git/objects" / oid[:2] / oid[2:]
        raw = zlib.decompress(loose.read_bytes())
        loose.chmod(0o644)
        loose.write_bytes(zlib.compress(raw.replace(b"original", b"tampered")))
        # Cached clean status must not substitute for hashing the Git object.
        self.git("update-index", "--assume-unchanged", "src/main.rs")
        with self.assertRaisesRegex(ValueError, "object checksum mismatch"):
            self.export()
        self.assertFalse(list(self.destination.iterdir()))

    def test_sibling_symlink_is_materialized(self):
        try:
            (self.source / "ALIAS.md").symlink_to("Cargo.lock")
        except OSError:
            self.skipTest("Symlinks are unavailable")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "link")
        self.lock["commit"] = self.git("rev-parse", "HEAD").decode().strip()
        self.export()
        self.assertEqual((self.destination / "ALIAS.md").read_bytes(), b"locked\n")
        self.assertFalse((self.destination / "ALIAS.md").is_symlink())

    def test_windows_regular_link_blob_is_safely_materialized(self):
        try:
            (self.source / "ALIAS.md").symlink_to("Cargo.lock")
        except OSError:
            self.skipTest("Symlinks are unavailable")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "link")
        self.lock["commit"] = self.git("rev-parse", "HEAD").decode().strip()
        self.git("config", "core.symlinks", "false")
        (self.source / "ALIAS.md").unlink()
        (self.source / "ALIAS.md").write_bytes(b"Cargo.lock")
        self.export()
        self.assertEqual((self.destination / "ALIAS.md").read_bytes(), b"locked\n")
        self.assertFalse((self.destination / "ALIAS.md").is_symlink())

    def test_escaping_symlink_is_refused(self):
        try:
            (self.source / "escape").symlink_to("../outside")
        except OSError:
            self.skipTest("Symlinks are unavailable")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "link")
        self.lock["commit"] = self.git("rev-parse", "HEAD").decode().strip()
        with self.assertRaisesRegex(ValueError, "Unsafe Git source link"):
            self.export()

    def test_replace_refs_cannot_substitute_commit(self):
        original = self.lock["commit"]
        (self.source / "src/main.rs").write_bytes(b"replacement")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "replacement")
        replacement = self.git("rev-parse", "HEAD").decode().strip()
        self.git("replace", original, replacement)
        # A checkout of the real original stays verifiable with replacements disabled.
        subprocess.check_call(["git", "--no-replace-objects", "-C", str(self.source),
                               "checkout", "--detach", "-q", original])
        self.export()
        self.assertEqual((self.destination / "src/main.rs").read_bytes(), b"original source\n")



if __name__ == "__main__":
    unittest.main()
