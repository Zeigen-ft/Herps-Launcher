"""Exercise Mac launch decisions with mocked dialogs and native executables.

These tests run the real Bash wrapper, but never open macOS GUI applications or
run a game. Native application signing and gameplay need separate Mac checks.
"""
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == "nt", "Mac Bash behavior tests need Unix paths and executable scripts")
class MacLauncherTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "darwin", "AppleScript compilation requires macOS")
    def test_actual_dialog_scripts_compile_on_mac(self):
        source = (PROJECT / "packaging/launch.command").read_text()
        dialogs = re.findall(r"<<'APPLESCRIPT'\n(.*?)\nAPPLESCRIPT", source, re.S)
        self.assertEqual(len(dialogs), 2)
        for index, dialog in enumerate(dialogs):
            result = subprocess.run(
                ["/usr/bin/osacompile", "-o", str(self.root / f"dialog-{index}.scpt")],
                input=dialog, text=True, capture_output=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def setUp(self):
        self.bash = shutil.which("bash")
        if self.bash is None:
            self.skipTest("Bash is unavailable")
        temporary = tempfile.TemporaryDirectory(prefix="herspers-mac-launch-")
        self.addCleanup(temporary.cleanup)
        # The wrapper uses pwd -P; macOS may expose /var or /tmp via symlinks.
        self.root = Path(temporary.name).resolve()
        self.app = self.root / "Herspers ' $(touch escaped-marker).app"
        self.resources = self.app / "Contents/Resources"
        self.binaries = self.app / "Contents/MacOS"
        self.resources.mkdir(parents=True)
        self.binaries.mkdir(parents=True)
        self.script = self.resources / "launch.command"
        shutil.copy2(PROJECT / "packaging/launch.command", self.script)
        (self.resources / "prepare.command").write_text("# fixture, never executed\n")
        self.home = self.root / "player ' $(touch escaped-marker) home"
        self.home.mkdir()
        self.support = self.home / "Library/Application Support/Herspers Minecraft"
        self.calls_path = self.root / "calls.jsonl"
        self.helper = self.root / "native-fixtures.py"
        self.helper.write_text(
            "import json, os, pathlib, sys\n"
            "action = sys.argv[1]\n"
            "record = {'action': action, 'args': sys.argv[2:], 'cwd': os.getcwd(),\n"
            "          'horizon_home': os.environ.get('HORIZON_HOME'),\n"
            "          'no_self_update': os.environ.get('HORIZON_LAUNCHER_NO_SELF_UPDATE')}\n"
            "if action == 'osascript': record['script'] = sys.stdin.read()\n"
            "with open(os.environ['TEST_CALLS'], 'a', encoding='utf-8') as stream:\n"
            "    stream.write(json.dumps(record) + '\\n')\n"
            "if action == 'prepare':\n"
            "    print('Resource check diagnostic: matching resources are unavailable.', file=sys.stderr)\n"
            "    sys.exit(int(os.environ.get('TEST_PREPARE_STATUS', '0')))\n"
            "if action == 'client':\n"
            "    print('Native client diagnostic: startup result.', file=sys.stderr)\n"
            "    sys.exit(int(os.environ.get('TEST_CLIENT_STATUS', '0')))\n"
            "if action == 'osascript':\n"
            "    print(os.environ.get('TEST_DIALOG_CHOICE', 'Quit'))\n"
            "    sys.exit(int(os.environ.get('TEST_DIALOG_STATUS', '0')))\n"
            "if action == 'open': sys.exit(int(os.environ.get('TEST_OPEN_STATUS', '0')))\n"
        )
        for filename, action in (("horizon-prepare", "prepare"), ("horizon-client", "client")):
            executable = self.binaries / filename
            executable.write_text('#!/bin/bash\nexec "$TEST_PYTHON" "$TEST_HELPER" ' + action + ' "$@"\n')
            executable.chmod(0o755)

    def run_launcher(self, *arguments, prepare_status=0, client_status=0,
                     choice="Quit", dialog_status=0, open_status=0, platform="Darwin"):
        environment = dict(os.environ)
        # Only the child fixture receives this home; player files are untouched.
        environment.update({
            "HOME": str(self.home), "TEST_CALLS": str(self.calls_path),
            "TEST_HELPER": str(self.helper), "TEST_PYTHON": sys.executable,
            "TEST_PREPARE_STATUS": str(prepare_status),
            "TEST_CLIENT_STATUS": str(client_status),
            "TEST_DIALOG_CHOICE": choice, "TEST_DIALOG_STATUS": str(dialog_status),
            "TEST_OPEN_STATUS": str(open_status), "TEST_PLATFORM": platform,
        })
        bootstrap = '''
uname() { printf '%s\n' "$TEST_PLATFORM"; }
/usr/bin/osascript() { "$TEST_PYTHON" "$TEST_HELPER" osascript "$@"; }
/usr/bin/open() { "$TEST_PYTHON" "$TEST_HELPER" open "$@"; }
source "$0" "$@"
'''
        return subprocess.run([self.bash, "-c", bootstrap, str(self.script), *arguments],
                              env=environment, cwd=self.root, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=15)

    def calls(self, action=None):
        rows = [] if not self.calls_path.exists() else [
            json.loads(line) for line in self.calls_path.read_text().splitlines()
        ]
        return rows if action is None else [row for row in rows if row["action"] == action]

    def assert_no_path_interpolation(self):
        self.assertFalse((self.root / "escaped-marker").exists())
        self.assertFalse((self.support / "game/escaped-marker").exists())

    def test_failed_resource_check_prints_error_and_opens_preparation(self):
        result = self.run_launcher(prepare_status=17, choice="Prepare resources")
        self.assertEqual(result.returncode, 17, result.stdout + result.stderr)
        self.assertIn("Resource check diagnostic", result.stderr)
        self.assertIn(str(self.support / "logs/resources-check.log"), result.stderr)
        self.assertFalse(self.calls("client"))
        self.assertEqual(self.calls("open")[0]["args"],
                         ["-a", "Terminal", str(self.resources / "prepare.command")])
        dialog = self.calls("osascript")[0]
        self.assertIn(str(self.support / "logs/resources-check.log"), dialog["args"])
        self.assertNotIn(str(self.home), dialog["script"])
        self.assert_no_path_interpolation()

    def test_show_resource_log_uses_exact_path_without_starting_game(self):
        result = self.run_launcher(prepare_status=126, choice="Show log")
        self.assertEqual(result.returncode, 126, result.stderr)
        self.assertFalse(self.calls("client"))
        self.assertEqual(self.calls("open")[0]["args"],
                         ["-a", "TextEdit", str(self.support / "logs/resources-check.log")])
        self.assert_no_path_interpolation()

    def test_dialog_cancellation_preserves_original_preparer_failure(self):
        result = self.run_launcher(prepare_status=19, dialog_status=128)
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assertFalse(self.calls("client"))
        self.assertFalse(self.calls("open"))

    def test_open_failure_preserves_preparer_error_and_prints_manual_path(self):
        result = self.run_launcher(prepare_status=17, choice="Prepare resources", open_status=2)
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertIn(str(self.resources / "prepare.command"), result.stderr)
        self.assertIn("Could not open", result.stderr)
        self.assertFalse(self.calls("client"))

    def test_prepared_resources_launch_client_with_literal_arguments_and_profile(self):
        arguments = ["--import-pack", "a ' $(touch escaped-marker) pack.zip"]
        result = self.run_launcher(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.calls("osascript"))
        self.assertFalse(self.calls("open"))
        clients = self.calls("client")
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0]["args"], [
            "--resources", str(self.support / "resources/26.3"),
            "--game-dir", str(self.support / "game"), *arguments,
        ])
        self.assertEqual(clients[0]["cwd"], str(self.support / "game"))
        self.assertEqual(clients[0]["horizon_home"], str(self.support))
        self.assertEqual(clients[0]["no_self_update"], "1")
        self.assert_no_path_interpolation()

    def test_game_failure_surfaces_log_and_preserves_client_status(self):
        result = self.run_launcher(client_status=23, choice="Show log")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertIn("Native client diagnostic", result.stderr)
        self.assertIn(str(self.support / "logs/launcher.log"), result.stderr)
        self.assertEqual(len(self.calls("client")), 1)
        self.assertEqual(self.calls("open")[0]["args"],
                         ["-a", "TextEdit", str(self.support / "logs/launcher.log")])
        self.assert_no_path_interpolation()

    def test_non_mac_host_is_rejected_before_creating_player_data(self):
        result = self.run_launcher(platform="Linux")
        self.assertEqual(result.returncode, 1)
        self.assertIn("requires macOS", result.stderr)
        self.assertFalse(self.support.exists())
        self.assertFalse(self.calls())


if __name__ == "__main__":
    unittest.main()
