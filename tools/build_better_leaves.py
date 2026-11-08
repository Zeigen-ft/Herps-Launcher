#!/usr/bin/env python3
"""Rebuild the licensed Better Leaves subset; never execute archive contents."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/better_leaves"
PACKAGE_NAME = "Herps-Better-Leaves-9.6-MC26.3.zip"
SOURCE_SHA256 = "cbeeccd774f910ed270dbe9651d789a8f785d055499f846e466d86f9cae91e90"
FORMAT = [97, 1]
MAX_ZIP = 8 << 20
MAX_FILE = 1 << 20
MAX_TOTAL = 64 << 20


def digest(data):
    return hashlib.sha256(data).hexdigest()


def path_name(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or ".." in p.parts or "\\" in name
            or ":" in name or str(p) != name or any(ord(c) < 32 for c in name)):
        raise ValueError("Unsafe or ambiguous resource-pack path")
    return p


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Non-finite JSON number")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def ordinary(root, name):
    p = root.joinpath(*path_name(name).parts)
    for part in [root, *p.relative_to(root).parents]:
        candidate = part if part == root else root / part
        if candidate.is_symlink() or candidate.is_junction():
            raise ValueError("Linked resource-pack source is unsupported")
    if p.is_symlink() or p.is_junction() or not p.is_file() or p.stat().st_size > MAX_FILE:
        raise ValueError("Missing, linked or oversized resource-pack file")
    return p


def read_archive(path, expected_sha=SOURCE_SHA256):
    """Read bounded regular ZIP entries; CLI always requires the original pin."""
    if path.is_symlink() or path.is_junction() or not path.is_file() or path.stat().st_size > MAX_ZIP:
        raise ValueError("Missing, linked or oversized input ZIP")
    raw = path.read_bytes()
    if expected_sha is not None and digest(raw) != expected_sha:
        raise ValueError("Original Better Leaves archive SHA-256 differs from the inspected input")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if len(entries) > 10000 or sum(i.file_size for i in entries) > MAX_TOTAL:
            raise ValueError("Archive entry/expansion limit exceeded")
        seen = set()
        for item in entries:
            name = item.filename.rstrip("/") if item.is_dir() else item.filename
            path_name(name)
            key = name.casefold()
            if key in seen:
                raise ValueError("Duplicate or case-colliding archive path")
            seen.add(key)
            kind = stat.S_IFMT(item.external_attr >> 16)
            if (kind not in (0, stat.S_IFREG, stat.S_IFDIR) or item.flag_bits & 1
                    or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or item.file_size > MAX_FILE):
                raise ValueError("Unsupported linked/encrypted/oversized archive entry")
        return {i.filename: z.read(i) for i in entries if not i.is_dir()}


def identifier(value):
    if not isinstance(value, str):
        raise ValueError("Resource identifier must be text")
    value = value if ":" in value else "minecraft:" + value
    if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", value):
        raise ValueError("Invalid resource identifier")
    namespace, name = value.split(":", 1)
    path_name(name)
    return namespace, name


def validate_graph(files, target_blocks):
    models = {}
    for name, raw in files.items():
        if name.startswith("assets/") and name.endswith(".json"):
            value = strict_json(raw)
            parts = name.split("/")
            if parts[2] == "models":
                models[parts[1] + ":" + "/".join(parts[3:])[:-5]] = value
    reached, textures = set(), set()
    def visit(name, trail=()):
        name = ":".join(identifier(name))
        if name in trail:
            raise ValueError("Cyclic model parent")
        if name == "minecraft:block/block":
            return {}, []
        if name not in models:
            raise ValueError("Missing model parent/reference: " + name)
        reached.add(name)
        value = models[name]
        slots, inherited = visit(value["parent"], (*trail, name)) if "parent" in value else ({}, [])
        slots = {**slots, **value.get("textures", {})}
        return slots, value.get("elements", inherited)
    def check_faces(slots, elements):
        def texture(slot):
            seen = set()
            while slot.startswith("#"):
                if slot in seen or slot[1:] not in slots:
                    raise ValueError("Unresolved/cyclic texture alias")
                seen.add(slot); slot = slots[slot[1:]]
            ns, path = identifier(slot)
            path = f"assets/{ns}/textures/{path}.png"
            if path not in files:
                raise ValueError("Missing leaf texture: " + path)
            textures.add(path)
        for element in elements:
            for face in element["faces"].values():
                texture(face["texture"])
    variants = 0
    for block in target_blocks:
        name = f"assets/minecraft/blockstates/{block}.json"
        definition = strict_json(files[name])
        if set(definition) != {"variants"} or set(definition["variants"]) != {""}:
            raise ValueError("Unexpected leaf blockstate structure")
        choices = definition["variants"][""]
        for choice in choices if isinstance(choices, list) else [choices]:
            check_faces(*visit(choice["model"])); variants += 1
    if reached != set(models):
        raise ValueError("Unused model included in focused pack")
    pngs = {n for n in files if n.startswith("assets/") and n.endswith(".png")}
    if textures != pngs:
        raise ValueError("Unused/missing texture in focused pack")
    return {"blocks": len(target_blocks), "models": len(models), "textures": len(textures),
            "blockstate_variants": variants, "external_parent": "minecraft:block/block"}


def payload(source=SOURCE, original=None):
    record = strict_json(ordinary(source, "upstream.json").read_bytes())
    if record["archive_sha256"] != SOURCE_SHA256 or record["target_resource_format"] != FORMAT:
        raise ValueError("Source provenance differs from reviewed input/target")
    supplied = read_archive(original) if original else None
    files = {}
    for name, expected in record["source_files"].items():
        path_name(name)
        if name not in ("LICENSE", "pack.png") and not name.startswith(("assets/minecraft/", "assets/betterleaves/")):
            raise ValueError("Unsupported namespace in focused source")
        raw = supplied[name] if supplied is not None else ordinary(source / "source", name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("Curated source checksum differs: " + name)
        files[name] = raw
    for name in ["pack.mcmeta", "NOTICE.txt", "README-HERPS.txt"]:
        files[name] = ordinary(source, name).read_bytes()
    meta = strict_json(files["pack.mcmeta"])["pack"]
    if meta.get("min_format") != FORMAT or meta.get("max_format") != FORMAT or meta.get("pack_format") != 97:
        raise ValueError("Pack metadata does not target the pinned resource format")
    if b"MIT License" not in files["LICENSE"] or b"2024 Motschen" not in files["LICENSE"]:
        raise ValueError("Missing upstream MIT attribution")
    return files, record, validate_graph(files, record["target_blocks"])


def package_bytes(source=SOURCE, original=None):
    files, _, _ = payload(source, original)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            z.writestr(info, raw)
    return out.getvalue()


def build(output, source=SOURCE, original=None):
    files, provenance, stats = payload(source, original)
    raw = package_bytes(source, original)
    if output.is_symlink() or output.is_junction():
        raise ValueError("Linked output folder")
    output.mkdir(parents=True, exist_ok=True)
    destination = output / PACKAGE_NAME
    if (destination.is_symlink() or destination.is_junction()
            or destination.exists() and destination.read_bytes() != raw):
        raise ValueError("Preserve different or linked existing pack output")
    for name in ["pack-build.json", "SHA256SUMS.txt", "README-HERPS.txt"]:
        p = output / name
        if p.is_symlink() or p.is_junction():
            raise ValueError("Linked report output")
    destination.write_bytes(raw)
    report = {"schema": 1, "package": PACKAGE_NAME, "bytes": len(raw), "sha256": digest(raw),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "input_archive_sha256": SOURCE_SHA256, "target_game": "26.3", "resource_format": FORMAT,
        "targets": provenance["target_blocks"], "files": len(files), "native_graph": stats,
        "original_source_asset_bytes_unchanged": True, "license": "MIT", "contains_code": False,
        "requires_launcher_reinstall": False, "default_enabled": False,
        "visual_verified": False, "gameplay_verified": False, "performance_verified": False,
        "unsupported_java_mod_overrides_omitted": True,
        "files_sha256": {name: digest(data) for name, data in sorted(files.items())}}
    (output / "pack-build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS.txt").write_text(f"{digest(raw)}  {PACKAGE_NAME}\n", encoding="utf-8")
    (output / "README-HERPS.txt").write_bytes(files["README-HERPS.txt"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/better-leaves")
    parser.add_argument("--original", type=Path, help="Optionally rebuild from the exact user-supplied ZIP")
    args = parser.parse_args()
    report = build(args.output, original=args.original)
    print(json.dumps({k: v for k, v in report.items() if k != "files_sha256"}, indent=2))
