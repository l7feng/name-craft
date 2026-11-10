"""随包文档定位：UCS 规范与分类表。

源码运行时取仓库 `docs/`；PyInstaller 打包后取 `sys._MEIPASS/docs/`
（onedir 即 `_internal/docs/`，onefile 为解包临时目录）。两个文件都由
打包规格 datas 收进产物，界面只读取与另存，不修改原件。
"""

from __future__ import annotations

import sys
from pathlib import Path

DOCS = {
    "guide": "UCS命名规范.md",
    "table": "UCS分类表-8.2.1.tsv",
}


def docs_dir() -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", ""):
        return Path(sys._MEIPASS) / "docs"
    return Path(__file__).resolve().parents[3] / "docs"


def doc_path(kind: str) -> Path:
    name = DOCS.get(kind)
    if name is None:
        raise ValueError(f"未知文档：{kind}")
    return docs_dir() / name


def read_text(kind: str) -> str:
    with open(doc_path(kind), encoding="utf-8") as f:
        return f.read()
