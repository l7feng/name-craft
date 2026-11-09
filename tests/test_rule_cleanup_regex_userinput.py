"""CleanUp / RegEx / UserInput 基准。"""

import pytest


def test_cleanup_brackets_with_fix_spaces(run):
    params = {"brackets": "([", "fix_spaces": True}
    assert run("cleanup", params, ["Track (remix) [final].wav"]) == ["Track.wav"]


def test_cleanup_brackets_without_fix_spaces(run):
    params = {"brackets": "(["}
    assert run("cleanup", params, ["Track (remix) [final].wav"]) == ["Track  .wav"]


def test_cleanup_chars_to_spaces(run):
    assert run("cleanup", {"chars_to_spaces": "_."}, ["a_b.c.txt"]) == ["a b c.txt"]


def test_cleanup_normalize_unicode_space(run):
    assert run("cleanup", {"normalize_space": True}, ["a\u00a0b.txt"]) == ["a b.txt"]


def test_cleanup_split_camel(run):
    assert run("cleanup", {"split_camel": True}, ["trackNameFinal.wav"]) == [
        "track Name Final.wav"
    ]


def test_cleanup_fix_spaces_collapses_and_trims(run):
    params = {"fix_spaces": True}
    assert run("cleanup", params, ["  a   b  .txt"]) == ["a b.txt"]


def test_regex_digit_class(run):
    assert run("regex", {"expression": r"\d+", "replacement": "NUM"}, ["take12.txt"]) == [
        "takeNUM.txt"
    ]


def test_regex_dollar_backreference(run):
    params = {"expression": r"(\w+)-(\w+)", "replacement": "$2-$1"}
    assert run("regex", params, ["john-smith.txt"]) == ["smith-john.txt"]


def test_regex_brace_backreference(run):
    params = {"expression": r"(\w+)-(\w+)", "replacement": "${2}_${1}"}
    assert run("regex", params, ["john-smith.txt"]) == ["smith_john.txt"]


def test_regex_case_insensitive(run):
    params = {"expression": "abc", "replacement": "x", "case_sensitive": False}
    assert run("regex", params, ["ABC.txt"]) == ["x.txt"]


def test_regex_invalid_expression_rejected(run):
    with pytest.raises(ValueError):
        run("regex", {"expression": "("}, ["a.txt"])


def test_userinput_replace_keeps_extension(run):
    params = {"names": ["第一", "第二"]}
    assert run("userinput", params, ["a.txt", "b.txt"]) == ["第一.txt", "第二.txt"]


def test_userinput_surplus_files_unchanged(run):
    params = {"names": ["only"]}
    assert run("userinput", params, ["a.txt", "b.txt"]) == ["only.txt", "b.txt"]


def test_userinput_front(run):
    params = {"names": ["01_", "02_"], "mode": "front"}
    assert run("userinput", params, ["a.txt", "b.txt"]) == ["01_a.txt", "02_b.txt"]


def test_userinput_after(run):
    params = {"names": ["_A", "_B"], "mode": "after"}
    assert run("userinput", params, ["a.txt", "b.txt"]) == ["a_A.txt", "b_B.txt"]


def test_userinput_skip_ext_false(run):
    params = {"names": ["X"], "mode": "after", "skip_ext": False}
    assert run("userinput", params, ["a.txt"]) == ["a.txtX"]