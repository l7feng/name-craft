"""架构边界静态断言：engine/rules 不得依赖 IO 与上层。"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "namecraft"

FORBIDDEN = re.compile(
    r"^\s*(?:from|import)\s+namecraft\.(?:fs|session|gui|cli)\b"
    r"|^\s*(?:from|import)\s+namecraft\.engine\.chain\b"
    r"|^\s*(?:from|import)\s+os\.path\b",
    re.MULTILINE,
)


def test_engine_and_rules_have_no_io_or_upward_imports():
    offenders = []
    for layer in ("engine", "rules"):
        for path in (SRC / layer).glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if FORBIDDEN.search(text) and "engine/chain" not in path.as_posix():
                offenders.append(path.name)
    assert offenders == []


def test_engine_has_no_disk_writes():
    for path in (SRC / "engine").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "shutil." not in text and "os.rename" not in text, path.name


def test_fs_is_only_layer_using_scandir():
    users = [
        p.relative_to(SRC).as_posix()
        for p in SRC.rglob("*.py")
        if "os.scandir" in p.read_text(encoding="utf-8")
    ]
    assert users == ["fs/__init__.py"]