# TASK_STATE

## 当前工作包

G03 公共桌面外壳与导航

## 状态

G03_PASS_WAITING_FOR_USER_TO_START_G04

## 阶段验收状态

- G00 验收结论：PASS。
- G01 初次验收：FAILED；能量单位共同基准和领域枚举字符串绕过问题已修复。
- G01 重新验收结论：PASS（本轮用户已明确确认）。
- G02 首次验收结论：FAILED；已按 Sol 意见完成返工，当前等待重新验收。
- G02 再次验收结论：FAILED；发现热力因子仍错误引用钢铁生产附件，本轮已改为 GB/T 32150—2025 标准条款来源。
- G02 最终重新验收结论：PASS（2026-09-11）；验收实施基线为 `78ff1f6`，确认第二次返工已解决热力因子来源问题。
- G03 正式验收结论：PASS WITH MINOR FIXES（2026-09-12）；验收实施基线为 `05a67f4`。桌面外壳可运行，但两项冻结规范细节须修正后重新验收。
- G03 小修已完成（2026-09-12）；修正提交为 `aaefe29`。
- G03 正式重新验收结论：PASS（2026-09-12）；被验收 HEAD 为 `e57af51`，确认两项小修全部关闭。
- G04 未开始；未创建或执行 G04 Goal。

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
- 新增 packages/ui/design_tokens.py、icons.py、routing.py、view_models.py、pages.py 和 shell.py，提供共享 Qt Widgets 外壳、固定侧栏、页面堆栈、路由和安全占位页。
- 应用接入 G03 温室气体产品视图模型：7 个固定导航入口、120 px 品牌区、176 px 等比例 Logo、首页工作台、最近记录/标准空状态和底部设置入口。
- Excel 导入只保留可达的占位页；文件、标准、模板、下一步和导入控件全部禁用且不可聚焦，没有文件读取、导入或计算动作。
- 新增 tests/test_g03_shell.py，覆盖路由可达性、首页空状态、导航顺序/尺寸、Logo 比例、窗口边距、滚动策略和 Excel 控件禁用。
- 按 G03 验收意见修正首页 StartPanel 顺序为“新建核算 → Excel 导入（暂未开放）→ 查看标准库”。
- 将导航图标的激活/非激活颜色和品牌区高度统一改为 `packages/ui/design_tokens.py` 中的 Design Token，Shell 不再写死 `#FFFFFF` 或 `120`。
- 新增首页固定按钮顺序和 Shell Design Token 使用回归断言；本轮仅修改 G03 UI 与测试。
- 计算表/ 下 7 个用户参考文件未修改、未纳入 Git；最终 SHA256 与既有基线一致。

## 未执行或未开始

- G04 标准库与参数因子库页面未执行；G03 已通过，允许由用户另行启动 G04 Goal，本次未启动 G04。
- G04 及以后页面、规则解析、推荐服务、GB/T 32151.34 计算、记录闭环、报告/导出和 Windows 安装包未执行。
- 完整 26 种燃料、碳酸盐、蒸汽焓值和完整 AR6 GWP 表未录入；G02 只录入 HANDOFF.md 规定的最小集合。
- 未引入 YAML 解析依赖；本阶段选择 JSON 作为实际 Canonical 源文件，避免在没有批准 loader/依赖时静默解释 YAML。
- 未生成或提交正式运行时 SQLite 构建产物；本轮仅在 tmp\g02-rework-validation.sqlite 和 tmp\g02-rework-databases\ 下生成被忽略的验证数据库，数据库仍由脚本在目标目录按需生成。

## 最后测试

- G03 返工定向命令：$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g03_shell -v
- G03 返工定向结果：8 个通过，0 个失败，0 个错误，0 个跳过。
- G03 返工与项目全量命令：$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
- G03 返工与项目全量结果：47 个通过，0 个失败，0 个错误，0 个跳过（使用项目 .venv，Python 3.12.14，PySide6 6.11.2）。
- G03 L3 编译：.venv\Scripts\python.exe -m compileall -q apps packages tests scripts，成功。
- G03 L3 依赖：.venv\Scripts\python.exe -m pip check，输出 No broken requirements found.。
- G03 L3 资源/UI 探查：Logo 3060x759、7 个 SVG 图标、AppShell 成功创建。
- G03 L3 禁入扫描：G03 范围未发现 sqlite3、QSql、QFileDialog、表格查询控件、报告/导出组件或其他后续业务实现。
- G03 L3 保护检查：计算表/ Git 差异为空。
- G03 初次验收复核：定向测试 6/6、项目全量回归 45/45、compileall 和 pip check 均通过；本轮返工后已重新执行并记录 8/8、47/47。
- Sol G03 原生 Qt 视觉复核：1180×720 与 1920×1080 首页无重叠，Logo 保持约 4.03:1；Excel 占位页布局正常且内部控件全部禁用。Windows 自动化辅助进程因沙箱初始化失败不可用，已改用原生 Qt 窗口截图和程序化路由/控件测试补充验证。
- Sol G03 正式重新验收定向命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g03_shell -v`；结果 8 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G03 正式重新验收全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；结果 47 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G03 正式重新验收辅助检查：`compileall` 成功，`pip check` 无破损依赖；范围扫描无 G04 越界，Shell 不再包含验收指出的 `setFixedHeight(120)` 与 `#FFFFFF` 硬编码。
- Sol G03 正式重新验收视觉与控件检查：原生 Qt 1180×720 首页及 Excel 占位页无重叠，Logo 为 176×43（约 4.09:1），无横向滚动；Excel 页 6 个内部控件全部禁用且不可聚焦。宽屏 1920×1080 的布局规则由 GUI 自动化测试覆盖。
- Sol G03 正式重新验收时间：2026-09-12。

- G02 历史定向命令：.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence -v
- G02 定向结果：21 个通过，0 个失败，0 个错误，0 个跳过。
- G02 历史项目全量命令：.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
- G02 历史项目全量结果：39 个通过，0 个失败，0 个错误，0 个跳过（使用项目 .venv，Python 3.12.14，PySide6 6.11.2）。
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
- G03 实施提交：`617d982 feat: implement G03 desktop shell`。
- G03 小修提交：`aaefe29 fix: close G03 minor acceptance findings`。
- G03 正式重新验收的被验收 HEAD：`e57af51 docs: record G03 minor fixes handoff`。
- 未使用破坏性 Git 操作；未修改 计算表/、.venv/ 或既有用户临时文件；本轮验证数据库为新生成的临时产物。
- 工作区另有未跟踪 docs/handoffs/，非本轮新增或修改，未暂存。

## 阶段门禁

- G03 小修项1：已修正并由回归测试锁定首页按钮顺序。
- G03 小修项2：已修正并由回归测试锁定导航图标颜色与品牌区高度使用 Design Token。
- G03 已通过，阶段门禁已解除；允许由用户另行启动 G04，本次未启动 G04。

## 下一步

1. G03 已通过，允许由用户另行启动 G04。
2. 本次验收未创建 Goal、未启动或实施 G04。
