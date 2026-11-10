"""命令行入口：预览、执行与撤销。

用法：
    namecraft preview <目录> --rules rules.json [--json]
    namecraft execute <目录> --rules rules.json [--mode block|suffix|overwrite] [--confirm <路径>]
    namecraft journals [--json]
    namecraft undo <日志id>

规则文件为 JSON 数组：`[{"type": "insert", "params": {...}, "enabled": true}]`，
类型键见 rules.REGISTRY（13 种）。预览按栈序计算新名并做四项校验；
不写盘、不改名。存在校验错误时退出码 1，参数或规则文件错误退出码 2。
"""

from __future__ import annotations

import argparse
import json
import sys

from namecraft.engine.models import PreviewRow, Rule
from namecraft.fs import journal as journal_store
from namecraft.session.execute import ExecutionError, UndoError, execute, undo
from namecraft.session.plan import MODES, PlanError, prepare
from namecraft.session.preview import compute


def load_rules(path: str) -> list[Rule]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise TypeError("规则文件顶层必须是数组")
    rules = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict) or "type" not in entry:
            raise TypeError(f"规则第 {i + 1} 项必须是含 type 的对象")
        params = entry.get("params", {})
        if not isinstance(params, dict):
            raise TypeError(f"规则第 {i + 1} 项 params 必须是对象")
        rules.append(Rule(str(entry["type"]), dict(params), bool(entry.get("enabled", True))))
    return rules


def _print_table(rows: list[PreviewRow]) -> None:
    marks = {"ok": "OK", "error": "ERR", "skipped": "-"}
    old_w = max(len(r.item.name) for r in rows)
    new_w = max(len(r.new_name) for r in rows)
    for r in rows:
        flag = "=" if r.changed else " "
        print(f"{marks[r.status]:>3} {r.item.name:<{old_w}} {flag}> {r.new_name:<{new_w}}")
        for reason in r.reasons:
            print(f"      ! {reason}")


def _print_json(rows: list[PreviewRow], cycles: list[list[str]]) -> None:
    payload = {
        "rows": [
            {
                "old": r.item.name,
                "new": r.new_name,
                "changed": r.changed,
                "status": r.status,
                "reasons": r.reasons,
            }
            for r in rows
        ],
        "cycles": cycles,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_preview(args: argparse.Namespace) -> int:
    try:
        rules = load_rules(args.rules)
        rows, cycles, _ = compute(args.directory, rules)
    except (OSError, TypeError, ValueError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 2
    if not rows:
        print("目录内没有文件。")
        return 0
    if args.json:
        _print_json(rows, cycles)
    else:
        _print_table(rows)
        errors = sum(1 for r in rows if r.status == "error")
        changed = sum(1 for r in rows if r.changed)
        print(f"\n共 {len(rows)} 项，将改名 {changed} 项，校验错误 {errors} 项（预览未写盘）。")
        if cycles:
            print(f"检测到 {len(cycles)} 组循环换位，执行时将用临时名两阶段完成。")
    return 1 if any(r.status == "error" for r in rows) else 0


def cmd_execute(args: argparse.Namespace) -> int:
    try:
        rules = load_rules(args.rules)
        rows, _, occupied = compute(args.directory, rules)
        plan = prepare(rows, occupied, mode=args.mode, confirm=set(args.confirm or ()))
        if not plan.ops:
            print("没有需要改名的文件。")
            return 0
        journal = execute(plan.ops, notes=plan.notes)
    except (OSError, TypeError, ValueError, PlanError, ExecutionError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(journal.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"已改名 {len(journal.entries)} 项（模式 {plan.mode}）。")
        for note in journal.notes:
            print(f"  注：{note}")
        print(f"日志：{journal.id}（撤销：namecraft undo {journal.id}）")
    return 0


def cmd_journals(args: argparse.Namespace) -> int:
    items = journal_store.list_all()
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    if not items:
        print("暂无改名日志。")
        return 0
    latest = journal_store.latest_done_id()
    for j in items:
        mark = "← 可撤销" if j.get("id") == latest else ""
        print(
            f"{j.get('id')}  {j.get('status'):<8} {len(j.get('entries', [])):>3} 项"
            f"  {j.get('created', '')} {mark}"
        )
    return 0


def cmd_undo(args: argparse.Namespace) -> int:
    try:
        journal = undo(args.journal_id)
    except (OSError, UndoError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(journal.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"已撤销 {len(journal.entries)} 项改名（日志 {journal.id}）。")
        for note in journal.notes:
            print(f"  注：{note}")
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    from namecraft.gui import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="namecraft", description="文件批量重命名工具（干净室重写）")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preview", help="只读预览：按规则栈计算新名并校验")
    p.add_argument("directory", help="目标目录（只读，不递归）")
    p.add_argument("--rules", required=True, help="规则栈 JSON 文件路径")
    p.add_argument("--json", action="store_true", help="输出 JSON 而非表格")
    p.set_defaults(func=cmd_preview)

    e = sub.add_parser("execute", help="执行改名（写日志，可撤销）")
    e.add_argument("directory", help="目标目录（不递归）")
    e.add_argument("--rules", required=True, help="规则栈 JSON 文件路径")
    e.add_argument(
        "--mode",
        choices=list(MODES),
        default="block",
        help="冲突口径：block 拦截／suffix 加 (n) 后缀／overwrite 覆盖（需逐项 confirm）",
    )
    e.add_argument("--confirm", action="append", default=[], help="覆盖模式确认的目标完整路径，可重复")
    e.add_argument("--json", action="store_true", help="输出 JSON 而非文本")
    e.set_defaults(func=cmd_execute)

    j = sub.add_parser("journals", help="列出改名日志")
    j.add_argument("--json", action="store_true", help="输出 JSON")
    j.set_defaults(func=cmd_journals)

    u = sub.add_parser("undo", help="撤销最近一次完成的改名")
    u.add_argument("journal_id", help="日志 id（journals 命令可查）")
    u.add_argument("--json", action="store_true", help="输出 JSON")
    u.set_defaults(func=cmd_undo)

    g = sub.add_parser("gui", help="打开图形界面")
    g.set_defaults(func=cmd_gui)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())