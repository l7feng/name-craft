"""Case 规则：大小写变换 + 片段强制写法 + 扩展名大小写。

优先级（对齐参考版）：mode 先作用于 base（或整名）→ fragments 按输入原样
强制替换（不区分大小写查找）→ ext_case 最后覆盖扩展名，优先于一切。
"""

from __future__ import annotations

import re

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import split_ext


def _capitalize(s: str, preserve: bool) -> str:
    base = s if preserve else s.lower()
    return re.sub(r"\b[a-z]", lambda m: m.group(0).upper(), base)


def _sentence(s: str) -> str:
    low = s.lower()
    for i, c in enumerate(low):
        if c.isalpha():
            return low[:i] + c.upper() + low[i + 1 :]
    return low


def make(params: dict):
    mode = str(params.get("mode", "none"))
    fragments = [f for f in str(params.get("fragments", "")).split(",") if f]
    ext_case = str(params.get("ext_case", "none"))  # none / lower / upper
    skip_ext = bool(params.get("skip_ext", True))

    def apply(name: str, ctx: Ctx) -> str:
        base, ext = split_ext(name)
        scope = base if skip_ext else name
        if mode == "lower":
            scope = scope.lower()
        elif mode == "upper":
            scope = scope.upper()
        elif mode == "capitalize":
            scope = _capitalize(scope, preserve=False)
        elif mode == "capitalize_preserve":
            scope = _capitalize(scope, preserve=True)
        elif mode == "invert":
            scope = scope.swapcase()
        elif mode == "sentence":
            scope = _sentence(scope)

        for frag in fragments:
            scope = re.sub(re.escape(frag), lambda m, f=frag: f, scope, flags=re.IGNORECASE)

        if skip_ext:
            result = scope + ext
        else:
            result = scope

        if ext_case in ("lower", "upper"):
            b, e = split_ext(result)
            if e:
                result = b + (e.lower() if ext_case == "lower" else e.upper())
        return result

    return apply