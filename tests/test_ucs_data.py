"""UCS 分类数据：数量、唯一性、大小写规范化与 TSV 同步。"""

from __future__ import annotations

import csv
from pathlib import Path

from namecraft import ucs

ROOT = Path(__file__).resolve().parents[1]
TSV = ROOT / "docs" / "UCS分类表-8.2.1.tsv"


def test_category_table_shape_and_unique_ids():
    assert len(ucs.CATEGORIES) == 753
    assert len(ucs.CATIDS) == 753
    assert len(ucs.BY_ID) == 753
    assert all(len(item) == 6 and all(isinstance(v, str) for v in item) for item in ucs.CATEGORIES)


def test_canonical_accepts_case_and_whitespace():
    assert ucs.canonical("airblow") == "AIRBlow"
    assert ucs.canonical(" gUNAuto ") == "GUNAuto"
    assert ucs.canonical("FOLYProp") == "FOLYProp"
    assert ucs.canonical("NotACategory") is None
    assert ucs.canonical("") is None
    assert ucs.canonical(None) is None


def test_generated_module_matches_tsv():
    with open(TSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    expected = [
        (
            row["CatID"].strip(),
            row["Category"].strip(),
            row["SubCategory"].strip(),
            row["Category_zh"].strip(),
            row["SubCategory_zh"].strip(),
            row["Synonyms_zh"].strip(),
        )
        for row in rows
    ]
    assert expected == list(ucs.CATEGORIES)
