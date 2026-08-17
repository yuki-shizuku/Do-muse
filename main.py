"""
Do Muse — Natural language driven music score generator desktop application
Entry point
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.i18n import LanguageManager


def main():
    """Initialize QApplication and launch the main window."""
    app = QApplication(sys.argv)
    app.setApplicationName("Do Muse")
    app.setApplicationDisplayName("Do Muse - Score Generator")

    # Load stylesheet
    style_path = os.path.join(os.path.dirname(__file__), "resources", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # Load config and apply language setting
    config = ConfigManager().load_config()
    LanguageManager.set_language(config.get("language", "zh"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()