#!/usr/bin/env python3
"""Embed/verify the supplied ICO in fresh unsigned Windows build outputs only.

LoadLibraryEx uses LOAD_LIBRARY_AS_DATAFILE: verification never executes the EXE.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import struct
import sys


def frames(raw: bytes):
    if len(raw) < 6 or len(raw) > 4 * 1024 * 1024:
        raise ValueError("Invalid ICO size")
    reserved, kind, count = struct.unpack_from("<HHH", raw)
    if reserved or kind != 1 or not 1 <= count <= 32 or 6 + count * 16 > len(raw):
        raise ValueError("Expected an ICO container, not an image renamed .ico")
    result = []
    for n in range(count):
        width, height, colors, zero, planes, bits, length, offset = struct.unpack_from("<BBBBHHII", raw, 6 + n * 16)
        if zero or not length or offset < 6 + count * 16 or offset + length > len(raw):
            raise ValueError("Invalid ICO image range")
        result.append(((width, height, colors, zero, planes, bits), raw[offset:offset + length]))
    return result


def kernel():
    if sys.platform != "win32":
        raise RuntimeError("Windows is required for actual executable resource verification")
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "BeginUpdateResourceW": ([w.LPCWSTR, w.BOOL], w.HANDLE),
        "UpdateResourceW": ([w.HANDLE, ctypes.c_void_p, ctypes.c_void_p, w.WORD, ctypes.c_void_p, w.DWORD], w.BOOL),
        "EndUpdateResourceW": ([w.HANDLE, w.BOOL], w.BOOL),
        "LoadLibraryExW": ([w.LPCWSTR, w.HANDLE, w.DWORD], w.HMODULE),
        "FindResourceW": ([w.HMODULE, ctypes.c_void_p, ctypes.c_void_p], w.HANDLE),
        "LoadResource": ([w.HMODULE, w.HANDLE], w.HANDLE),
        "SizeofResource": ([w.HMODULE, w.HANDLE], w.DWORD),
        "LockResource": ([w.HANDLE], ctypes.c_void_p),
        "FreeLibrary": ([w.HMODULE], w.BOOL),
    }
    for name, (args, result) in signatures.items():
        getattr(k, name).argtypes = args
        getattr(k, name).restype = result
    return k


def embed(exe: Path, icon: bytes):
    images = frames(icon)
    k = kernel()
    handle = k.BeginUpdateResourceW(str(exe.resolve()), False)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    commit = False
    try:
        group = struct.pack("<HHH", 0, 1, len(images))
        resources = []
        for index, (metadata, image) in enumerate(images, 1):
            group += struct.pack("<BBBBHHIH", *metadata, len(image), index)
            resources.append((3, index, image))
        resources.append((14, 1, group))
        for kind, identifier, raw in resources:
            buffer = ctypes.create_string_buffer(raw)
            if not k.UpdateResourceW(handle, kind, identifier, 0, buffer, len(raw)):
                raise ctypes.WinError(ctypes.get_last_error())
        commit = True
    finally:
        if not k.EndUpdateResourceW(handle, not commit):
            raise ctypes.WinError(ctypes.get_last_error())


def verify(exe: Path, icon: bytes):
    expected = frames(icon)
    k = kernel()
    module = k.LoadLibraryExW(str(exe.resolve()), None, 2)
    if not module:
        raise ctypes.WinError(ctypes.get_last_error())
    def read(kind, identifier):
        resource = k.FindResourceW(module, identifier, kind)
        if not resource:
            raise ctypes.WinError(ctypes.get_last_error())
        size = k.SizeofResource(module, resource)
        loaded = k.LoadResource(module, resource)
        address = k.LockResource(loaded)
        if not address or not size:
            raise ValueError("Empty icon resource")
        return ctypes.string_at(address, size)
    try:
        group = read(14, 1)
        if len(group) != 6 + 14 * len(expected) or struct.unpack_from("<HHH", group) != (0, 1, len(expected)):
            raise ValueError("Executable icon group does not match supplied ICO")
        for n, (metadata, raw) in enumerate(expected):
            entry = struct.unpack_from("<BBBBHHIH", group, 6 + 14 * n)
            if entry[:2] != metadata[:2] or read(3, entry[-1]) != raw:
                raise ValueError("Executable icon image differs from supplied ICO")
    finally:
        k.FreeLibrary(module)
    return dict(status="passed",frames=len(expected),icon_sha256=hashlib.sha256(icon).hexdigest(),
                executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                executable=exe.name,executed_executable=False,physical_visual_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--icon", required=True, type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.executable.is_symlink() or not args.executable.is_file():
        raise ValueError("Expected a regular build output executable")
    icon = args.icon.read_bytes()
    frames(icon)
    if not args.verify_only:
        embed(args.executable, icon)
    report = verify(args.executable, icon)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
