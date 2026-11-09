"""GUI 用的规则表单元数据：类型 → 中文名、说明、字段与默认值。

只描述“怎么填”，不参与计算；真正的语义在 rules/*.py。字段 kind 取值：
text / textarea / number / check / select。`when` 表示某字段只在另一字段取
特定值时才显示（如 Insert 的 position 只在 where=position 时出现）。
"""

from __future__ import annotations


def _f(key, label, kind="text", default="", *, hint="", options=None, when=None, minimum=None):
    field = {"key": key, "label": label, "kind": kind, "default": default}
    if hint:
        field["hint"] = hint
    if options:
        field["options"] = [{"value": v, "label": t} for v, t in options]
    if when:
        field["when"] = when
    if minimum is not None:
        field["min"] = minimum
    return field


_SEARCH_OCC = [
    ("first", "第一处"),
    ("last", "最后一处"),
    ("all", "全部"),
]

_SKIP_EXT = _f("skip_ext", "保留扩展名", "check", True, hint="只改主名，扩展名原样保留")

RULE_META = [
    {
        "type": "insert",
        "name": "插入",
        "desc": "在前缀、后缀、指定位置或锚文本前后插入文字",
        "fields": [
            _f("what", "插入内容"),
            _f(
                "where",
                "位置",
                "select",
                "prefix",
                options=[
                    ("prefix", "前缀"),
                    ("suffix", "后缀"),
                    ("position", "指定位置"),
                    ("after", "锚文本之后"),
                    ("before", "锚文本之前"),
                ],
            ),
            _f("position", "位置（第几位）", "number", 1, when={"where": "position"}, minimum=1),
            _f("from_right", "从右数", "check", False, when={"where": "position"}),
            _f("text", "锚文本", when={"where": ["after", "before"]}),
            _SKIP_EXT,
        ],
    },
    {
        "type": "delete",
        "name": "删除",
        "desc": "从起始点删除到终点（位置/分隔符/末尾）",
        "fields": [
            _f(
                "from_mode",
                "起始点",
                "select",
                "position",
                options=[("position", "第 N 个字符"), ("delimiter", "分隔符之后")],
            ),
            _f("from_value", "起始值", "text", "1"),
            _f(
                "until_mode",
                "终点",
                "select",
                "end",
                options=[("end", "段尾"), ("count", "往后 N 个字符"), ("delimiter", "分隔符之后")],
            ),
            _f("until_value", "终点值", "text", "1", when={"until_mode": ["count", "delimiter"]}),
            _f("right_to_left", "从右到左", "check", False),
            _f("keep_delimiters", "保留下界分隔符", "check", False),
            _SKIP_EXT,
        ],
    },
    {
        "type": "remove",
        "name": "移除",
        "desc": "按文本移除指定出现次数的字符段，支持通配符",
        "fields": [
            _f("text", "要移除的文本"),
            _f("occurrences", "出现次数", "select", "all", options=_SEARCH_OCC),
            _f("case_sensitive", "区分大小写", "check", True),
            _f("wildcards", "启用通配符（* 与 ?）", "check", False),
            _SKIP_EXT,
        ],
    },
    {
        "type": "replace",
        "name": "替换",
        "desc": "查找 → 替换；多组用 *|* 分隔",
        "fields": [
            _f("find", "查找", "textarea", "", hint="多个查找词用 *|* 分隔"),
            _f("replace", "替换为", "textarea", "", hint="多个替换词用 *|* 分隔，数量不足时补空"),
            _f("occurrences", "出现次数", "select", "all", options=_SEARCH_OCC),
            _f("case_sensitive", "区分大小写", "check", True),
            _f("wildcards", "启用通配符（* 与 ?）", "check", False),
            _SKIP_EXT,
        ],
    },
    {
        "type": "rearrange",
        "name": "重排",
        "desc": "按分隔符/位置拆段后用 $0 $1 $-1 模板重排",
        "fields": [
            _f(
                "split",
                "拆分方式",
                "select",
                "delimiters",
                options=[("delimiters", "分隔符"), ("positions", "固定位置"), ("exact", "精确字符串")],
            ),
            _f("value", "拆分值", "textarea", "", hint="分隔符/位置（*|* 分隔）/精确片段（*|* 分隔）"),
            _f("pattern", "新顺序模板", "text", "$0", hint="例：$2 - $1；$-1 表示最后一段"),
            _f("right_to_left", "从右到左拆分", "check", False),
            _SKIP_EXT,
        ],
    },
    {
        "type": "extension",
        "name": "扩展名",
        "desc": "替换、追加扩展名或调整其大小写",
        "fields": [
            _f("new_ext", "新扩展名", "text", "txt", hint="不带点，如 txt；留空表示移除扩展名"),
            _f("append", "追加到现有扩展名后", "check", False),
            _f(
                "case",
                "扩展名大小写",
                "select",
                "none",
                options=[("none", "不变"), ("lower", "小写"), ("upper", "大写")],
            ),
        ],
    },
    {
        "type": "strip",
        "name": "剥离",
        "desc": "剔除英文、数字、符号、括号或自定义字符集",
        "fields": [
            _f("english", "英文", "check", False),
            _f("digits", "数字", "check", False),
            _f("symbols", "符号", "check", False),
            _f("brackets", "括号", "check", False),
            _f("custom", "自定义字符集", hint="逐个字符剔除"),
            _f("except_selected", "反向：只保留勾选的字符", "check", False),
            _SKIP_EXT,
        ],
    },
    {
        "type": "case",
        "name": "大小写",
        "desc": "转换主名大小写，可强制指定片段的写法",
        "fields": [
            _f(
                "mode",
                "转换方式",
                "select",
                "none",
                options=[
                    ("none", "不变"),
                    ("capitalize", "每词首字母大写"),
                    ("capitalize_preserve", "首字母大写（保留其余）"),
                    ("lower", "全小写"),
                    ("upper", "全大写"),
                    ("invert", "反转大小写"),
                    ("sentence", "句首大写"),
                ],
            ),
            _f("fragments", "强制写法片段", "text", "", hint="逗号分隔，按输入原样替换，如 DJ,MP3"),
            _f(
                "ext_case",
                "扩展名大小写",
                "select",
                "none",
                options=[("none", "不变"), ("lower", "小写"), ("upper", "大写")],
            ),
            _SKIP_EXT,
        ],
    },
    {
        "type": "serialize",
        "name": "序号",
        "desc": "生成递增序号：十进制或字母序",
        "fields": [
            _f(
                "system",
                "序号系统",
                "select",
                "decimal",
                options=[("decimal", "十进制"), ("letters", "字母 a, b, …, aa")],
            ),
            _f("start", "起始值", "number", 1, minimum=1),
            _f("step", "步长", "number", 1),
            _f("repeat", "重复次数", "number", 1, minimum=1),
            _f("pad", "补零位数", "number", 0, minimum=0),
            _f("reset_every", "每 N 项重置（0 不重置）", "number", 0, minimum=0),
            _f("reset_folder", "换文件夹重置", "check", False),
            _f("reset_name", "换文件名重置", "check", False),
            _f(
                "where",
                "插入位置",
                "select",
                "suffix",
                options=[("prefix", "前缀"), ("suffix", "后缀"), ("position", "指定位置"), ("replace", "替换整名")],
            ),
            _f("position", "位置（第几位）", "number", 1, when={"where": "position"}, minimum=1),
            _SKIP_EXT,
        ],
    },
    {
        "type": "cleanup",
        "name": "清理",
        "desc": "删括号内容、字符转空格、驼峰拆分、修整空格",
        "fields": [
            _f("brackets", "删除括号内容", "text", "", hint="含哪对符号就删哪对，如 ( [ {"),
            _f("chars_to_spaces", "这些字符转成空格"),
            _f("normalize_space", "各种空白统一为普通空格", "check", False),
            _f("split_camel", "驼峰拆分", "check", False),
            _f("fix_spaces", "合并多余空格并去首尾", "check", False),
            _SKIP_EXT,
        ],
    },
    {
        "type": "regex",
        "name": "正则",
        "desc": "正则查找替换，$1 或 ${1} 引用分组",
        "fields": [
            _f("expression", "表达式"),
            _f("replacement", "替换为"),
            _f("case_sensitive", "区分大小写", "check", True),
            _SKIP_EXT,
        ],
    },
    {
        "type": "userinput",
        "name": "名称列表",
        "desc": "按行依次给文件指定新名",
        "fields": [
            _f("names", "新名列表（每行一个）", "textarea", ""),
            _f(
                "mode",
                "填入方式",
                "select",
                "replace",
                options=[("replace", "替换整个名称"), ("front", "放在原名前"), ("after", "追加到原名后")],
            ),
            _SKIP_EXT,
        ],
    },
]

BY_TYPE = {item["type"]: item for item in RULE_META}


def defaults(rule_type: str) -> dict:
    meta = BY_TYPE.get(rule_type)
    if meta is None:
        raise ValueError(f"未知规则类型：{rule_type}")
    return {f["key"]: f["default"] for f in meta["fields"]}
