import importlib.util
import json
from pathlib import Path
import platform
import struct
import tempfile
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_windows", PROJECT / "tools/package_windows.py")
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


def pe_fixture(import_name="KERNEL32.dll", delay_name=None, machine=0x8664, dll=False,
               stack_reserve=16 * 1024 * 1024, stack_commit=4096):
    """Non-executable PE fixture with one file-backed section and import tables."""
    data = bytearray(1024)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 132, machine, 1, 0, 0, 0, 240, 0x2002 if dll else 2)
    optional = 152
    struct.pack_into("<H", data, optional, 0x20B)
    struct.pack_into("<Q", data, optional + 24, 0x140000000)
    struct.pack_into("<I", data, optional + 60, 512)
    struct.pack_into("<QQ", data, optional + 72, stack_reserve, stack_commit)
    struct.pack_into("<I", data, optional + 108, 16)
    section = optional + 240
    data[section:section + 8] = b".rdata\0\0"
    struct.pack_into("<IIII", data, section + 8, 512, 4096, 512, 512)
    if import_name:
        struct.pack_into("<II", data, optional + 112 + 8, 4096, 40)
        struct.pack_into("<I", data, 512 + 12, 4096 + 64)
        name = import_name.encode() + b"\0"
        data[576:576 + len(name)] = name
    if delay_name:
        struct.pack_into("<II", data, optional + 112 + 13 * 8, 4096 + 128, 64)
        struct.pack_into("<II", data, 640, 1, 4096 + 256)
        name = delay_name.encode() + b"\0"
        data[768:768 + len(name)] = name
    return bytes(data)


class PeTests(unittest.TestCase):
    def test_architecture_normal_and_delay_imports(self):
        result = package.inspect_pe(pe_fixture(delay_name="D3D12.dll"))
        self.assertEqual(result["architecture"], "x86_64")
        self.assertEqual(result["imports"], ["d3d12.dll", "kernel32.dll"])
        self.assertEqual(result["stack_reserve_bytes"], 16 * 1024 * 1024)
        self.assertEqual(result["stack_commit_bytes"], 4096)

    def test_system_api_sets_are_allowed(self):
        result = package.inspect_pe(pe_fixture("api-ms-win-core-synch-l1-2-0.dll"))
        self.assertEqual(len(result["imports"]), 1)

    def test_rejects_foreign_dlls_in_normal_or_delayed_imports(self):
        for kwargs in ({"import_name": "VCRUNTIME140.dll"}, {"delay_name": "vulkan-1.dll"}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, "non-system DLL"):
                package.inspect_pe(pe_fixture(**kwargs))

    def test_rejects_non_windows_wrong_cpu_and_dll(self):
        for data in (b"\x7fELF" + bytes(1020), pe_fixture(machine=0xAA64), pe_fixture(dll=True)):
            with self.subTest(prefix=data[:4]), self.assertRaises(ValueError):
                package.inspect_pe(data)

    def test_rejects_truncated_headers_and_out_of_range_import_name(self):
        with self.assertRaises(ValueError):
            package.inspect_pe(pe_fixture()[:450])
        data = bytearray(pe_fixture())
        struct.pack_into("<I", data, 512 + 12, 0x10000000)
        with self.assertRaisesRegex(ValueError, "RVA"):
            package.inspect_pe(bytes(data))

    def test_rejects_unterminated_import_descriptors(self):
        data = bytearray(pe_fixture())
        struct.pack_into("<II", data, 152 + 112 + 8, 4096, 20)
        with self.assertRaisesRegex(ValueError, "unterminated"):
            package.inspect_pe(bytes(data))

    def test_rejects_path_in_import_name(self):
        with self.assertRaisesRegex(ValueError, "invalid PE DLL name"):
            package.inspect_pe(pe_fixture("C:\\bad.dll"))


class WindowsPackagingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herspers-windows-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source, self.binaries, self.output = [self.root / name for name in ("source", "binaries", "output")]
        self.source.mkdir()
        self.binaries.mkdir()
        (self.source / "research-lock.json").write_text(json.dumps({"minecraft": {"version": "26.3", "java_major": 25}}))
        for relative in package._common.PREPARATION_DIRS:
            path = self.source / relative / "input.txt"
            path.parent.mkdir(parents=True)
            path.write_text(relative)
        (self.source / "LICENSE").write_text("upstream MIT license")
        (self.source / "THIRD_PARTY_NOTICES.md").write_text("upstream notices")
        for name in package.BINARIES:
            (self.binaries / name).write_bytes(pe_fixture())
        self.launcher = self.root / package.LAUNCHER
        self.launcher.write_bytes(pe_fixture())
        self.project = self.root / "project"
        (self.project / "docs").mkdir(parents=True)
        (self.project / "docs/INSTALL-WINDOWS.md").write_text("# Install\nRun --setup first.\n")
        (self.project / "docs/HOSTING-TAILSCALE.md").write_text("# Private Tailscale hosting\nRun Host-Tailscale.cmd.\n")
        helpers = self.project / "packaging/windows"
        helpers.mkdir(parents=True)
        for name in package.HELPERS:
            (helpers / name).write_text(f"@echo off\nrem {name}\n")
        (self.project / "LICENSE").write_text("project GPLv3")
        (self.project / "upstream.lock.json").write_text("{}")
        self.project_patch = patch.object(package, "PROJECT", self.project)
        self.project_patch.start()
        self.addCleanup(self.project_patch.stop)

    def stage(self):
        return package.assemble(self.source, self.binaries, self.launcher, self.output, stage_only=True)

    def test_stage_layout_notices_instructions_no_assets_or_zip(self):
        extra = self.source / "tools/secret.jar"
        extra.write_bytes(b"game file must not be bundled")
        root, archive = self.stage()
        self.assertIsNone(archive)
        self.assertFalse(list(self.output.glob("*.zip")))
        self.assertEqual(root.name, "Herspers-Minecraft")
        self.assertTrue((root / package.LAUNCHER).is_file())
        self.assertTrue((root / "bin/horizon-client.exe").is_file())
        self.assertTrue((root / "preparation/mods/horizon/src/test/java/input.txt").is_file())
        self.assertEqual((root / "LICENSE").read_text(), "project GPLv3")
        self.assertEqual((root / "licenses/upstream/LICENSE").read_text(), "upstream MIT license")
        self.assertIn("--setup", (root / "INSTALL-WINDOWS.txt").read_text())
        for helper in package.HELPERS:
            self.assertIn(helper, (root / helper).read_text())
        self.assertFalse(list(root.rglob("*.jar")))
        self.assertEqual(len((root / "preparation-id.txt").read_text().strip()), 64)
        metadata = json.loads((root / "build-metadata.json").read_text())
        self.assertTrue(metadata["stage_only"])
        self.assertFalse(metadata["windows_runtime_tested"])
        self.assertFalse(metadata["game_resources_included"])
        self.assertEqual(metadata["product_version"], "0.2.2")
        self.assertIn("STAGED ONLY", (root / "BUILD-STATUS.txt").read_text())

    def test_missing_binary_fails_before_creating_output(self):
        (self.binaries / "horizon-client.exe").unlink()
        with self.assertRaisesRegex(ValueError, "missing regular file"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_small_client_stack_is_rejected_before_creating_output(self):
        (self.binaries / "horizon-client.exe").write_bytes(pe_fixture(stack_reserve=1024 * 1024))
        with self.assertRaisesRegex(ValueError, "16 MiB main-thread stack"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_smaller_stacks_on_other_executables_are_allowed_and_recorded(self):
        for name in ("horizon-ctl.exe", "horizon-prepare.exe"):
            (self.binaries / name).write_bytes(pe_fixture(stack_reserve=1024 * 1024))
        self.launcher.write_bytes(pe_fixture(stack_reserve=1024 * 1024))
        root, _ = self.stage()
        metadata = json.loads((root / "build-metadata.json").read_text())
        self.assertEqual(metadata["binaries"]["horizon-client.exe"]["stack_reserve_bytes"], 16 * 1024 * 1024)
        self.assertEqual(metadata["binaries"][package.LAUNCHER]["stack_reserve_bytes"], 1024 * 1024)

    def test_preserves_existing_output(self):
        root, _ = self.stage()
        (root / "keep-me.txt").write_text("preserve")
        with self.assertRaisesRegex(ValueError, "already contains"):
            self.stage()
        self.assertEqual((root / "keep-me.txt").read_text(), "preserve")

    def test_source_output_overlap_is_refused(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            package.assemble(self.source, self.binaries, self.launcher, self.source / "dist", True)

    def test_native_packaging_requires_windows(self):
        with patch.object(package.platform, "system", return_value="Linux"):
            with self.assertRaisesRegex(ValueError, "requires Windows"):
                package.assemble(self.source, self.binaries, self.launcher, self.output)

    def test_missing_installation_guide_or_helper_fails_before_output(self):
        guide = self.project / "docs/INSTALL-WINDOWS.md"
        original = guide.read_text()
        guide.unlink()
        with self.assertRaisesRegex(ValueError, "missing regular file"):
            self.stage()
        guide.write_text(original)
        (self.project / "packaging/windows/Setup.cmd").unlink()
        with self.assertRaisesRegex(ValueError, "missing regular file"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_real_archive_layout_with_os_guard_mocked_does_not_run_fixtures(self):
        with patch.object(package.platform, "system", return_value="Windows"):
            root, archive = package.assemble(self.source, self.binaries, self.launcher, self.output)
        from zipfile import ZipFile
        with ZipFile(archive) as zipped:
            self.assertIsNone(zipped.testzip())
            self.assertIn("Herspers-Minecraft/Herspers-Minecraft.exe", zipped.namelist())
            self.assertIn("Herspers-Minecraft/INSTALL-WINDOWS.txt", zipped.namelist())
            self.assertIn("Herspers-Minecraft/Setup.cmd", zipped.namelist())
            self.assertIn("Herspers-Minecraft/Play.cmd", zipped.namelist())
            self.assertIn("Herspers-Minecraft/Host-Tailscale.cmd", zipped.namelist())
            self.assertIn("Herspers-Minecraft/Join-Tailscale.cmd", zipped.namelist())
            self.assertIn("Herspers-Minecraft/HOSTING-TAILSCALE.txt", zipped.namelist())


if __name__ == "__main__":
    unittest.main()
