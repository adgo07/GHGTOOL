# TASK_STATE

## 当前工作包

G02 Canonical 数据与 SQLite 基础（已完成并通过验收）

## 状态

G02_PASS_WAITING_FOR_USER_TO_START_G03

## 阶段验收状态

- G00 验收结论：PASS。
- G01 初次验收：FAILED；能量单位共同基准和领域枚举字符串绕过问题已修复。
- G01 重新验收结论：PASS（本轮用户已明确确认）。
- G02 首次验收结论：FAILED；已按 Sol 意见完成返工，当前等待重新验收。
- G02 再次验收结论：FAILED；发现热力因子仍错误引用钢铁生产附件，本轮已改为 GB/T 32150—2025 标准条款来源。
- G02 最终重新验收结论：PASS（2026-09-11）；验收实施基线为 `78ff1f6`，确认第二次返工已解决热力因子来源问题。
- G03 未开始；G02 通过后已满足进入条件，但仍须由用户另行启动 G03 Goal。

## 已完成

- 新增 specs/common/canonical_catalog.schema.json，为 Canonical JSON 建立严格结构、枚举、日期、URI、Decimal 字符串和未知字段约束。
- 新增 packages/reference_data/validation.py 和 scripts/validate_canonical.py：构建前校验稳定 ID、来源引用、官方 HTTPS URL、参数/因子引用、单位白名单、Decimal 值和规范化换算。
- Canonical 源采用 JSON 这一已批准的 JSON/YAML 载体变体：data-source/carbon_accounting/catalog.json。
- 首批目录包含 9 个标准：GB/T 32150—2025、GB/T 32151.34—2024，以及其余 7 项经官方目录核对的标准元数据；7 项计划标准没有参数引用、排放源引用或计算规则，GB/T 32151.34 仅关联其标准专属的 3 个天然气参数。
- 首批来源包含 12 条；每个标准均绑定官方来源 ID 和官方 URL。标准全文、PDF 和计算公式未复制进 Canonical Source。
- Canonical schema、校验器与 SQLite CHECK 统一使用 G01 的 OfficialStatus、SourceType、ReviewStatus、ParameterType 和 ValueType；标准职责拆分为发布单位、主管部门和归口部门。
- 三项 2023 版标准名称已按官方目录修正；电力公告来源补全为生态环境部、国家统计局联合发布；0.11 热力因子定位到 GB/T 32150—2025 第7.5.6～7.5.7条。
- 首批参数/因子包含天然气低位发热量、单位热值含碳量、碳氧化率、2023 年全国电力平均因子、热力缺省因子和 CO₂ GWP100=1，共 6 个参数和 6 个因子；每个数值均有单位、来源定位、版本/年份和审核状态。
- 新增 migrations/catalog/001_initial.sql、migrations/user/001_initial.sql、migrations/records/001_initial.sql，三个 SQLite 数据库物理隔离、独立迁移和独立版本元数据。
- 新增 packages/persistence/sqlite.py、packages/persistence/catalog_builder.py 及两个构建脚本；Canonical 校验通过后按稳定 ID 排序、事务写入并原子替换 catalog.sqlite，可重复重建。
- 新增 tests/test_g02_canonical.py 和 tests/test_g02_persistence.py，覆盖 schema 错误、重复 ID、缺失来源、单位错误、浮点值、未知字段、错误规范化值、G01 枚举一致性、标准职责/名称、联合发布机关、专属参数、热力原始来源、三库隔离、全新创建、幂等迁移、重建一致性和非法源阻断。
- 计算表/ 下 7 个用户参考文件未修改、未纳入 Git；最终 SHA256 与既有基线一致。

## 未执行或未开始

- G03 公共桌面外壳、首页、导航、Logo 和禁用入口未执行；G02 已经 PASS，等待用户另行启动新的 G03 Goal。
- G04 及以后页面、规则解析、推荐服务、GB/T 32151.34 计算、记录闭环、报告/导出和 Windows 安装包未执行。
- 完整 26 种燃料、碳酸盐、蒸汽焓值和完整 AR6 GWP 表未录入；G02 只录入 HANDOFF.md 规定的最小集合。
- 未引入 YAML 解析依赖；本阶段选择 JSON 作为实际 Canonical 源文件，避免在没有批准 loader/依赖时静默解释 YAML。
- 未生成或提交正式运行时 SQLite 构建产物；本轮仅在 tmp\g02-rework-validation.sqlite 和 tmp\g02-rework-databases\ 下生成被忽略的验证数据库，数据库仍由脚本在目标目录按需生成。

## 最后测试

- G02 定向命令：.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence -v
- G02 定向结果：21 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量命令：.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
- 项目全量结果：39 个通过，0 个失败，0 个错误，0 个跳过（使用项目 .venv，Python 3.12.14，PySide6 6.11.2）。
- 备用系统 Python 全量收集曾因未安装 PySide6 产生 1 个导入错误；随后使用项目规定的 .venv 完成上述全量测试，该环境错误不计为项目测试结果。
- CLI 验证：.venv\Scripts\python.exe scripts\validate_canonical.py，成功，输出 9 standards, 12 sources, 6 parameters, 6 factors。
- CLI 构建：.venv\Scripts\python.exe scripts\build_catalog.py --source data-source\carbon_accounting\catalog.json --output tmp\g02-rework-validation.sqlite --app-version 0.1.0，成功从 Canonical 重建 SQLite。
- 依赖核验：.venv\Scripts\python.exe -m pip check，输出 No broken requirements found.。
- 编译核验：.venv\Scripts\python.exe -m compileall -q packages/core packages/reference_data packages/persistence tests scripts，成功。
- 隔离导入：.venv\Scripts\python.exe -S 成功导入 Canonical loader 和迁移 runner，并验证 9 个标准、1 个 catalog 迁移。
- 分层/禁入扫描：packages/core 和 packages/reference_data 未发现 PySide6、sqlite3、Windows API 或 QSql；Canonical/package 未发现标准全文字段；未发现 G03 应用/UI 文件变化。
- 受保护文件检查：7/7 个 计算表/ 文件 SHA256 与基线一致。
- Sol 最终验收复核：G02 定向测试 21/21、项目全量测试 39/39、Canonical 校验及 catalog/三库从零构建均通过；项目依赖无破损。
- Sol 原文复核：GB/T 32150—2025 第7.5.6～7.5.7条明确支持热力因子实测优先或采用 0.11 tCO₂/GJ；GB/T 32151.34—2024 第5.2.6.2及表C.3给出相同值。
- 测试时间：2026-09-11。

## Git

- 当前分支：main。
- G01 返工及前置修复提交仍保留；G02 原收口提交：e4d9b03 feat: establish G02 canonical data and database foundations。
- G02 返工实施提交：ba72f9a fix: address G02 catalog acceptance findings。
- G02 第二次返工实施提交：0cd6ed3 fix: correct G02 heat factor provenance。
- 未使用破坏性 Git 操作；未修改 计算表/、.venv/ 或既有用户临时文件；本轮验证数据库为新生成的临时产物。
- 工作区另有未跟踪 docs/handoffs/，非本轮新增或修改，未暂存。

## 阻塞项

- 无实现阻塞项。
- 阶段门禁：G02 已获 Sol PASS，允许由用户另行启动 G03；本次验收落盘未创建或执行 G03。

## 下一步

1. 等待用户向 Luna Max 发出 G03 Goal 启动指令。
2. G03 必须继续遵守 `HANDOFF.md` 的范围，只实现公共桌面外壳、首页、导航、Logo、空状态和 Excel 导入禁用占位。
3. 不得在 G03 中提前实施 G04 或后续阶段内容。
