"""Serialize 基准：十进制/字母两套进制、补位、重复、步进、三种重置。"""

import pytest


def _names(n: int) -> list[str]:
    return [f"f{i:02d}.txt" for i in range(n)]


def test_decimal_suffix_sequence(run):
    assert run("serialize", {}, ["a.txt", "b.txt", "c.txt"]) == ["a1.txt", "b2.txt", "c3.txt"]


def test_decimal_prefix_padded(run):
    params = {"where": "prefix", "pad": 3}
    assert run("serialize", params, ["a.txt", "b.txt"]) == ["001a.txt", "002b.txt"]


def test_replace_mode_emits_token_only(run):
    assert run("serialize", {"where": "replace", "start": 10, "step": 5}, ["a.txt", "b.txt"]) == [
        "10.txt",
        "15.txt",
    ]


def test_letters_sequence_boundaries(run):
    # 1..26 a..z，27 ba，52 bz，53 ca
    out = run("serialize", {"where": "replace", "system": "letters"}, _names(53))
    assert out[0] == "a.txt"
    assert out[25] == "z.txt"
    assert out[26] == "ba.txt"
    assert out[51] == "bz.txt"
    assert out[52] == "ca.txt"


def test_letters_length_three_start(run):
    # 676 = zz 收尾长度 2 区，677 = baa
    nums = {"start": 676, "where": "replace", "system": "letters"}
    assert run("serialize", nums, ["a.txt", "b.txt"]) == ["zz.txt", "baa.txt"]


def test_letters_padded_base26(run):
    params = {"where": "replace", "system": "letters", "pad": 3}
    assert run("serialize", params, ["a.txt", "b.txt"]) == ["aaa.txt", "aab.txt"]


def test_repeat_holds_value(run):
    params = {"where": "replace", "repeat": 2}
    out = run("serialize", params, ["a.txt", "b.txt", "c.txt", "d.txt"])
    assert out == ["1.txt", "1.txt", "2.txt", "2.txt"]


def test_reset_every(run):
    params = {"where": "replace", "reset_every": 2}
    out = run("serialize", params, ["a.txt", "b.txt", "c.txt", "d.txt"])
    assert out == ["1.txt", "2.txt", "1.txt", "2.txt"]


def test_reset_folder(run):
    params = {"where": "replace", "reset_folder": True}
    folders = ["C:/a", "C:/a", "C:/b"]
    out = run("serialize", params, ["x.txt", "y.txt", "z.txt"], folders)
    assert out == ["1.txt", "2.txt", "1.txt"]


def test_reset_name(run):
    params = {"where": "replace", "reset_name": True}
    out = run("serialize", params, ["same.txt", "same.txt", "other.txt"])
    assert out == ["1.txt", "2.txt", "1.txt"]


def test_invalid_start_rejected(run):
    with pytest.raises(ValueError):
        run("serialize", {"start": 0}, ["a.txt"])