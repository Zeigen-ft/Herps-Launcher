"""Resolve only the owned Inno uninstall entry; never execute fixture files."""
from pathlib import Path
import tempfile
import unittest

from tools.verify_herps_windows import installed_uninstaller


class UninstallerResolutionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='owned-inno-log-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.installed = self.root / 'Installed Apps With Spaces'
        self.installed.mkdir()
        self.log = self.root / 'install.log'

    def entry(self, name):
        path = self.installed / name
        path.write_bytes(b'owned passive uninstaller fixture; not executable')
        self.log.write_text(f'2026-11-08 03:52:29.037   Dest filename: {path}\n', encoding='utf-8-sig')
        return path

    def test_reinstall_selects_001_even_when_old_000_still_exists(self):
        (self.installed / 'unins000.exe').write_bytes(b'old passive fixture')
        actual = self.entry('unins001.exe')
        self.assertEqual(installed_uninstaller(self.installed, self.log), actual)

    def test_initial_install_selects_its_000_entry(self):
        actual = self.entry('unins000.exe')
        self.assertEqual(installed_uninstaller(self.installed, self.log), actual)

    def test_missing_file_is_refused_before_execution(self):
        path = self.entry('unins001.exe'); path.unlink()
        with self.assertRaisesRegex(ValueError, 'missing'): installed_uninstaller(self.installed, self.log)

    def test_log_cannot_select_uninstaller_outside_owned_installation(self):
        outside = self.root / 'unins001.exe'; outside.write_bytes(b'outside passive fixture')
        self.log.write_text(f'Dest filename: {outside}\n', encoding='utf-8-sig')
        with self.assertRaisesRegex(ValueError, 'outside'): installed_uninstaller(self.installed, self.log)

    def test_ambiguous_or_absent_uninstall_entry_is_refused(self):
        path = self.entry('unins000.exe'); other = self.installed / 'unins001.exe'; other.write_bytes(b'other')
        for text in ['', f'Dest filename: {path}\nDest filename: {other}\n']:
            self.log.write_text(text, encoding='utf-8-sig')
            with self.assertRaisesRegex(ValueError, 'exactly one'): installed_uninstaller(self.installed, self.log)

    def test_filename_like_a_command_cannot_be_executed(self):
        path = self.entry('unins000.exe')
        self.log.write_text(f'Dest filename: {path} /SILENT\n', encoding='utf-8-sig')
        with self.assertRaisesRegex(ValueError, 'exactly one'): installed_uninstaller(self.installed, self.log)
