"""Opt-in frozen stage-1 checks with owned fixtures, without developer tools."""
import json
from pathlib import Path
import shutil
import sys
import unittest

CASES = {
    "test_rlcraft_flint.FlintTests.test_install_off_and_full_support_preservation",
    "test_rlcraft_flint.FlintTests.test_existing_saves_and_missing_consent_refuse_without_writes",
    "test_rlcraft_flint.FlintTests.test_save_guard_missing_tampered_disabled_blocks_launch",
    "test_rlcraft_flint.FlintTests.test_removal_moves_only_owned_content_and_receipt",
    "test_rlcraft_flint_ui.FlintPageTests.test_explicit_profile_install_starts_off_and_keeps_unsupported_play_disabled",
    "test_rlcraft_flint_ui.FlintPageTests.test_cancel_profile_switch_busy_and_existing_world_preserve_data",
    "test_rlcraft_flint_ui.FlintPageTests.test_flint_controls_remain_reachable_in_supported_small_windows",
}


def run(report_path):
    from herps_launcher.modpacks.flint import PACKAGE_SHA256, bundled_package, validate_package
    report = {"status": "failed", "stage": 1, "tests": [],
              "interactive_verified": False, "gameplay_verified": False}
    try:
        if not getattr(sys, "frozen", False):
            raise ValueError("Flint acceptance requires the delivered frozen application")
        report["tools_on_path"] = {name: shutil.which(name) for name in ("cargo", "rustc", "rustup")}
        if any(report["tools_on_path"].values()):
            raise ValueError("Developer tools must be absent from PATH")
        validate_package(bundled_package())
        report["package_sha256"] = PACKAGE_SHA256
        test_root = Path(sys._MEIPASS) / "flint-tests"
        sys.path.insert(0, str(test_root))
        suite = unittest.defaultTestLoader.loadTestsFromNames(sorted(CASES))
        class EvidenceResult(unittest.TextTestResult):
            def stopTest(self, test):
                report["tests"].append(test.id())
                super().stopTest(test)
        with Path(report_path).with_suffix(".tests.log").open("w", encoding="utf-8") as stream:
            result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=EvidenceResult).run(suite)
        report.update(tests_run=result.testsRun,
            failures=[(t.id(), trace) for t, trace in result.failures],
            errors=[(t.id(), trace) for t, trace in result.errors],
            skipped=[(t.id(), reason) for t, reason in result.skipped])
        if not result.wasSuccessful() or result.skipped or set(report["tests"]) != CASES:
            raise ValueError("Delivered flint cohort failed, was incomplete or skipped")
        report["status"] = "passed"
    except Exception as error:
        report["error"] = str(error)
    Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "passed" else 1
