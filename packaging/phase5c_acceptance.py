"""Opt-in frozen acceptance harness; owned fixtures, never Java execution."""
import json
import os
from pathlib import Path
import shutil
import sys
import unittest


def run(report_path):
    from herps_launcher.core import Launcher
    from herps_launcher.javamods.adapter import PortPackAdapter, bundled_port_pack_candidates
    from herps_entry import port_pack_smoke
    import tempfile

    report = {"status": "failed", "interactive_verified": False,
              "gameplay_verified": False, "tests": []}
    try:
        if not getattr(sys, "frozen", False):
            raise ValueError("Acceptance requires the delivered frozen application")
        report["tools_on_path"] = {name: shutil.which(name) for name in ("cargo", "rustc", "rustup")}
        if any(report["tools_on_path"].values()):
            raise ValueError("Developer Rust tools are still discoverable")
        with tempfile.TemporaryDirectory(prefix="phase5c discovery ") as directory:
            launcher = Launcher(Path(directory))
            report["port_pack"] = {}
            port_pack_smoke(launcher, Path(directory), report["port_pack"])
        os.environ["HERPS_TEST_PORT_PACK"] = report["port_pack"]["path"]
        test_root = Path(sys._MEIPASS) / "phase5c-tests"
        suite = unittest.TestSuite()
        for name in ("test_javamods_ui.py", "test_modpacks_ui.py",
                     "test_javamods_library.py", "test_modpacks_service.py"):
            suite.addTests(unittest.TestLoader().discover(str(test_root), pattern=name))
        class EvidenceResult(unittest.TextTestResult):
            def stopTest(self, test):
                report["tests"].append(test.id())
                super().stopTest(test)
        result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
        report.update(tests_run=result.testsRun,
                      failures=[(t.id(), trace) for t, trace in result.failures],
                      errors=[(t.id(), trace) for t, trace in result.errors],
                      skipped=[(t.id(), reason) for t, reason in result.skipped])
        if not result.wasSuccessful() or result.skipped or result.testsRun < 50:
            raise ValueError("Frozen acceptance failed, skipped coverage, or collected too few cases")
        support = Path(os.environ["PHASE5C_SUPPORT"])
        persistent = Launcher(support)
        persistent.add_profile("owned_acceptance")
        save = persistent.game / "saves/Owned/level.dat"
        save.parent.mkdir(parents=True, exist_ok=True)
        save.write_bytes(b"owned phase5c save sentinel")
        persistent.config["close_on_play"] = True
        persistent.save()
        reloaded = Launcher(support)
        if (reloaded.config["profile"] != "owned_acceptance" or
                reloaded.config["close_on_play"] is not True or
                (reloaded.game / "saves/Owned/level.dat").read_bytes() != save.read_bytes()):
            raise ValueError("Persistent profile/settings/save reload failed")
        report["persistent_reload_verified"] = True
        report["status"] = "passed"
    except Exception as error:
        report["error"] = str(error)
    Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "passed" else 1
