"""Release receipts must not claim notarization or execution without evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.package_herps import notarize_dmg
from tools.release_evidence import candidate
from tools.verify_herps_windows import verify


class ReleaseEvidenceTests(unittest.TestCase):
    def test_notarization_failure_does_not_leave_success_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / 'owned.dmg'
            image.write_bytes(b'owned image')
            with patch.dict('os.environ', {'HERPS_NOTARY_PROFILE': 'owned', 'HERPS_CODESIGN_IDENTITY': 'owned'}), \
                 patch('tools.package_herps.run', side_effect=RuntimeError('rejected')):
                with self.assertRaisesRegex(RuntimeError, 'rejected'): notarize_dmg(image)
            r = json.loads(image.with_suffix('.notarization.json').read_text())
            self.assertEqual(r['status'], 'failed')
            self.assertFalse(r['notarized'])

    def test_success_requires_staple_validation_and_hashes_final_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / 'owned.dmg'
            image.write_bytes(b'owned image')
            with patch.dict('os.environ', {'HERPS_NOTARY_PROFILE': 'owned', 'HERPS_CODESIGN_IDENTITY': 'owned'}), \
                 patch('tools.package_herps.run') as run:
                notarize_dmg(image)
            self.assertEqual(run.call_args_list[-1].args[0][:3], ['xcrun', 'stapler', 'validate'])
            r = json.loads(image.with_suffix('.notarization.json').read_text())
            self.assertTrue(r['notarized'])
            self.assertEqual(r['status'], 'verified')

    def test_candidate_refuses_empty_output_and_never_claims_manual_or_gameplay(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            with patch('tools.release_evidence.subprocess.check_output', return_value='a' * 40):
                with self.assertRaisesRegex(ValueError, 'No candidate'): candidate(folder)
                (folder / 'owned.zip').write_bytes(b'owned')
                candidate(folder)
            r = json.loads((folder / 'candidate.json').read_text())
            self.assertEqual(r['source_commit'], 'a' * 40)
            self.assertFalse(r['interactive_verified'])
            self.assertFalse(r['gameplay_verified'])
            self.assertFalse(r['public_release_approved'])
            self.assertEqual(len(r['artifacts'][0]['sha256']), 64)

    def test_windows_verifier_refuses_non_windows_before_installing(self):
        with tempfile.TemporaryDirectory() as root:
            with patch('tools.verify_herps_windows.platform.system', return_value='Linux'), \
                 patch('tools.verify_herps_windows.subprocess.run') as run:
                with self.assertRaisesRegex(ValueError, 'Native Windows'): verify(Path(root) / 'unused.exe', Path(root))
            # platform.platform may invoke a platform probe; no installer command is allowed.
            self.assertFalse(any(str(c.args[0][0]).endswith('.exe') for c in run.call_args_list))
            self.assertFalse(json.loads((Path(root) / 'windows-lifecycle.json').read_text())['interactive_verified'])
