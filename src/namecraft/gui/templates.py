"""自定义规则模板：把常用规则栈按名称保存，换一批文件时一键套用。

存放在 `%LOCALAPPDATA%/namecraft/templates.json`（可用 `NAMECRAFT_HOME` 覆盖），
与设置、日志同目录。同名保存视为覆盖；读取容忍缺字段与损坏文件；写入走
临时文件 + os.replace，避免半截文件。模板只存规则定义，不存文件列表与路径。
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime

from namecraft.fs.runtime import runtime_dir

MAX_TEMPLATES = 100
MAX_RULES = 50
MAX_NAME = 40
_WS = re.compile(r"\s+")


def templates_path():
    return runtime_dir() / "templates.json"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _clean_name(value) -> str:
    name = _WS.sub(" ", str(value or "")).strip()
    if not name:
        raise ValueError("模板名称不能为空")
    if len(name) > MAX_NAME:
        raise ValueError(f"模板名称不能超过 {MAX_NAME} 个字符")
    return name


def _clean_rule(entry) -> dict | None:
    if not isinstance(entry, dict):
        return None
    rule_type = str(entry.get("type", "") or "").strip()
    if not rule_type:
        return None
    params = entry.get("params")
    return {
        "type": rule_type,
        "enabled": bool(entry.get("enabled", True)),
        "params": dict(params) if isinstance(params, dict) else {},
    }


def _clean_template(item) -> dict | None:
    if not isinstance(item, dict):
        return None
    name = _WS.sub(" ", str(item.get("name", "") or "")).strip()
    if not name:
        return None
    rules = [r for r in (_clean_rule(x) for x in (item.get("rules") or [])) if r]
    if not rules:
        return None
    template_id = str(item.get("id", "") or "").strip() or uuid.uuid4().hex[:12]
    return {
        "id": template_id,
        "name": name[:MAX_NAME],
        "rules": rules[:MAX_RULES],
        "updated": str(item.get("updated", "") or ""),
    }


def load() -> list[dict]:
    try:
        with open(templates_path(), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    items = data.get("templates") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    result: list[dict] = []
    seen: set[str] = set()
    for item in items:
        template = _clean_template(item)
        if template is None or template["id"] in seen:
            continue
        seen.add(template["id"])
        result.append(template)
        if len(result) >= MAX_TEMPLATES:
            break
    return result


def _write(items: list[dict]) -> None:
    path = templates_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "templates": items}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def save(name, rules, template_id: str = "") -> dict:
    """按 id 或名称写入模板；命中同名视为覆盖并把该模板置顶。"""
    clean_name = _clean_name(name)
    clean_rules = [r for r in (_clean_rule(x) for x in (rules or [])) if r]
    if not clean_rules:
        raise ValueError("模板至少需要一条规则")
    if len(clean_rules) > MAX_RULES:
        raise ValueError(f"单个模板最多 {MAX_RULES} 条规则")
    items = load()
    wanted_id = str(template_id or "").strip()
    index = next((i for i, t in enumerate(items) if wanted_id and t["id"] == wanted_id), None)
    if index is None:
        index = next(
            (i for i, t in enumerate(items) if t["name"].casefold() == clean_name.casefold()),
            None,
        )
    if index is None:
        if len(items) >= MAX_TEMPLATES:
            raise ValueError(f"模板数量已达上限 {MAX_TEMPLATES} 个")
        item = {
            "id": uuid.uuid4().hex[:12],
            "name": clean_name,
            "rules": clean_rules,
            "updated": _now(),
        }
    else:
        item = {**items[index], "name": clean_name, "rules": clean_rules, "updated": _now()}
        items.pop(index)
    items.insert(0, item)
    _write(items)
    return item


def delete(template_id: str) -> list[dict]:
    wanted = str(template_id or "").strip()
    items = load()
    remaining = [t for t in items if t["id"] != wanted]
    if len(remaining) == len(items):
        raise KeyError("模板不存在或已删除")
    _write(remaining)
    return remaining
