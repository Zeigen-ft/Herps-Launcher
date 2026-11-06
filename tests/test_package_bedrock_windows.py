"""Validate Bedrock packaging without running synthetic Windows binaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "package_bedrock_windows", PROJECT / "tools/package_bedrock_windows.py")
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


def pe_fixture(import_name="KERNEL32.dll", delay_name=None, machine=0x8664, dll=False):
    """Minimal file-backed PE headers; these are never executed."""
    data = bytearray(1024)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 132, machine, 1, 0, 0, 0, 240, 0x2002 if dll else 2)
    optional = 152
    struct.pack_into("<H", data, optional, 0x20B)
    struct.pack_into("<Q", data, optional + 24, 0x140000000)
    struct.pack_into("<I", data, optional + 60, 512)
    struct.pack_into("<I", data, optional + 108, 16)
    section = optional + 240
    data[section:section + 8] = b".rdata\0\0"
    struct.pack_into("<IIII", data, section + 8, 512, 4096, 512, 512)
    if import_name:
        struct.pack_into("<II", data, optional + 120, 4096, 40)
        struct.pack_into("<I", data, 524, 4096 + 64)
        name = import_name.encode("ascii") + b"\0"
        data[576:576 + len(name)] = name
    if delay_name:
        struct.pack_into("<II", data, optional + 112 + 13 * 8, 4096 + 128, 64)
        struct.pack_into("<II", data, 640, 1, 4096 + 256)
        name = delay_name.encode("ascii") + b"\0"
        data[768:768 + len(name)] = name
    return bytes(data)


class BedrockPeTests(unittest.TestCase):
    def test_system_and_bundled_imports_including_delay_imports(self):
        result = package.inspect_pe(pe_fixture("dxcompiler.dll", "D3D12.dll"),
                                    bundled_dlls={"dxcompiler.dll"})
        self.assertEqual(result["architecture"], "x86_64")
        self.assertEqual(result["imports"], ["d3d12.dll", "dxcompiler.dll"])
        self.assertEqual(package.inspect_pe(pe_fixture(dll=True), allow_dll=True)["architecture"], "x86_64")

    def test_unbundled_library_is_refused(self):
        for data in [pe_fixture("vcruntime140d.dll"), pe_fixture("vcruntime141.dll"), pe_fixture(delay_name="missing.dll")]:
            with self.subTest(), self.assertRaises(ValueError):
                package.inspect_pe(data)

    def test_visual_cpp_runtime_is_an_explicit_prerequisite_not_a_system_dll(self):
        result = package.inspect_pe(pe_fixture("VCRUNTIME140.dll", "msvcp140_2.dll"))
        self.assertEqual(result["vc_runtime_dlls"], ["msvcp140_2.dll", "vcruntime140.dll"])
        self.assertNotIn("vcruntime140.dll", package.SYSTEM_DLLS)

    def test_wrong_architecture_dll_and_malformed_headers_are_refused(self):
        for data in [pe_fixture(machine=0xAA64), pe_fixture(dll=True), b"\x7fELF" + bytes(1020), pe_fixture()[:300]]:
            with self.subTest(), self.assertRaises(ValueError):
                package.inspect_pe(data)

    def test_import_paths_and_unmapped_names_are_refused(self):
        with self.assertRaises(ValueError):
            package.inspect_pe(pe_fixture("C:\\evil.dll"), bundled_dlls={"C:\\evil.dll"})
        data = bytearray(pe_fixture())
        struct.pack_into("<I", data, 524, 0xFFFFFF)
        with self.assertRaises(ValueError):
            package.inspect_pe(bytes(data))


class BedrockPackagingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herspers-bedrock-package-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source, self.engine, self.output, self.project = [
            self.root / p for p in ("source", "engine", "output", "project")]
        self.source.mkdir()
        self.engine.mkdir()
        self.project.mkdir()
        self.runtime = ("cinnabar", "cinnabar-updater", "bedrock-core", "bedrock-local-server", "cinnabar-cxb")
        self.source_file("Cargo.toml", b'[workspace.package]\nversion = "0.1.31"\n')
        self.source_file("LICENSE", b"# PolyForm Noncommercial License 1.0.0\nPersonal use only.\nPreserve the wording.\n")
        self.source_file("THIRD_PARTY_NOTICES.md", b"# Third-party notices\nPreserve each attribution.\n")
        self.source_file("assets/bedrock-target.json", json.dumps({"game_version": "1.26.60", "wire_protocol": 2225}).encode())
        self.source_file("packaging/common/runtime-binaries.txt", "\n".join(f"{name} package ENV" for name in self.runtime).encode())
        self.source_file("assets/vanilla-source.json", json.dumps({
            "schema": 1, "tag": "v1.26.60.30-preview", "artifact_policy": "local-only",
            "url": "https://github.com/Mojang/bedrock-samples/releases/download/test/resources.zip",
            "sha256": "a" * 64, "archive": "resources.zip", "cache_dir": ".local/vanilla",
        }).encode())
        self.source_file("packaging/common/prep-kit-files.txt", b"assets/vanilla-source.json\n")
        font = b"test\nfont\n"
        self.source_file("assets/fonts/Example.ttf", font)
        self.source_file("assets/cinnangles-sans-source.json", json.dumps({
            "font_file": "Example.ttf", "font_sha256": hashlib.sha256(font).hexdigest(), "font_size_bytes": len(font),
        }).encode())
        self.source_file("assets/licenses/Example-LICENSE.txt", b"third-party license\nPreserve this line.\n")
        self.source_file("crates/assets/data/block-physics-v2225.bin", b"physics")
        dll = pe_fixture(dll=True)
        self.source_file("packaging/windows/dxc.json", json.dumps({
            "library": "dxcompiler.dll", "library_sha256": hashlib.sha256(dll).hexdigest(),
        }).encode())
        for name in self.runtime:
            self.engine_file(name + ".exe", pe_fixture("dxcompiler.dll" if name == "cinnabar" else "KERNEL32.dll"))
        self.engine_file("dxcompiler.dll", dll)
        self.engine_file("resources/prep-kit/bin/assetc.exe", pe_fixture())
        self.copy_source("LICENSE", "resources/licenses/Cinnabar-LICENSE.md")
        self.copy_source("THIRD_PARTY_NOTICES.md", "resources/assets/THIRD_PARTY_NOTICES.md")
        self.copy_source("crates/assets/data/block-physics-v2225.bin", "resources/assets/block-physics-v2225.bin")
        self.copy_source("assets/fonts/Example.ttf", "resources/fonts/Example.ttf")
        self.copy_source("assets/licenses/Example-LICENSE.txt", "resources/licenses/Example-LICENSE.txt")
        self.copy_source("assets/vanilla-source.json", "resources/prep-kit/assets/vanilla-source.json")
        self.launcher = self.root / "Herspers-Bedrock.exe"
        self.launcher.write_bytes(pe_fixture())
        (self.project / "LICENSE").write_text("Project GPLv3 license\n")
        (self.project / "docs").mkdir()
        (self.project / "docs/INSTALL-BEDROCK-WINDOWS.md").write_text("# Install\nDownload resources inside the app.\n")
        (self.project / "docs/BEDROCK-LICENSES.md").write_text(
            "# Component licenses\nHerspers launcher: GPLv3.\n"
            "Cinnabar engine: PolyForm Noncommercial 1.0.0; not relicensed as GPLv3.\n")
        self.project_patch = patch.object(package, "PROJECT", self.project)
        self.project_patch.start()
        self.addCleanup(self.project_patch.stop)

    def source_file(self, relative, data):
        target = self.source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def engine_file(self, relative, data):
        target = self.engine / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def copy_source(self, relative, target):
        self.engine_file(target, (self.source / relative).read_bytes())

    def stage(self):
        return package.assemble(self.engine, self.launcher, self.source, self.output, stage_only=True)

    def test_exact_payload_and_hashes_are_retained(self):
        report = package.inspect_engine(self.engine, self.source)
        expected = {str(p.relative_to(self.engine)).replace("\\", "/") for p in self.engine.rglob("*") if p.is_file()}
        self.assertEqual(package.expected_payload(self.source), expected)
        self.assertEqual(set(report["files"]), expected)
        for relative, info in report["files"].items():
            self.assertEqual(info["sha256"], hashlib.sha256((self.engine / relative).read_bytes()).hexdigest())

    def test_actual_vc_prerequisites_are_recorded_per_image_and_in_manifests(self):
        self.engine_file("cinnabar.exe", pe_fixture("vcruntime140.dll", "msvcp140.dll"))
        report = package.inspect_engine(self.engine, self.source)
        expected = ["msvcp140.dll", "vcruntime140.dll"]
        self.assertEqual(report["required_vc_runtime_dlls"], expected)
        self.assertEqual(report["files"]["cinnabar.exe"]["pe"]["vc_runtime_dlls"], expected)
        folder, _ = self.stage()
        for filename in ("bedrock-client.json", "build-metadata.json"):
            self.assertEqual(json.loads((folder / filename).read_text())["required_vc_runtime_dlls"], expected)

    def test_independent_launcher_must_not_require_visual_cpp_installation(self):
        self.launcher.write_bytes(pe_fixture("vcruntime140.dll"))
        with self.assertRaisesRegex(ValueError, "launcher must link"):
            self.stage()

    def test_content_failures_include_filenames_and_are_aggregated(self):
        path = self.engine / "resources/prep-kit/assets/vanilla-source.json"
        path.write_bytes(path.read_bytes() + b"tampered")
        self.engine_file("cinnabar.exe", pe_fixture("unknown.dll"))
        with self.assertRaises(ValueError) as caught:
            self.stage()
        self.assertIn("resources/prep-kit/assets/vanilla-source.json", str(caught.exception))
        self.assertIn("cinnabar.exe", str(caught.exception))
        self.assertIn("unknown.dll", str(caught.exception))

    def test_stage_preserves_separate_licenses_and_emits_no_zip(self):
        folder, archive = self.stage()
        self.assertIsNone(archive)
        self.assertFalse(list(self.output.glob("*.zip")))
        self.assertTrue((folder / "Herspers-Bedrock.exe").is_file())
        self.assertTrue((folder / "INSTALL-BEDROCK-WINDOWS.txt").is_file())
        component_licenses = (folder / "BEDROCK-LICENSES.txt").read_text()
        self.assertIn("Herspers launcher: GPLv3", component_licenses)
        self.assertIn("Cinnabar engine: PolyForm Noncommercial 1.0.0", component_licenses)
        self.assertIn("not relicensed as GPLv3", component_licenses)
        manifest = json.loads((folder / "bedrock-client.json").read_text())
        self.assertEqual(manifest["product_version"], "0.3.0")
        self.assertEqual(manifest["engine_version"], "0.1.31")
        self.assertEqual(manifest["bedrock_version"], "1.26.60")
        self.assertEqual(manifest["wire_protocol"], 2225)
        self.assertTrue(manifest["in_app_resource_downloads"])
        self.assertFalse(manifest["game_assets_included"])
        self.assertIn("engine/cinnabar.exe", manifest["files"])
        for relative, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((folder / relative).read_bytes()).hexdigest(), digest)
        self.assertIn("GPLv3", (folder / "LICENSE").read_text())
        self.assertIn("PolyForm", (folder / "licenses/cinnabar/LICENSE").read_text())

    def test_missing_or_extra_payload_is_rejected_before_output(self):
        binary = self.engine / "bedrock-core.exe"
        original = binary.read_bytes()
        binary.unlink()
        with self.assertRaises(ValueError):
            self.stage()
        binary.write_bytes(original)
        self.engine_file("resources/assets/vanilla-v2225.mcbea", b"unapproved generated game data")
        with self.assertRaises(ValueError):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_source_backed_resources_and_dxc_hash_cannot_be_tampered(self):
        for relative in ["resources/fonts/Example.ttf", "resources/prep-kit/assets/vanilla-source.json", "dxcompiler.dll"]:
            with self.subTest(relative=relative):
                path = self.engine / relative
                saved = path.read_bytes()
                path.write_bytes(saved + b"tampered")
                with self.assertRaises(ValueError):
                    package.inspect_engine(self.engine, self.source)
                path.write_bytes(saved)

    def test_only_observed_notice_paths_accept_deterministic_windows_crlf(self):
        self.assertEqual(len(package.WINDOWS_CRLF_SOURCE_PATHS), 18)
        for relative in package.WINDOWS_CRLF_SOURCE_PATHS:
            with self.subTest(relative=relative):
                if relative == "resources/licenses/Cinnabar-LICENSE.md":
                    source = self.source / "LICENSE"
                elif relative == "resources/assets/THIRD_PARTY_NOTICES.md":
                    source = self.source / "THIRD_PARTY_NOTICES.md"
                else:
                    source = self.source / "assets/licenses" / Path(relative).name
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.write_bytes(b"Required attribution.\nSecond unchanged line.\n")
                payload = self.engine / relative
                payload.parent.mkdir(parents=True, exist_ok=True)
                raw_source = source.read_bytes()
                raw_payload = raw_source.replace(b"\n", b"\r\n")
                payload.write_bytes(raw_payload)
                item = package.inspect_engine(self.engine, self.source)["files"][relative]
                self.assertEqual(item["source_comparison"], {
                    "source_sha256": hashlib.sha256(raw_source).hexdigest(), "variant": "windows_crlf"})
                self.assertEqual(item["sha256"], hashlib.sha256(raw_payload).hexdigest())

    def test_notice_wording_spacing_bare_cr_and_mixed_endings_are_rejected(self):
        relative = "resources/licenses/Cinnabar-LICENSE.md"
        source = (self.source / "LICENSE").read_bytes()
        crlf = source.replace(b"\n", b"\r\n")
        for changed in [
            crlf.replace(b"Personal", b"Commercial"),
            crlf.replace(b"use only", b"use  only"),
            crlf.replace(b"\r\n", b"\r", 1),
            source.replace(b"\n", b"\r\n", 1),
        ]:
            with self.subTest(changed=changed):
                (self.engine / relative).write_bytes(changed)
                with self.assertRaises(ValueError):
                    package.inspect_engine(self.engine, self.source)
        bare_cr_source = b"First\rBare carriage return.\nLast line.\n"
        (self.source / "LICENSE").write_bytes(bare_cr_source)
        (self.engine / relative).write_bytes(bare_cr_source.replace(b"\n", b"\r\n"))
        with self.assertRaises(ValueError):
            package.inspect_engine(self.engine, self.source)

    def test_binary_and_unobserved_license_paths_do_not_accept_crlf_variants(self):
        self.assertNotIn("resources/licenses/Monocraft-OFL-1.1.txt", package.WINDOWS_CRLF_SOURCE_PATHS)
        for relative in ["resources/fonts/Example.ttf", "resources/licenses/Example-LICENSE.txt"]:
            with self.subTest(relative=relative):
                self.assertNotIn(relative, package.WINDOWS_CRLF_SOURCE_PATHS)
                path = self.engine / relative
                original = path.read_bytes()
                path.write_bytes(original.replace(b"\n", b"\r\n"))
                with self.assertRaises(ValueError):
                    package.inspect_engine(self.engine, self.source)
                path.write_bytes(original)

    def test_crlf_source_exact_match_is_recorded_as_exact_bytes(self):
        relative = "resources/licenses/Cinnabar-LICENSE.md"
        source = (self.source / "LICENSE").read_bytes().replace(b"\n", b"\r\n")
        (self.source / "LICENSE").write_bytes(source)
        (self.engine / relative).write_bytes(source)
        item = package.inspect_engine(self.engine, self.source)["files"][relative]
        self.assertEqual(item["source_comparison"], {
            "source_sha256": hashlib.sha256(source).hexdigest(), "variant": "exact_bytes"})
        (self.engine / relative).write_bytes(source.replace(b"\r\n", b"\n"))
        with self.assertRaises(ValueError):
            package.inspect_engine(self.engine, self.source)

    def test_staging_preserves_actual_windows_notice_bytes_and_manifest_digest(self):
        relative = "resources/licenses/Cinnabar-LICENSE.md"
        source = (self.source / "LICENSE").read_bytes()
        payload = source.replace(b"\n", b"\r\n")
        (self.engine / relative).write_bytes(payload)
        folder, _ = self.stage()
        self.assertEqual((folder / "engine" / relative).read_bytes(), payload)
        self.assertEqual((folder / "licenses/cinnabar/LICENSE").read_bytes(), source)
        manifest = json.loads((folder / "bedrock-client.json").read_text())
        self.assertEqual(manifest["files"]["engine/" + relative], hashlib.sha256(payload).hexdigest())
        metadata = json.loads((folder / "build-metadata.json").read_text())
        self.assertEqual(metadata["engine_files"][relative]["source_comparison"]["variant"], "windows_crlf")

    def test_wrong_source_game_version_and_protocol_are_rejected(self):
        target = self.source / "assets/bedrock-target.json"
        for game, protocol in [("1.26.51", 2225), ("1.26.60", 2193)]:
            with self.subTest(game=game, protocol=protocol):
                target.write_text(json.dumps({"game_version": game, "wire_protocol": protocol}))
                with self.assertRaises(ValueError):
                    package.inspect_engine(self.engine, self.source)

    def test_unsafe_prep_kit_path_is_rejected(self):
        (self.source / "packaging/common/prep-kit-files.txt").write_text("../../outside\n")
        with self.assertRaises(ValueError):
            package.expected_payload(self.source)

    def test_engine_dll_must_be_amd64_dll_and_dependencies_bundled(self):
        path = self.engine / "dxcompiler.dll"
        pin = self.source / "packaging/windows/dxc.json"
        for data in [pe_fixture(dll=True, machine=0xAA64), pe_fixture(dll=False), pe_fixture("not-bundled.dll", dll=True)]:
            with self.subTest():
                path.write_bytes(data)
                pin.write_text(json.dumps({"library": "dxcompiler.dll", "library_sha256": hashlib.sha256(data).hexdigest()}))
                with self.assertRaises(ValueError):
                    package.inspect_engine(self.engine, self.source)

    def test_case_collision_is_rejected(self):
        if (self.engine / "CINNABAR.EXE").exists():
            self.skipTest("Filesystem cannot construct distinct case-colliding files")
        self.engine_file("CINNABAR.EXE", b"collision")
        with self.assertRaises(ValueError):
            package.inspect_engine(self.engine, self.source)

    def test_engine_symlink_is_rejected(self):
        target = self.engine / "resources/extra-link"
        try:
            target.symlink_to(self.source / "LICENSE")
        except OSError as error:
            self.skipTest(f"Host cannot create symlinks: {error}")
        with self.assertRaises(ValueError):
            package.inspect_engine(self.engine, self.source)

    def test_existing_output_is_preserved(self):
        folder, _ = self.stage()
        (folder / "keep.txt").write_text("preserve")
        with self.assertRaises(ValueError):
            self.stage()
        self.assertEqual((folder / "keep.txt").read_text(), "preserve")

    def test_real_package_requires_windows_and_missing_docs_is_refused(self):
        with patch.object(package.platform, "system", return_value="Linux"):
            with self.assertRaisesRegex(ValueError, "Windows"):
                package.assemble(self.engine, self.launcher, self.source, self.output)
        for relative in ("docs/INSTALL-BEDROCK-WINDOWS.md", "docs/BEDROCK-LICENSES.md"):
            with self.subTest(relative=relative):
                path = self.project / relative
                saved = path.read_text()
                path.unlink()
                with self.assertRaises(ValueError):
                    self.stage()
                path.write_text(saved)
        self.assertFalse(self.output.exists())

    def test_archive_layout_without_executing_fixture_binaries(self):
        with patch.object(package.platform, "system", return_value="Windows"):
            folder, archive = package.assemble(self.engine, self.launcher, self.source, self.output)
        with ZipFile(archive) as zipped:
            self.assertIsNone(zipped.testzip())
            self.assertIn("Herspers-Bedrock/Herspers-Bedrock.exe", zipped.namelist())
            self.assertIn("Herspers-Bedrock/engine/bedrock-core.exe", zipped.namelist())
            self.assertIn("Herspers-Bedrock/bedrock-client.json", zipped.namelist())
            self.assertIn("Herspers-Bedrock/BEDROCK-LICENSES.txt", zipped.namelist())
            self.assertFalse(any(".mcbea" in name for name in zipped.namelist()))


if __name__ == "__main__":
    unittest.main()
