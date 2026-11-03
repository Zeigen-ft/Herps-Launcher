"""Exercise Java Mods Qt flows with owned fixtures and the actual passive CLI."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
    from herps_launcher.app import Window, STYLE
except ImportError:
    QApplication = None

from herps_launcher.core import Launcher, digest, pairs
from herps_launcher.javamods.adapter import PortPackAdapter
from tools.make_javamods_fixtures import make_jar

BINARY = Path(os.environ["HERPS_TEST_PORT_PACK"]) if os.environ.get("HERPS_TEST_PORT_PACK") else None


class JavaModsHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(STYLE)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="herps-java-ui-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.launcher = Launcher(self.root / "owned support")
        if BINARY is not None:
            self.launcher.config["port_pack_binary"] = str(BINARY)
        self.warning = self.enterContext(patch("PySide6.QtWidgets.QMessageBox.warning"))
        self.enterContext(patch("PySide6.QtWidgets.QMessageBox.information"))
        self.enterContext(patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes))
        self.window = Window(self.launcher)
        self.window.show()
        self.page = self.window.java_mods
        self.window.navigate(2)
        self.app.processEvents()
        self.wait_idle()

    def tearDown(self):
        if self.window.worker:
            self.window.worker.wait(10000)
            self.app.processEvents()
        if self.launcher.child:
            self.launcher.child.wait(timeout=10)
            self.launcher.poll()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def click(self, button):
        self.assertTrue(button.isEnabled(), f"Button is disabled: {button.text()}")
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        self.app.processEvents()

    def wait_idle(self):
        deadline = time.monotonic() + 10
        while self.window.worker is not None and time.monotonic() < deadline:
            QTest.qWait(10)
            self.app.processEvents()
        self.assertIsNone(self.window.worker, "Background operation did not finish")
        self.app.processEvents()

    def import_fixture(self, name="owned.jar", **options):
        path = make_jar(self.root / name, **options)
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(path), "Java mods (*.jar)")):
            self.click(self.page.import_button)
        self.wait_idle()
        self.assertGreater(self.page.import_list.count(), 0)
        matching = [i for i, entry in enumerate(self.page.import_entries) if entry.sha256 == digest(path)]
        self.assertTrue(matching, "Imported snapshot was not listed")
        self.page.import_list.setCurrentRow(matching[-1])
        self.app.processEvents()
        return path

    def analyze(self):
        self.click(self.page.analyze_button)
        self.wait_idle()
        self.assertIsNotNone(self.page.current_report)
        return self.page.current_report

    def new_profile(self, profile):
        home = self.window.pages.widget(0)
        button = next(button for button in home.findChildren(QPushButton) if "New profile" in button.text())
        self.window.navigate(0)
        with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=(profile, True)):
            self.click(button)
        self.app.processEvents()
        self.window.navigate(2)
        self.app.processEvents()
        self.wait_idle()


@unittest.skipIf(QApplication is None, "Install pinned launcher requirements for Qt integration")
class JavaModsPageTests(JavaModsHarness):
    def test_java_mods_registration_preserves_all_existing_pages(self):
        self.assertEqual([button.text() for button in self.window.nav],
                         ["Home", "Mods", "Java Mods", "Shaders", "Multiplayer", "Settings"])
        self.assertEqual(self.window.pages.count(), 6)
        self.assertIs(self.window.pages.widget(2), self.page)
        for i, button in enumerate(self.window.nav):
            self.click(button)
            self.assertEqual(self.window.pages.currentIndex(), i)
            self.assertTrue(button.isChecked())
        self.assertTrue(hasattr(self.window, "mod_list"))
        self.assertTrue(hasattr(self.window, "shader_list"))
        self.assertTrue(hasattr(self.window, "address"))

    def test_fabric_forge_neoforge_imports_retain_local_copies_without_execution(self):
        for loader in ("fabric", "forge", "neoforge"):
            original = self.import_fixture(f"{loader}.jar", loader=loader, mod_id=loader)
            entry = self.page.import_entries[self.page.import_list.currentRow()]
            self.assertEqual(entry.loader, loader)
            self.assertEqual(entry.mod_id, loader)
            self.assertEqual(digest(Path(entry.path)), digest(original))
            self.assertTrue(Path(entry.path).is_relative_to(self.launcher.game))
            self.assertTrue(original.is_file())
            self.assertIn(loader, self.page.details.toPlainText().lower())
        self.assertEqual(self.page.import_list.count(), 3)
        self.assertFalse(self.page.build_button.isEnabled())
        self.assertFalse(self.page.test_button.isEnabled())

    def test_imports_and_selection_are_isolated_per_profile(self):
        original = self.import_fixture(mod_id="original")
        first = self.page.import_entries[0]
        self.new_profile("separate")
        self.assertEqual(self.page.import_list.count(), 0)
        self.assertIsNone(self.page.current_report)
        self.import_fixture("second.jar", mod_id="second")
        second = self.page.import_entries[0]
        self.assertNotEqual(first.path, second.path)
        self.assertTrue(Path(second.path).is_relative_to(self.launcher.game))
        self.window.profile.setCurrentText("default")
        self.app.processEvents()
        self.wait_idle()
        self.assertEqual(self.page.import_list.count(), 1)
        self.assertEqual(self.page.import_entries[0].mod_id, "original")
        self.assertTrue(original.is_file())

    def test_missing_binary_failure_is_visible_without_a_success_claim(self):
        self.launcher.config["port_pack_binary"] = str(self.root / "missing-port-pack")
        self.import_fixture()
        report = self.analyze()
        self.assertEqual(report["status"], "Unsupported")
        self.assertIsNone(report["test_execution"])
        self.assertFalse(report["java_bridge_available"])
        details = self.page.details.toPlainText().lower()
        self.assertIn("missing", details)
        self.assertIn("insufficient_evidence", details)

    def test_failed_subprocess_shows_exit_stdout_stderr_and_raw_diagnostics(self):
        self.launcher.config["port_pack_binary"] = str(BINARY or self.root / "owned-tool")
        if BINARY is None:
            tool = self.root / "owned-tool"
            tool.write_text("owned mocked executable", encoding="utf-8")
            tool.chmod(0o700)
        self.import_fixture()
        with patch("herps_launcher.javamods.adapter.subprocess.run", return_value=
                   subprocess.CompletedProcess(["owned-fixture"], 7, "owned stdout detail", "owned stderr detail")):
            report = self.analyze()
        self.assertEqual(report["status"], "Unsupported")
        self.assertEqual(report["commands"][-1]["exit_code"], 7)
        self.click(self.page.errors_button)
        details = self.page.details.toPlainText()
        self.assertIn("owned stdout detail", details)
        self.assertIn("owned stderr detail", details)
        self.assertIn("7", details)

    def test_failed_library_load_stops_retrying_and_keeps_actionable_error(self):
        self.page.library.root.mkdir(parents=True, exist_ok=True)
        with patch.object(self.page.library, "imports", side_effect=ValueError("owned corrupt receipt; preserve files")) as load:
            self.page.reload()
            self.wait_idle()
            QTest.qWait(50)
            self.app.processEvents()
            self.assertEqual(load.call_count, 1)
        self.assertIn("failed", self.page.status.text().lower())
        self.click(self.page.errors_button)
        self.assertIn("owned corrupt receipt", self.page.details.toPlainText())

    def test_ui_never_promotes_forged_saved_success_statuses(self):
        for status in ("Native compatibility", "Tested successfully", "Compatible through Java bridge"):
            report = {"status": status, "mods": [{"id": "owned", "status": status,
                "raw_evidence": {"check": {"verdict": "works"}}, "diagnostics": []}], "diagnostics": []}
            rendered = "\n".join(self.page._report_lines(report))
            self.assertIn("Compatibility: Unsupported", rendered)
            self.assertIn("adapter status: Unsupported", rendered)
            self.assertIn("insufficient_evidence", rendered)
            self.assertNotIn("Compatibility: " + status, rendered)


@unittest.skipIf(QApplication is None, "Install pinned launcher requirements for Qt integration")
@unittest.skipUnless(BINARY is not None and BINARY.is_file(),
                     "Set HERPS_TEST_PORT_PACK to the actual pinned executable for Java Mods UI regressions")
class JavaModsPageBackendTests(JavaModsHarness):
    def test_actual_false_positive_works_is_rendered_as_unsupported_with_full_evidence(self):
        self.import_fixture(depends={"missinglib": ">=2"}, mixins=True, access=True, invalid_class=True)
        report = self.analyze()
        self.assertEqual(report["status"], "Unsupported")
        self.assertEqual(report["mods"][0]["raw_evidence"]["check"]["verdict"], "works")
        details = self.page.details.toPlainText().lower()
        for expected in ("unsupported", "works", "missinglib", "mixin", "unreadable", "insufficient_evidence"):
            self.assertIn(expected, details)
        self.assertFalse(report["java_bridge_available"])
        self.assertIsNone(report["test_execution"])
        self.assertFalse(self.page.build_button.isEnabled())
        self.assertFalse(self.page.test_button.isEnabled())

    def test_saved_report_is_revalidated_before_rendering_after_profile_reload(self):
        self.import_fixture()
        self.analyze()
        entry = self.page.import_entries[0]
        value = json.loads(entry.report_file.read_text())
        value["status"] = "Tested successfully"
        value["mods"][0]["status"] = "Native compatibility"
        entry.report_file.write_text(json.dumps(value))
        self.page.reload()
        self.wait_idle()
        text = self.page.details.toPlainText()
        self.assertIn("Compatibility: Unsupported", text)
        self.assertIn("adapter status: Unsupported", text)
        self.assertIn("insufficient_evidence", text)

    def test_cancel_is_unavailable_once_result_recording_begins(self):
        self.import_fixture()
        entered, release = threading.Event(), threading.Event()
        original = self.page.library.save_report

        def delayed(*args, **kwargs):
            entered.set()
            release.wait(5)
            return original(*args, **kwargs)
        with patch.object(self.page.library, "save_report", side_effect=delayed):
            try:
                self.click(self.page.analyze_button)
                deadline = time.monotonic() + 3
                while not entered.is_set() and time.monotonic() < deadline:
                    QTest.qWait(10)
                    self.app.processEvents()
                self.assertTrue(entered.is_set())
                self.app.processEvents()
                self.assertFalse(self.page.cancel_button.isEnabled())
                self.page.cancel_analysis()
                self.assertFalse(self.page._cancel.is_set())
            finally:
                release.set()
                self.wait_idle()
        self.assertEqual(self.page.current_report["status"], "Requires porting")

    def test_json_and_readable_exports_preserve_actual_backend_evidence(self):
        self.import_fixture(depends={"missinglib": "*"})
        report = self.analyze()
        for format, button in (("json", self.page.export_json_button), ("text", self.page.export_text_button)):
            output = self.root / ("compatibility.json" if format == "json" else "compatibility.txt")
            with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(output), "")):
                self.click(button)
            self.wait_idle()
            self.assertTrue(output.is_file())
            exported = output.read_text(encoding="utf-8")
            self.assertIn("Unsupported", exported)
            self.assertIn("missinglib", exported)
            self.assertIn("works", exported)
            if format == "json":
                value = json.loads(exported)
                self.assertEqual(value["status"], report["status"])
                self.assertIsNone(value["test_execution"])
                self.assertFalse(value["java_bridge_available"])

    def test_resolve_dependencies_uses_user_directory_and_retains_hash_evidence(self):
        dependency_dir = self.root / "owned dependencies"
        dependency = make_jar(dependency_dir / "library.jar", mod_id="library", version="2")
        self.import_fixture(depends={"library": ">=2"})
        self.assertEqual(self.analyze()["status"], "Unsupported")
        with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value=str(dependency_dir)):
            self.click(self.page.resolve_button)
        self.wait_idle()
        entry = self.page.import_entries[self.page.import_list.currentRow()]
        self.assertEqual(Path(entry.dependencies), dependency_dir)
        report = self.analyze()
        self.assertEqual(report["status"], "Requires porting")
        evidence = report["raw_evidence"]["dependency_files"]["library"]
        self.assertEqual(evidence["sha256"], digest(dependency))
        self.assertIn("library", self.page.details.toPlainText())

    def test_background_analysis_keeps_event_loop_live_and_blocks_profile_mutations(self):
        self.new_profile("separate")
        self.window.profile.setCurrentText("default")
        self.app.processEvents()
        self.import_fixture()
        entered, release = threading.Event(), threading.Event()
        original = PortPackAdapter.check

        def delayed(adapter, *args, **kwargs):
            entered.set()
            release.wait(5)
            return original(adapter, *args, **kwargs)

        with patch.object(PortPackAdapter, "check", delayed):
            try:
                self.click(self.page.analyze_button)
                deadline = time.monotonic() + 2
                while not entered.is_set() and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertTrue(entered.is_set())
                self.assertFalse(self.page.import_button.isEnabled())
                self.assertFalse(self.page.analyze_button.isEnabled())
                timer_ticks = []
                QTimer.singleShot(0, lambda: timer_ticks.append("event processed"))
                QTest.qWait(30)
                self.app.processEvents()
                self.assertEqual(timer_ticks, ["event processed"])
                self.window.profile.setCurrentText("separate")
                self.app.processEvents()
                self.assertEqual(self.launcher.config["profile"], "default")
                self.assertEqual(self.window.profile.currentText(), "default")
            finally:
                release.set()
                self.wait_idle()
        self.assertEqual(self.page.current_report["status"], "Requires porting")
        self.assertTrue(self.page.import_button.isEnabled())

    def test_cancelled_analysis_discards_new_report_after_passive_worker_finishes(self):
        self.import_fixture()
        entered, release = threading.Event(), threading.Event()
        original = PortPackAdapter.check

        def delayed(adapter, *args, **kwargs):
            entered.set()
            release.wait(5)
            return original(adapter, *args, **kwargs)

        with patch.object(PortPackAdapter, "check", delayed):
            try:
                self.click(self.page.analyze_button)
                deadline = time.monotonic() + 2
                while not entered.is_set() and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertTrue(entered.is_set())
                self.click(self.page.cancel_button)
            finally:
                release.set()
                self.wait_idle()
        self.assertIsNone(self.page.current_report)
        self.assertFalse(self.page.cancel_button.isEnabled())
        self.assertTrue(self.page.analyze_button.isEnabled())
        self.assertIn("cancel", self.page.status.text().lower())

    def test_port_enable_disable_and_backup_preserve_saves_and_original_import(self):
        original = self.import_fixture()
        source_hash = digest(original)
        world = self.launcher.game / "saves/Owned/level.dat"
        world.parent.mkdir(parents=True)
        world.write_bytes(b"owned save sentinel")
        moddata = self.launcher.game / "horizon-mod-data/demo/sentinel.txt"
        moddata.parent.mkdir(parents=True)
        moddata.write_bytes(b"owned mod data sentinel")
        self.analyze()
        self.click(self.page.port_button)
        self.wait_idle()
        self.assertEqual(self.page.port_list.count(), 1)
        self.page.port_list.setCurrentRow(0)
        self.app.processEvents()
        port = self.page.port_entries[0]
        self.assertTrue((Path(port.path) / "horizon-mod.toml").is_file())
        self.assertFalse(port.enabled)
        self.click(self.page.port_details_button)
        self.assertIn("Requires porting", self.page.details.toPlainText())
        self.click(self.page.enable_button)
        self.wait_idle()
        self.assertEqual(pairs(self.launcher.game / "horizon-mods.txt")["mod.demo"], "true")
        self.click(self.page.enable_button)
        self.wait_idle()
        self.assertEqual(pairs(self.launcher.game / "horizon-mods.txt")["mod.demo"], "false")
        with patch("PySide6.QtGui.QDesktopServices.openUrl", return_value=True) as opened:
            self.click(self.page.open_folder_button)
        self.assertTrue(opened.called)
        self.assertTrue(opened.call_args.args[0].isLocalFile())
        self.click(self.page.remove_button)
        self.wait_idle()
        self.assertEqual(self.page.port_list.count(), 0)
        self.assertFalse(Path(port.path).exists())
        self.assertTrue(list((self.launcher.game / "java-mods/removed").rglob("horizon-mod.toml")))
        self.assertEqual(world.read_bytes(), b"owned save sentinel")
        self.assertEqual(moddata.read_bytes(), b"owned mod data sentinel")
        self.assertEqual(digest(original), source_hash)


if __name__ == "__main__":
    unittest.main()
