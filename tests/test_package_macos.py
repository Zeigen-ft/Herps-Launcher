import importlib.util
import hashlib
import json
import os
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
        self.project = self.root / "project"
        (self.project / "docs").mkdir(parents=True)
        (self.project / "docs/SHADERS.md").write_text("# Shader compatibility\nUse Shader Packs.\n")
        (self.project / "packaging").mkdir()
        for name in ("launch.command", "prepare.command", "launcher.c"):
            shutil.copy2(PROJECT / "packaging" / name, self.project / "packaging" / name)
        lock = {"commit": "a" * 40}
        (self.project / "upstream.lock.json").write_text(json.dumps(lock))
        patch_dir = self.project / "patches/engine"
        patch_dir.mkdir(parents=True)
        patch_bytes = b"--- /dev/null\n+++ b/shader-fixture.txt\n@@ -0,0 +1 @@\n+patched engine\n"
        (patch_dir / "fixture.patch").write_bytes(patch_bytes)
        (self.source / "shader-fixture.txt").write_bytes(b"patched engine\n")
        manifest = {"upstream_commit": lock["commit"], "files": [{
            "path": "shader-fixture.txt", "before_sha256": None,
            "after_sha256": hashlib.sha256(b"patched engine\n").hexdigest(),
            "patch": "engine/fixture.patch"}]}
        manifest_bytes = json.dumps(manifest).encode()
        (self.project / "patches/upstream.json").write_bytes(manifest_bytes)
        self.patch_hash = hashlib.sha256(manifest_bytes + len(patch_bytes).to_bytes(8, "big") + patch_bytes).hexdigest()
        self.stamp = {"upstream": lock, "patches_sha256": self.patch_hash, "tree_sha256": "b" * 64}
        (self.source / ".herspers-prepared.json").write_text(json.dumps(self.stamp))
        self.project_patch = patch.object(package, "PROJECT", self.project)
        self.project_patch.start()
        self.addCleanup(self.project_patch.stop)

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
        self.assertEqual("0.2.3", metadata["product_version"])
        self.assertTrue(metadata["engine_source"]["modified"])
        self.assertEqual(self.patch_hash, metadata["engine_source"]["patches_sha256"])
        self.assertIn("Shader Packs", (resources / "SHADERS.txt").read_text())
        provenance = json.loads((resources / "engine-patches.json").read_text())
        self.assertEqual(self.stamp, provenance["preparation"])
        self.assertTrue((resources / "preparation/mods/horizon/src/test/java/source.txt").is_file())
        self.assertEqual("winit license", (resources / "upstream-notices/third_party/winit/LICENSE").read_text())
        self.assertFalse(list(app.rglob("*.jar")))
        with (app / "Contents/Info.plist").open("rb") as stream:
            info = plistlib.load(stream)
        self.assertEqual("Herspers Minecraft", info["CFBundleName"])
        self.assertEqual("0.2.3", info["CFBundleShortVersionString"])
        entrypoint = app / "Contents/MacOS" / info["CFBundleExecutable"]
        self.assertTrue(entrypoint.is_file())
        self.assertEqual(entrypoint.read_bytes()[:4], b"\xcf\xfa\xed\xfe")
        if os.name != "nt":
            # Windows file modes do not represent Unix executable permissions.
            self.assertTrue(entrypoint.stat().st_mode & 0o111)

    def test_architecture_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected a x86_64"):
            self.stage("x86_64")
        self.assertFalse(self.output.exists())

    def test_prepared_source_must_match_current_patch_set(self):
        (self.project / "patches/engine/fixture.patch").write_text("different patch bytes")
        with self.assertRaisesRegex(ValueError, "current patch manifest"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_patch_manifest_cannot_name_files_outside_source(self):
        path = self.project / "patches/upstream.json"
        manifest = json.loads(path.read_text())
        manifest["files"][0]["path"] = "../outside.txt"
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            self.stage()
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
        if os.name == "nt":
            # System32/bash.exe is a WSL launcher, which need not have a distro.
            # Use Git for Windows' actual Bash interpreter on this platform.
            git = shutil.which("git")
            candidates = [] if git is None else [
                Path(git).parent.parent / "bin/bash.exe",
                Path(git).parent.parent / "usr/bin/bash.exe",
            ]
            bash = next((str(path) for path in candidates if path.is_file()), None)
        else:
            bash = shutil.which("bash")
        if bash is None:
            self.skipTest("Bash interpreter unavailable on this host")
        for name in ("launch.command", "prepare.command"):
            subprocess.run([bash, "-n", str(PROJECT / "packaging" / name)], check=True)

    def test_native_launcher_is_valid_c_with_platform_api_declared(self):
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler unavailable")
        # Declaration-only stubs let non-Mac hosts parse C without an Apple SDK.
        # This does not link or run the launcher or claim a macOS build.
        header = self.root / "include/mach-o/dyld.h"
        header.parent.mkdir(parents=True)
        header.write_text("#include <stdint.h>\nint _NSGetExecutablePath(char *, uint32_t *);\n"
                          "#ifdef _WIN32\nchar *realpath(const char *, char *);\n#endif\n")
        subprocess.run([compiler, "-Wall", "-Wextra", "-Werror", "-fsyntax-only",
                        "-I", str(header.parents[1]), str(PROJECT / "packaging/launcher.c")], check=True)


if __name__ == "__main__":
    unittest.main()
