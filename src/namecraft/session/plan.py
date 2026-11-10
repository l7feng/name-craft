"""执行计划：预览行 → 改名操作，落实冲突口径与确认式覆盖。

三种模式：
- block（默认）：任何校验错误或目标被占即拒绝，不自动改口径。
- suffix：先按 ` (n)` 后缀消解冲突，再生成操作。
- overwrite：目标被占时需用户在 `confirm` 中逐项给出目标路径，否则拒绝；
  确认后执行层用 os.replace 覆盖，日志记录被覆盖对象（不可恢复）。
"""

from __future__ import annotations

import os
from collections import Counter
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


def _occupancy(rows: list[PreviewRow], occupied: set[str] | None) -> tuple[set[str], set[str]]:
    """返回（外部占用键集合, 本批改名后仍留在原位的文件键集合），均已 normcase。"""
    occupied_cf = {os.path.normcase(p) for p in (occupied or set())}
    batch_sources = {os.path.normcase(r.item.path) for r in rows}
    vacated = {
        os.path.normcase(r.item.path) for r in rows if r.status == "ok" and r.changed
    }
    occupied_cf -= vacated  # 本批会腾出的源文件不再算占用
    return occupied_cf, batch_sources - vacated


def blocked_targets(rows: list[PreviewRow], occupied: set[str] | None = None) -> list[str]:
    """会撞上现有文件的目标路径（不考虑 confirm）；GUI 用它先收集待确认清单。

    包含已被校验标错的行：覆盖模式下，"重复/占用"这类错误正是要靠逐项确认消解的。
    """
    occupied_cf, staying = _occupancy(rows, occupied)
    result = []
    for row in rows:
        if row.status == "skipped" or not row.changed:
            continue
        key = os.path.normcase(row.new_path)
        if key in occupied_cf or key in staying:
            result.append(row.new_path)
    return result


def _only_fixable(row: PreviewRow) -> bool:
    """该行的错误是否全部属于覆盖/后缀可消解的类型。"""
    return bool(row.reasons) and all(
        any(x.startswith(p) for p in _FIXABLE) for x in row.reasons
    )


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
        errors = [r for r in errors if not _only_fixable(r)]
    if mode == "overwrite":
        # 覆盖只能消解“目标撞上现有文件”的错误；两个改动行抢同一个新名仍拒绝
        blocked_cf = {
            os.path.normcase(p) for p in blocked_targets(rows, occupied)
        }
        target_count = Counter(
            os.path.normcase(r.new_path)
            for r in rows
            if r.status != "skipped" and r.changed
        )
        for row in rows:
            key = os.path.normcase(row.new_path)
            if (
                row.status == "error"
                and _only_fixable(row)
                and key in blocked_cf
                and target_count[key] == 1
            ):
                row.status = "ok"
                row.reasons = []
        errors = [r for r in rows if r.status == "error"]
    if errors:
        detail = "；".join(f"{r.item.name}：{'、'.join(r.reasons)}" for r in errors[:5])
        raise PlanError(f"存在 {len(errors)} 项校验错误，不能执行：{detail}")

    notes: list[str] = []
    if mode == "suffix":
        before = [r.new_name for r in rows]
        # 除外部占用外，本批不改名的文件也会留在原地，必须一并避开
        _, staying = _occupancy(rows, occupied)
        resolve_conflicts(rows, {p for p in (occupied or set())} | staying)
        rows = validate(
            [r.item for r in rows], [r.new_name for r in rows], occupied
        )
        renamed = sum(1 for r, b in zip(rows, before) if r.new_name != b)
        if renamed:
            notes.append(f"按 (n) 后缀消解 {renamed} 处冲突")

    blocked = blocked_targets(rows, occupied)
    if blocked and mode != "overwrite":
        raise PlanError(f"目标被现有文件占用：{blocked[0]}")
    confirm_cf = {os.path.normcase(p) for p in confirm}
    unconfirmed = [p for p in blocked if os.path.normcase(p) not in confirm_cf]
    if unconfirmed:
        detail = "；".join(unconfirmed[:5])
        raise OverwriteNotConfirmed(f"覆盖需逐项确认：{detail}")
    blocked_cf = {os.path.normcase(p) for p in blocked}

    ops: list[RenameOp] = []
    for row in rows:
        if row.status != "ok" or not row.changed:
            continue
        target = row.new_path
        ops.append(
            RenameOp(
                old=row.item.path,
                new=target,
                overwrite=os.path.normcase(target) in blocked_cf,
            )
        )
    return Plan(ops=ops, mode=mode, notes=notes)