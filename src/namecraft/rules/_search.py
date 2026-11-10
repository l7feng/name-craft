"""查找辅助：多字符串 + 大小写 + 通配符 + 出现位置选择，供 Remove / Replace 共用。

多字符串以字面 `*|*` 分隔（ReNamer 口径）；单串为空时不参与查找。
"""

from __future__ import annotations

import re

from namecraft.engine.textutil import wildcard_to_regex

MULTI_SEP = "*|*"


def split_multi(text: str) -> list[str]:
    """按 *|* 拆分为查找串列表，去掉空串。"""
    return [p for p in text.split(MULTI_SEP) if p]


def occurrences(
    s: str,
    needle: str,
    *,
    case_sensitive: bool = True,
    wildcards: bool = False,
    which: str = "first",
) -> list[tuple[int, int]]:
    """返回 needle 在 s 中的 (start, end) 区间，按位置升序。

    which: first / last / all。通配符模式下按正则非重叠匹配。
    """
    if not needle or not s:
        return []
    flags = 0 if case_sensitive else re.IGNORECASE
    if wildcards:
        pat = re.compile(wildcard_to_regex(needle), flags)
        spans = [(m.start(), m.end()) for m in pat.finditer(s)]
    else:
        hay = s if case_sensitive else s.lower()
        sub = needle if case_sensitive else needle.lower()
        spans = []
        pos = hay.find(sub)
        while pos != -1:
            spans.append((pos, pos + len(sub)))
            pos = hay.find(sub, pos + len(sub))
    if not spans:
        return []
    if which == "first":
        return spans[:1]
    if which == "last":
        return spans[-1:]
    return spans


def cut_spans(s: str, spans: list[tuple[int, int]]) -> str:
    """删除若干区间（假定互不重叠）。"""
    out = s
    for start, end in sorted(spans, reverse=True):
        out = out[:start] + out[end:]
    return out