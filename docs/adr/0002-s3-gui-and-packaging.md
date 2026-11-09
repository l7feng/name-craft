# 0002 — S3 界面形态与打包方式

- 日期：2026-11-09
- 状态：已采纳
- 背景：S3 需要桌面界面、确认式覆盖与可分发 exe；需确定界面框架、打包形态与运行期数据位置。
- 决定：
  1. 界面取 pywebview（WinForms + WebView2），避免引入 Qt 等重依赖；前端为单个 `index.html`（内联 CSS/JS），经 `js_api` 桥接 `session` 层。
  2. 打包取 PyInstaller onedir、windowed；入口 `packaging/entry.py`，规格 `packaging/namecraft.spec`，版本资源 `packaging/version_info.txt`。界面资源以 data 形式落 `_internal/namecraft/gui/assets`。
  3. 运行期数据（设置、撤销日志）写 `%LOCALAPPDATA%/namecraft/`，`NAMECRAFT_HOME` 可覆盖；不写程序目录。
  4. 崩溃取证：`--windowed` 下安装 `sys.excepthook`，回溯写 exe 同目录与 TEMP 的 `namecraft_crash.log`。
  5. 交付落点沿用出口约定：`D:/Ai-Files/Tools/Exe/11-批量重命名工具/namecraft-v0.2.0/`，exe 与 `_internal/` 同级，附 README 与 `SHA256SUMS.txt`。
- 后果：onedir 目录必须整体分发，单独移动 exe 不成立；不含安装器与代码签名。WebView2 Runtime 由系统提供，Windows 10 需确认已安装。
- 验证：交付路径下真启动并完成预览、确认、改名、日志、撤销的隔离目录冒烟；未做跨机与签名验证。
