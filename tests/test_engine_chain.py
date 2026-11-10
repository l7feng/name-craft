"""规则链基准：栈序、禁用规则、未标记文件、未知类型。"""

import os

import pytest

from namecraft.engine.chain import apply_chain
from namecraft.engine.models import FileItem, Rule

FOLDER = os.path.join("C:", "t")


def test_rules_apply_in_stack_order(run_stack):
    rules = [("insert", {"what": "x", "where": "prefix"}), ("case", {"mode": "upper"})]
    assert run_stack(rules, ["a.txt"]) == ["XA.txt"]


def test_disabled_rule_skipped():
    items = [FileItem(os.path.join(FOLDER, "a.txt"))]
    rules = [Rule("insert", {"what": "x", "where": "prefix"}, enabled=False)]
    assert apply_chain(items, rules) == ["a.txt"]


def test_unmarked_item_unchanged(run_stack):
    items = [FileItem(os.path.join(FOLDER, "keep.txt"), marked=False)]
    out = apply_chain(items, [Rule("case", {"mode": "upper"})])
    assert out == ["keep.txt"]


def test_unmarked_not_counted_in_serialize_index():
    items = [
        FileItem(os.path.join(FOLDER, "skip.txt"), marked=False),
        FileItem(os.path.join(FOLDER, "a.txt")),
    ]
    out = apply_chain(items, [Rule("serialize", {"where": "replace"})])
    assert out == ["skip.txt", "1.txt"]


def test_unknown_rule_type_raises():
    items = [FileItem(os.path.join(FOLDER, "a.txt"))]
    with pytest.raises(ValueError):
        apply_chain(items, [Rule("nope", {})])