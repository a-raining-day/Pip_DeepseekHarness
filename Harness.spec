# -*- mode: python ; coding: utf-8 -*-
import os

# SPECPATH 为 PyInstaller 提供的 spec 所在目录（>= 4.3），保证任何 cwd 下都能找到 harness 包
project_dir = os.path.abspath(SPECPATH)

a = Analysis(
    ['Harness.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc_data', 'lib2to3', 'test'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Harness',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
