"""UCS 命名规则：按 Universal Category System 8.2.1 结构生成文件名。

结构：CatID(-UserCategory)_(VendorCategory-)FXName_CreatorID_SourceID_UserData。
空块省略，块间只用下划线；扩展名原样保留。CatID 必须存在于 ucs.CATEGORIES，
大小写不敏感地规范到标准写法；未知 CatID 直接报错，不生成猜测值。

FXName 三种来源：current（当前文件名，可先剥离已有 CatID 前缀）、fixed（固定
描述）、list（按行逐文件，行数不足时回落到当前文件名）。字段值默认清理
Windows 非法字符与多余空白，并去掉块内下划线，避免破坏 UCS 结构。
"""

from __future__ import annotations

import re

from namecraft.engine.models import Ctx
from namecraft.engine.textutil import split_ext
from namecraft.ucs import canonical

_FORBIDDEN = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_SPACES = re.compile(r"\s+")
_PREFIX = re.compile(r"^([A-Za-z0-9]+)(?:-[^_]*)?_(.+)$", re.DOTALL)


def _clean(value, *, keep_underscore: bool = False) -> str:
    text = _FORBIDDEN.sub(" ", str(value or ""))
    if not keep_underscore:
        text = text.replace("_", " ")
    return _SPACES.sub(" ", text).strip().strip(".")


def _strip_prefix(base: str) -> str:
    match = _PREFIX.match(base)
    if match and canonical(match.group(1)):
        return match.group(2).lstrip()
    return base


def make(params: dict):
    raw_catid = str(params.get("catid", "") or "").strip()
    catid = canonical(raw_catid)
    if not catid:
        raise ValueError(f"UCS: 未知 CatID「{raw_catid}」，请从 UCS 8.2.1 分类表选择")
    fx_mode = str(params.get("fx_mode", "current"))
    fx_name = str(params.get("fx_name", "") or "")
    raw_list = params.get("fx_list", "")
    if isinstance(raw_list, str):
        fx_list = raw_list.splitlines()
    else:
        fx_list = [str(x) for x in raw_list]
    creator = str(params.get("creator", "") or "")
    source = str(params.get("source", "") or "")
    user_category = str(params.get("user_category", "") or "")
    vendor_category = str(params.get("vendor_category", "") or "")
    user_data = str(params.get("user_data", "") or "")
    strip_existing = bool(params.get("strip_existing", True))
    sanitize = bool(params.get("sanitize", True))

    def clean(value: str, *, keep_underscore: bool = False) -> str:
        return _clean(value, keep_underscore=keep_underscore) if sanitize else str(value).strip()

    if fx_mode not in ("current", "fixed", "list"):
        raise ValueError(f"UCS: 未知 FXName 来源「{fx_mode}」")

    cat_block = catid + ("-" + clean(user_category) if clean(user_category) else "")

    def apply(name: str, ctx: Ctx) -> str:
        base, ext = split_ext(name)
        working = _strip_prefix(base) if strip_existing else base
        if fx_mode == "fixed":
            fx = fx_name or working
        elif fx_mode == "list":
            fx = fx_list[ctx.index].strip() if ctx.index < len(fx_list) else ""
            fx = fx or working
        else:
            fx = working
        fx_block = clean(fx)
        vendor = clean(vendor_category)
        if vendor:
            fx_block = f"{vendor}-{fx_block}" if fx_block else vendor
        blocks = [
            cat_block,
            fx_block,
            clean(creator),
            clean(source),
            clean(user_data, keep_underscore=True),
        ]
        new_base = "_".join(block for block in blocks if block)
        return new_base + ext

    return apply
