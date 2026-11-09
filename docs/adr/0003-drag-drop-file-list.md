# 0003 — 文件拖拽与显式文件列表

- 日期：2026-11-09
- 状态：已采纳
- 背景：桌面界面需要拖入文件后显示原名称，添加规则后在右侧显示新名称；WebView2 的 HTML5 拖放不暴露绝对路径，无法直接交给现有预览/执行链路。
- 决定：
  1. 关闭 WebView2 的 `AllowExternalDrop`，在宿主 WebView2 控件上接收 WinForms 拖放；`DragDrop` 读取 `DataFormats.FileDrop` 的绝对路径，经 `ExecuteScriptAsync` 调用页面 `window.namecraftDrop(paths)`。
  2. 显式文件路径进入独立入口：`fs.items_from_paths` 校验“现存文件”并去重，`session.preview.compute_items` 复用同一规则链、校验、占用扫描与环检测；桥接 `preview`/`execute` 接受 `paths`。
  3. 拖入的文件列表优先于文件夹；显式列表为空时回退文件夹。执行与撤销后用日志条目的 old/new 路径更新列表，避免下一次预览指向旧路径。
  4. 另设「选择文件…」多选回退入口，键盘与触控用户不依赖原生拖放。
- 后果：拖入目录或已不存在的路径会整体报错，不做静默过滤；拖入文件可来自多个目录，占用扫描按各自目录进行。原生拖放接线失败只影响拖拽入口，浏览文件夹与选择文件仍可用。
- 验证：源码态以合成 `DataObject(FileDrop)` 驱动真实 `DragDrop` 回调，经 CDP 核对拖入名、加规则后的新名称、仅改拖入文件、撤销后路径回退；真实 Explorer 鼠标拖拽未脚本化，保留人工复核边界。
