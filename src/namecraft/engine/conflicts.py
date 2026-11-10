"""冲突消解与循环换位检测。

后缀格式 ` (n)`（空格＋括号数字，插在扩展名前，n 从 2 起）为 ADR-0001 假设项。
"""

from __future__ import annotations

import os

from .models import FileItem, PreviewRow
from .textutil import split_ext


def _with_suffix(name: str, n: int) -> str:
    base, ext = split_ext(name)
    return f"{base} ({n}){ext}"


def resolve_conflicts(rows: list[PreviewRow], occupied: set[str] | None = None) -> None:
    """就地给冲突新名加递增 (n) 后缀；对列表内互撞与外部占用同口径。"""
    occupied_cf = {os.path.normcase(p) for p in (occupied or set())}
    used: set[str] = set()
    for row in rows:
        if row.status == "skipped":
            used.add(os.path.normcase(row.item.path))
            continue
        candidate = row.new_name
        n = 2
        while True:
            key = os.path.normcase(os.path.join(row.item.folder, candidate))
            if key not in used and key not in occupied_cf:
                break
            candidate = _with_suffix(row.new_name, n)
            n += 1
        row.new_name = candidate
        used.add(os.path.normcase(os.path.join(row.item.folder, candidate)))


def detect_cycles(items: list[FileItem], new_names: list[str]) -> list[list[str]]:
    """检测 a→b、b→a 类循环换位，返回环内原路径列表（执行层用临时名两阶段）。

    仅 marked 且名字有变化的项参与；按 normcase 全路径建映射。
    """
    mapping: dict[str, str] = {}
    for it, nn in zip(items, new_names):
        if it.marked and nn != it.name:
            src = os.path.normcase(it.path)
            dst = os.path.normcase(os.path.join(it.folder, nn))
            if src != dst:  # 纯大小写改名不算环（normcase 后同名）
                mapping[src] = dst
    cycles: list[list[str]] = []
    visited: set[str] = set()
    for start in mapping:
        if start in visited:
            continue
        path: list[str] = []
        pos: dict[str, int] = {}
        node = start
        while node in mapping and node not in visited:
            if node in pos:
                cycles.append(path[pos[node] :])
                break
            pos[node] = len(path)
            path.append(node)
            node = mapping[node]
        visited.update(path)
    return cycles