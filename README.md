# Do Muse

A PyQt6 desktop application that converts JSON score data to MusicXML (.mxl) format, ready to open with **MuseScore Studio 4**.

[中文文档](#中文介绍)

---

## Features

- **JSON Editor** — Write or paste score data in JSON format with syntax highlighting
- **Schema Validation** — Validate note structure, pitch ranges, durations, dynamics, articulations, and more
- **Multi-Format Export** — Export to `.mxl` (compressed MusicXML), `.mid` (MIDI), `.xml` (MusicXML), or `.ly` (LilyPond)
- **Multi-Format Import** — Import from `.xml`/`.mxl` (MusicXML) or `.mid`/`.midi` (MIDI) back to JSON
- **Score Preview** — Generate a PNG preview of the score via MuseScore CLI
- **CLI Mode** — Batch convert files without launching the GUI
- **Bilingual UI** — Switch between Chinese and English on the fly
- **Light/Dark Theme** — Toggle between light and dark color schemes
- **Templates & Recent Files** — Quick-start templates and recent file tracking
- **Rich Musical Notation** — Full support for:
  - Ties, slurs (start/continue/stop), articulations, dynamics
  - Ornaments (trill, mordent, turn, inverted mordent, inverted turn)
  - Grace notes, chords, arpeggios
  - Tremolo, glissando
  - Hairpin (crescendo/diminuendo)
  - Gradual tempo changes (accelerando/ritardando)
  - Subito dynamics
  - Expression markings
  - Navigation markers (D.C., D.S., Coda, Fine)
  - Repeats and voltas (1st/2nd endings)
  - Native pedal markings (PedalMark)
  - Fermatas
  - Intelligent clef assignment (treble/bass/alto) based on instrument
- **Macro System** — Define reusable note blocks in `"macros"` and reference them via `{"ref": "name"}` to eliminate repetition

---

## Quick Start

### Prerequisites

- Python 3.10+
- [MuseScore Studio 4](https://musescore.org/) (to open exported `.mxl` files and enable preview)

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

### Usage

#### GUI Mode

1. **Write JSON** — Paste or type JSON score data in the left panel
2. **Validate** — Click "Validate" to check syntax and score schema
3. **Export** — Click "Export" and choose format (.mxl, .mid, .xml, .ly)
4. **Preview** — Use "View → Preview Score" to see a rendered preview
5. **Open** — Open the exported file in MuseScore Studio 4

#### CLI Mode

```bash
# Export JSON to MXL
python main.py -i score.json -e output.mxl

# Import MusicXML to JSON
python main.py -i input.xml

# Export JSON to MIDI
python main.py -i score.json -e output.mid -f midi

# Import MIDI, export to LilyPond
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
  "macros": {
    "chord": [
      { "chord": [60, 64, 67], "duration": "half", "velocity": 80 }
    ]
  },
  "tracks": [
    {
      "instrument": "Acoustic Grand Piano",
      "notes": [
        { "ref": "chord" },
        { "pitch": 64, "duration": "quarter", "velocity": 80 },
        { "pitch": 67, "duration": "half", "velocity": 85, "fermata": true }
      ]
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
│   ├── config_manager.py        # Config file read/write (with theme support)
│   ├── gm_mapping.py            # General MIDI instrument mapping (128 instruments)
│   ├── i18n.py                  # Internationalization (zh/en)
│   ├── json_validator.py        # JSON schema validation
│   ├── music_exporter.py        # music21 score builder & multi-format export
│   └── format_importer.py       # MusicXML/MIDI importer
├── gui/
│   ├── __init__.py
│   ├── log_handler.py           # Log redirect to GUI console
│   ├── json_highlighter.py      # JSON syntax highlighter
│   ├── main_window.py           # Main window & UI logic
│   ├── workers.py               # Export/Preview worker threads
│   └── templates.py             # JSON score templates
├── resources/
│   ├── style.qss                # Light theme stylesheet
│   └── style_dark.qss           # Dark theme stylesheet
├── test_all_features.json       # Comprehensive feature demo JSON
└── output/                      # Export output directory (auto-created)
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| GUI Framework | PyQt6 |
| Music Notation Engine | music21 |
| Output Formats | Compressed MusicXML (.mxl), MIDI (.mid), MusicXML (.xml), LilyPond (.ly) |
| Target Notation Software | MuseScore Studio 4 |

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

### 功能

- JSON 编辑器：输入或粘贴乐谱 JSON 数据，支持语法高亮
- 格式校验：检查乐谱数据结构的完整性和合法性
- 多格式导出：支持 `.mxl`、`.mid`、`.xml`、`.ly` 格式
- 多格式导入：支持从 MusicXML 和 MIDI 文件导入回 JSON
- 乐谱预览：通过 MuseScore CLI 生成 PNG 预览图
- 命令行模式：支持无 GUI 批量转换
- 双语界面：支持中文/英文实时切换
- 浅色/暗色主题：一键切换界面配色
- 模板与最近文件：提供快速起始模板和最近文件记录
- 丰富的乐谱标记：连音线、演奏法、力度、装饰音、倚音、和弦、琶音、震音、滑音、渐强渐弱、渐快渐慢、突强突弱、表情术语、踏板标记、延音线、重复标记、Volta 括号等
- **宏系统**：在 JSON 顶层定义可复用的音符块，通过 `{"ref": "name"}` 引用，消除重复
- 智能谱号分配：根据乐器自动选择高音/低音/中音谱号

### 命令行用法

```bash
# 导出 JSON 为 MXL
python main.py -i score.json -e output.mxl

# 导入 MusicXML 为 JSON
python main.py -i input.xml

# 导出 JSON 为 MIDI
python main.py -i score.json -e output.mid -f midi
```

完整数据格式说明请参阅 [JSON_Format_Specification.md](JSON_Format_Specification.md)。
