#!/usr/bin/env python3
"""Generate original modpack fixtures locally; never run Java or ship mod JARs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.make_javamods_fixtures import make_jar


def mrpack(path: Path, jars: list[Path], *, missing=0, bad_hash=False, embedded=False,
           hash_algorithm="sha1", conflicting_hash=False) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    files = []
    for index, jar in enumerate(jars):
        data = Path(jar).read_bytes()
        if hash_algorithm not in ("sha1", "sha512"):
            raise ValueError("Fixture hash must be sha1 or sha512")
        value = hashlib.new(hash_algorithm, data).hexdigest()
        if bad_hash and index == 0:
            value = "0" * len(value)
        hashes = {hash_algorithm: value}
        if conflicting_hash:
            hashes = {"sha1": hashlib.sha1(data).hexdigest(), "sha512": "0" * 128}
        files.append({"path": "mods/" + Path(jar).name, "hashes": hashes,
                      "downloads": [], "fileSize": len(data), "env": {"client": "required", "server": "required"}})
    for index in range(missing):
        files.append({"path": f"mods/missing-{index}.jar", "hashes": {"sha1": hashlib.sha1(f"missing{index}".encode()).hexdigest()},
                      "downloads": [], "fileSize": 1})
    value = {"formatVersion": 1, "game": "minecraft", "versionId": "1",
             "name": "Owned Modrinth fixture", "dependencies": {"minecraft": "26.3"}, "files": files}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("modrinth.index.json", json.dumps(value))
        if embedded:
            for jar in jars:
                zipped.write(jar, "overrides/mods/" + Path(jar).name)
    return path


def curseforge(path: Path, jars: list[Path], *, include_modlist=False, omitted_manifest=0) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    files = [{"projectID": 100 + i, "fileID": 200 + i, "required": True}
             for i in range(len(jars) + omitted_manifest)]
    manifest = {"minecraft": {"version": "26.3", "modLoaders": []}, "manifestType": "minecraftModpack",
                "manifestVersion": 1, "name": "Owned CurseForge fixture", "version": "1", "author": "Owned fixture",
                "files": files, "overrides": "overrides"}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("manifest.json", json.dumps(manifest))
        if include_modlist:
            modlist = {}
            for jar in jars:
                modlist[Path(jar).name] = {"jarName": Path(jar).name,
                    "modrinthHash": hashlib.sha1(Path(jar).read_bytes()).hexdigest()}
            zipped.writestr("overrides/config/crash_assistant/modlist.json", json.dumps(modlist))
    return path


def local_cf_instance(directory: Path, jars: list[Path]) -> Path:
    directory = instance(directory, jars)
    value = {"installedAddons": [{"addonID": 100 + i, "installedFile": {"id": 200 + i,
        "fileName": Path(jar).name}} for i, jar in enumerate(jars)]}
    (directory / "minecraftinstance.json").write_text(json.dumps(value), encoding="utf-8")
    return directory


def instance(directory: Path, jars: list[Path]) -> Path:
    directory = Path(directory)
    (directory / ".minecraft/mods").mkdir(parents=True, exist_ok=True)
    (directory / "mmc-pack.json").write_text(json.dumps({"formatVersion": 1,
        "components": [{"uid": "net.minecraft", "version": "26.3"}]}), encoding="utf-8")
    (directory / "instance.cfg").write_text("[General]\nname=Owned Prism fixture\n", encoding="utf-8")
    for jar in jars:
        shutil.copyfile(jar, directory / ".minecraft/mods" / Path(jar).name)
    return directory


def packwiz(directory: Path) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "pack.toml").write_text('name="Owned packwiz fixture"\npack-format="packwiz:1.1.0"\n'
        '[index]\nfile="index.toml"\nhash-format="sha256"\nhash="owned"\n[versions]\nminecraft="26.3"\n', encoding="utf-8")
    (directory / "index.toml").write_text('hash-format="sha256"\nfiles=[]\n', encoding="utf-8")
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    jars = args.output / "user-mods"
    good = make_jar(jars / "good.jar", mod_id="good")
    unsupported = make_jar(jars / "unsupported.jar", mod_id="unsupported",
                           depends={"missinglib": "*"}, mixins=True, invalid_class=True)
    mrpack(args.output / "complete.mrpack", [good])
    mrpack(args.output / "partial.mrpack", [good, unsupported], missing=1)
    mrpack(args.output / "bad-hash.mrpack", [good], bad_hash=True)
    mrpack(args.output / "embedded.mrpack", [good], embedded=True)
    curseforge(args.output / "curseforge.zip", [good])
    curseforge(args.output / "curseforge-incomplete-modlist.zip", [good], include_modlist=True, omitted_manifest=1)
    local_cf_instance(args.output / "curseforge-instance", [good])
    instance(args.output / "prism-instance", [good, unsupported])
    packwiz(args.output / "packwiz")


if __name__ == "__main__":
    main()
