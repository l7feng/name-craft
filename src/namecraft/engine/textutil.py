"""文本工具：扩展名切分、通配符转正则、skip_extension 包装。"""

from __future__ import annotations

import re
from collections.abc import Callable


def split_ext(name: str) -> tuple[str, str]:
    """按最后一个点切分 (base, ext)，ext 含点。

    无点或点在首位（如 .hidden）视为无扩展名；文件夹语义不在本函数范围。
    """
    idx = name.rfind(".")
    if idx <= 0:
        return name, ""
    return name[:idx], name[idx:]


def on_name(name: str, skip_ext: bool, fn: Callable[[str], str]) -> str:
    """skip_ext=True 时只处理 base，扩展名原样拼回。"""
    if not skip_ext:
        return fn(name)
    base, ext = split_ext(name)
    return fn(base) + ext


def wildcard_to_regex(pattern: str) -> str:
    """ReNamer 口径通配符 → 正则：* 任意串、? 单字符、[abc] 字符集、[a-z] 范围。"""
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            out.append(".*")
        elif c == "?":
            out.append(".")
        elif c == "[":
            j = pattern.find("]", i + 1)
            if j == -1:
                out.append(re.escape(c))
            else:
                inner = pattern[i + 1 : j]
                # 字符集内仅转义反斜杠与 ^（避免意外取反），保留 a-z 范围语义
                inner = inner.replace("\\", "\\\\").replace("^", "\\^")
                out.append("[" + inner + "]")
                i = j
        else:
            out.append(re.escape(c))
        i += 1
    return "".join(out)