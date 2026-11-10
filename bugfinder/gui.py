import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QProgressBar, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from bugfinder.database import Database
from bugfinder.i18n import TEXT
from bugfinder.reporting import export_report
from bugfinder.rules import scan_project

class Worker(QThread):
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            self.done.emit(scan_project(self.path))
        except Exception as exc:
            self.failed.emit(str(exc))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang, self.project, self.findings = "de", None, []
        self.db = Database()
        self.setMinimumSize(1050, 680)
        self.setStyleSheet("""
            QMainWindow,QWidget{background:#10151d;color:#e8edf5;font-size:13px}
            QPushButton,QComboBox{background:#202c3a;border:1px solid #334155;
                border-radius:8px;padding:9px 13px}
            QPushButton:hover{background:#29394c;border-color:#38bdf8}
            QTableWidget{background:#151e29;alternate-background-color:#192432;
                gridline-color:#2b3949;border:1px solid #2b3949}
            QHeaderView::section{background:#202c3a;padding:8px;border:0}
        """)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        top = QHBoxLayout()
        title = QLabel("BugFinder")
        title.setStyleSheet("font-size:27px;font-weight:700;color:#7dd3fc")
        top.addWidget(title)
        top.addStretch()
        self.lang_box = QComboBox()
        self.lang_box.addItem("Deutsch", "de")
        self.lang_box.addItem("English", "en")
        self.lang_box.currentIndexChanged.connect(self.change_lang)
        top.addWidget(self.lang_box)
        layout.addLayout(top)
        subtitle = QLabel("Local-first code analysis · Read-only scanning")
        subtitle.setStyleSheet("color:#9aa9bb")
        layout.addWidget(subtitle)
        actions = QHBoxLayout()
        self.choose_btn, self.scan_btn, self.export_btn = QPushButton(), QPushButton(), QPushButton()
        self.choose_btn.clicked.connect(self.choose_folder)
        self.scan_btn.clicked.connect(self.start_scan)
        self.export_btn.clicked.connect(self.export)
        for button in (self.choose_btn, self.scan_btn, self.export_btn):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.path_label = QLabel("No project selected")
        layout.addWidget(self.path_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status = QLabel()
        layout.addWidget(self.status)
        self.table = QTableWidget(0, 7)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.apply_lang()

    def change_lang(self):
        self.lang = self.lang_box.currentData()
        self.apply_lang()

    def apply_lang(self):
        t = TEXT[self.lang]
        self.setWindowTitle("BugFinder")
        self.choose_btn.setText(t["folder"])
        self.scan_btn.setText(t["scan"])
        self.export_btn.setText(t["export"])
        self.status.setText(t["ready"])
        self.table.setHorizontalHeaderLabels([
            t["severity"], t["rule"], t["file"], t["line"],
            t["confidence"], t["message"], t["fix"]
        ])

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, TEXT[self.lang]["folder"])
        if folder:
            self.project = Path(folder)
            self.path_label.setText(str(self.project))

    def start_scan(self):
        if not self.project:
            QMessageBox.information(self, "BugFinder", TEXT[self.lang]["no_project"])
            return
        self.scan_btn.setEnabled(False)
        self.progress.setRange(0, 0)
        self.status.setText(TEXT[self.lang]["scanning"])
        self.worker = Worker(self.project)
        self.worker.done.connect(self.show_results)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(lambda: self.scan_btn.setEnabled(True))
        self.worker.start()

    def show_results(self, findings):
        self.findings = findings
        self.db.save_scan(str(self.project), [f.to_dict() for f in findings])
        self.table.setRowCount(len(findings))
        for row, finding in enumerate(findings):
            values = [
                finding.severity.upper(), finding.rule_id, finding.file_path,
                str(finding.line), finding.confidence, finding.message,
                finding.recommendation,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.status.setText(f"{TEXT[self.lang]['done']}: {len(findings)}")

    def show_error(self, message):
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        QMessageBox.critical(self, "BugFinder", message)

    def export(self):
        if not self.findings:
            QMessageBox.information(self, "BugFinder", "No findings to export.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, TEXT[self.lang]["export"], "bugfinder-report.json",
            "JSON (*.json);;HTML (*.html);;SARIF (*.sarif);;Text (*.txt);;CSV (*.csv)"
        )
        if not filename:
            return
        ext = Path(filename).suffix.lower().lstrip(".")
        fmt = "sarif" if ext == "sarif" else ext
        try:
            export_report(self.findings, Path(filename), fmt)
            QMessageBox.information(self, "BugFinder", f"Report saved: {filename}")
        except Exception as exc:
            QMessageBox.critical(self, "BugFinder", str(exc))

def launch():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
