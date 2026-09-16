# TASK_STATE

## 当前工作包

G06 GB/T 32151.34—2024 手工录入、专业校验与高精度计算

## 状态

G06_READY_FOR_SOL_REACCEPTANCE

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
- G04 Goal 已创建并提交（2026-09-12）；正式验收结论为 FAIL，被验收 HEAD 为 `812af02`。
- G04 返工已完成（2026-09-12）；修正提交为 `00c7ea6`，当前等待 Sol 重新验收。
- G04 返工补充空结果详情清空回归测试（2026-09-12）；测试提交为 `56cdd60`，当前等待 Sol 重新验收。
- G04 正式重新验收结论：PASS（2026-09-12）；被验收 HEAD 为 `28dd8c9`，两项首次验收缺陷均已关闭。
- G04已通过，允许由用户另行启动G05；本轮已创建并执行G05 Goal。
- G05 实施已完成（2026-09-12）；实现提交为 `e815d50`，当前停止等待 Sol 验收；G06 未创建、未执行。
- G05 正式验收结论：FAIL（2026-09-13）；被验收 HEAD 为 `cd880f2`。默认规则集未完整转录冻结映射，且最新官方因子、冲突快照和显式覆盖存在阻断性错误。
- G05 返工已完成（2026-09-13）；返工提交为 `549bca0`，已按冻结映射补齐默认规则、修正官方最新因子选择、冲突快照门禁和显式 OVERRIDE 关系，当前等待 Sol 重新验收。
- G05 正式重新验收结论：FAIL（2026-09-13）；被验收 HEAD 为 `c83df46`。既有回归测试通过，但默认规则仍缺少冻结规则、存在行业关系/覆盖对象错误，并有多条原始标准条款定位错误。
- G05 第二次返工已完成（2026-09-13）；实现与回归测试提交为 `9e74024`，当前停止等待 Sol 再次验收。
- G05 第二次正式重新验收结论：FAIL（2026-09-13）；被验收 HEAD 为 `1a7bd95`。普通购电与非化石购电未被区分，非化石规则会无条件覆盖普通电力规则并错误推荐全国平均因子；电热 SPECIALIZE 也未形成真实继承关系，冻结规则清单和部分行业来源定位仍不完整。
- 多种电力消费形式产品决策已批准并落盘（2026-09-13）：同一企业、同一核算期允许多条不同电力明细；批准新增独立 Canonical 非化石能源电力参数与零因子。此前 G05 第三次返工的 Canonical 缺口阻塞已获得决策，不代表 G05 已完成或通过验收。
- G05 第三次正式重新验收结论：PASS（2026-09-13）；被验收 HEAD 为 `f080f115f0d7a31249befc0703cfec132c19e515`，多种电力消费形式决策及全部 G05 MUST 已核对通过。
- G05已通过，允许由用户另行启动G06。
- G06 已完成实现与 R6 映射测试向量纠错回归；Sol 正式验收结论为 FAIL（2026-09-13），未创建或执行 G07。
- G06 正式重新验收结论：FAIL（2026-09-16）；被验收 HEAD 为 `ea4ff2eb3acb9c5d8c299ce7a09377dbad48ba9a`。首次验收的页面缺口大部分已关闭，但材料成分性质约束、多电力明细参数状态展示、其他行业活动与运输手工声明仍未满足 G06 MUST；不允许进入 G07。

## G06 BLOCKED 停止点（历史，2026-09-13；Sol R6 决策后已解除）

问题：

- G06 的正式映射文件 TV-CAR-FML-008 将式（8）石墨化向量（GPM=10、GPMFC=0.005、GTA=100、GTAFC=0.007、GWT=0.05、GP=95、GPFC=0.006、GPMVar=0.10、K3=0.35）预期写为 3.364166666… tCO₂。
- 正式标准 GB/T 32151.34—2024 第 5.2.4 条、PDF 第 13 页的式（8）仅包含 GPM×GPMVar×K3×44/16 挥发分项；按同一输入执行得到 1.439166666666666666666666667 tCO₂。
- HANDOFF.md 第 473 行明确要求发现映射与标准原文疑似不一致时必须 BLOCKED，不得按经验改公式。

证据：

- D:\MD仓库\杂\碳排放计算软件\GB T 32151.34—2024 炭素材料生产企业映射方案.md:728：TV-CAR-FML-008 期望为 3.364166666…。
- packages/standards/carbon_material.py:594-597：当前实现按正式标准式（8）执行。
- 只读执行 graphitization_emission(...)：结果为 1.439166666666666666666666667。
- G06 定向测试最新结果：8 通过、1 失败；唯一失败为该冲突向量，未继续执行 G06 全量验收。

为什么不能按原方案继续：

- 修改实现以迎合 3.364166666… 会偏离正式标准式（8）；修改映射测试期望则会偏离 HANDOFF.md 冻结映射。两者属于计算口径/标准解释变化，不能由 Luna 自行决定。

可选方案 A：

- Sol 确认以正式标准第 5.2.4 条式（8）为准，将 TV-CAR-FML-008 修正为 1.439166666…，并允许继续 G06。

可选方案 B：

- Sol 提供式（8）采用 3.364166666… 的正式解释、修订映射或批准决策，明确额外项及其来源后，再修改计算与测试。

建议：

- 采用方案 A，保留当前正式标准公式实现；但在 Sol 明确确认前不继续 G06。

需要 Sol 决策的具体问题：

- G06 式（8）在上述固定输入下，最终批准值应为 1.439166666666666666666666667（正式标准公式）还是 3.364166666…（当前冻结映射向量）？
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
- 新增首页固定按钮顺序和 Shell Design Token 使用回归断言；G03 小修阶段仅修改 G03 UI 与测试。
- 新增 `packages/standards/catalog.py` 平台无关的标准、来源、对象、参数和因子只读读模型与 Repository 契约；Domain/读模型不依赖 PySide6 或 SQLite。
- 新增 `packages/persistence/catalog_repository.py`，以只读 SQLite 连接加载 Canonical 构建的 `catalog.sqlite`，集中完成日期、Decimal、JSON 引用和 G01 枚举映射；缺失目录由空 Repository 安全降级。
- 新增 `packages/application/catalog_queries.py`，提供标准搜索/行业/年份/状态筛选、官方状态与日期推导、标准详情、参数/因子按对象或来源查询、类型/审核标签和来源追溯；未实现 G05 推荐解析。
- 新增 G04 `StandardLibraryPage` 与 `ParameterFactorLibraryPage`：标准详情显示发布单位、主管部门、归口部门、标准关系、参数/因子和官方来源；只有当前 GB/T 32151.34—2024 可进入新建核算，其余标准显示“核算模块待开发”并禁用入口。
- G04 参数/因子详情显示值、单位、年份、有效期、适用标准、来源定位、来源发布单位、审核状态和官方 URL 动作；官方 URL 缺失、目录数据库缺失或可选详情为空时安全降级，不制造标准全文或假数据。
- 新增 `tests/test_g04_catalog.py`，覆盖标准号/行业/年份/状态、日期推导、标准详情、可核算路由、对象/来源查询、来源追溯、G01 枚举筛选、URL 缺失和空目录启动。
- G04 未实现通用规则解析、参数推荐引擎、核算公式、报告/导出、记录闭环或 G05/G06 业务。
- G04 返工修复列表刷新后的详情同步：标准/参数列表重建后显式渲染当前首项，旧详情控件先隐藏再销毁，详情状态、官方 URL 和核算入口绑定当前可见对象。
- G04 返工增加 `CatalogValueCategory`，按来源声明的 `STANDARD_DEFAULT`、其他适用元数据和 `HISTORICAL`/弃用状态明确展示“推荐值（标准缺省）”“其他适用值”“历史值”及审核状态；未实现上下文驱动的场景推荐。
- G04 返工测试加入标准详情/官方 URL 一致性、天然气参数详情一致性、空结果清空详情、同一参数三版本分类夹具和对应断言。
- 计算表/ 下 7 个用户参考文件未修改、未纳入 Git；最终 SHA256 与既有基线一致。
- G05 新增平台无关的 `EffectiveRuleResolver`，覆盖 BASE、SPECIALIZE、OVERRIDE、EXTEND、SUPPLEMENT、CONFLICT_REVIEW，保留有效规则、继承/覆盖轨迹，并在未解决冲突时阻断。
- G05 新增上下文驱动 `ParameterResolver`，按标准、期间、地区、行业、对象、参数类型、排放源、气体、电力模式、核算框架及实测/证据上下文选择推荐值；行业明确规则优先于通用规则，歧义要求确认理由。
- G05 扩展因子和不可变参数快照，保存实际值、单位、因子/来源版本、来源定位、年度、选择方法、理由、标准和快照时间；参数库更新不会改变已创建快照。
- G05 新增通用活动数据来源等级、来源证据、活动数据校验契约、聚合契约和 `RuleRepository` 协议；未引入 UI、SQLite 或行业专属计算公式。
- G05 新增 `tests/test_g05_rules.py`，通过内存 Parameter/Rule Repository 覆盖关系优先级、覆盖/补充/冲突、官方/实测推荐、歧义确认、快照不可变性、活动校验、聚合及枚举字符串拒绝。

