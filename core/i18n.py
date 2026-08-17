"""
Internationalization (i18n) support for Do Muse — manages Chinese/English translations
"""


class LanguageManager:
    """Singleton-like language manager that provides translations for UI strings."""

    _current_lang = "zh"
    _strings: dict[str, dict[str, str]] = {
        # ── Window ──
        "window_title": {"zh": "Do Muse - 乐谱生成器", "en": "Do Muse - Score Generator"},
        # ── File menu ──
        "menu_file": {"zh": "文件", "en": "File"},
        "menu_import": {"zh": "导入", "en": "Import"},
        "menu_import_musicxml": {"zh": "MusicXML 文件...", "en": "MusicXML File..."},
        "menu_import_midi": {"zh": "MIDI 文件...", "en": "MIDI File..."},
        "menu_load_json": {"zh": "加载 JSON", "en": "Load JSON"},
        "menu_save_json": {"zh": "保存 JSON", "en": "Save JSON"},
        "menu_export": {"zh": "导出为", "en": "Export As"},
        "menu_export_mxl": {"zh": "MXL (压缩 MusicXML)", "en": "MXL (Compressed MusicXML)"},
        "menu_export_midi": {"zh": "MIDI", "en": "MIDI"},
        "menu_export_xml": {"zh": "MusicXML", "en": "MusicXML"},
        "menu_export_ly": {"zh": "LilyPond", "en": "LilyPond"},
        "menu_exit": {"zh": "退出", "en": "Exit"},
        # ── Language menu ──
        "menu_language": {"zh": "语言", "en": "Language"},
        "menu_lang_zh": {"zh": "中文", "en": "Chinese"},
        "menu_lang_en": {"zh": "英文", "en": "English"},
        # ── Buttons ──
        "btn_load_json": {"zh": "加载 JSON", "en": "Load JSON"},
        "btn_save_json": {"zh": "保存 JSON", "en": "Save JSON"},
        "btn_validate": {"zh": "校验格式", "en": "Validate"},
        "btn_import": {"zh": "导入文件", "en": "Import"},
        "btn_export": {"zh": "导出乐谱", "en": "Export"},
        # ── Placeholders ──
        "json_placeholder": {
            "zh": "在此输入或粘贴 JSON 格式的乐谱数据...",
            "en": "Paste JSON score data here...",
        },
        "log_placeholder": {"zh": "日志输出区域...", "en": "Log output..."},
        # ── Message box titles ──
        "msg_validation_result": {"zh": "校验结果", "en": "Validation Result"},
        "msg_load_failed": {"zh": "加载失败", "en": "Load Failed"},
        "msg_save_failed": {"zh": "保存失败", "en": "Save Failed"},
        "msg_export_hint": {"zh": "导出提示", "en": "Export"},
        "msg_export_failed": {"zh": "导出失败", "en": "Export Failed"},
        "msg_export_success": {"zh": "导出成功", "en": "Export Successful"},
        # ── Message box content ──
        "msg_empty_json_validate": {
            "zh": "JSON 内容为空，请输入内容后再校验。",
            "en": "JSON content is empty. Please enter content before validating.",
        },
        "msg_json_format_error": {
            "zh": "JSON 格式错误：\n{}",
            "en": "JSON format error:\n{}",
        },
        "msg_json_valid": {
            "zh": "JSON 格式正确，乐谱数据合法！",
            "en": "JSON format is valid and score data is correct!",
        },
        "msg_validation_failed": {
            "zh": "乐谱数据校验失败：\n{}",
            "en": "Score data validation failed:\n{}",
        },
        "msg_cannot_load": {
            "zh": "无法加载文件：{}",
            "en": "Cannot load file: {}",
        },
        "msg_cannot_save": {
            "zh": "无法保存文件：{}",
            "en": "Cannot save file: {}",
        },
        "msg_empty_json_export": {
            "zh": "JSON 内容为空，请输入内容后再导出。",
            "en": "JSON content is empty. Please enter content before exporting.",
        },
        "msg_export_success_content": {
            "zh": "乐谱已导出至：\n{}\n\n请使用 MuseScore Studio 4 打开该文件。",
            "en": "Score exported to:\n{}\n\nOpen with MuseScore Studio 4.",
        },
        "msg_export_error": {
            "zh": "导出过程中发生错误：\n{}",
            "en": "Error during export:\n{}",
        },
        # ── Import messages ──
        "msg_import_hint": {"zh": "导入提示", "en": "Import"},
        "msg_import_failed": {"zh": "导入失败", "en": "Import Failed"},
        "msg_import_success": {"zh": "导入成功", "en": "Import Successful"},
        "msg_import_success_content": {
            "zh": "已成功导入文件：\n{}\n\n乐谱数据已加载到编辑器中。",
            "en": "Successfully imported:\n{}\n\nScore data loaded into the editor.",
        },
        "msg_import_error": {
            "zh": "导入过程中发生错误：\n{}",
            "en": "Error during import:\n{}",
        },
        # ── Format selection ──
        "msg_select_export_format": {"zh": "选择导出格式", "en": "Select Export Format"},
        "msg_format_mxl": {"zh": "MXL (压缩 MusicXML)", "en": "MXL (Compressed MusicXML)"},
        "msg_format_midi": {"zh": "MIDI", "en": "MIDI"},
        "msg_format_xml": {"zh": "MusicXML", "en": "MusicXML"},
        "msg_format_ly": {"zh": "LilyPond", "en": "LilyPond"},
        # ── File dialog ──
        "fd_load_json": {"zh": "加载 JSON 文件", "en": "Load JSON File"},
        "fd_save_json": {"zh": "保存 JSON 文件", "en": "Save JSON File"},
        "fd_export_mxl": {"zh": "导出 MXL 文件", "en": "Export MXL File"},
        "fd_json_filter": {
            "zh": "JSON 文件 (*.json);;所有文件 (*)",
            "en": "JSON Files (*.json);;All Files (*)",
        },
        "fd_mxl_filter": {
            "zh": "MusicXML 文件 (*.mxl);;所有文件 (*)",
            "en": "MusicXML Files (*.mxl);;All Files (*)",
        },
        "fd_import_all_filter": {
            "zh": "支持的文件 (*.xml *.mxl *.mid *.midi *.json);;MusicXML 文件 (*.xml *.mxl);;MIDI 文件 (*.mid *.midi);;JSON 文件 (*.json);;所有文件 (*)",
            "en": "Supported Files (*.xml *.mxl *.mid *.midi *.json);;MusicXML Files (*.xml *.mxl);;MIDI Files (*.mid *.midi);;JSON Files (*.json);;All Files (*)",
        },
        "fd_export_filter": {
            "zh": "MXL 文件 (*.mxl);;MIDI 文件 (*.mid);;MusicXML 文件 (*.xml);;LilyPond 文件 (*.ly);;所有文件 (*)",
            "en": "MXL Files (*.mxl);;MIDI Files (*.mid);;MusicXML Files (*.xml);;LilyPond Files (*.ly);;All Files (*)",
        },
    }

    @classmethod
    def set_language(cls, lang: str) -> None:
        """
        Set the current language.

        Args:
            lang: Language code, either "zh" or "en".
        """
        if lang in ("zh", "en"):
            cls._current_lang = lang

    @classmethod
    def get_language(cls) -> str:
        """
        Get the current language code.

        Returns:
            str: "zh" or "en".
        """
        return cls._current_lang

    @classmethod
    def tr(cls, key: str, *args) -> str:
        """
        Translate a UI string identified by key.

        Args:
            key: The translation key.
            *args: Optional format arguments to interpolate into the string.

        Returns:
            str: The translated string, or the key itself if not found.
        """
        entry = cls._strings.get(key)
        if entry is None:
            return key
        text = entry.get(cls._current_lang, key)
        if args:
            text = text.format(*args)
        return text