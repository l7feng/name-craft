"""Case 基准：六种模式、片段强制、扩展名覆盖优先级。"""


def test_capitalize_words(run):
    assert run("case", {"mode": "capitalize"}, ["my file name.txt"]) == ["My File Name.txt"]


def test_capitalize_preserve_existing(run):
    assert run("case", {"mode": "capitalize_preserve"}, ["myFile name.txt"]) == [
        "MyFile Name.txt"
    ]


def test_lower_keeps_extension(run):
    assert run("case", {"mode": "lower"}, ["MyFile.TXT"]) == ["myfile.TXT"]


def test_upper_with_ext_case(run):
    params = {"mode": "upper", "ext_case": "lower"}
    assert run("case", params, ["MyFile.TXT"]) == ["MYFILE.txt"]


def test_invert_swapcase(run):
    assert run("case", {"mode": "invert"}, ["aBc.TxT"]) == ["AbC.TxT"]


def test_sentence_mode(run):
    assert run("case", {"mode": "sentence"}, ["hello WORLD.txt"]) == ["Hello world.txt"]


def test_fragments_forced_case_insensitive(run):
    params = {"mode": "none", "fragments": "iPhone,iPad"}
    assert run("case", params, ["iphone ipad.txt"]) == ["iPhone iPad.txt"]


def test_fragments_run_after_mode(run):
    params = {"mode": "lower", "fragments": "iPhone"}
    assert run("case", params, ["IPHONE NOTES.txt"]) == ["iPhone notes.txt"]


def test_ext_case_overrides_everything(run):
    params = {"mode": "upper", "ext_case": "lower", "fragments": "TXT"}
    assert run("case", params, ["a.TXT"]) == ["A.txt"]