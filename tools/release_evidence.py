"""Traceable candidate checksums and Python notice inventory; not a security certification."""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def collect_dependencies(output):
    rows = []
    for line in (ROOT / 'herps_launcher/requirements.txt').read_text().splitlines():
        if not line or line.startswith('#'): continue
        name, expected = line.split('==')
        dist = metadata.distribution(name)
        if dist.version != expected: raise ValueError(f'Unpinned installed dependency: {name}')
        notices = []
        for item in dist.files or []:
            if any(word in str(item).lower() for word in ('license', 'copying', 'notice')):
                source = Path(dist.locate_file(item))
                if not source.is_file(): continue
                destination = output / 'python-notices' / name / (digest(source)[:16] + '-' + source.name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                notices.append({'source_member': str(item), 'file': str(destination.relative_to(output)), 'sha256': digest(destination)})
        if name in ('PySide6-Essentials', 'shiboken6'):
            for source in (ROOT / 'licenses/LGPL-3.0.txt', ROOT / 'licenses/Qt-PySide-NOTICE.md', ROOT / 'LICENSE'):
                destination = output / 'python-notices' / name / source.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                notices.append({'source_member': str(source.relative_to(ROOT)),
                                'file': str(destination.relative_to(output)), 'sha256': digest(destination)})
        rows.append({'name': name, 'version': dist.version, 'license_expression': dist.metadata.get('License-Expression'),
                     'license': dist.metadata.get('License'), 'notices': notices})
    (output / 'python-dependencies.json').write_text(json.dumps({'dependencies': rows,
        'scope': 'Pinned Python distributions only; Rust/OS dependencies and vulnerability review separate'}, indent=2) + '\n')


def candidate(directory):
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    paths = sorted(p for p in directory.iterdir() if p.suffix in ('.zip', '.exe', '.dmg'))
    if not paths: raise ValueError('No candidate packages produced')
    rows = [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in paths]
    (directory / 'SHA256SUMS').write_text(''.join(f"{r['sha256']}  {r['file']}\n" for r in rows))
    (directory / 'candidate.json').write_text(json.dumps({'source_commit': head, 'artifacts': rows,
        'requirements_sha256': digest(ROOT / 'herps_launcher/requirements.txt'),
        'upstream_lock_sha256': digest(ROOT / 'upstream.lock.json'),
        'interactive_verified': False, 'gameplay_verified': False,
        'public_release_approved': False, 'reproducibility': 'pinned recipe and recorded hashes; not bit-for-bit reproducible'}, indent=2) + '\n')


if __name__ == '__main__': candidate(Path(sys.argv[1]))
