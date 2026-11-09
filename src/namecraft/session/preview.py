"""预览计算：列目录 → 规则链 → 校验 → 环检测。CLI 与 GUI 共用。"""

from __future__ import annotations

from namecraft.engine.chain import apply_chain
from namecraft.engine.conflicts import detect_cycles
from namecraft.engine.models import FileItem, PreviewRow, Rule
from namecraft.engine.validate import validate
from namecraft.fs import list_files, occupied_paths


def compute_items(
    items: list[FileItem], rules: list[Rule]
) -> tuple[list[PreviewRow], list[list[str]], set[str]]:
    """显式文件列表（拖入/多选）的预览；可与多个目录混批。"""
    names = apply_chain(items, rules)
    occupied = occupied_paths(items)
    rows = validate(items, names, occupied)
    return rows, detect_cycles(items, names), occupied


def compute(
    directory: str, rules: list[Rule]
) -> tuple[list[PreviewRow], list[list[str]], set[str]]:
    return compute_items(list_files(directory), rules)
