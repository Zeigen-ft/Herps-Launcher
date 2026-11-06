"""Failure receipts must survive native verification failures."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.verify_herps_dmg import verify


class DmgFailureTests(unittest.TestCase):
    def test_wrong_native_architecture_is_refused_and_reported(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / 'evidence'
            with patch('tools.verify_herps_dmg.platform.system', return_value='Darwin'), \
                 patch('tools.verify_herps_dmg.platform.machine', return_value='arm64'), \
                 patch('tools.verify_herps_dmg.subprocess.run') as command:
                with self.assertRaisesRegex(ValueError, 'Matching native'):
                    verify(Path(root) / 'unused.dmg', output, 'x86_64')
            command.assert_not_called()
            receipt = json.loads((output / 'delivered-dmg.json').read_text())
            self.assertEqual(receipt['status'], 'failed')
            self.assertFalse(receipt['interactive_verified'])

    def test_corrupt_dmg_stops_before_mount_and_retains_failure(self):
        import subprocess
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / 'owned.dmg'
            image.write_bytes(b'owned invalid image')
            output = Path(root) / 'evidence'
            with patch('tools.verify_herps_dmg.platform.system', return_value='Darwin'), \
                 patch('tools.verify_herps_dmg.platform.machine', return_value='arm64'), \
                 patch('tools.verify_herps_dmg.subprocess.run', return_value=
                       subprocess.CompletedProcess([], 1, '', 'corrupt image')) as command:
                with self.assertRaisesRegex(ValueError, 'Command failed'):
                    verify(image, output, 'arm64')
            self.assertEqual(sum(call.args[0][0] == 'hdiutil' for call in command.call_args_list), 1)
            receipt = json.loads((output / 'delivered-dmg.json').read_text())
            self.assertEqual(len(receipt['dmg_sha256']), 64)
            self.assertEqual(receipt['commands'][0]['stderr'], 'corrupt image')
