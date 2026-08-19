# GitHub Release 策略

## 📋 推送到GitHub的文件清单

### 🔴 必须推送的源代码文件

#### 核心程序文件
- `main.py` - 程序入口点
- `requirements.txt` - Python依赖列表
- `DoMuse.spec` - PyInstaller打包配置
- `create_default_icon.py` - 图标生成脚本

#### 源代码模块
- `core/` - 核心功能模块
  - `__init__.py`
  - `config_manager.py`
  - `format_importer.py`
  - `gm_mapping.py`
  - `i18n.py`
  - `json_validator.py`
  - `music_exporter.py`
- `gui/` - 图形界面模块
  - `__init__.py`
  - `main_window.py`
  - `json_highlighter.py`
  - `log_handler.py`
  - `templates.py`
  - `workers.py`

#### 资源文件
- `resources/` - 界面资源
  - `style.qss` - 浅色主题
  - `style_dark.qss` - 深色主题

#### 文档文件
- `README.md` - 项目说明文档
- `JSON_Format_Specification.md` - JSON格式规范
- `LICENSE` - MIT许可证
- `.gitattributes` - Git属性配置
- `.gitignore` - Git忽略文件

#### 构建脚本
- `build_release.bat` - Windows构建脚本
- `build_release.sh` - Linux/Mac构建脚本

#### Windows特定文件
- `windows/` - Windows相关文件
  - `domuse.ico` - 程序图标
  - `JSON_Format_Specification.md` - Windows版本的格式说明

#### 测试文件
- `tests/` - 测试模块
  - `conftest.py`
  - `test_exporter.py`
  - `test_importer.py`
  - `test_validator.py`

### 🟡 可选推送的文件

- `多声部支持实施方案.md` - 多声部支持方案
- `windows/` 文件夹中的其他说明文档

### 🔵 不需要推送的文件

- `dist/` - 构建输出目录（包含exe文件）
- `build/` - PyInstaller构建临时文件
- `.venv/` - 虚拟环境目录
- `config.ini` - 用户配置文件（运行时生成）
- `output/` - 程序输出目录
- `*.log` - 日志文件
- `Thumbs.db` - 系统缩略图文件
- `.DS_Store` - macOS系统文件

---

## 🚀 GitHub Release 创建流程

### 第一步：推送源代码

1. **提交所有源代码文件**
   ```bash
   git add .
   git commit -m "feat: 添加完整的Do Muse源代码和构建脚本"
   git push origin main
   ```

2. **确保.gitignore正确配置**
   - 已排除 `dist/`, `build/`, `.venv/`, `config.ini` 等

### 第二步：构建Release包

1. **在本地运行构建脚本**
   ```bash
   # Windows用户
   build_release.bat
   
   # Linux/Mac用户
   ./build_release.sh
   ```

2. **验证生成的文件**
   - 确认生成了 `DoMuse_windows.zip`
   - 检查zip文件内容完整

### 第三步：创建GitHub Release

1. **访问GitHub仓库页面**
   - 点击 "Releases" 标签
   - 点击 "Create a new release"

2. **填写Release信息**
   - **Tag版本**: `DoMuse_windows.zip` (重要！)
   - **Release标题**: `Do Muse Windows Release v1.0.0`
   - **描述**: 
     ```
     ## Do Muse Windows Release v1.0.0
     
     ### 新功能
     - 初始版本发布
     - 支持JSON乐谱编辑和验证
     - 多格式导出（MXL、MIDI、XML、LY等）
     - 双语界面支持
     - 浅色/深色主题
     
     ### 包含文件
     - DoMuse.exe - Windows可执行程序
     - domuse.ico - 程序图标
     - README.txt - 使用说明
     - README.md - 详细文档
     - LICENSE - MIT许可证
     - JSON_Format_Specification.md - JSON格式规范
     
     ### 使用方法
     1. 下载并解压 DoMuse_windows.zip
     2. 双击 DoMuse.exe 启动程序
     3. 详细使用说明请参阅 README.txt
     
     ### 系统要求
     - Windows 10/11
     - Python 3.10+ (已包含在exe中)
     - MuseScore Studio 4 (可选，用于打开MXL文件)
     ```

3. **上传Release文件**
   - 点击 "Choose files"
   - 选择构建生成的 `DoMuse_windows.zip`
   - 点击 "Upload file"

4. **发布Release**
   - 点击 "Publish release"
   - 系统自动创建Tag `DoMuse_windows.zip`

---

## 📦 Release包内容说明

### DoMuse_windows.zip 包含：

#### 核心程序
- `DoMuse.exe` - 主程序（67MB左右，包含所有依赖）
- `domuse.ico` - 程序图标

#### 文档文件
- `README.txt` - 简要使用说明
- `README.md` - 完整项目文档
- `LICENSE` - MIT许可证
- `JSON_Format_Specification.md` - JSON数据格式详细说明

#### 特点
- ✅ **独立运行** - 无需安装Python环境
- ✅ **包含所有依赖** - music21、PyQt6等已打包
- ✅ **双语言支持** - 中文/英文界面切换
- ✅ **主题支持** - 浅色/深色主题
- ✅ **多格式支持** - MXL、MIDI、XML、LY导出

---

## 🔧 版本管理策略

### 版本号规范
使用语义化版本号：`主版本号.次版本号.修订号`

- **v1.0.0** - 初始版本
- **v1.1.0** - 新增功能
- **v1.0.1** - 修复bug
- **v2.0.0** - 重大更新（不兼容）

### Release频率
- **重大版本**：每3-6个月
- **功能版本**：每月或每两个月
- **修复版本**：按需发布

### Tag管理
- 每个Release对应一个Tag
- Tag格式：`DoMuse_windows.zip`
- 不重复使用相同的Tag

---

## ⚠️ 注意事项

1. **文件大小**：exe文件约67MB，确保GitHub有足够存储空间
2. **病毒扫描**：建议对exe文件进行病毒扫描
3. **测试验证**：发布前在不同Windows版本上测试
4. **文档更新**：确保Release描述与实际功能一致
5. **备份策略**：重要Release建议在多个地方备份

---

## 🔄 更新流程

### 日常更新
1. 修改代码
2. 更新文档
3. 提交代码
4. 重新构建Release包
5. 更新GitHub Release

### 紧急修复
1. 快速修复bug
2. 提交代码并标记修复
3. 构建新的Release包
4. 创建新的Release，使用新的版本号