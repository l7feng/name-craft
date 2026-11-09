"""GUI 入口：启动 pywebview 窗口并加载单文件界面。"""

from __future__ import annotations

from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "assets"


def enable_dpi_awareness() -> None:
    """在导入 webview/WinForms 之前声明 DPI 感知，避免截图与坐标被虚拟化。"""
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_DPI_AWARE
    except (ImportError, AttributeError, OSError):
        pass


def run() -> int:
    from .crash import install

    install()
    enable_dpi_awareness()
    try:
        import webview
    except ImportError:
        print('未安装 pywebview：请执行 pip install "pywebview>=5" 后重试。')
        return 2
    from .bridge import Bridge

    api = Bridge()
    webview.create_window(
        "namecraft",
        str(ASSETS / "index.html"),
        js_api=api,
        width=1240,
        height=820,
        min_size=(980, 640),
    )
    webview.start()
    return 0
