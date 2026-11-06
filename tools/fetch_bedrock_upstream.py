#!/usr/bin/env python3
"""Fetch checksum-pinned Bedrock source and MSI; never execute the installer.

The source-cache stamp records origin, not subsequent local source edits. Keep
an unmodified cache when building reproducible packages.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("_herspers_source_fetch", ROOT / "tools/fetch_upstream.py")
_common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_common)


class HttpsOnlyRedirect(urllib.request.HTTPRedirectHandler):
    """Keep verified HTTPS for every step of a release/CDN redirect chain."""

    def redirect_request(self, request, fp, code, message, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme.lower() != "https":
            raise ValueError("Download redirected away from HTTPS; refusing it")
        return super().redirect_request(request, fp, code, message, headers, newurl)


def verify_file(path: Path, expected_digest: str, size: int | None, limit: int) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected a regular verified file: {path}")
    observed_size = path.stat().st_size
    if observed_size > limit or (size is not None and observed_size != size):
        raise ValueError(f"Locked download size mismatch; preserving existing file: {path}")
    if _common.digest(path) != expected_digest:
        raise ValueError(f"Locked download checksum mismatch; preserving existing file: {path}")
    return path


def download_verified(url: str, destination: Path, expected_digest: str,
                      size: int | None, limit: int) -> Path:
    if urllib.parse.urlsplit(url).scheme.lower() != "https":
        raise ValueError("Locked download URL must use HTTPS")
    if destination.exists() or destination.is_symlink():
        return verify_file(destination, expected_digest, size, limit)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".bedrock-download-", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        opener = urllib.request.build_opener(HttpsOnlyRedirect())
        with os.fdopen(fd, "wb") as output:
            with opener.open(url, timeout=120) as response:
                if urllib.parse.urlsplit(response.geturl()).scheme.lower() != "https":
                    raise ValueError("Download response is not HTTPS")
                declared = response.headers.get("Content-Length")
                if declared is not None:
                    length = int(declared)
                    if length < 0 or length > limit or (size is not None and length != size):
                        raise ValueError("Locked download size mismatch in HTTP response")
                total = 0
                while block := response.read(min(1024 * 1024, limit - total + 1)):
                    total += len(block)
                    if total > limit or (size is not None and total > size):
                        raise ValueError("Download exceeds its locked size limit")
                    output.write(block)
        verify_file(temporary, expected_digest, size, limit)
        try:
            # Publishing a hard link is atomic and refuses to replace an existing
            # name on POSIX and NTFS. No partial download is exposed as a cache hit.
            os.link(temporary, destination)
        except FileExistsError:
            # Another fetch may have won the race. Only accept the same bytes.
            verify_file(destination, expected_digest, size, limit)
        return destination
    finally:
        temporary.unlink(missing_ok=True)


def fetch_bedrock(lock: dict, cache: Path, archive: Path | None = None,
                  msi: Path | None = None) -> dict[str, str]:
    for key in ("archive_sha256", "windows_msi_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", lock[key]):
            raise ValueError(f"Invalid locked SHA-256: {key}")
    if not re.fullmatch(r"[0-9a-f]{40}", lock["commit"]):
        raise ValueError("Invalid locked source commit")
    msi_size = lock["windows_msi_size"]
    if type(msi_size) is not int or not 0 < msi_size <= 512 * 1024 * 1024:
        raise ValueError("Invalid locked MSI size")
    cache.mkdir(parents=True, exist_ok=True)
    if archive is None:
        archive = download_verified(lock["archive_url"], cache / f"{lock['commit']}.tar.gz",
                                    lock["archive_sha256"], None, _common.MAX_ARCHIVE_BYTES)
    else:
        verify_file(archive, lock["archive_sha256"], None, _common.MAX_ARCHIVE_BYTES)
    # Passing the already verified archive avoids the common fetcher's network
    # path; all actual downloads here enforce HTTPS across redirects.
    source = _common.fetch(lock, cache, archive)
    if msi is None:
        msi = download_verified(lock["windows_msi_url"], cache / "Cinnabar-x64.msi",
                                lock["windows_msi_sha256"], msi_size, msi_size)
    else:
        verify_file(msi, lock["windows_msi_sha256"], msi_size, msi_size)
    return {"source": str(source), "msi": str(msi)}


def safe_message(error: Exception) -> str:
    # Redirect errors may contain short-lived CDN query credentials. Never echo
    # a complete request URL in user-visible diagnostics.
    return re.sub(r"https?://[^\s\"<>]+", lambda match:
                  urllib.parse.urlsplit(match.group()).scheme + "://" +
                  str(urllib.parse.urlsplit(match.group()).hostname) + "/[redacted]", str(error))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use a local source archive; checksum is still required")
    parser.add_argument("--msi", type=Path, help="Use a local installer; exact size and checksum are still required")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/bedrock-upstream")
    args = parser.parse_args()
    try:
        lock = json.loads((ROOT / "bedrock-upstream.lock.json").read_text())
        result = fetch_bedrock(lock, args.cache.resolve(),
                               args.archive.absolute() if args.archive else None,
                               args.msi.absolute() if args.msi else None)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, urllib.error.URLError, _common.tarfile.TarError) as error:
        print("fetch_bedrock_upstream: " + safe_message(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
