"""
Do Muse — Natural language driven music score generator desktop application
Entry point
"""

import sys
import os
import argparse
import json
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.i18n import LanguageManager


def run_cli(args):
    """
    执行命令行模式的导入/导出操作。

    Args:
        args: argparse.Namespace 对象，包含 input、export、format 等参数。
    """
    from core.format_importer import import_file
    from core.music_exporter import export_score
    from core.json_validator import validate

    # Step 1: Load input file (if --input is provided)
    json_data = None
    if args.input:
        ext = os.path.splitext(args.input)[1].lower()
        if ext == ".json":
            with open(args.input, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        else:
            # Import from MusicXML/MIDI
            json_data = import_file(args.input)
            print(f"Imported from: {args.input}")

    # Step 2: Validate JSON
    if json_data is None:
        print("Error: No input provided. Use --input to specify a JSON/MusicXML/MIDI file.")
        sys.exit(1)

    is_valid, errors = validate(json_data)
    if not is_valid:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # Step 3: Export (if --export is provided)
    if args.export:
        fmt = args.format or "mxl"
        result = export_score(json_data, args.export, fmt)
        print(f"Exported to: {result}")
    else:
        # Print JSON to stdout
        print(json.dumps(json_data, ensure_ascii=False, indent=2))


def run_gui():
    """启动 GUI 模式。"""
    app = QApplication(sys.argv)
    app.setApplicationName("Do Muse")
    app.setApplicationDisplayName("Do Muse - Score Generator")

    # Load config and apply language setting
    config = ConfigManager().load_config()
    LanguageManager.set_language(config.get("language", "zh"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def main():
    """主入口：解析命令行参数，启动 GUI 或 CLI 模式。"""
    parser = argparse.ArgumentParser(
        description="Do Muse — JSON-driven music score generator",
    )
    parser.add_argument(
        "-i", "--input",
        help="Input file path (.json, .xml, .mxl, .mid, .midi)",
    )
    parser.add_argument(
        "-e", "--export",
        help="Output file path for export",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["mxl", "midi", "xml", "ly"],
        help="Export format (default: mxl)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch GUI mode (default when no CLI args given)",
    )

    args = parser.parse_args()

    # If no CLI arguments, launch GUI
    if args.input or args.export:
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()