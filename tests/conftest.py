"""测试夹具：不触盘的规则链执行助手。"""

from __future__ import annotations

import os

import pytest

from namecraft.engine.chain import apply_chain
from namecraft.engine.models import FileItem, Rule

BASE = os.path.join("C:", "t")


def _items(names: list[str], folders: list[str] | None = None) -> list[FileItem]:
    folders = folders or [BASE] * len(names)
    return [FileItem(os.path.join(f, n)) for f, n in zip(folders, names)]


@pytest.fixture
def run():
    """run("insert", {...}, ["a.txt"]) -> 新名列表（单条规则）。"""

    def _run(rule_type: str, params: dict, names: list[str], folders: list[str] | None = None):
        return apply_chain(_items(names, folders), [Rule(rule_type, params)])

    return _run


@pytest.fixture
def run_stack():
    """run_stack([("insert", {...}), ("case", {...})], ["a.txt"]) -> 新名列表。"""

    def _run(rules: list[tuple[str, dict]], names: list[str], folders: list[str] | None = None):
        return apply_chain(_items(names, folders), [Rule(t, p) for t, p in rules])

    return _run