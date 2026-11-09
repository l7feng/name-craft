# STRUCTURE.md — namecraft 存放规范

> 按个人知识库 `6-资产-R/00-模板/07-软件项目布局模板/01-共享层/01-存放规范骨架.md` 填写，技术栈取 Python src-layout 布局卡。变更记录见 `docs/adr/`。

## 顶层分区表

| 目录 | 所有权 | 放什么 | 不放什么 | 生命周期 |
| --- | --- | --- | --- | --- |
| `src/namecraft/` | 开发 | 唯一可导入包：engine／rules／session／fs／gui／cli | 生成物、缓存、配置实值、密钥 | 长期，随版本 |
| `tests/` | 开发 | 与源码对应的测试，只经安装后的包导入 | 任何 `sys.path` 注入、一次性验证脚本、测试数据大文件 | 长期，随版本 |
| `docs/` | 全员 | 设计说明与 `adr/` 决策记录 | 自动生成的 API 文档、构建产物 | 长期，随版本 |
| `packaging/` | 构建 | PyInstaller 规格、入口与版本资源 | 生成物、证书、密钥 | 长期，随版本 |
| `dist/` `build/` | 构建 | PyInstaller 可再生产物（S3） | 任何手写内容 | 临时，可删可重建 |

运行态数据（撤销日志、用户配置）写 `%LOCALAPPDATA%/namecraft/`，不入仓；打包交付产物落 `D:/Ai-Files/Tools/Exe/`（S3 起）。

## 落点路由表

| 序 | 判定问题 | 命中落点 |
| --- | --- | --- |
| 1 | 机器生成、删了能重建？ | `dist/` `build/`，已在 .gitignore |
| 2 | 运行期产生、不该进版本库？ | `%LOCALAPPDATA%/namecraft/` |
| 3 | 人手写的源码？ | `src/namecraft/<业务子域>/`（engine、rules、session、fs、gui） |
| 4 | 该源码的测试？ | `tests/` 镜像同名 `test_*.py` |
| 5 | 人要读的说明或决策？ | `docs/`；决策类固定 `docs/adr/` |
| 6 | 配置？ | 默认值在代码 dataclass；用户实值在用户数据区 |
| 7 | 第三方依赖？ | 只改 `pyproject.toml` |
| 8 | 可复用工具脚本？ | 打包入口与规格落 `packaging/`；其他一次性脚本放库外工作区，不入库 |
| 9 | 以上都不命中 | 停，补本表新行并写明「不放什么」，再落位 |

## 命名规则

- 目录与文件小写蛇形（Python 惯例，全局统一）；测试 `test_<被测模块>.py`。
- 每规则一文件，文件名即规则类型名（`insert.py`、`regex.py`）。
- 版本号、日期、机器名不写进目录名。

## 依赖与引用边界

- 单向：`gui`/`cli` → `session` → `engine`；`session` → `fs`；`engine` 与 `rules` 不 import `fs`、`session`、`gui`（纯函数，无 IO）。
- `pyproject.toml` 是依赖与工具配置唯一真源。
- 例外必须写 `docs/adr/NNNN-短标题.md`。

## 校验方式

- 干净 venv `pip install -e .[dev]` 后 `pytest` 全过；`ruff check` 无错。
- 依赖方向由测试 `test_architecture.py` 静态断言（engine/rules 源码不得 import fs/session/gui）。
- 打包产物在交付路径做真启动冒烟（窗口渲染＋预览＋执行＋撤销），冒烟不替代真实业务验收。
- 规范只有文档而没有校验时视为未生效。

## 变更记录

见 `docs/adr/`，只追加不覆盖。