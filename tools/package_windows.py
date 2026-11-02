#!/usr/bin/env python3
"""Package native x64 Windows binaries; portable staging never creates a ZIP."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import struct
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("_herspers_packaging_common", PROJECT / "tools/package_macos.py")
_common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_common)

BINARIES = ("horizon-client.exe", "horizon-ctl.exe", "horizon-prepare.exe")
LAUNCHER = "Herspers-Minecraft.exe"
FOLDER = "Herspers-Minecraft"
ARCHIVE = "herspers-minecraft-windows-x86_64.zip"
HELPERS = ("Setup.cmd", "Play.cmd")
PRODUCT_VERSION = "0.2.1"
MIN_CLIENT_STACK_RESERVE = 16 * 1024 * 1024

# Policy adapted from Horizon's MIT-licensed tools/check_imports.py, copyright
# Ludovic Marie and contributors. Original license is retained in licenses/.
WINDOWS_SYSTEM = {
    "advapi32.dll", "bcrypt.dll", "bcryptprimitives.dll", "cfgmgr32.dll", "combase.dll",
    "comctl32.dll", "comdlg32.dll", "crypt32.dll", "d2d1.dll", "d3d11.dll", "d3d12.dll",
    "d3dcompiler_47.dll", "dbghelp.dll", "dcomp.dll", "dwmapi.dll", "dwrite.dll", "dxgi.dll",
    "gdi32.dll", "hid.dll", "icuuc.dll", "imm32.dll", "iphlpapi.dll", "kernel32.dll",
    "kernelbase.dll", "mfplat.dll", "mmdevapi.dll", "msvcrt.dll", "ncrypt.dll", "ntdll.dll",
    "ole32.dll", "oleaut32.dll", "opengl32.dll", "propsys.dll", "secur32.dll", "setupapi.dll",
    "shcore.dll", "shell32.dll", "shlwapi.dll", "ucrtbase.dll", "user32.dll", "userenv.dll",
    "uxtheme.dll", "version.dll", "winmm.dll", "ws2_32.dll", "xinput1_4.dll",
}


def _range(data: bytes, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError("PE range extends beyond the file")
    return data[offset:offset + size]


def inspect_pe(data: bytes) -> dict:
    """Read PE64 architecture and normal/delay imports without running code."""
    if _range(data, 0, 2) != b"MZ":
        raise ValueError("expected a Windows PE executable")
    pe = struct.unpack("<I", _range(data, 0x3C, 4))[0]
    if _range(data, pe, 4) != b"PE\0\0":
        raise ValueError("invalid PE signature")
    machine, count = struct.unpack("<HH", _range(data, pe + 4, 4))
    optional_size, flags = struct.unpack("<HH", _range(data, pe + 20, 4))
    if machine != 0x8664:
        raise ValueError("expected an x86_64 PE executable")
    if flags & 0x2000 or not flags & 0x0002:
        raise ValueError("expected an executable, not a DLL")
    if count < 1 or count > 96 or optional_size < 112:
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
        values = bytearray()
        for index in range(260):
            value = data[offset(rva + index)]
            if value == 0:
                break
            values.append(value)
        else:
            raise ValueError("PE DLL name is too long or unterminated")
        try:
            name = values.decode("ascii").lower()
        except UnicodeDecodeError as error:
            raise ValueError("PE DLL name is not ASCII") from error
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
                raise ValueError("unsupported non-RVA PE delay-import descriptor")
            name_rva = struct.unpack_from("<I", descriptor, name_field)[0]
            names.add(dll_name(name_rva))
        else:
            raise ValueError("unterminated PE import table")
    foreign = sorted(name for name in names if name not in WINDOWS_SYSTEM
                     and not name.startswith(("api-ms-win-", "ext-ms-win-")))
    if foreign:
        raise ValueError("unbundled non-system DLL imports: " + ", ".join(foreign))
    stack_reserve, stack_commit = struct.unpack("<QQ", _range(data, optional + 72, 16))
    return {"format": "PE32+", "architecture": "x86_64", "imports": sorted(names),
            "stack_reserve_bytes": stack_reserve, "stack_commit_bytes": stack_commit}


def verify_binary(path: Path) -> dict:
    _common.checked_file(path)
    if path.stat().st_size > 512 * 1024 * 1024:
        raise ValueError(f"binary exceeds size limit: {path.name}")
    data = path.read_bytes()
    try:
        result = inspect_pe(data)
    except ValueError as error:
        raise ValueError(f"{path.name}: {error}") from error
    result["sha256"] = hashlib.sha256(data).hexdigest()
    return result


def assemble(source: Path, binaries: Path, launcher: Path, output: Path,
             stage_only: bool = False) -> tuple[Path, Path | None]:
    source, binaries, launcher, output = (p.resolve() for p in (source, binaries, launcher, output))
    if output.is_relative_to(source):
        raise ValueError("output must be outside the upstream source directory")
    if not stage_only and platform.system() != "Windows":
        raise ValueError("real packaging requires Windows; --stage-only is unverified assembly only")
    inputs = _common.source_inputs(source)
    notices = _common.license_files(source)
    verified = {name: verify_binary(binaries / name) for name in BINARIES}
    if verified["horizon-client.exe"]["stack_reserve_bytes"] < MIN_CLIENT_STACK_RESERVE:
        raise ValueError("horizon-client.exe needs at least a 16 MiB main-thread stack reserve; "
                         "rebuild with scripts/build_windows.ps1")
    verified[LAUNCHER] = verify_binary(launcher)
    project_license = _common.checked_file(PROJECT / "LICENSE")
    project_lock = _common.checked_file(PROJECT / "upstream.lock.json")
    guide = _common.checked_file(PROJECT / "docs/INSTALL-WINDOWS.md")
    helpers = [_common.checked_file(PROJECT / "packaging/windows" / name) for name in HELPERS]
    destination, archive = output / FOLDER, output / ARCHIVE
    if destination.exists() or destination.is_symlink() or archive.exists():
        raise ValueError("output already contains this package; choose a fresh output directory")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".herspers-windows-", dir=output) as temporary:
        package = Path(temporary) / FOLDER
        (package / "bin").mkdir(parents=True)
        for name in BINARIES:
            shutil.copy2(binaries / name, package / "bin" / name)
        shutil.copy2(launcher, package / LAUNCHER)
        _common.copy_files(inputs, source, package / "preparation")
        _common.copy_files(notices, source, package / "licenses/upstream")
        shutil.copy2(project_license, package / "LICENSE")
        shutil.copy2(project_lock, package / "upstream.lock.json")
        shutil.copy2(guide, package / "INSTALL-WINDOWS.txt")
        for helper in helpers:
            shutil.copy2(helper, package / helper.name)
        preparation_hash = hashlib.sha256()
        for path in sorted(inputs):
            preparation_hash.update(str(path.relative_to(source)).replace("\\", "/").encode())
            preparation_hash.update(b"\0")
            preparation_hash.update(path.read_bytes())
        (package / "preparation-id.txt").write_text(preparation_hash.hexdigest() + "\n")
        metadata = {"product_version": PRODUCT_VERSION, "architecture": "x86_64", "stage_only": stage_only,
                    "windows_runtime_tested": False, "game_resources_included": False,
                    "code_signed": False, "binaries": verified}
        (package / "build-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        status = ("STAGED ONLY: UNVERIFIED ASSEMBLY, NOT A WORKING WINDOWS BUILD.\n" if stage_only
                  else "Packaged native Windows binaries. Unsigned; gameplay has not been verified.\n")
        (package / "BUILD-STATUS.txt").write_text(status + "Run Herspers-Minecraft.exe --setup before playing.\n")
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
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    try:
        package, archive = assemble(args.source, args.binaries, args.launcher, args.output, args.stage_only)
    except (OSError, ValueError) as error:
        parser.exit(1, f"package_windows: {error}\n")
    print(f"{'STAGED ONLY (unverified)' if args.stage_only else 'Packaged (unsigned)'}: {package}")
    if archive:
        print(f"ZIP: {archive}\nResource preparation and Windows gameplay testing remain required.")


if __name__ == "__main__":
    main()
