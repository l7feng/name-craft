"""运行期数据目录：`%LOCALAPPDATA%/namecraft/`。

`NAMECRAFT_HOME` 环境变量可覆盖（测试与便携场景）；日志与设置都落这里，不进版本库。
"""

from __future__ import annotations

import os
from pathlib import Path


def runtime_dir() -> Path:
    override = os.environ.get("NAMECRAFT_HOME")
    if override:
        base = Path(override)
    else:
        root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        base = Path(root) / "namecraft"
    base.mkdir(parents=True, exist_ok=True)
    return base


def journals_dir() -> Path:
    d = runtime_dir() / "journals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def settings_path() -> Path:
    return runtime_dir() / "settings.json"