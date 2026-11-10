"""新名校验：重复、禁用字符/非法名、目标占用、超长（对齐参考版四项）。"""

from __future__ import annotations

import os

from .models import FileItem, PreviewRow

FORBIDDEN = '\\/:*?"<>|'
MAX_PATH = 260
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {
    f"LPT{i}" for i in range(1, 10)
}


def name_errors(name: str) -> list[str]:
    """单个文件名的非法性检查（不含路径长度与占用）。"""
    reasons = []
    if not name:
        return ["新名为空"]
    if any(c in FORBIDDEN for c in name):
        reasons.append("含禁用字符 \\/:*?\"<>|")
    if any(ord(c) < 32 for c in name):
        reasons.append("含控制字符")
    base = name.split(".")[0].upper()
    if base in _RESERVED:
        reasons.append(f"Windows 保留名 {base}")
    if name != name.rstrip(" ."):
        reasons.append("结尾为空格或点（Windows 无法表示）")
    return reasons


def validate(
    items: list[FileItem], new_names: list[str], occupied: set[str] | None = None
) -> list[PreviewRow]:
    """occupied＝目标盘上已存在、且不在本批 marked 原路径中的完整路径集合。"""
    occupied_cf = {os.path.normcase(p) for p in (occupied or set())}
    rows: list[PreviewRow] = []
    seen: dict[str, int] = {}
    for it, nn in zip(items, new_names):
        if not it.marked:
            rows.append(PreviewRow(it, it.name, status="skipped"))
            continue
        key = os.path.normcase(os.path.join(it.folder, nn))
        seen[key] = seen.get(key, 0) + 1
        rows.append(PreviewRow(it, nn))
    for row in rows:
        if row.status == "skipped":
            continue
        reasons = name_errors(row.new_name)
        key = os.path.normcase(row.new_path)
        if seen[key] > 1:
            reasons.append("列表内新路径重复")
        if key in occupied_cf:
            reasons.append("目标已被现有文件占用")
        if len(row.new_path) > MAX_PATH:
            reasons.append(f"路径超过 {MAX_PATH} 字符")
        if reasons:
            row.status = "error"
            row.reasons = reasons
    return rows