"""Profile-owned imported JARs and verified data-only folder-mod installation.

The pinned engine discovers immediate ``horizon-mods/<folder>/horizon-mod.toml``
packages (horizon-mods/src/manifest.rs::find/Package::read). Content API 0.2
with capability ``registries`` needs no WASM. The existing mod.<id> setting
controls enabling; this module never builds or executes imported code.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tomllib
import uuid

from ..core import ID, Launcher, atomic, digest, json_write, pairs, safe_name, update_pairs
from .adapter import AnalysisReport, PortPackAdapter, REQUIRES_PORTING, _json
from .metadata import JarMetadata, inspect_jar


TOKEN = re.compile(r"[a-f0-9]{32}\Z")
MAX_FILES = 4096
MAX_BYTES = 512 << 20


@dataclass(frozen=True)
class ImportedJar:
    token: str
    mod_id: str
    name: str
    version: str
    loader: str
    path: Path
    sha256: str
    report_file: Path | None
    dependencies: Path | None
    metadata: JarMetadata


@dataclass(frozen=True)
class PortedMod:
    id: str
    name: str
    version: str
    path: Path
    enabled: bool
    report_file: Path


def _plain(path: Path) -> None:
    """Refuse a linked leaf; callers separately guard managed ancestors.

    Standard system ancestors such as macOS /var and /tmp may be links. They
    are outside the selected support root, not profile-owned escape paths.
    """
    if path.is_symlink() or path.is_junction():
        raise ValueError(f"Preserve linked paths; Java mod library requires ordinary files: {path}")


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _read(path: Path) -> dict:
    _plain(path)
    if not path.is_file() or path.stat().st_size > 64 << 20:
        raise ValueError(f"Missing or oversized library receipt: {path}")
    value = _json(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ValueError("Invalid Java mod library receipt")
    return value


def _tree(path: Path) -> dict[str, str]:
    """Fingerprint bounded data-only output without following filesystem links."""
    _plain(path)
    if not path.is_dir():
        raise ValueError("The generated folder port is missing")
    result, total, folded = {}, 0, set()
    for folder, directories, filenames in os.walk(path, followlinks=False):
        for name in sorted(directories + filenames):
            child = Path(folder) / name
            _plain(child)
            relative = child.relative_to(path).as_posix()
            safe_name(name)
            if relative.casefold() in folded or any(part in (".", "..") for part in relative.split("/")):
                raise ValueError("Ambiguous folder port paths")
            folded.add(relative.casefold())
            if relative != "horizon-mod.toml" and relative.split("/", 1)[0] not in ("assets", "data"):
                raise ValueError("Folder ports may contain only horizon-mod.toml, assets/, and data/")
            if relative != "horizon-mod.toml" and not re.fullmatch(r"[a-z0-9_./-]+", relative):
                raise ValueError("Nonportable engine content path")
            if child.is_dir():
                continue
            mode = child.stat().st_mode
            if not stat.S_ISREG(mode) or child.stat().st_size > 16 << 20:
                raise ValueError("Invalid or oversized folder port file")
            total += child.stat().st_size
            if len(result) >= MAX_FILES or total > MAX_BYTES:
                raise ValueError("Folder port exceeds bounded copy limits")
            result[relative] = digest(child)
    if "horizon-mod.toml" not in result:
        raise ValueError("Missing folder content manifest")
    return result


def _manifest(path: Path) -> dict:
    value = tomllib.loads((path / "horizon-mod.toml").read_text(encoding="utf-8"))
    if (not ID.fullmatch(value.get("id", "")) or value.get("api") != "0.2"
            or value.get("capabilities") != ["registries"] or value.get("side") not in ("client", "both")
            or not isinstance(value.get("name"), str) or not isinstance(value.get("version"), str)):
        raise ValueError("Only validated API 0.2 data-only registries folder mods can be installed")
    return value


class JavaModLibrary:
    def __init__(self, launcher: Launcher):
        self.launcher = launcher

    @property
    def root(self) -> Path:
        return self.launcher.game.absolute() / "java-mods"

    def _safe(self, path: Path):
        boundary = self.launcher.support.absolute()
        if not path.is_absolute() or not path.is_relative_to(boundary):
            raise ValueError("Managed library path escaped the selected support root")
        for ancestor in (path, *path.parents):
            _plain(ancestor)
            if ancestor == boundary:
                break

    def _directories(self):
        for path in (self.root, self.root / "imports", self.root / "ports", self.root / "staging", self.root / "removed"):
            self._safe(path)
            path.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _mutation(self):
        self._directories()
        if self.launcher.child is not None and self.launcher.child.poll() is None:
            raise ValueError("Close the running game before changing Java mods")
        if self.launcher.operation_lock.exists():
            raise ValueError("Wait for the launcher operation to finish")
        lock = self.root / "library.lock"
        _plain(lock)
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ValueError("Another operation owns this Java mod library") from error
        try:
            os.write(descriptor, str(os.getpid()).encode())
            # Use the launcher's shared lock too: checking its existence alone
            # races another controller starting a game/native build.
            if self.launcher.lock_fd is not None:
                raise ValueError("This launcher already owns an operation")
            self.launcher.acquire()
            try:
                yield
            finally:
                self.launcher.release()
        finally:
            os.close(descriptor)
            lock.unlink()

    def _import_dir(self, token: str) -> Path:
        if not isinstance(token, str) or not TOKEN.fullmatch(token):
            raise ValueError("Invalid imported JAR token")
        path = self.root / "imports" / token
        self._safe(path)
        return path

    def _entry(self, token: str) -> ImportedJar:
        directory = self._import_dir(token)
        receipt = _read(directory / "import.json")
        path = directory / "source.jar"
        _plain(path)
        if receipt.get("token") != token or not path.is_file() or digest(path) != receipt.get("sha256"):
            raise ValueError("Imported JAR snapshot changed; preserve it and import a fresh copy")
        metadata = inspect_jar(path)
        if metadata.sha256 != receipt["sha256"]:
            raise ValueError("Imported JAR changed during inspection")
        report = self._report_path(receipt["report_file"]) if receipt.get("report_file") else None
        dependencies = Path(receipt["dependencies"]) if receipt.get("dependencies") else None
        return ImportedJar(token, metadata.mod_id, metadata.name, metadata.version, metadata.loader,
                           path, metadata.sha256, report, dependencies, metadata)

    def _report_path(self, relative: str) -> Path:
        if not isinstance(relative, str) or "\\" in relative or ":" in relative or any(part in ("", ".", "..") for part in relative.split("/")):
            raise ValueError("Invalid profile report path")
        path = self.root / relative
        self._safe(path)
        if not path.is_relative_to(self.root / "runs") or path.name != "report.json":
            raise ValueError("Report does not belong to this profile")
        return path

    def imports(self) -> list[ImportedJar]:
        self._directories()
        return [self._entry(path.name) for path in sorted((self.root / "imports").iterdir())]

    def import_jar(self, path: Path) -> ImportedJar:
        source = Path(path).expanduser().absolute()
        _plain(source)
        if source.suffix.lower() != ".jar" or not source.is_file() or source.stat().st_size > MAX_BYTES:
            raise ValueError("Choose a regular bounded Java .jar file")
        with self._mutation():
            token = uuid.uuid4().hex
            stage = self.root / "staging" / token
            stage.mkdir(mode=0o700)
            try:
                before = digest(source)
                shutil.copyfile(source, stage / "source.jar")
                metadata = inspect_jar(stage / "source.jar")
                if metadata.sha256 != before or digest(source) != before:
                    raise ValueError("Source JAR changed while importing")
                if not metadata.mod_id or not metadata.loader:
                    raise ValueError("JAR needs readable Fabric, Forge, or NeoForge metadata")
                json_write(stage / "import.json", {"schema": 1, "token": token, "sha256": before,
                    "original_name": source.name, "metadata": metadata.raw,
                    "report_file": None, "dependencies": None})
                if os.name != "nt":
                    (stage / "source.jar").chmod(0o400)
                os.rename(stage, self._import_dir(token))
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
            return self._entry(token)

    def set_dependencies(self, token: str, folder: Path) -> ImportedJar:
        folder = Path(folder).expanduser().absolute()
        _plain(folder)
        if not folder.is_dir():
            raise ValueError("Choose an existing user-owned mod or instance folder")
        with self._mutation():
            self._entry(token)
            path = self._import_dir(token) / "import.json"
            value = _read(path)
            value["dependencies"] = str(folder)
            json_write(path, value)
            return self._entry(token)

    def _validated(self, entry: ImportedJar, report: AnalysisReport) -> tuple[dict, Path]:
        report_file = Path(report.workspace).absolute() / "report.json"
        expected = self._report_path(report_file.relative_to(self.root).as_posix())
        if report.profile != self.launcher.config["profile"] or expected != report_file:
            raise ValueError("Analysis report belongs to another profile")
        data = _read(report_file)
        if _canonical(data) != _canonical(report.to_dict()):
            raise ValueError("Analysis object and saved report disagree")
        matching = [row for row in data.get("mods", []) if isinstance(row, dict)
                    and row.get("raw_evidence", {}).get("input_sha256") == entry.sha256
                    and row.get("id") == entry.mod_id]
        if len(matching) != 1:
            raise ValueError("Analysis does not identify this imported JAR snapshot")
        exported = self._import_dir(entry.token) / ("validated-" + uuid.uuid4().hex + ".json")
        PortPackAdapter(self.launcher).export_report(report_file, exported)
        return _read(exported), report_file

    def _save(self, token: str, report: AnalysisReport) -> ImportedJar:
        entry = self._entry(token)
        data, report_file = self._validated(entry, report)
        path = self._import_dir(token) / "import.json"
        receipt = _read(path)
        relative = report_file.relative_to(self.root).as_posix()
        port_trees = {}
        if data.get("operation") == "port" and data.get("status") == REQUIRES_PORTING:
            for row in data["mods"]:
                if row["id"] == entry.mod_id and row.get("port_path"):
                    source = Path(row["port_path"])
                    if not source.is_absolute() or not source.is_relative_to(report_file.parent):
                        raise ValueError("Generated port escaped its run")
                    self._safe(source)
                    port_trees[row["id"]] = _tree(source)
        if receipt.get("report_file") == relative and receipt.get("port_trees") != port_trees:
            raise ValueError("Generated folder port changed after its receipt was saved")
        receipt.update(report_file=relative, report_sha256=digest(report_file), port_trees=port_trees)
        json_write(path, receipt)
        return self._entry(token)

    def save_report(self, token: str, report: AnalysisReport) -> ImportedJar:
        with self._mutation():
            return self._save(token, report)

    def _occupied(self) -> dict[str, list[Path]]:
        found = {}
        for mod in self.launcher.mods():
            found.setdefault(mod.id, []).append(mod.path)
        folder = self.launcher.game / "horizon-mods"
        self._safe(folder.absolute())
        if folder.exists():
            for path in folder.iterdir():
                _plain(path)
                if path.is_dir() and (path / "horizon-mod.toml").is_file():
                    _plain(path / "horizon-mod.toml")
                    manifest = tomllib.loads((path / "horizon-mod.toml").read_text(encoding="utf-8"))
                    identity = manifest.get("id")
                    if not isinstance(identity, str) or not ID.fullmatch(identity):
                        raise ValueError("Existing folder mod has an unreadable identity")
                    found.setdefault(identity, []).append(path)
        return found

    def _port(self, identity: str) -> PortedMod:
        if not isinstance(identity, str) or not ID.fullmatch(identity):
            raise ValueError("Invalid engine mod ID")
        receipt = _read(self.root / "ports" / (identity + ".json"))
        path = self.launcher.game / "horizon-mods" / identity
        self._safe(path.absolute())
        if receipt.get("id") != identity or _tree(path) != receipt.get("tree"):
            raise ValueError("Installed folder port changed; preserve and review it before managing")
        manifest = _manifest(path)
        if manifest["id"] != identity:
            raise ValueError("Folder port manifest identity changed")
        return PortedMod(identity, manifest["name"], manifest["version"], path,
                         pairs(self.launcher.game / "horizon-mods.txt").get("mod." + identity) == "true",
                         self._report_path(receipt["report_file"]))

    def ports(self) -> list[PortedMod]:
        self._directories()
        return [self._port(path.stem) for path in sorted((self.root / "ports").glob("*.json"))]

    def install_port(self, token: str, report: AnalysisReport) -> PortedMod:
        with self._mutation():
            entry = self._entry(token)
            receipt_path = self._import_dir(token) / "import.json"
            receipt = _read(receipt_path)
            relative = (Path(report.workspace) / "report.json").relative_to(self.root).as_posix()
            if receipt.get("report_file") != relative:
                entry = self._save(token, report)
                receipt = _read(receipt_path)
            if digest(Path(report.workspace) / "report.json") != receipt.get("report_sha256"):
                raise ValueError("Saved analysis report changed after review")
            data, report_file = self._validated(entry, report)
            if data.get("operation") != "port" or data.get("status") != REQUIRES_PORTING or len(data.get("mods", [])) != 1:
                raise ValueError("Only a fully recorded single-mod local data port can be installed")
            row = data["mods"][0]
            if row.get("status") != REQUIRES_PORTING or row["id"] != entry.mod_id or not row.get("port_path"):
                raise ValueError("No supported data-only port was recorded")
            if not ID.fullmatch(entry.mod_id):
                raise ValueError("Java mod ID does not meet the pinned engine's [a-z0-9_] limit")
            source = Path(row["port_path"])
            if not source.is_absolute() or not source.is_relative_to(report_file.parent):
                raise ValueError("Generated folder port is outside its run")
            self._safe(source)
            tree = _tree(source)
            if tree != receipt.get("port_trees", {}).get(entry.mod_id):
                raise ValueError("Generated folder port changed after analysis")
            manifest = _manifest(source)
            if (manifest["id"], manifest["version"]) != (entry.mod_id, entry.version):
                raise ValueError("Ported manifest contradicts imported mod identity/version")
            destination = self.launcher.game / "horizon-mods" / entry.mod_id
            self._safe(destination.absolute())
            port_receipt = self.root / "ports" / (entry.mod_id + ".json")
            if destination.exists() or port_receipt.exists() or entry.mod_id in self._occupied():
                raise ValueError("A runtime, native, or folder mod with this ID is already installed")
            settings = self.launcher.game / "horizon-mods.txt"
            _plain(settings)
            stage = self.root / "staging" / uuid.uuid4().hex
            try:
                shutil.copytree(source, stage)
                if _tree(stage) != tree or _tree(source) != tree:
                    raise ValueError("Folder port changed during installation")
                destination.parent.mkdir(parents=True, exist_ok=True)
                update_pairs(settings, {"mod." + entry.mod_id: "false"})
                os.rename(stage, destination)
                try:
                    json_write(port_receipt, {
                        "schema": 1, "id": entry.mod_id, "token": token,
                        "tree": tree, "report_file": receipt["report_file"],
                        "report_sha256": receipt["report_sha256"], "source_sha256": entry.sha256})
                except OSError:
                    os.rename(destination, stage)
                    raise
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
            return self._port(entry.mod_id)

    def _selected_port(self, port: PortedMod) -> PortedMod:
        selected = self._port(port.id)
        if port.path != selected.path or port.report_file != selected.report_file:
            raise ValueError("The selected port belongs to another profile or receipt")
        return selected

    def enable_port(self, port: PortedMod, enabled: bool):
        with self._mutation():
            selected = self._selected_port(port)
            if any(path != selected.path for path in self._occupied().get(selected.id, [])):
                raise ValueError("Another installed mod now has this ID; resolve the collision first")
            _plain(self.launcher.game / "horizon-mods.txt")
            update_pairs(self.launcher.game / "horizon-mods.txt", {"mod." + selected.id: str(bool(enabled)).lower()})

    def remove_port(self, port: PortedMod) -> Path:
        with self._mutation():
            selected = self._selected_port(port)
            _plain(self.launcher.game / "horizon-mods.txt")
            backup = self.root / "removed" / (uuid.uuid4().hex + "-" + selected.id)
            backup.mkdir(mode=0o700)
            receipt = self.root / "ports" / (selected.id + ".json")
            shutil.copyfile(receipt, backup / "receipt.json")
            update_pairs(self.launcher.game / "horizon-mods.txt", {"mod." + selected.id: "false"})
            os.rename(selected.path, backup / "content")
            receipt.unlink()
            return backup
