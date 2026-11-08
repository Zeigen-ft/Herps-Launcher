#!/usr/bin/env python3
"""Assemble Herspers Minecraft from native desktop Horizon binaries.

Real packaging runs on macOS and checks architecture, library dependencies and
ad hoc signatures. --stage-only assembles an explicitly unverified bundle on
any host; it never signs, runs a game, or creates a distributable ZIP.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile


PROJECT = Path(__file__).resolve().parents[1]
APP_NAME = "Herspers Minecraft.app"
BINARIES = ("horizon-client", "horizon-ctl", "horizon-prepare")
PRODUCT_VERSION = "0.2.3"
CPUS = {"arm64": 0x0100000C, "x86_64": 0x01000007}
PREPARATION_DIRS = ("tools", "mods/horizon/src/test/java", "crates/horizon-prepare")
EXCLUDED_DIRS = {".git", ".local", "target", "build", "__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".jar", ".class", ".apk", ".pyc"}


def checked_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular file (symlinks are refused): {path}")
    return path


def tree_files(root):
    """Select source files only; never follow a link or copy generated game data."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"missing source directory (symlinks are refused): {root}")
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise ValueError(f"source tree contains a symlink: {Path(directory) / name}")
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            yield checked_file(path)


def binary_architecture(path, arch):
    """Check a thin 64-bit Mach-O executable header, without executing it."""
    checked_file(path)
    with path.open("rb") as stream:
        header = stream.read(32)
    if len(header) != 32 or header[:4] not in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"):
        raise ValueError(f"{path.name}: expected a thin 64-bit Mach-O executable")
    endian = "<" if header[:4] == b"\xcf\xfa\xed\xfe" else ">"
    _, cpu, _, filetype, _, _, _, _ = struct.unpack(endian + "8I", header)
    if cpu != CPUS[arch] or filetype != 2:
        raise ValueError(f"{path.name}: expected a {arch} Mach-O executable")
    if not os.access(path, os.X_OK):
        raise ValueError(f"{path.name}: binary is not executable")


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def verify_macos_binary(path, arch):
    observed = run("lipo", "-archs", str(path)).strip()
    if observed != arch:
        raise ValueError(f"{path.name}: lipo reports {observed!r}, expected {arch!r}")
    for line in run("otool", "-L", str(path)).splitlines()[1:]:
        dependency = line.strip().split(" (", 1)[0]
        if dependency and not dependency.startswith(("/System/Library/", "/usr/lib/")):
            raise ValueError(f"{path.name}: unbundled non-system library: {dependency}")


def source_inputs(source):
    selected = [checked_file(source / "research-lock.json")]
    lock = json.loads(selected[0].read_text())
    game = lock.get("minecraft") if isinstance(lock, dict) else None
    if not isinstance(game, dict) or game.get("version") != "26.3" or game.get("java_major") != 25:
        raise ValueError("preparation scripts require the pinned Minecraft 26.3 / Java 25 source")
    for relative in PREPARATION_DIRS:
        paths = list(tree_files(source / relative))
        if not paths:
            raise ValueError(f"empty preparation source directory: {relative}")
        selected.extend(paths)
    return selected


def license_files(source):
    required = [checked_file(source / name) for name in ("LICENSE", "THIRD_PARTY_NOTICES.md")]
    # Keep the upstream layout so relative license paths in its notices remain useful.
    # This includes wgpu, winit, font/icon licenses, and source headers for the FSR port.
    for directory, dirs, files in os.walk(source):
        # The upstream CLAUDE.md is an unrelated symlink. License discovery must
        # not follow arbitrary links, nor reject unrelated source metadata.
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS
                         and not (Path(directory) / d).is_symlink())
        for name in files:
            if name.upper().startswith(("LICENSE", "NOTICE", "OFL-")):
                required.append(checked_file(Path(directory) / name))
    for relative in (
        "third_party/winit/PATCHES.md",
        "crates/horizon-client-render/src/gfx/frame_gen/optical_flow.wgsl",
        "crates/horizon-client-render/src/gfx/frame_gen/optical_flow.rs",
    ):
        path = source / relative
        if path.is_file():
            required.append(checked_file(path))
    return sorted(set(required))


