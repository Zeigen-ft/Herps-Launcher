#!/usr/bin/env python3
"""Build an experimental, data-only Herps 26.3 server lighting pack and installer.

AGPL-3.0-only. Adapted from quillphen's Dynamic Lighting 1.0 (see NOTICE).
No Java bytecode, original JAR, OptiFine, or game resources are distributed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACK_NAME = "Herps-Server-Dynamic-Lighting-0.1.0.zip"
BUNDLE_NAME = "Herps-Server-Dynamic-Lighting-0.1.0-Windows-Test.zip"
SOURCE_SHA256 = "f4c66fc343c03532be4028859e8a0bd510c182348b8649b63301865f99239e82"
LEVELS = {
    15: ["glowstone", "sea_lantern", "lantern", "jack_o_lantern", "shroomlight", "beacon",
         "verdant_froglight", "pearlescent_froglight", "ochre_froglight"],
    14: ["torch", "campfire", "lava_bucket", "end_rod"],
    10: ["soul_torch", "soul_lantern", "soul_campfire", "redstone_torch", "glow_berries"],
    7: ["blaze_rod", "blaze_powder", "glowstone_dust", "glow_ink_sac"],
}
DIMENSIONS = ["overworld", "the_nether", "the_end"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pack_files():
    files = {}

    def add(path, value):
        if not isinstance(value, str):
            value = json.dumps(value, indent=2) + "\n"
        files[path] = value.encode("utf-8")

    def function(name, lines):
        add(f"data/herps_dl/function/{name}.mcfunction", "\n".join(lines) + "\n")

    add("pack.mcmeta", {"pack": {"pack_format": 121,
        "description": "Herps 26.3 experimental server lighting 0.1.0 (disabled until enabled)"}})
    for event in ["load", "tick"]:
        add(f"data/minecraft/tags/function/{event}.json", {"values": [f"herps_dl:{event}"]})
    for level, items in LEVELS.items():
        add(f"data/herps_dl/tags/item/level{level}.json",
            {"values": ["minecraft:" + item for item in items]})
    function("load", [
        "scoreboard objectives add herps_dl dummy",
        "execute unless score #enabled herps_dl matches 0..1 run scoreboard players set #enabled herps_dl 0",
    ])
    function("enable", ["scoreboard players set #enabled herps_dl 1"])
    cleanup = [f"execute in minecraft:{dim} as @e[type=minecraft:marker,tag=herps_dl.owned] at @s run function herps_dl:remove"
               for dim in DIMENSIONS]
    function("disable", ["scoreboard players set #enabled herps_dl 0", *cleanup])
    # Cleanup runs even while disabled, including saved markers when chunks reload.
    function("tick", [*cleanup,
        "execute if score #enabled herps_dl matches 1 run function herps_dl:sources"])
    sources = []
    # Higher tiers run first globally: shared positions keep the strongest source.
    for level in LEVELS:
        sources += [
            f"execute as @a at @s if items entity @s weapon.* #herps_dl:level{level} positioned ~ ~1 ~ run function herps_dl:place{level}",
            f"execute as @a at @s as @e[type=minecraft:item,distance=..24,limit=32,sort=nearest] at @s if items entity @s contents #herps_dl:level{level} run function herps_dl:place{level}",
        ]
    function("sources", sources)
    # Only ordinary air is eligible. Never replace water, solid blocks, existing
    # lights, cave_air, or void_air. No broad fill and no teleport/search side effects.
    for level in LEVELS:
        function(f"place{level}", [
            f"execute align xyz positioned ~0.5 ~ ~0.5 if block ~ ~ ~ minecraft:air run function herps_dl:claim{level}"])
        function(f"claim{level}", [
            # If summon fails (e.g. entity limit), do not leave an unowned light.
            "execute store success score #claimed herps_dl run summon minecraft:marker ~ ~ ~ "
            f'{{Tags:["herps_dl.owned","herps_dl.level{level}"]}}',
            f"execute if score #claimed herps_dl matches 1 run setblock ~ ~ ~ minecraft:light[level={level},waterlogged=false]",
        ])
    function("remove", [
        f"execute if entity @s[tag=herps_dl.level{level}] if block ~ ~ ~ minecraft:light[level={level},waterlogged=false] run setblock ~ ~ ~ minecraft:air"
        for level in LEVELS
    ] + ["kill @s"])
    add("NOTICE.txt", (ROOT / "content/server-lighting/NOTICE.txt").read_text())
    add("LICENSE.txt", (ROOT / "licenses/server-lighting-AGPL-3.0.txt").read_text())
    return files


def zip_bytes(files):
    import io
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            # ZipInfo otherwise records the build host (Windows=0, Unix=3),
            # changing checksums despite byte-identical source and contents.
            entry.create_system = 3
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return output.getvalue()


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    pack = zip_bytes(pack_files())
    installer = (ROOT / "packaging/server-lighting/Install-Lighting.ps1").read_text()
    installer = installer.replace("@PACK_SHA256@", digest(pack)).replace("@PACK_NAME@", PACK_NAME)
    bundle = {PACK_NAME: pack, "Install-Lighting.ps1": installer.encode(),
        "Install-Lighting.cmd": (ROOT / "packaging/server-lighting/Install-Lighting.cmd").read_bytes(),
        "README.txt": (ROOT / "docs/SERVER-DYNAMIC-LIGHTING.md").read_bytes(),
        "NOTICE.txt": (ROOT / "content/server-lighting/NOTICE.txt").read_bytes(),
        "LICENSE.txt": (ROOT / "licenses/server-lighting-AGPL-3.0.txt").read_bytes(),
        # Complete preferred source for this data-only adaptation and installer.
        "source/build_server_lighting.py": Path(__file__).read_bytes(),
        "source/packaging/server-lighting/Install-Lighting.ps1": (ROOT / "packaging/server-lighting/Install-Lighting.ps1").read_bytes(),
        "source/packaging/server-lighting/Install-Lighting.cmd": (ROOT / "packaging/server-lighting/Install-Lighting.cmd").read_bytes(),
        "source/content/server-lighting/NOTICE.txt": (ROOT / "content/server-lighting/NOTICE.txt").read_bytes(),
        "source/licenses/server-lighting-AGPL-3.0.txt": (ROOT / "licenses/server-lighting-AGPL-3.0.txt").read_bytes(),
        "source/docs/SERVER-DYNAMIC-LIGHTING.md": (ROOT / "docs/SERVER-DYNAMIC-LIGHTING.md").read_bytes(),
    }
    # Preserve the relative tools/ layout so the included source rebuilds as-is.
    bundle["source/tools/build_server_lighting.py"] = bundle.pop("source/build_server_lighting.py")
    bundle["SHA256SUMS.txt"] = "".join(f"{digest(data)}  {name}\n" for name, data in sorted(bundle.items())).encode()
    result = zip_bytes(bundle)
    (output / PACK_NAME).write_bytes(pack)
    (output / BUNDLE_NAME).write_bytes(result)
    (output / "SHA256SUMS.txt").write_text(f"{digest(pack)}  {PACK_NAME}\n{digest(result)}  {BUNDLE_NAME}\n")
    print(json.dumps({"pack": PACK_NAME, "pack_sha256": digest(pack),
        "bundle": BUNDLE_NAME, "bundle_sha256": digest(result)}, indent=2))
    return pack, result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/server-lighting")
    build(parser.parse_args().output)
