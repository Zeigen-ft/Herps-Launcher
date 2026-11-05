#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Standalone, offline RLCraft 2.9.3 inventory and bounded private export.

Python 3.12; standard library only. Never extracts archive paths, imports mod
code, executes Java/scripts, fetches dependencies or uploads anything. Export
ZIPs contain fixed-name byte chunks, not directly extractable modpack entries.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZIP_STORED, ZipFile

MIB = 1 << 20
PART_BYTES = 24 * MIB
TRANSFER_LIMIT = 32 * MIB  # every completed export ZIP must be strictly smaller
MAX_SOURCE = 4 << 30
MAX_EXPANDED = 8 << 30
MAX_ENTRIES = 100000
MAX_CENTRAL = 32 * MIB
MAX_METADATA = 2 * MIB
MAX_JAR = 128 * MIB
MAX_NESTED_EXPANDED = 2 << 30
MAX_NESTED_ENTRIES = 50000
MAX_NESTED_TOTAL = 4 << 30
MAX_NESTED_TOTAL_ENTRIES = 200000
CHUNK = MIB
SCHEMA = 1


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def read_json(data, *, strict=True):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate JSON key; identity/dependencies are ambiguous")
            value[key] = item
        return value
    return json.loads(data, object_pairs_hook=unique, strict=strict)


def regular(path):
    if (path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())
            or not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode)):
        raise ValueError("Choose an ordinary local ZIP file, not a link or special file")


def zip_preflight(stream, size):
    """Bound the central directory before ZipFile allocates its member table."""
    tail_size = min(size, 65535 + 22)
    stream.seek(size - tail_size)
    tail = stream.read(tail_size)
    position = len(tail)
    while True:
        position = tail.rfind(b"PK\x05\x06", 0, position)
        if position < 0:
            raise ValueError("ZIP end record is missing or malformed")
        if position + 22 <= len(tail):
            values = struct.unpack_from("<4s4H2LH", tail, position)
            if position + 22 + values[-1] == len(tail):
                break
    _, disk, cd_disk, disk_count, count, cd_bytes, cd_offset, _ = values
    eocd_offset = size - tail_size + position
    if disk or cd_disk or disk_count != count:
        raise ValueError("Multi-disk ZIPs are not supported")
    if count == 65535 or cd_bytes == 0xffffffff or cd_offset == 0xffffffff:
        if eocd_offset < 20:
            raise ValueError("Missing ZIP64 locator")
        stream.seek(eocd_offset - 20)
        signature, disk, offset, disks = struct.unpack("<4sLQL", stream.read(20))
        if signature != b"PK\x06\x07" or disk or disks != 1 or offset > eocd_offset - 56:
            raise ValueError("Invalid ZIP64 locator")
        stream.seek(offset)
        fields = struct.unpack("<4sQ2H2L4Q", stream.read(56))
        if fields[0] != b"PK\x06\x06" or fields[1] < 44 or fields[4] or fields[5] or fields[6] != fields[7]:
            raise ValueError("Invalid ZIP64 end record")
        count, cd_bytes, cd_offset = fields[7:10]
        eocd_offset = offset
    if count > MAX_ENTRIES or cd_bytes > MAX_CENTRAL or cd_offset + cd_bytes > eocd_offset:
        raise ValueError("ZIP central directory exceeds safe inspection bounds")
    stream.seek(0)