def copy_files(files, source, destination):
    for path in files:
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def engine_patch_provenance(source, project):
    """Reject unprepared/mismatched engine inputs and describe the applied changes."""
    lock = json.loads(checked_file(project / "upstream.lock.json").read_bytes())
    manifest_bytes = checked_file(project / "patches/upstream.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    stamp = json.loads(checked_file(source / ".herspers-prepared.json").read_bytes())
    if (not isinstance(lock, dict) or not isinstance(manifest, dict) or not isinstance(stamp, dict)
            or not re.fullmatch(r"[0-9a-f]{40,64}", str(lock.get("commit", "")))
            or manifest.get("upstream_commit") != lock["commit"]
            or not isinstance(manifest.get("files"), list) or not manifest["files"]):
        raise ValueError("engine patch provenance must match the pinned upstream source")

    def relative(value):
        if (not isinstance(value, str) or not value or "\\" in value or ":" in value
                or "\0" in value or any(p in ("", ".", "..") for p in value.split("/"))):
            raise ValueError("unsafe path in engine patch provenance")
        return Path(*value.split("/"))

    digest = hashlib.sha256(manifest_bytes)
    seen = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "before_sha256", "after_sha256", "patch"}:
            raise ValueError("invalid engine patch provenance entry")
        target = relative(entry["path"])
        identity = target.as_posix().casefold()
        if identity in seen or not re.fullmatch(r"[0-9a-f]{64}", str(entry["after_sha256"])):
            raise ValueError("invalid or duplicate engine patch target")
        seen.add(identity)
        patch = checked_file(project / "patches" / relative(entry["patch"])).read_bytes()
        digest.update(len(patch).to_bytes(8, "big") + patch)
        actual = hashlib.sha256(checked_file(source / target).read_bytes()).hexdigest()
        if actual != entry["after_sha256"]:
            raise ValueError(f"engine patch postimage mismatch: {target}")
    patch_hash = digest.hexdigest()
    if (stamp.get("upstream") != lock or stamp.get("patches_sha256") != patch_hash
            or not re.fullmatch(r"[0-9a-f]{64}", str(stamp.get("tree_sha256", "")))):
        raise ValueError("prepared engine source does not match the current patch manifest")
    summary = {"modified": True, "upstream_commit": lock["commit"],
               "patches_sha256": patch_hash, "prepared_tree_sha256": stamp["tree_sha256"],
               "provenance_file": "engine-patches.json"}
    # Advertise this opt-in interaction only for an engine carrying both parts
    # of the verified implementation, never just a content/launcher update.
    gathering = "crates/horizon-client/src/game/herspers_gathering"
    if {gathering + ".rs", gathering + "_rules.rs", "crates/horizon-client/src/game.rs",
            "crates/horizon-client/src/game/native_hooks.rs"} <= seen:
        summary["native_features"] = ["rlcraft-gathering-1"]
    woodcutting = "crates/horizon-client/src/game/herspers_woodcutting"
    if {woodcutting + ".rs", woodcutting + "_rules.rs", "crates/horizon-client/src/game.rs",
            "crates/horizon-client/src/game/native_hooks.rs"} <= seen:
        summary.setdefault("native_features", []).append("rlcraft-woodcutting-1")
    return summary, {"schema": 1, "preparation": stamp, "patches": manifest}


