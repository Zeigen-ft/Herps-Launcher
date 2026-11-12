#!/usr/bin/env python3
"""Regenerate committed icon containers from the user's unchanged PNG artwork.

Developer-only conversion: Pillow is not a launcher/runtime dependency.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    from PIL import Image, __version__
    source = ROOT / "packaging/icons/game-source.png"
    if hashlib.sha256(source.read_bytes()).hexdigest() != "a2e0fda7cd2d16507cc29221495476d1da75d811a77229217e8e641e9aa31965":
        raise ValueError("Icon source differs from the user-supplied artwork; review before rebuilding")
    output = ROOT / "patches/assets"
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.load()
        image = image.convert("RGBA")
        image.resize((64,64),Image.Resampling.LANCZOS).save(output/"game-window.png",format="PNG")
        image.save(output/"game.ico",format="ICO",sizes=[(n,n)for n in (16,20,24,32,40,48,64,128,256)])
        image.resize((1024,1024),Image.Resampling.LANCZOS).save(output/"game.icns",format="ICNS")
    paths = [source, output/"game-window.png", output/"game.icns", output/"game.ico"]
    files = {p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in paths}
    report = dict(source="User-supplied download.ico; file signature identifies original as 1254x1254 RGBA PNG",
                  conversion="Artwork preserved; standard resampling and icon container encoding only",pillow=__version__,files=files)
    (ROOT/"packaging/icons/provenance.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("Regenerated game icons; verify/update the pinned asset hashes before building.")


if __name__ == "__main__":
    main()
