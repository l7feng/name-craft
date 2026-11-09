"""CLI 预览基准：只读、退出码、JSON 输出（在临时目录内验证，不触真实文件）。"""

from __future__ import annotations

import json

from namecraft.cli import main


def _setup(tmp_path, files: list[str]) -> tuple[str, str]:
    target = tmp_path / "files"
    target.mkdir()
    for name in files:
        (target / name).write_text("x", encoding="utf-8")
    rules = tmp_path / "rules.json"
    return str(target), str(rules)


def _write_rules(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def test_preview_shows_new_names_and_writes_nothing(tmp_path, capsys):
    target, rules = _setup(tmp_path, ["a.txt", "b.txt"])
    _write_rules(rules, [{"type": "case", "params": {"mode": "upper"}}])
    code = main(["preview", target, "--rules", rules])
    out = capsys.readouterr().out
    assert code == 0
    assert "A.txt" in out and "B.txt" in out
    assert (tmp_path / "files" / "a.txt").exists()
    assert {p.name for p in (tmp_path / "files").iterdir()} == {"a.txt", "b.txt"}


def test_preview_exit_code_one_on_validation_error(tmp_path, capsys):
    target, rules = _setup(tmp_path, ["a.txt", "b.txt"])
    _write_rules(rules, [{"type": "userinput", "params": {"names": ["same", "same"]}}])
    code = main(["preview", target, "--rules", rules])
    out = capsys.readouterr().out
    assert code == 1
    assert "列表内新路径重复" in out


def test_preview_json_output(tmp_path, capsys):
    target, rules = _setup(tmp_path, ["a.txt"])
    _write_rules(rules, [{"type": "insert", "params": {"what": "x", "where": "prefix"}}])
    code = main(["preview", target, "--rules", rules, "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["rows"][0]["new"] == "xa.txt"
    assert payload["rows"][0]["changed"] is True


def test_bad_rule_file_returns_two(tmp_path, capsys):
    target, rules = _setup(tmp_path, ["a.txt"])
    _write_rules(rules, [{"params": {}}])
    code = main(["preview", target, "--rules", rules])
    assert code == 2
    assert "错误" in capsys.readouterr().err


def test_empty_directory_message(tmp_path, capsys):
    target = tmp_path / "empty"
    target.mkdir()
    rules = tmp_path / "rules.json"
    _write_rules(str(rules), [])
    code = main(["preview", str(target), "--rules", str(rules)])
    assert code == 0
    assert "没有文件" in capsys.readouterr().out