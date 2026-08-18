"""
JSON syntax highlighter — provides syntax highlighting for JSON text in QPlainTextEdit.
"""

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter


class JsonHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for JSON content.

    Highlights keys, strings, numbers, booleans, null, and structural characters.

    :param parent: Parent QTextDocument.
    """

    def __init__(self, parent):
        """
        Initialize the highlighter with JSON highlighting rules.

        Args:
            parent: The QTextDocument to attach this highlighter to.
        """
        super().__init__(parent)

        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []

        # Key: "key":
        key_format = QTextCharFormat()
        key_format.setForeground(QColor(81, 40, 183))
        key_format.setFontWeight(QFont.Weight.Bold)
        self._rules.append((QRegularExpression(r'"[^"\\]*(?:\\.[^"\\]*)*"\s*:'), key_format))

        # String value: "..."
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(4, 81, 165))
        self._rules.append((QRegularExpression(r'"[^"\\]*(?:\\.[^"\\]*)*"'), string_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(0, 128, 0))
        self._rules.append((QRegularExpression(r'\b-?\d+\.?\d*([eE][+-]?\d+)?\b'), number_format))

        # Boolean
        bool_format = QTextCharFormat()
        bool_format.setForeground(QColor(183, 28, 28))
        bool_format.setFontWeight(QFont.Weight.Bold)
        self._rules.append((QRegularExpression(r'\btrue\b|\bfalse\b'), bool_format))

        # Null
        null_format = QTextCharFormat()
        null_format.setForeground(QColor(183, 28, 28))
        null_format.setFontWeight(QFont.Weight.Bold)
        null_format.setFontItalic(True)
        self._rules.append((QRegularExpression(r'\bnull\b'), null_format))

    def highlightBlock(self, text: str):
        """
        Apply highlighting rules to a block of text.

        Args:
            text: The text block to highlight.
        """
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                captured_start = match.capturedStart()
                captured_len = match.capturedLength()
                self.setFormat(captured_start, captured_len, fmt)
