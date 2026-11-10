"""Strip 规则：按字符类别删除字符（英文字母/数字/符号/括号/自定义集合）。

except_selected=True 反转：只保留所选类别。未选任何类别时整名不变。
brackets 选项只删括号字符本身；删括号及其内容属 CleanUp（见 cleanup.py）。
"""

from __future__ import annotations

import unicodedata

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name

BRACKETS = "()[]{}<>"


def make(params: dict):
    english = bool(params.get("english", False))
    digits = bool(params.get("digits", False))
    symbols = bool(params.get("symbols", False))
    brackets = bool(params.get("brackets", False))
    custom = str(params.get("custom", ""))
    except_selected = bool(params.get("except_selected", False))
    skip_ext = bool(params.get("skip_ext", True))

    any_selected = english or digits or symbols or brackets or bool(custom)
    custom_set = set(custom)

    def selected(c: str) -> bool:
        if english and ("a" <= c <= "z" or "A" <= c <= "Z"):
            return True
        if digits and c.isdecimal():
            return True
        if symbols and unicodedata.category(c)[0] in ("P", "S"):
            return True
        if brackets and c in BRACKETS:
            return True
        return c in custom_set

    def apply(name: str, ctx: Ctx) -> str:
        if not any_selected:
            return name

        def run(s: str) -> str:
            if except_selected:
                return "".join(c for c in s if selected(c))
            return "".join(c for c in s if not selected(c))

        return on_name(name, skip_ext, run)

    return apply