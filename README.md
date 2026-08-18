# Do Muse

A PyQt6 desktop application that converts JSON score data to MusicXML (.mxl) format, ready to open with **MuseScore Studio 4**.

[中文文档](#中文介绍)

---

## Features

- **JSON Editor** — Write or paste score data in JSON format with syntax highlighting
- **Schema Validation** — Validate note structure, pitch ranges, durations, dynamics, articulations, and more
- **MXL Export** — Export to compressed MusicXML (.mxl) format
- **Bilingual UI** — Switch between Chinese and English on the fly
- **Rich Musical Notation** — Full support for:
  - Ties, slurs, articulations, dynamics
  - Ornaments (trill, mordent, turn)
  - Grace notes, chords, arpeggios
  - Tremolo, glissando
  - Hairpin (crescendo/diminuendo)
  - Gradual tempo changes (accelerando/ritardando)
  - Subito dynamics
  - Expression markings
  - Navigation markers (D.C., D.S., Coda, Fine)
  - Repeats and voltas
  - Pedal markings, fermatas

---

## Quick Start

### Prerequisites

- Python 3.10+
- [MuseScore Studio 4](https://musescore.org/) (to open exported .mxl files)

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

1. **Write JSON** — Paste or type JSON score data in the left panel
2. **Validate** — Click "Validate" to check syntax and score schema
3. **Export** — Click "Export MXL" to save as .mxl file
4. **Open** — Open the .mxl file in MuseScore Studio 4

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
├── main.py                      # Entry point
├── requirements.txt             # Python dependencies
├── JSON_Format_Specification.md # JSON format specification
├── .gitignore
├── LICENSE
├── README.md
├── config.ini                   # User config (auto-created)
├── core/
│   ├── __init__.py
│   ├── config_manager.py        # Config file read/write
│   ├── gm_mapping.py            # General MIDI instrument mapping
│   ├── i18n.py                  # Internationalization (zh/en)
│   ├── json_validator.py        # JSON schema validation
│   └── music_exporter.py        # music21 score builder & MXL export
├── gui/
│   ├── __init__.py
│   ├── log_handler.py           # Log redirect to GUI console
│   └── main_window.py           # Main window & UI logic
└── resources/
    └── style.qss                # Qt stylesheet
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| GUI Framework | PyQt6 |
| Music Notation Engine | music21 |
| Output Format | Compressed MusicXML (.mxl) |
| Target Notation Software | MuseScore Studio 4 |

---

## License

[MIT](LICENSE)

---

## 中文介绍

**Do Muse** 是一个基于 PyQt6 的桌面端乐谱生成器，通过 JSON 中间语言描述乐谱数据，导出为 `.mxl` 格式，可用 **MuseScore Studio 4** 打开。

### 快速开始

```bash
git clone https://github.com/yuki-shizuku/Do-muse.git
cd Do-muse
pip install -r requirements.txt
python main.py
```

### 功能

- JSON 编辑器：输入或粘贴乐谱 JSON 数据
- 格式校验：检查乐谱数据结构的完整性和合法性
- MXL 导出：生成压缩的 MusicXML 文件
- 双语界面：支持中文/英文实时切换
- 丰富的乐谱标记：连音线、演奏法、力度、装饰音、倚音、和弦、琶音、震音、滑音、渐强渐弱、渐快渐慢、突强突弱、表情术语等

完整数据格式说明请参阅 [JSON_Format_Specification.md](JSON_Format_Specification.md)。