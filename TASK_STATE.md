# TASK_STATE

## 当前工作包

Post-V1 新建核算 UI 重构：UIR02 排放源与活动数据卡片重构

## 状态

UIR02_REWORK_READY_FOR_SOL_REVIEW

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
- G06 最终正式重新验收结论：PASS（2026-09-16）；被验收 HEAD 为 `c2ca02e5453e4b597cc73647f3ae6cba0d2b1842`。三项剩余阻断均已关闭，允许由用户另行启动 G07；本次未启动 G07。

- G07 实施完成（2026-09-19）；实现提交为 `707c59a`，当前停止等待 Sol 验收；G08 未创建、未执行。
- G07 正式验收结论：FAIL（2026-09-19）；被验收 HEAD 为 `8510c2128a43f88605d3f35e8238ab51246bdc37`。默认应用仍使用内存记录仓库、标准版本保存错误、只读详情未展示实际输入值，且未计算输入未完整丢弃/关闭软件无提示；不允许进入 G08。
- G07 验收返工完成（2026-09-19）；实现与测试提交为 `b12a75b`，默认 records.sqlite、真实标准版本、只读实际快照、完整丢弃和关闭门禁均已修正，当前等待 Sol 重新验收；G08 未创建、未执行。
- G07 正式重新验收结论：PASS WITH MINOR FIXES（2026-09-19）；被验收 HEAD 为 `c4677a59f1d09f77d7294cd3bb500a9875815651`。核心 G07 闭环已关闭，但记录详情仍以内部 JSON 原样展示，且缺少“修改当前 Catalog 后历史展示不变”的直接回归测试；本验收环境也未能独立复跑 PySide6 自动测试。因此 G08 仍不得启动，小修并补充可复验测试证据后应发送“重新验收G07”。
- G07 历史详情小修完成（2026-09-19）；实现与测试提交为 `d6e4d91`，补充业务分组快照展示及修改当前 Catalog 后历史详情不变的回归测试，当前等待 Sol 重新验收；G08 未创建、未执行。
- G07 最终正式重新验收结论：PASS（2026-09-19）；被验收 HEAD 为 `7e3573dfd7fc105cc013c07028c5eb8815836569`。两项小修已关闭，G07 全部 MUST 与阶段门禁通过；允许由用户另行启动 G08，本次未启动 G08。
- G08 实施完成（2026-09-20）；从 `origin/main` 的 `fbe884d` 创建分支 `gxx-implementation`，仅执行 G08，未创建或执行 G09。实现与测试提交：`9aa0625` `feat: complete G08 Windows delivery baseline`。
- UIR01 正式验收结论：PASS（2026-09-21）；被验收 head 为 `97e2ba59f8ea4ffde8e111750caa0650f5000cf5`，PR #4 `feat: implement UIR01 field semantics and typed inputs` 已合并，merge commit 为 `09e9d5e66f30f46f4302f6b57f330c27c4a852a3`。
- UIR02 已由用户启动（2026-09-21）；本阶段从实时 `origin/main` 创建 `ui-refactor-uir02-source-cards`，仅实施 UIR02，不启动 UIR03。实现与专项测试提交为 `ed752c0`，PR #5 已创建；代码候选 head `ec8bfec1e5671fa6b92e1995ce6693f6ea22a296` 的 Actions run `35550650466` 已成功，当前等待最新报告提交后的检查与 Sol 验收。
- UIR02 首次正式验收结论：FAIL（2026-09-21）；被验收 HEAD 为 `8c3a45267687f46200d4b1f1de3bcedda8a68598`。卡片“已完成”未消费已有电力解析/Domain 校验结果，缺少 `NEEDS_ATTENTION` 门禁和合法成功 Domain parity；不允许进入 UIR03。

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

#- G07 实施完成（2026-09-19）；实现提交为 `707c59a`，当前停止等待 Sol 验收；G08 未创建、未执行。
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
- 编译：`.venv\Scripts\python.exe -m compileall -q packages apps tests scripts apps`；成功。
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
- 编译：`.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir <临时目录>`；`catalog.sqlite`、`user.sqlite`、`records.sqlite` 均成功生成，临时目录已清理。
- `git diff --check` 通过；`git diff --name-only -- 计算表/**` 为空；pytest 未执行，项目测试基线为 unittest。

### 提交与阶段门禁

- 实现与测试提交：`55bdd1b fix: close remaining G06 page validation gaps`；P01/P02/P03 成分字段回归补强提交：`345b023 test: cover G06 component kinds across process groups`；构造兼容修正提交：`bcb6307 fix: preserve G06 input constructor compatibility`。
- 当前等待 Sol 重新验收；G07 未创建、未执行。

## G06 Sol 最终正式重新验收记录（2026-09-16）

**结论：PASS**

