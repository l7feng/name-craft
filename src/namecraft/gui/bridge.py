"""pywebview 桥接：JS 只传原始数据，校验、计算与写盘全部在 Python 侧完成。

返回统一为 {ok: bool, ...} 字典；异常不抛给前端，转成 ok=False + error 文本，
避免 JS 侧出现无法解读的 Promise 拒绝。文件选择器显式传入起始目录
（当前输入的有效位置 → 该用途上次成功位置 → 系统默认），见经验 130。
"""

from __future__ import annotations

import os
import shutil

from namecraft import __version__, ucs
from namecraft.engine.models import Rule
from namecraft.fs import items_from_paths
from namecraft.fs import journal as journal_store
from namecraft.session.execute import ExecutionError, UndoError, execute, undo
from namecraft.session.plan import MODES, PlanError, blocked_targets, prepare
from namecraft.session.preview import compute, compute_items

from . import docs, schema, settings, templates


def _error(message: str, **extra) -> dict:
    return {"ok": False, "error": message, **extra}


def first_existing_dir(current: str = "", fallback: str = "") -> str:
    """当前输入的有效位置优先，其次该用途上次位置；无效路径逐级回退到父级。"""
    for candidate in (current, fallback):
        path = (candidate or "").strip().strip('"')
        if not path:
            continue
        if os.path.isdir(path):
            return path
        if os.path.isfile(path):
            return os.path.dirname(path)
        parent = os.path.dirname(path)
        while parent and parent != path and not os.path.isdir(parent):
            path, parent = parent, os.path.dirname(parent)
        if os.path.isdir(parent):
            return parent
    return ""


def to_rules(raw) -> list[Rule]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise TypeError("规则栈必须是数组")
    rules = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise TypeError(f"规则第 {i + 1} 项必须是对象")
        rule_type = str(entry.get("type", ""))
        if rule_type not in schema.BY_TYPE:
            raise ValueError(f"未知规则类型：{rule_type or '（空）'}")
        params = entry.get("params", {})
        if not isinstance(params, dict):
            raise TypeError(f"规则第 {i + 1} 项 params 必须是对象")
        rules.append(Rule(rule_type, dict(params), bool(entry.get("enabled", True))))
    return rules


def _rows_payload(rows) -> list[dict]:
    return [
        {
            "old": r.item.name,
            "new": r.new_name,
            "changed": r.changed,
            "status": r.status,
            "reasons": r.reasons,
            "path": r.item.path,
        }
        for r in rows
    ]


def _select_source(payload: dict, folder: str, rules: list[Rule]):
    """按显式文件列表（拖入/多选）或文件夹计算预览，返回 (rows, cycles, occupied, source)。

    两者同时给出时文件列表优先；显式列表为空则退回文件夹，方便清空拖拽后恢复原状态。
    """
    raw_paths = payload.get("paths")
    if raw_paths is not None and not isinstance(raw_paths, list):
        raise TypeError("文件列表必须是数组")
    if raw_paths:
        rows, cycles, occupied = compute_items(items_from_paths(raw_paths), rules)
        return rows, cycles, occupied, "paths"
    if not folder:
        raise ValueError("请先拖入文件或选择文件夹")
    if not os.path.isdir(folder):
        raise ValueError(f"文件夹不存在：{folder}")
    rows, cycles, occupied = compute(folder, rules)
    return rows, cycles, occupied, "folder"


