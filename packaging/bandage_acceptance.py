"""Opt-in frozen stage-4 checks with owned fixtures, without developer tools."""
import json
from pathlib import Path
import shutil
import sys
import unittest

CASES = {
    "test_rlcraft_bandage.BandageTests.test_install_disabled_preserves_starter_other_profiles_and_backups",
    "test_rlcraft_bandage.BandageTests.test_dependency_and_old_engine_are_rejected_without_installing",
    "test_rlcraft_bandage.BandageTests.test_enable_and_launch_require_enabled_unchanged_starter",
    "test_rlcraft_bandage.BandageTests.test_only_starter_is_required_for_independent_bandage_trial",
    "test_rlcraft_bandage.BandageTests.test_saved_profiles_cannot_disable_remove_or_launch_missing_content",
    "test_rlcraft_bandage.BandageTests.test_failed_receipt_write_rolls_back_new_files_and_preserves_settings",
    "test_rlcraft_bandage_ui.BandagePageTests.test_stage4_install_off_explicit_enable_and_unsupported_workflows_stay_disabled",
    "test_rlcraft_bandage_ui.BandagePageTests.test_stage4_consent_resets_and_controls_remain_reachable",
}


def run(report_path):
    from herps_launcher.modpacks.bandage import PACKAGE_SHA256, bundled_package, validate_package
    report = {"status": "failed", "stage": 4, "tests": [],
              "interactive_verified": False, "gameplay_verified": False}
    try:
        if not getattr(sys, "frozen", False):
            raise ValueError("Bandage acceptance requires the delivered frozen application")
        report["tools_on_path"] = {name: shutil.which(name) for name in ("cargo", "rustc", "rustup")}
        if any(report["tools_on_path"].values()):
            raise ValueError("Developer tools must be absent from PATH")
        validate_package(bundled_package())
        report["package_sha256"] = PACKAGE_SHA256
        test_root = Path(sys._MEIPASS) / "bandage-tests"
        sys.path.insert(0, str(Path(sys._MEIPASS) / "flint-tests"))
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
            raise ValueError("Delivered bandage cohort failed, was incomplete or skipped")
        report["status"] = "passed"
    except Exception as error:
        report["error"] = str(error)
    Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "passed" else 1
