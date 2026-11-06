#!/usr/bin/env python3
"""Passive inventory for the two requested legacy packs; never loads their code.

Output contains metadata, paths and hashes only, never copied classes/assets.
Run from the repository with Python 3.12. An unread archive is not a passed test.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import archive, digest
from herps_launcher.javamods.metadata import _manifest

FUNCRAFT_SHA256 = "09db709ff9ddcdabdf080ba814afe3c3c453e32dfde38356b99a00bed58ee12e"
FUNCRAFT_NAME = "FunCraft - FC"
FUNCRAFT_VERSION = "Release 1.1.1 - hotfix"


class ModList(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.current = [], None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = {"url": dict(attrs).get("href", ""), "name": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["name"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def jar_inventory(data: bytes, path: str, temporary: Path):
    sha = hashlib.sha256(data).hexdigest()
    local = temporary / (sha + ".jar")
    local.write_bytes(data)
    # Inventory is not import acceptance. Some supplied Maven JARs mark empty
    # directory entries with an invalid UNIX file type. Read ordinary members
    # in memory and record those anomalies, without weakening core.archive.
    files, anomalies, total, seen = {}, [], 0, set()
    with ZipFile(local) as zipped:
        if len(zipped.infolist()) > 20000:
            raise ValueError("Too many JAR entries")
        for item in zipped.infolist():
            name = item.orig_filename
            if ("\\" in name or ":" in name or name.startswith("/") or
                    any(p in (".", "..", "") for p in name.rstrip("/").split("/"))):
                raise ValueError("Unsafe JAR metadata path")
            if item.is_dir():
                if item.file_size or stat.S_IFMT(item.external_attr >> 16) not in (0, stat.S_IFDIR):
                    anomalies.append({"path": name, "unix_mode": oct(item.external_attr >> 16), "bytes": item.file_size})
                continue
            if stat.S_IFMT(item.external_attr >> 16) not in (0, stat.S_IFREG):
                raise ValueError("Nonregular JAR member")
            total += item.file_size
            if total > 64 << 20 or name.casefold() in seen:
                raise ValueError("Oversized or ambiguous JAR metadata")
            seen.add(name.casefold())
            files[name] = zipped.read(item)
    manifest = _manifest(files.get("META-INF/MANIFEST.MF", b""))
    # Old Forge metadata sometimes contains literal newlines in descriptions.
    # Record this as legacy input, not proof of a working loader.
    records, error = [], None
    if "mcmod.info" in files:
        try:
            value = json.loads(files["mcmod.info"], strict=False)
            records = value if isinstance(value, list) else value.get("modList", [value])
        except (ValueError, AttributeError) as exc:
            error = str(exc)
    poms = []
    for name, text in files.items():
        if not name.endswith("/pom.xml"):
            continue
        try:
            tree = ET.fromstring(text)
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            def content(node, field):
                return node.findtext("m:" + field, namespaces=ns) or node.findtext(field)
            license_nodes = tree.findall("m:licenses/m:license", ns) or tree.findall("licenses/license")
            deps = tree.findall("m:dependencies/m:dependency", ns) or tree.findall("dependencies/dependency")
            poms.append({"path": name, "group": content(tree, "groupId"),
                "artifact": content(tree, "artifactId"), "version": content(tree, "version"),
                "license_claims": [{"name": content(n, "name"), "url": content(n, "url")} for n in license_nodes],
                "dependencies": [{k: content(n, k) for k in ("groupId", "artifactId", "version", "scope")} for n in deps]})
        except ET.ParseError as exc:
            poms.append({"path": name, "parse_error": str(exc)})
    prefixes = ("net/minecraft/", "net/minecraftforge/", "org/spongepowered/asm/",
                "org/objectweb/asm/", "io/netty/", "com/google/common/")
    api_examples = {prefix: [] for prefix in prefixes}
    majors, classes, entrypoint_evidence = Counter(), 0, []
    for name, code in files.items():
        if not name.endswith(".class"):
            continue
        classes += 1
        if code[:4] == b"\xca\xfe\xba\xbe" and len(code) >= 8:
            majors[int.from_bytes(code[6:8], "big")] += 1
        if b"net/minecraftforge/fml/common/Mod;" in code:
            entrypoint_evidence.append(name)
        for prefix in prefixes:
            if prefix.encode() in code and len(api_examples[prefix]) < 4:
                api_examples[prefix].append(name)
    notices = [{"path": name, "sha256": hashlib.sha256(text).hexdigest()}
        for name, text in files.items() if any(v in name.lower() for v in ("license", "licence", "copying", "notice"))]
    selected_headers = {k: manifest[k] for k in ("fmlcoreplugin", "fmlat", "tweakclass", "maven-artifact", "implementation-version", "fmlcoreplugincontainsfmlmod") if k in manifest}
    return {"path": path, "sha256": sha, "bytes": len(data), "class_count": classes,
        "class_major_versions": dict(majors), "metadata": records, "metadata_error": error,
        "directory_mode_anomalies": anomalies,
        "manifest_hooks": selected_headers, "annotation_candidates": entrypoint_evidence,
        "mixin_configs": [n for n in files if "mixin" in n.lower() and n.endswith(".json")],
        "access_changes": [n for n in files if n.lower().endswith(("_at.cfg", ".accesswidener"))],
        "api_reference_examples": {k: v for k, v in api_examples.items() if v},
        "maven": poms, "notice_files": notices,
        "asset_files": sum(n.startswith("assets/") for n in files),
        "data_files": sum(n.startswith("data/") for n in files),
        "classification": "BLOCKED", "effort": "Unestimated until exact source/licence/API review",
        "reason": "Java bytecode is not executable in Herspers; the legacy runtime/API and full redistribution rights are not verified.",
        "dependency_scope": "Metadata/POM claims and byte-reference samples only; not a complete transitive dependency proof"}


def inspect_funcraft(source: Path):
    if digest(source) != FUNCRAFT_SHA256:
        raise ValueError("This inspection targets the supplied FunCraft hotfix ZIP's exact SHA-256")
    files = archive(source, limit=512 << 20)
    manifest = json.loads(files["manifest.json"])
    if (manifest.get("name"), manifest.get("version")) != (FUNCRAFT_NAME, FUNCRAFT_VERSION):
        raise ValueError("Unexpected FunCraft identity")
    parser = ModList()
    parser.feed(files.get("modlist.html", b"").decode("utf-8-sig"))
    labels = {}
    for item in parser.links:
        identity = re.search(r"/mc-mods/(\d+)(?:/|$)", item["url"])
        if identity:
            labels.setdefault(int(identity[1]), []).append(item)
    rows = []
    for item in manifest["files"]:
        matches = labels.get(item["projectID"], [])
        label = matches[0] if len(matches) == 1 else {}
        rows.append({"name": label.get("name", f"CurseForge project {item['projectID']}"),
            "project_id": item["projectID"], "file_id": item["fileID"],
            "required": item.get("required"), "project_url": label.get("url"),
            "version": "Unknown: exact manifest JAR not supplied/identity-mapped",
            "dependencies": "Unknown: file IDs do not declare mod dependencies",
            "required_apis": "Legacy Minecraft 1.12.2 / Forge; exact hooks unknown without the matching JAR/source",
            "license": "Unverified for this exact file; no reuse/redistribution grant assumed",
            "classification": "BLOCKED", "effort": "Unestimated pending JAR, source and licence evidence",
            "evidence": "manifest.json project/file pair; modlist.html project-label association only"})
    with tempfile.TemporaryDirectory(prefix="herps-static-inspection-") as tmp:
        jars = [jar_inventory(data, name, Path(tmp)) for name, data in files.items() if name.lower().endswith(".jar")]
    inner = []
    for name, data in files.items():
        if not name.lower().endswith(".zip"):
            continue
        with tempfile.TemporaryDirectory(prefix="herps-static-nested-") as tmp:
            p = Path(tmp) / "input.zip"
            p.write_bytes(data)
            entries = archive(p)
        inner.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(),
            "files": len(entries), "extensions": dict(Counter(Path(n).suffix.lower() for n in entries)),
            "pack_metadata": json.loads(entries["pack.mcmeta"]) if "pack.mcmeta" in entries else None,
            "license_files": [n for n in entries if any(k in n.lower() for k in ("license", "licence", "copying"))],
            "note": "Format adaptation may be possible; rights and 1.12-to-26.3 semantics need verification. No assets copied."})
    return {"schema": 1, "archive_sha256": FUNCRAFT_SHA256, "archive_bytes": source.stat().st_size,
        "name": manifest["name"], "version": manifest["version"], "minecraft": manifest["minecraft"],
        "uncompressed_bytes": sum(map(len, files.values())), "regular_files": len(files),
        "extensions": dict(Counter(Path(n).suffix.lower() for n in files)),
        "manifest_entries": rows, "bundled_jars": jars, "nested_archives": inner,
        "file_inventory": [{"path": n, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for n, data in files.items()],
        "java_executed": False, "gameplay_verified": False,
        "classification_note": "Whole-mod current readiness. BLOCKED can hide feasible individual features; no whole Java mod is certified native.",
        "dependencies_note": "154 opaque manifest requirements plus 16 physical JARs; JAR-to-project identity and duplicate coverage are unproven. Do not sum as unique mods."}


def write_inventory(source: Path, output: Path):
    value = inspect_funcraft(source)
    output.mkdir(parents=True, exist_ok=True)
    (output / "funcraft-inventory.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    with (output / "dependency-licensing-inventory.csv").open("w", newline="") as stream:
        columns = ["scope", "name", "version", "identity", "dependencies", "required_apis", "license", "classification", "effort", "evidence"]
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in value["manifest_entries"]:
            writer.writerow({**{k: row[k] for k in columns if k in row}, "scope": "FunCraft manifest", "identity": f"CF {row['project_id']}/{row['file_id']}"})
        for row in value["bundled_jars"]:
            meta = row["metadata"][0] if row["metadata"] else {}
            writer.writerow({"scope": "FunCraft physical JAR", "name": meta.get("name") or Path(row["path"]).name,
                "version": meta.get("version") or "Filename/Maven coordinate only: " + Path(row["path"]).name,
                "identity": row["sha256"], "dependencies": json.dumps(row["maven"]) if row["maven"] else "Incomplete; metadata/class review required",
                "required_apis": ", ".join(row["api_reference_examples"]) or "JVM; exact native replacement requirements unverified",
                "license": json.dumps([p.get("license_claims", []) for p in row["maven"]]) + "; notices: " + json.dumps(row["notice_files"]) + "; complete scope unverified",
                "classification": row["classification"], "effort": row["effort"], "evidence": row["path"]})
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--funcraft", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = write_inventory(args.funcraft, args.output)
    print(f"Inspected {len(result['manifest_entries'])} manifest rows and {len(result['bundled_jars'])} physical JARs without executing them")
