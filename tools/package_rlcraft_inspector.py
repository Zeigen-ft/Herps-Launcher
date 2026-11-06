#!/usr/bin/env python3
"""Stage the tested standalone inspector; no modpack data or compiled code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def stage(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for source, name in [(ROOT / "tools/inspect_rlcraft_293.py", "inspect_rlcraft_293.py"),
                         (ROOT / "packaging/Inspect-RLCraft.cmd", "Inspect-RLCraft.cmd"),
                         (ROOT / "docs/targeted-porting/WINDOWS_RLCRAFT_INSPECTION.md", "README.txt"),
                         (ROOT / "LICENSE", "LICENSE")]:
        shutil.copyfile(source, output / name)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    (output / "inspector.json").write_text(json.dumps({"schema": 1, "source_commit": commit,
        "script_sha256": hashes["inspect_rlcraft_293.py"], "files_sha256": hashes,
        "python": "3.12", "requires_rust": False, "requires_java": False,
        "default_export_payload_bytes": 24 << 20, "strict_export_zip_limit_bytes": 32 << 20,
        "gameplay_verified": False}, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS").write_text("\n".join(f"{value}  {name}" for name, value in sorted(hashes.items())) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    stage(parser.parse_args().output)
