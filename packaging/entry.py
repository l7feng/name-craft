"""PyInstaller 打包入口：等价于 `namecraft-gui` 控制台脚本。"""

from __future__ import annotations

import sys

from namecraft.gui import run

if __name__ == "__main__":
    sys.exit(run())
