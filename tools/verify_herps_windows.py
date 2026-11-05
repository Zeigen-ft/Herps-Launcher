#!/usr/bin/env python3
"""Disposable native installer lifecycle and frozen workflows; never gameplay."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_herps_dmg import sha256


def snapshot(root):
    return {str(p.relative_to(root)): sha256(p) for p in root.rglob('*') if p.is_file()}


def verify_early_rejection(log):
    text = Path(log).read_text(encoding='utf-8-sig')
    if ('This installation folder is too long for the bundled files.' not in text
            or 'Installing the file.' in text):
        raise ValueError('Installer did not prove early path rejection before file copying')


def verify(setup, output):
    output.mkdir(parents=True, exist_ok=True)
    output = output.resolve()
    report = {'status': 'failed', 'interactive_verified': False, 'gameplay_verified': False,
              'commands': [], 'platform': platform.platform()}
    def command(args, env=None, allow_failure=False):
        result = subprocess.run(list(map(str, args)), env=env, capture_output=True, text=True, timeout=600)
        report['commands'].append({'argv': list(map(str, args)), 'exit_code': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode and not allow_failure:
            raise ValueError(f'Command failed: {args[0]} ({result.returncode}): {result.stderr}')
        return result.returncode if allow_failure else result.stdout.strip()
    try:
        if platform.system() != 'Windows' or platform.machine().lower() not in ('amd64', 'x86_64'):
            raise ValueError('Native Windows x64 required')
        if os.environ.get('GITHUB_ACTIONS') != 'true':
            raise ValueError('Installer verifier is CI-only; use the manual protocol on personal machines')
        report['setup_sha256'] = sha256(setup)
        powershell = Path(os.environ['SYSTEMROOT']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        shortcuts = [Path(command([powershell, '-NoProfile', '-Command', f"[Environment]::GetFolderPath('{folder}')"])) / suffix
                     for folder, suffix in [('Programs', 'Herps Launcher/Herps Launcher.lnk'),
                                            ('DesktopDirectory', 'Herps Launcher.lnk')]]
        if any(p.exists() for p in shortcuts):
            raise ValueError('Refusing to overwrite preexisting launcher shortcuts')
        with tempfile.TemporaryDirectory(prefix='hwd-', dir=os.environ.get('RUNNER_TEMP')) as temporary:
            root = Path(temporary)
            installed = root / 'Installed Apps With Spaces'
            local = root / 'Local AppData'
            support = local / 'Herspers Minecraft'
            # Preexisting user data predates installation and must survive every stage.
            for name in ('game/saves/Existing/level.dat', 'game/options.txt',
                         'game/shaderpacks/owned.txt', 'game/horizon-mod-data/existing/data.txt',
                         'herps-launcher/targeted-backups/funcraft/existing/owned-backup-marker.txt',
                         'herps-launcher/profiles/existing/saves/Existing/level.dat'):
                p = support / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b'owned preexisting data sentinel')
            settings = support / 'herps-launcher/settings.json'
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps({'installation': '', 'profile': 'existing',
                'profiles': ['default', 'existing'], 'servers': [], 'close_on_play': False,
                'phase5d_preserved_setting': 'owned existing preference'}))
            original = snapshot(support)
            env = dict(os.environ)
            for key in ('HERPS_TEST_PORT_PACK', 'CARGO_HOME', 'RUSTUP_HOME', 'PYTHONPATH', 'PYTHONHOME'):
                env.pop(key, None)
            env.update(LOCALAPPDATA=str(local), APPDATA=str(root / 'Roaming'),
                       HOME=str(root / 'Home'), USERPROFILE=str(root / 'Home'),
                       PATH=str(Path(os.environ['SYSTEMROOT']) / 'System32'),
                       QT_QPA_PLATFORM='offscreen', HERPS_ACCEPTANCE_SUPPORT=str(support))
            for key in ('APPDATA', 'HOME'): Path(env[key]).mkdir(parents=True)
            launcher = installed / 'Herps Launcher/Herps Launcher.exe'
            helper = root / 'install.ps1'
            helper.write_text('param($exe, $destination, $log)\n'
                '$p = Start-Process -FilePath $exe -ArgumentList @(\'/VERYSILENT\', '
                '\'/SUPPRESSMSGBOXES\', \'/NORESTART\', \'/TASKS=desktopicon\', '
                '"/DIR=`\"$destination`\"", "/LOG=`\"$log`\"") -PassThru -Wait\n'
                'exit $p.ExitCode\n', encoding='utf-8')
            def install(stage, destination=installed, reject=False):
                code = command([powershell, '-NoProfile', '-File', helper, setup, destination,
                         output / f'installer-{stage}.log'], allow_failure=reject)
                if reject and (code == 0 or destination.exists()):
                    raise ValueError('Overlong destination was not rejected before copying')
            install('long-path', root / ('Long destination ' + 'x' * 140), reject=True)
            verify_early_rejection(output / 'installer-long-path.log')
            if snapshot(support) != original: raise ValueError('Rejected installation changed existing data')
            report['overlong_destination_rejected_before_copy'] = True
            install('first')
            if not all(p.is_file() for p in shortcuts) or not launcher.is_file():
                raise ValueError('Installed launcher or shortcuts missing')
            for mode, name in [('--smoke-test', 'installed-smoke.json'),
                               ('--native-acceptance', 'installed-workflows.json')]:
                receipt = output / name
                receipt.unlink(missing_ok=True)
                command([launcher, mode, '--require-installation', '--require-port-pack',
                         '--smoke-report', receipt], env)
                data = json.loads(receipt.read_text())
                if data.get('status') != 'passed': raise ValueError(f'Failed receipt: {name}')
                if mode == '--smoke-test' and data.get('pages_opened') != 7:
                    raise ValueError('Seven-page navigation missing')
                if mode == '--native-acceptance' and len(data.get('targeted_backup_cases_verified', [])) != 3:
                    raise ValueError('Delivered candidate did not verify the three FunCraft backup cases')
                if mode == '--native-acceptance' and len(data.get('chainmail_cases_verified', [])) != 3:
                    raise ValueError('Delivered candidate did not verify the three chainmail installation cases')
                report[name] = data
            if any(snapshot(support).get(name) != value for name, value in original.items()
                   if name != str(settings.relative_to(support))):
                raise ValueError('Existing user data changed during installed workflows')
            config = json.loads(settings.read_text())
            if config.get('phase5d_preserved_setting') != 'owned existing preference' or 'existing' not in config['profiles']:
                raise ValueError('Existing profile registration or unknown preference lost')
            report['existing_profile_and_preference_preserved'] = True
            before = snapshot(support)
            # Same-version replacement, then uninstall and reinstall, all against existing data.
            install('replacement')
            if snapshot(support) != before: raise ValueError('Replacement changed user data')
            command([installed / 'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', f'/LOG={output / "uninstall.log"}'])
            if launcher.exists() or any(p.exists() for p in shortcuts):
                raise ValueError('Uninstaller left launcher or shortcuts behind')
            if snapshot(support) != before: raise ValueError('Uninstall changed user data')
            install('reinstall')
            command([launcher, '--smoke-test', '--require-installation', '--require-port-pack',
                     '--smoke-report', output / 'reinstalled-smoke.json'], env)
            if snapshot(support) != before: raise ValueError('Reinstall changed user data')
            command([installed / 'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', f'/LOG={output / "uninstall.log"}'])
            if snapshot(support) != before: raise ValueError('Final uninstall changed user data')
            report['preserved_files'] = before
            report['existing_data_before_install'] = original
        report['status'] = 'passed'
    except Exception as error:
        report['error'] = str(error)
    finally:
        (output / 'windows-lifecycle.json').write_text(json.dumps(report, indent=2) + '\n')
    if report['status'] != 'passed': raise ValueError(report['error'])


if __name__ == '__main__':
    import sys
    # Script invocation imports tools through the repository root.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.setup.resolve(), args.output)
