"""执行计划：预览行 → 改名操作，落实冲突口径与确认式覆盖。

三种模式：
- block（默认）：任何校验错误或目标被占即拒绝，不自动改口径。
- suffix：先按 ` (n)` 后缀消解冲突，再生成操作。
- overwrite：目标被占时需用户在 `confirm` 中逐项给出目标路径，否则拒绝；
  确认后执行层用 os.replace 覆盖，日志记录被覆盖对象（不可恢复）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from namecraft.engine.conflicts import resolve_conflicts
from namecraft.engine.models import PreviewRow
from namecraft.engine.validate import validate

MODES = ("block", "suffix", "overwrite")
_FIXABLE = ("列表内新路径重复", "目标已被现有文件占用")


class PlanError(Exception):
    """计划不可执行（校验错误、目标占用或未确认覆盖）。"""


class OverwriteNotConfirmed(PlanError):
    """覆盖模式下列出了未确认的目标。"""


@dataclass
class RenameOp:
    old: str
    new: str
    overwrite: bool = False


@dataclass
class Plan:
    ops: list[RenameOp]
    mode: str
    notes: list[str] = field(default_factory=list)


def prepare(
    rows: list[PreviewRow],
    occupied: set[str] | None = None,
    *,
    mode: str = "block",
    confirm: set[str] | tuple[str, ...] = (),
) -> Plan:
    if mode not in MODES:
        raise ValueError(f"未知冲突模式：{mode}")
    errors = [r for r in rows if r.status == "error"]
    if mode == "suffix":
        # 重复与占用正是 suffix 模式要消解的错误，其余错误仍为硬错误
        errors = [
            r
            for r in errors
            if not all(any(x.startswith(p) for p in _FIXABLE) for x in r.reasons)
        ]
    if errors:
        detail = "；".join(f"{r.item.name}：{'、'.join(r.reasons)}" for r in errors[:5])
        raise PlanError(f"存在 {len(errors)} 项校验错误，不能执行：{detail}")

    occupied_cf = {os.path.normcase(p) for p in (occupied or set())}
    batch_sources = {os.path.normcase(r.item.path) for r in rows}
    vacated = {
        os.path.normcase(r.item.path) for r in rows if r.status == "ok" and r.changed
    }
    staying = batch_sources - vacated
    occupied_cf -= vacated  # 本批会腾出的源文件不再算占用

    notes: list[str] = []
    if mode == "suffix":
        before = [r.new_name for r in rows]
        # 除外部占用外，本批不改名的文件也会留在原地，必须一并避开
        resolve_conflicts(rows, {p for p in (occupied or set())} | staying)
        rows = validate(
            [r.item for r in rows], [r.new_name for r in rows], occupied
        )
        renamed = sum(1 for r, b in zip(rows, before) if r.new_name != b)
        if renamed:
            notes.append(f"按 (n) 后缀消解 {renamed} 处冲突")

    confirm_cf = {os.path.normcase(p) for p in confirm}
    ops: list[RenameOp] = []
    for row in rows:
        if row.status != "ok" or not row.changed:
            continue
        target = row.new_path
        key = os.path.normcase(target)
        overwrite = False
        blocked = key in occupied_cf or key in staying
        if blocked:
            if mode != "overwrite":
                raise PlanError(f"目标被现有文件占用：{target}")
            if key not in confirm_cf:
                raise OverwriteNotConfirmed(f"覆盖需逐项确认：{target}")
            overwrite = True
        ops.append(RenameOp(old=row.item.path, new=target, overwrite=overwrite))
    return Plan(ops=ops, mode=mode, notes=notes)