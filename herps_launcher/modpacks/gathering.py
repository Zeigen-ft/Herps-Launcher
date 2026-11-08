"""Opt-in installation of the bundled, code-free flint gathering add-on.

Uses the candidate engine extension and unchanged starter item IDs.
No original modpack import, Java execution or developer tool is needed. Only
fresh named disposable profiles can install it. Retain custom-item content once
saves exist: missing-item recovery is not yet physically verified.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tomllib
import uuid

from ..core import ID, archive, atomic, inspect_mod, pairs, update_pairs
from . import flint
from ..javamods.library import JavaModLibrary

MOD_ID = "herspers_rl_gathering"
VERSION = "0.1.0"
PACKAGE_NAME = f"{MOD_ID}-{VERSION}.hmod"
PACKAGE_SHA256 = "177c3f4eefedd4f0e4eda4e54634efeee555e4b22dd13e0ec022733328fb87fd"


ENGINE_FEATURE = "rlcraft-gathering-1"

def require_engine(launcher):
    features = launcher.installation().metadata.get("engine_source", {}).get("native_features", [])
    if ENGINE_FEATURE not in features:
        raise ValueError("Flint Gathering needs a stage-2 native client; select the new internal candidate installation")

def require_starter(launcher, *, enabled=False):
    state = flint.status(launcher)
    if not state["installed"] or (enabled and not state["enabled"]):
        raise ValueError("Install Flint Survival Starter in this empty disposable profile first; enable it before enabling Gathering")

def bundled_package() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "targeted-content" / PACKAGE_NAME
    return Path(__file__).resolve().parents[2] / ".cache/targeted-content" / PACKAGE_NAME


def validate_package(path: Path) -> bytes:
    if path.is_symlink() or path.is_junction() or not path.is_file() or path.stat().st_size > 256 << 10:
        raise ValueError("Missing or linked bundled flint package; use a verified internal candidate")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PACKAGE_SHA256:
        raise ValueError("Bundled flint package SHA-256 differs from the reviewed content")
    files = archive(path, 256 << 10)
    manifest = tomllib.loads(files["horizon-mod.toml"].decode())
    if (manifest.get("id") != MOD_ID or manifest.get("version") != VERSION
            or manifest.get("api") != "0.2" or manifest.get("capabilities") != ["registries"]
            or any(name.endswith((".wasm", ".jar", ".class", ".exe", ".dll")) for name in files)):
        raise ValueError("Not the reviewed code-free gathering content package")
    return data


def _path(launcher):
    return launcher.game / "horizon-mods" / PACKAGE_NAME


def _receipt(launcher):
    return launcher.state / "targeted-content" / "rlcraft-gathering" / launcher.config["profile"] / "receipt.json"


def _regular(guard, path, limit=1 << 20):
    guard._safe(path.absolute())
    if not path.exists():
        return None
    if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > limit:
        raise ValueError(f"Preserve nonregular/oversized managed file: {path}")
    return path.read_bytes()


def _profile(launcher, profile):
    if (profile != launcher.config["profile"] or profile == "default" or not ID.fullmatch(profile)
            or profile not in launcher.config["profiles"]):
        raise ValueError("Select a fresh named disposable profile; the default profile is protected")
    guard = JavaModLibrary(launcher)
    guard._safe(launcher.game.absolute())
    if launcher.pending_file.exists():
        raise ValueError("Resolve the pending launcher session before changing content")
    return guard


def _has_saves(launcher, guard):
    path = launcher.game / "saves"
    guard._safe(path.absolute())
    if not path.exists():
        return False
    if not path.is_dir():
        raise ValueError("Preserve the existing non-directory saves path")
    return next(path.iterdir(), None) is not None


def _settings(launcher, guard):
    path = launcher.game / "horizon-mods.txt"
    before = _regular(guard, path)
    _regular(guard, path.with_name(path.name + ".herps-backup"))
    return path, before


def _managed(launcher, guard):
    raw = _regular(guard, _receipt(launcher))
    if raw is None:
        raise ValueError("Install the bundled gathering feature using Modpacks and disposable-profile consent")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Flint gathering ownership receipt changed; preserve this profile for review")
    expected = {"schema": 1, "profile": launcher.config["profile"], "id": MOD_ID,
                "version": VERSION, "sha256": PACKAGE_SHA256, "disposable_confirmed": True}
    if any(value.get(key) != item for key, item in expected.items()):
        raise ValueError("Flint gathering ownership receipt changed; preserve this profile for review")
    guard._safe(_path(launcher).absolute())
    validate_package(_path(launcher))
    return value


def status(launcher):
    """Read-only status; do not treat an install receipt as gameplay evidence."""
    guard = JavaModLibrary(launcher)
    raw = _regular(guard, _receipt(launcher))
    if raw is None:
        return {"installed": False, "enabled": False, "gameplay_verified": False}
    _managed(launcher, guard)
    _settings(launcher, guard)
    return {"installed": True, "enabled": pairs(launcher.game / "horizon-mods.txt").get("mod." + MOD_ID) == "true",
            "profile": launcher.config["profile"], "sha256": PACKAGE_SHA256, "gameplay_verified": False}


def _collisions(launcher, guard):
    for identity, paths in guard._occupied().items():
        for path in paths:
            guard._safe(path.absolute())
            if path.is_dir():
                raw = _regular(guard, path / "horizon-mod.toml")
                manifest = tomllib.loads(raw.decode("utf-8"))
            else:
                manifest = inspect_mod(path).metadata
            if identity == MOD_ID or MOD_ID in manifest.get("namespaces", []):
                raise ValueError("Flint gathering ID/namespace is already occupied; existing content is preserved")


def install(launcher, profile, *, disposable_confirmed=False, games_closed=False):
    guard = _profile(launcher, profile)
    if disposable_confirmed is not True or games_closed is not True:
        raise ValueError("Explicitly confirm the selected profile is disposable and all games/servers are closed")
    if _has_saves(launcher, guard):
        raise ValueError("Install only before creating worlds in a fresh disposable profile; existing saves are protected")
    require_engine(launcher)
    require_starter(launcher)
    data = validate_package(bundled_package())
    with guard._mutation():
        _profile(launcher, profile)
        if _has_saves(launcher, guard):
            raise ValueError("The selected profile now has saves; nothing was installed")
        require_engine(launcher)
        require_starter(launcher)
        destination, receipt = _path(launcher), _receipt(launcher)
        if _regular(guard, destination) is not None or _regular(guard, receipt) is not None:
            raise ValueError("Flint gathering package/receipt already exists; preserve and review it")
        _collisions(launcher, guard)
        settings, before = _settings(launcher, guard)
        value = {"schema": 1, "profile": profile, "id": MOD_ID, "version": VERSION,
                 "sha256": PACKAGE_SHA256, "disposable_confirmed": True, "default_enabled": False,
                 "gameplay_verified": False}
        created = receipt_created = False
        settings_after = None
        try:
            # Disable before publishing, including a stale true setting for this id.
            update_pairs(settings, {"mod." + MOD_ID: "false"})
            settings_after = settings.read_bytes()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                created = True
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            receipt.parent.mkdir(parents=True, exist_ok=True)
            with receipt.open("xb") as stream:
                receipt_created = True
                stream.write((json.dumps(value, indent=2) + "\n").encode())
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            if created:
                destination.unlink(missing_ok=True)
            # Only undo our settings, never a later external edit.
            if settings_after is not None and _regular(guard, settings) == settings_after:
                if before is None:
                    settings.unlink(missing_ok=True)
                else:
                    atomic(settings, before)
            # A failed exclusive receipt write is ours only if it did open.
            if receipt_created:
                receipt.unlink(missing_ok=True)
            raise
    return status(launcher)


def set_enabled(launcher, mod, enabled):
    guard = _profile(launcher, launcher.config["profile"])
    with guard._mutation():
        _managed(launcher, guard)
        if mod.path != _path(launcher):
            raise ValueError("Flint gathering package is outside the selected managed profile")
        if enabled:
            require_engine(launcher)
            require_starter(launcher, enabled=True)
        if not enabled and _has_saves(launcher, guard):
            raise ValueError("Keep flint enabled while saves exist: missing custom-item recovery is unverified")
        settings, _ = _settings(launcher, guard)
        update_pairs(settings, {"mod." + MOD_ID: str(bool(enabled)).lower()})


def remove(launcher, mod):
    guard = _profile(launcher, launcher.config["profile"])
    with guard._mutation():
        _managed(launcher, guard)
        if mod.path != _path(launcher) or _has_saves(launcher, guard):
            raise ValueError("Remove only from the selected empty disposable profile; saves require this content")
        settings, _ = _settings(launcher, guard)
        update_pairs(settings, {"mod." + MOD_ID: "false"})
        backup = launcher.state / "removed" / (uuid.uuid4().hex + "-gathering")
        guard._safe(backup.absolute())
        backup.mkdir(parents=True)
        os.rename(mod.path, backup / PACKAGE_NAME)
        try:
            os.rename(_receipt(launcher), backup / "receipt.json")
        except BaseException:
            os.rename(backup / PACKAGE_NAME, mod.path)
            raise
        return backup


def protect_launch(launcher):
    """Fail closed for an owned profile with saves and missing/disabled content."""
    guard = JavaModLibrary(launcher)
    if _regular(guard, _receipt(launcher)) is None:
        return
    _managed(launcher, guard)
    _settings(launcher, guard)
    if status(launcher)["enabled"]:
        require_engine(launcher)
        require_starter(launcher, enabled=True)
    if _has_saves(launcher, guard) and not status(launcher)["enabled"]:
        raise ValueError("This disposable profile has saves: enable its gathering content before launching")
