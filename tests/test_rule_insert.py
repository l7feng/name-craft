"""Insert 规则基准：前缀/后缀/位置（1 起、可自右）/锚文本首现。"""


def test_prefix_keeps_extension(run):
    assert run("insert", {"what": "2026-", "where": "prefix"}, ["report.pdf"]) == [
        "2026-report.pdf"
    ]


def test_suffix_keeps_extension(run):
    assert run("insert", {"what": "_v2", "where": "suffix"}, ["intro.txt"]) == ["intro_v2.txt"]


def test_position_is_one_based(run):
    assert run("insert", {"what": "X", "where": "position", "position": 3}, ["abcdef.txt"]) == [
        "abXcdef.txt"
    ]


def test_position_from_right(run):
    # 自右第 2 位 = 插入到倒数第二字符 e 之前
    assert run(
        "insert",
        {"what": "X", "where": "position", "position": 2, "from_right": True},
        ["abcdef.txt"],
    ) == ["abcdeXf.txt"]


def test_after_anchor_first_occurrence(run):
    params = {"what": "_v", "where": "after", "text": " - "}
    assert run("insert", params, ["song - take2 - mix.wav"]) == ["song - _vtake2 - mix.wav"]


def test_missing_anchor_unchanged(run):
    params = {"what": "X", "where": "before", "text": "</>"}
    assert run("insert", params, ["plain.txt"]) == ["plain.txt"]


def test_skip_ext_false_appends_to_full_name(run):
    params = {"what": "_x", "where": "suffix", "skip_ext": False}
    assert run("insert", params, ["a.txt"]) == ["a.txt_x"]