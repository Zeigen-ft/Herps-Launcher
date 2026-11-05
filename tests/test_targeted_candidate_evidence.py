"""Reject old/skipped frozen cohorts and stage the exact standalone inspector."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.package_rlcraft_inspector import stage

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frozen_acceptance_guard',ROOT/'packaging/phase5c_acceptance.py')
acceptance=importlib.util.module_from_spec(spec)
spec.loader.exec_module(acceptance)


class TargetedCandidateEvidenceTests(unittest.TestCase):
    def test_old_frozen_cohort_cannot_claim_chainmail_installation(self):
        required = sorted(acceptance.CHAINMAIL_CASES)
        with self.assertRaisesRegex(ValueError, 'missing/skipped'):
            acceptance.verify_chainmail_cases(sorted(acceptance.TARGETED_BACKUP_CASES), [])
        with self.assertRaisesRegex(ValueError, 'missing/skipped'):
            acceptance.verify_chainmail_cases(required, [(required[0], 'unavailable')])
        self.assertEqual(acceptance.verify_chainmail_cases(required, []), required)

    def test_old_frozen_cohort_cannot_claim_the_new_backup_feature(self):
        with self.assertRaisesRegex(ValueError,'missing/skipped'):
            acceptance.verify_targeted_cases(['old.test']*65,[])
        required=sorted(acceptance.TARGETED_BACKUP_CASES)
        with self.assertRaisesRegex(ValueError,'missing/skipped'):
            acceptance.verify_targeted_cases(required,[(required[0],'not available')])
        self.assertEqual(acceptance.verify_targeted_cases(required,[]),required)

    def test_download_staging_binds_source_hash_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'Inspector'
            stage(output)
            data=json.loads((output/'inspector.json').read_text())
            self.assertEqual(data['script_sha256'],hashlib.sha256((output/'inspect_rlcraft_293.py').read_bytes()).hexdigest())
            self.assertEqual((output/'inspect_rlcraft_293.py').read_bytes(),(ROOT/'tools/inspect_rlcraft_293.py').read_bytes())
            self.assertIn('py -3.12',(output/'Inspect-RLCraft.cmd').read_text())
            self.assertFalse(data['requires_java'])
            self.assertFalse(data['requires_rust'])
            before=(output/'inspector.json').read_bytes()
            with self.assertRaises(FileExistsError):stage(output)
            self.assertEqual((output/'inspector.json').read_bytes(),before)
