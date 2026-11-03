"""Java archive management UI using passive inspection and real port-pack evidence."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from threading import Event, Lock

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMessageBox, QProgressBar, QPushButton, QSplitter, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget)

from .adapter import PortPackAdapter, REQUIRES_PORTING, UNSUPPORTED
from .library import JavaModLibrary


def _short(value, limit=12000):
    value = str(value)
    return value if len(value) <= limit else value[:limit] + "\n[Display shortened; export retains the full evidence.]"


class JavaModsPage(QWidget):
    """Profile-scoped UI. All archive, hash, report and process work runs off-thread."""

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.launcher = window.launcher
        self.library = None
        self.import_entries = []
        self.port_entries = []
        self.reports = {}
        self.port_reports = {}
        self._profile = None
        self._dirty = True
        self._operation = ""
        self._cancel = Event()
        self._cancel_lock = Lock()
        self._committing = False
        self._last_error = ""
        self._scheduled = False

        box = QVBoxLayout(self)
        box.setSpacing(12)
        heading = QLabel("Java Mods")
        heading.setObjectName("heading")
        box.addWidget(heading)
        description = QLabel("Inspect Fabric, Forge and NeoForge JARs without executing mod code. "
            "Only supported data content can be carried over; Java gameplay code, mixins and a Java bridge are unavailable.")
        description.setObjectName("muted")
        description.setWordWrap(True)
        box.addWidget(description)

        backend = QHBoxLayout()
        self.binary_path = QLineEdit()
        self.binary_path.setReadOnly(True)
        self.binary_path.setPlaceholderText("Automatic discovery · trusted horizon-port-pack build required")
        backend.addWidget(self.binary_path, 1)
        self.binary_button = self._button(backend, "Select backend…", self.choose_binary)
        box.addLayout(backend)

        splitter = QSplitter()
        self.tabs = QTabWidget()
        imported = QWidget()
        imported_box = QVBoxLayout(imported)
        self.import_list = QListWidget()
        self.import_list.currentRowChanged.connect(lambda _: self.show_import_details())
        imported_box.addWidget(self.import_list, 1)
        row = QHBoxLayout()
        self.import_button = self._button(row, "Import Java mod…", self.import_mod)
        self.refresh_button = self._button(row, "Refresh", self.reload)
        imported_box.addLayout(row)
        row = QHBoxLayout()
        self.analyze_button = self._button(row, "Analyze", self.analyze)
        self.resolve_button = self._button(row, "Resolve dependencies…", self.resolve_dependencies)
        imported_box.addLayout(row)
        self.port_button = self._button(imported_box, "Port to Herspers · data only", self.port_mod)
        self.tabs.addTab(imported, "Imported Java mods")

        ported = QWidget()
        ported_box = QVBoxLayout(ported)
        self.port_list = QListWidget()
        self.port_list.currentRowChanged.connect(lambda _: self.show_port_details())
        ported_box.addWidget(self.port_list, 1)
        row = QHBoxLayout()
        self.enable_button = self._button(row, "Enable / disable", self.toggle_port)
        self.remove_button = self._button(row, "Remove to backup", self.remove_port)
        ported_box.addLayout(row)
        self.open_folder_button = self._button(ported_box, "Open mod directory", self.open_port_folder)
        self.port_details_button = self._button(ported_box, "View compatibility details", self.show_port_details)
        self.tabs.addTab(ported, "Local data ports")
        self.tabs.currentChanged.connect(lambda _: self.show_selected_details())
        splitter.addWidget(self.tabs)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Import a Java mod to inspect its metadata and compatibility evidence.")
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        box.addWidget(splitter, 1)

        row = QHBoxLayout()
        self.export_json_button = self._button(row, "Export JSON…", lambda: self.export_report("json"))
        self.export_text_button = self._button(row, "Export text…", lambda: self.export_report("text"))
        self.errors_button = self._button(row, "View errors", self.view_errors)
        self.build_button = self._button(row, "Build Mod · Not available yet", lambda: None)
        self.test_button = self._button(row, "Test Mod · Not available yet", lambda: None)
        for button in (self.build_button, self.test_button):
            button.setEnabled(False)
            button.setToolTip("Not available yet. The native .hnmod smoke check does not build or test Java mods.")
        box.addLayout(row)
        self.status = QLabel("Select this page to load the current profile's Java mods.")
        self.status.setWordWrap(True)
        box.addWidget(self.status)
        row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        row.addWidget(self.progress, 1)
        self.cancel_button = self._button(row, "Discard analysis", self.cancel_analysis)
        self.cancel_button.setToolTip("Waits for the current tool call to finish, then discards its result. Does not terminate the process.")
        box.addLayout(row)
        self.refresh_profile()

    def _button(self, layout, label, function):
        button = QPushButton(label)
        button.clicked.connect(lambda: self.window.guard(function))
        layout.addWidget(button)
        return button

    @property
    def enabled_port_count(self):
        return sum(bool(port.enabled) for port in self.port_entries)

    @property
    def current_report(self):
        entry = self._selected(False) if self.tabs.currentIndex() == 0 else self._selected(True)
        if entry is None:
            return None
        return (self.reports.get(entry.token) if self.tabs.currentIndex() == 0
                else self.port_reports.get(entry.id))

    def _active(self):
        return getattr(self.window, "pages", None) is not None and self.window.pages.currentWidget() is self

    def refresh_profile(self):
        profile = self.launcher.config["profile"]
        if profile != self._profile:
            self._profile = profile
            self.library = JavaModLibrary(self.launcher)
            self.import_entries, self.port_entries = [], []
            self.reports, self.port_reports = {}, {}
            self.import_list.clear()
            self.port_list.clear()
            self.details.clear()
            self._dirty = True
            self.status.setText(f"Profile: {profile}. Import a Java mod or load existing local entries.")
        self.binary_path.setText(self.launcher.config.get("port_pack_binary", ""))
        self.busy_changed()

    def busy_changed(self):
        busy = self.window.busy()
        selected = self._selected(False) is not None
        ported = self._selected(True) is not None
        for button in (self.import_button, self.refresh_button, self.binary_button):
            button.setEnabled(not busy)
        for button in (self.analyze_button, self.resolve_button, self.port_button):
            button.setEnabled(not busy and selected)
        for button in (self.enable_button, self.remove_button, self.open_folder_button, self.port_details_button):
            button.setEnabled(not busy and ported)
        self.import_list.setEnabled(not busy)
        self.port_list.setEnabled(not busy)
        exportable = bool(self._report_file())
        self.export_json_button.setEnabled(not busy and exportable)
        self.export_text_button.setEnabled(not busy and exportable)
        self.cancel_button.setEnabled(busy and self._operation == "analysis" and not self._cancel.is_set())
        if self._committing:
            self.cancel_button.setEnabled(False)
        self.errors_button.setEnabled(not busy and (self.current_report is not None or bool(self._last_error)))
        self.build_button.setEnabled(False)
        self.test_button.setEnabled(False)
        if self._dirty and self._active() and not busy and not self._scheduled:
            self._scheduled = True
            QTimer.singleShot(0, self._load_if_idle)

    def _selected(self, ported=False):
        entries = self.port_entries if ported else self.import_entries
        index = self.port_list.currentRow() if ported else self.import_list.currentRow()
        return entries[index] if 0 <= index < len(entries) else None

    def _require_selected(self, ported=False):
        self.window.require_idle()
        entry = self._selected(ported)
        if entry is None:
            raise ValueError("Select a local data port first" if ported else "Import and select a Java mod first")
        return entry

    def _report_file(self):
        entry = self._selected(self.tabs.currentIndex() == 1)
        return getattr(entry, "report_file", None) if entry else None

    def _read_report(self, path):
        if path is None:
            return None
        path = Path(path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 << 20:
            raise ValueError("Saved compatibility report is missing, linked or too large")
        # Reuse Step 1's snapshot/hash/dependency validation before displaying a
        # saved status. The original JSON evidence remains inside the export.
        staging = self.library.root / "staging"
        self.library._safe(staging)
        staging.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="view-report-", dir=staging) as directory:
            exported = Path(directory) / "report.json"
            PortPackAdapter(self.launcher).export_report(path, exported)
            return json.loads(exported.read_text(encoding="utf-8"))

    def _snapshot(self, library, token=None, port_id=None):
        imports, ports = library.imports(), library.ports()
        selected = next((entry for entry in imports if entry.token == token), imports[0] if imports else None)
        port = next((entry for entry in ports if entry.id == port_id), ports[0] if ports else None)
        reports, port_reports = {}, {}
        if selected:
            reports[selected.token] = self._read_report(selected.report_file)
        if port:
            port_reports[port.id] = self._read_report(port.report_file)
        return imports, ports, reports, port_reports

    def _apply_snapshot(self, snapshot, token=None, port_id=None):
        self.import_entries, self.port_entries, reports, port_reports = snapshot
        self.reports.update(reports)
        self.port_reports.update(port_reports)
        for widget, entries, key, wanted in ((self.import_list, self.import_entries, "token", token),
                                             (self.port_list, self.port_entries, "id", port_id)):
            widget.blockSignals(True)
            widget.clear()
            selected = 0
            for index, entry in enumerate(entries):
                text = f"{entry.name or getattr(entry, 'mod_id', entry.id if hasattr(entry, 'id') else '')} {entry.version}"
                text += f" · {entry.loader or 'unknown loader'}" if key == "token" else f" · {'ON' if entry.enabled else 'OFF'} · data only"
                widget.addItem(text)
                if getattr(entry, key) == wanted:
                    selected = index
            if entries:
                widget.setCurrentRow(selected)
            widget.blockSignals(False)
        self._dirty = False
        self.show_selected_details()

    def _run(self, operation, label, function, done):
        self.window.require_idle()
        self._operation = operation
        self._cancel = Event()
        self._committing = False
        self._last_error = ""
        self.status.setText(label)
        self.progress.setRange(0, 0)

        def completed(result):
            self._operation = ""
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
            done(result)

        def failed(message):
            self._operation = ""
            self.progress.setRange(0, 1)
            self.progress.setValue(0)
            self._last_error = message
            self.status.setText("Operation failed. No successful result is claimed.")
            self.details.append("\nOperation error:\n" + _short(message))

        def progress(message):
            self.status.setText(str(message))
            self.busy_changed()
        self.window.start_work(function, done=completed, failed=failed, progress=progress)
        self.busy_changed()

    def _load_if_idle(self):
        self._scheduled = False
        if not self._dirty or not self._active() or self.window.busy():
            return
        library = self.library
        self._dirty = False
        if not library.root.exists():
            self.status.setText(f"Profile: {self._profile} · no imported JARs or local data ports yet.")
            self.busy_changed()
            return
        token = getattr(self._selected(), "token", None)
        port_id = getattr(self._selected(True), "id", None)

        def done(snapshot):
            self._apply_snapshot(snapshot, token, port_id)
            self.status.setText(f"Profile: {self._profile} · {len(self.import_entries)} imported JARs · {len(self.port_entries)} local data ports.")
        self._run("load", "Loading and verifying local Java mod files…", lambda progress: self._snapshot(library, token, port_id), done)

    def reload(self):
        self.window.require_idle()
        self._dirty = True
        self._load_if_idle()

    def choose_binary(self):
        self.window.require_idle()
        path, _ = QFileDialog.getOpenFileName(self, "Select trusted horizon-port-pack executable")
        if path:
            self.launcher.config["port_pack_binary"] = str(Path(path).expanduser().absolute())
            self.launcher.save()
            self.binary_path.setText(self.launcher.config["port_pack_binary"])
            self.status.setText("Backend path saved. The next operation records its hash and actual process results.")

    def import_mod(self):
        self.window.require_idle()
        self.refresh_profile()
        path, _ = QFileDialog.getOpenFileName(self, "Import Fabric, Forge or NeoForge mod", filter="Java mod archives (*.jar)")
        if not path:
            return
        library = self.library

        def work(progress):
            progress("Copying and passively inspecting the JAR; mod code is never executed…")
            entry = library.import_jar(Path(path))
            return entry.token, self._snapshot(library, entry.token)

        def done(result):
            token, snapshot = result
            self.tabs.setCurrentIndex(0)
            self._apply_snapshot(snapshot, token)
            self.status.setText("Java mod imported locally. Compatibility is unverified until analysis; nothing was enabled.")
        self._run("import", "Importing Java mod…", work, done)

    def _acknowledge(self, entry):
        licence = getattr(getattr(entry, "metadata", None), "license", "")
        restricted = any(part in licence.lower() for part in
            ("-nd", "-nc", "no derivatives", "noncommercial", "non-commercial", "all rights reserved", "all-rights-reserved"))
        if not restricted:
            return False
        answer = QMessageBox.warning(self, "Review restricted mod licence",
            f"Declared licence: {licence}\n\nThe backend's check command also generates a local data port. "
            "Review the licence before continuing. Acknowledgement does not grant permission to modify or redistribute this mod. "
            "Generated content stays local. Continue only if your use is permitted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        return answer == QMessageBox.StandardButton.Yes

    def analyze(self, dependencies=None):
        entry = self._require_selected()
        acknowledge = self._acknowledge(entry)
        if getattr(entry.metadata, "license", "") and any(part in entry.metadata.license.lower() for part in
                ("-nd", "-nc", "no derivatives", "noncommercial", "non-commercial", "all rights reserved", "all-rights-reserved")) and not acknowledge:
            self.status.setText("Analysis cancelled before the backend's local carry-over; restricted licence was not acknowledged.")
            return
        library, adapter = self.library, PortPackAdapter(self.launcher)
        folder = Path(dependencies) if dependencies is not None else entry.dependencies

        def work(progress):
            progress("Analyzing metadata and data-tier evidence. The tool call cannot be interrupted; Discard waits for it to finish.")
            report = adapter.check(entry.path, dependencies=folder, acknowledge_restricted=acknowledge)
            with self._cancel_lock:
                if self._cancel.is_set():
                    return None
                self._committing = True
            progress("Recording completed analysis. Discard is no longer available during this atomic update…")
            library.save_report(entry.token, report)
            if dependencies is not None:
                library.set_dependencies(entry.token, folder)
            return report, self._snapshot(library, entry.token)

        def done(result):
            if result is None:
                self.status.setText("Analysis cancelled: result discarded after the tool returned. No result was selected, installed or enabled; temporary run evidence remains local.")
                return
            report, snapshot = result
            self.reports[entry.token] = report.to_dict()
            self._apply_snapshot(snapshot, entry.token)
            self.status.setText(f"Analysis completed: {report.status}. Review the reasons and original backend verdict; no gameplay test ran.")
        self._run("analysis", "Analyzing Java mod…", work, done)

    def resolve_dependencies(self):
        self._require_selected()
        path = QFileDialog.getExistingDirectory(self, "Choose your own mod directory or Minecraft instance")
        if path:
            self.analyze(Path(path))

    def cancel_analysis(self):
        if self._operation == "analysis":
            with self._cancel_lock:
                if self._committing:
                    self.cancel_button.setEnabled(False)
                    self.status.setText("The completed analysis is already being recorded; wait for the update to finish.")
                    return
                self._cancel.set()
            self.cancel_button.setEnabled(False)
            self.status.setText("Discard requested. Waiting for the current tool call/timeout; no thread or process is forcibly terminated.")

    def port_mod(self):
        entry = self._require_selected()
        acknowledge = self._acknowledge(entry)
        licence = entry.metadata.license.lower()
        if any(part in licence for part in ("-nd", "-nc", "no derivatives", "noncommercial", "non-commercial", "all rights reserved", "all-rights-reserved")) and not acknowledge:
            self.status.setText("Port cancelled before carry-over; restricted licence was not acknowledged.")
            return
        library, adapter = self.library, PortPackAdapter(self.launcher)

        def work(progress):
            progress("Checking and carrying supported data only. Port/install cannot be interrupted; Java code is not converted.")
            report = adapter.port(entry.path, dependencies=entry.dependencies, acknowledge_restricted=acknowledge)
            library.save_report(entry.token, report)
            ported = None
            if report.status == REQUIRES_PORTING and any(mod.port_path for mod in report.mods):
                progress("Verifying and installing the local data port disabled…")
                ported = library.install_port(entry.token, report)
            return report, ported, self._snapshot(library, entry.token, ported.id if ported else None)

        def done(result):
            report, ported, snapshot = result
            self.reports[entry.token] = report.to_dict()
            self._apply_snapshot(snapshot, entry.token, ported.id if ported else None)
            if ported:
                self.tabs.setCurrentIndex(1)
                self.show_port_details()
                self.status.setText("Local data port installed disabled. Java functionality was not converted, and gameplay is unverified.")
            else:
                self.status.setText(f"Port not installed: {report.status}. See the retained reasons; no build/test success is claimed.")
        self._run("port", "Porting supported data…", work, done)

    def toggle_port(self):
        entry = self._require_selected(True)
        library = self.library
        token = getattr(self._selected(), "token", None)

        def work(progress):
            library.enable_port(entry, not entry.enabled)
            return self._snapshot(library, token, entry.id)

        def done(snapshot):
            self._apply_snapshot(snapshot, token, entry.id)
            self.status.setText("Data port enable state saved. Gameplay compatibility remains unverified.")
        self._run("manage", "Verifying data port and updating enable state…", work, done)

    def remove_port(self):
        entry = self._require_selected(True)
        library = self.library
        token = getattr(self._selected(), "token", None)

        def work(progress):
            backup = library.remove_port(entry)
            return backup, self._snapshot(library, token)

        def done(result):
            backup, snapshot = result
            self._apply_snapshot(snapshot, token)
            self.status.setText(f"Data port disabled and moved to backup: {backup}")
        self._run("manage", "Removing local data port to backup…", work, done)

    def open_port_folder(self):
        entry = self._require_selected(True)
        self.window.open_path(entry.path)

    def export_report(self, format):
        self.window.require_idle()
        source = self._report_file()
        if not source:
            raise ValueError("Analyze the selected Java mod before exporting a compatibility report")
        suffix = "json" if format == "json" else "txt"
        path, _ = QFileDialog.getSaveFileName(self, "Export compatibility evidence", f"java-mod-compatibility.{suffix}",
                                            f"{'JSON' if format == 'json' else 'Text'} reports (*.{suffix})")
        if not path:
            return
        adapter = PortPackAdapter(self.launcher)
        self._run("export", "Revalidating retained evidence and exporting report…",
                  lambda progress: adapter.export_report(Path(source), Path(path), format),
                  lambda output: self.status.setText(f"Report exported with retained evidence: {output}"))

    def view_errors(self):
        self.window.require_idle()
        lines = ["Actual diagnostics and process output. No build or gameplay result is inferred."]
        if self._last_error:
            lines += ["Operation error:", self._last_error]
        lines += self._report_lines(self.current_report)
        self.details.setPlainText(_short("\n".join(lines), 100000))

    def show_selected_details(self):
        if self.tabs.currentIndex() == 0:
            self.show_import_details()
        else:
            self.show_port_details()

    def _load_selected_report(self, entry, ported):
        cache, key = (self.port_reports, entry.id) if ported else (self.reports, entry.token)
        if key in cache or not entry.report_file or self.window.busy():
            return

        def done(data):
            cache[key] = data
            self.show_selected_details()
            self.status.setText("Saved compatibility evidence revalidated. Review the conservative status and reasons; no gameplay test ran.")
        self._run("load-report", "Loading saved compatibility evidence…",
                  lambda progress: self._read_report(entry.report_file), done)

    def show_import_details(self):
        entry = self._selected()
        if entry is None:
            if self.tabs.currentIndex() == 0:
                self.details.setPlainText("Import a Fabric, Forge or NeoForge .jar. Inspection never executes imported mod code.")
            self.busy_changed()
            return
        if self.tabs.currentIndex() != 0:
            return
        meta = asdict(entry.metadata)
        lines = [f"{entry.name} · {entry.mod_id} · {entry.version}", f"Loader: {entry.loader or 'Unknown'}",
                 f"Minecraft requirement: {meta.get('required_dependencies', {}).get('minecraft', 'Unknown / not declared')}",
                 f"Licence: {meta.get('license') or 'Unknown'}",
                 "Required dependencies: " + json.dumps(meta.get("required_dependencies", {}), ensure_ascii=False),
                 "Mixins: " + ", ".join(meta.get("mixins", [])),
                 "Access wideners / transformers: " + ", ".join(meta.get("access_changes", [])),
                 f"Class files: {meta.get('class_count', 0)}", ""]
        report = self.reports.get(entry.token)
        lines.extend(self._report_lines(report))
        if not report:
            lines += ["Passive inspection findings:"] + [f"  {d['code']}: {d['message']}" for d in meta.get("diagnostics", [])]
        lines += ["", f"Input SHA-256: {entry.sha256}", f"Profile-local input: {entry.path}",
                  f"Dependency source: {entry.dependencies or 'No user directory selected'}"]
        self.details.setPlainText(_short("\n".join(map(str, lines)), 100000))
        self.busy_changed()
        self._load_selected_report(entry, False)

    def show_port_details(self):
        entry = self._selected(True)
        if self.tabs.currentIndex() != 1:
            return
        if entry is None:
            self.details.setPlainText("Supported data-tier ports appear here after verified local installation. Java code and gameplay are not converted.")
            self.busy_changed()
            return
        lines = [f"{entry.name} · {entry.id} · {entry.version}", f"Enabled: {entry.enabled}",
                 f"Local data directory: {entry.path}", "Java functionality was not converted. No gameplay test ran.", ""]
        lines.extend(self._report_lines(self.port_reports.get(entry.id)))
        self.details.setPlainText(_short("\n".join(lines), 100000))
        self.busy_changed()
        self._load_selected_report(entry, True)

    @staticmethod
    def _report_lines(report):
        if report is None:
            return ["Compatibility: Unsupported", "Evidence: unknown / not analyzed. This does not establish proven incompatibility.",
                    "Build Mod: Not available yet · Test Mod: Not available yet", "Java bridge: unavailable"]
        raw_status = report.get("status")
        status = raw_status if raw_status in (UNSUPPORTED, REQUIRES_PORTING) else UNSUPPORTED
        lines = [f"Compatibility: {status}", "Static analysis only; gameplay is unverified.", "Java bridge: unavailable"]
        if status != raw_status:
            lines.append("insufficient_evidence: Saved status is not supported by this UI; exported evidence must be revalidated.")
        for row in [report, *report.get("mods", [])]:
            if row is not report:
                mod_status = row.get("status")
                shown_status = mod_status if mod_status in (UNSUPPORTED, REQUIRES_PORTING) else UNSUPPORTED
                lines += ["", f"Mod: {row.get('id', 'Unknown')} · adapter status: {shown_status}"]
                if mod_status != shown_status:
                    lines.append("insufficient_evidence: This saved per-mod status is not a validated compatibility or test result.")
                check = row.get("raw_evidence", {}).get("check", {})
                if isinstance(check, dict) and check:
                    lines += [f"Original backend verdict: {check.get('verdict', 'Not recorded')} (static backend evidence; not a compatibility/test receipt)",
                              "Backend summary: " + _short(check.get("summary", "")),
                              "Backend skipped / unsupported: " + _short(json.dumps(check.get("skipped", []), ensure_ascii=False)),
                              "Backend code features: " + _short(json.dumps(check.get("code", {}), ensure_ascii=False))]
                if row.get("port_path"):
                    lines.append("Generated data path: " + str(row["port_path"]))
            for diagnostic in row.get("diagnostics", []):
                code = diagnostic.get("code", "Unknown")
                prefix = "Missing / incomplete evidence" if code == "insufficient_evidence" else "Finding"
                lines.append(f"{prefix} · {code}: {_short(diagnostic.get('message', ''))}")
        dependencies = report.get("raw_evidence", {}).get("dependency_files", {})
        if dependencies:
            lines.append("\nUser-provided dependency hash evidence (no automatic downloads):")
            for key, evidence in dependencies.items():
                lines.append(f"{key} {evidence.get('version', '')} · SHA-256 {evidence.get('sha256', 'Missing')}")
        lines += ["", f"Operation: {report.get('operation', 'Unknown')} · Profile: {report.get('profile', 'Unknown')}",
                  f"Evidence workspace: {report.get('workspace', 'Unknown')}"]
        for command in report.get("commands", []):
            lines += ["", "Command: " + _short(json.dumps(command.get("argv", []), ensure_ascii=False)),
                      f"Exit code: {command.get('exit_code')} · timed out: {command.get('timed_out', False)}",
                      "stdout:\n" + _short(command.get("stdout", "")), "stderr:\n" + _short(command.get("stderr", ""))]
        return lines
