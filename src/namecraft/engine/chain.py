"""规则链：按栈序逐规则应用，每规则接收上一条修改后的名字。"""

from __future__ import annotations

from .models import Ctx, FileItem, Rule


def apply_chain(items: list[FileItem], rules: list[Rule]) -> list[str]:
    """对 marked 文件按规则栈计算新名；未 marked 文件原样返回。

    跨文件规则（Serialize/UserInput）按列表顺序取 ctx.index；
    每条规则内部维护 prev_input（上一个文件进入本规则时的名字）。
    """
    from namecraft.rules import REGISTRY

    marked_idx = [i for i, it in enumerate(items) if it.marked]
    names = [it.name for it in items]
    for rule in rules:
        if not rule.enabled:
            continue
        make = REGISTRY.get(rule.type)
        if make is None:
            raise ValueError(f"未知规则类型: {rule.type}")
        fn = make(dict(rule.params))
        prev: str | None = None
        for pos, i in enumerate(marked_idx):
            it = items[i]
            ctx = Ctx(
                index=pos,
                path=it.path,
                folder=it.folder,
                total=len(marked_idx),
                prev_input=prev,
            )
            prev = names[i]
            names[i] = fn(names[i], ctx)
    return names