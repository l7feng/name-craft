"""Replace 规则：查找/替换串成对顺序执行（串行语义，对齐参考版）。

要点：每对替换在上一次替换的结果上执行——ABBA 用 A|B → B|A 会得到 AAAA，
这是参考版的已知行为，本项目按对齐口径保留并有单测锚定。
Find 多于 Replace 时多出的查找串替换为空；Replace 多出的忽略。
"""

from __future__ import annotations

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name

from ._search import occurrences, split_multi


def make(params: dict):
    finds = split_multi(str(params.get("find", "")))
    replaces = str(params.get("replace", "")).split("*|*")
    which = str(params.get("occurrences", "all"))
    case_sensitive = bool(params.get("case_sensitive", True))
    wildcards = bool(params.get("wildcards", False))
    skip_ext = bool(params.get("skip_ext", True))

    pairs = [(f, replaces[i] if i < len(replaces) else "") for i, f in enumerate(finds)]

    def apply(name: str, ctx: Ctx) -> str:
        def run(s: str) -> str:
            for needle, repl in pairs:
                spans = occurrences(
                    s,
                    needle,
                    case_sensitive=case_sensitive,
                    wildcards=wildcards,
                    which=which,
                )
                for start, end in reversed(spans):
                    s = s[:start] + repl + s[end:]
            return s

        return on_name(name, skip_ext, run)

    return apply