class Bridge:
    """暴露给 JS 的 API 对象（方法名即 window.pywebview.api.<name>）。"""

    def __init__(self, window_getter=None):
        self._window_getter = window_getter

    def _window(self):
        getter = self._window_getter
        if getter is None:
            try:
                import webview
            except ImportError:
                return None
            windows = getattr(webview, "windows", [])
            return windows[0] if windows else None
        return getter()

    def _remember(self, folder: str, raw_rules, mode: str) -> None:
        payload = {"mode": mode}
        if folder:
            payload["folder"] = folder
            payload["lastFolders"] = {"target": folder}
        if isinstance(raw_rules, list):
            payload["rules"] = raw_rules
        try:
            settings.save(payload)
        except OSError:
            pass  # 记忆失败不影响改名本身

    def bootstrap(self) -> dict:
        return {
            "ok": True,
            "version": __version__,
            "settings": settings.load(),
            "rules": schema.RULE_META,
            "templates": templates.load(),
            "modes": [
                {"value": "block", "label": "拦截", "desc": "有冲突就拒绝，不动文件"},
                {"value": "suffix", "label": "加后缀", "desc": "重名时自动加 (2)、(3)…"},
                {"value": "overwrite", "label": "确认覆盖", "desc": "逐项确认后替换现有文件"},
            ],
        }

    def pick_folder(self, current: str = "", purpose: str = "target") -> dict:
        try:
            import webview
        except ImportError:
            return _error("未安装 pywebview，无法打开文件选择器")
        window = self._window()
        if window is None:
            return _error("窗口尚未就绪")
        remembered = settings.load().get("lastFolders", {}).get(purpose, "")
        initial = first_existing_dir(current, remembered)
        try:
            chosen = window.create_file_dialog(webview.FOLDER_DIALOG, directory=initial or None)
        except TypeError:
            chosen = window.create_file_dialog(webview.FOLDER_DIALOG)
        except OSError as error:
            return _error(f"打开文件选择器失败：{error}")
        if not chosen:
            return {"ok": True, "path": ""}
        path = chosen[0] if isinstance(chosen, (list, tuple)) else str(chosen)
        try:
            settings.save({"lastFolders": {purpose: path}})
        except OSError:
            pass
        return {"ok": True, "path": path}

    def pick_files(self, current: str = "", purpose: str = "target") -> dict:
        """多选文件，作为原生拖放的键盘/触控回退入口。"""
        try:
            import webview
        except ImportError:
            return _error("未安装 pywebview，无法打开文件选择器")
        window = self._window()
        if window is None:
            return _error("窗口尚未就绪")
        remembered = settings.load().get("lastFolders", {}).get(purpose, "")
        initial = first_existing_dir(current, remembered)
        try:
            chosen = window.create_file_dialog(
                webview.OPEN_DIALOG, directory=initial or None, allow_multiple=True
            )
        except TypeError:
            chosen = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        except OSError as error:
            return _error(f"打开文件选择器失败：{error}")
        if not chosen:
            return {"ok": True, "paths": []}
        paths = [str(p) for p in chosen]
        try:
            settings.save({"lastFolders": {purpose: first_existing_dir(paths[0])}})
        except OSError:
            pass
        return {"ok": True, "paths": paths}

    def preview(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        folder = str(payload.get("folder") or "").strip()
        try:
            rules = to_rules(payload.get("rules"))
        except (TypeError, ValueError) as error:
            return _error(str(error))
        try:
            rows, cycles, _, source = _select_source(payload, folder, rules)
        except (OSError, TypeError, ValueError) as error:
            message = f"预览失败：{error}" if isinstance(error, OSError) else str(error)
            return _error(message)
        self._remember(folder, payload.get("rules"), str(payload.get("mode", "block")))
        return {
            "ok": True,
            "folder": folder,
            "source": source,
            "rows": _rows_payload(rows),
            "cycles": len(cycles),
            "summary": {
                "total": len(rows),
                "changed": sum(1 for r in rows if r.changed),
                "errors": sum(1 for r in rows if r.status == "error"),
            },
        }

    def execute(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        folder = str(payload.get("folder") or "").strip()
        mode = str(payload.get("mode") or "block")
        confirm = payload.get("confirm") or []
        try:
            rules = to_rules(payload.get("rules"))
        except (TypeError, ValueError) as error:
            return _error(str(error))
        if mode not in MODES:
            return _error(f"未知冲突口径：{mode}")
        try:
            rows, _, occupied, _ = _select_source(payload, folder, rules)
            if mode == "overwrite":
                blocked = blocked_targets(rows, occupied)
                confirmed = {os.path.normcase(str(p)) for p in confirm}
                pending = [p for p in blocked if os.path.normcase(p) not in confirmed]
                if pending:
                    return _error(
                        "覆盖模式需要逐项确认目标文件",
                        kind="overwrite",
                        needConfirm=pending,
                    )
            plan = prepare(rows, occupied, mode=mode, confirm=confirm)
            if not plan.ops:
                self._remember(folder, payload.get("rules"), mode)
                return {"ok": True, "journal": None, "message": "没有需要改名的文件。"}
            journal = execute(plan.ops, notes=plan.notes)
        except (OSError, TypeError, ValueError, PlanError, ExecutionError) as error:
            return _error(str(error))
        self._remember(folder, payload.get("rules"), mode)
        return {
            "ok": True,
            "journal": journal.to_dict(),
            "count": len(journal.entries),
            "notes": journal.notes,
        }

    def journals(self) -> dict:
        items = journal_store.list_all()
        latest = journal_store.latest_done_id()
        for item in items:
            item["undoable"] = item.get("id") == latest and item.get("status") == "done"
        return {"ok": True, "journals": items}

    def undo(self, journal_id: str) -> dict:
        try:
            journal = undo(str(journal_id or ""))
        except (OSError, UndoError, KeyError) as error:
            return _error(str(error))
        return {
            "ok": True,
            "journal": journal.to_dict(),
            "count": len(journal.entries),
            "notes": journal.notes,
        }

    def save_settings(self, payload: dict) -> dict:
        try:
            saved = settings.save(payload if isinstance(payload, dict) else {})
        except OSError as error:
            return _error(f"保存设置失败：{error}")
        return {"ok": True, "settings": saved}

    def save_template(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        raw_rules = payload.get("rules")
        try:
            to_rules(raw_rules)  # 先拒未知类型与坏结构；参数错误留给预览提示
            item = templates.save(payload.get("name"), raw_rules, str(payload.get("id") or ""))
        except (TypeError, ValueError, OSError) as error:
            return _error(str(error))
        return {"ok": True, "template": item, "templates": templates.load()}

    def delete_template(self, template_id: str) -> dict:
        try:
            remaining = templates.delete(str(template_id or ""))
        except (KeyError, OSError) as error:
            return _error(str(error))
        return {"ok": True, "templates": remaining}

    def ucs_categories(self) -> dict:
        return {
            "ok": True,
            "count": len(ucs.CATEGORIES),
            "categories": [list(item) for item in ucs.CATEGORIES],
        }

    def ucs_guide(self) -> dict:
        try:
            text = docs.read_text("guide")
        except (OSError, ValueError) as error:
            return _error(f"读取 UCS 规范失败：{error}")
        return {
            "ok": True,
            "markdown": text,
            "guidePath": str(docs.doc_path("guide")),
            "tablePath": str(docs.doc_path("table")),
        }

    def save_ucs_doc(self, kind: str = "guide") -> dict:
        """把随包 UCS 规范或分类表另存到用户选择的位置。"""
        try:
            source = docs.doc_path(str(kind or "guide"))
        except ValueError as error:
            return _error(str(error))
        if not source.is_file():
            return _error(f"随包文档缺失：{source.name}")
        try:
            import webview
        except ImportError:
            return _error("未安装 pywebview，无法打开另存对话框")
        window = self._window()
        if window is None:
            return _error("窗口尚未就绪")
        home = os.path.expanduser("~")
        desktop = os.path.join(home, "Desktop")
        initial = desktop if os.path.isdir(desktop) else home
        try:
            chosen = window.create_file_dialog(
                webview.SAVE_DIALOG, directory=initial, save_filename=source.name
            )
        except TypeError:
            chosen = window.create_file_dialog(webview.SAVE_DIALOG, save_filename=source.name)
        except OSError as error:
            return _error(f"打开另存对话框失败：{error}")
        if not chosen:
            return {"ok": True, "path": ""}
        target = chosen[0] if isinstance(chosen, (list, tuple)) else str(chosen)
        try:
            shutil.copyfile(source, target)
        except OSError as error:
            return _error(f"另存失败：{error}")
        return {"ok": True, "path": target}