def check_members(zipped, *, nested=False):
    entries = zipped.infolist()
    if len(entries) > (MAX_NESTED_ENTRIES if nested else MAX_ENTRIES):
        raise ValueError("Too many archive members")
    total, seen = 0, set()
    anomalies = []
    for info in entries:
        name = info.orig_filename
        if (not name or len(name) > 2048 or "\\" in name or ":" in name
                or name.startswith("/") or any(ord(c) < 32 for c in name)
                or any(p in ("", ".", "..") for p in name.rstrip("/").split("/"))):
            raise ValueError("Unsafe archive member path (nothing was extracted)")
        key = name.rstrip("/").casefold()
        if key in seen or info.flag_bits & 1:
            raise ValueError("Duplicate/case-colliding or encrypted archive member")
        seen.add(key)
        mode = stat.S_IFMT(info.external_attr >> 16)
        if info.is_dir():
            if info.file_size:
                raise ValueError("Directory entry contains file bytes")
            if mode not in (0, stat.S_IFDIR):
                # Old Maven JARs have invalid bits on empty directories. This
                # is metadata-only inspection, not permission to import them.
                anomalies.append({"path": name, "unix_mode": oct(info.external_attr >> 16)})
        elif mode not in (0, stat.S_IFREG):
            raise ValueError("Link or special member is not accepted")
        total += info.file_size
        if total > (MAX_NESTED_EXPANDED if nested else MAX_EXPANDED):
            raise ValueError("Declared uncompressed bytes exceed inspection bounds")
    return entries, anomalies


def bounded_read(zipped, info, maximum=MAX_METADATA):
    if info.file_size > maximum:
        raise ValueError("Metadata member exceeds its bounded read limit")
    with zipped.open(info) as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum or len(data) != info.file_size:
        raise ValueError("Metadata member size differs from its declaration")
    return data


def member_hash(zipped, info):
    count, sha = 0, hashlib.sha256()
    with zipped.open(info) as stream:
        while block := stream.read(CHUNK):
            count += len(block)
            if count > info.file_size:
                raise ValueError("Archive member expanded beyond its declared size")
            sha.update(block)
    if count != info.file_size:
        raise ValueError("Truncated archive member")
    return sha.hexdigest()


def target_identity(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("minecraft"), dict):
        raise ValueError("Pack identity must contain a Minecraft object")
    minecraft = manifest["minecraft"]
    name, version = manifest.get("name"), manifest.get("version")
    loaders = minecraft.get("modLoaders", []) if isinstance(minecraft, dict) else []
    matches = (isinstance(name, str) and name.strip().casefold() == "rlcraft"
        and isinstance(version, str) and re.fullmatch(r"(?:release\s+)?v?2\.9\.3", version.strip(), re.I) is not None
        and minecraft.get("version") == "1.12.2" and isinstance(loaders, list)
        and any(isinstance(v, dict) and re.fullmatch(r"forge-14\.23\.5\.\d+", str(v.get("id", ""))) for v in loaders))
    return {"name": name, "version": version, "minecraft": minecraft.get("version"),
        "loaders": loaders, "matches_rlcraft_2_9_3": bool(matches),
        "note": "Identity is the archive's declaration, not authenticated publisher provenance or gameplay compatibility"}


