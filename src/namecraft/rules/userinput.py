"""UserInput 规则：按标记顺序逐行取用户输入名单（替换 / 前置 / 后置）。

名单行数不足时，超出的文件保持原名。skip_ext=True 时三种模式都保留
原扩展名；False 时 front 加在整名前、after 加在整名后、replace 换整名。
"""

from __future__ import annotations

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import split_ext


def make(params: dict):
    raw = params.get("names", [])
    if isinstance(raw, str):
        lines = raw.splitlines()
    else:
        lines = [str(x) for x in raw]
    mode = str(params.get("mode", "replace"))  # replace / front / after
    skip_ext = bool(params.get("skip_ext", True))

    def apply(name: str, ctx: Ctx) -> str:
        if ctx.index >= len(lines):
            return name
        line = lines[ctx.index]
        base, ext = split_ext(name)
        if not skip_ext:
            if mode == "front":
                return line + name
            if mode == "after":
                return name + line
            return line
        if mode == "front":
            return line + base + ext
        if mode == "after":
            return base + line + ext
        return line + ext

    return apply