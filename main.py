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


def _is_frozen() -> bool:
    """Return True when running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to a bundled resource file.

    When running as a PyInstaller bundle, resources are extracted to
    sys._MEIPASS at runtime. When running from source, resources are
    relative to the project root.

    Args:
        relative_path: Path relative to the project root, e.g. "resources/style.qss".

    Returns:
        str: Absolute path to the resource.
    """
    if _is_frozen():
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def ensure_icon_exists() -> str:
    """
    Ensure the icon file exists. If not, create a default one.
    
    Returns:
        str: Path to the icon file.
    """
    icon_path = get_app_dir()
    if _is_frozen():
        # 在打包模式下，图标应该已经在exe中
        icon_file = os.path.join(icon_path, "domuse.ico")
    else:
        # 在开发模式下，使用windows文件夹中的图标
        icon_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "windows", "domuse.ico")
    
    # 如果图标文件不存在，创建一个默认的
    if not os.path.exists(icon_file):
        try:
            import subprocess
            script_dir = os.path.dirname(os.path.abspath(__file__))
            create_icon_script = os.path.join(script_dir, "create_default_icon.py")
            
            if os.path.exists(create_icon_script):
                result = subprocess.run([sys.executable, create_icon_script], 
                                      capture_output=True, text=True, cwd=script_dir)
                if result.returncode == 0:
                    print("默认图标已创建")
                else:
                    print(f"创建图标失败: {result.stderr}")
        except Exception as e:
            print(f"创建图标时出错: {e}")
    
    return icon_file


def get_app_dir() -> str:
    """
    Get the writable application directory.

    When frozen, this is the directory containing the .exe (where config.ini
    and output/ live). When running from source, this is the project root.
    """
    if _is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


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

    # Load config once and apply language setting
    config = ConfigManager().load_config()
    LanguageManager.set_language(config.get("language", "zh"))

    window = MainWindow(config)
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
        choices=["mxl", "midi", "xml", "ly", "mp3", "wav", "flac", "ogg"],
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