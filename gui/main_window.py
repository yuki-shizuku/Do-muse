"""
Do Muse — Main window module
Defines the main window layout, menu bar, and interaction logic.
Supports JSON editing, validation, and MXL export with i18n (zh/en).
"""

import json
import logging
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QPushButton, QSplitter,
    QMenuBar, QAction, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt

from core import json_validator
from core.i18n import LanguageManager
from core.config_manager import ConfigManager
from gui.log_handler import LogHandler

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Do Muse main window, extends QMainWindow.

    Builds the full GUI layout and interaction, including:
      - JSON editor with log console
      - File menu (load/save JSON, export MXL)
      - Language menu (Chinese/English)
      - Validation and export actions

    :param parent: Parent widget, defaults to None.
    """

    def __init__(self, parent=None):
        """
        Initialize the main window: set up menus, layout, and logging.

        Args:
            parent: Parent widget, defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle(LanguageManager.tr("window_title"))
        self.resize(1000, 700)

        self.config_manager = ConfigManager()

        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_logging()
        self._connect_signals()

        logger.info("Main window initialized")

    # ── Menu bar ──────────────────────────────────────────────────────────

    def _setup_menu_bar(self):
        """Build the menu bar: File menu, Language menu, and their items."""
        menu_bar = self.menuBar()

        # ── File menu ──
        file_menu = menu_bar.addMenu(LanguageManager.tr("menu_file"))

        self.action_load_json = QAction(LanguageManager.tr("menu_load_json"), self)
        self.action_load_json.triggered.connect(self.on_load_json)
        file_menu.addAction(self.action_load_json)

        self.action_save_json = QAction(LanguageManager.tr("menu_save_json"), self)
        self.action_save_json.triggered.connect(self.on_save_json)
        file_menu.addAction(self.action_save_json)

        self.action_export_mxl = QAction(LanguageManager.tr("menu_export_mxl"), self)
        self.action_export_mxl.triggered.connect(self.on_export_mxl)
        file_menu.addAction(self.action_export_mxl)

        file_menu.addSeparator()

        action_exit = QAction(LanguageManager.tr("menu_exit"), self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # ── Language menu ──
        lang_menu = menu_bar.addMenu(LanguageManager.tr("menu_language"))

        self.action_lang_zh = QAction(LanguageManager.tr("menu_lang_zh"), self)
        self.action_lang_zh.triggered.connect(lambda: self._switch_language("zh"))
        lang_menu.addAction(self.action_lang_zh)

        self.action_lang_en = QAction(LanguageManager.tr("menu_lang_en"), self)
        self.action_lang_en.triggered.connect(lambda: self._switch_language("en"))
        lang_menu.addAction(self.action_lang_en)

    # ── Central widget ────────────────────────────────────────────────────

    def _setup_central_widget(self):
        """Build the central layout: JSON editor + log console (splitter), bottom toolbar."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── Splitter: JSON editor | Log console ──
        splitter = QSplitter(Qt.Horizontal, self)

        # Left: JSON editor
        self.json_text_edit = QPlainTextEdit(self)
        self.json_text_edit.setPlaceholderText(LanguageManager.tr("json_placeholder"))
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

        self.btn_export_mxl = QPushButton(LanguageManager.tr("btn_export_mxl"), self)
        bottom_layout.addWidget(self.btn_export_mxl)

        main_layout.addLayout(bottom_layout)

    # ── Signal connections ────────────────────────────────────────────────

    def _connect_signals(self):
        """Connect all button signals to their slot methods."""
        self.btn_load_json.clicked.connect(self.on_load_json)
        self.btn_save_json.clicked.connect(self.on_save_json)
        self.btn_validate.clicked.connect(self.on_validate_json)
        self.btn_export_mxl.clicked.connect(self.on_export_mxl)

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

        logger.info(f"Language switched to {lang}")

    def _retranslate_ui(self):
        """Update all UI text elements to match the current language."""
        self.setWindowTitle(LanguageManager.tr("window_title"))

        # Menu bar
        file_menu = self.menuBar().actions()[0]
        file_menu.setText(LanguageManager.tr("menu_file"))
        self.action_load_json.setText(LanguageManager.tr("menu_load_json"))
        self.action_save_json.setText(LanguageManager.tr("menu_save_json"))
        self.action_export_mxl.setText(LanguageManager.tr("menu_export_mxl"))

        lang_menu = self.menuBar().actions()[1]
        lang_menu.setText(LanguageManager.tr("menu_language"))
        self.action_lang_zh.setText(LanguageManager.tr("menu_lang_zh"))
        self.action_lang_en.setText(LanguageManager.tr("menu_lang_en"))

        # Buttons
        self.btn_load_json.setText(LanguageManager.tr("btn_load_json"))
        self.btn_save_json.setText(LanguageManager.tr("btn_save_json"))
        self.btn_validate.setText(LanguageManager.tr("btn_validate"))
        self.btn_export_mxl.setText(LanguageManager.tr("btn_export_mxl"))

        # Placeholders
        self.json_text_edit.setPlaceholderText(LanguageManager.tr("json_placeholder"))
        self.log_console.setPlaceholderText(LanguageManager.tr("log_placeholder"))

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
            QMessageBox.critical(self, LanguageManager.tr("msg_validation_result"),
                                 LanguageManager.tr("msg_json_format_error", str(e)))
            logger.error(f"JSON format validation failed: {e}")
            return

        # Step 2: Score schema validation
        is_valid, errors = json_validator.validate(json_data)
        if is_valid:
            QMessageBox.information(self, LanguageManager.tr("msg_validation_result"),
                                    LanguageManager.tr("msg_json_valid"))
            logger.info("JSON validation passed (valid syntax + valid score data)")
        else:
            error_msg = LanguageManager.tr("msg_validation_failed", "\n".join(errors))
            QMessageBox.warning(self, LanguageManager.tr("msg_validation_result"), error_msg)
            logger.warning(f"JSON validation failed: {'; '.join(errors)}")

    def on_load_json(self):
        """
        Open a file dialog to load a JSON file into the editor.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, LanguageManager.tr("fd_load_json"), "",
            LanguageManager.tr("fd_json_filter")
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.json_text_edit.setPlainText(content)
            logger.info(f"Loaded JSON file: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_load_failed"),
                                 LanguageManager.tr("msg_cannot_load", str(e)))
            logger.error(f"Failed to load JSON file: {e}")

    def on_save_json(self):
        """
        Open a file dialog to save the editor content as a JSON file.
        """
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
            logger.info(f"JSON saved to: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_save_failed"),
                                 LanguageManager.tr("msg_cannot_save", str(e)))
            logger.error(f"Failed to save JSON file: {e}")

    def on_export_mxl(self):
        """
        Export the JSON content to an .mxl file.

        Parses and validates the JSON, then exports to MusicXML (.mxl) format.
        """
        text = self.json_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, LanguageManager.tr("msg_export_hint"),
                                LanguageManager.tr("msg_empty_json_export"))
            logger.warning("MXL export failed: JSON content is empty")
            return

        # Parse JSON
        try:
            json_data = json.loads(text)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_export_failed"),
                                 LanguageManager.tr("msg_json_format_error", str(e)))
            logger.error(f"MXL export failed: JSON format error - {e}")
            return

        # Validate JSON
        from core import json_validator as jv
        is_valid, errors = jv.validate(json_data)
        if not is_valid:
            error_msg = LanguageManager.tr("msg_validation_failed", "\n".join(errors))
            QMessageBox.critical(self, LanguageManager.tr("msg_export_failed"), error_msg)
            logger.error(f"MXL export failed: {error_msg}")
            return

        # Choose save path
        default_dir = "./output/"
        file_path, _ = QFileDialog.getSaveFileName(
            self, LanguageManager.tr("fd_export_mxl"), default_dir,
            LanguageManager.tr("fd_mxl_filter")
        )
        if not file_path:
            return

        try:
            from core.music_exporter import export_to_mxl
            export_to_mxl(json_data, file_path)
            QMessageBox.information(
                self, LanguageManager.tr("msg_export_success"),
                LanguageManager.tr("msg_export_success_content", file_path)
            )
            logger.info(f"MXL export successful: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_export_failed"),
                                 LanguageManager.tr("msg_export_error", str(e)))
            logger.error(f"MXL export failed: {e}")