def assemble(source, binaries, arch, output, stage_only=False):
    source = source.resolve()
    binaries = binaries.resolve()
    output = output.resolve()
    if output.is_relative_to(source):
        raise ValueError("output must be outside the upstream source directory")
    if not stage_only and platform.system() != "Darwin":
        raise ValueError("real packaging requires macOS; --stage-only creates an unverified assembly only")
    inputs = source_inputs(source)
    notices = license_files(source)
    engine_source, patch_provenance = engine_patch_provenance(source, PROJECT)
    shader_guide = checked_file(PROJECT / "docs/SHADERS.md")
    for name in BINARIES:
        binary_architecture(binaries / name, arch)
        if not stage_only:
            verify_macos_binary(binaries / name, arch)
    app = output / APP_NAME
    archive = output / f"herspers-minecraft-macos-{arch}.zip"
    if app.exists() or app.is_symlink() or (not stage_only and archive.exists()):
        raise ValueError("output already contains this app or archive; choose a fresh output directory")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".herspers-package-", dir=output) as scratch:
        staged = Path(scratch) / APP_NAME
        macos = staged / "Contents/MacOS"
        resources = staged / "Contents/Resources"
        macos.mkdir(parents=True)
        resources.mkdir()
        for name in BINARIES:
            shutil.copy2(binaries / name, macos / name)
            (macos / name).chmod(0o755)
            if not stage_only:
                run("codesign", "--force", "--sign", "-", "--timestamp=none", str(macos / name))
        for template, target in (("launch.command", resources / "launch.command"),
                                 ("prepare.command", resources / "prepare.command")):
            shutil.copy2(PROJECT / "packaging" / template, target)
            target.chmod(0o755)
        native_launcher = macos / "herspers-minecraft"
        if stage_only:
            # A nonfunctional header permits layout checks without an Apple SDK.
            # It is explicitly marked in BUILD-STATUS and is never zipped.
            native_launcher.write_bytes(struct.pack("<8I", 0xFEEDFACF, CPUS[arch], 0, 2, 0, 0, 0, 0))
            native_launcher.chmod(0o755)
        else:
            run("xcrun", "--sdk", "macosx", "clang", "-arch", arch,
                "-mmacosx-version-min=11.0", "-Os", "-Wall", "-Wextra", "-Werror",
                str(PROJECT / "packaging/launcher.c"), "-o", str(native_launcher))
            binary_architecture(native_launcher, arch)
            verify_macos_binary(native_launcher, arch)
            run("codesign", "--force", "--sign", "-", "--timestamp=none", str(native_launcher))
        copy_files(inputs, source, resources / "preparation")
        copy_files(notices, source, resources / "upstream-notices")
        shutil.copy2(shader_guide, resources / "SHADERS.txt")
        (resources / "engine-patches.json").write_text(json.dumps(patch_provenance, indent=2) + "\n")
        preparation_hash = hashlib.sha256()
        for path in sorted(inputs):
            preparation_hash.update(str(path.relative_to(source)).encode())
            preparation_hash.update(b"\0")
            preparation_hash.update(path.read_bytes())
        (resources / "preparation-id.txt").write_text(preparation_hash.hexdigest() + "\n")
        project_lock = PROJECT / "upstream.lock.json"
        if project_lock.is_file():
            shutil.copy2(project_lock, resources / "upstream.lock.json")
        metadata = {"product_version": PRODUCT_VERSION, "architecture": arch, "stage_only": stage_only,
                    "macos_runtime_tested": False, "game_resources_included": False,
                    "native_launcher_compiled": not stage_only,
                    "engine_source": engine_source,
                    "binaries_sha256": {name: hashlib.sha256((macos / name).read_bytes()).hexdigest()
                                        for name in BINARIES}}
        (resources / "build-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        status = ("STAGED ONLY: UNVERIFIED, UNSIGNED, NOT A WORKING MACOS BUILD.\n"
                  if stage_only else
                  "Packaged on macOS with ad hoc signatures. Not notarized; gameplay has not been verified.\n")
        (resources / "BUILD-STATUS.txt").write_text(status + "Game resources are not included; run prepare.command first.\n")
        info = {"CFBundleName": "Herspers Minecraft", "CFBundleDisplayName": "Herspers Minecraft",
                "CFBundleIdentifier": "dev.herspers.minecraft", "CFBundleExecutable": "herspers-minecraft",
                "CFBundlePackageType": "APPL", "CFBundleInfoDictionaryVersion": "6.0",
                "CFBundleShortVersionString": PRODUCT_VERSION, "CFBundleVersion": "203",
                "LSMinimumSystemVersion": "11.0", "NSHighResolutionCapable": True,
                "LSApplicationCategoryType": "public.app-category.games",
                "NSHumanReadableCopyright": "Based on MIT-licensed Horizon by Ludovic Marie and contributors."}
        with (staged / "Contents/Info.plist").open("wb") as stream:
            plistlib.dump(info, stream)
        if not stage_only:
            run("codesign", "--force", "--sign", "-", "--timestamp=none", str(staged))
            run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(staged))
        staged.rename(app)
    if not stage_only:
        run("ditto", "-c", "-k", "--norsrc", "--noextattr", "--noqtn", "--keepParent", str(app), str(archive))
    return app, None if stage_only else archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--arch", choices=tuple(CPUS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage-only", action="store_true", help="assemble only; no signing, ZIP, or runtime verification")
    args = parser.parse_args()
    try:
        app, archive = assemble(args.source, args.binaries, args.arch, args.output, args.stage_only)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"package_macos: {error}\n")
    print(f"{'STAGED ONLY (unverified)' if args.stage_only else 'Packaged (ad hoc signed)'}: {app}")
    if archive:
        print(f"ZIP: {archive}\nNot notarized. Resource preparation and macOS gameplay testing remain required.")


if __name__ == "__main__":
    main()
