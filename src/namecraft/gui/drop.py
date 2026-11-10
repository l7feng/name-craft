"""Windows 原生文件拖放：拿绝对路径，再交给页面显示。

WebView2 默认把外部拖入的文件当作自身导航/拖放处理（可能直接打开文件），
所以关闭 AllowExternalDrop，改在宿主 WebView2 控件上接收 OLE 拖放：
DragEnter/DragOver 给复制光标，DragDrop 读取 DataFormats.FileDrop 的
绝对路径，通过 ExecuteScriptAsync 调用 window.namecraftDrop(paths)。
拖放接入失败只影响拖拽入口，不影响“浏览/选择文件”等既有功能。
"""

from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)

# 保留事件委托引用：部分 pythonnet 版本不会替 Python 回调保活
_HANDLERS: dict[int, tuple] = {}


def install(window, timeout: float = 15.0) -> bool:
    """等待窗口显示后在 UI 线程挂接拖放事件；返回是否挂接成功。"""
    try:
        if not window.events.shown.wait(timeout):
            log.warning("窗口未在 %.0f 秒内显示，跳过文件拖放接入", timeout)
            return False
        native = getattr(window, "native", None)
        control = getattr(native, "webview", None) if native is not None else None
        if native is None or control is None:
            log.warning("当前 GUI 后端没有可用的 WebView2 控件，跳过文件拖放接入")
            return False
        from System import Func, Type

        native.Invoke(Func[Type](lambda: _attach(control)))
        return True
    except Exception:  # pragma: no cover - 仅在真实 GUI 环境触发
        log.exception("文件拖放接入失败")
        return False


def _attach(control) -> None:  # pragma: no cover - 依赖 WinForms/WebView2
    """在 UI 线程订阅 WebView2 控件的拖放事件。"""
    from System.Windows.Forms import DataFormats, DragDropEffects

    copy_effect = DragDropEffects.Copy
    # .NET 枚举成员 None 在 Python 里是关键字，不能写成 DragDropEffects.None
    none_effect = getattr(DragDropEffects, "None")
    try:
        control.AllowExternalDrop = False
    except Exception:  # noqa: BLE001 - 旧版 WebView2 没有该属性
        log.warning("WebView2 不支持 AllowExternalDrop，外部文件可能仍由页面接管")
    control.AllowDrop = True

    def has_files(args) -> bool:
        try:
            return bool(args.Data and args.Data.GetDataPresent(DataFormats.FileDrop))
        except Exception:  # noqa: BLE001 - pythonnet 拖放数据可能为空/不可读
            return False

    def on_drag_enter(sender, args) -> None:
        if has_files(args):
            args.Effect = copy_effect
            _script(control, "window.namecraftDrag && window.namecraftDrag(true);")
        else:
            args.Effect = none_effect

    def on_drag_over(sender, args) -> None:
        args.Effect = copy_effect if has_files(args) else none_effect

    def on_drag_leave(sender, args) -> None:
        _script(control, "window.namecraftDrag && window.namecraftDrag(false);")

    def on_drag_drop(sender, args) -> None:
        _script(control, "window.namecraftDrag && window.namecraftDrag(false);")
        if not has_files(args):
            args.Effect = none_effect
            return
        try:
            paths = [str(p) for p in args.Data.GetData(DataFormats.FileDrop)]
        except Exception:
            log.exception("读取拖入文件路径失败")
            args.Effect = none_effect
            return
        args.Effect = copy_effect
        if paths:
            _script(
                control,
                "window.namecraftDrop && window.namecraftDrop("
                + json.dumps(paths, ensure_ascii=False)
                + ");",
            )

    control.DragEnter += on_drag_enter
    control.DragOver += on_drag_over
    control.DragLeave += on_drag_leave
    control.DragDrop += on_drag_drop
    _HANDLERS[id(control)] = (on_drag_enter, on_drag_over, on_drag_leave, on_drag_drop)


def _script(control, code: str) -> None:  # pragma: no cover - 依赖 WebView2
    try:
        core = getattr(control, "CoreWebView2", None)
        if core is not None:
            core.ExecuteScriptAsync(code)
    except Exception:
        log.debug("向页面发送拖放事件失败", exc_info=True)
