#!/usr/bin/env python3
"""Stage independently authored native survival content; execute no mod code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def package_bytes(source: Path = ROOT / "content/rlcraft_gathering") -> bytes:
    # Keep the reviewed deterministic ZIP format shared with the first slice.
    from tools.build_rlcraft_chainmail import package_bytes as content_bytes
    return content_bytes(source)


def build(output: Path) -> dict:
    from herps_launcher.core import REVISION
    from herps_launcher.modpacks.gathering import PACKAGE_NAME, PACKAGE_SHA256, validate_package
    data = package_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != PACKAGE_SHA256:
        raise ValueError(f"Reviewed gathering add-on changed: {sha}; review before updating the pin")
    if output.is_symlink() or output.is_junction():
        raise ValueError("Linked gathering output is unsupported")
    output.mkdir(parents=True, exist_ok=True)
    path = output / PACKAGE_NAME
    if path.is_symlink() or path.is_junction() or (path.exists() and path.read_bytes() != data):
        raise ValueError("Preserve a different or linked staged gathering package")
    path.write_bytes(data)
    validate_package(path)
    report = {"schema": 1, "source_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "stage": 2, "package": PACKAGE_NAME, "sha256": sha, "size": len(data),
        "default_enabled": False, "gameplay_verified": False, "interactive_verified": False,
        "engine_revision": REVISION, "api": "0.2", "items": 0, "recipes": 0, "requires": "herspers_rl_flint-0.1.0",
        "native_engine_feature": "rlcraft-gathering-1",
        "full_rlcraft_compatibility": False, "original_mod_code_or_assets_included": False}
    (output / "gathering-package.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "GATHERING-SHA256SUMS.txt").write_text(f"{sha}  {PACKAGE_NAME}\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/targeted-content")
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
