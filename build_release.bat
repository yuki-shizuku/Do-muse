@echo off
REM Do Muse 构建脚本 (Windows版本)
REM 用于生成GitHub Release的DoMuse_windows.zip

echo === Do Muse 构建脚本 ===

set PROJECT_NAME=DoMuse
set RELEASE_NAME=DoMuse_windows.zip
set DIST_DIR=dist
set RELEASE_DIR=release
set BUILD_LOG=build.log

REM 清理之前的构建
echo 清理之前的构建文件...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
if exist "%BUILD_LOG%" del "%BUILD_LOG%"
mkdir "%DIST_DIR%" 2>nul
mkdir "%RELEASE_DIR%" 2>nul

REM 检查uv环境
uv --version >nul 2>&1
if errorlevel 1 (
    echo 错误: uv 未安装。请先安装 uv。
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
if not exist ".venv" (
    echo 创建虚拟环境...
    uv venv
)

REM 安装依赖
echo 安装依赖...
uv pip install -r requirements.txt

REM 生成图标文件（如果不存在）
echo 确保图标文件存在...
python create_default_icon.py

REM 执行PyInstaller打包
echo 执行PyInstaller打包...
uv run pyinstaller DoMuse.spec

REM 检查构建是否成功
if not exist "%DIST_DIR%\%PROJECT_NAME%.exe" (
    echo 错误: 构建失败，请检查 %BUILD_LOG%
    pause
    exit /b 1
)

REM 创建Release文件夹
echo 创建Release文件夹...
copy "%DIST_DIR%\%PROJECT_NAME%.exe" "%RELEASE_DIR%\"
if exist "%DIST_DIR%\domuse.ico" (
    copy "%DIST_DIR%\domuse.ico" "%RELEASE_DIR%\"
) else (
    echo 警告: 图标文件未找到
)

REM 复制必要的文档
echo 复制文档文件...
copy README.md "%RELEASE_DIR%\"
copy LICENSE "%RELEASE_DIR%\"
if exist "windows\JSON_Format_Specification.md" (
    copy "windows\JSON_Format_Specification.md" "%RELEASE_DIR%\"
) else (
    echo 警告: JSON格式说明未找到
)

REM 创建使用说明
(
echo Do Muse - 乐谱生成器
echo.
echo 使用方法：
echo 1. 双击 DoMuse.exe 启动程序
echo 2. 或者命令行使用：
echo    - GUI模式: DoMuse.exe
echo    - CLI模式: DoMuse.exe -i input.json -e output.mxl
echo.
echo 依赖：
echo - 需要安装 MuseScore Studio 4 来打开 .mxl 文件
echo - 程序已包含所有必要的Python依赖
echo.
echo 项目地址：https://github.com/your-username/Do-Muse
) > "%RELEASE_DIR%\README.txt"

REM 创建zip文件
echo 创建Release zip文件...
cd "%RELEASE_DIR%"
powershell -Command "Compress-Archive -Path * -DestinationPath '..\%RELEASE_NAME%'"
cd ..

REM 检查zip文件是否创建成功
if exist "%RELEASE_NAME%" (
    echo ✅ 构建成功！
    echo Release文件: %RELEASE_NAME%
    for %%F in ("%RELEASE_NAME%") do echo 文件大小: %%~zF 字节
) else (
    echo ❌ 构建失败：无法创建zip文件
    pause
    exit /b 1
)

REM 显示Release内容
echo.
echo === Release 内容 ===
powershell -Command "Expand-Archive -Path '%RELEASE_NAME%' -DestinationPath 'temp_extract' -Force"
dir /b "temp_extract\"
rmdir /s /q "temp_extract"

REM 清理临时文件
echo.
echo 清理临时文件...
rmdir /s /q "%RELEASE_DIR%"

echo.
echo === 构建完成 ===
echo 请将以下文件推送到GitHub并创建Release：
echo 1. %RELEASE_NAME% (用于Release)
echo 2. 完整的项目源代码
echo 3. Tag标签: DoMuse_windows.zip

pause