class Labels(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items, self.current = [], None
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = {"url": dict(attrs).get("href", ""), "name": ""}
    def handle_data(self, value):
        if self.current is not None:
            self.current["name"] += value
    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.items.append(self.current)
            self.current = None


def class_constants(data):
    """Only the constant pool; never interprets bytecode or class attributes."""
    if len(data) < 10 or data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("Invalid class header")
    cursor, index, strings = 10, 1, []
    count = int.from_bytes(data[8:10], "big")
    while index < count:
        if cursor >= len(data):
            raise ValueError("Truncated constant pool")
        tag = data[cursor]
        cursor += 1
        if tag == 1:
            if cursor + 2 > len(data): raise ValueError("Truncated UTF length")
            size = int.from_bytes(data[cursor:cursor + 2], "big")
            cursor += 2
            end = cursor + size
            if end > len(data): raise ValueError("Truncated UTF constant")
            strings.append(data[cursor:end].decode("utf-8", errors="replace"))
            cursor = end
        else:
            size = {3: 4, 4: 4, 5: 8, 6: 8, 7: 2, 8: 2, 9: 4, 10: 4, 11: 4,
                    12: 4, 15: 3, 16: 2, 17: 4, 18: 4, 19: 2, 20: 2}.get(tag)
            if size is None or cursor + size > len(data): raise ValueError("Unknown/truncated constant pool entry")
            cursor += size
            if tag in (5, 6): index += 1
        index += 1
    return strings


def jar_inventory(outer, info, nested_listing, budget):
    result = {"path": info.filename, "sha256": member_hash(outer, info), "metadata": [],
        "declared_dependencies": [], "dependency_string_candidates": [], "maven": [],
        "manifest_hooks": {}, "entrypoint_candidates": [], "mixin_configs": [],
        "access_changes": [], "licenses": [], "class_count": 0, "class_scan_errors": [],
        "nested_jars": [], "unknowns": [], "java_executed": False, "compatible": False}
    if info.file_size > MAX_JAR:
        result["unknowns"].append("JAR metadata scan blocked by 128 MiB per-JAR bound; original bytes retained in archive export")
        return result
    with tempfile.SpooledTemporaryFile(max_size=8 * MIB) as local:
        with outer.open(info) as stream:
            shutil.copyfileobj(stream, local, CHUNK)
        zip_preflight(local, info.file_size)
        with ZipFile(local) as jar:
            entries, anomalies = check_members(jar, nested=True)
            budget["entries"] += len(entries)
            budget["bytes"] += sum(i.file_size for i in entries)
            if budget["entries"] > MAX_NESTED_TOTAL_ENTRIES or budget["bytes"] > MAX_NESTED_TOTAL:
                raise ValueError("Aggregate nested-JAR inspection budget exhausted; dependencies remain unverified")
            result["directory_mode_anomalies"] = anomalies
            class_bytes = 0
            for item in entries:
                name = item.filename
                row = {"jar": info.filename, "path": name, "bytes": item.file_size,
                       "directory": item.is_dir(), "sha256": None if item.is_dir() else member_hash(jar, item)}
                nested_listing.write(json.dumps(row, ensure_ascii=True) + "\n")
                if item.is_dir(): continue
                if name == "mcmod.info":
                    raw = bounded_read(jar, item)
                    try:
                        # Record legacy descriptions with literal newlines, but
                        # keep duplicate identity keys rejected.
                        value = read_json(raw)
                    except json.JSONDecodeError:
                        value = read_json(raw, strict=False)
                        result["unknowns"].append("mcmod.info required permissive legacy JSON parsing; not loader acceptance")
                    records = value if isinstance(value, list) else value.get("modList", [value]) if isinstance(value, dict) else []
                    result["metadata"] = records
                    for record in records:
                        if isinstance(record, dict):
                            result["declared_dependencies"].append({k: record.get(k) for k in ("modid", "dependencies", "requiredMods", "dependants", "useDependencyInformation")})
                elif name == "META-INF/MANIFEST.MF":
                    text = re.sub(r"\r?\n ", "", bounded_read(jar, item).decode("utf-8", errors="replace"))
                    values = {k.lower(): v.strip() for line in text.splitlines() if ":" in line for k, v in [line.split(":", 1)]}
                    result["manifest_hooks"] = {k: values[k] for k in ("fmlcoreplugin", "tweakclass", "fmlat", "maven-artifact", "implementation-version", "mixinconfigs") if k in values}
                elif name.endswith("/pom.xml"):
                    text = bounded_read(jar, item)
                    if b"<!DOCTYPE" in text or b"<!ENTITY" in text:
                        raise ValueError("XML entity declarations are not accepted")
                    tree = ET.fromstring(text)
                    def value(node, key):
                        child = next((v for v in node if v.tag.rsplit("}", 1)[-1] == key), None)
                        return child.text if child is not None else None
                    deps = [n for n in tree.iter() if n.tag.rsplit("}", 1)[-1] == "dependency"]
                    licenses = [n for n in tree.iter() if n.tag.rsplit("}", 1)[-1] == "license"]
                    result["maven"].append({"path": name, "dependencies": [{k: value(n, k) for k in ("groupId", "artifactId", "version", "scope", "optional")} for n in deps],
                        "license_claims": [{k: value(n, k) for k in ("name", "url")} for n in licenses]})
                if "mixin" in name.lower() and name.endswith(".json"):
                    result["mixin_configs"].append({"path": name, "sha256": row["sha256"]})
                if name.lower().endswith(("_at.cfg", ".accesswidener")):
                    result["access_changes"].append({"path": name, "sha256": row["sha256"]})
                if any(v in name.lower() for v in ("license", "licence", "notice", "copying")):
                    result["licenses"].append({"path": name, "sha256": row["sha256"], "scope": "This member's declared scope only; not whole-JAR clearance"})
                if name.lower().endswith(".jar"):
                    result["nested_jars"].append({"path": name, "sha256": row["sha256"], "dependency_metadata": "Unresolved nested JAR; inspect original export before declaring closure"})
                if name.endswith(".class"):
                    result["class_count"] += 1
                    class_bytes += item.file_size
                    if item.file_size > 4 * MIB or class_bytes > 64 * MIB:
                        result["class_scan_errors"].append({"path": name, "reason": "Constant-pool scan bound; file hash still recorded"})
                        continue
                    try:
                        constants = class_constants(bounded_read(jar, item, 4 * MIB))
                        if "Lnet/minecraftforge/fml/common/Mod;" in constants:
                            result["entrypoint_candidates"].append(name)
                        declarations = [v for v in constants if re.search(r"(?:required-)?(?:after|before):[A-Za-z0-9_.-]+", v)]
                        if declarations:
                            result["dependency_string_candidates"].append({"class": name, "strings": declarations, "scope": "Constant-pool candidates, not a complete annotation/linkage proof"})
                    except ValueError as error:
                        result["class_scan_errors"].append({"path": name, "reason": str(error)})
    result["dependency_closure_verified"] = False
    result["unknowns"].append("Absent declarations do not prove absent dependencies; no JVM/Forge runtime or gameplay verification")
    return result


def write_parts(source, destination, dataset, *, part_bytes=PART_BYTES):
    if not 1 <= part_bytes <= PART_BYTES:
        raise ValueError("Export chunk size is outside safe bounds")
    size, full_sha = source.stat().st_size, sha256(source)
    count = max(1, (size + part_bytes - 1) // part_bytes)
    rows, streamed = [], hashlib.sha256()
    with source.open("rb") as stream:
        for number in range(1, count + 1):
            data = stream.read(part_bytes)
            streamed.update(data)
            part = {"schema": SCHEMA, "dataset": dataset, "part": number, "parts": count,
                "offset": (number - 1) * part_bytes, "bytes": len(data), "payload_sha256": hashlib.sha256(data).hexdigest(),
                "source_bytes": size, "source_sha256": full_sha}
            path = destination / f"{dataset}-{number:04d}-of-{count:04d}.zip"
            with ZipFile(path, "x", compression=ZIP_STORED) as zipped:
                zipped.writestr("part.json", json_bytes(part))
                zipped.writestr("payload.bin", data)
            if path.stat().st_size >= TRANSFER_LIMIT:
                raise ValueError("Export ZIP exceeds the strict 32 MiB boundary")
            rows.append({"file": path.name, "zip_bytes": path.stat().st_size, "sha256": sha256(path), **part})
        if stream.read(1) or streamed.hexdigest() != full_sha:
            raise ValueError("Input changed while exporting")
    return rows


def inspect_archive(source, output, *, part_bytes=PART_BYTES, progress=print):
    source, output = Path(source).expanduser().absolute(), Path(output).expanduser().absolute()
    regular(source)
    if source.stat().st_size > MAX_SOURCE:
        raise ValueError("Source ZIP exceeds 4 GiB inspection bound")
    if output.exists() or output.is_symlink():
        raise ValueError("Choose a new output folder; existing output is never overwritten")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(mode=0o700)
    report = {"schema": SCHEMA, "tool": "Herspers RLCraft 2.9.3 local inspector", "status": "failed",
        "source_file": source.name, "source_bytes": source.stat().st_size, "source_sha256": sha256(source),
        "created_utc": datetime.now(timezone.utc).isoformat(), "java_executed": False, "network_used": False,
        "gameplay_verified": False, "dependency_closure_verified": False, "file_inventory_complete": False,
        "limits": {"export_payload_bytes": PART_BYTES, "export_zip_strict_limit": TRANSFER_LIMIT,
                   "source_bytes": MAX_SOURCE, "expanded_bytes": MAX_EXPANDED, "entries": MAX_ENTRIES,
                   "jar_bytes": MAX_JAR, "central_directory_bytes": MAX_CENTRAL}, "warnings": []}
    signature = source.stat()
    try:
        progress("Reading ZIP metadata; no content is executed…")
        with source.open("rb") as stream:
            zip_preflight(stream, signature.st_size)
            with ZipFile(stream) as zipped:
                entries, anomalies = check_members(zipped)
                manifest_info = next((i for i in entries if i.orig_filename == "manifest.json" and not i.is_dir()), None)
                if manifest_info is None:
                    raise ValueError("Root manifest.json is missing; archive identity is not established")
                raw_manifest = bounded_read(zipped, manifest_info)
                manifest = read_json(raw_manifest)
                if not isinstance(manifest, dict): raise ValueError("Pack manifest must be an object")
                identity = target_identity(manifest)
                report["identity"] = identity
                if not identity["matches_rlcraft_2_9_3"]:
                    raise ValueError("Target mismatch: archive must declare RLCraft 2.9.3 / Minecraft 1.12.2 / Forge; a 2.8.2 reference is not accepted")
                report["directory_mode_anomalies"] = anomalies
                parser = Labels()
                html_info = next((i for i in entries if i.orig_filename == "modlist.html"), None)
                raw_html = bounded_read(zipped, html_info) if html_info is not None else b""
                parser.feed(raw_html.decode("utf-8", errors="replace"))
                labels = {}
                for row in parser.items:
                    match = re.search(r"/mc-mods/(\d+)(?:/|$)", row["url"])
                    if match: labels.setdefault(int(match[1]), []).append(row)
                declared = manifest.get("files")
                if not isinstance(declared, list): raise ValueError("Manifest files must be an array")
                requirements = []
                for index, item in enumerate(declared):
                    if not isinstance(item, dict) or type(item.get("projectID")) is not int or type(item.get("fileID")) is not int:
                        raise ValueError("Invalid CurseForge project/file identity")
                    matches = labels.get(item["projectID"], [])
                    requirements.append({"manifest_index": index, **item,
                        "project_label": matches[0] if len(matches) == 1 else None,
                        "version": "Unknown until the exact local JAR is identity-mapped", "dependencies": None,
                        "license": "Unverified for this file", "state": "Unresolved exact file/dependency/rights evidence"})
                jars, extensions, expanded = [], Counter(), 0
                nested_budget = {"entries": 0, "bytes": 0}
                with (output / "files.jsonl").open("w", encoding="utf-8", newline="\n") as listing, (output / "files.sha256").open("w", encoding="utf-8", newline="\n") as sums, (output / "nested-files.jsonl").open("w", encoding="utf-8", newline="\n") as nested:
                    for index, item in enumerate(entries, 1):
                        value = {"path": item.orig_filename, "directory": item.is_dir(), "bytes": item.file_size,
                            "compressed_bytes": item.compress_size, "crc32": f"{item.CRC:08x}",
                            "sha256": None if item.is_dir() else member_hash(zipped, item)}
                        listing.write(json.dumps(value, ensure_ascii=True) + "\n")
                        if not item.is_dir():
                            sums.write(value["sha256"] + "  " + item.orig_filename + "\n")
                            extensions[Path(item.orig_filename).suffix.lower()] += 1
                            expanded += item.file_size
                        if not item.is_dir() and item.filename.lower().endswith(".jar"):
                            try:
                                jars.append(jar_inventory(zipped, item, nested, nested_budget))
                            except (ValueError, BadZipFile, ET.ParseError) as error:
                                jars.append({"path": item.filename, "sha256": value["sha256"], "metadata_scan_blocked": str(error), "dependency_closure_verified": False})
                        if index % 100 == 0: progress(f"Hashed {index}/{len(entries)} archive entries…")
                dependencies = {"schema": SCHEMA, "manifest_requirements": requirements, "unmapped_project_labels": parser.items,
                    "physical_jars": jars, "dependency_closure_verified": False,
                    "note": "Complete inventory of declarations available in this ZIP; missing JARs, nested-JAR closure and annotation candidates remain explicit unknowns. No compatibility verdict is inferred."}
                (output / "manifest.json").write_bytes(raw_manifest)
                if raw_html: (output / "modlist.html").write_bytes(raw_html)
                (output / "dependency-inventory.json").write_bytes(json_bytes(dependencies))
                report.update(file_inventory_complete=True, entries=len(entries), uncompressed_bytes=expanded,
                    declared_requirements=len(requirements), physical_jars=len(jars), extensions=dict(extensions))
        after = source.stat()
        if (after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (signature.st_size, signature.st_mtime_ns, signature.st_ctime_ns) or sha256(source) != report["source_sha256"]:
            raise ValueError("Source archive changed during inspection")
        progress("Writing private export parts, each below 32 MiB…")
        with tempfile.TemporaryDirectory(prefix="inspection-metadata-", dir=output) as temporary:
            metadata = Path(temporary) / "metadata.zip"
            with ZipFile(metadata, "x", compression=ZIP_STORED) as zipped:
                for name in ("manifest.json", "modlist.html", "files.jsonl", "files.sha256", "nested-files.jsonl", "dependency-inventory.json"):
                    if (output / name).exists(): zipped.write(output / name, name)
            parts = write_parts(metadata, output, "metadata", part_bytes=part_bytes)
        parts += write_parts(source, output, "archive", part_bytes=part_bytes)
        if any(p["source_sha256"] != report["source_sha256"] for p in parts if p["dataset"] == "archive"):
            raise ValueError("Exported original differs from inspected input")
        report.update(status="inspected", export_parts=parts,
            warnings=["Original mod code/assets are present as inert original ZIP chunks. Private inspection only; no redistribution licence is implied.",
                      "No automatic upload. Return every listed ZIP separately; do not combine into one large file.",
                      "File hashes establish integrity, not publisher authentication, safe execution, dependency closure or playability."])
        (output / "inspection.json").write_bytes(json_bytes(report))
        summary = output / "00-summary.zip"
        with ZipFile(summary, "x", compression=ZIP_STORED) as zipped:
            zipped.writestr("inspection.json", json_bytes(report))
            zipped.writestr("RETURN-INSTRUCTIONS.txt", "Return this summary first, then all archive-*.zip and metadata-*.zip listed in inspection.json. Never run mod code. Keep bundles private; nothing is uploaded automatically.\n")
        if summary.stat().st_size >= TRANSFER_LIMIT: raise ValueError("Summary exceeds export bound")
        (output / "EXPORT-SHA256SUMS.txt").write_text("\n".join(f"{sha256(p)}  {p.name}" for p in sorted(output.glob("*.zip"))) + "\n", encoding="utf-8")
        progress(f"Inspection complete. Return 00-summary.zip plus {len(parts)} numbered ZIPs from: {output}")
        return report
    except Exception as error:
        # These paths belong exclusively to this newly created output folder.
        # Partial exports are never presented as a completed inspection.
        for path in output.glob("*.zip"): path.unlink()
        (output / "inspection.json").unlink(missing_ok=True)
        (output / "EXPORT-SHA256SUMS.txt").unlink(missing_ok=True)
        report.update(status="failed", error=str(error), export_parts=[])
        (output / "inspection-failed.json").write_bytes(json_bytes(report))
        raise


def assemble_parts(folder, output, dataset="archive"):
    """Join fixed-name payloads, verify every part and full source; no extraction."""
    folder, output = Path(folder).absolute(), Path(output).absolute()
    if dataset not in ("archive", "metadata"): raise ValueError("Unknown export dataset")
    if output.exists(): raise ValueError("Reassembly output already exists; choose a new filename")
    parts = []
    for path in sorted(folder.glob(dataset + "-*.zip")):
        regular(path)
        if path.stat().st_size >= TRANSFER_LIMIT: raise ValueError("Part ZIP is oversized")
        with path.open("rb") as stream:
            zip_preflight(stream, path.stat().st_size)
            with ZipFile(stream) as zipped:
                entries, _ = check_members(zipped)
                if {i.filename for i in entries} != {"part.json", "payload.bin"} or len(entries) != 2:
                    raise ValueError("Unexpected export members")
                claim = read_json(bounded_read(zipped, zipped.getinfo("part.json")))
                if not isinstance(claim, dict) or claim.get("schema") != SCHEMA or claim.get("dataset") != dataset:
                    raise ValueError("Invalid part identity")
                for key in ("part", "parts", "offset", "bytes", "source_bytes"):
                    if type(claim.get(key)) is not int or claim[key] < 0: raise ValueError("Invalid part counters")
                if not 1 <= claim["part"] <= claim["parts"] <= 10000 or claim["bytes"] > PART_BYTES or claim["source_bytes"] > MAX_SOURCE:
                    raise ValueError("Part counters exceed limits")
                if any(not isinstance(claim.get(k), str) or re.fullmatch("[0-9a-f]{64}", claim[k]) is None for k in ("source_sha256", "payload_sha256")):
                    raise ValueError("Invalid part checksums")
                parts.append((claim, path))
    if not parts: raise ValueError("No export parts supplied")
    parts.sort(key=lambda row: row[0]["part"])
    first = parts[0][0]
    if len(parts) != first["parts"] or [p[0]["part"] for p in parts] != list(range(1, len(parts) + 1)):
        raise ValueError("Missing or duplicate export parts")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".rlcraft-reassembly-", dir=output.parent)
    temporary = Path(temporary)
    try:
        full, offset = hashlib.sha256(), 0
        with os.fdopen(descriptor, "wb") as stream:
            for claim, path in parts:
                if any(claim[k] != first[k] for k in ("parts", "source_bytes", "source_sha256")) or claim["offset"] != offset:
                    raise ValueError("Mixed archives or discontinuous part offsets")
                with ZipFile(path) as zipped:
                    payload = bounded_read(zipped, zipped.getinfo("payload.bin"), PART_BYTES)
                if len(payload) != claim["bytes"] or hashlib.sha256(payload).hexdigest() != claim["payload_sha256"]:
                    raise ValueError("Corrupt or truncated export payload")
                stream.write(payload)
                full.update(payload)
                offset += len(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if offset != first["source_bytes"] or full.hexdigest() != first["source_sha256"]:
            raise ValueError("Reassembled source checksum differs")
        if dataset == "archive":
            with temporary.open("rb") as stream:
                zip_preflight(stream, offset)
                with ZipFile(stream) as zipped:
                    check_members(zipped)
                    if not target_identity(read_json(bounded_read(zipped, zipped.getinfo("manifest.json"))))["matches_rlcraft_2_9_3"]:
                        raise ValueError("Reassembled archive is not declared RLCraft 2.9.3")
        # Publish without replacing any existing file, including a racing one.
        created = False
        try:
            with output.open("xb") as result:
                created = True
                with temporary.open("rb") as stream:
                    shutil.copyfileobj(stream, result, CHUNK)
        except Exception:
            if created: output.unlink(missing_ok=True)
            raise
        return {"dataset": dataset, "bytes": offset, "sha256": full.hexdigest(), "path": str(output)}
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, nargs="?")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--assemble", type=Path, metavar="PARTS_FOLDER", help="Developer: reassemble verified parts, never extract modpack files")
    parser.add_argument("--dataset", choices=("archive", "metadata"), default="archive")
    args = parser.parse_args()
    if args.assemble:
        if args.output is None: parser.error("--assemble requires a new --output filename")
        print(json.dumps(assemble_parts(args.assemble, args.output, args.dataset), indent=2))
    else:
        source = args.archive
        if source is None:
            source = Path(input("Paste the full path to your original RLCraft 2.9.3 ZIP (Copy as path), then press Enter:\n").strip().strip('"'))
        output = args.output or source.parent / ("RLCraft-2.9.3-inspection-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        inspect_archive(source, output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, BadZipFile, KeyError, EOFError, struct.error, UnicodeError, RuntimeError) as error:
        print(f"Inspection stopped: {error}\nNo mod code was executed. If present, return inspection-failed.json from the new output folder.", file=sys.stderr)
        raise SystemExit(2)