- 被验收 HEAD：`c2ca02e5453e4b597cc73647f3ae6cba0d2b1842`（`docs: record G06 constructor compatibility fix`）。验收开始前无已跟踪工作区差异，仅保留既有未跟踪 `docs/handoffs/`。
- 材料成分性质：P01、P02、P03 均分别具有固定碳字段性质和挥发分字段性质；错误类型分别产生 `CAR-VAL-MATERIAL-COMPONENT-KIND` 并定位到 `.fixed-carbon` 或 `.volatile-matter`。页面默认两类均为未确认，不能静默绕过。
- 多电力明细：同一企业、同一期间可同时存在外购常规、外购非化石和自发自用非化石三条明细。每行独立展示实际采用因子、来源定位、审核状态、选择状态和理由；Domain 仍逐条解析、校验、计算并形成独立快照。
- 核算边界：页面可声明其他行业活动和上下游运输，标志会传入 Domain 并产生 `CAR-VAL-OTHER-STANDARD` ERROR；错误阻止成功结果和内存记录，不将这些活动并入本标准结果。
- 其余 G06 MUST 复核通过：十类排放源、I03/I04 抵扣、Decimal 高精度、参数和默认值快照、月度/年度标识、多电力证明门禁、自发自用化石电力转交与防重复、企业名称必填、热力参数选择、内存 Record Repository、UI/Domain 分层均保持有效。
- 原始标准：GB/T 32151.34—2024 PDF SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。直接复核物理第13页式（8）和物理第30页（印刷页22）附录 D.1.1、D.1.2、D.2；R6 式（8）向量、全国平均因子规则、非化石零因子和证明门禁与原文一致。
- 冻结映射：版本 `SM01-2026-09-13-R6`，原始 LF SHA256 为 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`；关键规则 `CAR-FLD-MATERIAL-COMPONENT-KIND`、`CAR-RULE-OTHER-ACTIVITY-001`、`CAR-VAL-GREEN-ELECTRICITY-EVIDENCE` 和 `TV-CAR-FML-008` 均与实现一致。

### 本次实际执行的验收命令

- G06 定向：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`；28/28 通过，0 个失败，0 个错误，0 个跳过。
- G02/G04/G05 回归：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`；49/49 通过，0 个失败，0 个错误，0 个跳过。
- 项目全量：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；103/103 通过，0 个失败，0 个错误，0 个跳过。
- 编译：`.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\sol-g06-reaccept-20260916-2 --app-version g06-sol-reaccept`；三库成功生成，验收临时目录已清理。

### 范围与阶段门禁

- 未修改、删除或覆盖 `计算表/`；未修改项目 Git 外冻结映射；未处理既有未跟踪 `docs/handoffs/`。
- 未发现 G07 业务实现；本次未创建 Goal、未启动或实施 G07。

G06已通过，允许由用户另行启动G07；本次未启动G07。

## G07 实施停止点（2026-09-19）

- 已创建且仅执行 G07 Goal；未创建或执行 G08。
- 计算成功后通过 records.sqlite 单一事务写入不可编辑记录、完整输入/结果/参数/有效规则快照及 CREATE 审计；ERROR 不生成成功记录，事务失败回滚。
- 支持 `COMPLETED` 与 `COMPLETED_WITH_WARNINGS`；同一输入连续成功计算使用不同记录 ID，旧记录不覆盖。
- 已实现记录列表、企业/记录/标准搜索、状态筛选、只读详情、二次确认软删除、DELETE 审计和首页最近记录刷新；未计算输入离开页面会确认并丢弃。
- G07 定向测试 8/8 通过；项目全量回归 111/111 通过；Canonical、三库重建、compileall、pip check 均通过。
- `计算表/` 未修改；既有未跟踪 `docs/handoffs/` 未处理、未纳入提交。
- 当前门禁：停止等待 Sol 验收；不得开始 G08。

## G07 Sol 正式阶段验收记录（2026-09-19）

**结论：FAIL**

- 被验收 HEAD：`8510c2128a43f88605d3f35e8238ab51246bdc37`（`docs: record G07 implementation`）。验收开始前无已跟踪工作区差异，仅保留既有未跟踪 `docs/handoffs/`。
- 已通过项：records 002 迁移可重复执行；显式使用 `SQLiteRecordRepository` 时记录、快照和 CREATE 审计在单一事务内写入，审计写入失败会回滚记录；ERROR 不生成记录；支持 `COMPLETED` 和 `COMPLETED_WITH_WARNINGS`；同一输入连续计算生成不同记录 ID；软删除保留原记录和 CREATE/DELETE 审计，活动列表默认隐藏；列表搜索、状态筛选、只读控件、首页最近记录刷新均已有实现。
- 原始标准与 Canonical：GB/T 32151.34—2024 原始 PDF SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`；封面明确为 `GB/T 32151.34—2024`。Canonical 中该标准 `version` 为字符串 `2024`，当前 G07 数据库保存值与此不一致。

### 未满足的 G07 MUST

1. **正式应用默认不使用 records.sqlite。** `AppConfig.resolved_records_database()` 能返回用户数据目录，但 `create_shell()` 只在 `config.records_database` 被显式赋值时建立 `SQLiteRecordRepository`；普通启动的 `AppConfig()` 会落入 `InMemoryRecordRepository`。独立默认启动探针输出 `default_repository=InMemoryRecordRepository`。因此用户正常启动、计算并关闭软件后记录会丢失，不满足“计算即生成正式记录”和 records.sqlite 持久化闭环。现有 UI 测试显式同时注入数据库路径和 SQLite 仓库，未覆盖真实默认启动路径。
2. **标准版本保存错误。** `SQLiteRecordRepository.create_with_details()` 将 `standard_version` 写成 `record.standard_id`；独立数据库探针得到 `standard_id='gbt_32151_34_2024'`、`standard_version='gbt_32151_34_2024'`，而正式 Standard/Canonical 版本是 `2024`。详情页也把 `record.standard_id` 标为“标准版本”。这不满足保存并展示标准版本的 MUST。
3. **只读详情没有展示实际输入快照。** records.sqlite 已保存 `raw_input_snapshot_json`，但详情页只列出顶层字段名。独立探针写入 `activity_amount=12345.678` 和 `proof=PROOF-X` 后，详情中两个值均不可见，仅显示“原始输入快照字段：activity_amount, proof”。用户无法按项目目标查看历史活动数据和证明输入。
4. **未计算输入没有完整丢弃，关闭软件也没有提示。** 确认离开后代码只清空部分 `QLineEdit` 和复选框，不重置核算期间、下拉选择、排放源状态或动态电力行。独立探针离开前后均为年份 `2030`、电力行 `2` 条。窗口关闭路径没有调用该门禁；脏页面关闭探针得到 `close_accepted=True`、`prompt_calls=0`。这不满足“离开含有未计算输入的页面时提示并丢弃”，也与关闭后只能重新新建核算的既定规则不符。
5. **测试未覆盖上述真实路径。** 当前 8 项 G07 测试全部通过，但使用显式 SQLite 注入，只断言企业名称文本框被清空，没有检查默认应用重启持久化、正确 standard_version、实际输入值详情、全部控件/动态行重置或窗口关闭提示。

### 本次实际执行的验收命令

- G07 定向：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g07_records -v`；8/8 通过，0 个失败，0 个错误，0 个跳过。
- G06 与数据库迁移回归：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page tests.test_g02_persistence -v`；34/34 通过，0 个失败，0 个错误，0 个跳过。
- 项目全量：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；111/111 通过，0 个失败，0 个错误，0 个跳过。
- 编译：`.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\sol-g07-acceptance-20260919 --app-version g07-sol-acceptance`；三库生成成功，records 迁移为 001、002，临时数据库及 PDF 渲染目录均已清理。

### 范围与门禁

- 未修改、删除或覆盖 `计算表/`；未处理既有未跟踪 `docs/handoffs/`；未发现 G08、报告导出、记录重算或恢复删除 UI 越界。
- 本次只记录验收结论，不修改业务代码，不创建或执行 G08。

