import importlib.util
import json
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_macos", PROJECT / "tools/package_macos.py")
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="herspers-package-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.binaries = self.root / "binaries"
        self.output = self.root / "output"
        self.source.mkdir()
        self.binaries.mkdir()
        (self.source / "research-lock.json").write_text(json.dumps({"minecraft": {"version": "26.3", "java_major": 25}}))
        for relative in package.PREPARATION_DIRS:
            directory = self.source / relative
            directory.mkdir(parents=True)
            (directory / "source.txt").write_text(relative)
        (self.source / "LICENSE").write_text("upstream license")
        (self.source / "THIRD_PARTY_NOTICES.md").write_text("upstream notices")
        nested_license = self.source / "third_party/winit/LICENSE"
        nested_license.parent.mkdir(parents=True)
        nested_license.write_text("winit license")
        for name in package.BINARIES:
            self.write_binary(name)

    def write_binary(self, name, cpu=package.CPUS["arm64"]):
        path = self.binaries / name
        # Deliberately only a fixture header. Stage tests never run these files.
        path.write_bytes(struct.pack("<8I", 0xFEEDFACF, cpu, 0, 2, 0, 0, 0, 0))
        path.chmod(0o755)

    def stage(self, arch="arm64"):
        return package.assemble(self.source, self.binaries, arch, self.output, stage_only=True)

    def test_stage_contains_sources_notices_and_unverified_metadata_but_no_zip(self):
        private = self.source / ".local/game.jar"
        private.parent.mkdir()
        private.write_bytes(b"private game file")
        (self.source / "tools/unwanted.jar").write_bytes(b"not a source input")
        app, archive = self.stage()
        self.assertIsNone(archive)
        self.assertFalse(list(self.output.glob("*.zip")))
        resources = app / "Contents/Resources"
        self.assertIn("STAGED ONLY", (resources / "BUILD-STATUS.txt").read_text())
        metadata = json.loads((resources / "build-metadata.json").read_text())
        self.assertTrue(metadata["stage_only"])
        self.assertFalse(metadata["macos_runtime_tested"])
        self.assertFalse(metadata["game_resources_included"])
        self.assertFalse(metadata["native_launcher_compiled"])
        self.assertEqual("arm64", metadata["architecture"])
        self.assertTrue((resources / "preparation/mods/horizon/src/test/java/source.txt").is_file())
        self.assertEqual("winit license", (resources / "upstream-notices/third_party/winit/LICENSE").read_text())
        self.assertFalse(list(app.rglob("*.jar")))
        with (app / "Contents/Info.plist").open("rb") as stream:
            info = plistlib.load(stream)
        self.assertEqual("Herspers Minecraft", info["CFBundleName"])
        self.assertTrue((app / "Contents/MacOS" / info["CFBundleExecutable"]).stat().st_mode & 0o111)

    def test_architecture_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected a x86_64"):
            self.stage("x86_64")
        self.assertFalse(self.output.exists())

    def test_intel_stage_records_intel(self):
        for name in package.BINARIES:
            self.write_binary(name, package.CPUS["x86_64"])
        app, _ = self.stage("x86_64")
        data = json.loads((app / "Contents/Resources/build-metadata.json").read_text())
        self.assertEqual("x86_64", data["architecture"])

    def test_missing_binary_and_elf_are_rejected(self):
        binary = self.binaries / "horizon-client"
        binary.unlink()
        with self.assertRaisesRegex(ValueError, "missing regular file"):
            self.stage()
        binary.write_bytes(b"\x7fELF" + bytes(28))
        binary.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "Mach-O"):
            self.stage()

    def test_missing_preparation_sources_are_rejected(self):
        (self.source / "research-lock.json").unlink()
        with self.assertRaisesRegex(ValueError, "research-lock"):
            self.stage()

    def test_wrong_game_pin_is_rejected(self):
        (self.source / "research-lock.json").write_text('{"minecraft": "unexpected"}')
        with self.assertRaisesRegex(ValueError, "pinned Minecraft"):
            self.stage()

    def test_unrelated_metadata_symlink_is_not_copied(self):
        (self.source / "CLAUDE.md").symlink_to("AGENTS.md")
        app, _ = self.stage()
        self.assertFalse(list(app.rglob("CLAUDE.md")))

    def test_external_library_is_rejected(self):
        def fake_run(*command):
            if command[0] == "lipo":
                return "arm64\n"
            return "horizon-client:\n\t/opt/homebrew/lib/libexample.dylib (compatibility version 1.0.0)\n"
        with patch.object(package, "run", side_effect=fake_run):
            with self.assertRaisesRegex(ValueError, "non-system library"):
                package.verify_macos_binary(self.binaries / "horizon-client", "arm64")

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        app = self.output / package.APP_NAME
        app.mkdir()
        sentinel = app / "user-file"
        sentinel.write_text("preserve")
        with self.assertRaisesRegex(ValueError, "already contains"):
            self.stage()
        self.assertEqual("preserve", sentinel.read_text())

    def test_source_symlink_is_rejected(self):
        (self.source / "tools/linked").symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.stage()

    def test_real_packaging_refuses_linux(self):
        with patch.object(package.platform, "system", return_value="Linux"):
            with self.assertRaisesRegex(ValueError, "requires macOS"):
                package.assemble(self.source, self.binaries, "arm64", self.output)

    def test_wrappers_are_valid_bash(self):
        for name in ("launch.command", "prepare.command"):
            subprocess.run(["bash", "-n", str(PROJECT / "packaging" / name)], check=True)

    def test_native_launcher_is_valid_c_with_platform_api_declared(self):
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler unavailable")
        # A declaration-only stub lets Linux parse C without an Apple SDK.
        # This does not link or run the launcher or claim a macOS build.
        header = self.root / "include/mach-o/dyld.h"
        header.parent.mkdir(parents=True)
        header.write_text("#include <stdint.h>\nint _NSGetExecutablePath(char *, uint32_t *);\n")
        subprocess.run([compiler, "-Wall", "-Wextra", "-Werror", "-fsyntax-only",
                        "-I", str(header.parents[1]), str(PROJECT / "packaging/launcher.c")], check=True)


if __name__ == "__main__":
    unittest.main()
