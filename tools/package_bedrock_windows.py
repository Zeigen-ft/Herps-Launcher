#!/usr/bin/env python3
"""Assemble the licensed Rust Bedrock client and an independent Herspers launcher.

The engine is an unmodified, checksum-verified Cinnabar Windows payload. Its
PolyForm license is kept separate from the launcher's GPLv3 license. Staging
works on other hosts for tests and never produces a distributable ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import struct
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("_herspers_windows_pe", PROJECT / "tools/package_windows.py")
_windows = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_windows)
SYSTEM_DLLS = _windows.WINDOWS_SYSTEM | {
    "avrt.dll", "dbgcore.dll", "dhcpcsvc.dll", "dhcpcsvc6.dll", "dnsapi.dll",
    "fwpuclnt.dll", "imagehlp.dll", "msacm32.dll", "msimg32.dll", "mswsock.dll",
    "msvcp_win.dll", "normaliz.dll", "powrprof.dll", "profapi.dll", "psapi.dll",
    "rpcrt4.dll", "runtimeobject.dll", "samcli.dll", "sensapi.dll", "sspicli.dll",
    "uiautomationcore.dll", "windowscodecs.dll", "winhttp.dll", "wininet.dll",
    "winsta.dll", "wintrust.dll", "wldap32.dll", "wtsapi32.dll",
}
# These are prerequisites from Microsoft's Visual C++ 2015-2022 x64
# Redistributable, NOT libraries guaranteed to ship with Windows itself.
# No wildcard and no debug-runtime names are accepted.
VC_RUNTIME_DLLS = {
    "vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "msvcp140_1.dll",
    "msvcp140_2.dll", "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll",
}
PRODUCT_VERSION = "0.3.0"
ENGINE_VERSION = "0.1.31"
BEDROCK_VERSION = "1.26.60"
WIRE_PROTOCOL = 2225
ENGINE_COMMIT = "f64924fbb27004a1f785a2c131de9531fbcd252a"
LAUNCHER = "Herspers-Bedrock.exe"
FOLDER = "Herspers-Bedrock"
ARCHIVE = "Herspers-Bedrock-Windows-x64.zip"
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_PAYLOAD_BYTES = 2 * 1024 * 1024 * 1024
# These notice/license files in the verified 0.1.31 Windows MSI were copied
# from a Windows Git checkout. Only these observed text paths may match the
# deterministic CRLF form of the pinned archive's source bytes instead.
WINDOWS_CRLF_SOURCE_PATHS = frozenset({
    "resources/assets/THIRD_PARTY_NOTICES.md",
    "resources/licenses/Android-Bionic-BSD.txt",
    "resources/licenses/Android-ashmem-NOTICE.txt",
    "resources/licenses/Apache-2.0.txt",
    "resources/licenses/Box64-MIT.txt",
    "resources/licenses/Cinnabar-LICENSE.md",
    "resources/licenses/DirectXShaderCompiler-LICENSE.txt",
    "resources/licenses/GCC-GPL-3.0.txt",
    "resources/licenses/GCC-Runtime-Exception-3.1.txt",
    "resources/licenses/Inter-OFL-1.1.txt",
    "resources/licenses/Termux-glibc-MIT.txt",
    "resources/licenses/glibc-COPYING.LESSERv2.txt",
    "resources/licenses/glibc-COPYING.LIB.txt",
    "resources/licenses/glibc-COPYINGv2.txt",
    "resources/licenses/glibc-COPYINGv3.txt",
    "resources/licenses/glibc-LICENSES.txt",
    "resources/licenses/libandroid-shmem-BSD.txt",
    "resources/licenses/redb-MIT.txt",
})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _range(data: bytes, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError("PE range extends beyond file")
    return data[offset:offset + size]


def inspect_pe(data: bytes, allow_dll: bool = False, bundled_dlls=frozenset()) -> dict:
    """Inspect AMD64 PE32+ headers and imports; never execute the image.

    The parser follows the same PE import policy as the existing Windows
    packager, additionally accepting separately validated, bundled DLLs.
    """
    if _range(data, 0, 2) != b"MZ":
        raise ValueError("expected a Windows PE executable")
    pe = struct.unpack("<I", _range(data, 0x3C, 4))[0]
    if _range(data, pe, 4) != b"PE\0\0":
        raise ValueError("invalid PE signature")
    machine, count = struct.unpack("<HH", _range(data, pe + 4, 4))
    optional_size, flags = struct.unpack("<HH", _range(data, pe + 20, 4))
    if machine != 0x8664:
        raise ValueError("expected an x86_64 PE image")
    if not flags & 2 or bool(flags & 0x2000) != allow_dll:
        raise ValueError("expected a DLL" if allow_dll else "expected an executable, not a DLL")
    if not 1 <= count <= 96 or optional_size < 112:
        raise ValueError("invalid PE section or optional header size")
    optional = pe + 24
    _range(data, optional, optional_size + count * 40)
    if struct.unpack("<H", _range(data, optional, 2))[0] != 0x20B:
        raise ValueError("expected PE32+ optional header")
    header_size = struct.unpack("<I", _range(data, optional + 60, 4))[0]
    directory_count = struct.unpack("<I", _range(data, optional + 108, 4))[0]
    if directory_count > (optional_size - 112) // 8:
        raise ValueError("PE directory table extends beyond optional header")
    sections = []
    for index in range(count):
        section = optional + optional_size + index * 40
        virtual_size, address, raw_size, raw = struct.unpack("<IIII", _range(data, section + 8, 16))
        _range(data, raw, raw_size)
        sections.append((address, virtual_size, raw, raw_size))

    def offset(rva: int, size: int = 1) -> int:
        if rva < header_size and rva + size <= header_size:
            _range(data, rva, size)
            return rva
        for address, virtual_size, raw, raw_size in sections:
            relative = rva - address
            if 0 <= relative < max(virtual_size, raw_size) and relative + size <= raw_size:
                _range(data, raw + relative, size)
                return raw + relative
        raise ValueError(f"PE RVA {rva:#x} is outside file-backed sections")

    def dll_name(rva: int) -> str:
        value = bytearray()
        for index in range(260):
            byte = data[offset(rva + index)]
            if byte == 0:
                break
            value.append(byte)
        else:
            raise ValueError("PE DLL name is unterminated")
        try:
            name = value.decode("ascii").lower()
        except UnicodeDecodeError as error:
            raise ValueError("non-ASCII PE DLL name") from error
        if not name.endswith(".dll") or any(c in name for c in "\\/:"):
            raise ValueError("invalid PE DLL name")
        return name

    names = set()
    for directory, width, name_field in ((1, 20, 12), (13, 32, 4)):
        if directory >= directory_count:
            continue
        rva, size = struct.unpack("<II", _range(data, optional + 112 + directory * 8, 8))
        if not rva and not size:
            continue
        if not rva or size < width or size > len(data):
            raise ValueError("invalid PE import table size")
        for relative in range(0, size - width + 1, width):
            descriptor = _range(data, offset(rva + relative, width), width)
            if not any(descriptor):
                break
            if directory == 13 and struct.unpack_from("<I", descriptor)[0] != 1:
                raise ValueError("unsupported non-RVA delay import")
            names.add(dll_name(struct.unpack_from("<I", descriptor, name_field)[0]))
        else:
            raise ValueError("unterminated PE import table")
    bundled = {name.lower() for name in bundled_dlls}
    foreign = sorted(name for name in names if name not in SYSTEM_DLLS and name not in bundled
                     and name not in VC_RUNTIME_DLLS
                     and not name.startswith(("api-ms-win-", "ext-ms-win-")))
    if foreign:
        raise ValueError("unbundled non-system DLL imports: " + ", ".join(foreign))
    return {"format": "PE32+", "architecture": "x86_64", "kind": "dll" if allow_dll else "exe",
            "imports": sorted(names), "vc_runtime_dlls": sorted(names & VC_RUNTIME_DLLS)}


def relative_name(text: str) -> str:
    path = PurePosixPath(text)
    if (not text or "\\" in text or path.is_absolute() or path.as_posix() != text
            or any(part in (".", "..") or re.search(r'[<>:"|?*\x00-\x1f]', part)
                   or part.endswith((".", " "))
                   or re.match(r"(?i)^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", part)
                   for part in path.parts)):
        raise ValueError(f"unsafe payload path: {text!r}")
    return text


def regular_file(path: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular file: {path}")
    if getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
        raise ValueError(f"reparse-point file refused: {path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"file exceeds size limit: {path}")
    return path


def source_file(source: Path, relative: str) -> Path:
    relative_name(relative)
    path = source.joinpath(*PurePosixPath(relative).parts)
    regular_file(path)
    for parent in (path, *path.parents):
        if parent == source.parent:
            break
        if parent.is_symlink() or getattr(parent.lstat(), "st_file_attributes", 0) & 0x400:
            raise ValueError(f"source link refused: {path}")
    return regular_file(path)


def payload_plan(source: Path) -> tuple[dict[str, Path], set[str], dict]:
    text = source_file(source, "Cargo.toml").read_text(encoding="utf-8")
    workspace = re.search(r"(?ms)^\[workspace\.package\]\s*\n(.*?)(?=^\[|\Z)", text)
    version = re.search(r'(?m)^version\s*=\s*"([^"]+)"', workspace.group(1)) if workspace else None
    target = json.loads(source_file(source, "assets/bedrock-target.json").read_text())
    if (version is None or version.group(1) != ENGINE_VERSION
            or target.get("game_version") != BEDROCK_VERSION or target.get("wire_protocol") != WIRE_PROTOCOL):
        raise ValueError("source version/protocol does not match the pinned Bedrock engine")
    runtime = set()
    for line in source_file(source, "packaging/common/runtime-binaries.txt").read_text().splitlines():
        if line.strip():
            runtime.add(relative_name(line.split()[0] + ".exe"))
    required = {"cinnabar.exe", "cinnabar-updater.exe", "bedrock-core.exe", "bedrock-local-server.exe", "cinnabar-cxb.exe"}
    if runtime != required:
        raise ValueError("unexpected runtime executable table")
    dxc = json.loads(source_file(source, "packaging/windows/dxc.json").read_text())
    library = relative_name(dxc["library"])
    if library != "dxcompiler.dll" or not re.fullmatch(r"[0-9a-f]{64}", dxc.get("library_sha256", "")):
        raise ValueError("invalid pinned DXC library")
    binaries = runtime | {library, "resources/prep-kit/bin/assetc.exe"}
    copied = {
        "resources/assets/block-physics-v2225.bin": source_file(source, "crates/assets/data/block-physics-v2225.bin"),
        "resources/assets/THIRD_PARTY_NOTICES.md": source_file(source, "THIRD_PARTY_NOTICES.md"),
        "resources/licenses/Cinnabar-LICENSE.md": source_file(source, "LICENSE"),
    }
    font = json.loads(source_file(source, "assets/cinnangles-sans-source.json").read_text())["font_file"]
    if "/" in relative_name(font):
        raise ValueError("invalid UI font filename")
    copied["resources/fonts/" + font] = source_file(source, "assets/fonts/" + font)
    licenses = source / "assets/licenses"
    if licenses.is_symlink() or not licenses.is_dir():
        raise ValueError("missing source license directory")
    for path in sorted(licenses.iterdir()):
        copied["resources/licenses/" + relative_name(path.name)] = source_file(source, "assets/licenses/" + path.name)
    for line in source_file(source, "packaging/common/prep-kit-files.txt").read_text().splitlines():
        if line.strip():
            name = relative_name(line.strip())
            destination = "resources/prep-kit/" + name
            if destination in copied or destination in binaries:
                raise ValueError("duplicate prep-kit destination")
            copied[destination] = source_file(source, name)
    return copied, binaries, dxc


def expected_payload(source: Path) -> set[str]:
    copied, binaries, _ = payload_plan(source.resolve())
    return set(copied) | binaries


def inspect_engine(engine: Path, source: Path) -> dict:
    if engine.is_symlink() or not engine.is_dir():
        raise ValueError("engine must be an ordinary directory")
    engine, source = engine.resolve(), source.resolve()
    copied, binaries, dxc = payload_plan(source)
    actual = {}
    folded = set()
    total = 0
    def fail(error):
        raise error
    for directory, dirs, files in os.walk(engine, followlinks=False, onerror=fail):
        for name in dirs:
            path = Path(directory) / name
            if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError(f"engine directory link refused: {path}")
        for name in files:
            path = regular_file(Path(directory) / name)
            relative = relative_name(path.relative_to(engine).as_posix())
            if relative.casefold() in folded:
                raise ValueError(f"case-insensitive payload collision: {relative}")
            folded.add(relative.casefold())
            total += path.stat().st_size
            actual[relative] = path
    if len(actual) > 10000 or total > MAX_PAYLOAD_BYTES:
        raise ValueError("engine payload exceeds resource limits")
    expected = set(copied) | binaries
    if set(actual) != expected:
        raise ValueError(f"engine payload file mismatch: missing={sorted(expected - set(actual))}, unexpected={sorted(set(actual) - expected)}")
    metadata = {}
    errors = []
    required_vc = set()
    dlls = {name for name in binaries if name.lower().endswith(".dll")}
    for relative, path in sorted(actual.items()):
        digest = sha256(path)
        item = {"sha256": digest, "size_bytes": path.stat().st_size}
        if relative in copied:
            source_digest = sha256(copied[relative])
            comparison = {"source_sha256": source_digest, "variant": "exact_bytes"}
            if digest != source_digest:
                variant_digest = None
                if relative in WINDOWS_CRLF_SOURCE_PATHS:
                    canonical = copied[relative].read_bytes().replace(b"\r\n", b"\n")
                    if b"\r" not in canonical:
                        variant_digest = hashlib.sha256(canonical.replace(b"\n", b"\r\n")).hexdigest()
                if digest == variant_digest:
                    comparison["variant"] = "windows_crlf"
                else:
                    errors.append(f"{relative}: source-backed resource checksum mismatch")
            item["source_comparison"] = comparison
        if relative == dxc["library"] and digest != dxc["library_sha256"]:
            errors.append(f"{relative}: pinned DXC library checksum mismatch")
        if relative in binaries:
            try:
                item["pe"] = inspect_pe(path.read_bytes(), allow_dll=relative.lower().endswith(".dll"), bundled_dlls=dlls)
                required_vc.update(item["pe"]["vc_runtime_dlls"])
            except ValueError as error:
                errors.append(f"{relative}: {error}")
        metadata[relative] = item
    if errors:
        extra = f"\n... {len(errors) - 20} additional validation failures" if len(errors) > 20 else ""
        raise ValueError("engine validation failed:\n" + "\n".join(errors[:20]) + extra)
    return {"files": metadata, "runtime_executables": sorted(name for name in binaries if name.endswith(".exe")),
            "required_vc_runtime_dlls": sorted(required_vc)}


def assemble(engine: Path, launcher: Path, source: Path, output: Path, stage_only: bool = False) -> tuple[Path, Path | None]:
    if not stage_only and platform.system() != "Windows":
        raise ValueError("real packaging requires Windows; --stage-only is an unverified assembly")
    for directory in (engine, source):
        if (directory.is_symlink() or not directory.is_dir()
                or getattr(directory.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError(f"expected an ordinary input directory: {directory}")
    engine, source, output = engine.resolve(), source.resolve(), output.resolve()
    if output.is_relative_to(engine) or output.is_relative_to(source):
        raise ValueError("output must be outside engine and source directories")
    verified = inspect_engine(engine, source)
    launcher = regular_file(launcher)
    launcher_bytes = launcher.read_bytes()
    launcher_pe = inspect_pe(launcher_bytes)
    if launcher_pe["vc_runtime_dlls"]:
        raise ValueError(f"{LAUNCHER}: the independent launcher must link its Visual C runtime statically")
    guide = regular_file(PROJECT / "docs/INSTALL-BEDROCK-WINDOWS.md")
    license_guide = regular_file(PROJECT / "docs/BEDROCK-LICENSES.md")
    project_license = regular_file(PROJECT / "LICENSE")
    destination, archive = output / FOLDER, output / ARCHIVE
    if destination.exists() or destination.is_symlink() or archive.exists():
        raise ValueError("output already contains this package; choose a fresh directory")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".bedrock-package-", dir=output) as temporary:
        package = Path(temporary) / FOLDER
        package.mkdir()
        for relative in verified["files"]:
            target = package / "engine" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(engine / relative, target)
        shutil.copy2(launcher, package / LAUNCHER)
        shutil.copy2(guide, package / "INSTALL-BEDROCK-WINDOWS.txt")
        shutil.copy2(license_guide, package / "BEDROCK-LICENSES.txt")
        shutil.copy2(project_license, package / "LICENSE")
        notices = package / "licenses/cinnabar"
        notices.mkdir(parents=True)
        for filename in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
            shutil.copy2(source_file(source, filename), notices / filename)
        manifest = {
            "product_version": PRODUCT_VERSION, "engine": "cinnabar", "engine_version": ENGINE_VERSION,
            "bedrock_version": BEDROCK_VERSION, "wire_protocol": WIRE_PROTOCOL,
            "in_app_resource_downloads": True, "game_assets_included": False,
            "required_vc_runtime_dlls": verified["required_vc_runtime_dlls"],
            "files": {"engine/" + name: item["sha256"] for name, item in verified["files"].items()},
        }
        (package / "bedrock-client.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        metadata = {"source_commit": ENGINE_COMMIT, "stage_only": stage_only,
                    "launcher_sha256": hashlib.sha256(launcher_bytes).hexdigest(), "engine_files": verified["files"],
                    "launcher_pe": launcher_pe,
                    "required_vc_runtime_dlls": verified["required_vc_runtime_dlls"],
                    "gameplay_tested": False, "online_authentication_tested": False,
                    "engine_license": "PolyForm Noncommercial 1.0.0", "launcher_license": "GPL-3.0"}
        (package / "build-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        status = ("STAGED ONLY: UNVERIFIED ASSEMBLY, NO DISTRIBUTABLE ZIP.\n" if stage_only
                  else "Native Windows Bedrock client package. Gameplay and account login require personal testing.\n")
        (package / "BUILD-STATUS.txt").write_text(status, encoding="utf-8")
        package.rename(destination)
    if stage_only:
        return destination, None
    with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=6) as zipped:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(output))
    return destination, archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("engine", "launcher", "source", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    try:
        folder, archive = assemble(args.engine, args.launcher, args.source, args.output, args.stage_only)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"package_bedrock_windows: {error}\n")
    print(f"{'STAGED ONLY (unverified)' if args.stage_only else 'Packaged'}: {folder}")
    if archive:
        print(f"ZIP: {archive}")


if __name__ == "__main__":
    main()
