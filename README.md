# NameCraft

规则链式文件批量重命名工具（Windows，Python）。参考 ReNamer 7.2 的公开行为描述做干净室（clean-room）重写：只采用行为语义与公开文档示例作为测试基准，不含任何 ReNamer 代码、脚本或资源。

- 产品名 NameCraft（原名 namecraft，2026-11-10 更名）；项目记录在个人知识库 `5-领域-A/06-软件制作/89-文件批量重命名工具/`。
- 当前版本 0.3.0：13 规则引擎（含 UCS 8.2.1 命名）、自定义规则模板、CLI 预览、pywebview 桌面界面、文件拖拽区、确认式覆盖、执行日志与撤销、PyInstaller 打包。
- 与既有 `rename-unify` 仓相互独立、互不引用。

## 开发

```bash
python -m venv .venv
.venv/Scripts/pip install -e .[dev]
.venv/Scripts/pip install -e .[gui]
.venv/Scripts/pytest
.venv/Scripts/ruff check .
```

## 桌面界面（S3）

```bash
namecraft gui
# 或 namecraft-gui
```

界面支持规则栈增删排序与启停、实时预览、文件拖拽区（拖入即显示原名称，添加规则后在右侧显示新名称，也可用「选择文件…」多选）、三种冲突口径（拦截／加 `(n)` 后缀／逐项确认覆盖）、执行日志与最近一次撤销。拖入的文件列表优先于文件夹；清空后回到文件夹模式。设置、日志与自定义模板写 `%LOCALAPPDATA%/namecraft/`，可用 `NAMECRAFT_HOME` 覆盖。

UCS 命名规则内置 753 个 CatID 的分类选择器，附「查看 UCS 规范」与另存入口；自定义规则模板可把当前规则栈按名称保存，之后一键套用。

## CLI 预览（S2 起）

```bash
namecraft preview <目录> --rules rules.json
namecraft execute <目录> --rules rules.json   # S3：真实执行并写日志
namecraft undo                                 # S3：撤销最近一次已完成批次
```

`rules.json` 为规则栈数组，每项 `{"type": "insert", "params": {...}, "enabled": true}`；规则类型与参数见 `src/namecraft/rules/` 各模块 docstring 与 `docs/adr/`。

首期 13 种规则：`insert` `delete` `remove` `replace` `rearrange` `extension` `strip` `case` `serialize` `cleanup` `regex` `userinput` `ucs`。其中 `ucs` 按 UCS 8.2.1 结构生成名称，分类表见 `docs/UCS分类表-8.2.1.tsv`，使用说明见 `docs/UCS命名规范.md`。示例：

```json
[
  {"type": "cleanup", "params": {"brackets": "([{", "fix_spaces": true}},
  {"type": "case", "params": {"mode": "capitalize"}},
  {"type": "serialize", "params": {"where": "prefix", "pad": 3}}
]
```

预览只读，不改名；存在校验错误时退出码 1，规则文件错误退出码 2。

## 打包

```bash
.venv/Scripts/pip install pyinstaller
.venv/Scripts/python packaging/make_icon.py           # 重新生成 packaging/namecraft.ico
.venv/Scripts/python -m PyInstaller packaging/namecraft.spec --noconfirm --clean
.venv/Scripts/python -m PyInstaller packaging/namecraft-onefile.spec --noconfirm --clean
```

产物 `dist/namecraft/`（windowed onedir；exe 与 `_internal/` 同级）与 `dist/namecraft-onefile.exe`（windowed onefile，单文件可直接双击，启动时解压到临时目录，稍慢）。图标由 `packaging/make_icon.py` 程序化生成（渐变圆角底 + 字母标记，16/20/24 用单字 N，更大尺寸用 nc），PyInstaller 将 `namecraft.ico` 写入 exe 资源；窗口标题栏与任务栏沿用该 exe 图标。交付包落 `D:/Ai-Files/Tools/Exe/11-批量重命名工具/namecraft-v0.3.0/`，含 README、`docs/`（UCS 规范与分类表）与 `SHA256SUMS.txt`；面向桌面的单文件版可直接取 `dist/namecraft-onefile.exe`。

## 安全口径

- 预览先行，执行按预览所见（WYSIWYG）；校验四项：重复、禁用字符、目标占用、超长。
- 冲突默认拦截；可选 `(n)` 后缀消解；覆盖需逐项确认，无静默覆盖。
- 撤销基于执行日志，仅最近一次已完成批次可撤销；被覆盖的旧文件不可恢复。

## 布局

见 `STRUCTURE.md`；决策记录见 `docs/adr/`。
