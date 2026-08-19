# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Do Muse — standalone Windows executable.
Produces a single-file .exe with bundled resources (QSS stylesheets).
config.ini and output/ are created next to the .exe at runtime.

IMPORTANT: Do NOT exclude numpy/scipy/matplotlib — music21 imports them
lazily and excluding them causes 'NoneType has no attribute write' errors
in frozen mode. All music21 submodules are listed as hiddenimports to
ensure the format registry and converter pipeline work correctly.
"""

import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)

# Collect every music21 submodule so PyInstaller bundles them all.
# Without this, music21's format registry is incomplete in frozen mode
# and score.write() fails with cryptic NoneType errors.
import pkgutil
import music21
_m21_hidden = []
for _imp, _mod, _ispkg in pkgutil.walk_packages(music21.__path__, prefix='music21.'):
    _m21_hidden.append(_mod)

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('resources/style.qss', 'resources'),
        ('resources/style_dark.qss', 'resources'),
    ],
    hiddenimports=_m21_hidden + [
        'music21',
        'music21.musicxml',
        'music21.musicxml.m21ToXml',
        'music21.musicxml.helpers',
        'music21.musicxml.archiveTools',
        'music21.musicxml.xmlObjects',
        'music21.musicxml.xmlToM21',
        'music21.converter',
        'music21.converter.subConverters',
        'music21.converter.museScore',
        'music21.midi',
        'music21.midi.translate',
        'music21.midi.base',
        'music21.lily',
        'music21.lily.translate',
        'music21.lily.lilyObjects',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
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
