# SPDX-License-Identifier: GPL-3.0-only
"""One independent FunCraft replacement: verified manual, stopped-world backups.

No upstream FTB code/assets, Java execution, save conversion or in-place restore.
The shared launcher lock cannot stop games/servers started outside the launcher:
the user must close those too. A stable-tree check detects observed concurrent
changes; this is not a live-server snapshot/flush protocol.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from ..core import ID, digest, safe_name
from ..javamods.library import _plain

FUNCRAFT_SHA256 = "09db709ff9ddcdabdf080ba814afe3c3c453e32dfde38356b99a00bed58ee12e"
FUNCRAFT_NAME = "FunCraft - FC"
FUNCRAFT_VERSION = "Release 1.1.1 - hotfix"
FEATURE = "funcraft-manual-world-backup"
MAX_BYTES = 512 << 20
MAX_FILE_BYTES = 128 << 20
MAX_ENTRIES = 10000
MAX_MANIFEST_BYTES = 8 << 20
CHUNK = 1 << 20


def _json(data):
    def unique(pairs):
        result = {}
        for name, value in pairs:
            if name in result:
                raise ValueError("Ambiguous duplicate backup JSON key")
            result[name] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def eligibility(library, token):
    """Revalidate the managed import; a renamed/edited pack never opts in."""
    entry = library._entry(token)
    if not entry.source.is_file() or digest(entry.source) != FUNCRAFT_SHA256:
        return {"available": False, "reason": "Only the exact inspected FunCraft 1.1.1 hotfix ZIP has a replacement feature. RLCraft 2.9.3 remains uninspected."}
    with ZipFile(entry.source) as zipped:
        item = zipped.getinfo("manifest.json")
        if item.file_size > 1 << 20:
            raise ValueError("Oversized target manifest")
        manifest = _json(zipped.read(item))
    ids = [(row.get("projectID"), row.get("fileID")) for row in manifest.get("files", []) if isinstance(row, dict)]
    if ((manifest.get("name"), manifest.get("version")) != (FUNCRAFT_NAME, FUNCRAFT_VERSION)
            or (314904, 2749104) not in ids):
        raise ValueError("Target identity or FTB Backups requirement differs from the inspected pack")
    return {"available": True, "name": FUNCRAFT_NAME, "version": FUNCRAFT_VERSION,
        "feature": FEATURE, "pack_sha256": FUNCRAFT_SHA256,
        "reason": "Available: manual backup of stopped Herspers worlds. Original Java mods, live/timed backups and pack gameplay remain unsupported."}


def _relative(value, *, max_depth=32):
    if not isinstance(value, str) or not value or len(value.split("/")) > max_depth:
        raise ValueError("Invalid backup path")
    parts = value.split("/")
    reserved = {"con", "prn", "aux", "nul", *[f"{p}{i}" for p in ("com", "lpt") for i in range(1, 10)]}
    for part in parts:
        safe_name(part)
        if (part.endswith((".", " ")) or part.split(".")[0].lower() in reserved
                or any(ord(c) < 32 or c in '<>"|?*' for c in part)):
            raise ValueError("Nonportable backup path")
    if PurePosixPath(value).as_posix() != value:
        raise ValueError("Ambiguous backup path")
    return value


def _signature(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _open_source(library, path):
    library.guard._safe(path)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
    try:
        return os.fdopen(descriptor, "rb")
    except Exception:
        os.close(descriptor)
        raise


def _fingerprint_source(library, path, remaining):
    # Windows path stat and descriptor fstat need not expose identical metadata.
    # Take identity, size, timestamps and bytes from one descriptor, consistently
    # with the copy operation. Hash/size and the final rescan remain mandatory.
    with _open_source(library, path) as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Nonregular save entry")
        if before.st_size > min(MAX_FILE_BYTES, remaining):
            raise ValueError("Backup limit: at most 512 MiB total and 128 MiB per file; existing data is unchanged")
        sha, count = hashlib.sha256(), 0
        while chunk := stream.read(CHUNK):
            count += len(chunk)
            if count > before.st_size:
                raise ValueError("Save file grew while fingerprinting")
            sha.update(chunk)
        if count != before.st_size or _signature(os.fstat(stream.fileno())) != _signature(before):
            raise ValueError("Save files changed during backup; close all games/servers and retry")
        return {"bytes": count, "sha256": sha.hexdigest(), "signature": _signature(before)}


def _scan(library, source):
    library.guard._safe(source)
    if not source.is_dir():
        raise ValueError("This profile has no saves folder; no backup was created")
    files, directories, seen, total = {}, [], set(), 0
    def failed(error):
        raise error
    for folder, subdirs, names in os.walk(source, followlinks=False, onerror=failed):
        for name in sorted(subdirs + names):
            path = Path(folder) / name
            library.guard._safe(path)
            relative = _relative(path.relative_to(source).as_posix())
            if relative.casefold() in seen or len(seen) >= MAX_ENTRIES:
                raise ValueError("Ambiguous or oversized saves tree")
            seen.add(relative.casefold())
            value = path.stat(follow_symlinks=False)
            if stat.S_ISDIR(value.st_mode):
                directories.append(relative)
            elif stat.S_ISREG(value.st_mode):
                row = _fingerprint_source(library, path, MAX_BYTES - total)
                total += row["bytes"]
                files[relative] = row
            else:
                raise ValueError("Nonregular save entry")
    if not files:
        raise ValueError("This profile has no saved files; an empty folder is not a successful backup")
    return dict(sorted(files.items())), sorted(directories)


def _copy_file(library, source, relative, expected, zipped):
    path = source / relative
    with _open_source(library, path) as stream:
        observed = os.fstat(stream.fileno())
        if not stat.S_ISREG(observed.st_mode) or _signature(observed) != expected["signature"]:
            error = ValueError("Save file changed before copying")
            error.add_note(f"Relative save: {relative!r}; fingerprint={expected['signature']}; open={_signature(observed)}")
            raise error
        sha, count = hashlib.sha256(), 0
        with zipped.open("saves/" + relative, "w", force_zip64=True) as output:
            while chunk := stream.read(CHUNK):
                count += len(chunk)
                if count > expected["bytes"]:
                    raise ValueError("Save file grew during backup")
                sha.update(chunk)
                output.write(chunk)
        if (count != expected["bytes"] or sha.hexdigest() != expected["sha256"]
                or _signature(os.fstat(stream.fileno())) != expected["signature"]):
            raise ValueError("Save file changed during backup")


def verify_backup(path: Path):
    """Read and hash bounded members; never extract, restore or trust status flags.

    The manifest is an integrity inventory, not publisher authentication or proof
    that the contents constitute a valid/loadable Minecraft world.
    """
    path = Path(path).expanduser().absolute()
    _plain(path)
    if not path.is_file() or path.stat().st_size > MAX_BYTES + (16 << 20):
        raise ValueError("Missing or oversized backup ZIP")
    original_signature = _signature(path.stat(follow_symlinks=False))
    try:
        with ZipFile(path) as zipped:
            members = zipped.infolist()
            if len(members) > MAX_ENTRIES + 2 or sum(i.file_size for i in members) > MAX_BYTES + MAX_MANIFEST_BYTES:
                raise ValueError("Backup ZIP exceeds bounded limits")
            names, folded = {}, set()
            for item in members:
                name = item.orig_filename
                _relative(name.rstrip("/"), max_depth=33)  # includes the saves/ container
                kind = stat.S_IFMT(item.external_attr >> 16)
                normalized = name.rstrip("/").casefold()
                if (name in names or normalized in folded or kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or (kind == stat.S_IFDIR and not item.is_dir()) or (kind == stat.S_IFREG and item.is_dir())
                        or item.flag_bits & 1 or (item.is_dir() and item.file_size)):
                    raise ValueError("Ambiguous, encrypted or nonregular backup member")
                names[name] = item
                folded.add(normalized)
            item = names.get("backup-manifest.json")
            if item is None or item.is_dir() or item.file_size > MAX_MANIFEST_BYTES:
                raise ValueError("Missing or oversized backup manifest")
            manifest = _json(zipped.read(item))
            if (not isinstance(manifest, dict) or type(manifest.get("schema")) is not int or manifest["schema"] != 1 or manifest.get("feature") != FEATURE
                    or manifest.get("pack_sha256") != FUNCRAFT_SHA256
                    or not isinstance(manifest.get("profile"), str) or not ID.fullmatch(manifest["profile"])):
                raise ValueError("Invalid targeted backup manifest")
            files, directories = manifest.get("files"), manifest.get("directories")
            if (not isinstance(files, dict) or not files or not isinstance(directories, list)
                    or len(files) + len(directories) > MAX_ENTRIES):
                raise ValueError("Invalid or empty backup file inventory")
            expected, total = {"backup-manifest.json", "saves/"}, 0
            for directory in directories:
                expected.add("saves/" + _relative(directory) + "/")
            directory_set = set(directories)
            if len(directory_set) != len(directories):
                raise ValueError("Duplicate backup directory")
            for relative, row in files.items():
                name = "saves/" + _relative(relative)
                if (not isinstance(row, dict) or type(row.get("bytes")) is not int or not 0 <= row["bytes"] <= MAX_FILE_BYTES
                        or not isinstance(row.get("sha256"), str) or not re.fullmatch("[0-9a-f]{64}", row["sha256"])):
                    raise ValueError("Invalid backup checksum inventory")
                total += row["bytes"]
                item = names.get(name)
                if item is None or item.is_dir() or item.file_size != row["bytes"] or total > MAX_BYTES:
                    raise ValueError("Backup file is missing or has the wrong size")
                sha, count = hashlib.sha256(), 0
                with zipped.open(item) as stream:
                    while chunk := stream.read(CHUNK):
                        count += len(chunk)
                        if count > row["bytes"]:
                            raise ValueError("Backup file exceeds its declared size")
                        sha.update(chunk)
                if count != row["bytes"] or sha.hexdigest() != row["sha256"]:
                    raise ValueError("Backup checksum mismatch")
                expected.add(name)
            if set(names) != expected:
                raise ValueError("Backup contains undeclared or missing members")
            if any(not names[n].is_dir() for n in expected if n.endswith("/")):
                raise ValueError("Backup directory inventory differs")
            for relative in [*files, *directories]:
                if any(parent.as_posix() not in directory_set for parent in PurePosixPath(relative).parents if parent.as_posix() != "."):
                    raise ValueError("Backup directory hierarchy is incomplete")
        archive_sha = digest(path)
        if _signature(path.stat(follow_symlinks=False)) != original_signature:
            raise ValueError("Backup changed during verification")
        return {"schema": 1, "feature": FEATURE, "verified": True, "profile": manifest["profile"],
            "files": len(files), "bytes": total, "archive_sha256": archive_sha, "path": str(path),
            "gameplay_verified": False, "note": "Archive integrity verified; world loading and original-pack gameplay are not established"}
    except (BadZipFile, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid backup ZIP: {error}") from error


def create_backup(library, token, *, external_processes_closed=False, progress=lambda message: None):
    launcher = library.launcher
    if not external_processes_closed:
        raise ValueError("Confirm all external game/server processes are closed before backing up")
    if launcher.child is not None and launcher.child.poll() is None:
        raise ValueError("Close the running game before backing up")
    if launcher.lock_fd is not None or launcher.pending_file.exists():
        raise ValueError("An operation or unfinished game session remains; resolve it before backing up")
    library.guard._safe(launcher.state)
    library.guard._safe(launcher.game.absolute())
    launcher.acquire()
    directory, complete = None, False
    try:
        target = eligibility(library, token)
        if not target["available"]:
            raise ValueError(target["reason"])
        profile, game = launcher.config["profile"], launcher.game.absolute()
        source = game / "saves"
        progress("Checking the stopped profile's save files…")
        before, directories = _scan(library, source)
        destination = launcher.state / "targeted-backups" / "funcraft" / profile
        library.guard._safe(destination)
        destination.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-"), dir=destination))
        temporary = directory / "worlds.partial"
        manifest = {"schema": 1, "feature": FEATURE, "pack_sha256": target["pack_sha256"], "profile": profile,
            "created_at": datetime.now(timezone.utc).isoformat(), "directories": directories,
            "files": {name: {k: row[k] for k in ("bytes", "sha256")} for name, row in before.items()}}
        encoded = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if len(encoded) > MAX_MANIFEST_BYTES:
            raise ValueError("Backup manifest exceeds its limit")
        with temporary.open("xb") as stream:
            with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=5) as zipped:
                zipped.writestr("saves/", b"")
                for relative in directories:
                    zipped.writestr("saves/" + relative + "/", b"")
                for index, (relative, row) in enumerate(before.items(), 1):
                    _copy_file(library, source, relative, row, zipped)
                    if index % 100 == 0:
                        progress(f"Copied {index}/{len(before)} save files…")
                zipped.writestr("backup-manifest.json", encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if launcher.config["profile"] != profile or launcher.game.absolute() != game or _scan(library, source) != (before, directories):
            raise ValueError("Profile or save files changed; no completed backup was published")
        progress("Verifying every archived file checksum…")
        result = verify_backup(temporary)
        output = directory / "worlds.zip"
        # directory is newly created and private; no prior backup can be replaced.
        os.replace(temporary, output)
        result.update(path=str(output), source_tree_unchanged=True)
        complete = True
        return result
    finally:
        try:
            if directory is not None and not complete:
                shutil.rmtree(directory)
        finally:
            launcher.release()
