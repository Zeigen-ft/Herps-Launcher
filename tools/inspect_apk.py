#!/usr/bin/env python3
"""Inspect APK ZIP metadata and ELF headers without executing or extracting code.

Uses only Python's standard library. Embedded diagnostics and source references
are observations, not verification of an APK publisher or source equivalence.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import sys
from zipfile import BadZipFile, ZipFile

MAX_APK = 512 * 1024 * 1024
MAX_MEMBER = 128 * 1024 * 1024
MAX_UNCOMPRESSED = 512 * 1024 * 1024
MAX_ENTRIES = 10000


class AuditError(ValueError):
    """Input is malformed or exceeds a static-analysis resource limit."""


def _range(data: bytes, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise AuditError("ELF range extends beyond file")
    return data[offset:offset + size]


def inspect_elf(data: bytes) -> dict:
    if len(data) < 16 or data[:4] != b"\x7fELF":
        raise AuditError("Native library is not an ELF file")
    elf_class, encoding = data[4], data[5]
    if elf_class not in (1, 2) or encoding not in (1, 2) or data[6] != 1:
        raise AuditError("Unsupported ELF class, encoding, or version")
    endian = "<" if encoding == 1 else ">"
    header_format = endian + ("HHIIIIIHHHHHH" if elf_class == 1 else "HHIQQQIHHHHHH")
    header = struct.unpack(header_format, _range(data, 16, struct.calcsize(header_format)))
    machine, phoff, phentsize, phnum = header[1], header[4], header[8], header[9]
    ph_format = endian + ("IIIIIIII" if elf_class == 1 else "IIQQQQQQ")
    ph_size = struct.calcsize(ph_format)
    if phnum and phentsize < ph_size:
        raise AuditError("ELF program header size is too small")
    _range(data, phoff, phentsize * phnum)
    loads, dynamic = [], None
    for index in range(phnum):
        h = struct.unpack(ph_format, _range(data, phoff + index * phentsize, ph_size))
        kind = h[0]
        offset, vaddr, filesz = (h[1], h[2], h[4]) if elf_class == 1 else (h[2], h[3], h[5])
        _range(data, offset, filesz)
        if kind == 1:  # PT_LOAD
            loads.append((vaddr, offset, filesz))
        elif kind == 2:  # PT_DYNAMIC
            dynamic = (offset, filesz)
    needed, strtab, strsize = [], None, None
    if dynamic is not None:
        entry_format = endian + ("iI" if elf_class == 1 else "qQ")
        entry_size = struct.calcsize(entry_format)
        for p in range(dynamic[0], dynamic[0] + dynamic[1] - entry_size + 1, entry_size):
            tag, value = struct.unpack(entry_format, _range(data, p, entry_size))
            if tag == 0:
                break
            if tag == 1:
                needed.append(value)
            elif tag == 5:
                strtab = value
            elif tag == 10:
                strsize = value
    dependencies = []
    if needed:
        if strtab is None or strsize is None:
            raise AuditError("ELF dependencies have no dynamic string table")
        strings = None
        for vaddr, offset, size in loads:
            relative = strtab - vaddr
            if 0 <= relative and relative + strsize <= size:
                strings = _range(data, offset + relative, strsize)
                break
        if strings is None:
            raise AuditError("ELF dynamic string table is not file-backed")
        for index in needed:
            if index >= len(strings) or (end := strings.find(b"\0", index)) < 0:
                raise AuditError("ELF dependency name is out of bounds or unterminated")
            dependencies.append(strings[index:end].decode("ascii", errors="replace"))
    return {
        "format": "ELF",
        "bits": 32 if elf_class == 1 else 64,
        "endianness": "little" if encoding == 1 else "big",
        "machine_id": machine,
        "machine": {3: "x86", 40: "ARM", 62: "x86_64", 183: "AArch64"}.get(machine, "unknown"),
        "needed_libraries": dependencies,
    }


def _members(archive: ZipFile) -> dict:
    entries = archive.infolist()
    if len(entries) > MAX_ENTRIES:
        raise AuditError("ZIP contains too many entries")
    result, total = {}, 0
    for item in entries:
        path = PurePosixPath(item.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in item.filename:
            raise AuditError("ZIP contains an unsafe member path")
        if item.filename in result:
            raise AuditError("ZIP contains duplicate member names")
        if item.flag_bits & 1:
            raise AuditError("Encrypted ZIP members are unsupported")
        if item.file_size > MAX_MEMBER:
            raise AuditError("ZIP member exceeds size limit")
        total += item.file_size
        if total > MAX_UNCOMPRESSED:
            raise AuditError("ZIP uncompressed size exceeds limit")
        result[item.filename] = item
    return result


def _read(archive: ZipFile, item, limit: int = MAX_MEMBER) -> bytes:
    if item.file_size > limit:
        raise AuditError("ZIP member exceeds read limit")
    with archive.open(item) as stream:
        data = stream.read(limit + 1)
    if len(data) > limit or len(data) != item.file_size:
        raise AuditError("ZIP member actual size exceeds declared size or limit")
    return data


def audit_apk(path: Path) -> dict:
    size = path.stat().st_size
    if size > MAX_APK:
        raise AuditError("APK exceeds size limit")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    result = {"file": path.name, "size_bytes": size, "sha256": digest.hexdigest(),
              "analysis": "Static ZIP/ELF inspection only; no APK code executed",
              "native_libraries": [], "embedded_source_references": []}
    with ZipFile(path) as archive:
        members = _members(archive)
        result["entry_count"] = len(members)
        result["dex_files"] = [name for name in members if re.fullmatch(r"classes\d*\.dex", name)]
        for name, item in sorted(members.items()):
            if name.startswith("lib/") and name.endswith(".so"):
                data = _read(archive, item)
                library = inspect_elf(data)
                library.update({"path": name, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
                # Horizon diagnostics serialize these labels next to version and
                # build-id strings. Report only this anchored sequence, not any
                # arbitrary hexadecimal token occurring in compiled code.
                diagnostic = re.search(rb"pidversion(\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.-]+)?)\x00{1,8}([a-f0-9]{7,40})phase", data)
                if diagnostic:
                    library["embedded_diagnostic"] = {
                        "version": diagnostic[1].decode(), "source_commit_prefix": diagnostic[2].decode(),
                        "offset": diagnostic.start(), "evidence_label": "pidversion…phase",
                    }
                for url in ("https://github.com/Vasysik/horizon-android", "https://github.com/horizon-rust/horizon/blob/main/docs/play-with-friends.md"):
                    offset = data.find(url.encode())
                    if offset >= 0:
                        result["embedded_source_references"].append({"url": url, "library": name, "offset": offset})
                result["native_libraries"].append(library)
        for name, key in (("assets/LICENSE.txt", "license"), ("assets/THIRD_PARTY_NOTICES.md", "third_party_notices")):
            if name in members:
                data = _read(archive, members[name], 1024 * 1024)
                text = data.decode("utf-8", errors="replace")
                result[key] = {"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                               "headings": re.findall(r"^#{1,3} (.+)$", text, re.MULTILINE),
                               "first_line": text.splitlines()[0] if text.splitlines() else "",
                               "copyright_lines": [line for line in text.splitlines() if line.startswith("Copyright")]}
        engine_name = "assets/engine-data.zip"
        if engine_name in members:
            with ZipFile(io.BytesIO(_read(archive, members[engine_name]))) as engine:
                engine_members = _members(engine)
                result["engine_archive"] = {"path": engine_name, "entry_count": len(engine_members)}
                metadata_name = "horizon-resources.json"
                if metadata_name in engine_members:
                    metadata = json.loads(_read(engine, engine_members[metadata_name], 1024 * 1024))
                    if not isinstance(metadata, dict):
                        raise AuditError("Engine resource metadata must be a JSON object")
                    keys = ("schema", "minecraft", "data_version", "resource_files", "client_sha256", "server_sha256", "exporter_sha256")
                    result["engine_archive"]["resource_metadata"] = {key: metadata[key] for key in keys if key in metadata}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--output", type=Path, help="Write JSON here instead of stdout")
    args = parser.parse_args()
    try:
        result = audit_apk(args.apk)
        report = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
        if args.output:
            args.output.write_text(report, encoding="utf-8")
        else:
            sys.stdout.write(report)
    except (AuditError, OSError, BadZipFile, json.JSONDecodeError, RuntimeError, NotImplementedError) as exc:
        print(f"APK inspection failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
