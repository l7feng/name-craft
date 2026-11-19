# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 单文件规格：windowed onefile，便于直接放桌面运行。

在仓库根目录构建：

    .venv/Scripts/python.exe -m PyInstaller packaging/namecraft-onefile.spec --noconfirm --clean

产物 `dist/Name Craft.exe`：单文件，无需 `_internal/`。
"""

from pathlib import Path

PACKAGING = Path(SPECPATH)  # packaging/
PROJECT = PACKAGING.parent  # 仓库根

a = Analysis(
    [str(PACKAGING / "entry.py")],
    pathex=[str(PROJECT / "src")],
    binaries=[],
    datas=[
        (str(PROJECT / "src" / "namecraft" / "gui" / "assets"), "namecraft/gui/assets"),
        (str(PROJECT / "docs"), "docs"),
    ],
    hiddenimports=[
        "clr",
        "webview.platforms.winforms",
        "webview.platforms.win32",
        "webview.platforms.edgechromium",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Name Craft",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(PACKAGING / "version_info.txt"),
    icon=str(PROJECT / "assets" / "icons" / "app.ico"),
)
