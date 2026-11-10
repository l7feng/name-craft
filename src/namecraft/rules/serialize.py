"""Serialize 规则：序号插入（十进制 / 字母两套进制，含重复与重置）。

字母序（对齐参考版，S1 核查）：不补位时 1..26 → a..z，27 → ba，52 → bz，
53 → ca，677 → baa（长度 L≥2 的首位只取 b..z）；补位（pad>0）时为
(n-1) 的 26 进制定宽表示，a=0：1 → aaa、2 → aab（pad=3）。
十进制 pad 为 zfill 宽度。状态封闭在闭包内，每次预览重新 make。
"""

from __future__ import annotations

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name


def _letters(n: int) -> str:
    """不补位字母序：a..z, ba..bz, ca..cz, ..., za..zz, baa.."""
    if n <= 26:
        return chr(ord("a") + n - 1)
    n -= 27  # 进入长度 2 区，区容量 25*26
    length = 2
    while n >= 25 * 26 ** (length - 1):
        n -= 25 * 26 ** (length - 1)
        length += 1
    first = chr(ord("b") + n // 26 ** (length - 1))
    rest = n % 26 ** (length - 1)
    tail = []
    for _ in range(length - 1):
        tail.append(chr(ord("a") + rest % 26))
        rest //= 26
    return first + "".join(reversed(tail))


def _letters_padded(n: int, width: int) -> str:
    v = n - 1
    out = []
    for _ in range(width):
        out.append(chr(ord("a") + v % 26))
        v //= 26
    return "".join(reversed(out))


def make(params: dict):
    start = int(params.get("start", 1))
    step = int(params.get("step", 1))
    repeat = int(params.get("repeat", 1))
    reset_every = int(params.get("reset_every", 0))
    reset_folder = bool(params.get("reset_folder", False))
    reset_name = bool(params.get("reset_name", False))
    pad = int(params.get("pad", 0))
    where = str(params.get("where", "suffix"))  # prefix / suffix / position / replace
    position = int(params.get("position", 1))
    skip_ext = bool(params.get("skip_ext", True))
    system = str(params.get("system", "decimal"))  # decimal / letters

    if start < 1 or repeat < 1 or pad < 0 or reset_every < 0:
        raise ValueError("serialize: start/repeat 须 ≥1，pad/reset_every 须 ≥0")
    if system not in ("decimal", "letters"):
        raise ValueError("serialize: system 只支持 decimal / letters")

    state = {"value": start, "used": 0, "count": 0, "folder": None}

    def token(v: int) -> str:
        if system == "letters":
            return _letters_padded(v, pad) if pad > 0 else _letters(v)
        return str(v).zfill(pad)

    def apply(name: str, ctx: Ctx) -> str:
        need_reset = False
        if reset_folder and state["folder"] is not None and ctx.folder != state["folder"]:
            need_reset = True
        if reset_name and ctx.prev_input is not None and name != ctx.prev_input:
            need_reset = True
        if reset_every and state["count"] >= reset_every:
            need_reset = True
        if need_reset:
            state["value"] = start
            state["used"] = 0
            state["count"] = 0
        state["folder"] = ctx.folder

        tok = token(state["value"])
        state["used"] += 1
        state["count"] += 1
        if state["used"] >= repeat:
            state["value"] += step
            state["used"] = 0

        def run(s: str) -> str:
            if where == "prefix":
                return tok + s
            if where == "replace":
                return tok
            if where == "position":
                idx = max(0, min(len(s), position - 1))
                return s[:idx] + tok + s[idx:]
            return s + tok  # suffix

        return on_name(name, skip_ext, run)

    return apply