import sys
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
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


class BrandMark(QWidget):
    """A small, scalable vector logo drawn directly with Qt."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(58, 58)
        self.setToolTip("BugFinder")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        tile = QLinearGradient(3, 3, 55, 55)
        tile.setColorAt(0.0, QColor("#123c59"))
        tile.setColorAt(1.0, QColor("#102235"))
        painter.setPen(QPen(QColor("#287da5"), 1.4))
        painter.setBrush(tile)
        painter.drawRoundedRect(2, 2, 54, 54, 16, 16)

        shield = QPainterPath()
        shield.moveTo(29, 11)
        shield.cubicTo(35, 15, 40, 15, 44, 16)
        shield.lineTo(43, 31)
        shield.cubicTo(42, 39, 35, 45, 29, 48)
        shield.cubicTo(22, 45, 16, 39, 15, 31)
        shield.lineTo(14, 16)
        shield.cubicTo(20, 15, 24, 14, 29, 11)
        painter.setPen(QPen(QColor("#72dcff"), 2.1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(shield)

        painter.setPen(QPen(QColor("#d7f6ff"), 2.8))
        painter.drawEllipse(22, 22, 13, 13)
        painter.drawLine(33, 33, 39, 39)
        painter.setPen(QPen(QColor("#4dd7e9"), 2.2))
        painter.drawLine(26, 28, 29, 31)
        painter.drawLine(29, 31, 34, 25)
        painter.end()


class StatCard(QFrame):
    def __init__(self, caption, accent, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(5)

        self.caption = QLabel(caption.upper())
        self.caption.setObjectName("statCaption")
        self.value = QLabel("—")
        self.value.setObjectName("statValue")
        self.detail = QLabel("")
        self.detail.setObjectName("statDetail")
        self.detail.setStyleSheet(f"color: {accent};")

        layout.addWidget(self.caption)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = "de"
        self.project = None
        self.findings = []
        self.worker = None
        self.db = Database()

        self.setWindowTitle("BugFinder")
        self.setMinimumSize(1120, 760)
        self.resize(1440, 900)
        self.setStyleSheet(self.stylesheet())

        central = QWidget()
        central.setObjectName("appRoot")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        # Header / brand
        header = QHBoxLayout()
        header.setSpacing(15)
        self.logo = BrandMark()
        header.addWidget(self.logo)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        self.title_label = QLabel("BugFinder")
        self.title_label.setObjectName("brandTitle")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("brandSubtitle")
        brand_text.addWidget(self.title_label)
        brand_text.addWidget(self.subtitle)
        header.addLayout(brand_text)
        header.addStretch()

        self.header_status = QLabel()
        self.header_status.setObjectName("statusPill")
        header.addWidget(self.header_status)

        self.lang_box = QComboBox()
        self.lang_box.setObjectName("languageBox")
        self.lang_box.addItem("Deutsch", "de")
        self.lang_box.addItem("English", "en")
        self.lang_box.currentIndexChanged.connect(self.change_lang)
        self.lang_box.setMinimumWidth(132)
        header.addWidget(self.lang_box)
        root.addLayout(header)

        # Welcome / action panel
        self.hero = QFrame()
        self.hero.setObjectName("heroPanel")
        hero_layout = QHBoxLayout(self.hero)
        hero_layout.setContentsMargins(23, 20, 23, 20)
        hero_layout.setSpacing(18)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(5)
        self.hero_title = QLabel()
        self.hero_title.setObjectName("heroTitle")
        self.hero_description = QLabel()
        self.hero_description.setObjectName("heroDescription")
        self.hero_description.setWordWrap(True)
        hero_text.addWidget(self.hero_title)
        hero_text.addWidget(self.hero_description)
        hero_layout.addLayout(hero_text, 1)

        self.choose_btn = QPushButton()
        self.choose_btn.setObjectName("secondaryButton")
        self.scan_btn = QPushButton()
        self.scan_btn.setObjectName("primaryButton")
        self.export_btn = QPushButton()
        self.export_btn.setObjectName("secondaryButton")
        self.choose_btn.clicked.connect(self.choose_folder)
        self.scan_btn.clicked.connect(self.start_scan)
        self.export_btn.clicked.connect(self.export)

        actions = QVBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.choose_btn)
        actions.addWidget(self.scan_btn)
        actions.addWidget(self.export_btn)
        hero_layout.addLayout(actions)
        root.addWidget(self.hero)

        # Selected project strip
        project_strip = QFrame()
        project_strip.setObjectName("projectStrip")
        strip_layout = QHBoxLayout(project_strip)
        strip_layout.setContentsMargins(16, 11, 16, 11)
        strip_layout.setSpacing(10)
        self.project_icon = QLabel("◈")
        self.project_icon.setObjectName("projectIcon")
        strip_layout.addWidget(self.project_icon)
        self.path_label = QLabel()
        self.path_label.setObjectName("projectPath")
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        strip_layout.addWidget(self.path_label, 1)
        self.scan_state = QLabel()
        self.scan_state.setObjectName("scanState")
        strip_layout.addWidget(self.scan_state)
        self.history_btn = QPushButton("Verlauf" if self.lang == "de" else "History")
        self.history_btn.setObjectName("secondaryButton")
        self.history_btn.clicked.connect(self.show_history)
        strip_layout.addWidget(self.history_btn)
        root.addWidget(project_strip)

        # Overview cards
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(13)
        self.total_card = StatCard("", "#78d8ff")
        self.critical_card = StatCard("", "#ff7587")
        self.warning_card = StatCard("", "#ffc36e")
        self.project_card = StatCard("", "#7ee0c0")
        self.stats_grid.addWidget(self.total_card, 0, 0)
        self.stats_grid.addWidget(self.critical_card, 0, 1)
        self.stats_grid.addWidget(self.warning_card, 0, 2)
        self.stats_grid.addWidget(self.project_card, 0, 3)
        root.addLayout(self.stats_grid)

        # Results section
        results_header = QHBoxLayout()
        results_header.setSpacing(10)
        self.results_title = QLabel()
        self.results_title.setObjectName("sectionTitle")
        results_header.addWidget(self.results_title)
        results_header.addStretch()
        self.results_hint = QLabel()
        self.results_hint.setObjectName("mutedText")
        results_header.addWidget(self.results_hint)
        root.addLayout(results_header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setPlaceholderText("Ergebnisse durchsuchen …")
        self.search_box.textChanged.connect(self.apply_filters)
        filter_row.addWidget(self.search_box, 1)
        self.severity_filter = QComboBox()
        self.severity_filter.setObjectName("languageBox")
        self.severity_filter.addItem("Alle Schweregrade", "all")
        self.severity_filter.addItem("Kritisch", "critical")
        self.severity_filter.addItem("Hoch", "high")
        self.severity_filter.addItem("Mittel", "medium")
        self.severity_filter.addItem("Niedrig", "low")
        self.severity_filter.addItem("Info", "info")
        self.severity_filter.currentIndexChanged.connect(self.apply_filters)
        filter_row.addWidget(self.severity_filter)
        root.addLayout(filter_row)

        self.results_panel = QFrame()
        self.results_panel.setObjectName("resultsPanel")
        panel_layout = QVBoxLayout(self.results_panel)
        panel_layout.setContentsMargins(1, 1, 1, 1)
        panel_layout.setSpacing(0)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("findingsTable")
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 112)
        self.table.setColumnWidth(1, 115)
        self.table.setColumnWidth(2, 190)
        self.table.setColumnWidth(3, 72)
        self.table.setColumnWidth(4, 105)
        self.table.setColumnWidth(5, 260)
        panel_layout.addWidget(self.table)
        root.addWidget(self.results_panel, 1)

        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("detailPanel")
        detail_layout = QVBoxLayout(self.detail_panel)
        detail_layout.setContentsMargins(16, 12, 16, 12)
        detail_layout.setSpacing(7)
        self.detail_title = QLabel("Fundstelle auswählen" if self.lang == "de" else "Select a finding")
        self.detail_title.setObjectName("sectionTitle")
        self.detail_text = QPlainTextEdit()
        self.detail_text.setObjectName("detailText")
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(105)
        self.detail_text.setPlainText(
            "Wähle einen Eintrag aus der Tabelle, um Erklärung und Lösungsvorschlag zu sehen."
            if self.lang == "de" else
            "Select a row to view its explanation and recommendation."
        )
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_text)
        root.addWidget(self.detail_panel)
        self.table.itemSelectionChanged.connect(self.show_finding_details)

        # Footer / progress
        footer = QHBoxLayout()
        footer.setSpacing(12)
        self.status = QLabel()
        self.status.setObjectName("footerStatus")
        footer.addWidget(self.status)
        footer.addStretch()
        self.progress_text = QLabel("0%")
        self.progress_text.setObjectName("mutedText")
        footer.addWidget(self.progress_text)
        root.addLayout(footer)

        self.progress = QProgressBar()
        self.progress.setObjectName("scanProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(7)
        root.addWidget(self.progress)

        self.add_shadow(self.hero, blur=32, y=8, alpha=38)
        self.add_shadow(self.results_panel, blur=24, y=5, alpha=25)
        self.apply_lang()
        self.update_stats()
        self.animate_intro()

    @staticmethod
    def add_shadow(widget, blur=24, y=5, alpha=30):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y)
        shadow.setColor(QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(shadow)

    @staticmethod
    def stylesheet():
        return """
            * { font-family: "Segoe UI", "Inter", sans-serif; }
            QMainWindow, QWidget#appRoot {
                background: #0a1019;
                color: #e8f1fb;
                font-size: 13px;
            }
            QLabel { background: transparent; }
            QLabel#brandTitle {
                color: #eaf8ff; font-size: 29px; font-weight: 800;
                letter-spacing: 0.4px;
            }
            QLabel#brandSubtitle { color: #83a7c1; font-size: 12px; }
            QLabel#statusPill {
                color: #8ce8c8; background: #102b2b;
                border: 1px solid #20534c; border-radius: 12px;
                padding: 7px 12px; font-size: 11px; font-weight: 700;
            }
            QComboBox {
                color: #dceaf7; background: #172435;
                border: 1px solid #2a4057; border-radius: 9px;
                padding: 9px 12px; min-height: 20px;
            }
            QComboBox:hover { border-color: #39bde7; }
            QLineEdit#searchBox, QPlainTextEdit#detailText {
                color: #e4f1fb; background: #111e2c;
                border: 1px solid #2a4057; border-radius: 9px;
                padding: 9px 11px; selection-background-color: #17658a;
            }
            QLineEdit#searchBox:focus { border-color: #36b9df; }
            QFrame#detailPanel {
                background: #101c2a; border: 1px solid #263c52; border-radius: 12px;
            }
            QPlainTextEdit#detailText { border: 0; padding: 2px; }
            QComboBox QAbstractItemView {
                color: #eaf4ff; background: #172435;
                selection-background-color: #174c69;
                border: 1px solid #2a4057;
            }
            QFrame#heroPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #13283a, stop:0.55 #122235, stop:1 #17253a);
                border: 1px solid #25445d; border-radius: 17px;
            }
            QLabel#heroTitle { color: #f0f9ff; font-size: 20px; font-weight: 750; }
            QLabel#heroDescription { color: #9db9ce; font-size: 12px; }
            QPushButton {
                color: #e8f5ff; border-radius: 9px; padding: 10px 15px;
                font-size: 12px; font-weight: 650; min-height: 20px;
            }
            QPushButton#primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #087da5, stop:1 #1762a0);
                border: 1px solid #269bc2;
            }
            QPushButton#primaryButton:hover {
                background: #1596bd; border-color: #72e2ff;
            }
            QPushButton#primaryButton:pressed { background: #075d80; }
            QPushButton#secondaryButton {
                background: #1b2b3d; border: 1px solid #344e67;
            }
            QPushButton#secondaryButton:hover {
                background: #243d53; border-color: #45b9df;
            }
            QPushButton:disabled {
                color: #718397; background: #182331; border-color: #273748;
            }
            QFrame#projectStrip {
                background: #101c2a; border: 1px solid #22364b; border-radius: 11px;
            }
            QLabel#projectIcon { color: #5bd7ed; font-size: 19px; font-weight: 800; }
            QLabel#projectPath { color: #c4d8e8; font-size: 12px; }
            QLabel#scanState { color: #82d8c0; font-size: 11px; font-weight: 700; }
            QFrame#statCard {
                background: #111d2b; border: 1px solid #263a50; border-radius: 13px;
            }
            QFrame#statCard:hover { border-color: #327b9c; }
            QLabel#statCaption {
                color: #7894ad; font-size: 10px; font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#statValue { color: #edf8ff; font-size: 27px; font-weight: 800; }
            QLabel#statDetail { font-size: 10px; font-weight: 650; }
            QLabel#sectionTitle { color: #e8f4ff; font-size: 16px; font-weight: 750; }
            QLabel#mutedText { color: #718ba2; font-size: 11px; }
            QFrame#resultsPanel {
                background: #101a27; border: 1px solid #26394d; border-radius: 13px;
            }
            QTableWidget#findingsTable {
                background: #101a27; alternate-background-color: #132131;
                color: #dce9f5; border: 0; border-radius: 12px;
                selection-background-color: #174c68; selection-color: #ffffff;
                outline: 0;
            }
            QTableWidget#findingsTable::item { padding: 8px; border: 0; }
            QHeaderView::section {
                color: #9fc1d9; background: #18283a;
                border: 0; border-bottom: 1px solid #2a4056;
                padding: 13px 9px; font-size: 10px; font-weight: 800;
            }
            QProgressBar#scanProgress {
                background: #172638; border: 0; border-radius: 3px;
            }
            QProgressBar#scanProgress::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #17a6cf, stop:1 #65e0d0);
            }
            QLabel#footerStatus { color: #a9c3d7; font-size: 11px; }
            QToolTip {
                color: #eaf7ff; background: #172638;
                border: 1px solid #3b627c; padding: 5px;
            }
        """

    def animate_intro(self):
        effect = QGraphicsDropShadowEffect(self.logo)
        effect.setBlurRadius(25)
        effect.setOffset(0, 0)
        effect.setColor(QColor(30, 177, 224, 75))
        self.logo.setGraphicsEffect(effect)
        self._logo_glow = effect

        opacity = self.centralWidget().graphicsEffect()
        if opacity is None:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            opacity = QGraphicsOpacityEffect(self.centralWidget())
            self.centralWidget().setGraphicsEffect(opacity)
        opacity.setOpacity(0.0)
        self._intro_animation = QPropertyAnimation(opacity, b"opacity", self)
        self._intro_animation.setDuration(420)
        self._intro_animation.setStartValue(0.0)
        self._intro_animation.setEndValue(1.0)
        self._intro_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._intro_animation.start()

    def change_lang(self):
        selected = self.lang_box.currentData()
        if selected:
            self.lang = selected
            self.apply_lang()

    def apply_lang(self):
        t = TEXT[self.lang]
        self.setWindowTitle("BugFinder")
        self.subtitle.setText(
            "Lokale Codeanalyse · Sicheres Read-only-Scanning"
            if self.lang == "de"
            else "Local code analysis · Safe read-only scanning"
        )
        self.header_status.setText("● SYSTEM BEREIT" if self.lang == "de" else "● SYSTEM READY")
        self.hero_title.setText(
            "Dein Code. Klarer Überblick."
            if self.lang == "de"
            else "Your code. Clear visibility."
        )
        self.hero_description.setText(
            "Analysiere lokale Projekte, entdecke problematische Muster und behalte deine Ergebnisse im Blick."
            if self.lang == "de"
            else "Analyze local projects, discover problematic patterns and keep every finding in view."
        )
        self.choose_btn.setText("＋  " + t["folder"])
        self.scan_btn.setText("⌕  " + t["scan"])
        self.export_btn.setText("↧  " + t["export"])
        self.results_title.setText("Analyse-Ergebnisse" if self.lang == "de" else "Analysis results")
        self.results_hint.setText(
            "Einträge werden lokal angezeigt" if self.lang == "de" else "Findings stay on this device"
        )
        self.history_btn.setText("Verlauf" if self.lang == "de" else "History")
        self.search_box.setPlaceholderText(
            "Ergebnisse durchsuchen …" if self.lang == "de" else "Search findings …"
        )
        filter_labels = [
            ("Alle Schweregrade", "All severities", "all"),
            ("Kritisch", "Critical", "critical"),
            ("Hoch", "High", "high"),
            ("Mittel", "Medium", "medium"),
            ("Niedrig", "Low", "low"),
            ("Info", "Info", "info"),
        ]
        selected_filter = self.severity_filter.currentData()
        self.severity_filter.blockSignals(True)
        self.severity_filter.clear()
        for de_label, en_label, severity_key in filter_labels:
            self.severity_filter.addItem(
                de_label if self.lang == "de" else en_label, severity_key
            )
        index = self.severity_filter.findData(selected_filter)
        self.severity_filter.setCurrentIndex(max(0, index))
        self.severity_filter.blockSignals(False)
        self.detail_title.setText("Fundstelle auswählen" if self.lang == "de" else "Select a finding")
        if not self.table.selectedItems():
            self.detail_text.setPlainText(
                "Wähle einen Eintrag aus der Tabelle, um Erklärung und Lösungsvorschlag zu sehen."
                if self.lang == "de" else
                "Select a row to view its explanation and recommendation."
            )
        self.table.setHorizontalHeaderLabels([
            t["severity"], t["rule"], t["file"], t["line"],
            t["confidence"], t["message"], t["fix"]
        ])
        self.total_card.caption.setText("GEFUNDENE HINWEISE" if self.lang == "de" else "TOTAL FINDINGS")
        self.critical_card.caption.setText("KRITISCH" if self.lang == "de" else "CRITICAL")
        self.warning_card.caption.setText("WARNUNGEN" if self.lang == "de" else "WARNINGS")
        self.project_card.caption.setText("PROJEKTSTATUS" if self.lang == "de" else "PROJECT STATUS")
        self.total_card.detail.setText("Alle Schweregrade" if self.lang == "de" else "All severities")
        self.critical_card.detail.setText("Sofort prüfen" if self.lang == "de" else "Review first")
        self.warning_card.detail.setText("Manuell prüfen" if self.lang == "de" else "Review manually")
        self.project_card.detail.setText("Lokal & read-only" if self.lang == "de" else "Local & read-only")
        self.path_label.setText(
            str(self.project) if self.project else (
                "Kein Projekt ausgewählt" if self.lang == "de" else "No project selected"
            )
        )
        self.scan_state.setText("BEREIT" if self.lang == "de" else "READY")
        self.status.setText(t["ready"])
        self.update_stats()

    def update_stats(self):
        total = len(self.findings)
        critical = sum(1 for item in self.findings if str(item.severity).lower() == "critical")
        warnings = sum(1 for item in self.findings if str(item.severity).lower() in {"high", "medium", "warning"})
        self.total_card.value.setText(str(total))
        self.critical_card.value.setText(str(critical))
        self.warning_card.value.setText(str(warnings))
        self.project_card.value.setText(
            "AKTIV" if self.project and self.lang == "de" else
            "ACTIVE" if self.project else
            "—"
        )

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, TEXT[self.lang]["folder"], str(self.project) if self.project else ""
        )
        if folder:
            self.project = Path(folder)
            self.path_label.setText(str(self.project))
            self.scan_state.setText("AUSGEWÄHLT" if self.lang == "de" else "SELECTED")
            self.update_stats()

    def start_scan(self):
        if not self.project:
            QMessageBox.information(self, "BugFinder", TEXT[self.lang]["no_project"])
            return
        self.scan_btn.setEnabled(False)
        self.choose_btn.setEnabled(False)
        self.progress.setRange(0, 0)
        self.progress_text.setText("…" )
        self.status.setText(TEXT[self.lang]["scanning"])
        self.scan_state.setText("ANALYSE LÄUFT" if self.lang == "de" else "SCANNING")
        self.worker = Worker(self.project)
        self.worker.done.connect(self.show_results)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.scan_finished)
        self.worker.start()

    def scan_finished(self):
        self.scan_btn.setEnabled(True)
        self.choose_btn.setEnabled(True)

    def show_results(self, findings):
        self.findings = findings
        self.db.save_scan(str(self.project), [finding.to_dict() for finding in findings])
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(findings))

        for row, finding in enumerate(findings):
            values = [
                finding.severity.upper(), finding.rule_id, finding.file_path,
                str(finding.line), finding.confidence, finding.message,
                finding.recommendation,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    severity = str(finding.severity).lower()
                    color = {
                        "critical": "#ff7188",
                        "high": "#ff9a76",
                        "medium": "#ffc36e",
                        "low": "#79c9f2",
                        "info": "#8bcdbb",
                    }.get(severity, "#c5d7e8")
                    item.setForeground(QColor(color))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(row, col, item)

        self.table.resizeRowsToContents()
        self.table.setSortingEnabled(True)
        self.apply_filters()
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.progress_text.setText("100%")
        self.status.setText(f"{TEXT[self.lang]['done']}: {len(findings)}")
        self.scan_state.setText("ABGESCHLOSSEN" if self.lang == "de" else "COMPLETED")
        self.update_stats()

    def show_error(self, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress_text.setText("0%")
        self.status.setText("Analyse fehlgeschlagen" if self.lang == "de" else "Scan failed")
        self.scan_state.setText("FEHLER" if self.lang == "de" else "ERROR")
        QMessageBox.critical(self, "BugFinder", message)

    def export(self):
        if not self.findings:
            QMessageBox.information(
                self, "BugFinder",
                "Keine Ergebnisse zum Exportieren." if self.lang == "de" else "No findings to export."
            )
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            TEXT[self.lang]["export"],
            "bugfinder-report.json",
            "JSON (*.json);;HTML (*.html);;SARIF (*.sarif);;Text (*.txt);;CSV (*.csv)",
        )
        if not filename:
            return
        extension = Path(filename).suffix.lower().lstrip(".")
        report_format = "sarif" if extension == "sarif" else extension
        try:
            export_report(self.findings, Path(filename), report_format)
            QMessageBox.information(
                self, "BugFinder",
                f"Bericht gespeichert: {filename}" if self.lang == "de"
                else f"Report saved: {filename}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "BugFinder", str(exc))


def launch():
    app = QApplication(sys.argv)
    app.setApplicationName("BugFinder")
    app.setOrganizationName("SPX8k")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()
