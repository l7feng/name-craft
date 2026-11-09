"""预览计算：列目录 → 规则链 → 校验 → 环检测。CLI 与 GUI 共用。"""

from __future__ import annotations

from namecraft.engine.chain import apply_chain
from namecraft.engine.conflicts import detect_cycles
from namecraft.engine.models import PreviewRow, Rule
from namecraft.engine.validate import validate
from namecraft.fs import list_files, occupied_paths


def compute(
    directory: str, rules: list[Rule]
) -> tuple[list[PreviewRow], list[list[str]], set[str]]:
    items = list_files(directory)
    names = apply_chain(items, rules)
    occupied = occupied_paths(items)
    rows = validate(items, names, occupied)
    return rows, detect_cycles(items, names), occupied
