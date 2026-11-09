"""GUI 桥接与设置：文件选择起始目录、预览、执行、覆盖确认、撤销、日志。"""

from __future__ import annotations

import os
import sys
import types

import pytest

from namecraft.gui import settings
from namecraft.gui.bridge import Bridge, first_existing_dir, to_rules
from namecraft.gui.schema import RULE_META, defaults


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("NAMECRAFT_HOME", str(home))
    return home


def _setup(tmp_path, files: dict[str, str]) -> str:
    target = tmp_path / "files"
    target.mkdir()
    for name, content in files.items():
        (target / name).write_text(content, encoding="utf-8")
    return str(target)


def _payload(folder, rules, mode="block"):
    return {"folder": folder, "rules": rules, "mode": mode}


USERINPUT_TAKEN = [{"type": "userinput", "params": {"names": ["taken"]}}]


def test_first_existing_dir_prefers_current_then_fallback(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    assert first_existing_dir(str(real), str(other)) == str(real)
    # 无效路径逐级回退到仍存在的父级
    assert first_existing_dir(str(tmp_path / "missing" / "deep" / "x.txt"), str(other)) == str(tmp_path)
    assert first_existing_dir(str(tmp_path / "real" / "file.txt"), "") == str(real)
    # 当前输入为空时才用该用途上次位置
    assert first_existing_dir("", str(other)) == str(other)
    assert first_existing_dir("", "") == ""


def test_every_rule_has_gui_meta_and_usable_defaults():
    from namecraft.engine.models import Ctx
    from namecraft.rules import REGISTRY

    assert {m["type"] for m in RULE_META} == set(REGISTRY)
    ctx = Ctx(index=0, path=os.path.join("C:", "t", "Sample 01.txt"), folder=os.path.join("C:", "t"), total=1)
    for rule_type in REGISTRY:
        params = defaults(rule_type)
        fn = REGISTRY[rule_type](params)
        assert isinstance(fn("Sample 01.txt", ctx), str), rule_type


def test_to_rules_rejects_unknown_type_and_bad_shape():
    with pytest.raises(ValueError):
        to_rules([{"type": "nope"}])
    with pytest.raises(TypeError):
        to_rules({"type": "case"})
    assert to_rules(None) == []


def test_bootstrap_exposes_settings_rules_and_modes():
    res = Bridge().bootstrap()
    assert res["ok"] is True
    assert res["version"]
    assert len(res["modes"]) == 3
    assert {m["type"] for m in res["rules"]} == {m["type"] for m in RULE_META}


def test_preview_returns_rows_and_persists_settings(tmp_path):
    folder = _setup(tmp_path, {"a.txt": "x", "b.txt": "x"})
    bridge = Bridge()
    res = bridge.preview(_payload(folder, [{"type": "case", "params": {"mode": "upper"}}]))
    assert res["ok"] is True
    assert res["summary"] == {"total": 2, "changed": 2, "errors": 0}
    assert [r["new"] for r in res["rows"]] == ["A.txt", "B.txt"]
    saved = settings.load()
    assert saved["folder"] == folder
    assert saved["rules"][0]["type"] == "case"


def test_preview_reports_missing_folder_and_bad_rule(tmp_path):
    bridge = Bridge()
    assert bridge.preview(_payload(str(tmp_path / "nope"), []))["ok"] is False
    folder = _setup(tmp_path, {"a.txt": "x"})
    res = bridge.preview(_payload(folder, [{"type": "regex", "params": {"expression": "["}}]))
    assert res["ok"] is False
    assert "无效表达式" in res["error"]


def test_execute_block_mode_writes_and_journal_lists_undoable(tmp_path):
    folder = _setup(tmp_path, {"a.txt": "a", "b.txt": "b"})
    bridge = Bridge()
    rules = [{"type": "insert", "params": {"what": "x", "where": "prefix"}}]
    res = bridge.execute(_payload(folder, rules))
    assert res["ok"] is True
    assert res["count"] == 2
    assert sorted(os.listdir(folder)) == ["xa.txt", "xb.txt"]
    listed = bridge.journals()
    assert listed["journals"][0]["undoable"] is True

    undone = bridge.undo(res["journal"]["id"])
    assert undone["ok"] is True
    assert sorted(os.listdir(folder)) == ["a.txt", "b.txt"]
    assert bridge.journals()["journals"][0]["status"] == "undone"


def test_execute_overwrite_needs_per_item_confirm(tmp_path):
    folder = _setup(tmp_path, {"a.txt": "A", "taken.txt": "T"})
    bridge = Bridge()
    blocked = bridge.execute(_payload(folder, USERINPUT_TAKEN, mode="overwrite"))
    assert blocked["ok"] is False
    assert blocked["kind"] == "overwrite"
    assert blocked["needConfirm"] == [os.path.join(folder, "taken.txt")]
    assert (tmp_path / "files" / "taken.txt").read_text(encoding="utf-8") == "T"

    done = bridge.execute(
        _payload(folder, USERINPUT_TAKEN, mode="overwrite")
        | {"confirm": blocked["needConfirm"]}
    )
    assert done["ok"] is True
    assert done["journal"]["overwritten"] == [os.path.join(folder, "taken.txt")]
    assert not (tmp_path / "files" / "a.txt").exists()
    assert (tmp_path / "files" / "taken.txt").read_text(encoding="utf-8") == "A"


def test_execute_refuses_validation_errors(tmp_path):
    folder = _setup(tmp_path, {"a.txt": "x"})
    bridge = Bridge()
    res = bridge.execute(_payload(folder, [{"type": "userinput", "params": {"names": ["a<b"]}}]))
    assert res["ok"] is False
    assert "校验错误" in res["error"]


def test_undo_rejects_older_journal(tmp_path):
    folder = _setup(tmp_path, {"a.txt": "x"})
    bridge = Bridge()
    rules = [{"type": "insert", "params": {"what": "x", "where": "prefix"}}]
    first = bridge.execute(_payload(folder, rules))
    bridge.execute(_payload(folder, rules))
    res = bridge.undo(first["journal"]["id"])
    assert res["ok"] is False
    assert "最近一次" in res["error"]


def test_save_settings_merges_and_tolerates_corruption(tmp_path):
    settings.save({"folder": "D:/a", "rules": [], "mode": "suffix", "lastFolders": {"target": "D:/a"}})
    settings.save({"lastFolders": {"other": "D:/b"}})
    saved = settings.load()
    assert saved["mode"] == "suffix"
    assert saved["lastFolders"] == {"target": "D:/a", "other": "D:/b"}

    path = settings.settings_path()
    with open(path, "w", encoding="utf-8") as f:
        f.write("{not json")
    assert settings.load()["mode"] == "block"


class _FakeWindow:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def create_file_dialog(self, kind, directory=None):
        self.calls.append({"kind": kind, "directory": directory})
        return self.result


def test_pick_folder_passes_current_directory_and_remembers(tmp_path, monkeypatch):
    fake_module = types.SimpleNamespace(FOLDER_DIALOG=20)
    monkeypatch.setitem(sys.modules, "webview", fake_module)
    current = tmp_path / "current"
    current.mkdir()
    chosen = tmp_path / "chosen"
    chosen.mkdir()
    window = _FakeWindow((str(chosen),))
    bridge = Bridge(window_getter=lambda: window)

    res = bridge.pick_folder(str(current), "target")
    assert res == {"ok": True, "path": str(chosen)}
    assert window.calls[0]["kind"] == 20
    assert window.calls[0]["directory"] == str(current)
    assert settings.load()["lastFolders"]["target"] == str(chosen)

    # 当前输入无效时，用该用途上次成功位置作起始目录
    window2 = _FakeWindow(())
    bridge2 = Bridge(window_getter=lambda: window2)
    res = bridge2.pick_folder("", "target")
    assert res["path"] == ""
    assert window2.calls[0]["directory"] == str(chosen)