## 未执行或未开始

- G06 已完成本阶段实现与回归（2026-09-13）；G07、正式记录闭环、报告/导出和 Windows 安装包未执行。
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
- G06 定向尝试：QT_QPA_PLATFORM=offscreen；.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material -v；最新结果 8 个通过、1 个失败、0 个错误；失败为冻结映射与正式式（8）冲突，未执行 G06 全量、L2/L3 验收。
- G03 L3 保护检查：计算表/ Git 差异为空。
- G03 初次验收复核：定向测试 6/6、项目全量回归 45/45、compileall 和 pip check 均通过；本轮返工后已重新执行并记录 8/8、47/47。
- Sol G03 原生 Qt 视觉复核：1180×720 与 1920×1080 首页无重叠，Logo 保持约 4.03:1；Excel 占位页布局正常且内部控件全部禁用。Windows 自动化辅助进程因沙箱初始化失败不可用，已改用原生 Qt 窗口截图和程序化路由/控件测试补充验证。
- Sol G03 正式重新验收定向命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g03_shell -v`；结果 8 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G03 正式重新验收全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；结果 47 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G03 正式重新验收辅助检查：`compileall` 成功，`pip check` 无破损依赖；范围扫描无 G04 越界，Shell 不再包含验收指出的 `setFixedHeight(120)` 与 `#FFFFFF` 硬编码。
- Sol G03 正式重新验收视觉与控件检查：原生 Qt 1180×720 首页及 Excel 占位页无重叠，Logo 为 176×43（约 4.09:1），无横向滚动；Excel 页 6 个内部控件全部禁用且不可聚焦。宽屏 1920×1080 的布局规则由 GUI 自动化测试覆盖。
- Sol G03 正式重新验收时间：2026-09-12。

- G04 定向命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g04_catalog -v`
- G04 定向结果：8 个通过，0 个失败，0 个错误，0 个跳过。
- G04 项目全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`
- G04 项目全量结果：55 个通过，0 个失败，0 个错误，0 个跳过（项目 .venv，Python 3.12.14，PySide6 6.11.2）。
- G04 L3 编译：`.venv\Scripts\python.exe -m compileall -q apps packages tests scripts`，成功。
- G04 L3 依赖：`.venv\Scripts\python.exe -m pip check`，输出 `No broken requirements found.`。
- G04 Canonical/SQLite：`.venv\Scripts\python.exe scripts\validate_canonical.py` 成功（9 standards、12 sources、6 parameters、6 factors）；从 Canonical 构建 `tmp\g04-catalog-validation.sqlite` 成功。
- G04 分层/禁入扫描：UI 和应用边界未直接导入 sqlite3；未发现 QFileDialog、QSql、reportlab、matplotlib、G05 或推荐解析入口；SQLite 仅存在于 persistence 适配器。
- G04 保护检查：`git diff --name-only -- '计算表/**'` 为空；未修改 `计算表/` 用户参考文件。
- G04 未执行项：未启动系统浏览器验证外链，避免测试产生外部副作用；官方 URL 存在性、缺失时禁用和按钮路由均由 Qt 定向测试覆盖。
- G04 返工定向命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g04_catalog -v`
- G04 返工定向结果：9 个通过，0 个失败，0 个错误，0 个跳过；新增断言覆盖搜索/筛选后列表、详情、URL 一致性、空结果清空详情及三类多版本值。
- G04 返工全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`
- G04 返工全量结果：56 个通过，0 个失败，0 个错误，0 个跳过。
- G04 返工 L3：`compileall` 成功；`pip check` 输出 `No broken requirements found.`；Canonical 校验输出 9 standards、12 sources、6 parameters、6 factors；从 Canonical 重建 `tmp\g04-rework-validation.sqlite` 成功。
- G04 返工边界/保护检查：UI 无 sqlite3 直接导入，未发现 G05、QSql、QFileDialog、reportlab 或 matplotlib 实现；`计算表/` Git 差异为空。
- Sol G04 正式验收定向命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g04_catalog -v`；8 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G04 正式验收全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；55 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G04 正式验收构建检查：Canonical 校验通过（9 standards、12 sources、6 parameters、6 factors），`catalog.sqlite` 从 Canonical Source 重建成功；`compileall` 和 `pip check` 通过。
- Sol G04 原始来源复核：本地 GB/T 32150—2025 第7.5.6～7.5.7条、GB/T 32151.34—2024 第5.2.6.2与表C.1/表C.3支持当前 0.11、389.31、0.0153、0.99 等展示值；国家标准平台和生态环境部官方页面支持当前日期、状态及电力来源元数据。
- Sol G04 验收级交互探查发现失败：搜索 `32151.34` 后列表仅剩 GB/T 32151.34—2024，但详情仍显示 GB/T 32150—2025，当前详情按钮打开的也是 32150 官方 URL；搜索“天然气”后列表为 3 项天然气参数，详情仍停留在 CO₂ GWP。现有 8 项测试没有识别该错配。
- Sol G04 多版本检查发现失败：读模型、查询服务和页面只显示 `ValueType`/审核状态，没有明确产生或展示“推荐值、其他适用值、历史值”三类，也没有同一参数多版本测试数据或断言。
- Sol G04 Windows Computer Use 辅助进程经重试与重置后仍因 `windows sandbox failed: helper_unknown_error: setup refresh had errors` 无法连接；已用原生 Qt 截图和控件状态探查完成替代核验。
- Sol G04 正式验收时间：2026-09-12。
- Sol G04 正式重新验收定向命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g04_catalog -v`；9 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G04 正式重新验收全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；56 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G04 正式重新验收构建检查：`.venv\Scripts\python.exe scripts\validate_canonical.py` 通过（9 standards、12 sources、6 parameters、6 factors）；从 Canonical Source 重建临时 `catalog.sqlite` 成功；`compileall` 成功；`pip check` 输出 `No broken requirements found.`。
- Sol G04 正式重新验收交互探查：搜索 `32151.34` 后列表、详情标准号、按钮属性及实际传递给 `QDesktopServices.openUrl` 的官方 URL 一致；搜索“天然气”后列表和详情一致；两类空结果均清空旧详情；同一参数三版本明确显示推荐值、其他适用值、历史值及审核状态。
- Sol G04 正式重新验收来源核对：返工提交未修改 Canonical 数据、标准元数据、参数值、因子值或来源；首次正式验收对本地标准原文及官方页面的核对结论继续成立。
- Sol G04 正式重新验收范围检查：页面只经 Application Service/Repository 读取数据；未发现 G05 场景推荐、计算快照或后续业务实现；`计算表/` 无 Git 差异。
- Sol G04 正式重新验收环境说明：Windows Computer Use 辅助进程仍因系统沙箱初始化错误不可用，已用 Qt 离屏控件探查和原生截图替代；该环境问题不影响本次 PASS。
- Sol G04 正式重新验收时间：2026-09-12；被验收 HEAD：`28dd8c9`。

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

