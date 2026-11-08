"""Actual original progression policy and engine source contract; not gameplay."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.prepare_upstream import apply_patch

ROOT = Path(__file__).resolve().parents[1]


class WoodcuttingRulesTests(unittest.TestCase):
    def test_engine_patches_embed_reviewed_sources_without_changing_hook_api(self):
        manifest = json.loads((ROOT / "patches/upstream.json").read_text())
        files = {e["path"]: e for e in manifest["files"]}
        for canonical, patched in [("rules", "herspers_woodcutting_rules"), ("adapter", "herspers_woodcutting")]:
            path = f"crates/horizon-client/src/game/{patched}.rs"
            entry = files[path]
            self.assertIsNone(entry["before_sha256"])
            actual = apply_patch(b"", (ROOT / "patches" / entry["patch"]).read_bytes(), path, new_file=True)
            self.assertEqual(actual, (ROOT / f"native/rlcraft_woodcutting/{canonical}.rs").read_bytes().replace(b"\r\n", b"\n"))
        patch = (ROOT / "patches" / files["crates/horizon-client/src/game/native_hooks.rs"]["patch"]).read_text()
        self.assertNotIn("NATIVE_HOOKS_API", patch)
        self.assertIn("self.herspers_woodcutting_guard(state, canceled)", patch)

    @unittest.skipUnless(shutil.which("rustc"), "Pinned Rust tools required for native rule execution")
    def test_nine_progression_cases_pass_without_skips(self):
        with tempfile.TemporaryDirectory(prefix="owned-woodcutting-rules-") as directory:
            binary = Path(directory) / ("rules.exe" if os.name == "nt" else "rules")
            subprocess.run(["rustc", "+1.95.0", "--edition", "2024", "--test",
                str(ROOT / "native/rlcraft_woodcutting/rules.rs"), "-o", str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
            self.assertIn("9 passed; 0 failed; 0 ignored", result.stdout)
