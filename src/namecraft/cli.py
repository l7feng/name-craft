"""命令行入口：首期只有只读预览（执行与撤销在 S3）。

用法：
    namecraft preview <目录> --rules rules.json [--json]

规则文件为 JSON 数组：`[{"type": "insert", "params": {...}, "enabled": true}]`，
类型键见 rules.REGISTRY（12 种）。预览按栈序计算新名并做四项校验；
不写盘、不改名。存在校验错误时退出码 1，参数或规则文件错误退出码 2。
"""

from __future__ import annotations

import argparse
import json
import sys

from namecraft.engine.chain import apply_chain
from namecraft.engine.conflicts import detect_cycles
from namecraft.engine.models import PreviewRow, Rule
from namecraft.engine.validate import validate
from namecraft.fs import list_files, occupied_paths


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


def build_rows(directory: str, rules: list[Rule]) -> tuple[list[PreviewRow], list[list[str]]]:
    items = list_files(directory)
    names = apply_chain(items, rules)
    rows = validate(items, names, occupied_paths(items))
    return rows, detect_cycles(items, names)


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
        rows, cycles = build_rows(args.directory, rules)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="namecraft", description="文件批量重命名工具（干净室重写）")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preview", help="只读预览：按规则栈计算新名并校验")
    p.add_argument("directory", help="目标目录（只读，不递归）")
    p.add_argument("--rules", required=True, help="规则栈 JSON 文件路径")
    p.add_argument("--json", action="store_true", help="输出 JSON 而非表格")
    p.set_defaults(func=cmd_preview)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())