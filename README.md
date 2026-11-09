# namecraft

规则链式文件批量重命名工具（Windows，Python）。参考 ReNamer 7.2 的公开行为描述做干净室（clean-room）重写：只采用行为语义与公开文档示例作为测试基准，不含任何 ReNamer 代码、脚本或资源。

- 产品名与仓名 `namecraft` 为人类 2026-11-09 赐名；项目记录在个人知识库 `5-领域-A/06-软件制作/89-文件批量重命名工具/`。
- 当前阶段 S2：核心规则引擎（12 规则）＋ CLI 预览；GUI（pywebview）在 S3。
- 与既有 `rename-unify` 仓相互独立、互不引用。

## 开发

```bash
python -m venv .venv
.venv/Scripts/pip install -e .[dev]
.venv/Scripts/pytest
```

## CLI 预览（S2）

```bash
namecraft preview <目录> --rules rules.json
```

`rules.json` 为规则栈数组，每项 `{"type": "insert", "params": {...}, "enabled": true}`；规则类型与参数见 `src/namecraft/rules/` 各模块 docstring 与 `docs/adr/`。

首期 12 种规则：`insert` `delete` `remove` `replace` `rearrange` `extension` `strip` `case` `serialize` `cleanup` `regex` `userinput`。示例：

```json
[
  {"type": "cleanup", "params": {"brackets": "([{", "fix_spaces": true}},
  {"type": "case", "params": {"mode": "capitalize"}},
  {"type": "serialize", "params": {"where": "prefix", "pad": 3}}
]
```

预览只读，不改名；存在校验错误时退出码 1，规则文件错误退出码 2。

## 安全口径

- 预览先行，执行按预览所见（WYSIWYG）；校验四项：重复、禁用字符、目标占用、超长。
- 冲突默认拦截；可选 `(n)` 后缀消解；覆盖需逐次确认（S3 实现），无静默覆盖。
- 撤销基于执行日志（S3 实现）。

## 布局

见 `STRUCTURE.md`；决策记录见 `docs/adr/`。