G07 未通过，不允许进入 G08。请 Luna 只修正上述 G07 未通过项并补充真实默认启动、重启持久化、标准版本、完整详情、完整丢弃和关闭提示测试；修正完成后发送“重新验收G07”。

## G07 验收返工实施状态（2026-09-19）

**READY_FOR_SOL_REACCEPTANCE**

本轮仅修正 Sol G07 正式验收指出的四类业务缺口和测试缺口；未创建或执行 G08，未修改 schema_version、数据库迁移或“计算表/”，未处理既有未跟踪 `docs/handoffs/`。

### 已完成

- 正式应用入口在未显式注入仓储时默认创建用户数据目录下的 `records.sqlite` 仓储；测试和调用方仍可显式注入内存仓储。
- `AccountingRecord` 保存独立的 Canonical `standard_version`；GB/T 32151.34—2024 当前保存版本为 `2024`，同时保留稳定 `standard_id`，列表详情分别展示编号和版本。
- 记录详情以只读 JSON 展示 records.sqlite 中保存的实际输入快照值，包括活动量、电力明细、证明状态和其他输入，不回查当前页面状态。
- 离开未计算页面和关闭主窗口均经过同一确认门禁；确认丢弃后完整重置期间、下拉项、排放源状态、材料基准、证明字段、动态电力明细、结果、校验和内部计算索引；取消则保留页面并阻止导航/关闭。
- 既有 G00-G06 页面测试显式注入隔离内存仓储，新增测试覆盖真实默认启动、关闭并重启后的 records.sqlite 持久化、真实标准版本、详情快照、完整丢弃和关闭确认。

### 验证结果

- G07 定向：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g07_records -v`；11/11 通过，0 个失败，0 个错误，0 个跳过。
- 项目全量：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；114/114 通过，0 个失败，0 个错误，0 个跳过。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir tmp\g07-rework-final-databases-20260919 --app-version g07-rework-final`；`catalog.sqlite`、`user.sqlite`、`records.sqlite` 均生成成功，专用临时目录已清理。
- `git diff --check` 通过；`git diff --name-only -- '计算表/**'` 无输出；未执行 pytest、G08 构建或安装交付检查，原因是项目测试基线为 unittest 且 G08 仍受阶段门禁禁止。

### Git 与阶段门禁

- 实现与测试提交：`b12a75b fix: close G07 persistence and input lifecycle gaps`。
- 本轮文档更新后，工作区仅保留既有未跟踪 `docs/handoffs/`；该目录未处理、未纳入提交。
- G08 未创建、未执行；当前停止等待 Sol 重新验收 G07。

## G07 Sol 正式重新验收结论（2026-09-19）

### 结论

**PASS WITH MINOR FIXES**

被验收 HEAD：`c4677a59f1d09f77d7294cd3bb500a9875815651`。

本次以 GitHub `main` 已提交内容为验收对象。上一轮 FAIL 指出的默认持久化、真实标准版本、实际输入快照、完整丢弃和关闭门禁均已在 `b12a75b` 中关闭；从上次验收 findings 到本 HEAD 仅包含该修复提交和 `c4677a5` 文档就绪提交，未发现 G08 实施。

### 已通过项

- 正式应用未显式注入仓储时默认使用用户数据目录 `records.sqlite`；SQLite 初始化会创建父目录并执行 records 迁移。
- 成功记录在同一事务内写入记录主体、输入/结果/参数/有效规则快照与 CREATE 审计；审计写入失败会回滚记录。
- ERROR 不生成成功记录；`COMPLETED` 与 `COMPLETED_WITH_WARNINGS` 两种成功状态均有模型和持久化路径。
- `standard_id` 与 `standard_version` 已分离；GB/T 32151.34—2024 当前保存版本为 `2024`。国家标准全文公开系统对应标准页面亦确认标准号为 GB/T 32151.34-2024、发布日期 2024-08-23、实施日期 2025-03-01。
- 原始输入快照、有效规则 ID、参数来源快照、排放源判断、结果和警告均由记录快照读取，不以当前页面值替代。
- 同一输入连续成功计算使用 UUID 生成不同记录 ID；旧记录无更新覆盖路径。
- 删除为软删除，带二次确认、删除人/原因和 DELETE 审计；默认列表不展示已删除记录，记录 ID 不可复用。
- 离开未成功计算页面与关闭主窗口均经过同一丢弃确认门禁；确认后重置期间、下拉项、排放源状态、动态电力明细、结果、校验和内部计算索引。
- 首页最近记录和核算记录页均从同一 records 仓储读取。
- 未发现报告/导出、历史编辑、基于历史记录重新核算或 G08 Windows 交付内容提前实施。

### 需要小修

1. **记录详情的可读性未完全达到上一轮修正要求。** 当前页面把 `raw_input_snapshot_json` 通过格式化 JSON 整段展示，实际值已经可见且只读，但仍使用内部字段名和嵌套结构。上一轮 findings 明确要求“只读、可理解的分组展示活动数据、排放源状态、电力明细、证明状态和其他 G06 输入”。应只改展示层，把同一历史快照按业务分组和中文字段名呈现；不得回查当前页面或当前 Catalog，不得修改历史数据。
2. **缺少一条直接覆盖 G07 验收条件的历史稳定性回归。** 当前 G07 测试已验证 SQLite 往返、标准版本和实际输入快照，但未直接构造“先生成记录 → 修改/替换当前 Catalog 参数 → 再打开历史详情 → 历史结果与参数快照保持不变”的测试。现有实现从代码路径看使用冻结快照，未发现实际回查 Catalog 的缺陷；仍应补此回归以锁定验收条件。

### 测试与复验情况

- 实施方最近落盘记录：G07 定向 `11/11` 通过；全量 unittest `114/114` 通过；`compileall`、`pip check`、Canonical 校验和三库从零重建均成功。
- 本次 Sol **没有把上述数字冒充为独立执行结果**。验收容器只有 Python 3.13.5，而项目 `pyproject.toml` 冻结为 `>=3.12,<3.13`；容器未安装 PySide6，且外网/DNS 受限，无法取得依赖或直接 clone 后重跑 GUI 测试。
- 本次实际执行的环境探针：`python3 --version` 得到 `Python 3.13.5`；导入 `PySide6` 得到 `ModuleNotFoundError`；直接 `git clone https://github.com/adgo07/GHGTOOL.git` 因 `Could not resolve host: github.com` 失败。
- 因此本次结论结合 GitHub 当前 HEAD 的逐项源码/迁移/测试静态复核、上一轮已落盘测试记录和官方标准来源核对给出；未授予无保留 PASS。

