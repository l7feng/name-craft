"""Rearrange 规则：按分隔符/位置/精确串切分文件名，再用 $n 模板重排。

模板：$0 = 原始整段（skip_ext 范围内），$n = 第 n 段（1 起），
$-n = 倒数第 n 段，越界段替换为空。分隔符本身被丢弃。
right_to_left=True 时段编号反向（$1 指最右段）。
exact 模式按顺序逐个查找分隔符，任一缺失则整名不变（ADR-0001）。
"""

from __future__ import annotations

import re

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name

_TOKEN = re.compile(r"\$(-?\d+)")


def _split_delimiters(s: str, delims: list[str]) -> list[str]:
    if not delims:
        return [s]
    pat = "|".join(re.escape(d) for d in delims if d)
    if not pat:
        return [s]
    return re.split(pat, s)


def _split_positions(s: str, positions: list[int]) -> list[str]:
    """在第 n 个字符前切开（1 起）；越界或 <=1 的位置忽略。"""
    cuts = sorted({p - 1 for p in positions if 1 < p <= len(s)})
    parts = []
    prev = 0
    for c in cuts:
        parts.append(s[prev:c])
        prev = c
    parts.append(s[prev:])
    return parts


def _split_exact(s: str, delims: list[str]) -> list[str] | None:
    parts = []
    rest = s
    for d in delims:
        if not d:
            return None
        idx = rest.find(d)
        if idx == -1:
            return None
        parts.append(rest[:idx])
        rest = rest[idx + len(d) :]
    parts.append(rest)
    return parts


def make(params: dict):
    mode = str(params.get("split", "delimiters"))  # delimiters / positions / exact
    raw = str(params.get("value", ""))
    pattern = str(params.get("pattern", "$0"))
    rtl = bool(params.get("right_to_left", False))
    skip_ext = bool(params.get("skip_ext", True))

    if mode == "positions":
        nums = []
        for p in raw.split("*|*"):
            p = p.strip()
            if p:
                try:
                    nums.append(int(p))
                except ValueError:
                    continue
        delims: list[str] = []
    else:
        sep = "*|*" if mode == "exact" else "|"
        delims = [d for d in raw.split(sep) if d]
        nums = []

    def apply(name: str, ctx: Ctx) -> str:
        def run(s: str) -> str:
            if mode == "positions":
                pos = [len(s) + 1 - p for p in nums] if rtl else nums
                parts = _split_positions(s, pos)
            elif mode == "exact":
                ds = list(reversed(delims)) if rtl else delims
                got = _split_exact(s, ds)
                if got is None:
                    return s
                parts = got
            else:
                parts = _split_delimiters(s, delims)
            if rtl:
                parts = list(reversed(parts))

            def sub(m: re.Match) -> str:
                n = int(m.group(1))
                if n == 0:
                    return s
                idx = n - 1 if n > 0 else len(parts) + n
                if 0 <= idx < len(parts):
                    return parts[idx]
                return ""

            return _TOKEN.sub(sub, pattern)

        return on_name(name, skip_ext, run)

    return apply