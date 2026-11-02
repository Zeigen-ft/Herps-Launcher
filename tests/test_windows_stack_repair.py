"""Exercise the actual PowerShell repair on inert PE fixtures, never game binaries."""
import os
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from test_package_windows import pe_fixture, package


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts/repair_windows_stack.ps1"
# Exercise Windows PowerShell 5.1 when available, matching the player's command.
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


@unittest.skipUnless(POWERSHELL, "PowerShell is required to exercise Windows stack repair")
class StackRepairTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herspers stack repair ")
        self.addCleanup(temporary.cleanup)
        # macOS exposes its temporary root through /var -> /private/var.
        # Keep normal fixtures physical; link rejection has explicit cases.
        self.root = Path(temporary.name).resolve()
        self.package = self.root / "Herspers Minecraft 雪"
        (self.package / "bin").mkdir(parents=True)
        self.executable = self.package / "bin/horizon-client.exe"
        self.original = pe_fixture(stack_reserve=1024 * 1024)
        self.executable.write_bytes(self.original)
        self.backup = self.executable.with_name(self.executable.name + ".before-stack-fix.bak")
        self.metadata = self.package / "build-metadata.json"
        self.metadata.write_text(json.dumps({"binaries": {
            "horizon-client.exe": {"sha256": hashlib.sha256(self.original).hexdigest()}
        }}))

    def repair(self):
        environment = dict(os.environ)
        if os.name != "nt":
            for name in ("XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME"):
                environment[name] = str(self.root / name.lower())
        return subprocess.run(
            [POWERSHELL, "-NoLogo", "-NoProfile", "-NonInteractive", "-File",
             str(SCRIPT), "-PackagePath", str(self.package)],
            capture_output=True, text=True, timeout=30, env=environment,
        )

    def assert_refused(self, content, message):
        self.executable.write_bytes(content)
        result = self.repair()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)
        self.assertEqual(self.executable.read_bytes(), content)
        self.assertFalse(self.backup.exists())
        self.assertFalse(list(self.executable.parent.glob("*.tmp")))

    def test_only_stack_reserve_changes_and_original_is_backed_up(self):
        # These represent the user's data and must not be touched by a repair.
        saved_world = self.package / "game/saves/world/level.dat"
        saved_world.parent.mkdir(parents=True)
        saved_world.write_bytes(b"keep player data")
        original_metadata = self.metadata.read_bytes()
        result = self.repair()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        fixed = self.executable.read_bytes()
        self.assertEqual(self.backup.read_bytes(), self.original)
        self.assertEqual(len(fixed), len(self.original))
        field = 152 + 72
        self.assertEqual(fixed[:field], self.original[:field])
        self.assertEqual(fixed[field + 8:], self.original[field + 8:])
        report = package.inspect_pe(fixed)
        self.assertEqual(report["stack_reserve_bytes"], 16 * 1024 * 1024)
        self.assertEqual(report["stack_commit_bytes"], 4096)
        self.assertEqual(saved_world.read_bytes(), b"keep player data")
        self.assertEqual(self.metadata.read_bytes(), original_metadata)
        self.assertFalse(list(self.executable.parent.glob("*.tmp")))

    def test_repair_is_idempotent(self):
        first = self.repair()
        self.assertEqual(first.returncode, 0, first.stderr)
        fixed = self.executable.read_bytes()
        timestamp = self.executable.stat().st_mtime_ns
        second = self.repair()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("No change needed", second.stdout)
        self.assertEqual(self.executable.read_bytes(), fixed)
        self.assertEqual(self.executable.stat().st_mtime_ns, timestamp)
        self.assertEqual(self.backup.read_bytes(), self.original)

    def test_larger_existing_reserve_is_not_lowered(self):
        original = pe_fixture(stack_reserve=32 * 1024 * 1024)
        self.executable.write_bytes(original)
        result = self.repair()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.executable.read_bytes(), original)
        self.assertFalse(self.backup.exists())

    def test_existing_backup_is_never_overwritten(self):
        self.backup.write_bytes(b"existing user backup")
        result = self.repair()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Backup already exists", result.stderr)
        self.assertEqual(self.executable.read_bytes(), self.original)
        self.assertEqual(self.backup.read_bytes(), b"existing user backup")

    def test_wrong_architecture_or_dll_is_refused(self):
        for kwargs in ({"machine": 0xAA64}, {"dll": True}):
            with self.subTest(**kwargs):
                self.assert_refused(pe_fixture(**kwargs), "Expected an x64 executable")

    def test_truncated_and_non_pe_files_are_refused(self):
        for content in (b"not an exe", self.original[:170]):
            with self.subTest(size=len(content)):
                self.assert_refused(content, "Stack repair stopped")

    def test_invalid_header_offsets_and_directory_counts_are_refused(self):
        for offset, value, message in ((60, 0xFFFFFF00, "Invalid PE header"),
                                       (152 + 108, 1000, "Invalid PE directory count")):
            content = bytearray(self.original)
            struct.pack_into("<I", content, offset, value)
            with self.subTest(offset=offset):
                self.assert_refused(bytes(content), message)

    def test_signed_executable_is_refused(self):
        content = bytearray(self.original)
        struct.pack_into("<II", content, 152 + 112 + 4 * 8, 900, 100)
        self.assert_refused(bytes(content), "executable is signed")

    def test_invalid_stack_values_are_refused(self):
        for reserve, commit in ((0, 0), (1024, 2048), (1024, 0)):
            with self.subTest(reserve=reserve, commit=commit):
                self.assert_refused(pe_fixture(stack_reserve=reserve, stack_commit=commit), "Invalid stack")

    def test_modified_executable_is_refused_without_changing_expected_checksum(self):
        modified = bytearray(self.original)
        modified[-1] = 1
        metadata = self.metadata.read_bytes()
        self.assert_refused(bytes(modified), "checksum does not match")
        self.assertEqual(self.metadata.read_bytes(), metadata)

    def test_original_package_metadata_is_required(self):
        self.metadata.unlink()
        self.assert_refused(self.original, "build-metadata.json")

    def test_linked_executable_is_refused(self):
        real = self.root / "other.exe"
        real.write_bytes(self.original)
        self.executable.unlink()
        try:
            self.executable.symlink_to(real)
        except OSError:
            self.skipTest("Creating symlinks is not permitted on this machine")
        result = self.repair()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Links/reparse points", result.stderr)
        self.assertEqual(real.read_bytes(), self.original)
        self.assertFalse(self.backup.exists())


if __name__ == "__main__":
    unittest.main()
