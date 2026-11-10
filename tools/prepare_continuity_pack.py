#!/usr/bin/env python3
"""Extract Continuity's included texture pack for the rebuilt native Herps renderer.

This does not convert or execute Java code. The input remains a local, user-supplied
JAR; third-party artwork is never downloaded or checked into this repository.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile

VERSION = "3.0.1+26.3"
PREFIX = "resourcepacks/default/"
MAX_ARCHIVE_BYTES = 32 << 20
MAX_EXPANDED_BYTES = 64 << 20
MAX_FILE_BYTES = 4 << 20
MAX_ENTRIES = 10000
SUPPORTED_METHODS = {"ctm", "horizontal", "top"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str, directory: bool = False) -> None:
    path = name[:-1] if directory and name.endswith("/") else name
    if (not path or len(path) > 512 or "\\" in path or ":" in path or "\0" in path
            or PurePosixPath(path).is_absolute()
            or any(part in ("", ".", "..") or part.endswith((".", " "))
                   for part in path.split("/"))):
        raise ValueError(f"Unsafe archive path: {name!r}")


def checked_files(raw: bytes) -> dict[str, bytes]:
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("Continuity archive exceeds size limit")
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ENTRIES or sum(i.file_size for i in entries) > MAX_EXPANDED_BYTES:
            raise ValueError("Continuity archive exceeds expansion limits")
        seen: set[str] = set()
        for entry in entries:
            # ZipInfo keeps the raw stored name separately: on Windows its
            # filename normalizes backslashes, and every OS truncates NULs.
            # Check both so normalization cannot hide unsafe unused entries.
            safe_name(entry.orig_filename, entry.orig_filename.endswith("/"))
            safe_name(entry.filename, entry.is_dir())
            if entry.orig_filename != entry.filename:
                raise ValueError("Unsafe normalized archive path")
            identity = entry.filename.rstrip("/").casefold()
            if identity in seen:
                raise ValueError("Duplicate archive path")
            seen.add(identity)
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Archive links and special files are unsupported")
            if entry.flag_bits & 1 or entry.file_size > MAX_FILE_BYTES:
                raise ValueError("Encrypted or oversized archive entry")
            if not entry.is_dir():
                # Reading through ZipFile verifies each selected entry's CRC.
                if (entry.filename in ("fabric.mod.json", "LICENSE_continuity")
                        or entry.filename.startswith(PREFIX)):
                    files[entry.filename] = archive.read(entry)
    return files


def build(raw: bytes) -> tuple[bytes, dict]:
    files = checked_files(raw)
    try:
        mod = json.loads(files["fabric.mod.json"])
        metadata = json.loads(files[PREFIX + "pack.mcmeta"])
        license_text = files["LICENSE_continuity"]
    except (KeyError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Missing or invalid Continuity metadata, pack or license") from error
    if (not isinstance(mod, dict) or mod.get("id") != "continuity"
            or mod.get("version") != VERSION or mod.get("license") != "LGPL-3.0-only"):
        raise ValueError(f"Only Continuity {VERSION} with its declared license is supported")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("pack"), dict):
        raise ValueError("Invalid built-in pack metadata")
    if not license_text.strip():
        raise ValueError("Continuity license is empty")
    selected: dict[str, bytes] = {}
    methods: collections.Counter[str] = collections.Counter()
    for name, data in files.items():
        if not name.startswith(PREFIX):
            continue
        relative = name[len(PREFIX):]
        if relative in ("pack.mcmeta", "pack.png"):
            selected[relative] = data
        elif relative.startswith("assets/continuity/optifine/ctm/programmer_art/"):
            # The native overlay does not retain the selected source-pack identity,
            # so @programmer_art cannot be evaluated faithfully yet.
            continue
        elif relative.startswith("assets/continuity/optifine/ctm/default/"):
            if not relative.endswith((".png", ".properties")):
                raise ValueError(f"Unsupported built-in resource: {relative}")
            if relative.endswith(".properties"):
                properties: dict[str, str] = {}
                for line in data.decode("utf-8").splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith(("#", "!")):
                        continue
                    key, sep, value = stripped.partition("=")
                    if not sep or key.strip() in properties:
                        raise ValueError(f"Invalid built-in CTM properties: {relative}")
                    properties[key.strip()] = value.strip()
                method = properties.get("method", "ctm")
                if method not in SUPPORTED_METHODS:
                    raise ValueError(f"Unsupported connection method: {method}")
                methods[method] += 1
            selected[relative] = data
        else:
            raise ValueError(f"Unexpected file in built-in texture pack: {relative}")
    if not methods or not any(n.endswith(".png") and n.startswith("assets/") for n in selected):
        raise ValueError("Built-in connected textures are missing")
    metadata = {"pack": {
        "pack_format": 97,
        "min_format": [97, 1],
        "max_format": [97, 1],
        "description": "Continuity included textures by PepperCode1 — native Herps CTM build required",
    }}
    selected["pack.mcmeta"] = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode()
    selected["LICENSE_continuity"] = license_text
    provenance = {
        "source_mod": "continuity",
        "source_version": VERSION,
        "source_sha256": digest(raw),
        "source_license": mod["license"],
        "authors": mod.get("authors", []),
        "source_url": "https://github.com/PepperCode1/Continuity",
        "connection_rules": dict(sorted(methods.items())),
        "requires": "Herps engine with native CTM/horizontal/top support",
        "java_code_included": False,
        "glass_pane_culling_companion_included": False,
        "programmer_art_variant_included": False,
        "emissive_mod_implementation_included": False,
        "gameplay_verified": False,
    }
    selected["herps-continuity-provenance.json"] = (json.dumps(provenance, indent=2) + "\n").encode()
    selected["HERPS-NOTES.txt"] = (
        "Continuity included connected textures, extracted from your local JAR.\n"
        "Artwork and CTM rules: PepperCode1 / Continuity; original license is included.\n"
        "Requires the rebuilt native Herps engine with CTM, horizontal and top support.\n"
        "Unmodified released Herps engines do not implement these connection rules.\n"
        "This is not the Continuity Java mod. No Java code is executed or included.\n"
        "The separate glass-pane culling companion is intentionally not included.\n"
        "The Programmer Art variant is not included; use default vanilla textures.\n"
        "Place this ZIP in your active profile's resourcepacks folder and select it\n"
        "in Options > Resource Packs after installing the rebuilt native game.\n"
        "Extraction and static inspection do not establish in-game rendering.\n"
    ).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as output:
        for name, data in sorted(selected.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            output.writestr(info, data)
    result = buffer.getvalue()
    return result, {**provenance, "output_sha256": digest(result), "output_files": len(selected)}


def prepare(source: Path, destination: Path) -> dict:
    if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Expected a bounded regular Continuity JAR")
    result, report = build(source.read_bytes())
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise ValueError("Refusing output through a symbolic link")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file() or destination.read_bytes() != result:
            raise ValueError(f"Existing output differs; preserve it: {destination}")
        return report
    # Publish only a complete verified archive; exclusive creation preserves a concurrent output.
    descriptor, staged_name = tempfile.mkstemp(prefix=".continuity-", dir=destination.parent)
    staged = Path(staged_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(result)
        with zipfile.ZipFile(staged) as archive:
            if archive.testzip() is not None:
                raise ValueError("Generated pack failed integrity validation")
        os.link(staged, destination)
    finally:
        staged.unlink(missing_ok=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="User-supplied Continuity 3.0.1+26.3 JAR")
    parser.add_argument("output", type=Path, help="New connected-texture ZIP; differing output is preserved")
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.source, args.output), indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"prepare_continuity_pack: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
