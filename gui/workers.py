"""
Do Muse — Worker threads for async operations

Contains export and preview worker threads that run in background
to avoid blocking the UI.
"""

import os
import tempfile
import subprocess
import logging

from PyQt6.QtCore import QThread, pyqtSignal


logger = logging.getLogger(__name__)


class ExportWorker(QThread):
    """
    Worker thread for exporting scores without blocking the UI.

    Emits finished_signal with (success, error_message, output_path).
    """

    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, json_data: dict, output_path: str, fmt: str):
        """
        Initialize the export worker.

        Args:
            json_data: Validated score JSON dict.
            output_path: Output file path.
            fmt: Format identifier ("mxl", "midi", "xml", "ly", "mp3", "wav",
                 "flac", "ogg").
        """
        super().__init__()
        self._json_data = json_data
        self._output_path = output_path
        self._fmt = fmt

    def run(self):
        """
        Execute the export in a background thread.
        """
        try:
            from core.music_exporter import export_score
            export_score(self._json_data, self._output_path, self._fmt)
            self.finished_signal.emit(True, "", self._output_path)
        except Exception as e:
            self.finished_signal.emit(False, str(e), self._output_path)


class PreviewWorker(QThread):
    """
    Worker thread for generating a score preview image.

    Emits finished_signal with (success, image_path, error_message).
    """

    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, json_data: dict):
        """
        Initialize the preview worker.

        Args:
            json_data: Validated score JSON dict.
        """
        super().__init__()
        self._json_data = json_data

    def run(self):
        """
        Generate a PNG preview of the score using MuseScore CLI.
        Exports JSON → MusicXML → PNG via MuseScore's headless conversion.
        """
        xml_path = None
        try:
            from core.music_exporter import _build_score, _remove_doctype, _find_musescore

            score = _build_score(self._json_data)

            # Step 1: Export to temporary MusicXML
            tmp_fd, xml_path = tempfile.mkstemp(suffix='.xml')
            os.close(tmp_fd)

            score.write('musicxml', fp=xml_path)

            # Remove DOCTYPE to prevent network fetch
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            xml_content = _remove_doctype(xml_content)
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)

            # Step 2: Convert MusicXML to PNG via MuseScore CLI
            musescore_path = _find_musescore()
            if musescore_path:
                png_prefix = xml_path.replace('.xml', '')
                cmd = [musescore_path, "-o", png_prefix + ".png", "-T", "200", xml_path]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=30,
                )
                png_path = png_prefix + ".png"
                if os.path.exists(png_path):
                    self.finished_signal.emit(True, png_path, "")
                else:
                    svg_path = png_prefix + ".svg"
                    if os.path.exists(svg_path):
                        self.finished_signal.emit(True, svg_path, "")
                    else:
                        raise RuntimeError(
                            f"MuseScore did not produce preview image. "
                            f"stderr: {proc.stderr.decode('utf-8', errors='replace')}"
                        )
            else:
                # Fallback: open the MusicXML directly with system viewer
                self.finished_signal.emit(True, xml_path, "")
                xml_path = None  # Don't clean up

        except Exception as e:
            self.finished_signal.emit(False, "", str(e))
        finally:
            if xml_path and os.path.exists(xml_path):
                try:
                    os.unlink(xml_path)
                except OSError:
                    pass
