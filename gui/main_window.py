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

        self.btn_import = QPushButton(LanguageManager.tr("btn_import"), self)
        bottom_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton(LanguageManager.tr("btn_export"), self)
        bottom_layout.addWidget(self.btn_export)

        main_layout.addLayout(bottom_layout)

    # ── Signal connections ────────────────────────────────────────────────

    def _connect_signals(self):
        """Connect all button signals to their slot methods."""
        self.btn_load_json.clicked.connect(self.on_load_json)
        self.btn_save_json.clicked.connect(self.on_save_json)
        self.btn_validate.clicked.connect(self.on_validate_json)
        self.btn_import.clicked.connect(self.on_import_dialog)
        self.btn_export.clicked.connect(self.on_export_dialog)

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

        # Menu bar — File menu
        self._file_menu.setTitle(LanguageManager.tr("menu_file"))

        # Import submenu
        self._import_menu.setTitle(LanguageManager.tr("menu_import"))
        self.action_import_musicxml.setText(LanguageManager.tr("menu_import_musicxml"))
        self.action_import_midi.setText(LanguageManager.tr("menu_import_midi"))
        self.action_load_json.setText(LanguageManager.tr("menu_load_json"))

        self.action_save_json.setText(LanguageManager.tr("menu_save_json"))

        # Export submenu
        self._export_menu.setTitle(LanguageManager.tr("menu_export"))
        self.action_export_mxl.setText(LanguageManager.tr("menu_export_mxl"))
        self.action_export_midi.setText(LanguageManager.tr("menu_export_midi"))
        self.action_export_xml.setText(LanguageManager.tr("menu_export_xml"))
        self.action_export_ly.setText(LanguageManager.tr("menu_export_ly"))

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

        try:
            from core.format_importer import import_file
            json_data = import_file(file_path)
            json_text = json.dumps(json_data, indent=2, ensure_ascii=False)
            self.json_text_edit.setPlainText(json_text)
            QMessageBox.information(
                self, LanguageManager.tr("msg_import_success"),
                LanguageManager.tr("msg_import_success_content", file_path)
            )
            logger.info(f"Import successful: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_import_failed"),
                                 LanguageManager.tr("msg_import_error", str(e)))
            logger.error(f"Import failed: {e}")

    def on_import_dialog(self):
        """
        Open a unified import dialog supporting multiple file formats.

        User can pick .xml, .mxl, .mid, .midi, or .json files.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, LanguageManager.tr("msg_import_hint"), "",
            LanguageManager.tr("fd_import_all_filter")
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            # Load JSON directly
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.json_text_edit.setPlainText(content)
                logger.info(f"Loaded JSON file: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, LanguageManager.tr("msg_import_failed"),
                                     LanguageManager.tr("msg_import_error", str(e)))
                logger.error(f"Failed to load JSON file: {e}")
        else:
            # Import via format_importer
            try:
                from core.format_importer import import_file
                json_data = import_file(file_path)
                json_text = json.dumps(json_data, indent=2, ensure_ascii=False)
                self.json_text_edit.setPlainText(json_text)
                QMessageBox.information(
                    self, LanguageManager.tr("msg_import_success"),
                    LanguageManager.tr("msg_import_success_content", file_path)
                )
                logger.info(f"Import successful: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, LanguageManager.tr("msg_import_failed"),
                                     LanguageManager.tr("msg_import_error", str(e)))
                logger.error(f"Import failed: {e}")

    # ── Export handlers ───────────────────────────────────────────────────

    def _parse_and_validate_json(self) -> dict:
        """
        Parse and validate JSON content from the editor.
        Returns the parsed dict, or None on failure.
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

        return json_data

    def on_export_format(self, fmt: str):
        """
        Export the JSON content to a specific format.

        Args:
            fmt: Format identifier, one of "mxl", "midi", "xml", "ly".
        """
        json_data = self._parse_and_validate_json()
        if json_data is None:
            return

        # Determine file extension and filter
        format_config = {
            "mxl":  {"ext": ".mxl",  "filter_key": "fd_mxl_filter", "dialog_title_key": "fd_export_mxl"},
            "midi": {"ext": ".mid",  "filter_key": "fd_export_filter", "dialog_title_key": "fd_export_mxl"},
            "xml":  {"ext": ".xml",  "filter_key": "fd_export_filter", "dialog_title_key": "fd_export_mxl"},
            "ly":   {"ext": ".ly",   "filter_key": "fd_export_filter", "dialog_title_key": "fd_export_mxl"},
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

        try:
            from core.music_exporter import export_score
            export_score(json_data, file_path, fmt)
            QMessageBox.information(
                self, LanguageManager.tr("msg_export_success"),
                LanguageManager.tr("msg_export_success_content", file_path)
            )
            logger.info(f"Export successful ({fmt}): {file_path}")
        except Exception as e:
            QMessageBox.critical(self, LanguageManager.tr("msg_export_failed"),
                                 LanguageManager.tr("msg_export_error", str(e)))
            logger.error(f"Export failed ({fmt}): {e}")

    def on_export_dialog(self):
        """
        Open a format selection dialog then export in the chosen format.
        """
        json_data = self._parse_and_validate_json()
        if json_data is None:
            return

        # Let user choose format
        from PyQt5.QtWidgets import QInputDialog
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

        # Map label back to format key
        fmt_key = formats[format_labels.index(fmt)]
        self.on_export_format(fmt_key)