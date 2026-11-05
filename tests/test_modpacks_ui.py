"""Actual Qt Modpacks controls and conservative real-backend coverage rendering."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import QPoint, Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox
    from herps_launcher.app import Window, STYLE
except ImportError:
    QApplication = None

from herps_launcher.core import Launcher, digest
from herps_launcher.modpacks.service import ModpackLibrary
from herps_launcher.modpacks import targeted_backup
from tools.make_javamods_fixtures import make_jar
from tools.make_modpack_fixtures import mrpack, curseforge, local_cf_instance, instance, packwiz

BINARY = Path(os.environ["HERPS_TEST_PORT_PACK"]) if os.environ.get("HERPS_TEST_PORT_PACK") else None


@unittest.skipIf(QApplication is None, "Install pinned launcher requirements for Qt integration")
@unittest.skipUnless(BINARY is not None and BINARY.is_file(), "Set HERPS_TEST_PORT_PACK for actual modpack UI integration")
class ModpacksPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(STYLE)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps-modpacks-ui-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.launcher = Launcher(self.root / "owned support")
        self.launcher.config["port_pack_binary"] = str(BINARY)
        self.enterContext(patch("PySide6.QtWidgets.QMessageBox.warning"))
        self.enterContext(patch("PySide6.QtWidgets.QMessageBox.information"))
        self.enterContext(patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes))
        self.window = Window(self.launcher)
        self.window.show()
        self.page = self.window.modpacks
        self.window.navigate(3)
        self.app.processEvents()
        self.wait_idle()
        self.user = self.root / "user mods"
        self.good = make_jar(self.user / "good.jar", mod_id="good")

    def tearDown(self):
        if self.window.worker:
            self.window.worker.wait(15000)
            self.app.processEvents()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def wait_idle(self):
        deadline = time.monotonic() + 15
        for _ in range(3):
            self.app.processEvents()
            while self.window.worker is not None and time.monotonic() < deadline:
                self.app.processEvents()
                # QTest.qWait can hold the Python GIL between event passes.
                # Yield it so the real Python hashing/IO worker can progress,
                # as it does under QApplication.exec in the actual launcher.
                time.sleep(0.005)
        self.assertIsNone(self.window.worker, "Modpacks operation did not finish")

    def click(self, button):
        self.assertTrue(button.isEnabled(), button.text())
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        self.app.processEvents()

    def imported(self, source):
        if source.is_dir():
            with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value=str(source)):
                self.click(self.page.instance_button)
        else:
            with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(source), "")):
                self.click(self.page.import_button)
        self.wait_idle()
        self.assertGreater(self.page.pack_list.count(), 0)
        self.page.pack_list.setCurrentRow(self.page.pack_list.count() - 1)
        self.app.processEvents()
        self.wait_idle()

    def resolve(self, folder):
        with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value=str(folder)):
            self.click(self.page.resolve_button)
        self.wait_idle()

    def analyzed(self):
        self.click(self.page.analyze_button)
        self.wait_idle()
        self.assertIsNotNone(self.page.current_report)
        return self.page.current_report

    def table_text(self):
        return "\n".join(self.page.coverage_table.item(row, column).text()
            for row in range(self.page.coverage_table.rowCount())
            for column in range(self.page.coverage_table.columnCount())
            if self.page.coverage_table.item(row, column) is not None)

    def test_seventh_page_registration_preserves_all_existing_pages(self):
        expected = ["Home", "Mods", "Java Mods", "Modpacks", "Shaders", "Multiplayer", "Settings"]
        self.assertEqual([button.text() for button in self.window.nav], expected)
        self.assertEqual(self.window.pages.count(), 7)
        for index, button in enumerate(self.window.nav):
            self.click(button)
            self.assertEqual(self.window.pages.currentIndex(), index)
            self.assertTrue(button.isChecked())
        self.assertFalse(self.page.play_button.isEnabled())

    def targeted_fixture(self):
        source = self.root / "owned targeted metadata.zip"
        manifest = {"manifestType": "minecraftModpack", "manifestVersion": 1,
            "minecraft": {"version": "1.12.2", "modLoaders": [{"id": "forge-14.23.5.2847", "primary": True}]},
            "name": targeted_backup.FUNCRAFT_NAME, "version": targeted_backup.FUNCRAFT_VERSION,
            "author": "Owned test fixture", "files": [{"projectID": 314904, "fileID": 2749104, "required": True}], "overrides": "overrides"}
        with ZipFile(source, "w") as zipped:
            zipped.writestr("manifest.json", json.dumps(manifest))
        self.enterContext(patch.object(targeted_backup, "FUNCRAFT_SHA256", digest(source)))
        self.imported(source)
        for index, entry in enumerate(self.page.pack_entries):
            if entry.name == targeted_backup.FUNCRAFT_NAME:
                self.page.pack_list.setCurrentRow(index)
                break
        self.app.processEvents()
        self.wait_idle()
        return source

    def test_targeted_world_backup_and_verification_do_not_unlock_java_or_pack_play(self):
        self.targeted_fixture()
        saved = self.launcher.game / "saves/Owned/level.dat"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"owned UI backup fixture; not real gameplay")
        original = digest(saved)
        self.assertTrue(self.page.backup_button.isEnabled())
        self.assertIn(targeted_backup.FUNCRAFT_VERSION, self.page.feature_status.text())
        with patch("PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.StandardButton.Yes):
            self.click(self.page.backup_button)
        self.wait_idle()
        archives = list((self.launcher.state / "targeted-backups").rglob("worlds.zip"))
        self.assertEqual(len(archives), 1)
        self.assertIn("checksum verification passed", self.page.status.text())
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(archives[0]), "")):
            self.click(self.page.verify_backup_button)
        self.wait_idle()
        self.assertIn("integrity verified", self.page.status.text())
        self.assertEqual(digest(saved), original)
        self.assertFalse(self.page.play_button.isEnabled())
        self.assertFalse(self.window.java_mods.build_button.isEnabled())
        self.assertFalse(self.window.java_mods.test_button.isEnabled())
        self.assertFalse(json.loads(self.page.details.toPlainText())["gameplay_verified"])

    def test_targeted_backup_cancellation_unknown_pack_and_profile_switch_fail_closed(self):
        self.imported(mrpack(self.root / "unrelated.mrpack", [self.good]))
        self.assertFalse(self.page.backup_button.isEnabled())
        self.targeted_fixture()
        self.assertTrue(self.page.backup_button.isEnabled())
        with patch("PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.StandardButton.Cancel):
            self.click(self.page.backup_button)
        self.assertFalse((self.launcher.state / "targeted-backups").exists())
        self.window.navigate(0)
        self.launcher.add_profile("no_target")
        self.window.profile.addItem("no_target")
        self.window.profile.setCurrentText("no_target")
        self.window.refresh()
        self.window.navigate(3)
        self.app.processEvents()
        self.wait_idle()
        self.assertFalse(self.page.backup_button.isEnabled())
        self.assertFalse(self.page.verify_backup_button.isEnabled())
        self.assertFalse(self.page.play_button.isEnabled())

    def test_backup_and_existing_controls_remain_reachable_at_small_window_sizes(self):
        self.targeted_fixture()
        for width, height in [(1130, 790), (900, 640)]:
            with self.subTest(size=(width, height)):
                self.window.resize(width, height)
                self.app.processEvents()
                for button in (self.page.backup_button, self.page.verify_backup_button,
                        self.page.analyze_button, self.page.export_json_button, self.page.errors_button):
                    self.page.scroll.ensureWidgetVisible(button, 0, 0)
                    self.app.processEvents()
                    point = button.mapTo(self.page.scroll.viewport(), QPoint(0, 0))
                    self.assertGreaterEqual(button.height(), button.minimumSizeHint().height())
                    self.assertTrue(self.page.scroll.viewport().rect().contains(point), button.text())
                    self.assertTrue(self.page.scroll.viewport().rect().contains(point + QPoint(button.width() - 1, button.height() - 1)), button.text())

    def test_import_analyze_and_resolve_keep_all_mod_rows_and_required_columns(self):
        bad = make_jar(self.user / "bad.jar", mod_id="bad", depends={"missinglib": "*"}, mixins=True)
        self.imported(mrpack(self.root / "owned.mrpack", [self.good, bad], missing=1))
        self.resolve(self.user)
        report = self.analyzed()
        self.assertEqual(self.page.coverage_table.columnCount(), 7)
        self.assertEqual(self.page.coverage_table.rowCount(), 3)
        text = self.table_text()
        for wanted in ("good", "bad", "missinglib", "Unsupported", "MIT", "1"):
            self.assertIn(wanted, text)
        self.assertEqual(len(report["rows"]), 3)
        self.assertFalse(report["playable_verified"])
        self.assertFalse(self.page.play_button.isEnabled())

    def test_false_positive_works_stays_unsupported_in_coverage_and_errors(self):
        bad = make_jar(self.user / "bad.jar", mod_id="bad", depends={"missinglib": ">=2"},
                       mixins=True, invalid_class=True)
        self.imported(mrpack(self.root / "false-positive.mrpack", [bad]))
        self.resolve(self.user)
        report = self.analyzed()
        self.assertEqual(report["rows"][0]["status"], "Unsupported")
        self.assertIn("Unsupported", self.table_text())
        self.click(self.page.errors_button)
        rendered = self.page.details.toPlainText().lower()
        for wanted in ("works", "missinglib", "insufficient_evidence"):
            self.assertIn(wanted, rendered)
        self.assertFalse(self.page.play_button.isEnabled())

    def test_curseforge_user_instance_resolution_needs_no_api_key_or_download(self):
        self.imported(curseforge(self.root / "cf.zip", [self.good]))
        local = local_cf_instance(self.root / "own CF instance", [self.good])
        self.resolve(local)
        report = self.analyzed()
        self.assertIn("good", self.table_text())
        self.assertFalse(report["playable_verified"])
        self.assertNotIn("API key", self.page.summary.text())

    def test_partial_port_has_data_outputs_but_play_remains_disabled(self):
        bad = make_jar(self.user / "bad.jar", mod_id="bad", depends={"missinglib": "*"})
        self.imported(mrpack(self.root / "partial.mrpack", [self.good, bad]))
        self.resolve(self.user)
        self.click(self.page.port_button)
        self.wait_idle()
        report = self.page.current_report
        self.assertEqual(len(report["rows"]), 2)
        self.assertTrue(next(row for row in report["rows"] if row["id"] == "good")["carried"])
        self.assertFalse(next(row for row in report["rows"] if row["id"] == "bad")["carried"])
        self.assertIn("partial", self.page.summary.text().lower())
        self.assertFalse(self.page.play_button.isEnabled())
        self.assertFalse(report["playable_verified"])
        self.assertFalse((self.launcher.game / "horizon-mods").exists())

    def test_hash_mismatch_is_visible_and_does_not_enable_play(self):
        self.imported(mrpack(self.root / "bad-hash.mrpack", [self.good], bad_hash=True))
        self.resolve(self.user)
        self.analyzed()
        self.assertIn("Unsupported", self.table_text())
        self.assertIn("hash", self.table_text().lower() + self.page.details.toPlainText().lower())
        self.assertFalse(self.page.play_button.isEnabled())

    def test_failed_backend_retains_real_exit_stdout_stderr_in_view_errors(self):
        self.imported(mrpack(self.root / "owned.mrpack", [self.good]))
        with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                ["owned-backend"], 7, "owned modpack stdout", "owned modpack stderr")):
            report = self.analyzed()
        self.assertEqual(report["status"], "Unsupported")
        self.click(self.page.errors_button)
        text = self.page.details.toPlainText()
        self.assertIn("owned modpack stdout", text)
        self.assertIn("owned modpack stderr", text)
        self.assertIn("Exit code: 7", text)
        self.assertFalse(self.page.play_button.isEnabled())

    def test_json_and_text_exports_retain_pack_coverage_and_backend_evidence(self):
        self.imported(mrpack(self.root / "owned.mrpack", [self.good], missing=1))
        self.resolve(self.user)
        self.analyzed()
        for format, button in (("json", self.page.export_json_button), ("text", self.page.export_text_button)):
            output = self.root / ("compatibility." + format)
            with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(output), "")):
                self.click(button)
            self.wait_idle()
            self.assertTrue(output.is_file())
            content = output.read_text(encoding="utf-8")
            for wanted in ("good", "missing-0", "Unsupported"):
                self.assertIn(wanted, content)
            if format == "json":
                exported = json.loads(content)
                self.assertFalse(exported["playable_verified"])

    def test_profiles_isolate_pack_snapshots_and_report_selection(self):
        self.imported(instance(self.root / "Prism", [self.good]))
        first = self.page.pack_entries[0]
        self.window.navigate(0)
        self.launcher.add_profile("separate")
        self.window.profile.addItem("separate")
        self.window.profile.setCurrentText("separate")
        self.window.refresh()
        self.window.navigate(3)
        self.app.processEvents()
        self.wait_idle()
        self.assertEqual(self.page.pack_list.count(), 0)
        self.assertIsNone(self.page.current_report)
        self.assertTrue(Path(first.source).exists())
        self.window.profile.setCurrentText("default")
        self.app.processEvents()
        self.wait_idle()
        self.assertEqual(self.page.pack_list.count(), 1)

    def test_packwiz_explains_backend_limitation_and_never_offers_play(self):
        self.imported(packwiz(self.root / "packwiz"))
        report = self.analyzed()
        self.assertEqual(report["status"], "Unsupported")
        text = self.page.summary.text() + self.table_text() + self.page.details.toPlainText()
        self.assertIn("packwiz", text.lower())
        self.assertFalse(self.page.play_button.isEnabled())

    def test_pack_analysis_stays_off_gui_thread_and_busy_guard_preserves_profile(self):
        self.imported(mrpack(self.root / "owned.mrpack", [self.good]))
        entered, release = threading.Event(), threading.Event()
        original = ModpackLibrary.analyze
        def delayed(service, *args, **kwargs):
            entered.set()
            release.wait(5)
            return original(service, *args, **kwargs)
        with patch.object(ModpackLibrary, "analyze", delayed):
            try:
                self.click(self.page.analyze_button)
                deadline = time.monotonic() + 2
                while not entered.is_set() and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertTrue(entered.is_set())
                events = []
                QTimer.singleShot(0, lambda: events.append("live"))
                QTest.qWait(30)
                self.app.processEvents()
                self.assertEqual(events, ["live"])
                self.assertFalse(self.page.import_button.isEnabled())
                with self.assertRaises(ValueError):
                    self.window.require_idle()
            finally:
                release.set()
                self.wait_idle()


if __name__ == "__main__":
    unittest.main()
