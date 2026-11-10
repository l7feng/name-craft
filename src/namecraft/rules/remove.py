"""Remove 规则：删除指定字符串（多串顺序处理，支持通配符与出现位置选择）。"""

from __future__ import annotations

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import on_name

from ._search import cut_spans, occurrences, split_multi


def make(params: dict):
    text = str(params.get("text", ""))
    which = str(params.get("occurrences", "all"))  # first / last / all
    case_sensitive = bool(params.get("case_sensitive", True))
    wildcards = bool(params.get("wildcards", False))
    skip_ext = bool(params.get("skip_ext", True))

    def apply(name: str, ctx: Ctx) -> str:
        def run(s: str) -> str:
            for needle in split_multi(text):
                spans = occurrences(
                    s,
                    needle,
                    case_sensitive=case_sensitive,
                    wildcards=wildcards,
                    which=which,
                )
                s = cut_spans(s, spans)
            return s

        return on_name(name, skip_ext, run)

    return apply