"""Opt-in frozen acceptance harness; owned fixtures, never Java execution."""
import json
import os
from pathlib import Path
import shutil
import sys
import unittest

TARGETED_BACKUP_CASES = {
    "test_modpacks_ui.ModpacksPageTests.test_targeted_world_backup_and_verification_do_not_unlock_java_or_pack_play",
    "test_modpacks_ui.ModpacksPageTests.test_targeted_backup_cancellation_unknown_pack_and_profile_switch_fail_closed",
    "test_modpacks_ui.ModpacksPageTests.test_backup_and_existing_controls_remain_reachable_at_small_window_sizes",
}


def verify_targeted_cases(tests, skipped):
    missing = TARGETED_BACKUP_CASES - set(tests)
    omitted = TARGETED_BACKUP_CASES & {name for name, _ in skipped}
    if missing or omitted:
        raise ValueError(f"Required delivered FunCraft backup cases missing/skipped: {sorted(missing | omitted)}")
    return sorted(TARGETED_BACKUP_CASES)


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
        # Windows --windowed builds have no sys.stderr; retain a real test log.
        with Path(report_path).with_suffix(".tests.log").open("w", encoding="utf-8") as log:
            result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=EvidenceResult).run(suite)
        report.update(tests_run=result.testsRun,
                      failures=[(t.id(), trace) for t, trace in result.failures],
                      errors=[(t.id(), trace) for t, trace in result.errors],
                      skipped=[(t.id(), reason) for t, reason in result.skipped])
        allowed_windows = {"test_symlinked_profile_ancestor_cannot_redirect_mutations",
                           "test_system_style_link_above_support_root_is_allowed",
                           "test_symlinked_profile_parent_cannot_redirect_pack_import"}
        unexpected_skips = [(t.id(), reason) for t, reason in result.skipped
                            if sys.platform != "win32" or t.id().split(".")[-1] not in allowed_windows]
        report["unexpected_skips"] = unexpected_skips
        if not result.wasSuccessful() or unexpected_skips or result.testsRun < 65:
            raise ValueError("Frozen acceptance failed, skipped coverage, or collected too few cases")
        report["targeted_backup_cases_verified"] = verify_targeted_cases(report["tests"], report["skipped"])
        support = Path(os.environ.get("HERPS_ACCEPTANCE_SUPPORT") or os.environ["PHASE5C_SUPPORT"])
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
