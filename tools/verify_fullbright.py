#!/usr/bin/env python3
"""Run the pinned renderer's real CPU lightmap tests; never execute pack GLSL.

The optional private Photon upload is read as bounded data and is never bundled.
This probe does not validate resource-pack UI, GPU rendering or gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import RUST, REVISION
from tools.verify_rlcraft_flint import verified_source
from tools.verify_rlcraft_chainmail import registry_pins

ARCHIVE_SHA256 = "a51dc9c24afa8d98f75fa88abe6308774625cd10a126c62e4b1fa4d0254ab79e"
FRAGMENT_SHA256 = "cfeeb9abd871b1ac5a0e3b84a8f1a47182838880b33e3b6a7a08cbf95048a86a"
FRAGMENT = "assets/minecraft/shaders/core/lightmap.fsh"


def photon_fragment(path: Path) -> bytes:
    if path.stat().st_size != 3657:
        raise ValueError("Expected the exact original 3,657-byte Photon ZIP")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Photon archive SHA-256 differs; preserve the original ZIP unchanged")
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(FRAGMENT)
        if info.file_size != 216:
            raise ValueError("Unexpected Photon fragment size")
        fragment = archive.read(info)  # One pinned entry; never extract arbitrary paths.
    if hashlib.sha256(fragment).hexdigest() != FRAGMENT_SHA256:
        raise ValueError("Photon fragment SHA-256 differs")
    return fragment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-source", type=Path)
    parser.add_argument("--photon", type=Path, help="Optional original private user ZIP, never uploaded")
    parser.add_argument("--report", type=Path, default=ROOT / ".cache/photon-lightmap.json")
    parser.add_argument("--fetch", action="store_true", help="Fetch only dependencies from the pinned lock")
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.unlink(missing_ok=True)
    fragment = photon_fragment(args.photon) if args.photon else None
    source = verified_source(args.prepared_source) if args.prepared_source else Path(subprocess.check_output(
        [sys.executable, str(ROOT / "tools/prepare_upstream.py")], cwd=ROOT, text=True).strip())
    lightmap = (source / "crates/horizon-client-render/src/gfx/lightmap.rs").read_text(encoding="utf-8")
    # Preserve production code and its three asset-free tests byte for byte.
    # The following ignored integration tests need the complete GPU client crate;
    # they remain in that crate and are not compiled by this small CPU probe.
    probe = lightmap[:lightmap.index("    /// The uploaded archive remains an external validation input")] + "}\n"
    environment = (source / "crates/horizon-client-render/src/environment.rs").read_text(encoding="utf-8")
    sky = environment[environment.index("#[derive(Clone, Copy, Debug, Default)]\npub struct Sky {"):environment.index("impl Environment {")]
    env = dict(os.environ, CARGO_TARGET_DIR=str(ROOT / ".cache/better-leaves-target"))
    if sys.platform == "win32":
        env["RUSTFLAGS"] = "-C target-feature=+crt-static -C link-arg=/STACK:16777216"
    with tempfile.TemporaryDirectory(prefix="herps-fullbright-") as temporary:
        work = Path(temporary)
        (work / "src").mkdir()
        manifest = '[package]\nname="herps-fullbright-probe"\nversion="0.1.0"\nedition="2024"\n[workspace]\nresolver="2"\n[dependencies]\nglam="=0.30.10"\nsha2="=0.10.9"\n'
        (work / "Cargo.toml").write_text(manifest, encoding="utf-8")
        shutil.copyfile(source / "Cargo.lock", work / "Cargo.lock")
        (work / "src/lightmap.rs").write_text(probe, encoding="utf-8")
        library = "#![allow(dead_code)]\nmod environment {\n" + sky + "\n}\nmod lightmap;\n"
        if fragment is not None:
            effective = work / "effective-overlay"
            target = effective / FRAGMENT
            target.parent.mkdir(parents=True)
            target.write_bytes(fragment)
            env["HERPS_TEST_PHOTON_ROOT"] = str(effective)
            library += (ROOT / "packaging/photon_probe.rs").read_text(encoding="utf-8")
        (work / "src/lib.rs").write_text(library, encoding="utf-8")
        cargo = ["cargo", f"+{RUST}"]
        if args.fetch:
            subprocess.run(cargo + ["fetch", "--manifest-path", str(work / "Cargo.toml")], env=env, check=True)
        subprocess.run(cargo + ["metadata", "--offline", "--format-version", "1", "--manifest-path", str(work / "Cargo.toml")],
                       env=env, check=True, stdout=subprocess.DEVNULL)
        if not registry_pins(work / "Cargo.lock") <= registry_pins(source / "Cargo.lock"):
            raise ValueError("Probe dependencies differ from the pinned engine lock")
        result = subprocess.run(cargo + ["test", "--offline", "--locked", "--lib", "--manifest-path", str(work / "Cargo.toml")],
                                env=env, check=True, text=True, stdout=subprocess.PIPE)
        print(result.stdout)
        count = 4 if fragment is not None else 3
        if not re.search(rf"test result: ok\. {count} passed; 0 failed; 0 ignored", result.stdout):
            raise ValueError("Expected native CPU cases did not all run")
    report = dict(status="passed", passed=count, failed=0, skipped=0, platform=sys.platform,
                  engine_revision=REVISION, rust_toolchain=RUST,
                  lightmap_source_sha256=hashlib.sha256(lightmap.encode()).hexdigest(),
                  sky_type_sha256=hashlib.sha256(sky.encode()).hexdigest(),
                  private_photon_input="passed" if fragment is not None else "NOT RUN: private input absent",
                  archive_sha256=ARCHIVE_SHA256, fragment_sha256=FRAGMENT_SHA256,
                  scope="Exact production CPU code/type and unit tests; private case checks an effective file only",
                  resource_pack_overlay_integration="NOT RUN: full renderer integration needs private archive",
                  gpu_and_interactive_gameplay="NOT RUN", redistributed_pack=False)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
