import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile

from tools.build_server_lighting import build, pack_files, zip_bytes, LEVELS, PACK_NAME, BUNDLE_NAME


class ServerLightingTests(unittest.TestCase):
    def test_function_and_item_tag_dependency_closure(self):
        files = pack_files()
        functions = {name.removeprefix('data/herps_dl/function/').removesuffix('.mcfunction')
                     for name in files if name.endswith('.mcfunction')}
        for name, data in files.items():
            if name.endswith('.json') or name == 'pack.mcmeta':
                json.loads(data)
            if name.endswith('.mcfunction'):
                text = data.decode()
                for function in re.findall(r'\bfunction herps_dl:([\w/]+)', text):
                    self.assertIn(function, functions, name)
                for tag in re.findall(r'#herps_dl:(\w+)', text):
                    self.assertIn(f'data/herps_dl/tags/item/{tag}.json', files)
        for event in ['load', 'tick']:
            self.assertEqual(json.loads(files[f'data/minecraft/tags/function/{event}.json'])['values'],
                             [f'herps_dl:{event}'])

    def test_mutation_boundary_and_cleanup(self):
        files = pack_files()
        functions = {name: data.decode() for name, data in files.items() if name.endswith('.mcfunction')}
        # No arbitrary block-volume edits, Java payload, legacy function, or original unsafe disable.
        for name, text in functions.items():
            for line in text.splitlines():
                self.assertNotRegex(line, r'(^|run )(fill|tp|data|setworldspawn)\b', name)
        self.assertFalse(any(n.endswith(('.class', '.jar', '.exe', '.wasm')) for n in files))
        for level in LEVELS:
            place = files[f'data/herps_dl/function/place{level}.mcfunction'].decode()
            self.assertIn('if block ~ ~ ~ minecraft:air run function', place)
            claim = files[f'data/herps_dl/function/claim{level}.mcfunction'].decode().splitlines()
            self.assertIn('execute store success score #claimed', claim[0])
            self.assertIn('if score #claimed herps_dl matches 1 run setblock', claim[1])
        for name in ['tick', 'disable']:
            text = files[f'data/herps_dl/function/{name}.mcfunction'].decode()
            for dimension in ['overworld', 'the_nether', 'the_end']:
                self.assertIn(f'in minecraft:{dimension} as @e[type=minecraft:marker,tag=herps_dl.owned]', text)
        remove = files['data/herps_dl/function/remove.mcfunction'].decode()
        for level in LEVELS:
            self.assertIn(f'if entity @s[tag=herps_dl.level{level}] if block ~ ~ ~ minecraft:light[level={level},waterlogged=false]', remove)

    def test_defaults_priority_and_bounded_drops(self):
        files = pack_files()
        load = files['data/herps_dl/function/load.mcfunction'].decode()
        self.assertIn('unless score #enabled herps_dl matches 0..1', load)
        self.assertTrue(load.rstrip().endswith('herps_dl 0'))
        sources = files['data/herps_dl/function/sources.mcfunction'].decode().splitlines()
        self.assertEqual([int(re.search(r'place(\d+)$', line)[1]) for line in sources],
                         [15, 15, 14, 14, 10, 10, 7, 7])
        self.assertEqual(sum('distance=..24,limit=32,sort=nearest' in line for line in sources), 4)
        all_items = [item for items in LEVELS.values() for item in items]
        self.assertEqual(len(all_items), len(set(all_items)))

    def test_reproducible_bundle_and_complete_source(self):
        with tempfile.TemporaryDirectory() as directory:
            pack, bundle = build(Path(directory))
            self.assertEqual(pack, zip_bytes(pack_files()))
            self.assertEqual((Path(directory) / PACK_NAME).read_bytes(), pack)
            self.assertEqual((Path(directory) / BUNDLE_NAME).read_bytes(), bundle)
            with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
                self.assertTrue(all(entry.create_system == 3 for entry in archive.infolist()))
                with zipfile.ZipFile(io.BytesIO(pack)) as inner:
                    self.assertTrue(all(entry.create_system == 3 for entry in inner.infolist()))
                sums = archive.read('SHA256SUMS.txt').decode()
                for line in sums.splitlines():
                    expected, name = line.split('  ', 1)
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected)
                self.assertIn(hashlib.sha256(pack).hexdigest(), archive.read('Install-Lighting.ps1').decode())
                # Rebuild solely from the preferred source shipped to users.
                for name in archive.namelist():
                    if name.startswith('source/'):
                        archive.extract(name, directory)
            import subprocess
            import sys
            subprocess.run([sys.executable, str(Path(directory) / 'source/tools/build_server_lighting.py'),
                            '--output', str(Path(directory) / 'rebuilt')], check=True, capture_output=True)
            self.assertEqual((Path(directory) / 'rebuilt' / BUNDLE_NAME).read_bytes(), bundle)


if __name__ == '__main__':
    unittest.main()
