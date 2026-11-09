"""数据模型：文件项、规则、预览状态。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class FileItem:
    """一个待处理文件。path 为原始完整路径，marked=False 时不参与预览与执行。"""

    path: str
    marked: bool = True

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def folder(self) -> str:
        return os.path.dirname(self.path)


@dataclass
class Rule:
    """规则栈中的一项。type 对应 rules.REGISTRY 键；params 为参数字典。"""

    type: str
    params: dict = field(default_factory=dict)
    enabled: bool = True


@dataclass
class Ctx:
    """传给规则函数的上下文（跨文件规则用）。"""

    index: int
    path: str
    folder: str
    total: int
    prev_input: str | None = None


@dataclass
class PreviewRow:
    """单个文件的预览结果。"""

    item: FileItem
    new_name: str
    status: str = "ok"  # ok | error | skipped
    reasons: list[str] = field(default_factory=list)

    @property
    def new_path(self) -> str:
        return os.path.join(self.item.folder, self.new_name)

    @property
    def changed(self) -> bool:
        return self.new_name != self.item.name