"""冲突消解与循环换位基准。

(n) 后缀格式为 ADR-0001 假设项：扩展名前、空格＋括号、n 从 2 起。
"""

import os

from namecraft.engine.conflicts import detect_cycles, resolve_conflicts
from namecraft.engine.models import FileItem, PreviewRow

FOLDER = os.path.join("C:", "t")


def _row(name, new_name, marked=True):
    return PreviewRow(FileItem(os.path.join(FOLDER, name), marked), new_name)


def test_suffix_starts_at_two_before_extension():
    rows = [_row("a.txt", "same.txt"), _row("b.txt", "same.txt")]
    resolve_conflicts(rows)
    assert [r.new_name for r in rows] == ["same.txt", "same (2).txt"]


def test_suffix_increments_until_free():
    rows = [_row(f"f{i}.txt", "same.txt") for i in range(3)]
    resolve_conflicts(rows, occupied={os.path.join(FOLDER, "same (2).txt")})
    assert [r.new_name for r in rows] == ["same.txt", "same (3).txt", "same (4).txt"]


def test_occupied_external_name_pushed(tmp_path):
    folder = str(tmp_path)
    rows = [PreviewRow(FileItem(os.path.join(folder, "a.txt")), "taken.txt")]
    resolve_conflicts(rows, occupied={os.path.join(folder, "taken.txt")})
    assert rows[0].new_name == "taken (2).txt"


def test_skipped_original_reserves_name(tmp_path):
    folder = str(tmp_path)
    rows = [
        PreviewRow(FileItem(os.path.join(folder, "keep.txt"), marked=False), "keep.txt",
                   status="skipped"),
        PreviewRow(FileItem(os.path.join(folder, "a.txt")), "keep.txt"),
    ]
    resolve_conflicts(rows)
    assert rows[1].new_name == "keep (2).txt"


def test_multi_dot_extension_suffix():
    rows = [_row("a.txt", "x.tar.gz"), _row("b.txt", "x.tar.gz")]
    resolve_conflicts(rows)
    assert rows[1].new_name == "x.tar (2).gz"


def test_cycle_two_files(tmp_path):
    folder = str(tmp_path)
    items = [FileItem(os.path.join(folder, "a.txt")), FileItem(os.path.join(folder, "b.txt"))]
    cycles = detect_cycles(items, ["b.txt", "a.txt"])
    assert len(cycles) == 1
    assert len(cycles[0]) == 2


def test_cycle_three_files(tmp_path):
    folder = str(tmp_path)
    names = ["a.txt", "b.txt", "c.txt"]
    items = [FileItem(os.path.join(folder, n)) for n in names]
    cycles = detect_cycles(items, ["b.txt", "c.txt", "a.txt"])
    assert len(cycles) == 1
    assert len(cycles[0]) == 3


def test_no_cycle_for_linear_chain(tmp_path):
    folder = str(tmp_path)
    names = ["a.txt", "b.txt", "c.txt"]
    items = [FileItem(os.path.join(folder, n)) for n in names]
    assert detect_cycles(items, ["b.txt", "c.txt", "d.txt"]) == []


def test_case_only_rename_is_not_a_cycle(tmp_path):
    # normcase 后同路径：大小写改名不是环，执行层按自身处理
    folder = str(tmp_path)
    items = [FileItem(os.path.join(folder, "a.txt"))]
    assert detect_cycles(items, ["A.txt"]) == []