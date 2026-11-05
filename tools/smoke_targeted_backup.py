#!/usr/bin/env python3
"""Exact FunCraft input + trusted passive helper + owned world-byte round trip.

This uses temporary profiles, never the user's existing game data. The bytes
are not a Minecraft world and the result never establishes real gameplay.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import Launcher, digest, json_write
from herps_launcher.modpacks.service import ModpackLibrary
from herps_launcher.modpacks.targeted_backup import (FUNCRAFT_SHA256, create_backup,
                                                     eligibility, verify_backup)


def run(source: Path, backend: Path):
    source, backend = source.absolute(), backend.absolute()
    if digest(source) != FUNCRAFT_SHA256:
        raise ValueError("Use the exact inspected FunCraft hotfix ZIP")
    with tempfile.TemporaryDirectory(prefix="actual-funcraft-backup-") as temporary:
        root = Path(temporary)
        launcher = Launcher(root / "owned support")
        launcher.add_profile("funcraft_trial")
        launcher.config["port_pack_binary"] = str(backend)
        launcher.save()
        paths = [launcher.game / "saves/Owned/level.dat", launcher.support / "game/saves/Untouched/level.dat",
                 launcher.game / "options.txt", launcher.config_file]
        for path in paths[:3]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"Owned fixture only, not real gameplay or a valid Minecraft world: " + path.name.encode())
        before = {str(p.relative_to(launcher.support)): digest(p) for p in paths}
        original_path = os.environ.get("PATH")
        os.environ["PATH"] = ""
        try:
            library = ModpackLibrary(launcher, executable=backend)
            entry = library.import_pack(source)
            identity = eligibility(library, entry.token)
            if not identity["available"] or digest(entry.source) != FUNCRAFT_SHA256:
                raise ValueError("Actual input did not pass the production target guard")
            result = create_backup(library, entry.token, external_processes_closed=True)
            checked = verify_backup(Path(result["path"]))
            if not checked["verified"] or checked["gameplay_verified"]:
                raise ValueError("Backup receipt did not retain the evidence boundary")
        finally:
            if original_path is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = original_path
        if before != {str(p.relative_to(launcher.support)): digest(p) for p in paths}:
            raise ValueError("Owned fixture/config data changed")
        restored = root / "separate restore"
        # This ZIP was just created from owned data and independently verified.
        with ZipFile(result["path"]) as zipped:
            zipped.extractall(restored)
        if (restored / "saves/Owned/level.dat").read_bytes() != paths[0].read_bytes():
            raise ValueError("Scratch restore differs from the owned source bytes")
        _, receipt = library._receipt(entry.token)
        commands = [{"program": "horizon-port-pack", "command": c["argv"][1], "exit_code": c["exit_code"]}
                    for c in receipt["import_evidence"]["commands"]]
        if not commands or any(c["command"] != "import" or c["exit_code"] != 0 for c in commands):
            raise ValueError("Expected only successful passive import commands")
        result["path"] = "$OWNED_TEST_SUPPORT/" + Path(result["path"]).relative_to(launcher.support).as_posix()
        return {"schema": 1, "platform": platform.system(), "input_sha256": digest(source),
            "backend_sha256": digest(backend), "input_identity": identity, "commands": commands,
            "source_files": {p: digest(ROOT / p) for p in ("herps_launcher/modpacks/targeted_backup.py", "herps_launcher/modpacks/page.py")},
            "developer_tools_on_path": False, "backup": result, "source_hashes_preserved": before,
            "scratch_unzip_roundtrip": True, "fixture_note": "Owned sentinel bytes; not a valid Minecraft world; no original mod code/assets executed",
            "interactive_verified": False, "gameplay_verified": False, "rlcraft_2_9_3_inspected": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--funcraft", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True, help="Trusted local horizon-port-pack from the pinned engine, never a modpack executable")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.funcraft, args.backend)
    json_write(args.report, result)
    print("Exact-input backup round trip passed with owned fixtures; real gameplay remains unverified")
