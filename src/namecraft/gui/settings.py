"""本机 GUI 设置：目录记忆、规则栈、冲突口径。

存放在 %LOCALAPPDATA%/namecraft/settings.json（可用 NAMECRAFT_HOME 覆盖），
与改名日志同目录。读取时容忍缺字段与损坏文件；写入走临时文件 + os.replace，
避免半截文件。目录记忆按用途分键，当前只有 "target"。
"""

from __future__ import annotations

import json
import os

from namecraft.fs.runtime import settings_path

DEFAULTS = {
    "folder": "",
    "rules": [],
    "mode": "block",
    "lastFolders": {},
}


def _clean(data) -> dict:
    if not isinstance(data, dict):
        return dict(DEFAULTS)
    result = dict(DEFAULTS)
    result["folder"] = str(data.get("folder", "") or "")
    result["mode"] = str(data.get("mode", "block") or "block")
    rules = data.get("rules")
    result["rules"] = rules if isinstance(rules, list) else []
    folders = data.get("lastFolders")
    result["lastFolders"] = folders if isinstance(folders, dict) else {}
    return result


def load() -> dict:
    path = settings_path()
    try:
        with open(path, encoding="utf-8") as f:
            return _clean(json.load(f))
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save(payload: dict) -> dict:
    """合并写入：只覆盖 payload 中出现的键，保留其余记忆。"""
    current = load()
    incoming = _clean({**current, **(payload or {})})
    if isinstance(payload, dict) and isinstance(payload.get("lastFolders"), dict):
        incoming["lastFolders"] = {**current["lastFolders"], **payload["lastFolders"]}
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(incoming, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return incoming
