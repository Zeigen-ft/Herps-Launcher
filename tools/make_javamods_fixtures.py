#!/usr/bin/env python3
"""Create owned synthetic test archives locally; never compile or execute Java."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile


def make_jar(path: Path, *, loader="fabric", mod_id="demo", version="1", depends=None,
             mixins=False, access=False, invalid_class=False, license="MIT",
             minecraft="26.3", content=True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dependencies = {"minecraft": minecraft, **(depends or {})}
    files = {}
    if loader == "fabric":
        metadata = {"schemaVersion": 1, "id": mod_id, "name": f"Owned {mod_id} fixture",
                    "version": version, "license": license, "depends": dependencies}
        if mixins:
            metadata["mixins"] = ["owned.mixins.json"]
        if access:
            metadata["accessWidener"] = "owned.accesswidener"
        files["fabric.mod.json"] = json.dumps(metadata)
    elif loader in ("forge", "neoforge"):
        lines = [f'modLoader="javafml"', f'license={json.dumps(license)}', '[[mods]]',
                 f'modId={json.dumps(mod_id)}', f'displayName={json.dumps("Owned " + mod_id + " fixture")}',
                 f'version={json.dumps(version)}']
        for dep, constraint in dependencies.items():
            lines += [f'[[dependencies.{mod_id}]]', f'modId={json.dumps(dep)}', 'mandatory=true',
                      'type="required"', f'versionRange={json.dumps(constraint)}']
        if mixins:
            lines += ['[[mixins]]', 'config="owned.mixins.json"']
        files["META-INF/neoforge.mods.toml" if loader == "neoforge" else "META-INF/mods.toml"] = "\n".join(lines) + "\n"
        if access:
            files["META-INF/accesstransformer.cfg"] = "# owned fixture\n"
    else:
        raise ValueError("Fixture loader must be fabric, forge, or neoforge")
    if mixins:
        files["owned.mixins.json"] = '{"required":true,"mixins":["Owned"]}'
    if access and loader == "fabric":
        files["owned.accesswidener"] = "accessWidener v2 named\n"
    if invalid_class:
        files[f"{mod_id}/Owned.class"] = b"deliberately invalid owned class bytes"
    if content:
        files[f"data/{mod_id}/recipe/owned.json"] = json.dumps({
            "type": "minecraft:crafting_shapeless", "ingredients": ["minecraft:red_dye"],
            "result": {"id": "minecraft:red_dye"}})
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for name, data in files.items():
            zipped.writestr(name, data)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for loader in ("fabric", "forge", "neoforge"):
        make_jar(args.output / f"{loader}-content.jar", loader=loader)
    make_jar(args.output / "false-positive-works.jar", depends={"missinglib": ">=2"},
             mixins=True, access=True, invalid_class=True)


if __name__ == "__main__":
    main()
