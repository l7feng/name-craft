# ADR 0004：UCS 命名规则与随包分类数据

- 日期：2026-11-09
- 状态：已采纳

## 背景

人类要求在 namecraft 中加入 UCS（Universal Category System 8.2.1）命名规则，并把规范文件同时放进软件与个人知识库。UCS 的 CatID 必须来自官方分类表，不能由程序猜写；同时 `rules` 层是纯函数，不允许做文件 IO。

## 决策

1. 分类真源放在仓库 `docs/UCS分类表-8.2.1.tsv`（753 行，UTF-8、制表符分隔），随包分发。
2. `scripts/build_ucs.py` 从 TSV 生成 `src/namecraft/ucs.py` 纯常量模块（`CATEGORIES`、`CATIDS`、`BY_ID`、`canonical`），规则运行时只导入常量，不读文件。
3. `rules/ucs.py` 只负责文件名结构：`CatID(-UserCategory)_(VendorCategory-)FXName_CreatorID_SourceID_UserData`，空块省略；非法字符与下划线按规范处理；已有的 CatID 前缀可剥离。
4. 界面通过桥接 `ucs_categories()` 取同一份数据做搜索选择器；`ucs_guide()` 读取随包规范供内置查看，`save_ucs_doc(kind)` 负责另存。
5. 打包规格把 `docs/` 收进 `_internal/docs`（onedir）或解包目录（onefile）；交付目录另放一份可读副本。

## 结果

- CatID 集合与 TSV 由 `tests/test_ucs_data.py` 做逐项一致性断言，防止生成物漂移。
- 未知 CatID 在预览阶段直接报错，不产生猜测值；大小写不敏感但输出标准写法。
- 升级 UCS 版本时替换 TSV、重跑脚本、重跑测试即可；规则实现通常不变。
- 未采用在规则内实时读 TSV：会破坏 `rules` 纯函数边界，并让打包路径与测试路径变复杂。
