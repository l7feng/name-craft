"""执行计划基准：三种冲突口径与覆盖确认。"""

from __future__ import annotations

import os

import pytest

from namecraft.engine.models import FileItem
from namecraft.engine.validate import validate
from namecraft.session.plan import OverwriteNotConfirmed, PlanError, prepare

FOLDER = os.path.join("C:", "t")


def _rows(names, new_names, occupied=None):
    items = [FileItem(os.path.join(FOLDER, n)) for n in names]
    return validate(items, new_names, occupied)


def test_block_mode_rejects_occupied_target():
    rows = _rows(["a.txt"], ["taken.txt"])
    occupied = {os.path.join(FOLDER, "taken.txt")}
    with pytest.raises(PlanError, match="占用"):
        prepare(rows, occupied)


def test_suffix_mode_resolves_and_notes():
    rows = _rows(["a.txt", "b.txt"], ["same.txt", "same.txt"])
    plan = prepare(rows, set(), mode="suffix")
    assert [op.new for op in plan.ops] == [
        os.path.join(FOLDER, "same.txt"),
        os.path.join(FOLDER, "same (2).txt"),
    ]
    assert plan.notes


def test_overwrite_requires_explicit_confirm():
    rows = _rows(["a.txt"], ["taken.txt"])
    occupied = {os.path.join(FOLDER, "taken.txt")}
    with pytest.raises(OverwriteNotConfirmed):
        prepare(rows, occupied, mode="overwrite")


def test_overwrite_confirmed_marks_op():
    rows = _rows(["a.txt"], ["taken.txt"])
    occupied = {os.path.join(FOLDER, "taken.txt")}
    plan = prepare(rows, occupied, mode="overwrite", confirm=occupied)
    assert plan.ops[0].overwrite is True


def test_validation_errors_block_every_mode():
    rows = _rows(["a.txt"], [""])
    with pytest.raises(PlanError, match="校验错误"):
        prepare(rows, set(), mode="suffix")


def test_target_inside_batch_needs_no_overwrite():
    # a→b、b→c：目标是批内源文件，不算外部占用
    rows = _rows(["a.txt", "b.txt"], ["b.txt", "c.txt"])
    occupied = {os.path.join(FOLDER, "a.txt"), os.path.join(FOLDER, "b.txt")}
    plan = prepare(rows, occupied)
    assert len(plan.ops) == 2
    assert not any(op.overwrite for op in plan.ops)


def test_unchanged_rows_produce_no_ops():
    rows = _rows(["a.txt"], ["a.txt"])
    assert prepare(rows, set()).ops == []


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        prepare([], set(), mode="nope")