"""
Configuration management — reads and writes config.ini using configparser
"""

import configparser
import json
import os
from typing import Dict, Any, List


class ConfigManager:
    """Config file manager responsible for reading/writing config.ini."""

    MAX_RECENT_FILES = 10

    def __init__(self, config_path: str = None):
        """
        Initialize the config manager.

        Args:
            config_path: Full path to config.ini. If None, auto-detects:
                         - When frozen (PyInstaller): next to the .exe
                         - When running from source: project root
        """
        if config_path is None:
            import sys
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                base = os.path.dirname(sys.executable)
            else:
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(base, "config.ini")
        else:
            self.config_path = config_path

    def get_default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration dictionary.

        Returns:
            dict: Default config with all keys.
        """
        return {
            "default_save_path": "./output/",
            "auto_open": "false",
            "output_format": "mxl",
            "language": "zh",
            "theme": "light",
            "import_recent_dir": "",
            "recent_files": [],
        }

    def load_config(self) -> Dict[str, Any]:
        """
        Read config.ini and return the configuration dictionary.

        Returns:
            dict: Config dictionary. Returns defaults if the file does not exist.
        """
        if not os.path.exists(self.config_path):
            return self.get_default_config()

        config = configparser.ConfigParser()
        config.read(self.config_path, encoding="utf-8")

        result = {}
        defaults = self.get_default_config()

        if config.has_section("Preferences"):
            for key in defaults:
                if key == "recent_files":
                    raw = config.get("Preferences", key, fallback="")
                    try:
                        result[key] = json.loads(raw) if raw else []
                    except (json.JSONDecodeError, ValueError):
                        result[key] = []
                else:
                    result[key] = config.get("Preferences", key, fallback=defaults.get(key, ""))
        else:
            for key in defaults:
                result[key] = defaults.get(key, "")

        return result

    def save_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Save the configuration dictionary to config.ini.

        Args:
            config_dict: Config dictionary containing all keys.
        """
        config = configparser.ConfigParser()

        # Serialize recent_files as JSON
        recent_files = config_dict.get("recent_files", [])
        if isinstance(recent_files, list):
            recent_files_str = json.dumps(recent_files, ensure_ascii=False)
        else:
            recent_files_str = "[]"

        config["Preferences"] = {
            "default_save_path": config_dict.get("default_save_path", "./output/"),
            "auto_open": config_dict.get("auto_open", "false"),
            "output_format": config_dict.get("output_format", "mxl"),
            "language": config_dict.get("language", "zh"),
            "theme": config_dict.get("theme", "light"),
            "import_recent_dir": config_dict.get("import_recent_dir", ""),
            "recent_files": recent_files_str,
        }

        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            config.write(f)

    def add_recent_file(self, file_path: str) -> List[str]:
        """
        Add a file path to the recent files list (most recent first).

        Args:
            file_path: Path to the file to add.

        Returns:
            list: The updated recent files list.
        """
        config = self.load_config()
        recent = config.get("recent_files", [])

        # Remove duplicates and prepend
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)

        # Trim to max length
        recent = recent[:self.MAX_RECENT_FILES]

        config["recent_files"] = recent
        self.save_config(config)
        return recent

    def get_recent_files(self) -> List[str]:
        """
        Return the list of recently opened files.

        Returns:
            list: Recent file paths, most recent first.
        """
        config = self.load_config()
        return config.get("recent_files", [])
