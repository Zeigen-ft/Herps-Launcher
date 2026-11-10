#!/usr/bin/env python3
"""Fetch checksum-locked archives or export a hash-verified pinned Git commit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_EXPANDED_BYTES = 1024 * 1024 * 1024


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def unpack(archive: Path, destination: Path, prefix: str) -> None:
    """Extract files/directories, materializing safe sibling-file symlinks."""
    with tarfile.open(archive, "r:gz") as tar:
        entries = tar.getmembers()
        if len(entries) > 50000 or sum(m.size for m in entries) > MAX_EXPANDED_BYTES:
            raise ValueError("Source archive exceeds extraction limits")
        seen = set()
        for member in entries:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or ".." in name.parts or not name.parts
                    or name.parts[0] != prefix or member.name in seen
                    or not (member.isfile() or member.isdir() or member.issym())):
                raise ValueError(f"Unsafe source archive member: {member.name}")
            if member.issym():
                link = PurePosixPath(member.linkname)
                # The pinned source has CLAUDE.md -> AGENTS.md. Materialize
                # sibling regular files instead of creating filesystem links.
                if link.is_absolute() or len(link.parts) != 1 or link.parts[0] in ("..", "."):
                    raise ValueError(f"Unsafe source archive member: {member.name}")
                try:
                    original = tar.getmember(str(name.parent / link))
                except KeyError as error:
                    raise ValueError(f"Missing source archive link target: {member.name}") from error
                if not original.isfile():
                    raise ValueError(f"Unsafe source archive member: {member.name}")
            seen.add(member.name)
        # No filesystem links, devices or traversal; supports macOS Python 3.9+.
        for member in entries:
            relative = PurePosixPath(member.name).relative_to(prefix)
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            original = tar.getmember(str(PurePosixPath(member.name).parent / member.linkname)) if member.issym() else member
            source = tar.extractfile(original)
            if source is None:
                raise ValueError(f"Missing source data: {member.name}")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(0o755 if member.mode & 0o111 else 0o644)


def export_git(lock: dict, source: Path, destination: Path) -> dict:
    """Export the locked commit's verified objects, never a working-tree snapshot.

    This explicit alternative is useful when a repository rename changes GitHub's
    generated archive bytes. The archive lock is deliberately not weakened.
    """
    revision = lock.get("commit", "")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Git source requires a full pinned SHA-1 commit")
    for part in (source, *source.parents):
        if part.is_symlink():
            raise ValueError("Symlinked Git source paths are unsupported")
    source = source.resolve(strict=True)
    env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0")
    # Do not permit caller-supplied repository/index/object selectors to redirect
    # verification away from the explicitly selected source.
    for key in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(key, None)
    command = ["git", "--no-replace-objects", "-C", str(source),
               "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null"]
    def git(*args):
        try:
            return subprocess.run(command + list(args), env=env, check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        except subprocess.CalledProcessError as error:
            raise ValueError("Git source verification failed") from error
    if Path(os.fsdecode(git("rev-parse", "--show-toplevel").strip())).resolve() != source:
        raise ValueError("Git source must identify the checkout root")
    if git("rev-parse", "--verify", "HEAD^{commit}").decode().strip() != revision:
        raise ValueError("Git checkout HEAD does not match the pinned commit")
    if git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=matching"):
        raise ValueError("Git source contains local changes or extra files; preserve it")
    process = subprocess.Popen(command + ["cat-file", "--batch"], env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
    total, count = 0, 0
    def read_object(oid, kind):
        nonlocal total, count
        process.stdin.write(oid.encode() + b"\n")
        process.stdin.flush()
        header = process.stdout.readline().split()
        if len(header) != 3 or header[0].decode() != oid or header[1].decode() != kind:
            raise ValueError("Missing or invalid Git source object")
        size = int(header[2])
        total += size
        count += 1
        if size < 0 or total > MAX_EXPANDED_BYTES or count > 50000:
            raise ValueError("Git source exceeds export limits")
        data = process.stdout.read(size)
        if len(data) != size or process.stdout.read(1) != b"\n":
            raise ValueError("Truncated Git source object")
        actual = hashlib.sha1(kind.encode() + b" " + str(size).encode() + b"\0" + data).hexdigest()
        if actual != oid:
            raise ValueError("Git source object checksum mismatch")
        return data
    try:
        commit = read_object(revision, "commit")
        match = re.match(rb"tree ([0-9a-f]{40})\n", commit)
        if not match:
            raise ValueError("Pinned Git commit has no valid tree")
        tree = match[1].decode()
        entries, seen = {}, set()
        def walk(oid, prefix=""):
            raw = read_object(oid, "tree")
            offset = 0
            while offset < len(raw):
                space, end = raw.find(b" ", offset), raw.find(b"\0", offset)
                if space < offset or end <= space or end + 21 > len(raw):
                    raise ValueError("Invalid Git source tree entry")
                mode = raw[offset:space].decode("ascii")
                name = raw[space + 1:end].decode("utf-8")
                child = raw[end + 1:end + 21].hex()
                offset = end + 21
                if not name or name in (".", "..") or any(c in name for c in "/\\:\0") or name.casefold() == ".git":
                    raise ValueError("Unsafe Git source path")
                reserved = {"con", "prn", "aux", "nul", *[f"{kind}{n}" for kind in ("com", "lpt") for n in range(1, 10)]}
                if name.endswith((".", " ")) or name.split(".")[0].casefold() in reserved:
                    raise ValueError("Unsafe portable Git source path")
                path = prefix + name
                identity = path.casefold()
                if identity in seen:
                    raise ValueError("Duplicate Git source path")
                seen.add(identity)
                if mode == "40000":
                    walk(child, path + "/")
                elif mode in ("100644", "100755", "120000"):
                    entries[path] = (mode, read_object(child, "blob"))
                else:
                    raise ValueError("Unsupported Git source mode (including submodules)")
        walk(tree)
        # Check real checkout bytes as well: clean/smudge filters and a stale
        # index must not disguise edited source. Export still uses verified blobs.
        for name, (mode, data) in entries.items():
            target = source.joinpath(*PurePosixPath(name).parts)
            for parent in target.parents:
                if parent == source:
                    break
                if parent.is_symlink():
                    raise ValueError("Symlinked Git source parent")
            info = target.lstat()
            if mode == "120000":
                # Git on Windows commonly checks out a symlink as its exact
                # link-blob text when core.symlinks=false. Both representations
                # are verified, and neither is followed during export.
                actual = (os.fsencode(os.readlink(target)) if stat.S_ISLNK(info.st_mode)
                          else target.read_bytes() if stat.S_ISREG(info.st_mode) else None)
                if actual != data:
                    raise ValueError("Git source link does not match its committed blob")
            elif (not stat.S_ISREG(info.st_mode) or target.read_bytes() != data
                  or (os.name != "nt" and bool(info.st_mode & 0o111) != (mode == "100755"))):
                raise ValueError("Git source file does not match its committed blob")
        for name, (mode, data) in entries.items():
            if mode == "120000":
                link = PurePosixPath(os.fsdecode(data))
                original = entries.get(str(PurePosixPath(name).parent / link))
                if (link.is_absolute() or len(link.parts) != 1 or link.parts[0] in (".", "..")
                        or original is None or original[0] not in ("100644", "100755")):
                    raise ValueError("Unsafe Git source link")
                mode, data = original
            target = destination.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(data)
            target.chmod(0o755 if mode == "100755" else 0o644)
        return {"method": "git-object-hash", "commit": revision, "tree": tree}
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()


def fetch(lock: dict, cache: Path, supplied_archive: Path | None = None) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    archive = supplied_archive or cache / f"{lock['commit']}.tar.gz"
    if not archive.exists():
        if supplied_archive is not None:
            raise ValueError(f"Archive does not exist: {archive}")
        if not lock["archive_url"].startswith("https://"):
            raise ValueError("Source download must use HTTPS")
        fd, download = tempfile.mkstemp(prefix="download-", dir=cache)
        try:
            with os.fdopen(fd, "wb") as output:
                with urllib.request.urlopen(lock["archive_url"], timeout=120) as response:
                    total = 0
                    while block := response.read(1024 * 1024):
                        total += len(block)
                        if total > MAX_ARCHIVE_BYTES:
                            raise ValueError("Source download exceeds size limit")
                        output.write(block)
            if digest(Path(download)) != lock["archive_sha256"]:
                raise ValueError("Source archive checksum mismatch")
            os.replace(download, archive)
        finally:
            Path(download).unlink(missing_ok=True)
    if archive.stat().st_size > MAX_ARCHIVE_BYTES or digest(archive) != lock["archive_sha256"]:
        raise ValueError("Source archive checksum mismatch; refusing to use it")
    source = cache / lock["commit"]
    stamp = source / ".herspers-source.json"
    if source.exists():
        if not stamp.is_file() or json.loads(stamp.read_text()) != lock:
            raise ValueError(f"Existing source has different provenance; preserve it: {source}")
        # Like a normal checkout, this cache can contain deliberate local edits.
        # The stamp records origin; it does not attest an unmodified source tree.
        return source
    stage = Path(tempfile.mkdtemp(prefix="source-", dir=cache))
    try:
        unpack(archive, stage, lock["archive_root"])
        (stage / ".herspers-source.json").write_text(json.dumps(lock, indent=2) + "\n")
        os.rename(stage, source)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use a previously downloaded archive (still checksum checked)")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "upstream")
    args = parser.parse_args()
    try:
        lock = json.loads((ROOT / "upstream.lock.json").read_text())
        print(fetch(lock, args.cache.resolve(), args.archive.resolve() if args.archive else None))
        return 0
    except (OSError, ValueError, tarfile.TarError) as error:
        print(f"fetch_upstream: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
