"""Actual original Rust transaction rules on owned doubles, not gameplay."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.prepare_upstream import apply_patch

ROOT = Path(__file__).resolve().parents[1]


class GatheringRulesTests(unittest.TestCase):
    def test_engine_patches_embed_reviewed_sources_without_changing_hook_api(self):
        manifest = json.loads((ROOT / "patches/upstream.json").read_text())
        files = {e["path"]: e for e in manifest["files"]}
        for canonical, patched in [("rules", "herspers_gathering_rules"), ("adapter", "herspers_gathering")]:
            path = f"crates/horizon-client/src/game/{patched}.rs"
            entry = files[path]
            self.assertIsNone(entry["before_sha256"])
            actual = apply_patch(b"", (ROOT / "patches" / entry["patch"]).read_bytes(), path, new_file=True)
            self.assertEqual(actual, (ROOT / f"native/rlcraft_gathering/{canonical}.rs").read_bytes().replace(b"\r\n", b"\n"))
        patch = (ROOT / "patches" / files["crates/horizon-client/src/game/native_hooks.rs"]["patch"]).read_text()
        self.assertNotIn("NATIVE_HOOKS_API", patch)
        self.assertIn("self.herspers_gathering_use_on(stack, pos, face, claimed)", patch)

    @unittest.skipUnless(shutil.which("rustc"), "Pinned Rust tools required for native rule execution")
    def test_twelve_transaction_cases_pass_without_skips(self):
        with tempfile.TemporaryDirectory(prefix="owned-gathering-rules-") as directory:
            binary = Path(directory) / ("rules.exe" if os.name == "nt" else "rules")
            subprocess.run(["rustc", "+1.95.0", "--edition", "2024", "--test",
                str(ROOT / "native/rlcraft_gathering/rules.rs"), "-o", str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
            self.assertIn("12 passed; 0 failed; 0 ignored", result.stdout)