### Git、范围与门禁

- GitHub `main` 验收前 HEAD：`c4677a59f1d09f77d7294cd3bb500a9875815651`。
- 最近 5 个提交已复核：`c4677a5`、`b12a75b`、`2abce5d`、`8510c21`、`707c59a`。
- 从上一轮 findings `2abce5d` 到验收 HEAD 仅前进 2 个提交：G07 修复 + 返工就绪文档；未发现 G08 越界。
- GitHub 连接器只能看到已提交树，不能读取用户开发机的未跟踪工作区，因此无法独立复核开发机本地 `git status` 中既有 `docs/handoffs/`。已提交树中未发现验收临时数据库/测试产物，也未发现 `计算表/` 用户文件被纳入或修改。
- 本次只修改 `TASK_STATE.md` 与 `IMPLEMENTATION_REPORT.md` 的验收记录，不修改业务代码、标准数据或用户文件。

G07 当前结论为 PASS WITH MINOR FIXES，不允许进入 G08。完成上述两项小修并在 Python 3.12 + PySide6 环境重跑 G07 定向测试及必要回归后，应发送“重新验收G07”。

## G07 历史详情小修实施状态（2026-09-19）

**READY_FOR_SOL_REACCEPTANCE**

本轮只处理 Sol 指出的两项 G07 小修；未创建或执行 G08，未修改 schema_version、数据库迁移或“计算表/”，未处理既有未跟踪 `docs/handoffs/`。

### 已完成

- 历史记录详情不再直接展示格式化 JSON；从冻结 `raw_input_snapshot_json` 生成面向普通用户的只读分组：活动数据、排放源、电力明细、证明状态、其他输入。电力取得方式、属性、数量和单位使用业务标签展示，内部枚举值转换为中文，实际历史值仍来自记录快照。
- 新增稳定性回归：生成记录后修改隔离测试 Catalog 的参数名称和来源定位，再刷新历史详情；详情文本保持完全一致，历史参数快照、活动量和其他输入不受当前 Catalog 变化影响。

### 验证结果

- G07 定向：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g07_records -v`；12/12 通过，0 个失败，0 个错误，0 个跳过。
- 项目全量：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；115/115 通过，0 个失败，0 个错误，0 个跳过。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功并清理专用临时目录；`git diff --check` 通过；`git diff --name-only -- '计算表/**'` 无输出。

### Git 与阶段门禁

- 实现与测试提交：`d6e4d91 fix: refine G07 history snapshot details`。
- 当前等待 Sol 重新验收 G07；G08 未创建、未执行。


## G07 Sol 最终正式重新验收结论（2026-09-19）

### 结论

**PASS**

被验收 HEAD：`7e3573dfd7fc105cc013c07028c5eb8815836569`（`merge: preserve remote G07 acceptance findings`）。

本次以 GitHub `main` 当前已提交树为验收对象，并以此前 G07 已通过项为基础，重点重新核对上次 `PASS WITH MINOR FIXES` 的两项小修、对应测试、提交范围及 G08 阶段门禁。

### 两项小修复核

1. **历史详情业务化分组：通过。** `packages/ui/pages.py` 不再直接显示内部 JSON；历史 `raw_input_snapshot_json` 被转换为“活动数据、排放源、电力明细、证明状态、其他输入”五个只读分组。常见字段和枚举值使用中文业务标签；数据仍读取 records.sqlite 中冻结的历史快照，没有改写记录、回查当前页面输入或改变计算口径。
2. **Catalog 变化后的历史稳定性回归：通过。** `tests/test_g07_records.py` 新增 `test_historical_snapshot_stays_stable_after_catalog_parameter_change`：先生成历史记录，再修改隔离 Catalog 中当前参数名称和来源定位，刷新历史记录后断言完整详情保持不变，并确认修改后的当前 Catalog 文本不会进入历史详情。结合 `RecordLibraryPage` 本身不依赖 Catalog 查询的实现，满足 HANDOFF 的“修改 catalog 当前参数后，历史记录展示不改变”验收条件。

### G07 其余 MUST 与验收条件复核

- 正式应用默认使用用户数据目录 `records.sqlite`，成功计算形成不可编辑新记录。
- 成功记录主体、输入/结果/参数/有效规则快照及 CREATE 审计使用单一 SQLite 事务；审计失败会回滚，不产生半条记录。
- ERROR 不生成成功记录；支持 `COMPLETED` 和 `COMPLETED_WITH_WARNINGS`。
- 同一输入连续成功计算生成不同记录 ID，旧记录不覆盖。
- `standard_id` 与真实 `standard_version` 分开保存；GB/T 32151.34—2024 保存版本为 `2024`。
- 记录列表具备搜索/状态筛选，详情只读；历史输入、排放源判断、结果、参数来源、有效规则和警告均来自记录快照。
- 删除需要二次确认，采用软删除并写 DELETE 审计；默认列表隐藏已删除记录，审计证据保留。
- 未计算输入离开页面和关闭主窗口均执行确认门禁；确认后完整恢复新核算状态。
- 首页最近记录从同一 records 仓储读取。
- 未发现基于记录重新核算、恢复已删除记录 UI、报告/导出、历史编辑或 G08 Windows 交付内容提前实施。

### 原始标准/官方来源核对

- 国家标准全文公开系统当前记录确认：`GB/T 32151.34-2024`《温室气体排放核算与报告要求 第34部分：炭素材料生产企业》状态为“现行”，发布日期 `2024-08-23`，实施日期 `2025-03-01`。
- 本轮小修只涉及历史详情展示和回归测试，没有修改标准公式、Canonical 参数、排放因子、标准版本数据或数据库迁移。

### 测试与复验情况

项目本地实施记录（已落盘）：

- G07 定向：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g07_records -v`；**12/12 通过，0 失败，0 错误，0 跳过**。
- 项目全量：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；**115/115 通过，0 失败，0 错误，0 跳过**。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功，专用临时目录已清理；`git diff --check` 通过；`git diff --name-only -- '计算表/**'` 无输出。

Sol 当前执行环境限制：

