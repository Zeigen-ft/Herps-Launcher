"""Compute UTF-16 destination path budgets for Inno's legacy-path installer."""
import json
from pathlib import Path
import sys


def payload_limits(root):
    limits = {'file_chars': 0, 'directory_chars': 0}
    for path in Path(root).rglob('*'):
        if path.is_symlink(): raise ValueError('Linked Windows installer payload is not supported')
        relative = str(path.relative_to(root)).replace('/', '\\')
        count = len(relative.encode('utf-16-le')) // 2
        key = 'directory_chars' if path.is_dir() else 'file_chars'
        limits[key] = max(limits[key], count)
    if not limits['file_chars']: raise ValueError('Installer payload is empty')
    return limits


if __name__ == '__main__': print(json.dumps(payload_limits(Path(sys.argv[1]))))
