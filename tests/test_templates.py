"""自定义规则模板：同名覆盖、删除、损坏容忍与上限。"""

from __future__ import annotations

import json

import pytest

from namecraft.gui import templates


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("NAMECRAFT_HOME", str(home))
    return home


RULES = [
    {"type": "cleanup", "params": {"fix_spaces": True}},
    {"type": "case", "params": {"mode": "upper"}, "enabled": False},
]


def test_save_load_upsert_by_name_and_delete():
    saved = templates.save("音效归档", RULES)
    assert saved["name"] == "音效归档"
    assert saved["rules"][1]["enabled"] is False
    assert templates.load() == [saved]

    updated = templates.save(" 音效归档 ", [{"type": "insert", "params": {"what": "x"}}])
    assert updated["id"] == saved["id"]  # 同名覆盖而非新增
    items = templates.load()
    assert len(items) == 1
    assert items[0]["rules"][0]["type"] == "insert"

    remaining = templates.delete(saved["id"])
    assert remaining == []
    assert templates.load() == []
    with pytest.raises(KeyError):
        templates.delete(saved["id"])


def test_save_keeps_latest_first_and_supports_id_rename():
    first = templates.save("一", RULES)
    second = templates.save("二", RULES)
    assert [t["name"] for t in templates.load()] == ["二", "一"]
    renamed = templates.save("一号", RULES, first["id"])
    assert renamed["id"] == first["id"]
    assert [t["name"] for t in templates.load()] == ["一号", "二"]
    assert second["id"] != first["id"]


def test_rejects_empty_name_empty_rules_and_over_limit():
    with pytest.raises(ValueError):
        templates.save("  ", RULES)
    with pytest.raises(ValueError):
        templates.save("x" * (templates.MAX_NAME + 1), RULES)
    with pytest.raises(ValueError):
        templates.save("空", [])
    too_many = [{"type": "case", "params": {}}] * (templates.MAX_RULES + 1)
    with pytest.raises(ValueError):
        templates.save("超限", too_many)


def test_load_tolerates_corrupt_file_and_bad_items():
    templates.save("有效", RULES)
    path = templates.templates_path()
    path.write_text("{not json", encoding="utf-8")
    assert templates.load() == []

    path.write_text(
        json.dumps(
            {
                "version": 1,
                "templates": [
                    {"name": "", "rules": RULES},
                    {"name": "无规则", "rules": []},
                    {"id": "a", "name": "好", "rules": [{"type": "case"}, "坏"]},
                    {"id": "a", "name": "重复", "rules": [{"type": "case"}]},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    items = templates.load()
    assert len(items) == 1
    assert items[0]["name"] == "好"
    assert items[0]["rules"] == [{"type": "case", "enabled": True, "params": {}}]
