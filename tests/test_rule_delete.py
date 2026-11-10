"""Delete 规则基准：位置/分隔符起止、保留分隔符、右到左镜像。"""


def test_position_to_count(run):
    params = {"from_mode": "position", "from_value": 1, "until_mode": "count", "until_value": 2}
    assert run("delete", params, ["abcdef.txt"]) == ["cdef.txt"]


def test_delimiter_to_end(run):
    params = {"from_mode": "delimiter", "from_value": "-", "until_mode": "end"}
    assert run("delete", params, ["report-final.txt"]) == ["report.txt"]


def test_delimiter_to_delimiter_inclusive(run):
    params = {"from_mode": "delimiter", "from_value": " - ", "until_mode": "delimiter",
              "until_value": " - "}
    assert run("delete", params, ["song - take2 - mix.wav"]) == ["songmix.wav"]


def test_keep_delimiters(run):
    params = {"from_mode": "delimiter", "from_value": " - ", "until_mode": "delimiter",
              "until_value": " - ", "keep_delimiters": True}
    assert run("delete", params, ["song - take2 - mix.wav"]) == ["song -  - mix.wav"]


def test_right_to_left_keeps_right_four(run):
    # 自右第 5 位到结尾删除 = 保留最右 4 字符（参考版手册示例口径）
    params = {"from_mode": "position", "from_value": 5, "until_mode": "end",
              "right_to_left": True}
    assert run("delete", params, ["abcdefgh.txt"]) == ["efgh.txt"]


def test_missing_from_delimiter_unchanged(run):
    params = {"from_mode": "delimiter", "from_value": "#", "until_mode": "end"}
    assert run("delete", params, ["plain.txt"]) == ["plain.txt"]


def test_missing_until_delimiter_conservative_unchanged(run):
    params = {"from_mode": "delimiter", "from_value": "-", "until_mode": "delimiter",
              "until_value": "#"}
    assert run("delete", params, ["a-b.txt"]) == ["a-b.txt"]