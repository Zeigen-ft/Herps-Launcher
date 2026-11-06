import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

SPEC = importlib.util.spec_from_file_location("bedrock_fetch", Path(__file__).resolve().parents[1] / "tools/fetch_bedrock_upstream.py")
fetcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetcher)


class Response(io.BytesIO):
    def __init__(self, content, url="https://cdn.example.test/file", declared=None):
        super().__init__(content)
        self.url = url
        self.headers = {} if declared is None else {"Content-Length": str(declared)}

    def geturl(self):
        return self.url


class FetchBedrockTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / "source.tar.gz"
        with tarfile.open(self.archive, "w:gz") as tar:
            member = tarfile.TarInfo("upstream/Cargo.toml")
            content = b"[workspace]\n"
            member.size = len(content)
            tar.addfile(member, io.BytesIO(content))
        self.msi = self.root / "installer.msi"
        self.payload = b"small test installer fixture; never executed"
        self.msi.write_bytes(self.payload)
        self.sha = hashlib.sha256(self.payload).hexdigest()
        self.lock = {
            "commit": "a" * 40, "archive_root": "upstream",
            "archive_url": "https://example.test/source.tar.gz",
            "archive_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            "windows_msi_url": "https://example.test/installer.msi",
            "windows_msi_sha256": self.sha, "windows_msi_size": len(self.payload),
        }

    def download(self, response, destination=None):
        destination = destination or self.root / "cache/download.msi"
        with patch.object(fetcher.urllib.request, "build_opener") as make:
            make.return_value.open.return_value = response
            return fetcher.download_verified(self.lock["windows_msi_url"], destination,
                                             self.sha, len(self.payload), len(self.payload))

    def test_local_verified_files_and_source_repeatability(self):
        result = fetcher.fetch_bedrock(self.lock, self.root / "cache", self.archive, self.msi)
        source = Path(result["source"])
        self.assertEqual((source / "Cargo.toml").read_bytes(), b"[workspace]\n")
        self.assertEqual(Path(result["msi"]), self.msi)
        self.assertEqual(fetcher.fetch_bedrock(self.lock, self.root / "cache", self.archive, self.msi), result)
        self.assertEqual(json.loads((source / ".herspers-source.json").read_text()), self.lock)

    def test_local_size_and_checksum_are_not_bypassed(self):
        for data in (self.payload + b"x", b"x" * len(self.payload)):
            self.msi.write_bytes(data)
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "mismatch"):
                fetcher.fetch_bedrock(self.lock, self.root / "cache", self.archive, self.msi)
            self.assertEqual(self.msi.read_bytes(), data)

    def test_archive_checksum_failure_prevents_extraction(self):
        self.lock["archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checksum"):
            fetcher.fetch_bedrock(self.lock, self.root / "cache", self.archive, self.msi)
        self.assertFalse((self.root / "cache" / self.lock["commit"]).exists())

    def test_download_verifies_bytes_and_publishes_atomically(self):
        target = self.download(Response(self.payload, declared=len(self.payload)))
        self.assertEqual(target.read_bytes(), self.payload)
        self.assertFalse(list(target.parent.glob(".bedrock-download-*")))

    def test_failed_downloads_leave_no_cache_file(self):
        for payload, declared in [(b"short", None), (self.payload + b"x", None),
                                  (b"x" * len(self.payload), None), (self.payload, 1)]:
            with self.subTest(payload=payload, declared=declared), self.assertRaises(ValueError):
                self.download(Response(payload, declared=declared))
            self.assertFalse((self.root / "cache/download.msi").exists())
            self.assertFalse(list((self.root / "cache").glob(".bedrock-download-*")))

    def test_existing_wrong_cache_is_preserved_without_network(self):
        target = self.root / "cache/download.msi"
        target.parent.mkdir()
        target.write_bytes(b"user data")
        with patch.object(fetcher.urllib.request, "build_opener") as make:
            with self.assertRaisesRegex(ValueError, "preserving"):
                fetcher.download_verified(self.lock["windows_msi_url"], target,
                                           self.sha, len(self.payload), len(self.payload))
            make.assert_not_called()
        self.assertEqual(target.read_bytes(), b"user data")

    def test_matching_cache_does_not_download(self):
        with patch.object(fetcher.urllib.request, "build_opener") as make:
            result = fetcher.download_verified(self.lock["windows_msi_url"], self.msi,
                                               self.sha, len(self.payload), len(self.payload))
            make.assert_not_called()
        self.assertEqual(result, self.msi)

    def test_conflicting_cache_created_during_download_is_preserved(self):
        target = self.root / "cache/download.msi"

        def another_writer(_temporary, destination):
            destination.write_bytes(b"concurrent user data")
            raise FileExistsError("another writer published this name")

        with patch.object(fetcher.os, "link", side_effect=another_writer):
            with self.assertRaisesRegex(ValueError, "preserving"):
                self.download(Response(self.payload), target)
        self.assertEqual(target.read_bytes(), b"concurrent user data")
        self.assertFalse(list(target.parent.glob(".bedrock-download-*")))

    def test_http_source_and_redirects_are_refused(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            fetcher.download_verified("http://example.test/file", self.root / "bad.msi",
                                       self.sha, len(self.payload), len(self.payload))
        request = urllib.request.Request("https://example.test/file")
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            fetcher.HttpsOnlyRedirect().redirect_request(request, None, 302, "Found", {},
                                                        "http://cdn.example.test/file")
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            self.download(Response(self.payload, url="http://cdn.example.test/file"))

    def test_signed_urls_are_redacted_from_errors(self):
        message = fetcher.safe_message(ValueError('Get "https://cdn.example.test/file?sig=secret": Forbidden'))
        self.assertNotIn("secret", message)
        self.assertNotIn("?sig", message)
        self.assertIn("cdn.example.test", message)


if __name__ == "__main__":
    unittest.main()
