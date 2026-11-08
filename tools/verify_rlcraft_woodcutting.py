#!/usr/bin/env python3
"""Verify the opt-in native tag and woodcutting transaction rules, not gameplay."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import REVISION, RUST, target
from tools.verify_rlcraft_chainmail import probe_manifest, registry_pins
from tools.verify_rlcraft_flint import verified_source


def verify_rules(source: Path, work: Path, env: dict) -> dict:
    for name, file in [("rules", "herspers_woodcutting_rules"), ("adapter", "herspers_woodcutting")]:
        if (ROOT / f"native/rlcraft_woodcutting/{name}.rs").read_bytes().replace(b"\r\n", b"\n") != (
                source / f"crates/horizon-client/src/game/{file}.rs").read_bytes():
            raise ValueError("Woodcutting engine patch differs from its reviewed source")
    binary = work / ("woodcutting-rules.exe" if sys.platform == "win32" else "woodcutting-rules")
    subprocess.run(["rustc", f"+{RUST}", "--edition", "2024", "--test",
        str(source / "crates/horizon-client/src/game/herspers_woodcutting_rules.rs"), "-o", str(binary)], check=True, env=env)
    result = subprocess.run([str(binary), "--nocapture"], check=True, env=env, text=True, capture_output=True)
    (work / "rules.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if not re.search(r"test result: ok\. 9 passed; 0 failed; 0 ignored", result.stdout):
        raise ValueError("Woodcutting rule cohort is incomplete")
    return {"tests_run":9, "passed":9, "failed":0, "skipped":0,
        "scope":"actual progression policy; not live Game hook execution"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-source", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / ".cache/woodcutting-native.json")
    args = parser.parse_args()
    from tools.build_rlcraft_flint import build as build_starter
    from tools.build_rlcraft_woodcutting import build
    from herps_launcher.modpacks import flint, gathering, woodcutting
    content = ROOT / ".cache/targeted-content"; build_starter(content); build(content)
    from tools.build_rlcraft_gathering import build as build_gathering
    build_gathering(content)
    source = verified_source(args.prepared_source) if args.prepared_source else Path(subprocess.check_output(
        [sys.executable, str(ROOT / "tools/prepare_upstream.py")], cwd=ROOT, text=True).strip())
    host = "x86_64-unknown-linux-gnu" if sys.platform == "linux" else target()
    env = dict(os.environ, CARGO_TARGET_DIR=str(ROOT / ".cache/target"))
    if sys.platform == "win32": env["RUSTFLAGS"] = "-C target-feature=+crt-static -C link-arg=/STACK:16777216"
    cache = ROOT / ".cache/woodcutting-probe"; cache.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True); args.report.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="probe-", dir=cache) as temporary:
        crate = Path(temporary)
        rules = verify_rules(source, crate, env)
        args.report.with_suffix(".rules.log").write_bytes((crate / "rules.log").read_bytes())
        manifest = probe_manifest(source, True).replace('name="herspers-chainmail-probe"', 'name="herspers-woodcutting-probe"')
        manifest += '\n[dependencies.horizon-core]\npath=' + json.dumps((source / "crates/horizon-core").as_posix()) + '\n'
        (crate / "Cargo.toml").write_text(manifest, encoding="utf-8")
        (crate / "src").mkdir(); shutil.copyfile(ROOT / "packaging/woodcutting_probe.rs", crate / "src/main.rs")
        shutil.copyfile(source / "crates/horizon-client/src/game/herspers_woodcutting_rules.rs", crate / "src/woodcutting_rules.rs")
        shutil.copyfile(source / "Cargo.lock", crate / "Cargo.lock")
        subprocess.run(["cargo", f"+{RUST}", "metadata", "--offline", "--filter-platform", host,
            "--format-version", "1", "--manifest-path", str(crate / "Cargo.toml"), "--features", "crafting"],
            check=True, env=env, stdout=subprocess.DEVNULL)
        if not registry_pins(crate / "Cargo.lock") <= registry_pins(source / "Cargo.lock"):
            raise ValueError("Probe resolved packages outside the pinned lock")
        subprocess.run(["cargo", f"+{RUST}", "build", "--offline", "--locked", "--profile", "fast", "--target", host,
            "--manifest-path", str(crate / "Cargo.toml"), "--features", "crafting"], check=True, env=env)
        binary = ROOT / ".cache/target" / host / "fast" / ("herspers-woodcutting-probe.exe" if sys.platform == "win32" else "herspers-woodcutting-probe")
        subprocess.run([str(binary), str(content / flint.PACKAGE_NAME), str(content / gathering.PACKAGE_NAME), str(content / woodcutting.PACKAGE_NAME),
            str(args.report.resolve()), str(crate / "fixture")], check=True, env=env)
        report = json.loads(args.report.read_text())
        report.update(engine_revision=REVISION, package_sha256=woodcutting.PACKAGE_SHA256,
            starter_sha256=flint.PACKAGE_SHA256, target=host, rust_toolchain=RUST, rules=rules,
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
