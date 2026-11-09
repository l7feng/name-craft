"""执行与撤销基准：真实临时目录内的两阶段改名、日志与撤销预检。"""

from __future__ import annotations

import pytest

from namecraft.fs import journal as journal_store
from namecraft.session.execute import ExecutionError, UndoError, execute, undo
from namecraft.session.plan import RenameOp


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("NAMECRAFT_HOME", str(tmp_path / "home"))


def _touch(path, text="x"):
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_execute_renames_and_writes_journal(tmp_path):
    a = tmp_path / "a.txt"
    _touch(a, "content-a")
    ops = [RenameOp(str(a), str(tmp_path / "b.txt"))]
    journal = execute(ops)
    assert journal.status == "done"
    assert not a.exists()
    assert (tmp_path / "b.txt").read_text(encoding="utf-8") == "content-a"
    stored = journal_store.load(journal.id)
    assert stored["status"] == "done"
    assert stored["entries"][0]["new"] == str(tmp_path / "b.txt")


def test_cycle_rename_uses_two_phase(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    _touch(a, "A")
    _touch(b, "B")
    ops = [RenameOp(str(a), str(b)), RenameOp(str(b), str(a))]
    execute(ops)
    assert a.read_text(encoding="utf-8") == "B"
    assert b.read_text(encoding="utf-8") == "A"


def test_undo_restores_names_and_content(tmp_path):
    a = tmp_path / "a.txt"
    _touch(a, "A")
    journal = execute([RenameOp(str(a), str(tmp_path / "b.txt"))])
    undo(journal.id)
    assert a.read_text(encoding="utf-8") == "A"
    assert not (tmp_path / "b.txt").exists()
    assert journal_store.load(journal.id)["status"] == "undone"


def test_undo_precheck_blocks_when_new_missing(tmp_path):
    a = tmp_path / "a.txt"
    _touch(a, "A")
    journal = execute([RenameOp(str(a), str(tmp_path / "b.txt"))])
    (tmp_path / "b.txt").unlink()
    with pytest.raises(UndoError, match="预检未通过"):
        undo(journal.id)
    assert not a.exists()


def test_undo_only_latest_done(tmp_path):
    a = tmp_path / "a.txt"
    _touch(a, "A")
    first = execute([RenameOp(str(a), str(tmp_path / "b.txt"))])
    second = execute([RenameOp(str(tmp_path / "b.txt"), str(tmp_path / "c.txt"))])
    with pytest.raises(UndoError, match="最近一次"):
        undo(first.id)
    undo(second.id)
    undo(first.id)
    assert a.exists()


def test_execute_refuses_missing_source(tmp_path):
    ops = [RenameOp(str(tmp_path / "ghost.txt"), str(tmp_path / "b.txt"))]
    with pytest.raises(ExecutionError, match="源文件不存在"):
        execute(ops)


def test_overwrite_replaces_target_and_records_victim(tmp_path):
    src = tmp_path / "a.txt"
    victim = tmp_path / "taken.txt"
    _touch(src, "new")
    _touch(victim, "old")
    journal = execute([RenameOp(str(src), str(victim), overwrite=True)])
    assert victim.read_text(encoding="utf-8") == "new"
    assert journal.overwritten == [str(victim)]
    undo(journal.id)
    assert src.read_text(encoding="utf-8") == "new"
    assert not victim.exists()
    assert any("不可恢复" in n for n in journal_store.load(journal.id)["notes"])


def test_empty_ops_rejected(tmp_path):
    with pytest.raises(ExecutionError):
        execute([])