# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包规格：onedir、窗口化。

在仓库根目录构建：

    .venv/Scripts/python.exe -m PyInstaller packaging/namecraft.spec --noconfirm --clean

产物 `dist/namecraft/`：`namecraft.exe` 与 `_internal/` 同级。
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
    [],
    exclude_binaries=True,
    name="namecraft",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(PACKAGING / "version_info.txt"),
    icon=str(PACKAGING / "namecraft.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="namecraft",
)