- 当前验收容器为 Python `3.13.5`，项目冻结要求为 Python `>=3.12,<3.13`。
- 当前容器没有 PySide6，且没有可用的项目 Python 3.12 运行时；GitHub 当前提交也没有 Actions workflow run 可作为替代的独立远端执行环境。
- 因此本次没有把 12/12 与 115/115 表述为 Sol 在本容器内重新执行的结果；这些是项目本地已经执行并写入阶段文件的真实测试记录。本次 Sol 对新增代码、测试逻辑、提交范围、已有 G07 事务/记录路径和官方标准来源进行了独立复核，未发现与测试记录相矛盾的证据。

### Git、范围与阶段门禁

- 验收前 GitHub `main` HEAD：`7e3573dfd7fc105cc013c07028c5eb8815836569`。
- 最近 5 个提交：`7e3573d`、`3766294`、`d6e4d91`、`bcdb661`、`c4677a5`。
- 从上次验收提交 `bcdb661` 到本次被验收 HEAD 只涉及：`packages/ui/pages.py`、`tests/test_g07_records.py`、`TASK_STATE.md`、`IMPLEMENTATION_REPORT.md`。
- 未修改数据库 schema、Canonical 数据、计算公式或标准参数；未发现 G08 实施。
- GitHub 只能核对已提交树，无法读取用户开发机未跟踪文件；按用户本轮说明，本地与远端提交一致，`docs/handoffs/` 仍未上传，`计算表/` 未修改。
- 本次验收只更新 `TASK_STATE.md` 与 `IMPLEMENTATION_REPORT.md`，不修改业务代码、测试代码、标准数据或用户文件。

**G07已通过，允许由用户另行启动G08；本次未启动G08。**
## G08 实施状态（2026-09-20）

**G08_REWORK_IN_PROGRESS**

本轮严格只执行 G08；未创建或执行 G09，未修改 `计算表/`，未处理既有未跟踪 `docs/handoffs/`。工作从已对齐的 `origin/main` `fbe884df0dad890f1be6da945a52b288ea8c8f1c` 创建 `gxx-implementation` 分支并恢复唯一 G08 Goal。

### 实现内容

- 应用版本更新为 `1.0.0`；Canonical `schema_version` 保持 `1.0.0`，未新增数据库迁移；Catalog `data_version` 更新为 `2026.09.20-g08.1`，三个数据库迁移版本仍为 catalog `001`、user `001`、records `002`。
- 增加 PyInstaller `onedir/windowed` 构建脚本、独立绝对导入入口、`build-manifest.json` SHA-256/大小清单和发布审计脚本。发布审计只允许 `databases/catalog.sqlite` 作为 SQLite，并拒绝标准全文、用户 `计算表/`、测试/开发目录、环境文件和密钥。
- standalone 运行时从包内 Catalog 启动，records.sqlite 与结构化日志写入 `%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting`；未知未来迁移版本和数据库不可打开均以 `MigrationError` 安全失败，不删除或覆盖用户数据。
- 交付说明、安装/启动、数据目录、卸载数据保留、当前限制、故障排查和 Windows CI 构建/审计/双启动烟测已补齐。

### 验证结果

- G08 定向：`.venv\Scripts\python.exe -m unittest tests.test_g08_delivery -v`；7/7 通过。
- G02/G04/G05/G06/G07 相关回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_multi_electricity tests.test_g05_rules tests.test_g06_carbon_material tests.test_g06_page tests.test_g07_records -v`；89/89 通过。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；122/122 通过。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir <temporary>`；catalog、user、records 均成功生成，临时目录已清理。
- Windows 11 本机 standalone：`build_standalone.py --output-root dist --clean` 成功；`inspect_release.py` 通过（229 files）；`smoke_standalone.py` 双启动通过，隔离 records.sqlite 和 application.jsonl 均创建。Windows 10 未具备独立实机环境，未宣称已验证。
- `git diff --check` 通过；`git diff --name-only -- '计算表/**'` 无输出；`docs/handoffs/` 保持原有未跟踪状态。

### 阶段门禁

当前等待 GitHub PR 检查和 Sol 预验收；不得开始 G09。提交 SHA、PR 链接和 GitHub 检查状态将在推送后补录。
## G08 预验收 NEEDS FIX 返工状态（2026-09-20）

**G08_REWORK_READY_FOR_GITHUB_CHECKS**

本轮只处理 G08 预验收指出的五项交付缺口，未创建或执行 G09，未修改 计算表/，未处理既有未跟踪 docs/handoffs/。

### 已完成的修正

- 发布 manifest 不再把 .gitkeep 等隐藏占位文件列为交付内容；构建阶段移除发布目录中的隐藏占位文件，并新增 verify_release_archive.py，按 GitHub upload-artifact 默认不上传隐藏文件的规则模拟最终归档，再对归档解压结果执行完整 manifest 校验。
- Catalog app_compatibility 统一为 1.x，与应用 1.0.0 相容范围一致；发布审计和 G08 测试均锁定该字段。
- 交付文档区分真实 Windows 11 本机证据与 GitHub windows-latest 的 Windows Server 2025 运行环境；不再把后者表述为 Windows 11 CI，Windows 10 22H2 仍明确为未验证。
- Windows CI 保留 PR merge-ref 集成测试，并新增 exact PR head 的 standalone 构建；manifest 分别记录 source_commit、pr_head_sha 和 tested_merge_sha，上传前对最终可见文件集合执行归档一致性验证。
- G08 测试新增 fresh-data GUI 全链路：新用户启动、进入 GB/T 32151.34 页面、录入并计算、records.sqlite 生成记录、重启后历史页面读取记录。

### 本地验证

- 实施与测试提交：59d4a8e fix: close G08 delivery preacceptance gaps。
- G08 定向：.venv\\Scripts\\python.exe -m unittest tests.test_g08_delivery -v；9/9 通过。
- 相关回归：tests.test_g08_delivery、tests.test_g02_canonical、tests.test_g02_persistence、tests.test_g04_catalog、tests.test_g05_multi_electricity、tests.test_g05_rules、tests.test_g06_carbon_material、tests.test_g06_page、tests.test_g07_records；98/98 通过。
- 全量：.venv\\Scripts\\python.exe -m unittest discover -s tests -t . -q；124/124 通过。
- compileall 成功；pip check 为 No broken requirements found.；Canonical 为 valid: 9 standards, 12 sources, 7 parameters, 7 factors；三库从零重建成功并清理临时目录。
- Windows 11 本机证据：Windows 11 Professional x64，版本 10.0.26200、Build 26200、AMD64；Python 3.12.14、PySide6 6.11.2、PyInstaller 6.22.3。standalone 构建、发布目录审计（227 个内容文件）、模拟 GitHub 最终归档审计（228 个可见条目）和双次隔离启动均通过。
- 本地 manifest 已验证 app_version=1.0.0、catalog_data_version=2026.09.20-g08.1；返工后的 GitHub exact-head 构建将按同一规则生成新的三项 SHA 追溯字段。

