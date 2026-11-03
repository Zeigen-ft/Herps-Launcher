"""Local modpack snapshots, complete coverage, and conservative data carry-over.

Conversion and compatibility analysis remain in the pinned Rust tool and Step 1
adapter. This module only supplies local files, preserves pack manifests, and
coordinates safe subsets. It never launches Java, a game, a fetch, or an oracle.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid

from ..core import Launcher, archive, atomic, digest, json_write, safe_name
from ..javamods.adapter import (AnalysisReport, PortPackAdapter, REQUIRES_PORTING,
                               UNSUPPORTED, _json, _plain)
from ..javamods.library import JavaModLibrary, _manifest, _tree
from ..javamods.models import Diagnostic, parse_coverage

TOKEN = re.compile(r"[0-9a-f]{32}\Z")
PLAY_REASON = "Play is unavailable: no real modpack runtime/content validation or gameplay test backend exists. Data carry-over alone does not prove playability."


def _read(path: Path):
    _plain(path)
    if not path.is_file() or path.stat().st_size > 64 << 20:
        raise ValueError(f"Missing or oversized modpack evidence: {path}")
    return _json(path.read_text(encoding="utf-8"))


def _snapshot_hashes(path: Path) -> dict[str, str]:
    _plain(path)
    if path.is_file():
        return {".": digest(path)}
    if not path.is_dir():
        raise ValueError("Imported modpack snapshot is missing")
    values, total = {}, 0
    for folder, directories, files in os.walk(path, followlinks=False):
        for name in directories + files:
            item = Path(folder) / name
            _plain(item)
            if len(item.relative_to(path).parts) > 32:
                raise ValueError("Modpack snapshot is too deep")
        for name in files:
            item = Path(folder) / name
            if not item.is_file():
                raise ValueError("Nonregular modpack snapshot file")
            total += item.stat().st_size
            if len(values) >= 4096 or total > 512 << 20:
                raise ValueError("Modpack snapshot exceeds bounded limits")
            values[item.relative_to(path).as_posix()] = digest(item)
    return values


@dataclass(frozen=True)
class ImportedPack:
    token: str
    name: str
    format: str
    source: Path
    report_file: Path | None = None
    dependencies: Path | None = None


@dataclass
class CoverageEntry:
    id: str
    name: str
    version: str
    status: str
    reason: str
    license: str
    tier: str
    missing_dependencies: list[str]
    source: str
    raw_evidence: dict = field(default_factory=dict)
    carried: bool = False
    output_path: str | None = None

    def to_dict(self):
        return asdict(self)


@dataclass
class PackReport:
    status: str
    summary: str
    rows: list[CoverageEntry]
    analysis: AnalysisReport | None
    report_file: Path
    diagnostics: list[Diagnostic] = field(default_factory=list)
    raw_evidence: dict = field(default_factory=dict)

    def to_dict(self):
        return {"schema": 1, "status": self.status, "summary": self.summary,
                "rows": [row.to_dict() for row in self.rows],
                "analysis": self.analysis.to_dict() if self.analysis else None,
                "report_file": str(self.report_file),
                "diagnostics": [asdict(d) for d in self.diagnostics],
                "raw_evidence": self.raw_evidence, "play_enabled": False,
                "playable_verified": False, "test_execution": None,
                "java_bridge_available": False, "play_disabled_reason": PLAY_REASON}


class LocalPackAdapter(PortPackAdapter):
    """Supply local archive/instance files without invoking network fetch.

    Rust import output is retained before normalization. Standard CurseForge
    manifest placeholders have no .jar extension; adding the extension only
    lets the existing Step 1 local-file path handle them. No mod conversion or
    compatibility decision is replaced here.
    """

    def __init__(self, launcher, executable=None, dependencies=None):
        super().__init__(launcher, executable=executable)
        self.local_folder = Path(dependencies).expanduser().absolute() if dependencies else None
        self.pack = None
        self.expected_hashes = {}
        self.cf_names = {}
        self.cf_hashes = {}
        self.expected_files = []

    def _cf_mapping(self, report):
        if self.local_folder is None:
            return {}
        choices = [self.local_folder / "minecraftinstance.json"]
        if self.local_folder.name == "mods":
            choices.append(self.local_folder.parent / "minecraftinstance.json")
            if self.local_folder.parent.name in (".minecraft", "minecraft"):
                choices.append(self.local_folder.parent.parent / "minecraftinstance.json")
        for path in choices:
            if not path.exists():
                continue
            value = _read(path)
            report.raw_evidence["curseforge_instance_metadata"] = {
                "path": str(path), "sha256": digest(path), "json": deepcopy(value)}
            if not isinstance(value, dict) or not isinstance(value.get("installedAddons"), list):
                raise ValueError("Invalid CurseForge instance installedAddons metadata")
            mapping = {}
            for addon in value["installedAddons"]:
                if not isinstance(addon, dict) or not isinstance(addon.get("installedFile"), dict):
                    raise ValueError("Invalid CurseForge installed-file mapping")
                item = addon["installedFile"]
                project, file_id, filename = addon.get("addonID"), item.get("id"), item.get("fileName")
                if type(project) is not int or type(file_id) is not int or not isinstance(filename, str):
                    raise ValueError("Incomplete CurseForge project/file mapping")
                safe_name(filename)
                if (project, file_id) in mapping:
                    raise ValueError("Ambiguous CurseForge installed-file mapping")
                mapping[(project, file_id)] = filename
                hashes = {}
                if item.get("sha1") is not None:
                    hashes["sha1"] = item["sha1"]
                declared = item.get("hashes", {})
                if isinstance(declared, dict):
                    hashes.update(declared)
                elif isinstance(declared, list):
                    for claim in declared:
                        if not isinstance(claim, dict) or claim.get("algo") not in (1, 2):
                            raise ValueError("Unsupported declared CurseForge hash algorithm")
                        hashes[{1: "sha1", 2: "md5"}[claim["algo"]]] = claim.get("value")
                else:
                    raise ValueError("Malformed declared CurseForge file hashes")
                self.cf_hashes[(project, file_id)] = hashes
            return mapping
        return {}

    def _run(self, report, *args):
        super()._run(report, *args)
        if str(args[0]) != "import":
            return
        source, work = Path(args[1]), Path(args[2])
        original = self._artifact(report, work / "pack.json", "rust_import_original")
        pack = deepcopy(original)
        if not isinstance(pack, dict) or not isinstance(pack.get("files"), list):
            raise ValueError("Rust importer did not produce a pack files array")
        files = archive(source, limit=512 << 20) if source.is_file() and source.suffix.lower() != ".json" else {}
        self.cf_names = self._cf_mapping(report) if "manifest.json" in files else {}
        if "modrinth.index.json" in files:
            index = _json(files["modrinth.index.json"].decode("utf-8-sig"))
            report.raw_evidence["original_modrinth_index"] = deepcopy(index)
            for item in index.get("files", []):
                if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("hashes", {}), dict):
                    raise ValueError("Malformed Modrinth indexed file/hash metadata")
                self.expected_hashes[item["path"]] = deepcopy(item.get("hashes", {}))
        if "manifest.json" in files:
            manifest = _json(files["manifest.json"].decode("utf-8-sig"))
            report.raw_evidence["original_curseforge_manifest"] = deepcopy(manifest)
            remaining, normalized = list(pack["files"]), []
            for index, item in enumerate(manifest.get("files", [])):
                if not isinstance(item, dict) or type(item.get("projectID")) is not int or type(item.get("fileID")) is not int:
                    raise ValueError("Invalid original CurseForge manifest file identity")
                ids = (item["projectID"], item["fileID"])
                filename = self.cf_names.get(ids)
                matching = [entry for entry in remaining if entry.get("curseforge") == list(ids)
                            or (filename and Path(entry.get("path", "")).name == filename)]
                if len(matching) > 1:
                    raise ValueError("Ambiguous original CurseForge manifest entries")
                if matching:
                    entry = remaining.pop(remaining.index(matching[0]))
                else:
                    entry = {"path": f"mods/curseforge-{ids[0]}-{ids[1]}.jar", "client": "", "server": ""}
                entry["curseforge"] = list(ids)
                if not entry["path"].endswith(".jar"):
                    entry["path"] += ".jar"
                entry["original_manifest_index"] = index
                normalized.append(entry)
            # Uncorrelated named mod-list entries remain visible alongside
            # unresolved manifest IDs; no claim is made that they are identical.
            pack["files"] = normalized + remaining
        # Embedded user-supplied mod JARs can be provided as local inputs. Rust
        # still decides the metadata/classification/carry; code is never run.
        for name, data in files.items():
            prefix = next((p for p in ("overrides/mods/", "client-overrides/mods/", "mods/") if name.startswith(p)), None)
            if not prefix or not name.lower().endswith(".jar"):
                continue
            relative = "mods/" + name[len(prefix):]
            if "/" in relative[5:]:
                report.diagnostics.append(Diagnostic("insufficient_evidence", f"Nested embedded mod path requires review: {name}"))
                continue
            filename = safe_name(Path(relative).name)
            target = report.workspace / "embedded" / (hashlib.sha256(data).hexdigest()[:16] + "-" + filename)
            atomic(target, data)
            matching = [entry for entry in pack["files"] if entry.get("path") == relative]
            if len(matching) > 1 or (matching and matching[0].get("jar")):
                report.diagnostics.append(Diagnostic("insufficient_evidence", f"Conflicting embedded mod entries: {relative}"))
                continue
            if matching:
                matching[0]["jar"] = str(target)
            else:
                pack["files"].append({"path": relative, "jar": str(target),
                                      "sha1": hashlib.sha1(data).hexdigest(), "client": "", "server": ""})
        self.expected_files = deepcopy(pack["files"])
        report.raw_evidence["original_expected_files"] = deepcopy(self.expected_files)
        report.raw_evidence["declared_file_hashes"] = deepcopy(self.expected_hashes)
        json_write(work / "pack.json", pack)

    def _artifact(self, report, path, label):
        value = super()._artifact(report, path, label)
        if label == "pack":
            self.pack = value
        return value

    @staticmethod
    def _hashes_match(path, hashes):
        for algorithm, expected in hashes.items():
            if algorithm not in ("sha1", "sha256", "sha512", "md5") or not isinstance(expected, str):
                raise ValueError(f"Unsupported or malformed declared hash: {algorithm}")
            value = hashlib.new(algorithm, path.read_bytes()).hexdigest()
            if not re.fullmatch(r"[a-fA-F0-9]{" + str(len(value)) + r"}", expected) or value != expected.lower():
                return False
        return True

    def _dependencies(self, folder, report):
        available = super()._dependencies(folder, report)
        resolutions, rejected, opaque_names = [], set(), set()
        for entry in (self.pack or {}).get("files", []):
            relative = entry.get("path", "")
            if not relative.startswith("mods/") or not relative.endswith(".jar"):
                continue
            hashes = deepcopy(self.expected_hashes.get(relative, {}))
            for algorithm, value in self.cf_hashes.get(tuple(entry.get("curseforge", [])), {}).items():
                if algorithm in hashes and hashes[algorithm] != value:
                    raise ValueError("Contradictory pack and instance declared hashes")
                hashes[algorithm] = value
            if entry.get("sha1"):
                hashes.setdefault("sha1", entry["sha1"])
            selected = Path(entry["jar"]) if entry.get("jar") else None
            filename = self.cf_names.get(tuple(entry.get("curseforge", [])), Path(relative).name)
            if entry.get("curseforge") and selected is None and not hashes and tuple(entry["curseforge"]) not in self.cf_names:
                # Rust's opaque placeholder is not the publisher's filename.
                # Renaming an arbitrary JAR cannot prove a project/file-ID match.
                opaque_names.add(Path(relative).name)
                resolutions.append({"path": relative, "state": "missing-identity-mapping",
                    "note": "Supply matching CurseForge instance metadata or a declared hash; placeholder filenames cannot establish project/file identity"})
                continue
            if selected is None:
                candidates = []
                for meta in available.values():
                    path = Path(meta.raw["source_path"])
                    if hashes and self._hashes_match(path, hashes):
                        candidates.append(path)
                if not candidates:
                    candidates = [Path(meta.raw["source_path"]) for meta in available.values()
                                  if meta.raw.get("original_filename") == filename]
                if len(candidates) > 1:
                    report.diagnostics.append(Diagnostic("insufficient_evidence", f"Ambiguous local files for {relative}"))
                    continue
                selected = candidates[0] if candidates else None
            if selected is None:
                continue
            _plain(selected)
            if not selected.is_absolute() or not selected.is_relative_to(report.workspace):
                raise ValueError("Resolved local file escaped its run snapshot")
            if not self._hashes_match(selected, hashes):
                report.diagnostics.append(Diagnostic("hash_mismatch", f"Declared file hash mismatch: {relative}"))
                rejected.add(digest(selected))
                entry.pop("jar", None)
                resolutions.append({"path": relative, "state": "hash-mismatch", "declared_hashes": hashes})
                continue
            entry["jar"] = str(selected)
            resolutions.append({"path": relative, "state": "local", "sha256": digest(selected),
                                "declared_hashes": hashes,
                                "declared_hash_verified": bool(hashes), "publisher_authenticated": False,
                                "note": "Known declared hashes matched" if hashes else "User instance mapping/filename only; no publisher hash is available"})
        # Prevent the base adapter's SHA-1/filename fallback from accepting a
        # file rejected by an additional declared hash such as Modrinth SHA-512.
        available = {key: value for key, value in available.items()
                     if value.sha256 not in rejected and value.raw.get("original_filename") not in opaque_names}
        report.raw_evidence["local_file_resolution"] = resolutions
        return available


def _coverage(data: dict, expected: list[dict]) -> list[CoverageEntry]:
    rows, seen = [], set()
    for mod in data.get("mods", []):
        raw = mod.get("raw_evidence", {})
        inventory = raw.get("inventory", {})
        metadata = mod.get("metadata") or {}
        path = inventory.get("path", "")
        seen.add(path)
        diagnostics = mod.get("diagnostics", [])
        missing = set(inventory.get("missing", []))
        for diagnostic in diagnostics:
            if diagnostic.get("code") == "missing_dependency":
                missing.update(re.findall(r"(?:Required dependency|requires unresolved dependency|Inventory reports unresolved dependency)\s+([A-Za-z0-9_.:-]+)", diagnostic.get("message", ""), re.I))
        status = mod.get("status") if mod.get("status") in (UNSUPPORTED, REQUIRES_PORTING) else UNSUPPORTED
        reason = "; ".join(d.get("message", "") for d in diagnostics) or "Static data-tier candidate; gameplay has not been tested"
        if mod.get("port_path") and status == REQUIRES_PORTING:
            reason = "Data carried; folder, manifest and hash validation passed. Gameplay remains unverified. " + reason
        source = inventory.get("source", "local file")
        matching = next((item for item in expected if item.get("path") == path), {})
        name = metadata.get("name") or inventory.get("name") or mod.get("id", "Unknown mod")
        if not metadata and matching.get("curseforge"):
            ids = matching["curseforge"]
            name = f"CurseForge project {ids[0]} / file {ids[1]}"
        rows.append(CoverageEntry(mod.get("id", path), name,
            metadata.get("version") or inventory.get("version") or "Unknown", status, reason,
            metadata.get("license") or inventory.get("license") or "Unknown",
            inventory.get("tier") or raw.get("coverage", {}).get("tier") or "none",
            sorted(missing), source, deepcopy(raw),
            bool(mod.get("port_path") and status == REQUIRES_PORTING),
            mod.get("port_path") if status == REQUIRES_PORTING else None))
    for index, item in enumerate(expected):
        path = item.get("path", "")
        if path in seen:
            continue
        ids = item.get("curseforge")
        name = f"CurseForge project {ids[0]} / file {ids[1]}" if ids else item.get("name") or path or "Unknown manifest entry"
        rows.append(CoverageEntry(f"unresolved-{index}-{path}", name, item.get("version") or "Unknown",
            UNSUPPORTED, "insufficient_evidence: Original manifest entry has no complete validated local analysis; resolve the user-provided file", "Unknown", "none", [],
            "CurseForge" if ids else "pack manifest", {"manifest": deepcopy(item)}))
    return rows


def _summary(rows, operation, status):
    carried = sum(row.carried for row in rows)
    if carried:
        if carried < len(rows) or status == UNSUPPORTED:
            return f"Partial data carry-over: {carried}/{len(rows)} rows validated locally. Not fully playable; unresolved/unsupported content remains. Gameplay unverified."
        return f"Data carried: {carried} local folder ports validated. Gameplay and complete modpack playability remain unverified."
    return "Not proven playable. " + ("No safely validated data ports were produced; inspect every row." if operation == "port" else "Static pack analysis only; resolve all missing and unsupported evidence before considering a data port.")


class ModpackLibrary:
    def __init__(self, launcher: Launcher, executable: Path | None = None):
        self.launcher = launcher
        self.executable = executable
        self.guard = JavaModLibrary(launcher)

    @property
    def root(self):
        return self.launcher.game.absolute() / "modpacks"

    def _directories(self):
        for path in (self.root, self.root / "imports"):
            self.guard._safe(path)
            path.mkdir(parents=True, exist_ok=True)

    def _receipt(self, token):
        if not isinstance(token, str) or not TOKEN.fullmatch(token):
            raise ValueError("Invalid imported pack token")
        path = self.root / "imports" / token / "import.json"
        self.guard._safe(path)
        value = _read(path)
        if not isinstance(value, dict) or value.get("schema") != 1 or value.get("token") != token:
            raise ValueError("Invalid imported pack receipt")
        return path, value

    def _entry(self, token, verify=True):
        _, value = self._receipt(token)
        source = Path(value["source"])
        self.guard._safe(source)
        if not source.is_relative_to(self.launcher.game.absolute()):
            raise ValueError("Imported pack snapshot belongs to another profile")
        if verify and _snapshot_hashes(source) != value.get("source_hashes"):
            raise ValueError("Imported pack snapshot changed; preserve it and import a fresh copy")
        report = Path(value["report_file"]) if value.get("report_file") else None
        if report:
            self.guard._safe(report)
            if not report.is_relative_to(self.launcher.game.absolute()):
                raise ValueError("Saved pack report belongs to another profile")
        return ImportedPack(token, value["name"], value["format"], source, report,
                            Path(value["dependencies"]) if value.get("dependencies") else None)

    def imports(self):
        self._directories()
        return [self._entry(path.name) for path in sorted((self.root / "imports").iterdir())]

    def import_pack(self, source: Path):
        self._directories()
        source = Path(source).expanduser().absolute()
        _plain(source)
        unsupported = source.name == "pack.toml" or (source.is_dir() and (source / "pack.toml").is_file())
        adapter = LocalPackAdapter(self.launcher, self.executable)
        report = adapter._new("import-pack")
        if unsupported:
            manifest = source / "pack.toml" if source.is_dir() else source
            snapshot = adapter._copy(manifest, report.workspace / "input/pack.toml")
            name, kind = source.stem, "packwiz"
            report.diagnostics.append(Diagnostic("unsupported_feature", "packwiz is not supported by the pinned horizon-port-pack importer; no parser was invented"))
            expected = [{"path": "pack.toml", "name": name}]
        else:
            snapshot = adapter._snapshot_pack(source, report)
            name, kind, expected = source.stem, "unknown", []
            try:
                work = report.workspace / "pack"
                adapter._run(report, "import", snapshot, work)
                pack = adapter._artifact(report, work / "pack.json", "pack")
                name, kind = pack.get("name") or name, pack.get("format") or kind
                expected = deepcopy(pack.get("files", []))
            except (OSError, ValueError) as error:
                report.diagnostics.append(Diagnostic("insufficient_evidence", f"Backend import failed: {error}"))
                expected = adapter.expected_files
        adapter._finish(report)
        token = uuid.uuid4().hex
        directory = self.root / "imports" / token
        directory.mkdir(mode=0o700)
        json_write(directory / "import.json", {"schema": 1, "token": token, "name": name,
            "format": kind, "source": str(snapshot), "source_hashes": _snapshot_hashes(snapshot),
            "report_file": None, "dependencies": None, "expected_files": expected,
            "import_evidence": report.to_dict()})
        return self._entry(token)

    def _prune(self, analysis, produced=False):
        chosen = {mod.id: mod for mod in analysis.mods if mod.status == REQUIRES_PORTING and (mod.port_path or not produced)}
        while True:
            removed = []
            for identity, mod in chosen.items():
                required = set(mod.metadata.required_dependencies if mod.metadata else []) - {"minecraft"}
                missing = required - chosen.keys()
                if missing:
                    mod.status, mod.port_path = UNSUPPORTED, None
                    mod.diagnostics += [Diagnostic("missing_dependency", f"Required dependency {dependency} was not validated for carry") for dependency in sorted(missing)]
                    mod.diagnostics.append(Diagnostic("insufficient_evidence", "External file metadata does not establish a successfully carried dependency ensemble"))
                    removed.append(identity)
            if not removed:
                return chosen
            for identity in removed:
                chosen.pop(identity)

    def _execute(self, token, dependencies, acknowledge_restricted, port):
        entry = self._entry(token)
        _, receipt = self._receipt(token)
        folder = Path(dependencies).expanduser().absolute() if dependencies is not None else entry.dependencies
        adapter = LocalPackAdapter(self.launcher, self.executable, folder)
        if entry.format == "packwiz":
            analysis = adapter._new("port" if port else "analyze-pack")
            analysis.diagnostics += [Diagnostic("unsupported_feature", "packwiz is unsupported by the pinned Rust importer"),
                                     Diagnostic("insufficient_evidence", "No packwiz mod inventory or conversion backend exists")]
            adapter._finish(analysis)
            expected = receipt["expected_files"]
        else:
            analysis = adapter.analyze_pack(entry.source, dependencies=folder, acknowledge_restricted=acknowledge_restricted)
            expected = deepcopy(adapter.expected_files or receipt["expected_files"])
        if port:
            analysis.operation = "port"
            chosen = self._prune(analysis)
            if chosen:
                try:
                    work = analysis.workspace / "pack"
                    adapter._run(analysis, "carry", work, *chosen.keys())
                    for mod in chosen.values():
                        adapter._verify_carry(analysis, mod, work / "mods" / mod.id)
                        if mod.port_path:
                            _manifest(Path(mod.port_path))
                            tree = _tree(Path(mod.port_path))
                            mod.raw_evidence["validated_tree"] = tree
                    successful = self._prune(analysis, produced=True)
                    analysis.raw_evidence["validated_data_ports"] = {key: {"path": mod.port_path, "tree": mod.raw_evidence["validated_tree"]} for key, mod in successful.items()}
                    analysis.raw_evidence["analysis_coverage"] = deepcopy(analysis.raw_evidence.get("coverage"))
                    adapter._run(analysis, "report", work)
                    rows = parse_coverage(adapter._artifact(analysis, work / "coverage.json", "coverage"))
                    by_key = {row.key: row.raw for row in rows}
                    for mod in analysis.mods:
                        if mod.id not in by_key:
                            raise ValueError("Post-carry coverage omitted an original mod")
                        mod.raw_evidence["coverage"] = by_key[mod.id]
                except (OSError, ValueError) as error:
                    for mod in analysis.mods:
                        mod.port_path = None
                        mod.status = UNSUPPORTED
                        mod.diagnostics.append(Diagnostic("insufficient_evidence", f"Data carry validation did not complete: {error}"))
                    analysis.diagnostics.append(Diagnostic("insufficient_evidence", f"Data carry validation did not complete: {error}"))
            adapter._finish(analysis)
        coverage = _coverage(analysis.to_dict(), expected)
        if not coverage:
            coverage = [CoverageEntry("unknown-pack", entry.name, "Unknown", UNSUPPORTED,
                "insufficient_evidence: No complete pack inventory was produced; inspect the backend errors", "Unknown", "none", [], entry.format)]
        result = PackReport(analysis.status, _summary(coverage, analysis.operation, analysis.status), coverage, analysis,
            analysis.workspace / "modpack-report.json", list(analysis.diagnostics),
            {"expected_files": expected, "import_evidence": receipt["import_evidence"], "format": entry.format,
             "source_hashes": receipt["source_hashes"]})
        json_write(result.report_file, result.to_dict())
        path, receipt = self._receipt(token)
        receipt.update(report_file=str(result.report_file), report_sha256=digest(result.report_file),
                       adapter_report_sha256=digest(analysis.workspace / "report.json"),
                       dependencies=str(folder) if folder else None)
        json_write(path, receipt)
        return result

    def analyze(self, token, dependencies=None, acknowledge_restricted=False):
        return self._execute(token, dependencies, acknowledge_restricted, False)

    def port(self, token, dependencies=None, acknowledge_restricted=False):
        return self._execute(token, dependencies, acknowledge_restricted, True)

    def load_report(self, token):
        entry = self._entry(token)
        if entry.report_file is None:
            return None
        _, receipt = self._receipt(token)
        value = _read(entry.report_file)
        if digest(entry.report_file) != receipt.get("report_sha256"):
            raise ValueError("Saved modpack report changed; rerun analysis rather than trust edited compatibility claims")
        original = value.get("analysis")
        if not isinstance(original, dict):
            raise ValueError("Saved report lacks original adapter evidence")
        raw_path = Path(original.get("workspace", "")) / "report.json"
        self.guard._safe(raw_path)
        if not raw_path.is_relative_to(self.launcher.game.absolute() / "java-mods/runs"):
            raise ValueError("Saved adapter evidence escaped this profile")
        if digest(raw_path) != receipt.get("adapter_report_sha256"):
            raise ValueError("Original adapter report changed; rerun analysis instead of trusting edited evidence")
        with tempfile.TemporaryDirectory(prefix="pack-export-", dir=entry.report_file.parent) as directory:
            validated = Path(directory) / "validated.json"
            PortPackAdapter(self.launcher).export_report(raw_path, validated)
            data = _read(validated)
        for mod in data.get("mods", []):
            output = mod.get("port_path")
            if not output:
                continue
            expected_tree = original.get("raw_evidence", {}).get("validated_data_ports", {}).get(mod["id"], {}).get("tree")
            try:
                path = Path(output)
                self.guard._safe(path)
                if not path.is_relative_to(raw_path.parent) or expected_tree is None or _tree(path) != expected_tree:
                    raise ValueError("Generated data port changed or lacks a validation receipt")
                _manifest(path)
            except (OSError, ValueError) as error:
                mod["status"], mod["port_path"] = UNSUPPORTED, None
                mod.setdefault("diagnostics", []).append({"code": "insufficient_evidence", "message": str(error)})
                data["status"] = UNSUPPORTED
        value["analysis"] = data
        value["rows"] = [row.to_dict() for row in _coverage(data, value["raw_evidence"]["expected_files"])]
        if not value["rows"]:
            value["rows"] = [CoverageEntry("unknown-pack", entry.name, "Unknown", UNSUPPORTED,
                "insufficient_evidence: No validated pack inventory", "Unknown", "none", [], entry.format).to_dict()]
        value["status"] = data["status"] if data["status"] in (UNSUPPORTED, REQUIRES_PORTING) else UNSUPPORTED
        value["summary"] = _summary([CoverageEntry(**row) for row in value["rows"]], data.get("operation"), value["status"])
        value.update(play_enabled=False, playable_verified=False, test_execution=None,
                     java_bridge_available=False, play_disabled_reason=PLAY_REASON)
        return value

    def export_report(self, token, output, format="json"):
        value = self.load_report(token)
        if value is None:
            raise ValueError("Analyze the selected pack before exporting a report")
        output = Path(output).expanduser().absolute()
        if format == "json":
            json_write(output, value)
        elif format == "text":
            lines = [f"Modpack status: {value['status']}", value["summary"], PLAY_REASON, ""]
            for row in value["rows"]:
                lines += [f"{row['name']} {row['version']}: {row['status']} · {row['tier']} · {row['license']}",
                          row["reason"], "Missing dependencies: " + ", ".join(row["missing_dependencies"]), ""]
            lines.append("Original evidence:\n" + json.dumps(value, indent=2))
            atomic(output, ("\n".join(lines) + "\n").encode("utf-8"))
        else:
            raise ValueError("Export format must be json or text")
        return output
