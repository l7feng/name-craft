"""Extension / Strip 基准。"""


def test_extension_replace(run):
    assert run("extension", {"new_ext": "txt"}, ["photo.jpeg"]) == ["photo.txt"]


def test_extension_leading_dot_tolerated(run):
    assert run("extension", {"new_ext": ".mp3"}, ["track.wav"]) == ["track.mp3"]


def test_extension_append(run):
    assert run("extension", {"new_ext": "bak", "append": True}, ["track.wav"]) == [
        "track.wav.bak"
    ]


def test_extension_remove(run):
    assert run("extension", {"new_ext": ""}, ["a.txt"]) == ["a"]


def test_extension_case_upper(run):
    assert run("extension", {"new_ext": "mp3", "case": "upper"}, ["a.wav"]) == ["a.MP3"]


def test_strip_english(run):
    assert run("strip", {"english": True}, ["abc123.txt"]) == ["123.txt"]


def test_strip_digits(run):
    assert run("strip", {"digits": True}, ["abc123.txt"]) == ["abc.txt"]


def test_strip_symbols(run):
    # 中划线/下划线属于 Unicode P 类；扩展名的点受 skip_ext 保护
    assert run("strip", {"symbols": True}, ["a-b_c.txt"]) == ["abc.txt"]


def test_strip_brackets(run):
    assert run("strip", {"brackets": True}, ["[abc]{def}.txt"]) == ["abcdef.txt"]


def test_strip_except_selected_keeps_digits_only(run):
    params = {"digits": True, "except_selected": True}
    assert run("strip", params, ["abc123def456"]) == ["123456"]


def test_strip_nothing_selected_unchanged(run):
    assert run("strip", {}, ["unchanged.txt"]) == ["unchanged.txt"]


def test_strip_custom_set(run):
    assert run("strip", {"custom": "xyz"}, ["axbyc.txt"]) == ["abc.txt"]