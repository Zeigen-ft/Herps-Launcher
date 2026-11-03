"""Profile-local modpack UI over the existing passive Rust/adapter workflow."""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QFileDialog, QGroupBox,
    QHeaderView, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox,
    QProgressBar, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget)

from .service import ModpackLibrary


UNSUPPORTED = "Unsupported"
REQUIRES_PORTING = "Requires porting"
PLAY_REASON = ("Play is unavailable: imported packs have no verified game/content "
               "validation and launch backend. A local data carry-over is not a fully playable modpack.")


def _short(value, limit=20000):
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "\n[Display shortened; export retains the full evidence.]"


def _data(value):
    return value.to_dict() if hasattr(value, "to_dict") else value


class ModpacksPage(QWidget):
    """Never installs or launches a pack; expensive operations use Window's worker."""

    def __init__(self, window):
        super().__init__()
        self.window, self.launcher = window, window.launcher
        self.library = None
        self.pack_entries = []
        self.reports = {}
        self.current_report = None
        self._profile = None
        self._dirty = True
        self._scheduled = False
        self._last_error = ""

        box = QVBoxLayout(self)
        box.setSpacing(10)
        heading = QLabel("Modpacks")
        heading.setObjectName("heading")
        box.addWidget(heading)
        description = QLabel("Import Modrinth .mrpack, CurseForge ZIP or Prism/MultiMC instances. "
            "Analysis never executes Java mod code. packwiz is not supported by the current backend.")
        description.setWordWrap(True)
        description.setObjectName("muted")
        box.addWidget(description)

        row = QHBoxLayout()
        self.binary_path = QLineEdit()
        self.binary_path.setReadOnly(True)
        self.binary_path.setPlaceholderText("Automatic discovery · trusted horizon-port-pack build required")
        row.addWidget(self.binary_path, 1)
        self.binary_button = self._button(row, "Select backend…", self.choose_binary)
        box.addLayout(row)

        row = QHBoxLayout()
        self.pack_list = QListWidget()
        self.pack_list.setMaximumHeight(100)
        self.pack_list.currentRowChanged.connect(lambda _: self.show_selected_pack())
        row.addWidget(self.pack_list, 1)
        imports = QVBoxLayout()
        self.import_button = self._button(imports, "Import modpack…", self.import_pack)
        self.instance_button = self._button(imports, "Import instance…", self.import_instance)
        row.addLayout(imports)
        self.refresh_button = self._button(row, "Refresh", self.reload)
        box.addLayout(row)

        self.summary = QLabel("Playable status: unverified. Import a pack to inspect every indexed mod.")
        self.summary.setWordWrap(True)
        box.addWidget(self.summary)
        row = QHBoxLayout()
        self.analyze_button = self._button(row, "Analyze pack", self.analyze)
        self.resolve_button = self._button(row, "Resolve missing files…", self.resolve_missing_files)
        port_group = QGroupBox("Port and Play")
        port_box = QHBoxLayout(port_group)
        self.port_button = self._button(port_box, "Port supported data…", self.port_pack)
        self.play_button = self._button(port_box, "Play · unavailable", lambda: None)
        self.play_button.setEnabled(False)
        self.play_button.setToolTip(PLAY_REASON)
        row.addWidget(port_group)
        box.addLayout(row)

        splitter = QSplitter()
        from PySide6.QtCore import Qt
        splitter.setOrientation(Qt.Orientation.Vertical)
        self.coverage_table = QTableWidget(0, 7)
        self.coverage_table.setHorizontalHeaderLabels(
            ["Name", "Version", "Compatibility", "Reason", "Licence", "Porting tier", "Missing dependencies"])
        self.coverage_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.coverage_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.coverage_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.coverage_table.setWordWrap(True)
        self.coverage_table.setStyleSheet("QTableWidget { background: #19222e; gridline-color: #344252; selection-background-color: #31574a; } "
            "QHeaderView::section { background: #23303e; color: #dde7ee; border: 1px solid #344252; padding: 6px; }")
        header = self.coverage_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for index, width in enumerate((155, 70, 125, 280, 85, 85, 160)):
            self.coverage_table.setColumnWidth(index, width)
        self.coverage_table.currentCellChanged.connect(lambda *_: self.show_coverage_details())
        splitter.addWidget(self.coverage_table)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Every mod remains listed, including unresolved and unsupported content. Select a row for original evidence.")
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        box.addWidget(splitter, 1)

        self.play_reason = QLabel(PLAY_REASON)
        self.play_reason.setWordWrap(True)
        self.play_reason.setObjectName("muted")
        box.addWidget(self.play_reason)
        row = QHBoxLayout()
        self.errors_button = self._button(row, "View errors", self.view_errors)
        self.export_json_button = self._button(row, "Export JSON…", lambda: self.export_report("json"))
        self.export_text_button = self._button(row, "Export text…", lambda: self.export_report("text"))
        self.restricted_ack = QCheckBox("I reviewed restricted licences")
        self.restricted_ack.toggled.connect(self._licence_acknowledged)
        row.addWidget(self.restricted_ack)
        box.addLayout(row)
        self.status = QLabel("Select this page to load the current profile's local pack imports.")
        self.status.setWordWrap(True)
        box.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        box.addWidget(self.progress)
        self.refresh_profile()

    def _button(self, layout, label, callback):
        button = QPushButton(label)
        button.clicked.connect(lambda: self.window.guard(callback))
        layout.addWidget(button)
        return button

    def _active(self):
        return self.window.pages.currentWidget() is self

    def _selected(self):
        index = self.pack_list.currentRow()
        return self.pack_entries[index] if 0 <= index < len(self.pack_entries) else None

    def _require_selected(self):
        self.window.require_idle()
        entry = self._selected()
        if entry is None:
            raise ValueError("Import and select a modpack or instance first")
        return entry

    def refresh_profile(self):
        profile = self.launcher.config["profile"]
        if profile != self._profile:
            self._profile = profile
            self.library = ModpackLibrary(self.launcher)
            self.pack_entries, self.reports = [], {}
            self.current_report = None
            self.pack_list.clear()
            self.coverage_table.setRowCount(0)
            self.details.clear()
            self._dirty = True
            self._last_error = ""
            self.restricted_ack.blockSignals(True)
            self.restricted_ack.setChecked(False)
            self.restricted_ack.blockSignals(False)
            self.summary.setText("Playable status: unverified. No pack analysis is selected for this profile.")
            self.status.setText(f"Profile: {profile}. Import a pack or load its retained local evidence.")
        self.binary_path.setText(self.launcher.config.get("port_pack_binary", ""))
        self.busy_changed()

    def busy_changed(self):
        busy = self.window.busy()
        entry = self._selected()
        for button in (self.import_button, self.instance_button, self.refresh_button, self.binary_button):
            button.setEnabled(not busy)
        for button in (self.analyze_button, self.resolve_button, self.port_button):
            button.setEnabled(not busy and entry is not None)
        exportable = entry is not None and bool(entry.report_file)
        self.export_json_button.setEnabled(not busy and exportable)
        self.export_text_button.setEnabled(not busy and exportable)
        self.errors_button.setEnabled(not busy and (self.current_report is not None or bool(self._last_error)))
        self.pack_list.setEnabled(not busy)
        self.coverage_table.setEnabled(not busy)
        self.restricted_ack.setEnabled(not busy)
        # No verified runtime/content validation backend exists. A static Works
        # verdict or a carried folder can never unlock Play here.
        self.play_button.setEnabled(False)
        if self._dirty and self._active() and not busy and not self._scheduled:
            self._scheduled = True
            QTimer.singleShot(0, self._load_if_idle)

    def _run(self, label, function, done):
        self.window.require_idle()
        self._last_error = ""
        self.status.setText(label)
        self.progress.setRange(0, 0)

        def completed(result):
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
            done(result)

        def failed(message):
            self.progress.setRange(0, 1)
            self.progress.setValue(0)
            self._last_error = message
            self.status.setText("Operation failed. Files and previous evidence are preserved; no playable result is claimed.")
            self.details.append("\nOperation error:\n" + _short(message))

        self.window.start_work(function, done=completed, failed=failed,
                               progress=lambda message: self.status.setText(str(message)))
        self.busy_changed()

    @staticmethod
    def _snapshot(library, token=None):
        entries = library.imports()
        selected = next((entry for entry in entries if entry.token == token), entries[0] if entries else None)
        reports = {}
        if selected and selected.report_file:
            reports[selected.token] = _data(library.load_report(selected.token))
        return entries, reports

    def _apply_snapshot(self, snapshot, token=None):
        self.pack_entries, reports = snapshot
        self.reports.update(reports)
        self.pack_list.blockSignals(True)
        self.pack_list.clear()
        selected = 0
        for index, entry in enumerate(self.pack_entries):
            self.pack_list.addItem(f"{entry.name} · {entry.format}")
            if entry.token == token:
                selected = index
        if self.pack_entries:
            self.pack_list.setCurrentRow(selected)
        self.pack_list.blockSignals(False)
        self._dirty = False
        self.show_selected_pack()

    def _load_if_idle(self):
        self._scheduled = False
        if not self._dirty or not self._active() or self.window.busy():
            return
        self._dirty = False
        library = self.library
        root = getattr(library, "root", None)
        if root is not None and not Path(root).exists():
            self.status.setText(f"Profile: {self._profile} · no imported modpacks yet.")
            self.busy_changed()
            return
        token = getattr(self._selected(), "token", None)

        def done(snapshot):
            self._apply_snapshot(snapshot, token)
            self.status.setText(f"Profile: {self._profile} · {len(self.pack_entries)} local pack imports. Play remains unavailable.")
        self._run("Loading and verifying profile-local pack imports…", lambda progress: self._snapshot(library, token), done)

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
            self.status.setText("Backend path saved; its actual command output and hash are recorded by analysis.")

    def import_pack(self):
        self.window.require_idle()
        path, _ = QFileDialog.getOpenFileName(self, "Import supported modpack", filter="Modrinth / CurseForge packs (*.mrpack *.zip)")
        if path:
            self._import(Path(path))

    def import_instance(self):
        self.window.require_idle()
        path = QFileDialog.getExistingDirectory(self, "Import your own Prism, MultiMC or Minecraft instance")
        if path:
            self._import(Path(path))

    def _import(self, path):
        library = self.library

        def work(progress):
            progress("Snapshotting local pack metadata and files. Imported mod code is never executed…")
            entry = library.import_pack(path)
            return entry.token, self._snapshot(library, entry.token)

        def done(result):
            token, snapshot = result
            self._apply_snapshot(snapshot, token)
            self.status.setText("Pack imported locally. Analyze and resolve every missing file; nothing was activated or launched.")
        self._run("Importing local modpack…", work, done)

    def _licence_acknowledged(self, checked):
        if not checked:
            return
        answer = QMessageBox.warning(self, "Review restricted mod licences",
            "The underlying check operation can generate local data carry-over. Review each mod's declared licence before acknowledging restricted, "
            "non-commercial or no-derivatives content. This acknowledgement grants no modification or redistribution permission. "
            "Generated ports stay local. Continue only if your use is permitted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if answer != QMessageBox.StandardButton.Yes:
            self.restricted_ack.blockSignals(True)
            self.restricted_ack.setChecked(False)
            self.restricted_ack.blockSignals(False)

    def analyze(self, dependencies=None):
        self._execute("analyze", dependencies)

    def resolve_missing_files(self):
        self._require_selected()
        folder = QFileDialog.getExistingDirectory(self, "Choose your own mod folder or installed instance; no API keys or downloads")
        if folder:
            self.analyze(Path(folder))

    def port_pack(self):
        self._execute("port")

    def _execute(self, operation, dependencies=None):
        entry = self._require_selected()
        library = self.library
        acknowledge = self.restricted_ack.isChecked()

        def work(progress):
            progress("Carrying only supported local data; no content is installed or launched…" if operation == "port"
                     else "Analyzing every indexed mod and retaining missing/unsupported evidence…")
            method = getattr(library, operation)
            report = method(entry.token, dependencies=dependencies, acknowledge_restricted=acknowledge)
            return _data(report), self._snapshot(library, entry.token)

        def done(result):
            report, snapshot = result
            self.reports[entry.token] = report
            self._apply_snapshot(snapshot, entry.token)
            self.status.setText("Data carry-over finished; inspect the retained coverage. Play remains unavailable and no content was activated."
                                if operation == "port" else "Pack analysis completed. Review all missing files, dependencies and compatibility reasons.")
        self._run("Porting supported data only…" if operation == "port" else "Analyzing modpack…", work, done)

    def show_selected_pack(self):
        entry = self._selected()
        self.current_report = self.reports.get(entry.token) if entry else None
        self.coverage_table.setRowCount(0)
        if entry is None:
            self.summary.setText("Playable status: unverified. Import a supported pack or instance first.")
            self.details.setPlainText("packwiz is not supported by the current Rust backend. Missing or unsupported mods are never omitted from coverage.")
        elif self.current_report is not None:
            self._render(self.current_report)
        else:
            self.summary.setText("Playable status: unverified. This pack has no selected analysis result.")
            self.details.setPlainText(f"{entry.name}\nFormat: {entry.format}\nProfile-local source: {entry.source}\n"
                f"Missing-file source: {entry.dependencies or 'No user folder selected'}\n\n{PLAY_REASON}")
            if entry.report_file and not self.window.busy():
                library, token = self.library, entry.token

                def done(data):
                    self.reports[token] = _data(data)
                    self.show_selected_pack()
                    self.status.setText("Saved pack evidence revalidated. Play remains unavailable.")
                self._run("Loading and revalidating saved pack report…", lambda progress: library.load_report(token), done)
        self.busy_changed()

    def _render(self, report):
        if not isinstance(report, dict) or not isinstance(report.get("rows"), list):
            raise ValueError("Pack report has an invalid coverage structure")
        status = report.get("status")
        shown = status if status in (UNSUPPORTED, REQUIRES_PORTING) else UNSUPPORTED
        summary = str(report.get("summary", "Evidence is insufficient to establish a playable pack."))
        if shown != status or report.get("playable_verified") or report.get("play_enabled"):
            shown = UNSUPPORTED
            summary = "insufficient_evidence: a playable/native/tested claim cannot be established by the available static backend."
        self.summary.setText(f"Playable status: unverified · {shown}\n{summary}")
        self.play_reason.setText(PLAY_REASON)
        self.play_button.setToolTip(PLAY_REASON)
        self.play_button.setEnabled(False)
        self.coverage_table.blockSignals(True)
        self.coverage_table.setRowCount(len(report["rows"]))
        for index, row in enumerate(report["rows"]):
            row_status = row.get("status")
            shown_status = row_status if row_status in (UNSUPPORTED, REQUIRES_PORTING) else UNSUPPORTED
            values = [row.get("name") or row.get("id", "Unknown"), row.get("version") or "Unknown",
                      shown_status, row.get("reason") or "insufficient_evidence: no reason recorded",
                      row.get("license") or "Unknown", row.get("tier") or "Unknown",
                      ", ".join(map(str, row.get("missing_dependencies", []))) or "None recorded"]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.coverage_table.setItem(index, column, item)
        if report["rows"]:
            self.coverage_table.selectRow(0)
        self.coverage_table.blockSignals(False)
        self.show_coverage_details()

    def _report_details(self, errors_only=False):
        report = self.current_report
        lines = ["Playable status: unverified. Static data carry-over is not tested gameplay.", PLAY_REASON]
        if self._last_error:
            lines += ["Operation error:", self._last_error]
        if not isinstance(report, dict):
            return lines
        if report.get("status") not in (UNSUPPORTED, REQUIRES_PORTING) or report.get("playable_verified") or report.get("play_enabled"):
            lines.append("insufficient_evidence: No successful compatibility/playability claim can be established by this UI.")
        analysis = report.get("analysis") or {}
        if not isinstance(analysis, dict):
            analysis = {}
        mod_evidence = [mod for mod in analysis.get("mods", []) if isinstance(mod, dict)]
        for source in (report, analysis, *mod_evidence):
            for diagnostic in source.get("diagnostics", []):
                if isinstance(diagnostic, dict):
                    lines.append(f"{diagnostic.get('code', 'Unknown')}: {diagnostic.get('message', '')}")
        for mod in mod_evidence:
            check = mod.get("raw_evidence", {}).get("check", {})
            if isinstance(check, dict) and check:
                lines.append(f"{mod.get('id', 'Unknown')}: original backend verdict {check.get('verdict', 'Missing')} "
                             "(static evidence only; not a compatibility/test result)")
        if errors_only:
            for row in report.get("rows", []):
                lines += ["", f"Mod: {row.get('name') or row.get('id', 'Unknown')}",
                          "Reason: " + str(row.get("reason", "insufficient_evidence: no reason recorded")),
                          "Missing dependencies: " + ", ".join(map(str, row.get("missing_dependencies", [])))]
        if not errors_only:
            index = self.coverage_table.currentRow()
            rows = report.get("rows", [])
            if 0 <= index < len(rows):
                row = rows[index]
                lines += ["", f"Mod: {row.get('name') or row.get('id', 'Unknown')}",
                          "Reason: " + str(row.get("reason", "Missing evidence")),
                          "Missing dependencies: " + ", ".join(map(str, row.get("missing_dependencies", []))),
                          "Original per-mod evidence:", _short(json.dumps(row.get("raw_evidence", {}), indent=2, ensure_ascii=False))]
        for command in analysis.get("commands", []):
            lines += ["", "Command: " + _short(json.dumps(command.get("argv", []), ensure_ascii=False)),
                      f"Exit code: {command.get('exit_code')} · timed out: {command.get('timed_out', False)}",
                      "stdout:\n" + _short(command.get("stdout", "")), "stderr:\n" + _short(command.get("stderr", ""))]
        return lines

    def show_coverage_details(self):
        self.details.setPlainText(_short("\n".join(self._report_details()), 100000))

    def view_errors(self):
        self.window.require_idle()
        self.details.setPlainText(_short("\n".join(self._report_details(errors_only=True)), 100000))

    def export_report(self, format):
        entry = self._require_selected()
        if not entry.report_file:
            raise ValueError("Analyze the selected pack before exporting a report")
        suffix = "json" if format == "json" else "txt"
        path, _ = QFileDialog.getSaveFileName(self, "Export full pack compatibility evidence", f"modpack-report.{suffix}",
                                            f"{'JSON' if format == 'json' else 'Text'} reports (*.{suffix})")
        if path:
            library = self.library
            self._run("Revalidating and exporting pack evidence…",
                      lambda progress: library.export_report(entry.token, Path(path), format),
                      lambda output: self.status.setText(f"Report exported: {output}. Compatibility remains subject to its recorded limitations."))
