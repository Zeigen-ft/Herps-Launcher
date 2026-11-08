#!/usr/bin/env python3
"""Validate rebuilt leaves with exact pinned native parsing/baking; no visual claim."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import RUST, REVISION
from tools.build_better_leaves import build, SOURCE, PACKAGE_NAME, payload, digest
from tools.verify_rlcraft_flint import verified_source
from tools.verify_rlcraft_chainmail import registry_pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-source", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/better-leaves")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--fetch", action="store_true", help="Fetch the pinned probe dependency subset on a clean CI runner")
    args = parser.parse_args()
    report = args.report or args.output / ("native-windows.json" if sys.platform == "win32" else "native-linux.json")
    report.parent.mkdir(parents=True, exist_ok=True); report.unlink(missing_ok=True)
    packaged = build(args.output)
    source = verified_source(args.prepared_source) if args.prepared_source else Path(subprocess.check_output(
        [sys.executable, str(ROOT / "tools/prepare_upstream.py")], cwd=ROOT, text=True).strip())
    # Compile the exact production format helpers without linking the GPU client.
    text = (source / "crates/horizon-client-render/src/packs.rs").read_text(encoding="utf-8")
    native_format = text[text.index("fn format_of("):text.index("/// PackCompatibility: inside")]
    native_format += '\npub fn check(pack:&serde_json::Value)->Result<((i64,i64),(i64,i64)),String>{validate_pack_range(pack,last_pre_minor(horizon_core::version::RESOURCE_PACK_FORMAT))}\n'
    cache = ROOT / ".cache/better-leaves-probe"; cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="owned-", dir=cache) as temporary:
        work = Path(temporary); (work / "src").mkdir()
        manifest = '[package]\nname="herps-better-leaves-probe"\nversion="0.1.0"\nedition="2024"\n[workspace]\nresolver="2"\n[dependencies]\nserde_json="=1.0.151"\npng="=0.18.1"\n'
        for crate in ["horizon-assets", "horizon-core"]:
            manifest += crate + '={path=' + json.dumps((source / "crates" / crate).as_posix()) + '}\n'
        manifest += '\n[profile.fast]\ninherits="release"\nlto=false\ncodegen-units=16\nincremental=true\n'
        (work / "Cargo.toml").write_text(manifest, encoding="utf-8")
        shutil.copyfile(source / "Cargo.lock", work / "Cargo.lock")
        shutil.copyfile(ROOT / "packaging/better_leaves_probe.rs", work / "src/main.rs")
        (work / "src/native_pack_format.rs").write_text('#![allow(dead_code)]\n' + native_format, encoding="utf-8")
        expanded = work / "pack"; files, _, _ = payload()
        for name, raw in files.items():
            p = expanded / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
        env = dict(os.environ, CARGO_TARGET_DIR=str(ROOT / ".cache/better-leaves-target"))
        if sys.platform == "win32": env["RUSTFLAGS"] = "-C target-feature=+crt-static -C link-arg=/STACK:16777216"
        if args.fetch:
            subprocess.run(["cargo", f"+{RUST}", "fetch", "--manifest-path", str(work / "Cargo.toml")], check=True, env=env)
        subprocess.run(["cargo", f"+{RUST}", "metadata", "--offline", "--format-version", "1", "--manifest-path", str(work / "Cargo.toml")],
            check=True, env=env, stdout=subprocess.DEVNULL)
        if not registry_pins(work / "Cargo.lock") <= registry_pins(source / "Cargo.lock"):
            raise ValueError("Native verification resolved dependencies outside the pinned lock")
        subprocess.run(["cargo", f"+{RUST}", "build", "--offline", "--locked", "--profile", "fast", "--manifest-path", str(work / "Cargo.toml")], check=True, env=env)
        binary = ROOT / ".cache/better-leaves-target/fast" / ("herps-better-leaves-probe.exe" if sys.platform == "win32" else "herps-better-leaves-probe")
        subprocess.run([str(binary), str(expanded), str(SOURCE / "upstream.json"), str(report.resolve())], check=True, env=env)
        result = json.loads(report.read_text())
        if result.get("status") != "passed" or len(result.get("cases", [])) != 8:
            raise ValueError("Native asset verification incomplete")
        result.update(source_commit=packaged["source_commit"], engine_revision=REVISION, rust_toolchain=RUST,
            package_sha256=packaged["sha256"], platform=sys.platform,
            metadata_helpers_sha256=hashlib.sha256(native_format.encode()).hexdigest(),
            registry_dependencies_subset_of_pinned_lock=True)
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
