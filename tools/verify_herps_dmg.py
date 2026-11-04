#!/usr/bin/env python3
"""Native, offscreen delivered-DMG verification. Not interactive acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(image, output, arch):
    output.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'architecture': arch, 'interactive_verified': False,
              'gameplay_verified': False, 'commands': [], 'platform': platform.platform()}
    def command(args, **kwargs):
        result = subprocess.run(list(map(str, args)), capture_output=True, text=True, **kwargs)
        report['commands'].append({'argv': list(map(str, args)), 'exit_code': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode:
            raise ValueError(f'Command failed: {args[0]} ({result.returncode}): {result.stderr}')
        return result.stdout
    try:
        if platform.system() != 'Darwin' or platform.machine() != arch:
            raise ValueError('Matching native macOS host required; no emulated acceptance')
        report['dmg_sha256'] = sha256(image)
        command(['hdiutil', 'verify', image])
        with tempfile.TemporaryDirectory(prefix='Herps delivered DMG ') as temporary:
            root = Path(temporary)
            mount = root / 'mounted'
            installed = root / 'Installed Apps With Spaces'
            installed.mkdir()
            command(['hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', mount, image])
            try:
                for name in ('Herps Launcher.app', 'Herspers Minecraft.app'):
                    command(['/usr/bin/ditto', mount / name, installed / name])
            finally:
                command(['hdiutil', 'detach', mount])
            for name in ('Herps Launcher.app', 'Herspers Minecraft.app'):
                command(['codesign', '--verify', '--deep', '--strict', installed / name])
            executable = installed / 'Herps Launcher.app/Contents/MacOS/Herps Launcher'
            command(['lipo', executable, '-verify_arch', arch])
            # Empty PATH removes developer tool discovery; absolute app/helper paths still work.
            empty_path = root / 'no developer tools'
            empty_path.mkdir()
            support = root / 'Persistent Support'
            env = {k: v for k, v in os.environ.items() if k not in
                   ('HERPS_TEST_PORT_PACK', 'CARGO_HOME', 'RUSTUP_HOME', 'PYTHONPATH', 'PYTHONHOME')}
            env.update(PATH=str(empty_path), QT_QPA_PLATFORM='offscreen',
                       PHASE5C_SUPPORT=str(support), HOME=str(root / 'clean home'))
            Path(env['HOME']).mkdir()
            for mode, name in (('--smoke-test', 'delivered-smoke.json'),
                               ('--phase5c-acceptance', 'frozen-acceptance.json')):
                receipt = output.resolve() / name
                receipt.unlink(missing_ok=True)
                command([executable, mode, '--require-installation', '--require-port-pack',
                         '--smoke-report', receipt], env=env, cwd=root, timeout=600)
                data = json.loads(receipt.read_text())
                if data.get('status') != 'passed':
                    raise ValueError(f'Failed receipt: {name}')
                if mode == '--smoke-test' and (data.get('pages_opened') != 7 or
                        data.get('architecture') != arch or not data.get('port_pack', {}).get('bundled')):
                    raise ValueError('Delivered smoke lacks architecture/navigation/bundled evidence')
                report[name] = data
            before = {str(p.relative_to(support)): sha256(p) for p in support.rglob('*') if p.is_file()}
            if not before or not any('level.dat' in name for name in before):
                raise ValueError('No persistent save evidence was created')
            # macOS removal is deletion of app bundles; support data must survive.
            for name in ('Herps Launcher.app', 'Herspers Minecraft.app'):
                shutil.rmtree(installed / name)
            after = {str(p.relative_to(support)): sha256(p) for p in support.rglob('*') if p.is_file()}
            if before != after:
                raise ValueError('App removal changed persistent support data')
            report['preserved_after_app_removal'] = after
        report.update(status='passed', gatekeeper_interactive='not tested',
                      notarization='not requested; development signing only')
    except Exception as error:
        report['error'] = str(error)
    finally:
        (output / 'delivered-dmg.json').write_text(json.dumps(report, indent=2) + '\n')
    if report['status'] != 'passed':
        raise ValueError(report['error'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dmg', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arch', choices=('arm64', 'x86_64'), required=True)
    args = parser.parse_args()
    verify(args.dmg.resolve(), args.output, args.arch)
