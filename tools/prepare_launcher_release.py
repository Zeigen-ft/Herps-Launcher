#!/usr/bin/env python3
"""Collect verified native CI files for manual publication; never create a release/tag."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
PACK = "herspers_rl_chainmail-0.1.0.hmod"
PACK_SHA = "015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346"
SPECS = {
    "windows": ("Windows-x86_64", None),
    "macos-intel": ("macOS-x86_64", "x86_64"),
    "macos-arm64": ("macOS-arm64", "arm64"),
}
GUIDES = ("README.md", "INSTALLATION.md", "QUICK_START.md", "RELEASE_NOTES.md",
          "LICENSE", "THIRD_PARTY_NOTICES.md")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def regular(path, limit=1 << 30):
    if path.is_symlink() or path.is_junction() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError(f"Missing, linked or oversized release input: {path}")
    return path


def document(path):
    value = json.loads(regular(path, 16 << 20).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Invalid receipt object: {path}")
    return value


def unique(folder, suffix):
    paths = sorted(path for path in folder.rglob("*") if path.is_file() and path.name.endswith(suffix))
    if len(paths) != 1:
        raise ValueError(f"Expected exactly one {suffix} under {folder}; found {len(paths)}")
    return paths[0]


def zip_tree(folder, output):
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as zipped:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                regular(path)
                entry = ZipInfo(path.relative_to(folder).as_posix(), (2026, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = ZIP_DEFLATED
                zipped.writestr(entry, path.read_bytes())


def validate_platform(inputs, platform, source):
    label, arch = SPECS[platform]
    main = inputs / f"Herps-Launcher-{VERSION}-{label}"
    evidence = inputs / f"Herps-Launcher-evidence-{label}"
    content = inputs / f"RLCraft-Chainmail-{VERSION}-{label}"
    receipt = document(main / "candidate.json")
    if (receipt.get("source_commit") != source or receipt.get("gameplay_verified") is not False
            or receipt.get("interactive_verified") is not False or receipt.get("public_release_approved") is not False):
        raise ValueError(f"Source/claim mismatch for {platform}")
    members = receipt.get("artifacts")
    expected_extensions = {".exe", ".zip"} if platform == "windows" else {".dmg"}
    if (not isinstance(members, list) or len(members) != len(expected_extensions)
            or {Path(m.get("file", "")).suffix for m in members} != expected_extensions):
        raise ValueError(f"Incomplete native package set for {platform}")
    sums = {}
    for line in regular(main / "SHA256SUMS", 1 << 20).read_text().splitlines():
        sha, name = line.split(None, 1)
        sums[name.strip()] = sha
    copies, hashes = [], {}
    for member in members:
        name = member.get("file", "")
        if Path(name).name != name or "/" in name or "\\" in name or ".." in name:
            raise ValueError("Release member escaped its artifact folder")
        path = regular(main / name)
        sha = digest(path)
        if path.stat().st_size != member.get("bytes") or sha != member.get("sha256") or sums.get(name) != sha:
            raise ValueError(f"Native package checksum mismatch: {name}")
        if path.suffix == ".exe":
            with path.open("rb") as stream:
                if stream.read(2) != b"MZ":
                    raise ValueError("Windows installer is not a PE executable")
            final = f"Herps-Launcher-{VERSION}-Windows-x64-Setup.exe"
        elif path.suffix == ".zip":
            with ZipFile(path) as zipped:
                if "Herps Launcher/Herps Launcher.exe" not in zipped.namelist():
                    raise ValueError("Portable package lacks its launcher")
            final = f"Herps-Launcher-{VERSION}-Windows-x64-Portable.zip"
        else:
            with path.open("rb") as stream:
                if path.stat().st_size < 512:
                    raise ValueError("DMG is too small")
                stream.seek(-512, 2)
                if stream.read(4) != b"koly":
                    raise ValueError("Mac package lacks a UDIF trailer")
            sidecar = document(main / path.with_suffix(".notarization.json").name)
            if sidecar.get("dmg_sha256") != sha or sidecar.get("notarized") is not False:
                raise ValueError("DMG notarization/hash receipt differs; review changed signing scope")
            final = f"Herps-Launcher-{VERSION}-macOS-{'Intel' if arch == 'x86_64' else 'Apple-Silicon'}.dmg"
        copies.append((path, final))
        hashes[final] = {"sha256": sha, "bytes": path.stat().st_size, "original_filename": name}
    lifecycle = document(unique(evidence, "windows-lifecycle.json" if arch is None else "delivered-dmg.json"))
    if (lifecycle.get("status") != "passed" or lifecycle.get("gameplay_verified") is not False
            or lifecycle.get("interactive_verified") is not False):
        raise ValueError(f"Native installed verification did not pass for {platform}")
    frozen = lifecycle.get("installed-workflows.json" if arch is None else "frozen-acceptance.json", {})
    if (frozen.get("status") != "passed" or frozen.get("tests_run") != 68 or frozen.get("failures")
            or frozen.get("errors") or frozen.get("skipped") or frozen.get("unexpected_skips")
            or set(frozen.get("tools_on_path", {})) != {"cargo", "rustc", "rustup"}
            or any(frozen["tools_on_path"].values())
            or len(frozen.get("chainmail_cases_verified", [])) != 3
            or len(frozen.get("targeted_backup_cases_verified", [])) != 3):
        raise ValueError(f"Incomplete/failed 68-case frozen verification for {platform}")
    smoke = lifecycle.get("installed-smoke.json" if arch is None else "delivered-smoke.json", {})
    if smoke.get("status") != "passed" or smoke.get("pages_opened") != 7:
        raise ValueError("Seven-page delivered navigation is missing")
    if arch is None:
        setup = f"Herps-Launcher-{VERSION}-Windows-x64-Setup.exe"
        if (lifecycle.get("setup_sha256") != hashes[setup]["sha256"]
                or lifecycle.get("overlong_destination_rejected_before_copy") is not True
                or lifecycle.get("existing_profile_and_preference_preserved") is not True):
            raise ValueError("Windows lifecycle/preservation evidence differs")
        proof = document(main / "native-build-proof.json")
        if proof.get("status") != "passed" or not all(proof.get(key) is True for key in
                ("injected_marker_present", "native_selection_verified", "rollback_selection_verified",
                 "save_preserved", "clean_binary_preserved", "source_cache_preserved")):
            raise ValueError("Existing Windows native-mod regression is missing")
    elif (lifecycle.get("architecture") != arch or smoke.get("architecture") != arch
            or lifecycle.get("dmg_sha256") != next(iter(hashes.values()))["sha256"]
            or not lifecycle.get("preserved_after_app_removal")):
        raise ValueError("Mac architecture/DMG/preservation evidence differs")
    pack = regular(content / PACK, 256 << 10)
    pack_receipt = document(content / "package.json")
    if (digest(pack) != PACK_SHA or pack_receipt.get("source_commit") != source
            or pack_receipt.get("sha256") != PACK_SHA or pack_receipt.get("default_enabled") is not False):
        raise ValueError("Bundled content source/hash/default differs")
    if arch is None:
        native = document(content / "native-validation.json")
        if (native.get("status") != "passed" or native.get("native_recipe_matcher_verified") is not True
                or native.get("gameplay_verified") is not False or native.get("package_sha256") != PACK_SHA
                or len(native.get("cases", [])) != 10):
            raise ValueError("Windows native recipe probe evidence is incomplete")
    return copies, pack, {"source_commit": source, "platform": lifecycle.get("platform"),
        "architecture": arch or "x86_64", "files": hashes, "frozen_tests": 68, "frozen_skipped": [],
        "interactive_verified": False, "gameplay_verified": False,
        "signing": "unsigned Windows installer" if arch is None else "ad hoc/development; not notarized"}


def prepare(inputs, output, source, root=ROOT):
    if not re.fullmatch("[0-9a-f]{40}", source):
        raise ValueError("Expected an exact verified source commit")
    if output.exists() or output.is_symlink():
        raise FileExistsError("Preserve an existing release output; choose a fresh directory")
    for name in GUIDES:
        regular(root / name)
    validated = {name: validate_platform(inputs, name, source) for name in SPECS}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="release-stage-", dir=output.parent) as temporary:
        stage = Path(temporary) / "files"
        stage.mkdir()
        for copies, _, report in validated.values():
            for path, final in copies:
                shutil.copyfile(path, stage / final)
                if digest(stage / final) != report["files"][final]["sha256"]:
                    raise ValueError("Release copy changed native package bytes")
        shutil.copyfile(validated["windows"][1], stage / PACK)
        for name in GUIDES:
            shutil.copyfile(root / name, stage / name)
        notice_root = Path(temporary) / "notices"
        shutil.copytree(root / "licenses", notice_root / "licenses")
        shutil.copyfile(root / "LICENSE", notice_root / "LICENSE")
        chain_notices = notice_root / "chainmail"
        chain_notices.mkdir()
        for name in ("NOTICE.txt", "LICENSE-CraftableChainmail.txt"):
            shutil.copyfile(root / "content/rlcraft_chainmail" / name, chain_notices / name)
        for path in sorted(inputs.rglob("*")):
            if path.is_file() and (path.name in ("python-dependencies.json", "resolved-build-requirements.txt")
                                   or "python-notices" in path.parts):
                regular(path, 16 << 20)
                destination = notice_root / "platform-evidence" / path.relative_to(inputs)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        zip_tree(notice_root, stage / "LICENSES.zip")
        from tools.package_rlcraft_inspector import stage as stage_inspector
        inspector = Path(temporary) / "inspector"
        stage_inspector(inspector)
        zip_tree(inspector, stage / "RLCraft-2.9.3-Local-Inspector.zip")
        manifest = {"schema": 1, "version": VERSION, "prerelease_candidate": True,
            "source_commit": source, "repository": "Zeigen-ft/Herps-Launcher",
            "platforms": {name: data[2] for name, data in validated.items()},
            "public_release_created": False, "tag_created": False,
            "macos_physical_gameplay": "NOT RUN", "full_modpack_compatibility": False,
            "physical_evidence": "User-reported Windows cases belong to original source run 42118750443; see guides.",
            "unresolved_observations": ["earlier loading-logo stall", "initially empty crafting output"],
            "reproducibility": "Pinned inputs and hashes; not a bit-for-bit reproducibility claim"}
        (stage / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with (stage / "RELEASE_NOTES.md").open("a", encoding="utf-8") as notes:
            notes.write(f"\n## Verified destination build\n\nSource: `{source}`. All three native targets passed; each delivered frozen cohort passed 68/68 with zero skips.\n\n")
            notes.write("The DMG/installer names are release-facing copies of real CI files; internal app names and bytes were preserved.\n\n")
            notes.write("| File | SHA-256 |\n| --- | --- |\n")
            for path in sorted(stage.iterdir()):
                if path.suffix in (".exe", ".dmg", ".zip", ".hmod"):
                    notes.write(f"| `{path.name}` | `{digest(path)}` |\n")
        sums = [f"{digest(path)}  {path.name}" for path in sorted(stage.iterdir()) if path.is_file()]
        (stage / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
        # No GitHub release/tag API exists here. Publish only the prepared local directory.
        stage.rename(output)
    return manifest


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-source", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.inputs, args.output, args.expected_source), indent=2))
