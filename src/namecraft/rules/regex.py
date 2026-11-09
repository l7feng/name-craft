"""RegEx 规则：Python re 正则替换（干净室实现，不复制 TRegExpr）。

替换串兼容 $1 / ${1}，统一转成 Python 的 \\g<n>；原生 \\1 直接可用。
无效表达式在 make 时抛 ValueError。与 TRegExpr 的方言差异见项目 cairn 开放问题。
"""

from __future__ import annotations

import re

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name

_DOLLAR = re.compile(r"\$\{(\d+)\}|\$(\d+)")


def _convert_replacement(repl: str) -> str:
    return _DOLLAR.sub(lambda m: "\\g<" + (m.group(1) or m.group(2)) + ">", repl)


def make(params: dict):
    expression = str(params.get("expression", ""))
    replacement = _convert_replacement(str(params.get("replacement", "")))
    case_sensitive = bool(params.get("case_sensitive", True))
    skip_ext = bool(params.get("skip_ext", True))

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pat = re.compile(expression, flags)
    except re.error as e:
        raise ValueError(f"regex: 无效表达式 {expression!r}: {e}") from e

    def apply(name: str, ctx: Ctx) -> str:
        return on_name(name, skip_ext, lambda s: pat.sub(replacement, s))

    return apply