- G05 定向命令：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`
- G05 定向结果：8 个通过，0 个失败，0 个错误，0 个跳过。
- G05 定向覆盖：BASE/SPECIALIZE/OVERRIDE/EXTEND/SUPPLEMENT/CONFLICT_REVIEW 关系、未决冲突阻断、行业规则优先、宁夏场景全国电力因子选择、热力实测优先与 0.11 回退、歧义确认、快照版本/来源/不可变性、活动数据校验、聚合契约、内存 Parameter/Rule Repository 和领域枚举字符串拒绝。
- G05 项目全量命令：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`
- G05 项目全量结果：64 个通过，0 个失败，0 个错误，0 个跳过（项目 `.venv`，Python 3.12.14）。
- G05 L3 编译：`.venv\Scripts\python.exe -m compileall -q packages apps tests`，成功。
- G05 L3 依赖：`.venv\Scripts\python.exe -m pip check`，输出 `No broken requirements found.`。
- G05 分层/禁入扫描：`packages/core` 和 G05 测试未发现 PySide6、sqlite3、QSql、QWidget、QFileDialog、G06 公式或行业输入页实现。
- G05 保护检查：`git diff --name-only -- 计算表/**` 为空；Canonical、SQLite 迁移和 `计算表/` 均未修改。
- G05 提交前 `git diff --check` 成功；pytest 未作为项目测试命令执行（环境未安装 pytest），按 README 规定的 unittest 命令完成验收测试。
- Sol G05 正式验收定向命令：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；8 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G05 正式验收全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；64 个通过，0 个失败，0 个错误，0 个跳过。
- Sol G05 正式验收辅助检查：`.venv\Scripts\python.exe -m compileall -q packages apps tests` 成功；`.venv\Scripts\python.exe -m pip check` 输出 `No broken requirements found.`；Domain 未发现 PySide6/SQLite 依赖，`计算表/` 无 Git 差异。
- Sol G05 原文与映射复核：直接核对 GB/T 32150—2025 PDF 第13～17页及 SHA256 `673B85DF6EBEB6CE8894995534EC6EA3E2B7FA4F50B6A03AC0208E2DE34469BC`；活动数据、因子来源优先级、电力/热力实测优先、0.11 缺省值和 GWP 来源表述与冻结映射一致。
- Sol G05 验收探查失败：向生产解析器同时提供 2023 与 2024 全国官方电力因子时，`OFFICIAL_LATEST` 仍选择固定 ID `electricity_national_average_2023`；未解决 `CONFLICT_REVIEW` 可在用户确认分支生成参数快照；未声明 `supersedes_rule_ids` 的 `OVERRIDE` 会静默移除 BASE 且不留下覆盖记录。
- Sol G05 默认规则集检查失败：`default_g05_rules()` 只有 3 条通则参数规则和 5 条行业参数规则，没有装载冻结映射中的边界、总量、逸散阻断及行业覆盖规则，也没有任何实际 `CONFLICT_REVIEW`；其中 6 个规则 ID 在两份冻结映射中不存在，且把 `GEN-PAR-*` 参数 ID 用作 `rule_id`。
- Sol G05 正式验收时间：2026-09-13；被验收 HEAD：`cd880f2`。

## Git

- 当前分支：main。
- G01 返工及前置修复提交仍保留；G02 原收口提交：e4d9b03 feat: establish G02 canonical data and database foundations。
- G02 返工实施提交：ba72f9a fix: address G02 catalog acceptance findings。
- G02 第二次返工实施提交：0cd6ed3 fix: correct G02 heat factor provenance。
- G03 实施提交：`617d982 feat: implement G03 desktop shell`。
- G03 小修提交：`aaefe29 fix: close G03 minor acceptance findings`。
- G03 正式重新验收的被验收 HEAD：`e57af51 docs: record G03 minor fixes handoff`。
- G04 实施提交：`4419a73 feat: implement G04 catalog query pages`。
- G04 正式验收的被验收 HEAD：`812af02 docs: record G04 catalog handoff`。
- G04 返工实施提交：`00c7ea6 fix: close G04 catalog acceptance findings`。
- G04 返工测试提交：`56cdd60 test: cover G04 empty detail reset`。
- G04 正式重新验收的被验收 HEAD：`28dd8c9 docs: record G04 rework handoff`。
- G05 实施提交：`e815d50 feat: implement G05 rule resolution foundation`。
- G05 正式验收的被验收 HEAD：`cd880f2 docs: record G05 delivery`。
- G05 返工实施提交：`549bca0 fix: rework G05 rule resolution acceptance findings`。
- G05 第二次返工实现与测试提交：`9e74024 fix: complete G05 frozen rule mappings`。
- 当前工作区仅保留既有未跟踪 `docs/handoffs/`；未纳入 G05 提交。
- G05 第二次返工已完成并停止等待 Sol 再次验收；G06 未创建、未执行。
- 未使用破坏性 Git 操作；未修改 计算表/、.venv/ 或既有用户临时文件；本轮验证数据库为新生成的临时产物。
- 工作区另有未跟踪 docs/handoffs/，非本轮新增或修改，未暂存。

## 阶段门禁

- G03 小修项1：已修正并由回归测试锁定首页按钮顺序。
- G03 小修项2：已修正并由回归测试锁定导航图标颜色与品牌区高度使用 Design Token。
- G03 已通过，阶段门禁已解除。
- G04 首次正式验收结论为 FAIL；对应缺陷已在 `00c7ea6` 和 `56cdd60` 中修正并由本次重新验收关闭。
- G04 正式重新验收结论为 PASS，阶段门禁已解除。
- G04已通过，允许由用户另行启动G05；本轮 G05 已实施并完成首次正式验收。
- G05 正式验收结论为 FAIL；默认规则转录、最新官方因子选择、冲突快照阻断和显式覆盖语义必须返工。
- G05 返工提交 `549bca0` 已完成上述修正；当前阶段门禁仍保持关闭，等待 Sol 重新验收。
- G05 正式重新验收结论为 FAIL；规则映射完整性、行业关系与原始条款定位仍须再次返工。
- G05 第二次返工提交 `9e74024` 已补齐冻结规则清单、修正行业关系/电热路径和全部指定来源定位；当前阶段门禁保持关闭，等待 Sol 再次验收。
- G05 第二次正式重新验收结论为 FAIL；非化石电力适用条件和取值逻辑、电热 SPECIALIZE 的真实解析关系、冻结 ID 完整性及行业来源定位仍须返工。
- 2026-09-13 已批准多种电力消费形式和独立 Canonical 非化石能源电力零因子；G05 的决策阻塞已解除，但实现与正式验收尚未完成。
- G05 第三次正式重新验收为 PASS，G06 阶段门禁已解除；仅允许由用户另行启动 G06，本次验收未创建或执行 G06。

## 下一步

1. 等待用户另行启动 G06。
2. 启动 G06 时必须重新读取 `AGENTS.md`、`HANDOFF.md` 和 `TASK_STATE.md`，创建一个 G06 Goal，且不得提前执行 G07。

## G05 第一次返工交付状态（历史）

**READY_FOR_SOL_REACCEPTANCE**

- 已按 `HANDOFF.md` 仅返工 G05；没有创建或执行 G06。
- `default_g05_rules()` 现装载 35 条 CommonRuleSet 和 11 条 IndustryRuleSet，包含冻结的边界、总量、逸散执行阻断、实际 `CONFLICT_REVIEW`、行业覆盖关系及来源定位；参数命名空间不再冒充 `rule_id`，未加入未冻结的 GWP 默认规则。
- `OFFICIAL_LATEST` 先按上下文过滤，再按官方因子年度选择；规则固定的旧因子 ID 不再压过更新值。未解决冲突时，用户确认不能形成推荐或快照。
- OVERRIDE 现在强制校验缺失、悬空和不完整的 `supersedes_rule_ids`；非法覆盖保留 BASE 并阻断，只有最终胜者能消解冲突。
- G05 定向测试 12/12、项目全量回归 68/68；compileall、pip check、Canonical 校验、临时 SQLite 三库重建、领域/SQLite 边界和 `计算表/` 保护检查均通过。
- 返工实施提交：`549bca0 fix: rework G05 rule resolution acceptance findings`。
- 当前停止等待 Sol 重新验收；G06 未创建、未执行。

## G05 Sol 正式重新验收记录（2026-09-13）

**结论：FAIL**

