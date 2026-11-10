"""Insert 规则：前缀/后缀/指定位置/锚文本前后插入。

params: what, where(prefix|suffix|position|after|before), position=1,
from_right=False, text(锚文本), skip_ext=True。
锚文本取首次出现（ADR-0001 假设）；未找到则不插入。
"""

from __future__ import annotations

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name


def make(params: dict):
    what = str(params.get("what", ""))
    where = params.get("where", "prefix")
    position = int(params.get("position", 1))
    from_right = bool(params.get("from_right", False))
    anchor = str(params.get("text", ""))
    skip_ext = bool(params.get("skip_ext", True))

    def apply(s: str) -> str:
        if where == "prefix":
            return what + s
        if where == "suffix":
            return s + what
        if where == "position":
            idx = len(s) - position + 1 if from_right else position - 1
            idx = max(0, min(idx, len(s)))
            return s[:idx] + what + s[idx:]
        if where == "after":
            i = s.find(anchor)
            return s if i < 0 or not anchor else s[: i + len(anchor)] + what + s[i + len(anchor) :]
        if where == "before":
            i = s.find(anchor)
            return s if i < 0 or not anchor else s[:i] + what + s[i:]
        raise ValueError(f"未知 Insert where: {where}")

    def fn(name: str, ctx: Ctx) -> str:
        return on_name(name, skip_ext, apply)

    return fn