"""
Do Muse — Log handler module
Redirects Python logging output to a QPlainTextEdit widget in the GUI
"""

import logging
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextCursor, QTextCharFormat


class LogHandler(logging.Handler):
    """
    Log handler that redirects logging messages to a QPlainTextEdit widget.

    :param text_edit: Target QPlainTextEdit instance.
    """

    LEVEL_COLORS = {
        logging.ERROR: QColor(255, 80, 80),
        logging.WARNING: QColor(255, 200, 50),
        logging.INFO: QColor(212, 212, 212),
        logging.DEBUG: QColor(140, 140, 140),
    }

    def __init__(self, text_edit: QPlainTextEdit):
        """
        Initialize the log handler.

        Args:
            text_edit: QPlainTextEdit widget to display log messages.
        """
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        ))

    def emit(self, record: logging.LogRecord):
        """
        Process a log record: format and append the message to the console with color.

        Args:
            record: logging.LogRecord containing the log message and level.
        """
        try:
            msg = self.format(record)
            color = self.LEVEL_COLORS.get(record.levelno, QColor(212, 212, 212))

            text_format = QTextCharFormat()
            text_format.setForeground(color)
            self.text_edit.mergeCurrentCharFormat(text_format)
            self.text_edit.insertPlainText(msg + "\n")
            self.text_edit.moveCursor(QTextCursor.End)

            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception:
            self.handleError(record)