- 被验收 HEAD：`c83df46`（G05 返工实现提交 `549bca0`，返工交接文档提交 `c83df46`）。
- 定向测试：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；12 个通过，0 个失败，0 个错误，0 个跳过。
- 全量回归：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；68 个通过，0 个失败，0 个错误，0 个跳过。
- 辅助检查：`.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests` 成功；`.venv\Scripts\python.exe -m pip check` 输出 `No broken requirements found.`；`.venv\Scripts\python.exe scripts\validate_canonical.py` 输出 `valid: 9 standards, 12 sources, 6 parameters, 6 factors`。
- 通过项：首次验收指出的 `OFFICIAL_LATEST` 固定旧值、冲突结果可生成快照、无效 `OVERRIDE` 不阻断三类缺陷已修正；Domain 分层、Repository 内存测试、快照不可变性和通用契约测试通过；未提前实施 G06，未修改 `计算表/`。
- 未通过项一：生产默认规则缺少冻结映射中明确列出的 `GEN-RULE-ACTIVITY-PRIMARY-001` 和 `GEN-RULE-INDUSTRY-DELEGATION-001`，现有测试只断言部分 ID 子集，不能证明 35 条规则与冻结清单完整一致。
- 未通过项二：冻结炭素映射将 `CAR-RULE-NONFOSSIL-POWER-001` 定义为 `OVERRIDE`，生产规则却仍为 `BASE`；`CAR-RULE-POWER-HEAT-001` 应同时特化电力和热力，生产规则实际只绑定全国电力因子，没有覆盖热力参数路径。
- 未通过项三：多条 `source_location` 与原始 GB/T 32150—2025 不符。原文第 7.2.2、7.2.3、7.2.4 分别是排放因子法、物料平衡法、实测法；第 7.5.2～7.5.8 依次为燃料、过程、废弃物、逸散、购入电热、输出电热和总量，标准不存在第 7.5.9、7.5.10。当前实现把上述多条规则错标为第 7.3、7.4、7.5.1～7.5.10，并把通则总量覆盖定位到不存在的第 5.2.7 条。
- 未通过项四：GB/T 32151.34—2024 原文及冻结映射均把购入和输出电力、热力放在第 5.2.6 条，当前 `CAR-RULE-POWER-HEAT-001` 却定位到第 5.2.7.1 条（该条实际为直接排放总量）。
- 独立映射一致性探针返回退出码 1；上述缺失规则、关系类型和 11 组关键来源条款断言均失败。因此不能仅凭 12/12 与 68/68 测试判定通过。
- 工作区检查：验收开始及测试后均仅有既有未跟踪 `docs/handoffs/`；该目录未处理、未暂存。验收文档提交前没有其他未解释修改。

G05 未通过，不允许进入 G06。修正完成后应发送“重新验收G05”。

## G05 第二次返工实施状态（2026-09-13）

**READY_FOR_SOL_REACCEPTANCE**

- 本轮严格只返工 HANDOFF.md 的 G05；没有创建或执行 G06，没有修改 UI、Canonical 数据、SQLite 迁移、正式数据库、行业输入页、行业计算公式或 `计算表/`。
- `default_g05_rules()` 现为 37 条 CommonRuleSet、11 条 IndustryRuleSet；测试对两组完整 ID 集合使用相等断言，补齐 `GEN-RULE-ACTIVITY-PRIMARY-001` 与 `GEN-RULE-INDUSTRY-DELEGATION-001`。
- `CAR-RULE-NONFOSSIL-POWER-001` 已改为显式 `OVERRIDE`，完整追溯并覆盖 `GEN-RULE-ELECTRICITY-001`；`CAR-RULE-POWER-HEAT-001` 通过既有 RuleDefinition 字段覆盖电力/热力参数 ID、参数类型，并保留对两条通则规则的 payload 追踪。电力与热力实际解析路径均有回归断言。
- 已修正通则方法、公式、聚合及总量覆盖规则的 `source_location`：方法为 7.2.2/7.2.3/7.2.4，公式为 7.5.2～7.5.8 的正确顺序；购入电/热均为 7.5.6，输出电/热均为 7.5.7；移除不存在的 7.5.9、7.5.10 和通则 5.2.7 错误定位。炭素电热规则已改为第 5.2.6 条。
- G05 定向命令：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；12 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；68 个通过，0 个失败，0 个错误，0 个跳过。
- 编译命令：`.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests`；成功。
- 依赖命令：`.venv\Scripts\python.exe -m pip check`；输出 `No broken requirements found.`。
- Canonical 命令：`.venv\Scripts\python.exe scripts\validate_canonical.py`；输出 `valid: 9 standards, 12 sources, 6 parameters, 6 factors`。
- 三库重建命令：`.venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\g05-second-rework-databases-final --app-version 0.1.0`；catalog、user、records 三库均从 Canonical 创建成功，未写入正式数据库目录。
- 分层命令：`.venv\Scripts\python.exe -m unittest tests.test_g00_layout tests.test_g01_domain_dependencies tests.test_g02_persistence -v`；9 个通过，0 个失败，0 个错误，0 个跳过；独立扫描确认 `packages/core` 无 PySide6、sqlite3、QSql、QWidget、QFileDialog 依赖。
- 保护/范围检查：`git diff --check` 成功；`git diff --name-only -- 计算表/**` 为空；本轮变更仅为 G05 Domain、G05 测试及本阶段文档；G06 未创建或执行。
- 未执行 pytest：项目环境未安装 pytest，按项目基线使用 unittest 完成定向和全量测试；未执行 G06、行业专属输入/计算、记录闭环、报告导出或安装包工作。
- G05 二次返工实现与回归测试提交：`9e74024 fix: complete G05 frozen rule mappings`。
- 当前停止等待 Sol 再次验收；G06 阶段门禁保持关闭。

## G05 Sol 第二次正式重新验收记录（2026-09-13）

**结论：FAIL**

- 被验收 HEAD：`1a7bd95`（第二次返工实现提交 `9e74024`，交接文档提交 `1a7bd95`）。
- 定向测试：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；12 个通过，0 个失败，0 个错误，0 个跳过。
- 全量回归：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；68 个通过，0 个失败，0 个错误，0 个跳过。
- 分层回归：`.venv\Scripts\python.exe -m unittest tests.test_g00_layout tests.test_g01_domain_dependencies tests.test_g02_persistence -v`；9 个通过，0 个失败，0 个错误，0 个跳过。
- 辅助检查：`compileall` 成功；`pip check` 无破损依赖；Canonical 校验为 9 standards、12 sources、6 parameters、6 factors。G05 Domain 未发现 PySide6/SQLite 依赖；第二次返工只修改 G05 Domain、G05 测试和交接文档，未修改 `计算表/`，未实施 G06。
- 已关闭项：上次指出的两条缺失规则和通则第 7.2、7.5 条款错位已修正；非化石规则形式上已改为 `OVERRIDE`；电热规则形式上已列出两个参数 ID。
- 阻断问题一：`CAR-RULE-NONFOSSIL-POWER-001` 没有非化石电力适用条件，对 `ordinary_purchase` 和 `nonfossil` 两种上下文均生效，并在普通购电场景无条件覆盖 `GEN-RULE-ELECTRICITY-001`。独立探针显示两种上下文的有效规则集完全相同。
- 阻断问题二：GB/T 32151.34—2024 附录 D.1.1 明确自发自用及市场化交易购入的非化石能源电力因子为零，D.2 要求相应证明；当前非化石 `OVERRIDE` 却配置为 `OFFICIAL_LATEST`。独立探针在 `electricity_type='nonfossil'` 时无阻断地推荐全国平均因子 0.5306，既没有零因子路径，也没有证明文件门禁。现有测试反而断言普通购电必须包含非化石规则，固化了错误口径。
- 阻断问题三：`CAR-RULE-POWER-HEAT-001` 的分组键是 `parameter_selection:power_heat`，两条通则规则的分组键分别是具体电力/热力参数。解析器不会跨分组解释 payload；热力探针中 `GEN-RULE-HEAT-001` 的轨迹仍为独立 `SELECTED`，不存在由行业 SPECIALIZE 产生的 `INHERITED` 轨迹。因此当前实现只是元数据标记，不是 `EffectiveRuleResolver` 实际关系。
- 阻断问题四：所谓“完整 ID 集合”仍是测试内手写集合，不等于冻结映射注册表。FROZEN R5 通则注册表还列出 `GEN-RULE-ACTIVITY-PROXY-001`、`GEN-RULE-ACTIVITY-SECONDARY-001`、`GEN-RULE-PRINCIPLE-001`、`GEN-RULE-SOURCE-CATALOG-001`、`GEN-RULE-WORKFLOW-001`，生产代码和测试集合均未包含；生产代码中的 `GEN-RULE-REPORT-001` 又未在该冻结注册表登记。
- 阻断问题五：行业来源定位仍有错位。`CAR-RULE-PROCESS-001` 应按冻结映射对应第 5.2.2～5.2.5 条，当前写为 5.2.3～5.2.6；`CAR-RULE-FUEL-001` 应追溯第 5.2.1 条及附录 C，却混入无关附录 D；`CAR-RULE-FUGITIVE-COVERAGE-001` 的冻结依据是行业第 4.2、5.2 条和软件决策，当前只指向第 5.2.7.2 间接排放总量。
- 工作区在验收开始和测试后均仅有既有未跟踪 `docs/handoffs/`；该目录未处理、未暂存，未发现测试临时产物。

