"""Validate exact renderer overlays without modifying the immutable source cache."""
import hashlib
import json
from pathlib import Path
import unittest

from tools.prepare_upstream import apply_patch

ROOT = Path(__file__).resolve().parents[1]


class DistantTerrainPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = {e['path']: e for e in json.loads((ROOT / 'patches/upstream.json').read_text())['files']}

    def new_source(self, path):
        entry = self.entries[path]
        self.assertIsNone(entry['before_sha256'])
        raw = apply_patch(b'', (ROOT / 'patches' / entry['patch']).read_bytes(), path, new_file=True)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['after_sha256'])
        return raw.decode()

    def test_new_modules_are_exact_original_source_patches(self):
        for path in ['crates/horizon-client-render/src/lod/observed.rs',
                     'crates/horizon-client-render/src/lod/visited_cache.rs',
                     'crates/horizon-client/src/game/visited_lod.rs']:
            self.assertTrue(self.new_source(path))

    def test_received_source_never_generates_or_requests_network_data(self):
        source = self.new_source('crates/horizon-client-render/src/lod/observed.rs')
        source = source.split('#[cfg(test)]')[0]
        for forbidden in ['ChunkGenerator', '.send(', 'std::process', 'Command::', 'unsafe {']:
            self.assertNotIn(forbidden, source)
        self.assertIn('impl LodSource for ObservedSource', source)
        self.assertIn('self.cache.put', source)

    def test_cache_and_profile_namespace_stay_outside_world_saves(self):
        source = self.new_source('crates/horizon-client/src/game/visited_lod.rs')
        self.assertIn('herps-lod-cache/v1', source)
        self.assertIn('canonical.to_string_lossy(), self.visited_lod_seed', source)
        self.assertIn('self.dim.id()', source)
        self.assertIn('state.properties.hash', source)
        self.assertIn('biome.name.hash', source)
        for forbidden in ['save_game(', 'server.properties', 'AuthSession', '.hnmod', '.hmod']:
            self.assertNotIn(forbidden, source)

    def test_enabled_default_and_limits_are_declared(self):
        entry = self.entries['crates/horizon-client-render/src/graphics.rs']
        patch = (ROOT / 'patches' / entry['patch']).read_text()
        self.assertIn('visited_lod: false', patch)
        for key in ['visitedLod', 'visitedLodRadius', 'lodMemoryMiB', 'lodDiskMiB', 'lodWorkers']:
            self.assertIn(key, patch)


if __name__ == '__main__':
    unittest.main()
