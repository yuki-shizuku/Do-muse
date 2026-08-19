# Do Muse

A PyQt6 desktop application that converts JSON score data to MusicXML (.mxl) format, ready to open with **MuseScore Studio 4**.

[中文文档](#中文介绍)

---

## Features

- **JSON Editor** — Write or paste score data in JSON format with syntax highlighting
- **Schema Validation** — Validate note structure, pitch ranges, durations, dynamics, articulations, and more
- **Multi-format Export** — Export to `.mxl`, `.mid`, `.xml`, or `.ly` (LilyPond)
- **Multi-format Import** — Import from `.xml`, `.mxl`, `.mid` files back to JSON
- **Score Preview** — Render score to PNG/SVG via MuseScore CLI
- **Bilingual UI** — Switch between Chinese and English on the fly
- **Dark Mode** — Light and dark themes with persisted preference
- **Command-line Interface** — Batch convert JSON ↔ MusicXML/MIDI without GUI
- **Rich Musical Notation** — Full support for:
  - Ties, slurs (start/continue/stop), articulations, dynamics
  - Ornaments (trill, mordent, turn)
  - Grace notes, chords, arpeggios
  - Tremolo, glissando
  - Hairpin (crescendo/diminuendo)
  - Gradual tempo changes (accelerando/ritardando)
  - Subito dynamics
  - Expression markings
  - Navigation markers (D.C., D.S., Coda, Fine)
  - Repeats and voltas (1st/2nd endings)
  - Pedal markings (native music21 PedalMark)
  - Fermatas
  - Tuplets
  - Automatic clef assignment (treble/bass/alto) based on instrument

---

## Quick Start

### Prerequisites

- Python 3.10+
- [MuseScore Studio 4](https://musescore.org/) (to open exported files and enable score preview)

### Installation

```bash
# Clone the repository
git clone https://github.com/yuki-shizuku/Do-muse.git
cd Do-muse

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### GUI Usage

1. **Write JSON** — Paste or type JSON score data in the left panel
2. **Validate** — Click "Validate" to check syntax and score schema
3. **Export** — Click "Export" and choose format (.mxl, .mid, .xml, .ly)
4. **Preview** — Click "Preview Score" to render the score to an image
5. **Open** — Open the exported file in MuseScore Studio 4

### CLI Usage

```bash
# Export JSON to MXL
python main.py -i score.json -e output.mxl

# Import MusicXML to JSON
python main.py -i input.xml

# Export to MIDI format
python main.py -i score.json -e output.mid -f midi

# Import MIDI and export as LilyPond
python main.py -i input.mid -e output.ly -f ly
```

---

## JSON Format Quick Reference

```json
{
  "title": "My Piece",
  "composer": "Do Muse",
  "metadata": {
    "tempo_bpm": 120,
    "time_signature": "4/4",
    "key_signature": "C"
  },
  "tracks": [
    {
      "instrument": "Acoustic Grand Piano",
      "notes": [
        { "pitch": 60, "duration": "quarter", "velocity": 80 },
        { "pitch": 64, "duration": "quarter", "velocity": 80 },
        { "pitch": 67, "duration": "half", "velocity": 85, "fermata": true }
      ],
      "repeat_begin": true,
      "repeat_end": true
    }
  ]
}
```

See [JSON_Format_Specification.md](JSON_Format_Specification.md) for the complete specification.

---

## Project Structure

```
Do-muse/
├── main.py                      # Entry point (GUI + CLI)
├── requirements.txt             # Python dependencies
├── JSON_Format_Specification.md # JSON format specification
├── .gitignore
├── LICENSE
├── README.md
├── config.ini                   # User config (auto-created)
├── core/
│   ├── __init__.py
│   ├── config_manager.py        # Config file read/write
│   ├── format_importer.py       # MusicXML/MIDI import to JSON
│   ├── gm_mapping.py            # General MIDI instrument mapping
│   ├── i18n.py                  # Internationalization (zh/en)
│   ├── json_validator.py        # JSON schema validation
│   └── music_exporter.py        # music21 score builder & multi-format export
├── gui/
│   ├── __init__.py
│   ├── json_highlighter.py      # JSON syntax highlighter
│   ├── log_handler.py           # Log redirect to GUI console
│   ├── main_window.py           # Main window & UI logic
│   ├── templates.py             # Built-in score templates
│   └── workers.py               # Export/preview worker threads
├── resources/
│   ├── style.qss                # Light theme stylesheet
│   └── style_dark.qss           # Dark theme stylesheet
└── tests/
    ├── __init__.py
    ├── test_gm_mapping.py       # GM mapping tests
    ├── test_json_validator.py   # Validator tests
    └── test_music_exporter.py   # Exporter tests
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| GUI Framework | PyQt6 |
| Music Notation Engine | music21 |
| Output Formats | MusicXML (.mxl/.xml), MIDI (.mid), LilyPond (.ly) |
| Target Notation Software | MuseScore Studio 4 |

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

---

## License

[MIT](LICENSE)

---

## 中文介绍

**Do Muse** 是一个基于 PyQt6 的桌面端乐谱生成器，通过 JSON 中间语言描述乐谱数据，导出为 `.mxl` 等格式，可用 **MuseScore Studio 4** 打开。

### 快速开始

```bash
git clone https://github.com/yuki-shizuku/Do-muse.git
cd Do-muse
pip install -r requirements.txt
python main.py
```

### 命令行使用

```bash
# JSON 导出为 MXL
python main.py -i score.json -e output.mxl

# 导入 MusicXML 为 JSON
python main.py -i input.xml

# 导出为 MIDI 格式
python main.py -i score.json -e output.mid -f midi
```

### 功能

- JSON 编辑器：输入或粘贴乐谱 JSON 数据，支持语法高亮
- 格式校验：检查乐谱数据结构的完整性和合法性
- 多格式导出：支持 `.mxl`、`.mid`、`.xml`、`.ly` 格式
- 多格式导入：支持从 `.xml`、`.mxl`、`.mid` 文件导入
- 乐谱预览：通过 MuseScore CLI 渲染乐谱为图片
- 双语界面：支持中文/英文实时切换
- 暗色模式：浅色/暗色主题切换，自动保存偏好
- 命令行接口：无需 GUI 即可批量转换文件
- 丰富的乐谱标记：连音线（start/continue/stop）、演奏法、力度、装饰音、倚音、和弦、琶音、震音、滑音、渐强渐弱、渐快渐慢、突强突弱、表情术语、踏板标记（原生 PedalMark）、重复标记、Voltas、导航标记（D.C./D.S./Coda/Fine）等
- 自动谱号分配：根据乐器自动选择高音/低音/中音谱号

完整数据格式说明请参阅 [JSON_Format_Specification.md](JSON_Format_Specification.md)。
