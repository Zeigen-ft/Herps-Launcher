#!/usr/bin/env python3
"""Verify native bandage content, recipes and effect kernels; never claim gameplay."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import REVISION, RUST, target
from tools.verify_rlcraft_chainmail import probe_manifest, registry_pins
from tools.verify_rlcraft_flint import verified_source
from tools.build_rlcraft_bandage import build

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-source", type=Path, help="Reuse a checksum-verified local engine cache")
    parser.add_argument("--report", type=Path, default=ROOT / ".cache/bandage-native.json")
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.unlink(missing_ok=True)
    from herps_launcher.modpacks.bandage import PACKAGE_NAME, PACKAGE_SHA256, validate_package
    from herps_launcher.modpacks import flint, gathering, woodcutting
    build(ROOT / ".cache/targeted-content")
    from tools.build_rlcraft_flint import build as starter
    from tools.build_rlcraft_gathering import build as gathering_build
    from tools.build_rlcraft_woodcutting import build as woodcutting_build
    for builder in [starter, gathering_build, woodcutting_build]: builder(ROOT / ".cache/targeted-content")
    package = ROOT / ".cache/targeted-content" / PACKAGE_NAME
    validate_package(package)
    if args.prepared_source:
        source = verified_source(args.prepared_source)
    else:
        source = Path(subprocess.check_output([sys.executable, str(ROOT / "tools/prepare_upstream.py")], cwd=ROOT, text=True).strip())
    stamp = json.loads((source / ".herspers-prepared.json").read_text())
    if stamp["upstream"]["commit"] != REVISION:
        raise ValueError("Unexpected native engine revision")
    cache = ROOT / ".cache/bandage-probe"; cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="probe-", dir=cache) as temporary:
        crate = Path(temporary)
        manifest = probe_manifest(source, True).replace('name="herspers-chainmail-probe"', 'name="herspers-bandage-probe"')
        (crate / "Cargo.toml").write_text(manifest, encoding="utf-8")
        (crate / "src").mkdir()
        shutil.copyfile(ROOT / "packaging/bandage_probe.rs", crate / "src/main.rs")
        shutil.copyfile(source / "Cargo.lock", crate / "Cargo.lock")
        env = dict(os.environ)
        env["CARGO_TARGET_DIR"] = str(ROOT / ".cache/target")
        host = target() if sys.platform != "linux" else "x86_64-unknown-linux-gnu"
        if sys.platform == "win32":
            env["RUSTFLAGS"] = "-C target-feature=+crt-static -C link-arg=/STACK:16777216"
        features = ["--features", "crafting"]
        command = ["cargo", f"+{RUST}", "metadata", "--offline", "--filter-platform", host,
                   "--format-version", "1", "--manifest-path", str(crate / "Cargo.toml"), *features]
        subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL)
        if not registry_pins(crate / "Cargo.lock") <= registry_pins(source / "Cargo.lock"):
            raise ValueError("Probe resolved dependencies outside the pinned engine lock")
        subprocess.run(["cargo", f"+{RUST}", "build", "--offline", "--locked", "--profile", "fast",
            "--target", host, "--manifest-path", str(crate / "Cargo.toml"), *features], check=True, env=env)
        binary = ROOT / ".cache/target" / host / "fast" / ("herspers-bandage-probe.exe" if sys.platform == "win32" else "herspers-bandage-probe")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.unlink(missing_ok=True)
        subprocess.run([str(binary), *[str(ROOT / ".cache/targeted-content" / m.PACKAGE_NAME) for m in [flint, gathering, woodcutting]], str(package), str(args.report.resolve()), str(crate / "fixture")], check=True, env=env)
        report = json.loads(args.report.read_text())
        report.update(engine_revision=REVISION, package_sha256=PACKAGE_SHA256,
                      target=host, rust_toolchain=RUST,
                      source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
