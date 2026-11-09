"""Extension 规则：替换或追加扩展名（作用于整名，无 skip_ext）。

new_ext 允许带或不带前导点；置空 + 替换 = 去掉扩展名。
append=True 时整名后追加 ".new_ext"（原扩展名成为 base 的一部分）。
"""

from __future__ import annotations

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import split_ext


def make(params: dict):
    new_ext = str(params.get("new_ext", "")).lstrip(".")
    append = bool(params.get("append", False))
    case_mode = str(params.get("case", "none"))  # none / lower / upper（作用于新扩展名）

    if case_mode == "lower":
        ext = new_ext.lower()
    elif case_mode == "upper":
        ext = new_ext.upper()
    else:
        ext = new_ext

    def apply(name: str, ctx: Ctx) -> str:
        if append:
            return name + "." + ext if ext else name
        base, _ = split_ext(name)
        return base + "." + ext if ext else base

    return apply