G05 未通过，不允许进入 G06。修正完成后应发送“重新验收G05”。

## G05 第三次返工状态（2026-09-13）

**历史状态：BLOCKED_WAITING_FOR_SOL_DECISION；该决策阻塞已于 2026-09-13 获批准解除。**

### G06 BLOCKED 停止点（历史，2026-09-13；Sol R6 决策后已解除）

问题：

- G06 的正式映射文件 TV-CAR-FML-008 将式（8）石墨化向量（GPM=10、GPMFC=0.005、GTA=100、GTAFC=0.007、GWT=0.05、GP=95、GPFC=0.006、GPMVar=0.10、K3=0.35）预期写为 3.364166666… tCO₂。
- 正式标准 GB/T 32151.34—2024 第 5.2.4 条、PDF 第 13 页的式（8）仅包含 GPM×GPMVar×K3×44/16 挥发分项；按同一输入执行得到 1.439166666666666666666666667 tCO₂。
- HANDOFF.md 第 473 行明确要求发现映射与标准原文疑似不一致时必须 BLOCKED，不得按经验改公式。

证据：

- D:\MD仓库\杂\碳排放计算软件\GB T 32151.34—2024 炭素材料生产企业映射方案.md:728：TV-CAR-FML-008 期望为 3.364166666…。
- packages/standards/carbon_material.py:594-597：当前实现按正式标准式（8）执行。
- 只读执行 graphitization_emission(...)：结果为 1.439166666666666666666666667。
- G06 定向测试最新结果：8 通过、1 失败；唯一失败为该冲突向量，未继续执行 G06 全量验收。

为什么不能按原方案继续：

- 修改实现以迎合 3.364166666… 会偏离正式标准式（8）；修改映射测试期望则会偏离 HANDOFF.md 冻结映射。两者属于计算口径/标准解释变化，不能由 Luna 自行决定。

可选方案 A：

- Sol 确认以正式标准第 5.2.4 条式（8）为准，将 TV-CAR-FML-008 修正为 1.439166666…，并允许继续 G06。

可选方案 B：

- Sol 提供式（8）采用 3.364166666… 的正式解释、修订映射或批准决策，明确额外项及其来源后，再修改计算与测试。

建议：

- 采用方案 A，保留当前正式标准公式实现；但在 Sol 明确确认前不继续 G06。

需要 Sol 决策的具体问题：

- G06 式（8）在上述固定输入下，最终批准值应为 1.439166666666666666666666667（正式标准公式）还是 3.364166666…（当前冻结映射向量）？
## 已完成的安全修正

- CAR-RULE-NONFOSSIL-POWER-001 仅在非化石电力上下文（包括市场化绿电和自发自用绿电别名）命中；普通购电继续使用通则官方最新因子。
- 非化石场景必须提供附录 D.2 证明；有证明时只接受值为 0、类型为 STANDARD_SPECIFIED 且来源定位包含附录 D.1.1 的因子，禁止回退全国平均 0.5306。
- CAR-RULE-POWER-HEAT-001 使用既有 parameter_ids 关系由 EffectiveRuleResolver 映射到电力/热力两个公共参数组，留下真实 SELECTED 与 INHERITED 轨迹；没有使用 payload 模拟关系。
- CommonRuleSet 补齐冻结注册表的 GEN-RULE-ACTIVITY-PROXY-001、GEN-RULE-ACTIVITY-SECONDARY-001、GEN-RULE-PRINCIPLE-001、GEN-RULE-SOURCE-CATALOG-001、GEN-RULE-WORKFLOW-001，并移除未登记的 GEN-RULE-REPORT-001。
- 修正 CAR-RULE-FUEL-001、CAR-RULE-PROCESS-001、CAR-RULE-FUGITIVE-COVERAGE-001 的冻结来源定位，并为上述关系/条件/来源补充回归断言。

### BLOCKED

问题：有 D.2 证明的市场化绿电或自发自用绿电必须推荐附录 D.1.1 的零因子，但当前 Canonical 因子库没有该有来源因子。

证据：data-source/carbon_accounting/catalog.json 当前只有 6 个因子；磁盘核对 value=0 且 source_location 包含“附录D.1.1”的因子数量为 0。冻结行业映射明确要求附录 D.1.1 零因子和 D.2 证明门禁。

为什么不能按原方案继续：如果继续而不新增 Canonical 因子，生产解析器只能安全阻断，不能在有证明时形成可追溯的 0 推荐；若把 0 写入 payload、代码常量或只放在测试夹具，会违反 Canonical Source 规则和 Sol 明确禁止的绕过方式。

可选方案 A：Sol 批准新增一个 Canonical 因子/参数记录，明确稳定 ID、单位、版本、来源 ID、附录 D.1.1 定位和适用标准；随后由 Luna 接入并完成 G05 验收。

可选方案 B：Sol 明确批准将附录 D.1.1 的 0 作为现有规则模型中的标准直接值，并补充其来源快照表达方式；当前实现仍需按该决定调整，不能自行解释。

建议：选择方案 A，保持官方数值、来源和 SQLite 重建链路都来自 Canonical Source。

需要 Sol 决策的具体问题：是否批准按附录 D.1.1 新增一条 Canonical 零因子（以及其稳定 ID/来源定位）？

### 测试与边界

