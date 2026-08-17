"""
Configuration management — reads and writes config.ini using configparser
"""

import configparser
import os
from typing import Dict, Any


class ConfigManager:
    """Config file manager responsible for reading/writing config.ini."""

    def __init__(self, config_path: str = None):
        """
        Initialize the config manager.

        Args:
            config_path: Full path to config.ini. Defaults to config.ini under the project root.
        """
        if config_path is None:
            self.config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config.ini",
            )
        else:
            self.config_path = config_path

    def get_default_config(self) -> Dict[str, str]:
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
        }

    def load_config(self) -> Dict[str, str]:
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
                result[key] = config.get("Preferences", key, fallback=defaults.get(key, ""))
        else:
            for key in defaults:
                result[key] = defaults.get(key, "")

        return result

    def save_config(self, config_dict: Dict[str, str]) -> None:
        """
        Save the configuration dictionary to config.ini.

        Args:
            config_dict: Config dictionary containing all keys.
        """
        config = configparser.ConfigParser()

        config["Preferences"] = {
            "default_save_path": config_dict.get("default_save_path", "./output/"),
            "auto_open": config_dict.get("auto_open", "false"),
            "output_format": config_dict.get("output_format", "mxl"),
            "language": config_dict.get("language", "zh"),
        }

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            config.write(f)