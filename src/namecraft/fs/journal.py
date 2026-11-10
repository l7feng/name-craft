"""改名日志读写：每条操作一个 JSON，原子写（临时文件 + replace）。

日志结构与状态机见 session/execute.py；本模块只负责落盘与枚举。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .runtime import journals_dir


def path_of(journal_id: str) -> Path:
    return journals_dir() / f"{journal_id}.json"


def write(journal: dict) -> Path:
    target = path_of(journal["id"])
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)
    return target


def load(journal_id: str) -> dict:
    return json.loads(path_of(journal_id).read_text(encoding="utf-8"))


def list_all() -> list[dict]:
    items = []
    for p in journals_dir().glob("*.json"):
        try:
            items.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return sorted(items, key=lambda j: j.get("id", ""), reverse=True)


def latest_done_id() -> str | None:
    for journal in list_all():
        if journal.get("status") == "done":
            return journal.get("id")
    return None