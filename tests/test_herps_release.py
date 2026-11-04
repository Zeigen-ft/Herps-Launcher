"""Release receipts must not claim notarization or execution without evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.package_herps import notarize_dmg, copy_documentation
from tools.release_evidence import candidate, collect_dependencies
from tools.verify_herps_windows import verify
from tools.windows_installer import payload_limits


class ReleaseEvidenceTests(unittest.TestCase):
    def test_offline_guides_and_referenced_support_documents_are_shipped(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root)
            copy_documentation(output)
            self.assertIn("docs/HERPS-LAUNCHER.md", (output / 'START-HERE.txt').read_text())
            for name in ('docs/HERPS-LAUNCHER.md', 'docs/HERPS-SUPPORT.md',
                         'docs/herps/native-acceptance.md', 'docs/herps/release-security.md',
                         'licenses/Qt-PySide-NOTICE.md', 'LICENSE-HERPS.txt'):
                self.assertTrue((output / name).is_file(), name)

    def test_resolved_inventory_preserves_qt_notices_despite_distribution_name_normalization(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root)
            collect_dependencies(output)
            r = json.loads((output / 'python-dependencies.json').read_text())
            rows = {x['name'].lower().replace('_', '-'): x for x in r['dependencies']}
            for name in ('pyside6-essentials', 'shiboken6'):
                members = [Path(n['file']).name for n in rows[name]['notices']]
                self.assertIn('LGPL-3.0.txt', members)
                self.assertIn('Qt-PySide-NOTICE.md', members)
                self.assertTrue(all((output / n['file']).is_file() for n in rows[name]['notices']))
            self.assertTrue((output / 'resolved-build-requirements.txt').is_file())

    def test_installer_path_budget_counts_utf16_and_refuses_empty_payload(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            with self.assertRaisesRegex(ValueError, 'empty'): payload_limits(folder)
            (folder / 'nested').mkdir()
            (folder / 'nested' / '\U0001f600.txt').write_text('owned')
            limits = payload_limits(folder)
            self.assertEqual(limits, {'file_chars': 13, 'directory_chars': 6})

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
