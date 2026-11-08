"""Actual Qt controls; owned package fixtures and metadata, not a game world."""
from types import SimpleNamespace
from unittest.mock import patch
import test_rlcraft_flint_ui as base
from herps_launcher.modpacks import flint, gathering
import unittest


QApplication = base.QApplication
QMessageBox, QTest, Qt, QPoint = (getattr(base, name, None) for name in ("QMessageBox", "QTest", "Qt", "QPoint"))

@unittest.skipIf(QApplication is None, "Install pinned Qt requirements")
class GatheringPageTests(base.FlintPageTests):
    # Do not repeat the inherited stage-1 test cohort.
    test_explicit_profile_install_starts_off_and_keeps_unsupported_play_disabled = None
    test_cancel_profile_switch_busy_and_existing_world_preserve_data = None
    test_flint_controls_remain_reachable_in_supported_small_windows = None

    def prepare(self):
        self.select("gathering_disposable")
        self.enterContext(patch.object(self.launcher, "installation", return_value=SimpleNamespace(
            metadata={"engine_source": {"native_features": [gathering.ENGINE_FEATURE]}})))
        flint.install(self.launcher, self.launcher.config["profile"], disposable_confirmed=True, games_closed=True)
        starter = next(m for m in self.launcher.mods() if m.id == flint.MOD_ID)
        self.launcher.set_enabled(starter, True)
        self.window.refresh(); self.wait_idle()

    def test_stage2_install_off_explicit_enable_and_unsupported_workflows_stay_disabled(self):
        self.assertFalse(self.page.gathering_button.isEnabled()); self.prepare()
        self.page.gathering_consent.setChecked(True)
        with patch("PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.StandardButton.Yes):
            QTest.mouseClick(self.page.gathering_button, Qt.MouseButton.LeftButton)
        self.wait_idle()
        self.assertTrue(gathering.status(self.launcher)["installed"])
        self.assertFalse(gathering.status(self.launcher)["enabled"])
        mod = next(m for m in self.launcher.mods() if m.id == gathering.MOD_ID)
        self.launcher.set_enabled(mod, True)
        self.assertTrue(gathering.status(self.launcher)["enabled"])
        self.assertFalse(self.page.play_button.isEnabled())
        self.assertFalse(self.window.java_mods.build_button.isEnabled())
        self.assertFalse(self.window.java_mods.test_button.isEnabled())
        self.assertEqual(self.window.pages.count(), 7)

    def test_stage2_consent_resets_and_controls_remain_reachable(self):
        self.prepare(); self.page.gathering_consent.setChecked(True)
        self.select("gathering_other")
        self.assertFalse(self.page.gathering_consent.isChecked())
        for width, height in [(1130, 790), (900, 640)]:
            self.window.resize(width, height); self.app.processEvents()
            for control in [self.page.gathering_consent, self.page.gathering_button]:
                self.page.scroll.ensureWidgetVisible(control, 0, 0); self.app.processEvents()
                point = control.mapTo(self.page.scroll.viewport(), QPoint(0, 0))
                self.assertTrue(self.page.scroll.viewport().rect().contains(point))
                self.assertTrue(self.page.scroll.viewport().rect().contains(point + QPoint(control.width()-1, control.height()-1)))
