"""文件系统适配层：namecraft 唯一允许做磁盘 IO 的层。

S2 只实现只读枚举与占用扫描；执行/回滚落盘在 S3 于本层扩展。
engine 与 rules 不得 import 本包（tests/test_architecture.py 静态断言）。
"""

from __future__ import annotations

import os

from namecraft.engine.models import FileItem


def list_files(directory: str, *, include_folders: bool = False) -> list[FileItem]:
    """只读枚举目录直接子项（不递归），按名称字典序。

    首期只处理文件；include_folders=True 时文件夹排在文件之后
    （父文件夹须晚于内容处理的对齐口径，S3 递归时生效）。
    """
    entries = []
    with os.scandir(directory) as it:
        for e in it:
            if e.is_file() or (include_folders and e.is_dir()):
                entries.append(e)
    files = sorted((e.path for e in entries if e.is_file()), key=lambda p: os.path.basename(p).lower())
    folders = sorted(
        (e.path for e in entries if not e.is_file()), key=lambda p: os.path.basename(p).lower()
    )
    return [FileItem(p) for p in files + folders]


def occupied_paths(items: list[FileItem]) -> set[str]:
    """扫描各目标目录中已存在、且不属于本批原路径的完整路径集合。"""
    originals = {os.path.normcase(it.path) for it in items}
    occupied: set[str] = set()
    for folder in {it.folder for it in items}:
        try:
            with os.scandir(folder) as it:
                for e in it:
                    p = os.path.normcase(e.path)
                    if p not in originals:
                        occupied.add(e.path)
        except OSError:
            continue
    return occupied