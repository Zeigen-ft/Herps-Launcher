#!/usr/bin/env python3
"""Compile an external trusted probe; never change the pinned prepared source."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import REVISION, RUST, target
from herps_launcher.modpacks.chainmail import PACKAGE_NAME, PACKAGE_SHA256, validate_package
from tools.build_rlcraft_chainmail import build


def registry_pins(lock):
    return {(p["name"], p["version"], p.get("source"), p.get("checksum"))
            for p in tomllib.loads(lock.read_text(encoding="utf-8"))["package"] if p.get("source")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-crafting", action="store_true", help="Also link actual native recipe loader/matcher")
    parser.add_argument("--report", type=Path, default=ROOT / ".cache/chainmail-native.json")
    args = parser.parse_args()
    build(ROOT / ".cache/targeted-content")
    package = ROOT / ".cache/targeted-content" / PACKAGE_NAME
    validate_package(package)
    prepared = subprocess.check_output([sys.executable, str(ROOT / "tools/prepare_upstream.py")], cwd=ROOT, text=True).strip()
    source = Path(prepared)
    stamp = json.loads((source / ".herspers-prepared.json").read_text())
    if stamp["upstream"]["commit"] != REVISION:
        raise ValueError("Unexpected engine revision")
    cache = ROOT / ".cache/chainmail-probe"
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="probe-", dir=cache) as directory:
        crate = Path(directory)
        features = '["dep:horizon-client","dep:horizon-world"]' if args.native_crafting else '[]'
        manifest = ('[package]\nname="herspers-chainmail-probe"\nversion="0.1.0"\nedition="2024"\n'
                    f'[workspace]\n[features]\ncrafting={features}\n[dependencies]\n'
                    'serde_json="=1.0.151"\n')
        dependencies = ("horizon-mods", "horizon-client", "horizon-world") if args.native_crafting else ("horizon-mods",)
        for name in dependencies:
            path = (source / "crates" / name).as_posix()
            optional = ', optional=true' if name != "horizon-mods" else ', default-features=false'
            features = ', features=["mods"]' if name == "horizon-client" else ''
            manifest += f'{name}={{path={json.dumps(path)}{optional}{features}}}\n'
        manifest += '\n[profile.fast]\ninherits="release"\nlto=false\ncodegen-units=16\nincremental=true\n'
        (crate / "Cargo.toml").write_text(manifest, encoding="utf-8")
        (crate / "src").mkdir()
        shutil.copyfile(ROOT / "packaging/chainmail_probe.rs", crate / "src/main.rs")
        shutil.copyfile(source / "Cargo.lock", crate / "Cargo.lock")
        env = dict(os.environ)
        env["CARGO_TARGET_DIR"] = str(ROOT / ".cache/target")
        host = target() if sys.platform != "linux" else "x86_64-unknown-linux-gnu"
        if sys.platform == "win32":
            env["RUSTFLAGS"] = "-C target-feature=+crt-static -C link-arg=/STACK:16777216"
        command = ["cargo", f"+{RUST}", "metadata", "--offline", "--filter-platform", host, "--format-version", "1", "--manifest-path", str(crate / "Cargo.toml")]
        if args.native_crafting:
            command += ["--features", "crafting"]
        subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL)
        if not registry_pins(crate / "Cargo.lock") <= registry_pins(source / "Cargo.lock"):
            raise ValueError("Probe resolved dependencies outside the pinned engine lock")
        command = ["cargo", f"+{RUST}", "build", "--offline", "--locked", "--profile", "fast",
                   "--target", host, "--manifest-path", str(crate / "Cargo.toml")]
        if args.native_crafting:
            command += ["--features", "crafting"]
        subprocess.run(command, check=True, env=env)
        binary = ROOT / ".cache/target" / host / "fast" / ("herspers-chainmail-probe.exe" if sys.platform == "win32" else "herspers-chainmail-probe")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.unlink(missing_ok=True)
        subprocess.run([str(binary), str(package), str(args.report.resolve()), str(crate / "fixture")], check=True, env=env)
        report = json.loads(args.report.read_text())
        report.update(engine_revision=REVISION, package_sha256=PACKAGE_SHA256,
                      target=host, rust_toolchain=RUST)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
