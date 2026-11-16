#!/usr/bin/env python3
"""Validate reviewed server functions with the pinned native command parser only."""
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
from tools.build_server_lighting import pack_files
from tools.verify_rlcraft_chainmail import probe_manifest, registry_pins
from tools.verify_rlcraft_flint import verified_source
from herps_launcher.core import RUST


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared-source', type=Path)
    args = parser.parse_args()
    if args.prepared_source:
        source = verified_source(args.prepared_source)
    else:
        source = Path(subprocess.check_output([sys.executable, str(ROOT / 'tools/prepare_upstream.py')], text=True).strip())
    with tempfile.TemporaryDirectory(prefix='herps-lighting-probe-') as directory:
        crate = Path(directory)
        manifest = probe_manifest(source, False).replace('herspers-chainmail-probe', 'herps-lighting-command-probe')
        manifest = manifest.replace('horizon-mods={', 'horizon-command={').replace('/crates/horizon-mods', '/crates/horizon-command')
        (crate / 'Cargo.toml').write_text(manifest)
        shutil.copyfile(source / 'Cargo.lock', crate / 'Cargo.lock')
        (crate / 'src').mkdir()
        shutil.copyfile(ROOT / 'packaging/server-lighting/command_probe.rs', crate / 'src/main.rs')
        functions = crate / 'functions'
        functions.mkdir()
        for name, data in pack_files().items():
            if name.endswith('.mcfunction'):
                (functions / Path(name).name).write_bytes(data)
        env = dict(os.environ, CARGO_TARGET_DIR=str(ROOT / '.cache/server-lighting-target'))
        command = ['cargo', f'+{RUST}']
        subprocess.run([*command, 'metadata', '--format-version', '1', '--manifest-path', str(crate / 'Cargo.toml')],
                       check=True, env=env, stdout=subprocess.DEVNULL)
        if not registry_pins(crate / 'Cargo.lock') <= registry_pins(source / 'Cargo.lock'):
            raise ValueError('Probe resolved dependencies outside the pinned engine lock')
        subprocess.run([*command, 'run', '--locked', '--profile', 'fast', '--manifest-path', str(crate / 'Cargo.toml'),
                        '--', str(functions)], check=True, env=env)
        print(json.dumps({'engine_revision': json.loads((source / '.herspers-prepared.json').read_text())['upstream']['commit'],
                          'verification': 'native command parsing only', 'runtime': 'NOT RUN', 'gameplay': 'NOT RUN'}))


if __name__ == '__main__':
    main()
