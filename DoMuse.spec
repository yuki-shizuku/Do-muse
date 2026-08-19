# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Do Muse — standalone Windows executable.
Produces a single-file .exe with bundled resources (QSS stylesheets).
config.ini and output/ are created next to the .exe at runtime.
"""

import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('resources/style.qss', 'resources'),
        ('resources/style_dark.qss', 'resources'),
    ],
    hiddenimports=[
        'music21.musicxml.m21ToXml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
