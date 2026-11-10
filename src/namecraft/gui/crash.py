"""窗口化 exe 崩溃取证：把未捕获异常的回溯写到 exe 旁与 TEMP 两份。

--windowed 打包时 stdout/stderr 被丢弃，崩框只报一行 "Failed to execute script"。
装了本钩子后，Python 侧异常会留下完整回溯；若什么都没写出来，则是 bootloader
级崩溃（依赖缺失/构建中断），应重新打包而不是改代码。
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

LOG_NAME = "namecraft_crash.log"


def _targets() -> list[str]:
    dirs = []
    if getattr(sys, "frozen", False):
        dirs.append(str(Path(sys.executable).resolve().parent))
    dirs.append(os.environ.get("TEMP") or os.environ.get("TMP") or str(Path.home()))
    return dirs


def dump(exc_type, exc_val, exc_tb) -> None:
    text = f"==== {datetime.now():%Y-%m-%d %H:%M:%S} ====\n"
    text += "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
    for folder in _targets():
        try:
            with open(Path(folder) / LOG_NAME, "a", encoding="utf-8") as fh:
                fh.write(text)
        except OSError:
            pass


def install() -> None:
    sys.excepthook = dump