### 阶段门禁

返工代码和文档完成后推送 gxx-implementation，等待以新 PR head 触发的 GitHub merge 集成检查和 exact-head standalone 检查全部完成；在 Sol 重新预验收前不得开始 G09。

## G08 Sol 正式验收结论（2026-09-20）

**PASS**

- 被验收候选 SHA：`d24fa6f19f19f6aab1770585023f517dd50ad784`。
- GitHub PR：`#1 feat: complete G08 Windows delivery baseline`；该候选 SHA 对应的 Windows / Python 3.12 merge-ref 全量测试与 exact-head standalone 审计均成功。
- G08 定向测试：`.venv\Scripts\python.exe -m unittest tests.test_g08_delivery -v`；9/9 通过。
- G02/G04/G05/G06/G07/G08 相关回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_multi_electricity tests.test_g05_rules tests.test_g06_carbon_material tests.test_g06_page tests.test_g07_records tests.test_g08_delivery -v`；98/98 通过。
- 全量测试：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；124/124 通过。
- 补充校验：`compileall` 成功；`pip check` 无损坏依赖；Canonical 校验通过（9 standards / 12 sources / 7 parameters / 7 factors）；catalog、user、records 三库从零重建成功，临时目录已清理。
- Windows 11 x64 独立构建成功；发布目录审计通过（227 个内容文件）；模拟 GitHub 最终归档审计通过（228 个可见条目）；隔离环境双启动冒烟通过。manifest 已核对 `app_version=1.0.0`、`catalog_data_version=2026.09.20-g08.1` 及三项 Git SHA 追溯字段。
- Windows 10 22H2 因无独立实机环境未验证，交付文档已明确记录，符合 G08 的允许条件。原生界面自动化辅助程序因本机 Windows 沙箱初始化失败未能执行，因此未把人工界面操作列为验收证据；Qt fresh-data GUI 全链路测试和真实独立程序双启动冒烟均已实际完成。
- 已核对 G08 的 MUST、Scope 和阶段门禁；未发现标准、参数或排放因子口径变更；未实施报告导出、Excel 导入、其他七项标准等越界功能；`计算表/` 无修改；既有未跟踪 `docs/handoffs/` 未处理。

G08 已通过。G08 是当前 `HANDOFF.md` 定义的最终阶段，Windows V1 的 G00—G08 阶段门禁已完成；本次未启动任何未批准的后续阶段。验收文档提交后须推送当前 PR 分支，并以该验收提交重新确认 GitHub 检查通过后，方可普通 Merge 到 `main`。

## G08 验收后退出确认框缺陷修复（2026-09-20）

**READY_FOR_REVIEW**

在 G08 正式验收通过后进行实际界面测试时发现：新建核算页面存在未计算输入，点击其他导航或关闭窗口，在确认框选择 Yes 仍被阻止；本轮仅修复该 G07 生命周期回归，不创建或执行 G09。

### 修复

- packages/ui/carbon_material_page.py 将 QMessageBox 返回值从对象身份比较改为相等比较，兼容 PySide6 返回 StandardButton 枚举或其整数值（Yes=16384）。
- tests/test_g07_records.py 的导航、关闭和删除确认测试覆盖整数形式的 Yes 返回值；导航确认后验证页面切换和输入清空，关闭确认后验证窗口关闭。

### 验证

- G07 定向：tests.test_g07_records；12/12 通过。
- 项目全量：unittest discover -s tests -t . -q；124/124 通过。
- compileall apps packages scripts tests：成功。
- 修复分支：codex/g08-discard-confirmation-fix；main 未直接修改。
- G09 未创建、未执行；计算表/ 和既有未跟踪 docs/handoffs/ 未处理。
## G08 验收后输入保留行为调整（2026-09-20）

**READY_FOR_REVIEW**

Sol/用户确认采用无弹窗方案：新建核算页面在应用运行期间切换导航不再询问或清空输入；关闭窗口直接退出，未成功计算的输入只保留在内存中，不写入草稿，也不承诺下次启动恢复。未创建或执行 G09。

### 实现与测试

- AppShell 导航不再调用放弃输入门禁；页面对象继续缓存，因此返回新建核算页面时已填写内容保持不变。
- 主窗口关闭直接接受关闭事件；兼容性确认方法不再弹窗。
- 新增/调整导航保留和关闭直退回归测试。
- G07 定向：12/12 通过；项目全量：124/124 通过；compileall 成功；pip check 无损坏依赖。
- 修复分支：codex/g08-discard-confirmation-fix；main 未直接修改。

## G08 验收后修复版交付状态（2026-09-20）

**DELIVERED_LOCALLY**

- 已将修复版替换到 D:\\project\\碳排放核算工具\\dist\\QingzhouCarbonAccounting\\QingzhouCarbonAccounting.exe。
- 原版本保留在 dist\\QingzhouCarbonAccounting-legacy，未删除，便于回退。
- 修复分支已快进合并到本地 main，当前合并提交为 e64311a。
- 原路径发布审计通过（227 files），standalone 双启动 smoke 通过（2 isolated starts）。
- G09 未创建、未执行；计算表/ 和既有未跟踪 docs/handoffs/ 未处理。

## UIR01 实施状态（2026-09-20）

**UIR01_READY_FOR_SOL_REVIEW**

本阶段从 origin/main 最新基线 a42bedc 创建独立分支 ui-refactor-uir01-field-semantics，仅实施 Post-V1 新建核算 UI 重构的 UIR01；未创建或实施 UIR02、UIR03、UIR04。

实现提交：2017832（feat: add UIR01 field semantics and typed inputs）。
文档最终提交：dac401b（docs: finalize UIR01 status and report）。

### 已完成

- 在 packages/ui/field_specs.py 建立 GB/T 32151.34—2024 当前页面的 FieldSpec Presentation 映射，覆盖身份、边界、十项排放源状态、燃料、P01-P04B、材料基准、电力明细、I02/I03/I04 和热力参数选择理由。
- 中文 display_name、standard_symbol、单位、范围、必填性、帮助文本、标准条款/来源定位和 advanced 属性来自仓库已有冻结映射或标准定位；普通用户标签不再直接使用 gc、wfc、bpm、gpmvar 等内部变量名。
- 在 packages/ui/typed_inputs.py 建立文本、数量、百分比、整数、枚举、布尔和只读标准参数控件 helper；数值控件即时拒绝字母、负值和超范围百分数，单位由 FieldSpec 控制。
- 百分比 UI 使用 0—100，进入 Domain 前以 Decimal 显式转换为 ratio 0—1；未修改 CarbonMaterialInput、GB/T 32151.34 公式、Canonical、SQLite schema、records.sqlite 或输入保留行为。
- 页面燃料、过程、材料基准、电力、热力和输出能源控件已接入 FieldSpec；现有对象名、导航/关闭时输入保留和成功计算立即记录行为保持不变。
- HANDOFF.md 已在末尾增加 Post-V1 UIR01～UIR04 治理章节，未改写 G00-G08 历史章节。

### 定向测试

- tests/test_uir01_field_semantics.py：5/5 通过，覆盖 FieldSpec 完整性、普通模式标签、数值输入边界、比例双向转换以及 Domain Input/计算结果等价。
- tests/test_g06_page.py、tests/test_g06_carbon_material.py、tests/test_g07_records.py、tests/test_g08_delivery.py 合计 54/54 通过。
- 项目全量测试：129/129 通过。

### 阶段门禁

UIR01 未开始 UIR02；完成提交后停止等待 Sol 验收。既有未跟踪 docs/handoffs/ 保持原样，不处理、不提交；计算表/ 未修改。

## UIR01 验收返工状态（2026-09-21）

**UIR01_REWORK_READY_FOR_SOL_REVIEW**

Sol 验收发现原 NumericLineEdit 只覆盖了程序化 `setText()`，Qt 实际键盘输入中 `QDoubleValidator` 会把百分比 `101` 标为 Intermediate，导致越界值仍显示；负号还可能被丢弃后把 `-1` 变成 `1`。本轮仅修复该 UIR01 阻断项，未开始 UIR02。

### 返工内容

- `packages/ui/typed_inputs.py` 新增 Decimal-aware 严格候选校验器；键盘事件在 QLineEdit 修改文本前检查完整候选值，立即拒绝越界、负号、字母和千位分隔符。
- 覆盖粘贴路径，非法粘贴值整体拒绝；对被拒绝的负号序列做阻断，避免 `-1` 静默变为 `1`。
- 保留 0、100 边界、合法小数、空值和修正后继续输入行为；Domain 仍使用 Decimal，未改公式或数据模型。
- `tests/test_uir01_field_semantics.py` 增加真实 Qt 键盘、Ctrl+V 粘贴、千位分隔符、边界值和非法输入修正回归。

### 返工验证

- UIR01 定向测试：`.venv\Scripts\python.exe -m unittest tests.test_uir01_field_semantics -v`；6/6 通过，0 失败，0 错误，0 跳过。
- G06/G07/G08 相关回归：`.venv\Scripts\python.exe -m unittest tests.test_uir01_field_semantics tests.test_g06_page tests.test_g06_carbon_material tests.test_g07_records tests.test_g08_delivery`；55/55 通过。
- 项目全量测试：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -q`；130/130 通过。
- `compileall`、`pip check`、Canonical 校验和三库从零重建均通过；Canonical 为 9 standards / 12 sources / 7 parameters / 7 factors。