- G05 定向：.venv\Scripts\python.exe -m unittest tests.test_g05_rules；13 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量：.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'；69 个通过，0 个失败，0 个错误，0 个跳过（项目 .venv，Python 3.12.14，PySide6 已安装）。
- 分层回归：.venv\Scripts\python.exe -m unittest tests.test_g00_layout tests.test_g01_domain_dependencies tests.test_g02_persistence；9 个通过，0 个失败，0 个错误，0 个跳过。
- L3：.venv\Scripts\python.exe -m compileall -q packages apps tests scripts 成功；.venv\Scripts\python.exe -m pip check 输出 No broken requirements found.；Canonical 校验输出 9 standards、12 sources、6 parameters、6 factors；三库从零重建输出 catalog/user/records 三个临时数据库。
- 保护检查：git diff --check 成功；git diff --name-only -- 计算表/** 为空；G06 未创建、未执行。
- 系统 Python 的一次全量收集未计入项目结果：缺少 PySide6 导致 3 个导入错误；随后使用项目 .venv 完成 69/69。
- 未执行 pytest：项目测试基线为 unittest，环境未安装 pytest。

代码/测试提交：4ac0e7f fix: harden G05 nonfossil rule resolution。该记录形成时等待 Sol 决策；后续批准结论见下节。本次治理更新不创建或执行 G06。

## 产品决策：多种电力消费形式（2026-09-13）

**状态：APPROVED；已按批准范围继续 G05，当前等待 Sol 重新验收。**

- 同一企业、同一核算期的电力消费采用多条明细，不得单选一种电力类型。
- 每条明细分别保存电量、取得方式、电力属性、核算期间、排放因子及来源、证明材料类型和状态、参数选择理由及独立参数快照。
- 取得方式（外购/自发自用）与电力属性（常规/非化石）是两个独立维度；界面使用“外购常规电力（电网电力）”表述。
- 外购常规电力采用适用的最新全国平均因子；有附录 D.2 适用证明的外购或自发自用非化石能源电力采用附录 D.1.1 零因子；缺少证明必须产生 `ERROR`，不得使用零因子或静默回退全国平均因子。
- 自发自用化石能源电力的燃料排放进入直接排放路径，不得重复计入外购电力间接排放。
- 批准新增 `electricity_emission_factor_nonfossil` 参数和 `electricity_nonfossil_zero_gbt32151_34_2024` 因子，完整字段以 `HANDOFF.md` 第 4.5.1 节和决策记录为准；不得挂到 `electricity_emission_factor_national` 下。
- G05 仅负责 Canonical 补录、多明细领域上下文和每条明细独立解析/校验/快照，并新增三种电力同时存在的组合测试；不制作电力录入页面，不计算企业电力排放总量。
- G06 后续负责多明细增删和选择、逐条计算与汇总、防重复计算；当前阶段门禁仍关闭。

### 下一动作

1. 由用户另行让 Luna 继续 G05，按已批准决策补录 Canonical 数据并完成 G05 剩余范围。
2. Luna 完成 G05、更新 `TASK_STATE.md` 和 `IMPLEMENTATION_REPORT.md` 后停止，等待 Sol 重新验收。
3. 未获 G05 `PASS` 前不得创建或执行 G06。

## G05 第三次返工实施状态（获批准后继续，2026-09-13）

**READY_FOR_SOL_REACCEPTANCE**

本轮恢复已 BLOCKED 的 G05 Goal，仅执行 Sol 已批准的多种电力消费形式第三次返工；没有创建或执行 G06。

### 实现内容

- Canonical 新增独立参数 electricity_emission_factor_nonfossil 和因子 electricity_nonfossil_zero_gbt32151_34_2024；值、单位、来源、有效期和适用标准严格采用 HANDOFF.md 第 4.5.1 节批准值。GB/T 32151.34—2024 新增该 parameter_ref，data_version 更新为 2026.09.13-g05-third-rework.1，schema_version 和数据库迁移未修改；零因子未挂到 electricity_emission_factor_national。
- Domain 新增取得方式与电力属性两个独立枚举维度，以及每条电力消费明细的证明类型/状态；同一企业和核算期通过多条明细解析，不使用企业级单选状态。
- 每条明细分别进行规则解析、证明门禁、稳定因子选择和带 detail_id 的不可变参数快照；外购常规电力沿用最新全国平均因子；外购非化石电力仅接受合同及结算凭证或 GEC 有效证明；自发自用非化石电力仅接受月度原始记录有效证明。
- 证明缺失或 Canonical 独立零因子缺失均为 ERROR，禁止零因子和全国平均因子回退；自发自用化石能源电力返回明确的直接燃料路径转交结果，不进入外购电力路径，也未实现 G06 公式。
- CAR-RULE-NONFOSSIL-POWER-001 引用新参数和稳定零因子 ID；因子选择不读取中文 source_location 识别。附录 D 定位统一为 PDF 第30页、印刷页22。
- 新增同一企业同时存在外购常规、外购非化石、自发自用非化石三条明细的组合回归，以及普通购电、市场化非化石电力、自发自用非化石电力、证明缺失、零因子缺失、稳定 ID 反绕过和自发自用化石防重复路径测试。

### 验证与边界

- G05 定向：.venv\Scripts\python.exe -m unittest tests.test_g05_rules tests.test_g05_multi_electricity -v；18 个通过，0 个失败，0 个错误。
- G02 Canonical/持久化与 G04 参数展示定向：.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog -v；31 个通过，0 个失败，0 个错误。
- 全量：.venv\Scripts\python.exe -m unittest discover -s tests -t . -v；75 个通过，0 个失败，0 个错误。
- 编译：.venv\Scripts\python.exe -m compileall -q packages apps tests；成功。
- 依赖：.venv\Scripts\python.exe -m pip check；No broken requirements found.
- Canonical：.venv\Scripts\python.exe scripts\validate_canonical.py；valid: 9 standards, 12 sources, 7 parameters, 7 factors。
- 三库从零重建：.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir tmp\g05-third-rework-databases；catalog、user、records 三库生成成功，临时目录已清理。
- git diff --check、迁移范围检查和 计算表/ 保护检查通过；既有 docs/handoffs/ 未处理、未暂存。pytest 未执行，项目测试基线为 unittest。
- 未制作电力录入页面、企业电力排放总量、G06 计算公式或其他 G06 模块。

### Git 与等待状态

- 实现与回归测试提交：7173394 fix: complete G05 multi-electricity rework。
- 本节状态文档和 IMPLEMENTATION_REPORT.md 随后更新；G05 当前停止等待 Sol 重新验收。

## G05 Sol 第三次正式重新验收记录（2026-09-13）

**结论：PASS**

- 被验收 HEAD：`f080f115f0d7a31249befc0703cfec132c19e515`（实现提交 `7173394`，交接文档提交 `f080f11`）。
- 原始标准：直接读取 GB/T 32151.34—2024 原始 PDF；SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。PDF 物理第30页页脚为印刷页22，D.1.1、D.1.2、D.2 与 Canonical 口径和证明门禁一致。
- Canonical：独立参数 `electricity_emission_factor_nonfossil` 和零因子 `electricity_nonfossil_zero_gbt32151_34_2024` 真实存在；值为字符串 `"0"`，单位 `tCO₂/MWh`，来源、年份、有效期、审核状态正确，且仅适用于 `gbt_32151_34_2024`。零因子未挂到 `electricity_emission_factor_national`。
- 多明细领域能力：取得方式和电力属性为两个独立枚举；同一企业和同一核算期的外购常规、外购非化石、自发自用非化石三条明细可同时解析，各自校验并以唯一 `detail_id` 形成独立不可变快照，未相互覆盖。
- 参数与证明：普通购电采用全国平均因子；外购非化石仅接受合同及结算凭证或 GEC，自发自用非化石仅接受月度电量原始记录。证明缺失产生 `ERROR`，不生成快照且不回退全国平均因子。
- 防重复路径：自发自用化石能源电力返回 `DELEGATE_DIRECT_FUEL_PATH` 和阻断性校验，不进入外购电力间接排放参数路径。
- 组合场景：`.venv\Scripts\python.exe -m unittest tests.test_g05_multi_electricity.G05MultiElectricityTests.test_same_enterprise_resolves_three_details_independently -v`；1 个通过，0 个失败，0 个错误。
- G05 定向：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules tests.test_g05_multi_electricity -v`；18 个通过，0 个失败，0 个错误。
- G02/G04 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog -v`；31 个通过，0 个失败，0 个错误。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；75 个通过，0 个失败，0 个错误。
- 辅助检查：Canonical 校验为 9 standards、12 sources、7 parameters、7 factors；三库从零重建和真实 SQLite 独立查询通过；`compileall` 成功，`pip check` 无破损依赖，Domain 分层检查 3/3 通过。
- 范围：未修改或覆盖 `计算表/`，未提前实现 G06 页面、公式或汇总，未创建或执行 G06；本次临时 PDF 和数据库产物均已清理。工作区仅保留既有未跟踪 `docs/handoffs/`。

G05已通过，允许由用户另行启动G06；本次未启动G06。

## G06 实施状态（Sol R6 决策后，2026-09-13）

**G06_READY_FOR_SOL_ACCEPTANCE**

本轮继续现有 G06 Goal，仅执行 Sol 批准的 R6 映射测试向量纠错收口并完成 G06；未创建或执行 G07。

### Sol 决策与 R6 映射

- 外部映射文件已升为 SM01-2026-09-13-R6，顶部状态为 FROZEN。
- TV-CAR-FML-008 已按 Sol 决策由 3.364166666... tCO2 修正为 1.439166666... tCO2；第19节（外部文件第1057行）登记为“映射测试向量纠错”，明确不是标准勘误，也不标记为 CONFIRMED_CORRECTION。
- G06 保留正式标准式（8），不增加 GTA×GTAVar×K3×44/16；MAPPING_VERSION 为 SM01-2026-09-13-R6。
- 外部映射文件 SHA256：变更前 8BC09741DC6E34E4A14D8801D776760BE56336B5499E4B1FFA2F9FDC0E997DD4，变更后 D3023387B04BF20ECF2D9F6CECF1F816EACF995C1C4B0A57AED8D72F7E519F26。该文件位于项目 Git 外；项目提交 4d52b32 通过回归测试同时保留旧值和 R6 新值的差异证据。

### G06 实现

- packages/standards/carbon_material.py 完成十类排放源的 Decimal 计算、单位与适用性校验、验证问题、默认值警告、参数快照、C.4/C.5 蒸汽焓值查表/插值、产出扣减和其他活动/运输边界阻断。
- 多电力明细按 G05 的取得方式和电力属性逐条解析；每条明细独立完成因子选择、证明校验和快照，不被后录入明细覆盖。外购常规、非化石证明门禁、自发自用非化石月度记录门禁和自发自用化石能源直接路径转交均已覆盖。
- packages/application/carbon_accounting.py 和 packages/ui/carbon_material_page.py 接入 G05 参数解析与 G06 计算结果展示；界面不承载公式，记录仅使用内存 Record Repository，本阶段未实现正式记录持久化。
- packages/ui/pages.py 和 packages/ui/shell.py 接入 G06 路由；未制作 G07 页面、报告/导出或安装包。

### 验证与边界

- G06 定向：.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v；20 个通过，0 个失败，0 个错误。
- G02 Canonical/持久化、G04 参数展示、G05 相关回归：.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v；49 个通过，0 个失败，0 个错误。
- 全量：.venv\Scripts\python.exe -m unittest discover -s tests -t . -v；95 个通过，0 个失败，0 个错误。
- 编译：.venv\Scripts\python.exe -m compileall -q packages apps tests；成功。
- 依赖：.venv\Scripts\python.exe -m pip check；No broken requirements found.
- Canonical：.venv\Scripts\python.exe scripts\validate_canonical.py；valid: 9 standards, 12 sources, 7 parameters, 7 factors。
- 三库从零重建：.venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\g06-final-three-databases --app-version 0.1.0；catalog.sqlite、user.sqlite、records.sqlite 均生成成功，临时目录已清理。
- git diff --check 通过；git diff --name-only -- 计算表/** 为空；既有 docs/handoffs/ 未处理。未执行 pytest，项目测试基线为 unittest。
- 实现提交为 bc1f83c；R6 旧值/新值测试证据提交为 4d52b32。当前停止等待 Sol 重新验收，不启动 G07。

## G06 Sol 正式阶段验收记录（2026-09-13）

**结论：FAIL**

- 被验收 HEAD：`16e47722e5dfeaf34025460b90c659c260967ee5`（`docs: record G06 R6 implementation and acceptance state`）。验收前工作区只有既有未跟踪 `docs/handoffs/`，无已跟踪差异；G06 相对 G05 的提交范围为实现、页面、路由、测试和阶段文档，未发现 G07 实现。
- 原始标准：直接读取 GB/T 32151.34—2024 原始 PDF，SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`；式（1）～式（16）以及附录 D 已核对。第 5.2.4 条式（8）不含 `GTA×GTAVar×K3×44/16`，R6 的 `TV-CAR-FML-008=1.439166666666666666666666667 tCO2` 与原文和独立复算一致。
- 通过项：十类排放源的 Domain 公式与聚合、Decimal 计算、单位/比例/缺失/不涉及校验、标准缺省值提示与快照、蒸汽焓值查表和内插、多电力明细独立解析和汇总、非化石证明门禁、自发自用化石电力直接燃料路径转交、内存 Record Repository、其他活动/运输的 Domain 阻断均已有实现和通过测试。
- 未通过项一（G06 手工录入页面不完整）：`packages/ui/carbon_material_page.py` 只构建 I01 购入电力和 I02 购入热力输入区，没有 I03 输出电力、I04 输出热力录入控件；`_input()` 也从不传入 `exported_electricity` 或 `exported_heat`。无界面探针确认两者恒为 0 条，页面只有 I03/I04 的“是否涉及”选择。用户无法通过 G06 页面完成式（15）的两项抵扣输入，不满足“实现 CAR-I03、CAR-I04”和首个标准手工录入的 MUST。
- 未通过项二（最小身份信息必填被绕过）：页面把空企业名称静默替换为字符串“未填写企业”，因此用户未填写企业名称也能通过领域模型并形成内存记录，不满足“最小身份信息只要求企业名称和核算期间”中的必填要求。
- 未通过项三（参数选择器未实现且来源表达不可靠）：HANDOFF 要求参数选择器接入 G05 服务并显示来源和选择状态；当前参数区只有说明文字和计算后的快照数量，页面唯一可编辑的热力因子是普通文本框。无界面探针未发现参数/因子选择控件；用户输入的热力因子又被构造成默认 `ParameterValue`，不能让用户选择候选值、查看来源/审核状态或确认选择理由。
- 未通过项四（收到基/成分性质在页面被静默假定）：Domain 虽定义 `mass_basis`、`composition_basis`、`normalized_basis`、`component_kind` 及换算证据，但页面没有这些输入或确认控件，所有式（6）～式（8）手工数据均通过构造器默认成收到基和固定碳口径，无法让用户表达未知、不一致、干燥基及换算证据，不满足冻结映射第 8.1 节的实际校验要求。
- 未通过项五（冻结校验编号未完整落地）：冻结映射要求 `CAR-VAL-GREEN-ELECTRICITY-EVIDENCE`，当前非化石证明缺失只透传 G05 的 `GEN-VAL-NONFOSSIL-EVIDENCE`；全项目不存在前一稳定 ID。G06 测试也断言通用 ID，未检查行业映射 ID。
- 测试缺口：现有 G06 页面测试只核对十个状态选择器、多电力行和基础计算展示，没有覆盖 I03/I04 页面输入、企业名称空值阻断、参数选择/来源展示、收到基元数据输入和行业校验 ID，故 20/20 与全量 95/95 通过不能证明上述 MUST 已完成。
- R6 文档证据：外部映射磁盘原始 SHA256 为 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`（62019 字节、LF）；既有文档所记 `D3023387B04BF20ECF2D9F6CECF1F816EACF995C1C4B0A57AED8D72F7E519F26` 是同内容转换为 CRLF 后的规范化哈希。R5 未归档、R6 签署区仍是 2026-09-11 旧签署、G06 历史 BLOCKED 块重复，均为治理证据待整理项；本次 FAIL 下未修改外部映射或历史文档结构。

### 本次实际执行的验收命令

- G06 定向：`.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`；20 个通过，0 个失败，0 个错误。
- G02/G04/G05 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`；49 个通过，0 个失败，0 个错误。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；95 个通过，0 个失败，0 个错误。
- 编译：`.venv\Scripts\python.exe -m compileall -q packages apps tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir D:\project\碳排放核算工具\tmp\sol-g06-acceptance-20260913 --app-version 0.1.0`；三库成功生成，验收临时目录已清理。
- 页面独立探针：空企业名称得到“未填写企业”，`exported_electricity` 与 `exported_heat` 均为 0 条，未发现输出能源或参数选择控件。

G06 未通过，不允许进入 G07。本次未创建或执行 G07。请 Luna 只修正上述 G06 未通过项并补充对应测试；修正完成后发送“重新验收G06”。

## G06 页面返工实施状态（2026-09-14）

**READY_FOR_SOL_REACCEPTANCE**

本轮针对 Sol 的 G06 FAIL 只修正手工页面缺口和冻结行业校验码；未创建或执行 G07，未修改 `计算表/`，未处理既有未跟踪 `docs/handoffs/`。

### 已完成修正

- 页面新增 I03 输出电力和 I04 输出热力/动力录入控件；`_input()` 生成独立输出明细并传入 Domain，I03/I04 可参与式（15）扣减。输出热力与 I02 共用 G05 热力因子选择，但保留独立明细和源状态。
- 企业名称不再替换为“未填写企业”；空名称在计算按钮入口产生 `ERROR [GEN-VAL-REQUIRED-MISSING]`，不调用计算、不形成内存记录，Domain 输入仍保持名称必填。
- 参数区接入 G05 热力因子目录选择器，显示推荐/其他适用/历史分类、因子值和单位、来源 ID、审核状态、来源定位及选择理由；推荐值按核算期间刷新，选择其他候选必须填写人工确认理由，并将实际值、来源、版本、因子 ID、理由带入 Domain 参数值和快照。
- P01/P02/P03 页面新增收到基/干燥基/其他有证基准、成分性质、归一化基准、水分/换算证明和证明定位控件；默认值为“未确认”，不会静默采用收到基/固定碳。非收到基没有完整证明时由 Domain 产生 `CAR-VAL-MATERIAL-BASIS-CONVERSION`。
- G06 电力解析将 G05 的 `GEN-VAL-NONFOSSIL-EVIDENCE` 映射为冻结行业码 `CAR-VAL-GREEN-ELECTRICITY-EVIDENCE`；未改变 G05 通用规则、参数或 G06 计算口径。

### 针对性测试

- 新增页面回归覆盖 I03/I04 控件和输入映射、空企业名称必填且不生成记录、真实 Canonical 热力参数选择器的来源/审核/理由展示、P01 基准与换算证明缺失阻断。
- 更新 G06 缺失非化石证明断言，固定验证 `CAR-VAL-GREEN-ELECTRICITY-EVIDENCE`。

### 验证结果

- G06 定向：`.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`；24/24 通过。
- G02/G04/G05 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`；49/49 通过。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -v`；99/99 通过。
- 编译：`.venv\Scripts\python.exe -m compileall -q packages tests scripts apps`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir tmp\g06-final-dbcheck\databases --app-version g06-rework-check`；catalog/user/records 三库均生成成功，随后已校验并清理临时目录。
- `git diff --check` 通过；`git diff --name-only -- 计算表/**` 为空；未执行 pytest，项目测试基线为 unittest。

### R6 证据整理

- 当前外部 R6 映射文件磁盘原始内容为 LF，SHA256 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`（62019 字节）。
- 历史报告中的 `D3023387B04BF20ECF2D9F6CECF1F816EACF995C1C4B0A57AED8D72F7E519F26` 是同内容转换为 CRLF 后的规范化哈希，不是当前 LF 原始哈希；本轮未修改项目 Git 外映射文件、签署区或历史验收记录。

### Git 与等待状态

- G06 页面返工实现与回归测试提交：`5d26d20 fix: close G06 page acceptance gaps`。
- 本节文档提交后，工作区仅保留既有未跟踪 `docs/handoffs/`；当前停止等待 Sol 重新验收，不启动 G07。

## G06 Sol 正式重新验收记录（2026-09-16）

**结论：FAIL**

- 被验收 HEAD：`ea4ff2eb3acb9c5d8c299ce7a09377dbad48ba9a`（`docs: record G06 page rework`）。验收开始前无已跟踪工作区差异，仅保留既有未跟踪 `docs/handoffs/`。
- 已关闭首次验收缺口：I03 输出电力、I04 输出热力已进入页面和 Domain；空企业名称会产生 ERROR 且不形成记录；热力参数选择器已接入真实目录并展示来源、审核状态和理由；材料基准默认改为未确认；缺少非化石证明已使用行业码 `CAR-VAL-GREEN-ELECTRICITY-EVIDENCE`。
- 原始标准与 R6：直接核对 GB/T 32151.34—2024 原始 PDF，SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。PDF 物理第13页式（8）不含 GTA 挥发分项；物理第30页（印刷页22）D.1.1、D.1.2、D.2 与零因子和证明门禁一致。外部冻结映射为 `SM01-2026-09-13-R6`，原始 LF SHA256 为 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`，`TV-CAR-FML-008=1.439166666666666666666666667` 与标准和独立复算一致。

### 未满足的 G06 MUST

1. **材料成分性质没有按字段组约束。** 冻结映射 `CAR-FLD-MATERIAL-COMPONENT-KIND` 要求固定碳字段只能是 `FIXED_CARBON`，挥发分字段只能是 `VOLATILE_MATTER`。当前每个 P01/P02/P03 过程只有一个 `component_kind`，但同一公式同时含固定碳和挥发分字段；Domain 只检查该单值是否属于两个合法枚举之一，不能证明两组字段各自口径正确。独立探针中同一组式（6）输入无论选择 `FIXED_CARBON` 还是 `VOLATILE_MATTER`，均未产生 `CAR-VAL-MATERIAL-COMPONENT-KIND`。因此错误口径可被接受。
2. **每条电力明细未展示独立参数来源和选择状态。** `_ElectricityRow` 只有电量、取得方式、电力属性、证明类型/状态和删除控件，没有因子、来源、审核/选择状态或选择理由。G05 服务虽在后台产生快照，但 G06 页面无法让用户看到每条明细实际采用的参数及状态，未满足 HANDOFF 4.5.1 和 G06 参数选择器 MUST；三条电力明细的独立显示也没有页面测试。
3. **其他行业活动与运输无法从手工页面声明。** Domain 已有 `other_activity_present`、`transport_present` 及 `CAR-VAL-OTHER-STANDARD` 阻断，但页面没有对应控件，`_input()` 也不传入这两个标志。用户无法通过 G06 手工录入路径触发 HANDOFF 4.6 要求的阻止和提示。

### 本次实际执行的验收命令

- G06 定向：`.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`；24/24 通过，0 个失败，0 个错误。
- G02/G04/G05 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`；49/49 通过，0 个失败，0 个错误。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；99/99 通过，0 个失败，0 个错误。
- 编译：`.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功；验收临时数据库与 PDF 渲染目录均已清理。
- 页面/领域独立探针：两种单一 `component_kind` 均未触发字段组错误；电力行未发现参数状态控件；页面未发现其他活动或运输声明控件。

### 范围与阶段门禁

- 未修改、删除或覆盖 `计算表/`；未修改业务代码或项目 Git 外的冻结映射；未处理既有未跟踪 `docs/handoffs/`。
- 未发现 G07 已创建或执行；本次也未创建 Goal 或实施 G07。

G06 未通过，不允许进入 G07。请 Luna 只修正上述三项 G06 缺口并补充对应的领域和页面测试；修正完成后发送“重新验收G06”。

## G06 页面缺口返工实施状态（2026-09-16）

**READY_FOR_SOL_REACCEPTANCE**

本轮只处理 Sol 最新 G06 重新验收指出的三项阻断问题；未创建或执行 G07，未修改“计算表/”，未处理既有未跟踪 `docs/handoffs/`。

### 已完成

- 为 P01 煅烧、P02 焙烧/炭化、P03 石墨化分别增加固定碳字段性质和挥发分字段性质两个独立 Domain 输入；页面不再提供共享“成分性质”选择器。固定碳字段不是 `FIXED_CARBON` 或挥发分字段不是 `VOLATILE_MATTER` 时，分别产生 `CAR-VAL-MATERIAL-COMPONENT-KIND`，并定位到对应字段组。既有 `component_kind` 构造兼容保留，但页面和新校验使用独立字段；未改变 SQLite schema 或迁移。
- 每条电力明细增加独立的采用因子、来源/定位、审核状态、选择状态和选择理由展示；展示直接来自 G05 `resolve_electricity_details()` 的该明细结果和快照，不以企业级状态覆盖其他明细。普通购电、外购非化石和自发自用非化石可同时显示各自的真实因子。
- 核算边界增加“存在本标准未覆盖的其他行业活动”和“存在上下游运输”两个手工声明；两项标志传入 `CarbonMaterialInput`，由既有 Domain `CAR-VAL-OTHER-STANDARD` 阻断，不进入成功结果。
- 增加领域与页面针对性回归测试，覆盖固定碳/挥发分两类错误口径、电力三明细独立展示、其他活动/运输声明和阻断。

### 验证

- G06 定向：`.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`；28/28 通过，0 个失败，0 个错误。
- G02/G04/G05 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`；49/49 通过，0 个失败，0 个错误。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -v`；103/103 通过，0 个失败，0 个错误。
- 编译：`.venv\Scripts\python.exe -m compileall -q packages tests scripts`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir <临时目录>`；`catalog.sqlite`、`user.sqlite`、`records.sqlite` 均成功生成，临时目录已清理。
- `git diff --check` 通过；`git diff --name-only -- 计算表/**` 为空；pytest 未执行，项目测试基线为 unittest。

### 提交与阶段门禁

- 实现与测试提交：`55bdd1b fix: close remaining G06 page validation gaps`。
- 当前等待 Sol 重新验收；G07 未创建、未执行。