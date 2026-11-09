"""执行与撤销：临时名两阶段、日志先落盘、失败回滚、撤销预检。

为什么两阶段：a→b 且 b→a 的循环换位直接改名会互相踩；统一先改成同目录
临时名再落到目标，循环与链式交换都只需一次遍历。覆盖模式在落目标时用
os.replace（原子替换），被覆盖文件原内容不可恢复，日志如实记录。
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime

from namecraft.fs import journal as journal_store

from .plan import RenameOp

TMP_PREFIX = ".namecraft-tmp-"


class ExecutionError(Exception):
    """执行失败；journal 中保留已完成与回滚情况。"""


class UndoError(Exception):
    """撤销被拒绝或失败。"""


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _new_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)


def _tmp_path(path: str, tag: str) -> str:
    folder, name = os.path.split(path)
    return os.path.join(folder, f"{TMP_PREFIX}{tag}-{name}")


@dataclass
class Journal:
    id: str
    created: str
    status: str  # running / done / failed / partial / undone
    entries: list[dict]
    notes: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created": self.created,
            "status": self.status,
            "entries": self.entries,
            "notes": self.notes,
            "overwritten": self.overwritten,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Journal:
        return cls(
            id=data["id"],
            created=data.get("created", ""),
            status=data.get("status", ""),
            entries=list(data.get("entries", [])),
            notes=list(data.get("notes", [])),
            overwritten=list(data.get("overwritten", [])),
        )


def execute(ops: list, notes: list[str] | None = None) -> Journal:
    """按计划执行改名；返回日志。失败时尽量回滚并把情况写进日志备注。"""
    if not ops:
        raise ExecutionError("没有可执行的操作")
    for op in ops:
        if not os.path.exists(op.old):
            raise ExecutionError(f"源文件不存在：{op.old}")

    journal = Journal(
        id=_new_id(),
        created=_now(),
        status="running",
        entries=[{"old": op.old, "new": op.new, "overwrite": op.overwrite} for op in ops],
        notes=list(notes or []),
    )
    journal_store.write(journal.to_dict())

    staged: list[tuple[int, str, RenameOp]] = []
    finalized: set[int] = set()
    try:
        for i, op in enumerate(ops):
            tmp = _tmp_path(op.old, f"{journal.id}-{i}")
            os.rename(op.old, tmp)
            staged.append((i, tmp, op))
        for i, tmp, op in staged:
            if op.overwrite:
                os.replace(tmp, op.new)
            else:
                os.rename(tmp, op.new)
            finalized.add(i)
    except OSError as error:
        journal.notes.append(f"执行中断：{error}")
        rollback_failed = 0
        for i, tmp, op in staged:
            if i in finalized:
                try:
                    os.rename(op.new, op.old)
                except OSError as e2:
                    rollback_failed += 1
                    journal.notes.append(f"回滚失败：{op.old}（{e2}）")
            else:
                try:
                    os.rename(tmp, op.old)
                except OSError as e2:
                    rollback_failed += 1
                    journal.notes.append(f"回滚失败：{tmp}（{e2}）")
        journal.status = "partial" if rollback_failed else "failed"
        if not rollback_failed:
            journal.notes.append("已回滚，未产生净变更")
        journal_store.write(journal.to_dict())
        raise ExecutionError(f"执行失败，已尽量回滚：{error}") from error

    journal.overwritten = [op.new for i, _, op in staged if i in finalized and op.overwrite]
    if journal.overwritten:
        journal.notes.append(f"覆盖 {len(journal.overwritten)} 个现有文件（原内容不可恢复）")
    journal.status = "done"
    journal_store.write(journal.to_dict())
    return journal


def undo(journal_id: str) -> Journal:
    """撤销一次已完成的改名。只允许撤销最近一次 done 的操作。"""
    journal = Journal.from_dict(journal_store.load(journal_id))
    if journal.status != "done":
        raise UndoError(f"该日志状态为 {journal.status}，不可撤销")
    latest = journal_store.latest_done_id()
    if latest != journal.id:
        raise UndoError("只能撤销最近一次完成的改名")

    problems = []
    for e in journal.entries:
        if not os.path.exists(e["new"]):
            problems.append(f"新路径不存在：{e['new']}")
        elif os.path.normcase(e["old"]) != os.path.normcase(e["new"]) and os.path.exists(
            e["old"]
        ):
            problems.append(f"原路径已被占用：{e['old']}")
    if problems:
        raise UndoError("撤销预检未通过：" + "；".join(problems[:5]))

    staged: list[tuple[str, dict]] = []
    try:
        for i, e in enumerate(journal.entries):
            tmp = _tmp_path(e["new"], f"undo-{journal.id}-{i}")
            os.rename(e["new"], tmp)
            staged.append((tmp, e))
        for tmp, e in staged:
            os.rename(tmp, e["old"])
    except OSError as error:
        for tmp, e in staged:
            try:
                if os.path.exists(tmp):
                    os.rename(tmp, e["new"])
            except OSError as e2:
                journal.notes.append(f"撤销回滚失败：{tmp}（{e2}）")
        journal.status = "partial"
        journal.notes.append(f"撤销中断：{error}")
        journal_store.write(journal.to_dict())
        raise UndoError(f"撤销失败：{error}") from error

    journal.status = "undone"
    journal.notes.append("已撤销")
    if journal.overwritten:
        journal.notes.append("被覆盖的原文件内容不可恢复")
    journal_store.write(journal.to_dict())
    return journal