返工实现提交：`249e5f9c2849b06d8b40b064d35b6167d559407d`。当前停止等待 Sol 重新验收 UIR01；不得开始 UIR02。既有未跟踪 `docs/handoffs/` 保持原样且未纳入提交，`计算表/` 未修改。

## UIR01 正式通过与 UIR02 启动状态（2026-09-21）

**UIR02_IN_PROGRESS**

UIR01 已由 Sol 正式验收 PASS，PR #4 已合并到 `main`；以上 UIR01 返工状态是历史实施记录，本节记录其后正式验收与合并事实，不改写历史内容。当前唯一实施阶段为 UIR02，基线为实时 `origin/main@09e9d5e66f30f46f4302f6b57f330c27c4a852a3`，分支为 `ui-refactor-uir02-source-cards`。

当前仅同步治理文件，业务代码尚未开始修改。UIR02 只实现统一“排放源与活动数据”页面、十个排放源 Presentation 卡片、状态派生、业务分组、输入保持和指定回归；不得启动 UIR03。既有未跟踪 `docs/handoffs/` 保持原样、不处理、不提交；`计算表/` 保持未修改。

## UIR02 实施完成状态（2026-09-21）

**UIR02_READY_FOR_SOL_REVIEW**

UIR02 已在实时 `origin/main` 基线 `09e9d5e66f30f46f4302f6b57f330c27c4a852a3` 上的独立分支 `ui-refactor-uir02-source-cards` 完成。治理扩展提交为 `a90777a`，实现与专项测试提交为 `ed752c0`；未创建、未实施 UIR03。

### 实施范围

- 将原“03 排放源识别”和“04 活动数据”合并为“02 排放源与活动数据”。
- 新增可复用 `SourceCard` Presentation 组件和 UI-only `SourceCardPresentationState`，覆盖十个既有排放源；Domain `EmissionSourceStatus`、`CarbonMaterialInput.source_states` 和数据库模型未改动。
- 默认“不涉及”卡片折叠；“启用”只将现有状态设为 `INVOLVED` 并展开，不制造活动数据；折叠/展开不改变 Domain 状态。
- 为煅烧、焙烧/炭化、石墨化按投入数据、产出数据、其他必要数据分组；摘要只显示业务名称、数量和完成度，不显示内部变量名或稳定 ID。
- 所有输入继续使用 UIR01 `FieldSpec`/typed input；I01 多条电力明细、独立取得方式/属性/证明/参数状态和页面导航输入保持行为未改变。

### 验证结果

