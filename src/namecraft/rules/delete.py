"""Delete 规则：删除 From 到 Until 的字符段。

params: from_mode(position|delimiter), from_value, until_mode(count|delimiter|end),
until_value, skip_ext=True, right_to_left=False, keep_delimiters=False。
右到左通过镜像字符串实现（From/Until 语义自然对调）。
Until 分隔符未找到时不删除（保守假设，待参考版副本消歧）。
"""

from __future__ import annotations

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name


def make(params: dict):
    from_mode = params.get("from_mode", "position")
    from_value = params.get("from_value", 1)
    until_mode = params.get("until_mode", "end")
    until_value = params.get("until_value", 1)
    skip_ext = bool(params.get("skip_ext", True))
    rtl = bool(params.get("right_to_left", False))
    keep = bool(params.get("keep_delimiters", False))

    def cut(s: str) -> str:
        if from_mode == "position":
            start = int(from_value) - 1
            from_delim = ""
        else:
            from_delim = str(from_value)
            start = s.find(from_delim)
            if start < 0:
                return s
        if until_mode == "count":
            end = start + int(until_value)
            until_delim = ""
        elif until_mode == "delimiter":
            until_delim = str(until_value)
            search_from = start + len(from_delim)
            i = s.find(until_delim, search_from)
            if i < 0:
                return s
            end = i + len(until_delim)
        else:  # end
            end = len(s)
            until_delim = ""
        if keep:
            start += len(from_delim)
            end -= len(until_delim)
        start = max(0, min(start, len(s)))
        end = max(start, min(end, len(s)))
        return s[:start] + s[end:]

    def apply(s: str) -> str:
        return cut(s[::-1])[::-1] if rtl else cut(s)

    def fn(name: str, ctx: Ctx) -> str:
        return on_name(name, skip_ext, apply)

    return fn