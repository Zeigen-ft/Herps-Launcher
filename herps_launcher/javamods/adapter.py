"""Subprocess adapter for the audited port-pack file protocol, not a Java bridge."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import uuid
import zipfile

from ..core import GAME, REVISION, Launcher, archive, digest, json_write, safe_name
from .metadata import JarMetadata, assess_dependencies, inspect_jar
from .models import CheckResult, Diagnostic, SchemaError, parse_coverage, parse_inventory

UNSUPPORTED = "Unsupported"
REQUIRES_PORTING = "Requires porting"
MAX_BYTES = 512 << 20
MAX_FILES = 4096
KEY = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}\Z")


def bundled_port_pack_candidates() -> tuple[Path, ...]:
    """Locate trusted package resources without searching the user's PATH.

    PyInstaller's resource directory is authoritative. Executable-relative
    fallbacks cover onedir Windows packages and the macOS application layout;
    none of these directories is used for mutable profile work.
    """
    if not getattr(sys, "frozen", False):
        return ()
    name = "horizon-port-pack.exe" if platform.system() == "Windows" else "horizon-port-pack"
    executable_dir = Path(sys.executable).absolute().parent
    directories = []
    if getattr(sys, "_MEIPASS", None):
        directories.append(Path(sys._MEIPASS))
    directories += [executable_dir, executable_dir / "_internal"]
    if platform.system() == "Darwin" and executable_dir.name == "MacOS" and executable_dir.parent.name == "Contents":
        directories += [executable_dir.parent / "Frameworks", executable_dir.parent / "Resources"]
    return tuple(dict.fromkeys(directory / name for directory in directories))


def _plain(path: Path) -> None:
    if path.is_symlink() or path.is_junction():
        raise ValueError(f"Links are not supported for imported files/work folders: {path}")


def _unique(items: list[Diagnostic]) -> list[Diagnostic]:
    return list(dict.fromkeys(items))


def _json(text: str):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SchemaError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result

    def finite(value):
        raise SchemaError(f"Non-finite JSON value: {value}")
    return json.loads(text, object_pairs_hook=unique_pairs, parse_constant=finite)


def _carry_gaps(raw) -> list[Diagnostic]:
    if not isinstance(raw, dict) or type(raw.get("copied")) is not int or raw["copied"] < 0:
        raise SchemaError("Invalid carry report count")
    gaps = []
    fields = {"outside": list, "unreadable": dict, "blocks_unknown": dict,
              "items_unknown": dict, "differences": dict, "recipes_unregistered": list, "recipes_kept": list}
    for name, kind in fields.items():
        if not isinstance(raw.get(name), kind):
            raise SchemaError(f"Missing or invalid carry report {name}")
        if raw[name]:
            gaps.append(Diagnostic("unsupported_feature", f"Data carry has {name}: {raw[name]}"))
    worldgen = raw.get("worldgen_types")
    if not isinstance(worldgen, dict):
        raise SchemaError("Missing carry worldgen evidence")
    for name in ("unsupported", "rules_lost", "processors_dropped", "modifiers_left"):
        if not isinstance(worldgen.get(name), dict):
            raise SchemaError(f"Missing carry worldgen {name}")
        if worldgen[name]:
            gaps.append(Diagnostic("unsupported_feature", f"Worldgen carry has {name}: {worldgen[name]}"))
    return gaps


@dataclass
class CommandEvidence:
    argv: tuple[str, ...]
    cwd: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass
class ModAnalysis:
    id: str
    status: str = UNSUPPORTED
    diagnostics: list[Diagnostic] = field(default_factory=list)
    metadata: JarMetadata | None = None
    check: CheckResult | None = None
    raw_evidence: dict = field(default_factory=dict)
    port_path: str | None = None

    @property
    def mod_id(self) -> str:
        return self.id

    def to_dict(self) -> dict:
        return {"id": self.id, "status": self.status,
                "diagnostics": [asdict(d) for d in self.diagnostics],
                "metadata": asdict(self.metadata) if self.metadata else None,
                "raw_evidence": self.raw_evidence, "port_path": self.port_path,
                "test_execution": None}


@dataclass
class AnalysisReport:
    operation: str
    profile: str
    workspace: Path
    status: str = UNSUPPORTED
    diagnostics: list[Diagnostic] = field(default_factory=list)
    mods: list[ModAnalysis] = field(default_factory=list)
    commands: list[CommandEvidence] = field(default_factory=list)
    raw_evidence: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"schema": 1, "operation": self.operation, "profile": self.profile,
                "workspace": str(self.workspace), "created_at": self.created_at,
                "status": self.status, "diagnostics": [asdict(d) for d in self.diagnostics],
                "mods": [m.to_dict() for m in self.mods],
                "commands": [asdict(c) for c in self.commands], "raw_evidence": self.raw_evidence,
                "test_execution": None, "java_bridge_available": False,
                "playable_verified": False}


class PortPackAdapter:
    def __init__(self, launcher: Launcher, executable: Path | None = None, timeout: float = 120):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout must be finite and positive")
        self.launcher = launcher
        self.executable = executable
        self.timeout = timeout

    def _new(self, operation: str) -> AnalysisReport:
        game = self.launcher.game.absolute()
        # Resolve the caller's support layout, but never follow a link inside the
        # profile-owned area to place an import in another profile or application.
        boundary = self.launcher.support.absolute()
        for ancestor in (game, *game.parents):
            _plain(ancestor)
            if ancestor == boundary:
                break
        for path in (game, game / "java-mods", game / "java-mods/runs"):
            _plain(path)
            path.mkdir(parents=True, exist_ok=True)
        work = game / "java-mods/runs" / uuid.uuid4().hex
        work.mkdir(mode=0o700)
        return AnalysisReport(operation, self.launcher.config["profile"], work)

    def _binary(self, report: AnalysisReport) -> Path:
        name = "horizon-port-pack.exe" if platform.system() == "Windows" else "horizon-port-pack"
        explicit = self.executable or self.launcher.config.get("port_pack_binary") or os.environ.get("HERPS_PORT_PACK")
        candidates = [Path(explicit)] if explicit else []
        if not explicit:
            if getattr(sys, "frozen", False):
                candidates += bundled_port_pack_candidates()
            else:
                if os.environ.get("CARGO_TARGET_DIR"):
                    candidates += [Path(os.environ["CARGO_TARGET_DIR"]) / mode / name for mode in ("release", "debug")]
                found = shutil.which(name)
                if found:
                    candidates.append(Path(found))
        for path in candidates:
            path = path.expanduser().absolute()
            if path.is_file() and os.access(path, os.X_OK):
                report.raw_evidence["backend"] = {"path": str(path), "sha256": digest(path),
                    "audited_engine_revision": REVISION,
                    "note": "Binary hash recorded; port-pack has no version protocol. Use a trusted build of the pinned engine."}
                return path
        if explicit:
            raise ValueError(f"Selected horizon-port-pack executable is missing or not executable: {explicit}; "
                             "select a trusted pinned build or clear port_pack_binary/HERPS_PORT_PACK to use automatic discovery")
        if getattr(sys, "frozen", False):
            raise ValueError("Bundled horizon-port-pack executable is missing or not executable; reinstall the launcher "
                             "or select a trusted pinned build. Cargo/Rust is not required for packaged metadata analysis")
        raise ValueError("horizon-port-pack executable is missing or not executable; select a trusted pinned build "
                         "with --port-pack, port_pack_binary, HERPS_PORT_PACK, CARGO_TARGET_DIR, or PATH")

    def _run(self, report: AnalysisReport, *args: str | Path) -> None:
        binary = self._binary(report)
        argv = (str(binary), *map(str, args))
        try:
            result = subprocess.run(argv, cwd=report.workspace, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=self.timeout,
                shell=False)
            evidence = CommandEvidence(argv, str(report.workspace), result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired as error:
            decode = lambda value: value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
            evidence = CommandEvidence(argv, str(report.workspace), None, decode(error.stdout), decode(error.stderr), True)
        except OSError as error:
            evidence = CommandEvidence(argv, str(report.workspace), None, "", str(error))
        report.commands.append(evidence)
        json_write(report.workspace / "commands.json", [asdict(c) for c in report.commands])
        if evidence.exit_code != 0:
            raise ValueError(f"port-pack {args[0]} failed (exit {evidence.exit_code}, timeout={evidence.timed_out}): {evidence.stderr.strip()}")

    def _artifact(self, report: AnalysisReport, path: Path, label: str):
        _plain(path)
        if not path.is_file() or path.stat().st_size > 16 << 20:
            raise SchemaError(f"Missing or oversized {label} artifact")
        text = path.read_text(encoding="utf-8")
        report.raw_evidence[label] = {"path": str(path), "sha256": digest(path), "text": text}
        value = _json(text)
        report.raw_evidence[label]["json"] = deepcopy(value)
        return value

    def _copy(self, source: Path, destination: Path) -> Path:
        _plain(source)
        if not source.is_file() or source.stat().st_size > MAX_BYTES:
            raise ValueError(f"Not a regular bounded input file: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        return destination

    def _snapshot_pack(self, source: Path, report: AnalysisReport) -> Path:
        source = source.expanduser().absolute()
        _plain(source)
        destination = report.workspace / "input" / safe_name(source.name)
        if source.is_file():
            self._copy(source, destination)
            if source.suffix.lower() != ".json":
                try:
                    files = archive(destination, limit=MAX_BYTES)
                except (zipfile.BadZipFile, RuntimeError) as error:
                    raise ValueError(f"Cannot inspect pack archive: {error}") from error
                report.raw_evidence["source_archive_entries"] = list(files)
            return destination
        if not source.is_dir():
            raise ValueError(f"Pack source does not exist: {source}")
        destination.mkdir(parents=True)
        total, count = 0, 0
        # Snapshot the instance, excluding unrelated saves/logs/game assets.
        game = next((source / g for g in (".minecraft", "minecraft", ".")
                     if (source / g / "mods").is_dir() or (source / g / "resourcepacks").is_dir()), source)
        _plain(game)
        selected = [source / "mmc-pack.json", source / "instance.cfg"]
        selected += [game / n for n in ("mods", "config", "kubejs", "defaultconfigs", "datapacks", "resourcepacks", "shaderpacks")]
        if game == source and not (game / "mods").exists():
            selected += sorted(source.glob("*.jar"))

        def copy(item: Path):
            nonlocal total, count
            _plain(item)
            if not item.exists():
                return
            relative = item.relative_to(source)
            safe_name(item.name)
            if len(relative.parts) > 32:
                raise ValueError("Instance exceeds snapshot depth limit")
            if item.is_dir():
                for child in sorted(item.iterdir()):
                    copy(child)
            elif item.is_file():
                count += 1
                total += item.stat().st_size
                if count > MAX_FILES or total > MAX_BYTES or len(relative.parts) > 32:
                    raise ValueError("Instance exceeds bounded snapshot limits")
                self._copy(item, destination / relative)
            else:
                raise ValueError(f"Unsupported instance file: {item}")
        for item in selected:
            copy(item)
        if (game / "mods").is_dir():
            (destination / game.relative_to(source) / "mods").mkdir(parents=True, exist_ok=True)
        return destination

    def _dependencies(self, folder: Path | None, report: AnalysisReport) -> dict[str, JarMetadata]:
        if folder is None:
            return {}
        folder = folder.expanduser().absolute()
        _plain(folder)
        if not folder.is_dir():
            raise ValueError("Dependency source must be the user's mod/instance directory")
        folder = next((folder / p for p in ("mods", ".minecraft/mods", "minecraft/mods") if (folder / p).is_dir()), folder)
        _plain(folder)
        found: dict[str, JarMetadata] = {}
        total = 0
        for path in sorted(folder.rglob("*.jar")):
            if len(path.relative_to(folder).parts) > 4:
                continue
            for ancestor in (path, *path.parents):
                _plain(ancestor)
                if ancestor == folder:
                    break
            total += path.stat().st_size
            if len(found) >= MAX_FILES or total > MAX_BYTES:
                raise ValueError("Dependency folder exceeds bounded import limits")
            copied = self._copy(path, report.workspace / "dependencies" / f"{len(found)}-{safe_name(path.name)}")
            meta = inspect_jar(copied)
            meta.raw["source_path"] = str(copied)
            meta.raw["original_filename"] = path.name
            if meta.mod_id in found:
                raise ValueError(f"Ambiguous duplicate dependency ID: {meta.mod_id}")
            found[meta.mod_id] = meta
        report.raw_evidence["dependency_files"] = {key: {"version": m.version, "sha256": m.sha256,
            "metadata": m.raw, "diagnostics": [asdict(d) for d in m.diagnostics]} for key, m in found.items()}
        return found

    def _dependency_diagnostics(self, root: JarMetadata, available: dict[str, JarMetadata]) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        visited: set[str] = set()

        def visit(meta: JarMetadata, chain: tuple[str, ...]):
            if meta.mod_id in chain:
                diagnostics.append(Diagnostic("insufficient_evidence", f"Dependency cycle requires review: {' -> '.join((*chain, meta.mod_id))}"))
                return
            if meta.mod_id in visited:
                return
            visited.add(meta.mod_id)
            prefix = f"Dependency {meta.mod_id}: " if chain else ""
            diagnostics.extend(Diagnostic(d.code, prefix + d.message) for d in assess_dependencies(meta, available, minecraft=GAME))
            if chain:
                diagnostics.extend(Diagnostic(d.code, prefix + d.message) for d in meta.diagnostics)
                if meta.class_count:
                    diagnostics.append(Diagnostic("unsupported_feature", prefix + "Java code is required; a data-only port cannot satisfy it"))
            for dependency in meta.required_dependencies:
                if dependency in available and dependency != "minecraft":
                    visit(available[dependency], (*chain, meta.mod_id))
        visit(root, ())
        return diagnostics

    def _mod(self, jar: Path, key: str, available: dict[str, JarMetadata], report: AnalysisReport,
             acknowledge_restricted: bool, inventory=None) -> ModAnalysis:
        meta = inspect_jar(jar)
        mod = ModAnalysis(key, metadata=meta)
        mod.raw_evidence["metadata"] = meta.raw
        mod.raw_evidence["input_sha256"] = meta.sha256
        mod.raw_evidence["snapshot_path"] = str(jar)
        mod.diagnostics.extend(meta.diagnostics)
        mod.diagnostics.extend(self._dependency_diagnostics(meta, available))
        if not KEY.fullmatch(key) or not KEY.fullmatch(meta.mod_id):
            mod.diagnostics.append(Diagnostic("insufficient_evidence", "Unsafe or missing mod identity; backend invocation refused"))
            return mod
        if meta.mod_id != key:
            mod.diagnostics.append(Diagnostic("insufficient_evidence", f"Inventory identity {key!r} contradicts metadata {meta.mod_id!r}"))
        if inventory:
            mod.raw_evidence["inventory"] = inventory.raw
            for missing in inventory.missing:
                if missing not in available:
                    mod.diagnostics.append(Diagnostic("missing_dependency", f"Inventory reports unresolved dependency {missing}"))
            if inventory.info is None:
                mod.diagnostics.append(Diagnostic("insufficient_evidence", "Inventory did not parse this JAR"))
            elif (inventory.info.mod_id, inventory.info.version, inventory.info.census.classes) != (meta.mod_id, meta.version, meta.class_count):
                mod.diagnostics.append(Diagnostic("insufficient_evidence", "Inventory identity/version/class census contradicts the input metadata"))
            if inventory.class_ != "content" or inventory.tier != "data" or inventory.confidence in ("", "unknown", "guess"):
                mod.diagnostics.append(Diagnostic("insufficient_evidence", f"Inventory does not establish data-tier content: {inventory.class_}/{inventory.tier}/{inventory.confidence}"))
        if meta.class_count:
            mod.diagnostics.append(Diagnostic("unsupported_feature", "Java class code cannot run through a Java bridge; only data-tier carry-over is available"))
        license_text = meta.license.lower()
        restricted = any(part in license_text for part in ("-nd", "-nc", "no derivatives", "noncommercial", "non-commercial", "all rights reserved", "all-rights-reserved"))
        if restricted and not acknowledge_restricted:
            mod.diagnostics.append(Diagnostic("license_review_required", "Port-pack check also generates a local port. Review this restricted licence and pass --acknowledge-restricted-license before proceeding; no redistribution permission is implied."))
            mod.diagnostics.append(Diagnostic("insufficient_evidence", "Backend carry-over was withheld pending licence review"))
            return mod
        if not meta.license:
            mod.diagnostics.append(Diagnostic("insufficient_evidence", "Mod licence is unknown"))
        out = report.workspace / "checks" / key
        try:
            self._run(report, "check", jar, out)
            raw = self._artifact(report, out / "check.json", f"check:{key}")
            mod.raw_evidence["check"] = raw
            mod.check = CheckResult.parse(raw)
            check = mod.check
            if (check.mod_id, check.version, check.loader, check.license) != (meta.mod_id, meta.version, meta.loader, meta.license):
                mod.diagnostics.append(Diagnostic("insufficient_evidence", "Backend identity/version/loader contradicts the input metadata"))
            if check.code.classes != meta.class_count:
                mod.diagnostics.append(Diagnostic("unreadable_classes", f"Backend read {check.code.classes} of {meta.class_count} class files"))
            if check.code.features or check.code.events or check.code.examples or check.skipped:
                mod.diagnostics.append(Diagnostic("unsupported_feature", f"Backend reports unsupported features/events/skips: {check.code.features}, {check.code.events}, {check.skipped}"))
            for dep in check.depends:
                if dep not in available and dep not in (meta.mod_id, "minecraft"):
                    mod.diagnostics.append(Diagnostic("missing_dependency", f"Backend requires unresolved dependency {dep}"))
            if check.verdict == "no" or not check.ports:
                mod.diagnostics.append(Diagnostic("unsupported_feature", check.summary or "No supported data-tier content to port"))
            elif check.verdict == "partly":
                mod.diagnostics.append(Diagnostic("unsupported_feature", check.summary or "Backend reports partial carry-over"))
            if check.verdict == "works":
                carry_raw = self._artifact(report, out / "carry-report.json", f"check-carry:{key}")
                mod.raw_evidence["carry"] = carry_raw
                mod.diagnostics.extend(_carry_gaps(carry_raw))
            if not mod.diagnostics and check.verdict == "works":
                mod.status = REQUIRES_PORTING
            else:
                mod.diagnostics.append(Diagnostic("insufficient_evidence", "Static port-pack verdict does not establish full compatibility; unresolved or contradictory evidence remains"))
        except (OSError, ValueError, SchemaError) as error:
            mod.diagnostics += [Diagnostic("backend_error", str(error)), Diagnostic("insufficient_evidence", "No complete validated result from this backend invocation")]
        mod.diagnostics = _unique(mod.diagnostics)
        return mod

    def _finish(self, report: AnalysisReport) -> AnalysisReport:
        for mod in report.mods:
            if mod.status == UNSUPPORTED and not any(d.code == "insufficient_evidence" for d in mod.diagnostics):
                mod.diagnostics.append(Diagnostic("insufficient_evidence", "Compatibility could not be established from the recorded evidence"))
        if report.mods and all(m.status == REQUIRES_PORTING for m in report.mods) and not report.diagnostics:
            report.status = REQUIRES_PORTING
        else:
            report.status = UNSUPPORTED
            report.diagnostics.append(Diagnostic("insufficient_evidence", "This run has unresolved or unsupported evidence; inspect every mod and command result"))
        report.diagnostics = _unique(report.diagnostics)
        json_write(report.workspace / "report.json", report.to_dict())
        return report

    def _failed(self, report: AnalysisReport, error: Exception) -> AnalysisReport:
        report.diagnostics.append(Diagnostic("adapter_error", str(error)))
        for mod in report.mods:
            mod.status = UNSUPPORTED
            mod.port_path = None
            mod.diagnostics.append(Diagnostic("insufficient_evidence", f"Run validation did not complete: {error}"))
        return self._finish(report)

    def check(self, jar: Path, dependencies: Path | None = None, acknowledge_restricted: bool = False) -> AnalysisReport:
        report = self._new("check")
        try:
            copied = self._copy(Path(jar).expanduser().absolute(), report.workspace / "input" / safe_name(Path(jar).name))
            available = self._dependencies(dependencies, report)
            meta = inspect_jar(copied)
            if meta.mod_id in available and available[meta.mod_id].sha256 != meta.sha256:
                raise ValueError(f"Ambiguous duplicate input/dependency ID: {meta.mod_id}")
            available.setdefault(meta.mod_id, meta)
            report.mods.append(self._mod(copied, meta.mod_id, available, report, acknowledge_restricted))
        except (OSError, ValueError) as error:
            return self._failed(report, error)
        return self._finish(report)

    def analyze_pack(self, source: Path, dependencies: Path | None = None,
                     acknowledge_restricted: bool = False) -> AnalysisReport:
        return self._pack(source, dependencies, acknowledge_restricted, False)

    def _pack(self, source: Path, dependencies: Path | None, acknowledge_restricted: bool,
              port: bool) -> AnalysisReport:
        report = self._new("port" if port else "analyze-pack")
        try:
            snapshot = self._snapshot_pack(Path(source), report)
            work = report.workspace / "pack"
            self._run(report, "import", snapshot, work)
            pack = self._artifact(report, work / "pack.json", "pack")
            if not isinstance(pack, dict) or not isinstance(pack.get("files"), list):
                raise SchemaError("pack.json must contain a files array")
            available = self._dependencies(dependencies, report)
            # Materialize only user-supplied files, never fetch/port's network
            # pipeline. Hash-indexed files must match before Rust inventory runs.
            for entry in pack["files"]:
                if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                    raise SchemaError("Invalid indexed pack file")
                relative = entry["path"]
                if any(p in ("", ".", "..") for p in relative.split("/")) or "\\" in relative or ":" in relative or relative.startswith("/"):
                    raise ValueError("Unsafe indexed pack path")
                if not relative.startswith("mods/") or not relative.endswith(".jar"):
                    continue
                filename = safe_name(Path(relative).name)
                if entry.get("jar") is not None and not isinstance(entry["jar"], str):
                    raise SchemaError("Indexed JAR path must be a string")
                if entry.get("sha1") is not None and (not isinstance(entry["sha1"], str) or not re.fullmatch(r"[0-9a-fA-F]{40}", entry["sha1"])):
                    raise SchemaError("Indexed SHA-1 must be a hexadecimal digest")
                original = Path(entry["jar"]) if entry.get("jar") else None
                if original is None:
                    sha1 = entry.get("sha1")
                    matches = [m for m in available.values() if (sha1 and hashlib.sha1(Path(m.raw["source_path"]).read_bytes()).hexdigest() == sha1.lower())] if sha1 else []
                    # The metadata records the staged source; without a known
                    # hash a filename match is retained as unverified evidence.
                    if not matches:
                        matches = [m for m in available.values() if Path(m.raw.get("original_filename", "")).name == filename]
                    original = Path(matches[0].raw["source_path"]) if len(matches) == 1 else None
                if original:
                    if not original.is_relative_to(report.workspace):
                        raise ValueError("Backend referenced a JAR outside this import snapshot")
                    _plain(original)
                    expected = entry.get("sha1")
                    if expected and hashlib.sha1(original.read_bytes()).hexdigest() != expected.lower():
                        report.diagnostics.append(Diagnostic("hash_mismatch", f"SHA-1 mismatch for {relative}"))
                        entry.pop("jar", None)
                        continue
                    dest = self._copy(original, work / "jars" / filename)
                    entry["jar"] = str(dest)
                    if expected:
                        entry["sha1"] = expected.lower()
            json_write(work / "pack.json", pack)
            self._artifact(report, work / "pack.json", "resolved_pack")
            self._run(report, "inventory", work, "--offline")
            inventory = parse_inventory(self._artifact(report, work / "inventory.json", "inventory"))
            for record in inventory:
                if record.jar:
                    jar = Path(record.jar)
                    if not jar.is_relative_to(report.workspace):
                        raise ValueError("Inventory JAR escaped its snapshot")
                    meta = inspect_jar(jar)
                    if meta.mod_id in available and available[meta.mod_id].sha256 != meta.sha256:
                        report.diagnostics.append(Diagnostic("insufficient_evidence", f"Duplicate mod ID with differing bytes: {meta.mod_id}"))
                    available[meta.mod_id] = meta
            for record in inventory:
                if not record.path.startswith("mods/") or not record.jar:
                    report.mods.append(ModAnalysis(record.key, diagnostics=[Diagnostic("insufficient_evidence", f"No locally resolved Java JAR for {record.path}; downloads are disabled")], raw_evidence={"inventory": record.raw}))
                else:
                    report.mods.append(self._mod(Path(record.jar), record.key, available, report, acknowledge_restricted, record))
            if len(inventory) != len(pack["files"]) or not inventory:
                report.diagnostics.append(Diagnostic("insufficient_evidence", "Empty or incomplete pack inventory"))
            if pack.get("minecraft") and pack["minecraft"] != GAME:
                report.diagnostics.append(Diagnostic("version_mismatch", f"Pack targets Minecraft {pack['minecraft']}, launcher targets {GAME}"))
            if pack.get("overrides") or pack.get("curseforge_files", 0) > len(pack["files"]):
                report.diagnostics.append(Diagnostic("unsupported_feature", "Pack overrides or unresolved manifest entries require separate verification; the pack is not proven playable"))
            if port and report.mods and not report.diagnostics and all(m.status == REQUIRES_PORTING for m in report.mods):
                self._run(report, "carry", work, *(m.id for m in report.mods))
                for mod in report.mods:
                    self._verify_carry(report, mod, work / "mods" / mod.id)
            self._run(report, "report", work)
            rows = parse_coverage(self._artifact(report, work / "coverage.json", "coverage"))
            if {r.key for r in rows} != {r.key for r in inventory}:
                raise SchemaError("Coverage does not account for every inventory record")
            for mod in report.mods:
                row = next(r for r in rows if r.key == mod.id)
                mod.raw_evidence["coverage"] = row.raw
                record = next(r for r in inventory if r.key == mod.id)
                if (row.class_, row.tier, row.license) != (record.class_, record.tier, record.license) or row.status == "not-needed":
                    mod.status = UNSUPPORTED
                    mod.port_path = None
                    mod.diagnostics.append(Diagnostic("insufficient_evidence", "Coverage contradicts inventory or assumes a Java feature is replaced without validation"))
        except (OSError, ValueError) as error:
            return self._failed(report, error)
        return self._finish(report)

    def _verify_carry(self, report: AnalysisReport, mod: ModAnalysis, directory: Path) -> None:
        raw = self._artifact(report, directory / "carry-report.json", f"carry:{mod.id}")
        mod.raw_evidence["carry"] = raw
        gaps = _carry_gaps(raw)
        if gaps:
            mod.status = UNSUPPORTED
            mod.diagnostics.extend(gaps)
            mod.port_path = None
            return
        carry = directory / "carry"
        _plain(carry)
        if not isinstance(raw, dict) or not carry.is_dir() or not (carry / "horizon-mod.toml").is_file():
            raise SchemaError(f"No verified folder content mod was generated for {mod.id}")
        # Carry reports are retained, not interpreted as a build/test receipt.
        mod.port_path = str(carry)

    def port(self, source: Path, dependencies: Path | None = None,
             acknowledge_restricted: bool = False) -> AnalysisReport:
        if Path(source).is_file() and Path(source).suffix.lower() == ".jar":
            report = self.check(source, dependencies, acknowledge_restricted)
            report.operation = "port"
            try:
                for mod in report.mods:
                    if mod.status == REQUIRES_PORTING:
                        if any(dep != "minecraft" for dep in mod.metadata.required_dependencies):
                            mod.status = UNSUPPORTED
                            mod.diagnostics.append(Diagnostic("insufficient_evidence", "Standalone check carries this JAR in isolation. Use a local pack/instance port to carry its required dependency set together."))
                        else:
                            self._verify_carry(report, mod, report.workspace / "checks" / mod.id)
            except (OSError, ValueError) as error:
                return self._failed(report, error)
            return self._finish(report)
        return self._pack(source, dependencies, acknowledge_restricted, True)

    def export_report(self, report_file: Path, output: Path, format: str = "json") -> Path:
        """Export retained evidence; saved files cannot inject a test success claim."""
        report_file = Path(report_file).absolute()
        root = (self.launcher.game / "java-mods/runs").resolve()
        _plain(report_file)
        if not report_file.resolve().is_relative_to(root) or report_file.name != "report.json":
            raise ValueError("Select a report.json belonging to this profile")
        if report_file.stat().st_size > 64 << 20:
            raise ValueError("Report is oversized")
        data = _json(report_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != 1 or not isinstance(data.get("mods"), list):
            raise SchemaError("Invalid adapter report")
        for row in [data, *data["mods"]]:
            if not isinstance(row, dict) or not isinstance(row.get("diagnostics"), list):
                raise SchemaError("Invalid adapter report row/diagnostics")
            if any(not isinstance(d, dict) or not isinstance(d.get("code"), str) or not isinstance(d.get("message"), str) for d in row["diagnostics"]):
                raise SchemaError("Invalid adapter diagnostic")

        available: dict[str, JarMetadata] = {}
        current: dict[str, JarMetadata] = {}
        source_error = None

        def saved_source(path, expected) -> JarMetadata:
            if not isinstance(path, str) or not isinstance(expected, str):
                raise SchemaError("Missing snapshot path/hash")
            snapshot = Path(path)
            if not snapshot.is_absolute() or not snapshot.resolve().is_relative_to(report_file.parent.resolve()):
                raise SchemaError("Saved source escaped its run workspace")
            _plain(snapshot)
            meta = inspect_jar(snapshot)
            if not meta.sha256 or meta.sha256 != expected:
                raise SchemaError("Saved source hash changed or snapshot is missing")
            return meta

        try:
            if data.get("workspace") != str(report_file.parent):
                raise SchemaError("Saved workspace does not match this report")
            for row in data["mods"]:
                if row.get("status") == REQUIRES_PORTING:
                    evidence = row.get("raw_evidence", {})
                    meta = saved_source(evidence.get("snapshot_path"), evidence.get("input_sha256"))
                    current[row["id"]] = meta
                    available[meta.mod_id] = meta
            dependencies = data.get("raw_evidence", {}).get("dependency_files", {})
            if not isinstance(dependencies, dict):
                raise SchemaError("Invalid saved dependency evidence")
            for key, dependency in dependencies.items():
                meta = saved_source(dependency["metadata"]["source_path"], dependency["sha256"])
                if meta.mod_id != key or (key in available and available[key].sha256 != meta.sha256):
                    raise SchemaError("Ambiguous saved dependency identity")
                available[key] = meta
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
            source_error = str(error)

        for row in [data, *data["mods"]]:
            unsupported = row.get("status") not in (UNSUPPORTED, REQUIRES_PORTING) or row.get("test_execution") is not None
            if row is not data and row.get("status") == REQUIRES_PORTING:
                try:
                    check = CheckResult.parse(row.get("raw_evidence", {}).get("check"))
                    meta = row["metadata"]
                    if row.get("id") in current:
                        fresh = current[row["id"]]
                        for diagnostic in _unique([*fresh.diagnostics, *self._dependency_diagnostics(fresh, available)]):
                            value = asdict(diagnostic)
                            if value not in row["diagnostics"]:
                                row["diagnostics"].append(value)
                    unsupported |= (not isinstance(meta, dict) or bool(row["diagnostics"]) or bool(meta.get("diagnostics"))
                        or type(meta.get("class_count")) is not int or meta.get("class_count") != 0 or check.verdict != "works" or not check.ports
                        or bool(check.skipped) or check.code.classes != 0 or bool(check.code.features)
                        or bool(check.code.events) or bool(check.code.examples)
                        or (check.mod_id, check.version, check.loader) != (meta.get("mod_id"), meta.get("version"), meta.get("loader"))
                        or bool(_carry_gaps(row.get("raw_evidence", {}).get("carry")))
                        or source_error is not None or row["id"] not in current
                        or bool(current[row["id"]].diagnostics)
                        or bool(self._dependency_diagnostics(current[row["id"]], available)))
                except (ValueError, KeyError, TypeError, AttributeError):
                    unsupported = True
            if unsupported:
                row["status"] = UNSUPPORTED
                reason = source_error or "Compatibility/test claim is unsupported by the retained evidence; this adapter never runs mod tests"
                row.setdefault("diagnostics", []).append({"code": "insufficient_evidence", "message": f"Saved report could not be verified: {reason}"})
            row["test_execution"] = None
        if not data["mods"] or data["diagnostics"] or any(m.get("status") == UNSUPPORTED for m in data["mods"]):
            data["status"] = UNSUPPORTED
            if not any(d["code"] == "insufficient_evidence" for d in data["diagnostics"]):
                data["diagnostics"].append({"code": "insufficient_evidence", "message": "Saved report has missing, unsupported, or contradictory evidence"})
        data["java_bridge_available"] = False
        data["playable_verified"] = False
        output = Path(output).expanduser().absolute()
        if format == "json":
            json_write(output, data)
        elif format == "text":
            from ..core import atomic
            lines = [f"Herps Java mods: {data['status']}", "Static data-tier analysis only. No Java bridge or gameplay test."]
            for row in [data, *data["mods"]]:
                lines.append(f"{row.get('id', 'Run')}: {row['status']}")
                lines.extend(f"  {d['code']}: {d['message']}" for d in row.get("diagnostics", []))
            lines.append("\nRaw evidence (including backend JSON and command output):\n" + json.dumps(data, indent=2))
            atomic(output, ("\n".join(lines) + "\n").encode("utf-8"))
        else:
            raise ValueError("Report format must be json or text")
        return output
