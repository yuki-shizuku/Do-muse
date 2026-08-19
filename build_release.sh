#!/bin/bash

# Do Muse 构建脚本
# 用于生成GitHub Release的DoMuse_windows.zip

set -e

echo "=== Do Muse 构建脚本 ==="

# 设置变量
PROJECT_NAME="DoMuse"
RELEASE_NAME="DoMuse_windows.zip"
DIST_DIR="dist"
RELEASE_DIR="release"
BUILD_LOG="build.log"

# 清理之前的构建
echo "清理之前的构建文件..."
rm -rf "$DIST_DIR" "$RELEASE_DIR" "$BUILD_LOG"
mkdir -p "$DIST_DIR" "$RELEASE_DIR"

# 检查Python环境
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装。请先安装 uv。"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    uv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "安装依赖..."
uv pip install -r requirements.txt

# 生成图标文件（如果不存在）
echo "确保图标文件存在..."
python create_default_icon.py

# 执行PyInstaller打包
echo "执行PyInstaller打包..."
uv run pyinstaller DoMuse.spec >> "$BUILD_LOG" 2>&1

# 检查构建是否成功
if [ ! -f "$DIST_DIR/$PROJECT_NAME.exe" ]; then
    echo "错误: 构建失败，请检查 $BUILD_LOG"
    exit 1
fi

# 创建Release文件夹
echo "创建Release文件夹..."
cp "$DIST_DIR/$PROJECT_NAME.exe" "$RELEASE_DIR/"
cp "$DIST_DIR/domuse.ico" "$RELEASE_DIR/" 2>/dev/null || echo "警告: 图标文件未找到"

# 复制必要的文档
echo "复制文档文件..."
cp README.md "$RELEASE_DIR/"
cp LICENSE "$RELEASE_DIR/"
cp windows/JSON_Format_Specification.md "$RELEASE_DIR/" 2>/dev/null || echo "警告: JSON格式说明未找到"

# 创建使用说明
cat > "$RELEASE_DIR/README.txt" << EOF
Do Muse - 乐谱生成器

使用方法：
1. 双击 DoMuse.exe 启动程序
2. 或者命令行使用：
   - GUI模式: DoMuse.exe
   - CLI模式: DoMuse.exe -i input.json -e output.mxl

依赖：
- 需要安装 MuseScore Studio 4 来打开 .mxl 文件
- 程序已包含所有必要的Python依赖

项目地址：https://github.com/your-username/Do-Muse

EOF

# 创建zip文件
echo "创建Release zip文件..."
cd "$RELEASE_DIR"
zip -r "../$RELEASE_NAME" ./*
cd ..

# 检查zip文件是否创建成功
if [ -f "$RELEASE_NAME" ]; then
    echo "✅ 构建成功！"
    echo "Release文件: $RELEASE_NAME"
    echo "文件大小: $(du -h "$RELEASE_NAME" | cut -f1)"
    echo "SHA256: $(sha256sum "$RELEASE_NAME" | cut -d' ' -f1)"
else
    echo "❌ 构建失败：无法创建zip文件"
    exit 1
fi

# 显示Release内容
echo ""
echo "=== Release 内容 ==="
unzip -l "$RELEASE_NAME"

# 清理临时文件
echo ""
echo "清理临时文件..."
rm -rf "$RELEASE_DIR"

echo ""
echo "=== 构建完成 ==="
echo "请将以下文件推送到GitHub并创建Release："
echo "1. $RELEASE_NAME (用于Release)"
echo "2. 完整的项目源代码"
echo "3. Tag标签: DoMuse_windows.zip"