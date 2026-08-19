"""
Do Muse — Main window module
Defines the main window layout, menu bar, and interaction logic.
Supports JSON editing, validation, multi-format import/export, templates,
recent files, score preview, and i18n (zh/en).
"""

import json
import logging
import os
import platform
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QPushButton, QSplitter,
    QMenuBar, QMessageBox, QFileDialog,
    QStatusBar, QProgressBar, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from core import json_validator
from core.i18n import LanguageManager
from core.config_manager import ConfigManager
from gui.log_handler import LogHandler
from gui.json_highlighter import JsonHighlighter
from gui.workers import ExportWorker, PreviewWorker
from gui.templates import TEMPLATES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """
    Do Muse main window, extends QMainWindow.

    Builds the full GUI layout and interaction, including:
      - JSON editor with syntax highlighting and log console
      - File menu (load/save JSON, import, export, templates, recent files)
      - Edit menu (undo/redo)
      - View menu (score preview)
      - Language menu (Chinese/English)
      - Validation and export actions with progress indication
      - Status bar (language, file name, validation status)
      - Drag & drop file support
      - Keyboard shortcuts

    :param parent: Parent widget, defaults to None.
    """

    def __init__(self, parent=None):
        """
        Initialize the main window: set up menus, layout, logging, and state.

        Args:
            parent: Parent widget, defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle(LanguageManager.tr("window_title"))
        self.resize(1000, 700)

        self.config_manager = ConfigManager()
        self._current_file_path: str = ""
        self._validation_status: str = "none"
        self._export_worker: ExportWorker = None
        self._preview_worker: PreviewWorker = None
        self._current_theme: str = "light"

        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_logging()
        self._connect_signals()
        self._setup_shortcuts()
        self._enable_drag_drop()
        self._update_status_bar()

        # Apply saved theme
        config = self.config_manager.load_config()
        self._current_theme = config.get("theme", "light")
        self._apply_theme(self._current_theme)

        logger.info("Main window initialized")

    # ── Menu bar ──────────────────────────────────────────────────────────

    def _setup_menu_bar(self):
        """Build the menu bar: File, Edit, View, Language menus and their items."""
        menu_bar = self.menuBar()

        # ── File menu ──
        self._file_menu = menu_bar.addMenu(LanguageManager.tr("menu_file"))

        # Import submenu
        self._import_menu = self._file_menu.addMenu(LanguageManager.tr("menu_import"))

        self.action_import_musicxml = QAction(LanguageManager.tr("menu_import_musicxml"), self)
        self.action_import_musicxml.triggered.connect(lambda: self.on_import_file("musicxml"))
        self._import_menu.addAction(self.action_import_musicxml)

        self.action_import_midi = QAction(LanguageManager.tr("menu_import_midi"), self)
        self.action_import_midi.triggered.connect(lambda: self.on_import_file("midi"))
        self._import_menu.addAction(self.action_import_midi)

        self._import_menu.addSeparator()

        self.action_load_json = QAction(LanguageManager.tr("menu_load_json"), self)
        self.action_load_json.triggered.connect(self.on_load_json)
        self._import_menu.addAction(self.action_load_json)

        # Save JSON
        self.action_save_json = QAction(LanguageManager.tr("menu_save_json"), self)
        self.action_save_json.triggered.connect(self.on_save_json)
        self._file_menu.addAction(self.action_save_json)

        self._file_menu.addSeparator()

        # Templates submenu
        self._templates_menu = self._file_menu.addMenu(LanguageManager.tr("menu_templates"))

        self.action_template_blank = QAction(LanguageManager.tr("menu_templates_blank"), self)
        self.action_template_blank.triggered.connect(lambda: self.on_load_template("blank"))
        self._templates_menu.addAction(self.action_template_blank)

        self.action_template_piano = QAction(LanguageManager.tr("menu_templates_piano"), self)
        self.action_template_piano.triggered.connect(lambda: self.on_load_template("piano"))
        self._templates_menu.addAction(self.action_template_piano)

        self.action_template_duo = QAction(LanguageManager.tr("menu_templates_duo"), self)
        self.action_template_duo.triggered.connect(lambda: self.on_load_template("duo"))
        self._templates_menu.addAction(self.action_template_duo)

        self.action_template_scale = QAction(LanguageManager.tr("menu_templates_scale"), self)
        self.action_template_scale.triggered.connect(lambda: self.on_load_template("scale"))
        self._templates_menu.addAction(self.action_template_scale)

        # Recent files submenu
        self._recent_menu = self._file_menu.addMenu(LanguageManager.tr("menu_recent"))
        self._refresh_recent_files_menu()

        self._file_menu.addSeparator()

        # Export submenu
        self._export_menu = self._file_menu.addMenu(LanguageManager.tr("menu_export"))

        self.action_export_mxl = QAction(LanguageManager.tr("menu_export_mxl"), self)
        self.action_export_mxl.triggered.connect(lambda: self.on_export_format("mxl"))
        self._export_menu.addAction(self.action_export_mxl)

        self.action_export_midi = QAction(LanguageManager.tr("menu_export_midi"), self)
        self.action_export_midi.triggered.connect(lambda: self.on_export_format("midi"))
        self._export_menu.addAction(self.action_export_midi)

        self.action_export_xml = QAction(LanguageManager.tr("menu_export_xml"), self)
        self.action_export_xml.triggered.connect(lambda: self.on_export_format("xml"))
        self._export_menu.addAction(self.action_export_xml)

        self.action_export_ly = QAction(LanguageManager.tr("menu_export_ly"), self)
        self.action_export_ly.triggered.connect(lambda: self.on_export_format("ly"))
        self._export_menu.addAction(self.action_export_ly)

        self._file_menu.addSeparator()

        action_exit = QAction(LanguageManager.tr("menu_exit"), self)
        action_exit.triggered.connect(self.close)
        self._file_menu.addAction(action_exit)

        # ── Edit menu ──
        self._edit_menu = menu_bar.addMenu(LanguageManager.tr("menu_edit"))

        self.action_undo = QAction(LanguageManager.tr("menu_undo"), self)
        self.action_undo.triggered.connect(self._on_undo)
        self._edit_menu.addAction(self.action_undo)

        self.action_redo = QAction(LanguageManager.tr("menu_redo"), self)
        self.action_redo.triggered.connect(self._on_redo)
        self._edit_menu.addAction(self.action_redo)

        # ── View menu ──
        self._view_menu = menu_bar.addMenu(LanguageManager.tr("menu_view"))

        self.action_preview = QAction(LanguageManager.tr("menu_preview"), self)
        self.action_preview.triggered.connect(self.on_preview_score)
        self._view_menu.addAction(self.action_preview)

        self._view_menu.addSeparator()

        self._theme_menu = self._view_menu.addMenu(LanguageManager.tr("menu_theme"))
        self.action_theme_light = QAction(LanguageManager.tr("menu_theme_light"), self)
        self.action_theme_light.triggered.connect(lambda: self._switch_theme("light"))
        self._theme_menu.addAction(self.action_theme_light)

        self.action_theme_dark = QAction(LanguageManager.tr("menu_theme_dark"), self)
        self.action_theme_dark.triggered.connect(lambda: self._switch_theme("dark"))
        self._theme_menu.addAction(self.action_theme_dark)

        # ── Language menu ──
        self._lang_menu = menu_bar.addMenu(LanguageManager.tr("menu_language"))

        self.action_lang_zh = QAction(LanguageManager.tr("menu_lang_zh"), self)
        self.action_lang_zh.triggered.connect(lambda: self._switch_language("zh"))
        self._lang_menu.addAction(self.action_lang_zh)

        self.action_lang_en = QAction(LanguageManager.tr("menu_lang_en"), self)
        self.action_lang_en.triggered.connect(lambda: self._switch_language("en"))
        self._lang_menu.addAction(self.action_lang_en)

    # ── Central widget ────────────────────────────────────────────────────

    def _setup_central_widget(self):
        """Build the central layout: JSON editor + log console (splitter), bottom toolbar."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── Splitter: JSON editor | Log console ──
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left: JSON editor
        self.json_text_edit = QPlainTextEdit(self)
        self.json_text_edit.setPlaceholderText(LanguageManager.tr("json_placeholder"))
        # Apply JSON syntax highlighting
        self._json_highlighter = JsonHighlighter(self.json_text_edit.document())
        splitter.addWidget(self.json_text_edit)

        # Right: log console
        self.log_console = QPlainTextEdit(self)
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText(LanguageManager.tr("log_placeholder"))
        splitter.addWidget(self.log_console)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

        # ── Bottom toolbar ──
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        self.btn_load_json = QPushButton(LanguageManager.tr("btn_load_json"), self)
        bottom_layout.addWidget(self.btn_load_json)

        self.btn_save_json = QPushButton(LanguageManager.tr("btn_save_json"), self)
        bottom_layout.addWidget(self.btn_save_json)

        self.btn_validate = QPushButton(LanguageManager.tr("btn_validate"), self)
        bottom_layout.addWidget(self.btn_validate)

        bottom_layout.addStretch()

        self.btn_import = QPushButton(LanguageManager.tr("btn_import"), self)
        bottom_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton(LanguageManager.tr("btn_export"), self)
        bottom_layout.addWidget(self.btn_export)

        main_layout.addLayout(bottom_layout)

    # ── Status bar ────────────────────────────────────────────────────────

    def _setup_status_bar(self):
        """Set up the bottom status bar with language, file, and validation info."""
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

        self._status_label_lang = QLabel("")
        self._status_label_file = QLabel("")
        self._status_label_validation = QLabel("")

        self._status_bar.addWidget(self._status_label_lang)
        self._status_bar.addWidget(self._status_label_file, 1)
        self._status_bar.addPermanentWidget(self._status_label_validation)

        # Progress bar (hidden by default)
        self._progress_bar = QProgressBar(self)
        self._progress_bar.setMaximumWidth(200)
        self._progress_bar.setVisible(False)
        self._status_bar.addPermanentWidget(self._progress_bar)

    def _update_status_bar(self):
        """Refresh the status bar labels."""
        lang_display = "中文" if LanguageManager.get_language() == "zh" else "English"
        self._status_label_lang.setText(
            LanguageManager.tr("status_language", lang_display)
        )

        file_display = self._current_file_path if self._current_file_path \
            else LanguageManager.tr("status_file_none")
        self._status_label_file.setText(
            LanguageManager.tr("status_file", os.path.basename(file_display) if self._current_file_path else file_display)
        )

        if self._validation_status == "ok":
            val_text = LanguageManager.tr("status_validation_ok")
        elif self._validation_status == "failed":
            val_text = LanguageManager.tr("status_validation_failed")
        else:
            val_text = LanguageManager.tr("status_validation_none")
        self._status_label_validation.setText(
            LanguageManager.tr("status_validation", val_text)
        )

    def _show_progress(self, message: str):
        """
        Show the progress bar with a message.

        Args:
            message: The progress message to display.
        """
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setVisible(True)
        self._status_bar.showMessage(message)

    def _hide_progress(self):
        """Hide the progress bar and clear the status message."""
        self._progress_bar.setVisible(False)
        self._status_bar.clearMessage()

    # ── Signal connections ────────────────────────────────────────────────

    def _connect_signals(self):
        """Connect all button signals to their slot methods."""
        self.btn_load_json.clicked.connect(self.on_load_json)
        self.btn_save_json.clicked.connect(self.on_save_json)
        self.btn_validate.clicked.connect(self.on_validate_json)
        self.btn_import.clicked.connect(self.on_import_dialog)
        self.btn_export.clicked.connect(self.on_export_dialog)

    # ── Keyboard shortcuts ────────────────────────────────────────────────

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts for common actions."""
        self.action_load_json.setShortcut(LanguageManager.tr("shortcut_load_json"))
        self.action_save_json.setShortcut(LanguageManager.tr("shortcut_save_json"))
        self.action_undo.setShortcut(LanguageManager.tr("shortcut_undo"))
        self.action_redo.setShortcut(LanguageManager.tr("shortcut_redo"))
        self.action_preview.setShortcut(LanguageManager.tr("shortcut_preview"))

        # F5 for validate
        self.btn_validate.setShortcut(LanguageManager.tr("shortcut_validate"))

        # Ctrl+E for export
        self.btn_export.setShortcut(LanguageManager.tr("shortcut_export"))

        # Ctrl+I for import
        self.btn_import.setShortcut(LanguageManager.tr("shortcut_import"))

    # ── Drag and drop ──────────────────────────────────────────────────────

    def _enable_drag_drop(self):
        """Enable drag and drop for files on the JSON editor."""
        self.json_text_edit.setAcceptDrops(True)
        self.json_text_edit.dragEnterEvent = self._drag_enter_event
        self.json_text_edit.dragMoveEvent = self._drag_move_event
        self.json_text_edit.dropEvent = self._drop_event

    def _drag_enter_event(self, event):
        """Handle drag enter event — accept if the dragged item is a file URL."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _drag_move_event(self, event):
        """Handle drag move event — accept file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _drop_event(self, event):
        """
        Handle drop event — load the dropped file.

        Supports .json files (direct load) and .xml/.mxl/.mid/.midi files (via importer).
        """
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = urls[0].toLocalFile()
        if not file_path or not os.path.exists(file_path):
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            self._load_json_file(file_path)
        elif ext in (".xml", ".mxl", ".mid", ".midi"):
            self._import_file(file_path)
        else:
            logger.warning(f"Unsupported file type dropped: {ext}")

    # ── Logging setup ─────────────────────────────────────────────────────

    def _setup_logging(self):
        """Initialize the logging system: attach LogHandler to root logger."""
        log_handler = LogHandler(self.log_console)
        log_handler.setLevel(logging.DEBUG)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(log_handler)
        logger.info("Logging system initialized")

    # ── Language switching ────────────────────────────────────────────────

    def _switch_language(self, lang: str):
        """
        Switch the UI language and update all visible text.

        Args:
            lang: Language code, "zh" or "en".
        """
        if lang == LanguageManager.get_language():
            return
        LanguageManager.set_language(lang)
        self._retranslate_ui()

        # Save language preference to config
        config = self.config_manager.load_config()
        config["language"] = lang
        self.config_manager.save_config(config)

        self._update_status_bar()
        logger.info(f"Language switched to {lang}")

    def _switch_theme(self, theme: str):
        """
        切换 UI 主题（浅色/暗色）。

        Args:
            theme: 主题名称，"light" 或 "dark"。
        """
        self._apply_theme(theme)

        # Save theme preference to config
        config = self.config_manager.load_config()
        config["theme"] = theme
        self.config_manager.save_config(config)
        logger.info(f"Theme switched to {theme}")

    def _apply_theme(self, theme: str):
        """
        应用指定的主题样式表。

        Args:
            theme: 主题名称，"light" 或 "dark"。
        """
        style_file = "style.qss" if theme == "light" else "style_dark.qss"
        style_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources",
            style_file,
        )
        app = QApplication.instance()
        if app and os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())

    def _retranslate_ui(self):
        """Update all UI text elements to match the current language."""
        self.setWindowTitle(LanguageManager.tr("window_title"))

        # Menu bar — File menu
        self._file_menu.setTitle(LanguageManager.tr("menu_file"))

        # Import submenu
        self._import_menu.setTitle(LanguageManager.tr("menu_import"))
        self.action_import_musicxml.setText(LanguageManager.tr("menu_import_musicxml"))
        self.action_import_midi.setText(LanguageManager.tr("menu_import_midi"))
        self.action_load_json.setText(LanguageManager.tr("menu_load_json"))

        self.action_save_json.setText(LanguageManager.tr("menu_save_json"))

        # Templates submenu
        self._templates_menu.setTitle(LanguageManager.tr("menu_templates"))
        self.action_template_blank.setText(LanguageManager.tr("menu_templates_blank"))
        self.action_template_piano.setText(LanguageManager.tr("menu_templates_piano"))
        self.action_template_duo.setText(LanguageManager.tr("menu_templates_duo"))
        self.action_template_scale.setText(LanguageManager.tr("menu_templates_scale"))

        # Recent files submenu
        self._recent_menu.setTitle(LanguageManager.tr("menu_recent"))

        # Export submenu
        self._export_menu.setTitle(LanguageManager.tr("menu_export"))
        self.action_export_mxl.setText(LanguageManager.tr("menu_export_mxl"))
        self.action_export_midi.setText(LanguageManager.tr("menu_export_midi"))
        self.action_export_xml.setText(LanguageManager.tr("menu_export_xml"))
        self.action_export_ly.setText(LanguageManager.tr("menu_export_ly"))

        # Edit menu
        self._edit_menu.setTitle(LanguageManager.tr("menu_edit"))
        self.action_undo.setText(LanguageManager.tr("menu_undo"))
        self.action_redo.setText(LanguageManager.tr("menu_redo"))

        # View menu
        self._view_menu.setTitle(LanguageManager.tr("menu_view"))
        self.action_preview.setText(LanguageManager.tr("menu_preview"))
        self._theme_menu.setTitle(LanguageManager.tr("menu_theme"))
        self.action_theme_light.setText(LanguageManager.tr("menu_theme_light"))
        self.action_theme_dark.setText(LanguageManager.tr("menu_theme_dark"))

        # Language menu
        self._lang_menu.setTitle(LanguageManager.tr("menu_language"))
        self.action_lang_zh.setText(LanguageManager.tr("menu_lang_zh"))
        self.action_lang_en.setText(LanguageManager.tr("menu_lang_en"))

        # Buttons
        self.btn_load_json.setText(LanguageManager.tr("btn_load_json"))
        self.btn_save_json.setText(LanguageManager.tr("btn_save_json"))
        self.btn_validate.setText(LanguageManager.tr("btn_validate"))
        self.btn_import.setText(LanguageManager.tr("btn_import"))
        self.btn_export.setText(LanguageManager.tr("btn_export"))

        # Placeholders
        self.json_text_edit.setPlaceholderText(LanguageManager.tr("json_placeholder"))
        self.log_console.setPlaceholderText(LanguageManager.tr("log_placeholder"))

        # Re-apply shortcuts (in case labels changed)
        self._setup_shortcuts()

        # Refresh recent files menu
        self._refresh_recent_files_menu()

    # ── Recent files ──────────────────────────────────────────────────────

    def _refresh_recent_files_menu(self):
        """Rebuild the recent files submenu from the config."""
        self._recent_menu.clear()
        recent_files = self.config_manager.get_recent_files()

        if not recent_files:
            action = QAction(LanguageManager.tr("msg_no_recent_files"), self)
            action.setEnabled(False)
            self._recent_menu.addAction(action)
            return

        for file_path in recent_files:
            if not os.path.exists(file_path):
                continue
            action = QAction(os.path.basename(file_path), self)
            action.setToolTip(file_path)
            action.triggered.connect(lambda checked, p=file_path: self._open_recent_file(p))
            self._recent_menu.addAction(action)

    def _open_recent_file(self, file_path: str):
        """
        Open a file from the recent files list.

        Args:
            file_path: Path to the file to open.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            self._load_json_file(file_path)
        elif ext in (".xml", ".mxl", ".mid", ".midi"):
            self._import_file(file_path)
        else:
            logger.warning(f"Unsupported recent file type: {ext}")

    def _record_recent_file(self, file_path: str):
        """
        Add a file to the recent files list and refresh the menu.

        Args:
            file_path: Path to the file that was opened.
        """
        self.config_manager.add_recent_file(file_path)
        self._refresh_recent_files_menu()

    # ── Slots: Edit actions ───────────────────────────────────────────────

    def _on_undo(self):
        """Undo the last edit in the JSON editor."""
        self.json_text_edit.undo()

    def _on_redo(self):
        """Redo the last undone edit in the JSON editor."""
        self.json_text_edit.redo()

    # ── Slots: UI actions ─────────────────────────────────────────────────

    def on_validate_json(self):
        """
        Validate the JSON content: check syntax and score schema.

        First parses with json.loads(), then validates with json_validator.validate().
        Results are displayed in the log console and message boxes.
        """
        text = self.json_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, LanguageManager.tr("msg_validation_result"),
                                LanguageManager.tr("msg_empty_json_validate"))
            logger.warning("JSON validation failed: empty content")
            return

        # Step 1: JSON syntax parsing
        try:
            json_data = json.loads(text)
            logger.info("JSON syntax is valid")
        except json.JSONDecodeError as e:
            self._validation_status = "failed"
            self._update_status_bar()
            QMessageBox.critical(self, LanguageManager.tr("msg_validation_result"),
                                 LanguageManager.tr("msg_json_format_error", str(e)))
            logger.error(f"JSON format validation failed: {e}")
            return

        # Step 2: Score schema validation
        is_valid, errors = json_validator.validate(json_data)
        if is_valid:
            self._validation_status = "ok"
            self._update_status_bar()
            QMessageBox.information(self, LanguageManager.tr("msg_validation_result"),
                                    LanguageManager.tr("msg_json_valid"))
            logger.info("JSON validation passed (valid syntax + valid score data)")
        else:
            self._validation_status = "failed"
            self._update_status_bar()
            error_msg = LanguageManager.tr("msg_validation_failed", "\n".join(errors))
            QMessageBox.warning(self, LanguageManager.tr("msg_validation_result"), error_msg)
            logger.warning(f"JSON validation failed: {'; '.join(errors)}")

    def _load_json_file(self, file_path: str):
        """
        Load a JSON file into the editor.

        Args:
            file_path: Path to the JSON file to load.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.json_text_edit.setPlainText(content)
            self._current_file_path = file_path
            self._validation_status = "none"
            self._update_status_bar()
            self._record_recent_file(file_path)
            logger.info(f"Loaded JSON file: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_load_failed"),
                                 LanguageManager.tr("msg_cannot_load", str(e)))
            logger.error(f"Failed to load JSON file: {e}")

    def on_load_json(self):
        """Open a file dialog to load a JSON file into the editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, LanguageManager.tr("fd_load_json"), "",
            LanguageManager.tr("fd_json_filter")
        )
        if not file_path:
            return
        self._load_json_file(file_path)

    def on_save_json(self):
        """Open a file dialog to save the editor content as a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, LanguageManager.tr("fd_save_json"), "",
            LanguageManager.tr("fd_json_filter")
        )
        if not file_path:
            return
        try:
            content = self.json_text_edit.toPlainText()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._current_file_path = file_path
            self._update_status_bar()
            self._record_recent_file(file_path)
            logger.info(f"JSON saved to: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_save_failed"),
                                 LanguageManager.tr("msg_cannot_save", str(e)))
            logger.error(f"Failed to save JSON file: {e}")

    # ── Template handlers ─────────────────────────────────────────────────

    def on_load_template(self, template_key: str):
        """
        Load a pre-built template into the JSON editor.

        Args:
            template_key: Template key, one of "blank", "piano", "duo", "scale".
        """
        template = TEMPLATES.get(template_key)
        if template is None:
            logger.warning(f"Unknown template: {template_key}")
            return

        json_text = json.dumps(template, indent=2, ensure_ascii=False)
        self.json_text_edit.setPlainText(json_text)
        self._current_file_path = ""
        self._validation_status = "none"
        self._update_status_bar()
        logger.info(f"Loaded template: {template_key}")

    # ── Import handlers ───────────────────────────────────────────────────

    def on_import_file(self, fmt: str):
        """
        Import a file (MusicXML or MIDI) and load the JSON into the editor.

        Args:
            fmt: Format type, "musicxml" or "midi".
        """
        if fmt == "musicxml":
            title = LanguageManager.tr("fd_load_json")
            flt = "MusicXML Files (*.xml *.mxl);;All Files (*)"
        else:
            title = LanguageManager.tr("fd_load_json")
            flt = "MIDI Files (*.mid *.midi);;All Files (*)"

        file_path, _ = QFileDialog.getOpenFileName(self, title, "", flt)
        if not file_path:
            return
        self._import_file(file_path)

    def _import_file(self, file_path: str):
        """
        Import a file via the format importer and load JSON into the editor.

        Args:
            file_path: Path to the file to import.
        """
        self._show_progress(LanguageManager.tr("progress_importing"))
        try:
            from core.format_importer import import_file
            json_data = import_file(file_path)
            json_text = json.dumps(json_data, indent=2, ensure_ascii=False)
            self.json_text_edit.setPlainText(json_text)
            self._current_file_path = ""
            self._validation_status = "none"
            self._update_status_bar()
            self._record_recent_file(file_path)
            QMessageBox.information(
                self, LanguageManager.tr("msg_import_success"),
                LanguageManager.tr("msg_import_success_content", file_path)
            )
            logger.info(f"Import successful: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_import_failed"),
                                 LanguageManager.tr("msg_import_error", str(e)))
            logger.error(f"Import failed: {e}")
        finally:
            self._hide_progress()

    def on_import_dialog(self):
        """Open a unified import dialog supporting multiple file formats."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, LanguageManager.tr("msg_import_hint"), "",
            LanguageManager.tr("fd_import_all_filter")
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            self._load_json_file(file_path)
        else:
            self._import_file(file_path)

    # ── Export handlers ───────────────────────────────────────────────────

    def _parse_and_validate_json(self) -> dict:
        """
        Parse and validate JSON content from the editor.

        Returns:
            The parsed dict, or None on failure.
        """
        text = self.json_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, LanguageManager.tr("msg_export_hint"),
                                LanguageManager.tr("msg_empty_json_export"))
            logger.warning("Export failed: JSON content is empty")
            return None

        try:
            json_data = json.loads(text)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_export_failed"),
                                 LanguageManager.tr("msg_json_format_error", str(e)))
            logger.error(f"Export failed: JSON format error - {e}")
            return None

        from core import json_validator as jv
        is_valid, errors = jv.validate(json_data)
        if not is_valid:
            error_msg = LanguageManager.tr("msg_validation_failed", "\n".join(errors))
            QMessageBox.critical(self, LanguageManager.tr("msg_export_failed"), error_msg)
            logger.error(f"Export failed: {error_msg}")
            return None

        self._validation_status = "ok"
        self._update_status_bar()
        return json_data

    def on_export_format(self, fmt: str):
        """
        Export the JSON content to a specific format asynchronously.

        Args:
            fmt: Format identifier, one of "mxl", "midi", "xml", "ly".
        """
        json_data = self._parse_and_validate_json()
        if json_data is None:
            return

        # Determine file extension and filter
        format_config = {
            "mxl":  {"ext": ".mxl",  "filter_key": "fd_mxl_filter", "dialog_title_key": "fd_export_mxl"},
            "midi": {"ext": ".mid",  "filter_key": "fd_export_filter", "dialog_title_key": "fd_export_midi"},
            "xml":  {"ext": ".xml",  "filter_key": "fd_export_filter", "dialog_title_key": "fd_export_xml"},
            "ly":   {"ext": ".ly",   "filter_key": "fd_export_filter", "dialog_title_key": "fd_export_ly"},
        }
        cfg = format_config.get(fmt, format_config["mxl"])

        default_dir = "./output/"
        default_name = f"{json_data.get('title', 'Untitled')}{cfg['ext']}"
        file_path, _ = QFileDialog.getSaveFileName(
            self, LanguageManager.tr(cfg["dialog_title_key"]),
            os.path.join(default_dir, default_name),
            LanguageManager.tr(cfg["filter_key"])
        )
        if not file_path:
            return

        # Run export in a background thread
        self._show_progress(LanguageManager.tr("progress_exporting"))
        self._export_worker = ExportWorker(json_data, file_path, fmt)
        self._export_worker.finished_signal.connect(self._on_export_finished)
        self._export_worker.start()

    def _on_export_finished(self, success: bool, error_msg: str, output_path: str):
        """
        Handle the completion of an export operation.

        Args:
            success: Whether the export succeeded.
            error_msg: Error message if failed, empty string if success.
            output_path: The output file path.
        """
        self._hide_progress()
        if success:
            QMessageBox.information(
                self, LanguageManager.tr("msg_export_success"),
                LanguageManager.tr("msg_export_success_content", output_path)
            )
            logger.info(f"Export successful: {output_path}")
        else:
            QMessageBox.critical(self, LanguageManager.tr("msg_export_failed"),
                                 LanguageManager.tr("msg_export_error", error_msg))
            logger.error(f"Export failed: {error_msg}")

    def on_export_dialog(self):
        """Open a format selection dialog then export in the chosen format."""
        json_data = self._parse_and_validate_json()
        if json_data is None:
            return

        from PyQt6.QtWidgets import QInputDialog
        formats = ["mxl", "midi", "xml", "ly"]
        format_labels = [
            LanguageManager.tr("msg_format_mxl"),
            LanguageManager.tr("msg_format_midi"),
            LanguageManager.tr("msg_format_xml"),
            LanguageManager.tr("msg_format_ly"),
        ]

        fmt, ok = QInputDialog.getItem(
            self, LanguageManager.tr("msg_select_export_format"),
            LanguageManager.tr("msg_select_export_format"),
            format_labels, 0, False
        )
        if not ok:
            return

        fmt_key = formats[format_labels.index(fmt)]
        self.on_export_format(fmt_key)

    # ── Preview handler ───────────────────────────────────────────────────

    def on_preview_score(self):
        """Generate a score preview and open it with the system viewer."""
        text = self.json_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, LanguageManager.tr("msg_preview_failed"),
                                LanguageManager.tr("msg_preview_empty"))
            return

        json_data = self._parse_and_validate_json()
        if json_data is None:
            return

        self._show_progress(LanguageManager.tr("progress_previewing"))
        self._preview_worker = PreviewWorker(json_data)
        self._preview_worker.finished_signal.connect(self._on_preview_finished)
        self._preview_worker.start()

    def _on_preview_finished(self, success: bool, file_path: str, error_msg: str):
        """
        Handle the completion of a preview generation.

        Args:
            success: Whether the preview was generated successfully.
            file_path: Path to the generated preview file.
            error_msg: Error message if failed.
        """
        self._hide_progress()
        if success:
            logger.info(f"Preview generated: {file_path}")
            # Open with system default viewer
            try:
                if platform.system() == "Windows":
                    os.startfile(file_path)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", file_path])
                else:
                    subprocess.Popen(["xdg-open", file_path])
            except Exception as e:
                logger.warning(f"Could not open preview file: {e}")
        else:
            QMessageBox.critical(self, LanguageManager.tr("msg_preview_failed"),
                                 LanguageManager.tr("msg_preview_error", error_msg))
            logger.error(f"Preview failed: {error_msg}")
