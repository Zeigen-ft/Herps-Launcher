"""Actual Qt controls with owned profiles; no gameplay claims."""
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox
    from herps_launcher.app import Window
except ImportError:
    QApplication = None

from herps_launcher.core import Launcher
from herps_launcher.modpacks import flint


@unittest.skipIf(QApplication is None, "Install pinned Qt requirements")
class FlintPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="owned-flint-ui-")
        self.addCleanup(directory.cleanup)
        self.launcher = Launcher(Path(directory.name) / "support")
        self.window = Window(self.launcher)
        self.window.show(); self.window.navigate(3)
        self.page = self.window.modpacks
        self.wait_idle()

    def tearDown(self):
        if self.window.worker: self.window.worker.wait(15000)
        self.app.processEvents()
        self.window.close(); self.window.deleteLater(); self.app.processEvents()

    def wait_idle(self):
        deadline = time.monotonic() + 15
        for _ in range(3):
            self.app.processEvents()
            while self.window.worker is not None and time.monotonic() < deadline:
                self.app.processEvents(); time.sleep(0.005)
        self.assertIsNone(self.window.worker)

    def select(self, name):
        self.launcher.add_profile(name)
        self.window.refresh(); self.wait_idle()

    def click_install(self, answer):
        with patch("PySide6.QtWidgets.QMessageBox.warning", return_value=answer):
            QTest.mouseClick(self.page.flint_button, Qt.MouseButton.LeftButton)
        self.wait_idle()

    def test_explicit_profile_install_starts_off_and_keeps_unsupported_play_disabled(self):
        self.assertFalse(self.page.flint_button.isEnabled())
        self.select("flint_disposable")
        self.assertFalse(self.page.flint_button.isEnabled())
        self.page.flint_consent.setChecked(True)
        self.assertTrue(self.page.flint_button.isEnabled())
        self.click_install(QMessageBox.StandardButton.Yes)
        self.assertTrue(flint.status(self.launcher)["installed"])
        self.assertFalse(flint.status(self.launcher)["enabled"])
        self.assertFalse(flint.status(self.launcher)["gameplay_verified"])
        self.window.mod_list.setCurrentRow(0); self.window.toggle_mod()
        self.assertTrue(flint.status(self.launcher)["enabled"])
        self.assertFalse(self.page.play_button.isEnabled())
        self.assertFalse(self.window.java_mods.build_button.isEnabled())
        self.assertFalse(self.window.java_mods.test_button.isEnabled())
        self.assertEqual(self.window.pages.count(), 7)

    def test_cancel_profile_switch_busy_and_existing_world_preserve_data(self):
        self.select("flint_disposable"); self.page.flint_consent.setChecked(True)
        self.click_install(QMessageBox.StandardButton.Cancel)
        self.assertFalse(flint.status(self.launcher)["installed"])
        self.select("flint_other")
        self.assertFalse(self.page.flint_consent.isChecked())
        with patch.object(self.window, "busy", return_value=True):
            self.page.busy_changed()
            self.assertFalse(self.page.flint_button.isEnabled())
            with self.assertRaises(ValueError): self.page.install_flint()
        self.page.busy_changed()
        saved = self.launcher.game / "saves/Owned/level.dat"
        saved.parent.mkdir(parents=True); saved.write_bytes(b"owned non-gameplay sentinel")
        self.page.flint_consent.setChecked(True)
        self.click_install(QMessageBox.StandardButton.Yes)
        self.assertIn("existing saves", self.page._last_error)
        self.assertEqual(saved.read_bytes(), b"owned non-gameplay sentinel")
        self.assertFalse(flint.status(self.launcher)["installed"])

    def test_flint_controls_remain_reachable_in_supported_small_windows(self):
        self.select("flint_disposable"); self.page.flint_consent.setChecked(True)
        for width, height in [(1130, 790), (900, 640)]:
            self.window.resize(width, height); self.app.processEvents()
            for control in (self.page.flint_consent, self.page.flint_button):
                self.page.scroll.ensureWidgetVisible(control, 0, 0); self.app.processEvents()
                point = control.mapTo(self.page.scroll.viewport(), QPoint(0, 0))
                self.assertTrue(self.page.scroll.viewport().rect().contains(point))
                self.assertTrue(self.page.scroll.viewport().rect().contains(point + QPoint(control.width()-1, control.height()-1)))
