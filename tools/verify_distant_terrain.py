#!/usr/bin/env python3
"""Test the actual patched native LOD code and type-check its game integration.

No Java, world assets, login, server connection or mod execution is involved.
These are native CPU/type checks, never evidence of interactive gameplay.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herps_launcher.core import REVISION, RUST
from tools.verify_rlcraft_flint import verified_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared-source', type=Path)
    parser.add_argument('--report', type=Path, default=ROOT / '.cache/distant-terrain-verification.json')
    args = parser.parse_args()
    source = args.prepared_source or Path(subprocess.check_output(
        [sys.executable, str(ROOT / 'tools/prepare_upstream.py')], cwd=ROOT, text=True).strip())
    source = verified_source(source)
    env = dict(os.environ, CARGO_TARGET_DIR=str(ROOT / '.cache/distant-terrain-target'),
               CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0', CARGO_BUILD_JOBS='3')
    common = ['cargo', f'+{RUST}']
    manifest = ['--locked', '--manifest-path', str(source / 'Cargo.toml')]
    commands = [
        [*common, 'test', *manifest, '-p', 'horizon-client-render', '--lib', 'lod::', '--', '--nocapture'],
        [*common, 'test', *manifest, '-p', 'horizon-client-render', '--lib', 'graphics::', '--', '--nocapture'],
        [*common, 'test', *manifest, '-p', 'horizon-client-render', '--lib', 'graphics_ui::', '--', '--nocapture'],
        [*common, 'check', *manifest, '-p', 'horizon-client', '--bin', 'horizon-client', '--features', 'horizon-client/mods'],
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.unlink(missing_ok=True)
    for command in commands:
        print('VERIFY:', ' '.join(command), flush=True)
        subprocess.run(command, cwd=source, check=True, env=env)
    stamp = json.loads((source / '.herspers-prepared.json').read_text())
    report = dict(status='PASS', engine_revision=REVISION, rust_toolchain=RUST,
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        patches_sha256=stamp['patches_sha256'], checks=['native lod and GPU fade math unit tests', 'graphics config unit tests', 'graphics UI unit tests', 'full client integration check'],
        coverage=['native LOD downsampling/observed source/cache/mesh tests',
                  'graphics default/config/UI tests', 'existing GPU fade math tests',
                  'game binary integration type-check with existing mods feature'],
        new_mode_default='OFF', java_executed=False, distant_horizons_source_adapted=False,
        server_streaming_added=False, physical_windows_gameplay='NOT RUN',
        macos_gameplay='NOT RUN', interactive_graphics='NOT RUN', installer_built=False)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
