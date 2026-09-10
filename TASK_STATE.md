# TASK_STATE

## 当前工作包

G02 Canonical 数据与 SQLite 基础

## 状态

READY_FOR_SOL_ACCEPTANCE

## 阶段验收状态

- G00 验收结论：PASS。
- G01 初次验收：FAILED；能量单位共同基准和领域枚举字符串绕过问题已修复。
- G01 重新验收结论：PASS（本轮用户已明确确认）。
- G02 已按 HANDOFF.md 完成实现、测试和收口检查，当前等待 Sol 验收。
- G03 未开始；本轮没有创建或执行 G03 Goal。

## 已完成

- 新增 specs/common/canonical_catalog.schema.json，为 Canonical JSON 建立严格结构、枚举、日期、URI、Decimal 字符串和未知字段约束。
- 新增 packages/reference_data/validation.py 和 scripts/validate_canonical.py：构建前校验稳定 ID、来源引用、官方 HTTPS URL、参数/因子引用、单位白名单、Decimal 值和规范化换算。
- Canonical 源采用 JSON 这一已批准的 JSON/YAML 载体变体：data-source/carbon_accounting/catalog.json。
- 首批目录包含 9 个标准：GB/T 32150—2025、GB/T 32151.34—2024，以及其余 7 项经官方目录核对的标准元数据；7 项计划标准没有参数引用、排放源引用或计算规则。
- 首批来源包含 12 条；每个标准均绑定官方来源 ID 和官方 URL。标准全文、PDF 和计算公式未复制进 Canonical Source。
- 首批参数/因子包含天然气低位发热量、单位热值含碳量、碳氧化率、2023 年全国电力平均因子、热力缺省因子和 CO₂ GWP100=1，共 6 个参数和 6 个因子；每个数值均有单位、来源定位、版本/年份和审核状态。
- 新增 migrations/catalog/001_initial.sql、migrations/user/001_initial.sql、migrations/records/001_initial.sql，三个 SQLite 数据库物理隔离、独立迁移和独立版本元数据。
- 新增 packages/persistence/sqlite.py、packages/persistence/catalog_builder.py 及两个构建脚本；Canonical 校验通过后按稳定 ID 排序、事务写入并原子替换 catalog.sqlite，可重复重建。
- 新增 tests/test_g02_canonical.py 和 tests/test_g02_persistence.py，覆盖 schema 错误、重复 ID、缺失来源、单位错误、浮点值、未知字段、错误规范化值、三库隔离、全新创建、幂等迁移、重建一致性和非法源阻断。
- 计算表/ 下 7 个用户参考文件未修改、未纳入 Git；最终 SHA256 与既有基线一致。

## 未执行或未开始

- G03 公共桌面外壳、首页、导航、Logo 和禁用入口未执行，等待本阶段 Sol PASS 后由用户启动新的 G03 Goal。
- G04 及以后页面、规则解析、推荐服务、GB/T 32151.34 计算、记录闭环、报告/导出和 Windows 安装包未执行。
- 完整 26 种燃料、碳酸盐、蒸汽焓值和完整 AR6 GWP 表未录入；G02 只录入 HANDOFF.md 规定的最小集合。
- 未引入 YAML 解析依赖；本阶段选择 JSON 作为实际 Canonical 源文件，避免在没有批准 loader/依赖时静默解释 YAML。
- 未生成或提交运行时 SQLite 构建产物；数据库由脚本在目标目录按需生成。

## 最后测试

- G02 定向命令：.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence -v
- G02 定向结果：15 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量命令：$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v
- 项目全量结果：33 个通过，0 个失败，0 个错误，0 个跳过。
- CLI 验证：.venv\Scripts\python.exe scripts\validate_canonical.py，输出 valid: 9 standards, 12 sources, 6 parameters, 6 factors。
- CLI 构建：.venv\Scripts\python.exe scripts\build_catalog.py --output 临时目录\catalog.sqlite 和 .venv\Scripts\python.exe scripts\initialize_databases.py --output-dir 临时目录 均成功生成三库。
- 依赖核验：.venv\Scripts\python.exe -m pip check，输出 No broken requirements found.。
- 编译核验：.venv\Scripts\python.exe -m compileall -q packages/core packages/reference_data packages/persistence tests scripts，成功。
- 隔离导入：.venv\Scripts\python.exe -S 成功导入 Canonical loader 和迁移 runner，并验证 9 个标准、1 个 catalog 迁移。
- 分层/禁入扫描：packages/core 和 packages/reference_data 未发现 PySide6、sqlite3、Windows API 或 QSql；Canonical/package 未发现标准全文字段；未发现 G03 应用/UI 文件变化。
- 受保护文件检查：7/7 个 计算表/ 文件 SHA256 与基线一致。
- 测试时间：2026-09-11。

## Git

- 当前分支：main。
- G01 返工及前置修复提交仍保留；G02 收口提交将在本报告和状态文件完成后形成。
- 未使用破坏性 Git 操作；未修改 计算表/、.venv/ 或用户临时文件。

## 阻塞项

- 无实现阻塞项。
- 阶段门禁：G02 交付后停止，等待 Sol 验收；未获 PASS 前不得进入 G03。

## 下一步

1. Sol 复核 Canonical 来源、最小数据、单位规范化和三库职责隔离。
2. Sol 复核 15 个 G02 定向测试、33 个全量测试及 L3 检查记录。
3. 只有 G02 获得 PASS 后，才由用户启动新的 G03 Goal。
