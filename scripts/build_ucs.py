"""从 docs/UCS分类表-8.2.1.tsv 生成 src/namecraft/ucs.py（纯数据模块）。

用法：.venv/Scripts/python scripts/build_ucs.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "UCS分类表-8.2.1.tsv"
TARGET = ROOT / "src" / "namecraft" / "ucs.py"


def main() -> None:
    with open(SOURCE, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    seen: set[str] = set()
    items = []
    for row in rows:
        catid = row["CatID"].strip()
        if not catid or catid in seen:
            raise SystemExit(f"CatID 为空或重复：{catid}")
        seen.add(catid)
        fields = (
            catid,
            row["Category"].strip(),
            row["SubCategory"].strip(),
            row["Category_zh"].strip(),
            row["SubCategory_zh"].strip(),
            row["Synonyms_zh"].strip(),
        )
        items.append("    (" + ", ".join(repr(v) for v in fields) + "),")
    header = (
        '"""UCS 8.2.1 分类数据（纯常量，无 IO）。\n\n'
        "由 scripts/build_ucs.py 从 docs/UCS分类表-8.2.1.tsv 生成，请勿手改。\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "# (CatID, Category, SubCategory, Category_zh, SubCategory_zh, Synonyms_zh)\n"
        "CATEGORIES = (\n"
    )
    footer = (
        ")\n\n"
        "CATIDS = frozenset(item[0] for item in CATEGORIES)\n"
        "BY_ID = {item[0]: item for item in CATEGORIES}\n"
        "_LOWER = {item[0].lower(): item[0] for item in CATEGORIES}\n\n\n"
        "def canonical(catid: str) -> str | None:\n"
        '    """大小写不敏感地返回标准 CatID；不在表中时返回 None。"""\n'
        "    return _LOWER.get(str(catid or '').strip().lower())\n"
    )
    TARGET.write_text(header + "\n".join(items) + "\n" + footer, encoding="utf-8")
    print(f"写入 {TARGET}（{len(items)} 个 CatID）")


if __name__ == "__main__":
    main()
