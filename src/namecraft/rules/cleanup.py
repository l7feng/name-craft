"""CleanUp 规则：括号内容清除、字符转空格、空格规整、驼峰拆分。

执行顺序固定：删括号及内容 → 指定字符逐个换空格 → Unicode 空格归一 →
驼峰拆分 → 多余空格合并与首尾去除。首期不含 SharePoint 与 marks 选项。
"""

from __future__ import annotations

import re
import unicodedata

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name

_BRACKET_PATTERNS = [
    re.compile(r"\([^()]*\)"),
    re.compile(r"\[[^\[\]]*\]"),
    re.compile(r"\{[^{}]*\}"),
    re.compile(r"<[^<>]*>"),
]
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def make(params: dict):
    brackets = str(params.get("brackets", ""))  # 含哪对符号就删哪对，如 "([{"
    chars_to_spaces = str(params.get("chars_to_spaces", ""))
    normalize_space = bool(params.get("normalize_space", False))
    split_camel = bool(params.get("split_camel", False))
    fix_spaces = bool(params.get("fix_spaces", False))
    skip_ext = bool(params.get("skip_ext", True))

    def apply(name: str, ctx: Ctx) -> str:
        def run(s: str) -> str:
            for opener, pat in zip("([{<", _BRACKET_PATTERNS):
                if opener in brackets:
                    prev = None
                    while prev != s:  # 嵌套括号由内向外反复剥
                        prev = s
                        s = pat.sub("", s)
            for c in chars_to_spaces:
                s = s.replace(c, " ")
            if normalize_space:
                s = "".join(" " if unicodedata.category(c) == "Zs" else c for c in s)
            if split_camel:
                s = _CAMEL.sub(" ", s)
            if fix_spaces:
                s = re.sub(r" {2,}", " ", s).strip(" ")
            return s

        return on_name(name, skip_ext, run)

    return apply