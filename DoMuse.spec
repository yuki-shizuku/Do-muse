# -*- mode: python ; coding: utf-8 -*-
# Do Muse PyInstaller spec — onefile GUI build with icon.
# Output: windows/DoMuse.exe (run: pyinstaller DoMuse.spec --distpath windows)

import os
import sys

# 项目根目录
root_dir = os.getcwd()

a = Analysis(
    ['main.py'],
    pathex=[root_dir],
    binaries=[],
    datas=[
        # 包含资源文件
        (os.path.join(root_dir, 'resources', 'style.qss'), 'resources'),
        (os.path.join(root_dir, 'resources', 'style_dark.qss'), 'resources'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'music21',
        'music21.stream',
        'music21.note',
        'music21.chord',
        'music21.key',
        'music21.meter',
        'music21.tempo',
        'music21.clef',
        'music21.instrument',
        'music21.dynamics',
        'music21.expressions',
        'music21.bar',
        'music21.tie',
        'music21.articulations',
        'music21.volume',
        'music21.spanner',
        'music21.beam',
        'music21.layout',
        'music21.repeat',
        'music21.roman',
        'music21.harmony',
        'music21.voiceLeading',
        'music21.midi',
        'music21.musicxml',
        'music21.converter',
        'music21.midi.realtime',
        'music21.midi.translate',
        'music21.environment',
        'music21.derivation',
        'music21.sites',
        'music21.common',
        'music21.prebase',
        'music21.base',
    ],
    hookspath=[],
    runtime_hooks=[os.path.join(root_dir, 'runtime_hook.py')],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'cv2',
        'PIL',
        'notebook',
        'jupyter',
        'IPython',
        'pandas',
        'sympy',
        'networkx',
        'nltk',
        'sqlalchemy',
        'django',
        'flask',
        'bottle',
        'tornado',
        'zmq',
        'numpy',
        'turtle',
        'turtledemo',
        'lib2to3',
        'distutils',
        'setuptools',
        'pydoc',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DoMuse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.join(root_dir, 'domuse.ico'),
)