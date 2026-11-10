"""UCS 命名规则：结构块、CatID 校验、前缀剥离、名单与字符清理。"""

from __future__ import annotations

import pytest


def _params(**over):
    base = {
        "catid": "AIRBlow",
        "fx_mode": "current",
        "creator": "AB",
        "source": "LIB",
    }
    base.update(over)
    return base


def test_builds_all_ucs_blocks(run):
    params = _params(
        catid="gunauto",
        fx_mode="fixed",
        fx_name="Uzi 9mm Rapid Fire",
        creator="TN",
        source="DORY",
        user_category="INT",
        vendor_category="UZI 9mm",
        user_data="MKH8020",
    )
    assert run("ucs", params, ["raw.wav"]) == [
        "GUNAuto-INT_UZI 9mm-Uzi 9mm Rapid Fire_TN_DORY_MKH8020.wav"
    ]


def test_current_name_keeps_extension_and_omits_empty_blocks(run):
    assert run("ucs", _params(), ["Alpha Beta.wav"]) == ["AIRBlow_Alpha Beta_AB_LIB.wav"]
    assert run("ucs", _params(creator="", source=""), ["Alpha.wav"]) == ["AIRBlow_Alpha.wav"]
    assert run("ucs", _params(creator="", source=""), ["Alpha"]) == ["AIRBlow_Alpha"]


def test_strips_existing_category_prefix(run):
    assert run("ucs", _params(strip_existing=True), ["AIRBlow_Old Name.wav"]) == [
        "AIRBlow_Old Name_AB_LIB.wav"
    ]
    assert run("ucs", _params(strip_existing=False), ["AIRBlow_Old Name.wav"]) == [
        "AIRBlow_AIRBlow Old Name_AB_LIB.wav"
    ]


def test_unknown_catid_fails_without_guessing():
    from namecraft.rules import REGISTRY

    with pytest.raises(ValueError, match="未知 CatID"):
        REGISTRY["ucs"](_params(catid="NOTACAT"))


def test_sanitizes_forbidden_chars_and_underscores(run):
    params = _params(catid="AIRBlow", creator="A_B", source="")
    assert run("ucs", params, ["Bad:Name?.wav"]) == ["AIRBlow_Bad Name_A B.wav"]


def test_list_mode_uses_lines_and_falls_back_to_current(run):
    params = _params(fx_mode="list", fx_list="First sound\n\nThird sound")
    assert run("ucs", params, ["a.wav", "b.wav", "c.wav", "d.wav"]) == [
        "AIRBlow_First sound_AB_LIB.wav",
        "AIRBlow_b_AB_LIB.wav",
        "AIRBlow_Third sound_AB_LIB.wav",
        "AIRBlow_d_AB_LIB.wav",
    ]


def test_fixed_mode_empty_falls_back_to_current(run):
    assert run("ucs", _params(fx_mode="fixed", fx_name=""), ["a.wav"]) == [
        "AIRBlow_a_AB_LIB.wav"
    ]
