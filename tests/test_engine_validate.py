"""校验基准：四项检查（重复/非法名/占用/超长）与 skipped 行为。"""

import os

from namecraft.engine.models import FileItem
from namecraft.engine.validate import validate

FOLDER = os.path.join("C:", "t")


def _rows(names, new_names, occupied=None):
    items = [FileItem(os.path.join(FOLDER, n)) for n in names]
    return validate(items, new_names, occupied)


def test_empty_name_error():
    rows = _rows(["a.txt"], [""])
    assert rows[0].status == "error"
    assert "新名为空" in rows[0].reasons[0]


def test_forbidden_char_error():
    rows = _rows(["a.txt"], ["a:b.txt"])
    assert rows[0].status == "error"
    assert any("禁用字符" in r for r in rows[0].reasons)


def test_reserved_name_error():
    rows = _rows(["a.txt"], ["CON.txt"])
    assert any("保留名" in r for r in rows[0].reasons)


def test_trailing_dot_error():
    rows = _rows(["a.txt"], ["a.txt."])
    assert any("结尾" in r for r in rows[0].reasons)


def test_duplicate_within_batch_case_insensitive():
    rows = _rows(["a.txt", "b.txt"], ["same.txt", "SAME.txt"])
    assert all(r.status == "error" for r in rows)
    assert all(any("重复" in x for x in r.reasons) for r in rows)


def test_occupied_target_error():
    rows = _rows(["a.txt"], ["taken.txt"], occupied={os.path.join(FOLDER, "taken.txt")})
    assert any("占用" in r for r in rows[0].reasons)


def test_too_long_path_error():
    long_name = "x" * 260 + ".txt"
    rows = _rows(["a.txt"], [long_name])
    assert any("260" in r for r in rows[0].reasons)


def test_valid_rows_ok():
    rows = _rows(["a.txt"], ["b.txt"])
    assert rows[0].status == "ok"
    assert rows[0].changed is True


def test_unmarked_row_skipped():
    items = [FileItem(os.path.join(FOLDER, "a.txt"), marked=False)]
    rows = validate(items, ["ignored.txt"])
    assert rows[0].status == "skipped"
    assert rows[0].new_name == "a.txt"