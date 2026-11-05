#!/usr/bin/env python3
"""Deterministically stage the reviewed native content pack; no game/mod code runs."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZipInfo, ZIP_STORED

ROOT = Path(__file__).resolve().parents[1]
NAME = "herspers_rl_chainmail-0.1.0.hmod"


def package_bytes(source: Path = ROOT / "content/rlcraft_chainmail") -> bytes:
    files = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Linked package source")
        if path.is_file():
            files[path.relative_to(source).as_posix()] = path.read_bytes().replace(b"\r\n", b"\n")
    files["LICENSE-HERPS.txt"] = (ROOT / "LICENSE").read_bytes().replace(b"\r\n", b"\n")
    output = io.BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as zipped:
        for name, data in sorted(files.items()):
            entry = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            zipped.writestr(entry, data)
    data = output.getvalue()
    if len(data) > 256 << 10:
        raise ValueError("Unexpectedly large content pack")
    return data


def build(output: Path) -> dict:
    from herps_launcher.modpacks.chainmail import PACKAGE_SHA256, validate_package
    data = package_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != PACKAGE_SHA256:
        raise ValueError(f"Reviewed package changed: {sha}; review definitions and update the pinned digest")
    output.mkdir(parents=True, exist_ok=True)
    path = output / NAME
    if path.is_symlink() or path.is_junction() or (path.exists() and path.read_bytes() != data):
        raise ValueError("Refuse to replace a different/linked staged package")
    path.write_bytes(data)
    validate_package(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    receipt = {"schema": 1, "source_commit": commit, "package": NAME, "sha256": sha,
               "size": len(data), "default_enabled": False, "gameplay_verified": False,
               "engine_revision": "7301f6fdd7f470b11317276e7a11b4dc615c137a",
               "api": "0.2", "items": 1, "recipes": 2,
               "original_mod_code_or_assets_included": False}
    (output / "package.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS").write_text(f"{sha}  {NAME}\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/targeted-content")
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    main()
