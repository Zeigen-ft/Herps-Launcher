"""Synthetic distribution-contract fixtures; never gameplay/platform acceptance."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

from tools import prepare_launcher_release as release
from tools.build_rlcraft_chainmail import package_bytes


class ReleasePreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="release-contract-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.inputs = self.root / "inputs"
        self.output = self.root / "release"
        self.source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=release.ROOT, text=True).strip()
        for platform, (label, arch) in release.SPECS.items():
            self.fixture(platform, label, arch)

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def fixture(self, platform, label, arch):
        main = self.inputs / f"Herps-Launcher-0.1.0-{label}"
        evidence = self.inputs / f"Herps-Launcher-evidence-{label}"
        content = self.inputs / f"RLCraft-Chainmail-0.1.0-{label}"
        main.mkdir(parents=True)
        files = []
        if arch is None:
            exe = main / "owned-Setup.exe"
            exe.write_bytes(b"MZowned synthetic installer fixture; not runnable")
            portable = main / "owned-portable.zip"
            with ZipFile(portable, "w") as zipped:
                zipped.writestr("Herps Launcher/Herps Launcher.exe", b"owned synthetic fixture")
            paths = [exe, portable]
        else:
            dmg = main / "owned.dmg"
            dmg.write_bytes(b"owned synthetic DMG fixture" + b"koly" + b"\0" * 508)
            self.write_json(dmg.with_suffix(".notarization.json"), {"notarized": False, "dmg_sha256": release.digest(dmg)})
            paths = [dmg]
        for path in paths:
            files.append({"file": path.name, "bytes": path.stat().st_size, "sha256": release.digest(path)})
        self.write_json(main / "candidate.json", {"source_commit": self.source, "artifacts": files,
            "interactive_verified": False, "gameplay_verified": False, "public_release_approved": False})
        (main / "SHA256SUMS").write_text("".join(f"{x['sha256']}  {x['file']}\n" for x in files))
        frozen = {"status": "passed", "tests_run": 68, "failures": [], "errors": [], "skipped": [],
            "unexpected_skips": [], "tools_on_path": {"cargo": None, "rustc": None, "rustup": None},
            "chainmail_cases_verified": ["owned-a", "owned-b", "owned-c"],
            "targeted_backup_cases_verified": ["owned-d", "owned-e", "owned-f"]}
        smoke = {"status": "passed", "pages_opened": 7, "architecture": arch}
        life = {"status": "passed", "gameplay_verified": False, "interactive_verified": False,
            "platform": "owned synthetic fixture, not a native OS test"}
        if arch is None:
            life.update({"installed-workflows.json": frozen, "installed-smoke.json": smoke,
                "setup_sha256": files[0]["sha256"], "overlong_destination_rejected_before_copy": True,
                "existing_profile_and_preference_preserved": True})
            proof = {"status": "passed", **{k: True for k in ("injected_marker_present", "native_selection_verified",
                "rollback_selection_verified", "save_preserved", "clean_binary_preserved", "source_cache_preserved")}}
            self.write_json(main / "native-build-proof.json", proof)
        else:
            life.update({"architecture": arch, "frozen-acceptance.json": frozen, "delivered-smoke.json": smoke,
                "dmg_sha256": files[0]["sha256"], "preserved_after_app_removal": {"owned.txt": "owned"}})
        self.write_json(evidence / ("windows-lifecycle.json" if arch is None else "delivered-dmg.json"), life)
        content.mkdir()
        (content / release.PACK).write_bytes(package_bytes())
        self.write_json(content / "package.json", {"source_commit": self.source, "sha256": release.PACK_SHA,
            "default_enabled": False})
        if arch is None:
            self.write_json(content / "native-validation.json", {"status": "passed",
                "native_recipe_matcher_verified": True, "gameplay_verified": False,
                "package_sha256": release.PACK_SHA, "cases": list(range(10))})

    def mutate_receipt(self, folder, name, callback):
        path = self.inputs / folder / name
        data = json.loads(path.read_text())
        callback(data)
        self.write_json(path, data)

    def test_copies_verified_bytes_and_ships_both_guides_notices_and_hashes(self):
        expected = (self.inputs / "Herps-Launcher-0.1.0-macOS-arm64/owned.dmg").read_bytes()
        report = release.prepare(self.inputs, self.output, self.source)
        self.assertEqual((self.output / "Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg").read_bytes(), expected)
        self.assertEqual((self.output / "INSTALLATION.md").read_bytes(), (release.ROOT / "INSTALLATION.md").read_bytes())
        self.assertTrue((self.output / "QUICK_START.md").is_file())
        self.assertTrue((self.output / "LICENSES.zip").is_file())
        self.assertTrue((self.output / "RLCraft-2.9.3-Local-Inspector.zip").is_file())
        self.assertFalse(report["public_release_created"])
        self.assertFalse(report["tag_created"])
        self.assertEqual(report["macos_physical_gameplay"], "NOT RUN")
        sums = {line.split(None, 1)[1]: line.split(None, 1)[0]
                for line in (self.output / "SHA256SUMS.txt").read_text().splitlines()}
        self.assertIn("INSTALLATION.md", sums)
        self.assertIn("QUICK_START.md", sums)
        for name, sha in sums.items():
            self.assertEqual(release.digest(self.output / name), sha)
        with ZipFile(self.output / "LICENSES.zip") as zipped:
            self.assertIn("chainmail/LICENSE-CraftableChainmail.txt", zipped.namelist())

    def test_corrupt_native_package_is_rejected_before_output(self):
        (self.inputs / "Herps-Launcher-0.1.0-macOS-arm64/owned.dmg").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "checksum"):
            release.prepare(self.inputs, self.output, self.source)
        self.assertFalse(self.output.exists())

    def test_mixed_source_commits_are_rejected(self):
        self.mutate_receipt("Herps-Launcher-0.1.0-macOS-x86_64", "candidate.json", lambda d: d.update(source_commit="0" * 40))
        with self.assertRaisesRegex(ValueError, "Source/claim"):
            release.prepare(self.inputs, self.output, self.source)

    def test_missing_platform_never_produces_partial_release(self):
        (self.inputs / "Herps-Launcher-0.1.0-macOS-x86_64/candidate.json").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            release.prepare(self.inputs, self.output, self.source)
        self.assertFalse(self.output.exists())

    def test_skipped_frozen_tests_and_false_gameplay_claim_fail_closed(self):
        self.mutate_receipt("Herps-Launcher-evidence-Windows-x86_64", "windows-lifecycle.json",
            lambda d: d["installed-workflows.json"].update(skipped=[["owned-a", "missing"]]))
        with self.assertRaisesRegex(ValueError, "68-case"):
            release.prepare(self.inputs, self.output, self.source)
        self.mutate_receipt("Herps-Launcher-evidence-Windows-x86_64", "windows-lifecycle.json",
            lambda d: d["installed-workflows.json"].update(skipped=[]))
        self.mutate_receipt("Herps-Launcher-0.1.0-macOS-arm64", "candidate.json", lambda d: d.update(gameplay_verified=True))
        with self.assertRaisesRegex(ValueError, "Source/claim"):
            release.prepare(self.inputs, self.output, self.source)

    def test_mismatched_mac_architecture_or_dmg_receipt_is_rejected(self):
        self.mutate_receipt("Herps-Launcher-evidence-macOS-x86_64", "delivered-dmg.json", lambda d: d.update(architecture="arm64"))
        with self.assertRaisesRegex(ValueError, "architecture"):
            release.prepare(self.inputs, self.output, self.source)

    def test_existing_release_directory_is_never_overwritten(self):
        self.output.mkdir()
        (self.output / "owned.txt").write_text("keep")
        with self.assertRaises(FileExistsError):
            release.prepare(self.inputs, self.output, self.source)
        self.assertEqual((self.output / "owned.txt").read_text(), "keep")

    def test_native_member_path_traversal_is_rejected(self):
        self.mutate_receipt("Herps-Launcher-0.1.0-macOS-arm64", "candidate.json",
            lambda d: d["artifacts"][0].update(file="../outside.dmg"))
        with self.assertRaisesRegex(ValueError, "escaped"):
            release.prepare(self.inputs, self.output, self.source)