- UIR02 定向：`.venv\Scripts\python.exe -m unittest tests.test_uir02_source_cards -v`；7/7 通过。
- UIR02 与指定回归：`.venv\Scripts\python.exe -m unittest -v tests.test_uir02_source_cards tests.test_uir01_field_semantics tests.test_g06_page tests.test_g06_carbon_material tests.test_g07_records tests.test_g08_delivery`；62/62 通过。
- 全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；137/137 通过，0 失败，0 错误，0 跳过。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`；通过。
- 依赖：`.venv\Scripts\python.exe -m pip check`；通过，No broken requirements found。
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；9 standards / 12 sources / 7 parameters / 7 factors，通过。
- 三库从零重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir <临时目录>`；`catalog.sqlite`、`user.sqlite`、`records.sqlite` 均成功生成，临时目录已清理。
- `git diff --check`：通过；`计算表/` 无修改；没有将测试数据库、临时文件、标准全文或敏感数据加入提交。

### 阶段门禁

本地实现与测试已完成；PR #5 的代码候选 head `ec8bfec1e5671fa6b92e1995ce6693f6ea22a296` 对应 Actions run `35550650466` 已成功通过 merge-ref full tests 与 exact PR-head standalone audit。报告同步提交后需以最新 head 的检查结果为准；随后停止等待 Sol 独立验收。未执行 UIR03；既有未跟踪 `docs/handoffs/` 保持原样、不处理、不提交。

## UIR02 返工状态（2026-09-21）

**UIR02_REWORK_READY_FOR_SOL_REVIEW**

本轮仅依据 Sol 对 PR #5 的 UIR02 FAIL 意见返工，仍在 `ui-refactor-uir02-source-cards` 分支上进行，未创建或实施 UIR03。

### 返工内容

- 在 `packages/ui/carbon_material_page.py` 增加 Presentation-only 的电力解析状态缓存；I01 卡片只有在每条活动明细均由现有 G05 解析形成参数快照时才显示“已完成”。证明缺失、解析阻断、自发自用化石能源转交或解析异常均显示“需要处理”，不改变 Domain 路径。
- 在页面已有 `_run_calculation()` 结果上记录 source-scoped ERROR，仅将既有 Domain 校验反馈给对应卡片；未复制、重写或新增 Domain 校验规则。
- 将多电力专项测试中的自发自用非化石明细补成有效月度原始记录证明，保留“证明缺失 → 需要处理”的独立回归。
- 将 UIR02 折叠 parity 测试改为完整合法的 GB/T 32151.34 输入，并明确断言折叠前后均成功、结果和参数快照等价；新增非收到基缺少换算证明的卡片状态回归。

### 返工验证

- UIR02 定向：`.venv\Scripts\python.exe -m unittest tests.test_uir02_source_cards -v`；9/9 通过，0 失败，0 错误，0 跳过。
- UIR02 与指定回归：`.venv\Scripts\python.exe -m unittest tests.test_uir02_source_cards tests.test_uir01_field_semantics tests.test_g06_page tests.test_g06_carbon_material tests.test_g07_records tests.test_g08_delivery -v`；64/64 通过，0 失败，0 错误，0 跳过。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；139/139 通过，0 失败，0 错误，0 跳过。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests`；通过。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`。
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：使用 `scripts\build_catalog.py` 和 `scripts\initialize_databases.py` 在隔离临时目录生成 catalog/user/records 三库，成功后已清理临时目录。
- `git diff --check`：通过；`计算表/` 无修改；本轮未处理、未提交既有未跟踪 `docs/handoffs/`，未加入测试数据库、标准全文、敏感数据或 UIR03 产物。

### 门禁

- 当前状态：返工完成，等待 Sol 重新验收 UIR02。
- PR #5 保持以 `main` 为目标，修复将同步到同一 PR；不得合并 PR，不得启动 UIR03。

## UIR02 I02 Domain 错误归属返工状态（2026-09-21）

**UIR02_REWORK_READY_FOR_SOL_REVIEW**

本轮继续只返工 UIR02，针对 Sol 在 PR #5 最新 head `92595bb4` 发现的 I02 阻断问题完成修复；未创建、未实施 UIR03。

### 问题与修复

- 原问题：购入热力/动力 I02 在有热力数量和因子、但缺少焓值或压力时，Domain 已产生 `CAR-VAL-STEAM-STATE`，其动态 `field_id` 为 `heat-1`，旧的仅按 source ID 前缀匹配逻辑无法把错误归属到 I02 卡片，卡片可能错误显示“已完成”。
- 修复：在 Presentation 层增加 Domain problem field 到 source card 的归属映射，支持现有 source ID、动态电力/热力/输出明细 ID 及稳定字段前缀；卡片只消费既有 Domain 错误，不复制或改写 Domain 校验规则。
- 增加 I02 回归：缺少蒸汽状态时必须显示“需要处理”且不得显示“已完成”；补充焓值后重新计算，错误消失并恢复“已完成”。
- 页面参数边界增加显示单位到 Domain 单位的 Presentation 转换（例如 `tCO₂/GJ` 到 Domain 使用的 `tCO2/GJ`），未修改 Canonical、Domain 公式、数据模型或数据库 schema。

### 验证

- UIR02 定向：`.venv\Scripts\python.exe -m unittest tests.test_uir02_source_cards -v`；10/10 通过。
- UIR02 与指定回归：UIR02、UIR01、G06 页面、G06 Domain、G07 records、G08 delivery；65/65 通过。
- 全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；140/140 通过，0 失败，0 错误，0 跳过。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests`；通过。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`。
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建：独立临时目录成功生成 `catalog.sqlite`、`user.sqlite`、`records.sqlite`，完成后已清理。
- `git diff --check`：通过；`计算表/` 无差异；未加入测试数据库、临时文件、标准全文或敏感数据。

### 阶段门禁

- 实现与测试提交：`7fe978c` `fix: map UIR02 domain errors to source cards`。
- 当前工作仍在 `ui-refactor-uir02-source-cards` 分支，已同步到 PR #5；当前 PR head 为 `273ea85d264a8eb087eb3699060f1981d572392f`，PR 不合并。
- 既有未跟踪 `docs/handoffs/` 保持原样、不处理、不提交。
- GitHub Actions run `35581128076` 已针对该 head 完成：merge-ref full tests 与 PR-head standalone audit 均为 success。
- 当前状态：返工完成，停止等待 Sol 重新验收 UIR02；不得启动 UIR03。
