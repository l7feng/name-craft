"""Rearrange 基准：精确/分隔符/位置切分、$n 模板、右到左。"""


def test_exact_split_swaps_parts(run):
    params = {"split": "exact", "value": ", ", "pattern": "$2 $1"}
    assert run("rearrange", params, ["Smith, John.txt"]) == ["John Smith.txt"]


def test_exact_missing_delimiter_unchanged(run):
    params = {"split": "exact", "value": ", ", "pattern": "$2 $1"}
    assert run("rearrange", params, ["NoComma.txt"]) == ["NoComma.txt"]


def test_delimiter_split_with_multiple_parts(run):
    params = {"split": "delimiters", "value": " - ", "pattern": "$3 - $1 - $2"}
    assert run("rearrange", params, ["song - take2 - mix.wav"]) == ["mix - song - take2.wav"]


def test_positions_split(run):
    params = {"split": "positions", "value": "*|*3", "pattern": "$2$1"}
    assert run("rearrange", params, ["ABCDEF.txt"]) == ["CDEFAB.txt"]


def test_dollar_zero_is_whole_base(run):
    params = {"split": "delimiters", "value": "_", "pattern": "$0 (copy)"}
    assert run("rearrange", params, ["a_b.txt"]) == ["a_b (copy).txt"]


def test_negative_part_index(run):
    params = {"split": "delimiters", "value": "_", "pattern": "$-1_$1"}
    assert run("rearrange", params, ["a_b_c.txt"]) == ["c_a.txt"]


def test_out_of_range_part_becomes_empty(run):
    params = {"split": "delimiters", "value": "_", "pattern": "$5$1"}
    assert run("rearrange", params, ["a_b.txt"]) == ["a.txt"]


def test_right_to_left_reverses_numbering(run):
    params = {"split": "delimiters", "value": "_", "pattern": "$1$2$3", "right_to_left": True}
    assert run("rearrange", params, ["a_b_c.txt"]) == ["cba.txt"]