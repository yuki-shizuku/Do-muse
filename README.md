# Do Muse

A PyQt6 desktop application that converts JSON score data to MusicXML (.mxl) format, ready to open with **MuseScore Studio 4**.

[中文文档](#中文介绍)

---

## Features

- **JSON Editor** — Write or paste score data in JSON format with syntax highlighting
- **Schema Validation** — Validate note structure, pitch ranges, durations, dynamics, articulations, and more
- **Multi-Format Export** — Export to `.mxl` (compressed MusicXML), `.mid` (MIDI), `.xml` (MusicXML), `.ly` (LilyPond), `.mp3`, `.wav`, `.flac`, or `.ogg` (audio via MuseScore CLI)
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
3. **Export** — Click "Export" and choose format (.mxl, .mid, .xml, .ly, .mp3, .wav, .flac, .ogg)
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

# Export JSON to MP3 audio
python main.py -i score.json -e output.mp3 -f mp3
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
| Output Formats | Compressed MusicXML (.mxl), MIDI (.mid), MusicXML (.xml), LilyPond (.ly), MP3 (.mp3), WAV (.wav), FLAC (.flac), OGG (.ogg) |
| Audio Synthesis | MuseScore Studio 4 CLI |
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

---

## 🏗️ 构建和发布

### 构建Windows可执行文件

#### 方法一：使用构建脚本（推荐）

**Windows用户：**
```bash
# 运行构建脚本
build_release.bat
```

**Linux/Mac用户：**
```bash
# 运行构建脚本
chmod +x build_release.sh
./build_release.sh
```

#### 方法二：手动构建

```bash
# 1. 创建虚拟环境
uv venv

# 2. 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. 安装依赖
uv pip install -r requirements.txt

# 4. 生成图标文件（如果需要）
python create_default_icon.py

# 5. 执行打包
uv run pyinstaller DoMuse.spec
```

### GitHub Release

#### 创建Release
1. 推送代码到GitHub仓库
2. 在GitHub仓库页面点击 "Releases"
3. 点击 "Create a new release"
4. **Tag标签**: `DoMuse_windows.zip`
5. **标题**: `Do Muse Windows Release v{版本号}`
6. **描述**: 更新新版本特性和修复
7. 点击 "Choose files" 上传 `build_release.bat` 生成的 `DoMuse_windows.zip`

#### Release内容
Release包包含：
- `DoMuse.exe` - 主程序
- `domuse.ico` - 程序图标
- `README.txt` - 使用说明
- `README.md` - 项目文档
- `LICENSE` - 许可证文件
- `JSON_Format_Specification.md` - JSON格式规范

### 版本管理

#### 版本号格式
使用语义化版本号：`主版本号.次版本号.修订号`
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

#### 发布流程
1. 更新 `README.md` 中的版本信息
2. 运行构建脚本生成Release包
3. 创建GitHub Release并上传 `DoMuse_windows.zip`
4. 设置Tag为 `DoMuse_windows.zip`
5. 发布Release并通知用户

---

## 📁 项目结构

```
Do-Muse/
├── main.py                    # 程序入口
├── requirements.txt           # Python依赖
├── DoMuse.spec               # PyInstaller配置
├── create_default_icon.py     # 图标生成脚本
├── build_release.bat/.sh     # 构建脚本
├── core/                    # 核心模块
│   ├── config_manager.py     # 配置管理
│   ├── format_importer.py    # 格式导入
│   ├── gm_mapping.py        # MIDI乐器映射
│   ├── i18n.py              # 国际化
│   ├── json_validator.py    # JSON验证
│   └── music_exporter.py    # 音乐导出
├── gui/                     # GUI模块
│   ├── main_window.py       # 主窗口
│   ├── json_highlighter.py  # JSON语法高亮
│   ├── log_handler.py       # 日志处理
│   ├── templates.py         # 模板系统
│   └── workers.py           # 工作线程
├── resources/               # 资源文件
│   ├── style.qss           # 浅色主题
│   └── style_dark.qss      # 深色主题
├── windows/                 # Windows相关文件
│   ├── domuse.ico          # 程序图标
│   └── JSON_Format_Specification.md
├── tests/                   # 测试文件
├── dist/                   # 构建输出（不提交）
└── .venv/                  # 虚拟环境（不提交）
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
1. Fork项目
2. 克隆到本地：`git clone https://github.com/your-username/Do-Muse.git`
3. 创建虚拟环境：`uv venv`
4. 安装依赖：`uv pip install -r requirements.txt`
5. 运行开发：`python main.py`

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式化
- refactor: 代码重构
- test: 测试相关
- chore: 构建或辅助工具的变动

---

## 📄 许可证

[MIT](LICENSE)

---

## 📞 联系方式

- 项目地址：https://github.com/your-username/Do-Muse
- 问题反馈：[GitHub Issues](https://github.com/your-username/Do-Muse/issues)
- 邮箱：your-email@example.com
