"""规则注册表：类型 → make(params) -> fn(name, ctx) -> str。

每个 make 返回的函数是无副作用纯函数（Serialize 的计数状态封闭在闭包内，
每次预览重新 make，不跨会话泄漏）。
"""

from __future__ import annotations

from .case import make as case
from .cleanup import make as cleanup
from .delete import make as delete
from .extension import make as extension
from .insert import make as insert
from .rearrange import make as rearrange
from .regex import make as regex
from .remove import make as remove
from .replace import make as replace
from .serialize import make as serialize
from .strip import make as strip
from .ucs import make as ucs
from .userinput import make as userinput

REGISTRY = {
    "insert": insert,
    "delete": delete,
    "remove": remove,
    "replace": replace,
    "rearrange": rearrange,
    "extension": extension,
    "strip": strip,
    "case": case,
    "serialize": serialize,
    "cleanup": cleanup,
    "regex": regex,
    "userinput": userinput,
    "ucs": ucs,
}