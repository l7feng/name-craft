"""Remove / Replace 基准：多串、出现位置、通配符、串行替换语义。"""


def test_remove_all_occurrences_case_insensitive(run):
    params = {"text": "the ", "case_sensitive": False}
    assert run("remove", params, ["The Cat in the Hat.txt"]) == ["Cat in Hat.txt"]


def test_remove_last_occurrence(run):
    assert run("remove", {"text": "a", "occurrences": "last"}, ["aaaa.txt"]) == ["aaa.txt"]


def test_remove_wildcard(run):
    params = {"text": "_0?", "wildcards": True}
    assert run("remove", params, ["track_07_final.wav"]) == ["track_final.wav"]


def test_remove_multi_strings(run):
    assert run("remove", {"text": "a*|*c"}, ["a-b-c.txt"]) == ["-b-.txt"]


def test_remove_case_sensitive_default(run):
    assert run("remove", {"text": "the "}, ["The cat.txt"]) == ["The cat.txt"]


def test_replace_serial_pairs_give_reference_result(run):
    # 串行语义：A→B 后 B→A，ABBA 变 AAAA（对齐参考版已知行为，S1 已记录）
    params = {"find": "A*|*B", "replace": "B*|*A"}
    assert run("replace", params, ["ABBA.txt"]) == ["AAAA.txt"]


def test_replace_paired_lists(run):
    params = {"find": "one*|*two", "replace": "1*|*2"}
    assert run("replace", params, ["one two.txt"]) == ["1 2.txt"]


def test_extra_find_replaced_by_empty(run):
    params = {"find": "1*|*2*|*3", "replace": "a"}
    assert run("replace", params, ["123.txt"]) == ["a.txt"]


def test_replace_first_occurrence_only(run):
    params = {"find": "a", "replace": "b", "occurrences": "first"}
    assert run("replace", params, ["aaa.txt"]) == ["baa.txt"]


def test_replace_wildcard(run):
    params = {"find": "[0-9][0-9][0-9]", "replace": "NUM", "wildcards": True}
    assert run("replace", params, ["IMG_001.jpg"]) == ["IMG_NUM.jpg"]


def test_replace_skip_ext_false_touches_extension(run):
    params = {"find": ".", "replace": "_", "skip_ext": False}
    assert run("replace", params, ["a.b.txt"]) == ["a_b_txt"]