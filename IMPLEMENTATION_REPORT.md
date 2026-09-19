# IMPLEMENTATION_REPORT

## 阶段

G08 Windows 交付与全链路回归（实施完成，等待预验收）

## 前置验收与阶段边界

- G00 验收结论：PASS。
- G01 初次验收为 FAILED；能量单位共同基准和领域枚举字符串绕过问题已完成修复。
- G01 重新验收结论：PASS（本轮用户已明确确认）。
- G02 已通过 Sol 最终验收（2026-09-11），G03 已通过 Sol 正式重新验收（2026-09-12）。
- G02 首次验收结论：FAILED；本轮仅处理 Sol 指定的 Canonical/SQLite/G01 枚举、标准职责、来源定位和参数引用返工，未开始 G03。
- 首次返工后状态曾为 READY_FOR_SOL_REACCEPTANCE。
- G02 再次验收结论：FAILED；Sol 指出 0.11 热力因子仍引用钢铁生产附件，本轮完成第二次返工，未开始 G03。
- G02 最终重新验收结论：PASS（2026-09-11）；验收实施基线为 `78ff1f6`，在该验收时 G03 尚未创建或执行。
- G03 正式重新验收结论：PASS（2026-09-12）。本轮创建并执行唯一的 G04 Goal；G05 未创建、未执行。
- G04 正式重新验收结论：PASS（2026-09-12）；被验收 HEAD 为 `28dd8c9`。G05 仍未创建、未执行。

## G06 BLOCKED 停止点（历史，2026-09-13；Sol R6 决策后已解除）

本轮已按 G06 范围开始实现 Domain 公式/校验、Application 参数适配、手工录入页面接线和定向测试；未创建或执行 G07，未修改迁移、计算表/ 或既有 docs/handoffs/。实现尚未提交，因为在冻结口径核对阶段发现必须由 Sol 决策的关键冲突。

### BLOCKED

问题：

- 正式映射文件的 TV-CAR-FML-008 将 GB/T 32151.34—2024 式（8）石墨化测试向量预期写为 3.364166666… tCO₂。
- 正式标准第 5.2.4 条、PDF 第 13 页的式（8）仅含 GPM×GPMVar×K3×44/16 挥发分项；同一向量按该式得到 1.439166666666666666666666667 tCO₂。
- HANDOFF.md 要求发现映射与标准原文疑似不一致时必须 BLOCKED，不得自行改公式。

证据：

- D:\MD仓库\杂\碳排放计算软件\GB T 32151.34—2024 炭素材料生产企业映射方案.md:728。
- packages/standards/carbon_material.py:594-597。
- G06 定向测试最新结果为 8/9 通过，唯一失败为上述向量冲突。

为什么不能按原方案继续：

- 迎合映射期望会改变正式标准计算口径；改测试期望会改变冻结映射。两者都需要标准解释/计算口径批准。

需要 Sol 决策：

- 请确认式（8）固定输入下采用正式标准值 1.439166666666666666666666667，还是采用冻结映射值 3.364166666…；如采用后者，请提供额外项的正式来源/决策。

停止范围：

- 未执行 G06 全量测试、compileall/pip check、Canonical/三库回归验收，未形成 G06 实现提交；G07 未创建或执行。
## G05 第三次返工（获批准后继续，2026-09-13）

### 目标与范围

本轮恢复现有 BLOCKED 的 G05 Goal，仅执行 Sol 已批准的多种电力消费形式第三次返工。没有创建或执行 G06，没有修改 UI、数据库迁移、正式数据库、行业输入页面、行业计算公式或 计算表/，没有处理既有 docs/handoffs/。

### 实现结果

- 在 Canonical Source 中新增独立参数 electricity_emission_factor_nonfossil 和因子 electricity_nonfossil_zero_gbt32151_34_2024，严格使用批准的 0、tCO₂/MWh、STANDARD_SPECIFIED、VERIFIED、SRC-32151-34-2024、2024、2025-03-01、gbt_32151_34_2024 及 PDF 第30页/印刷页22定位。行业标准 parameter_refs 已同步，data_version 更新为 2026.09.13-g05-third-rework.1；schema_version 仍为 1.0.0，SQLite 迁移仍为 001。
- 在 packages/core 建立取得方式与电力属性两个独立枚举维度、证明类型/状态和 ElectricityConsumptionDetail/ElectricityDetailResolution；多条明细共享企业/标准/期间上下文，但各自解析规则、证明、候选因子、选择理由和快照。自发自用化石能源只返回直接燃料路径转交阻断，不进入外购电力间接排放路径。
- CAR-RULE-NONFOSSIL-POWER-001 现在是带条件的显式 OVERRIDE，引用新参数和稳定零因子 ID；零因子判断只使用稳定 ID、参数 ID、值类型和值及来源 ID，不依赖中文 source_location。普通外购电力采用通则最新全国平均因子；非化石电力按外购证明或自发自用月度原始记录门禁采用零因子，证明或 Canonical 零因子缺失均 ERROR 且不回退。
- 回归测试覆盖三明细组合互不覆盖、普通购电、外购非化石、自发自用非化石、证明缺失、Canonical 零因子缺失、稳定 ID 反绕过、自发自用化石防重复路径，以及 G02 Canonical/SQLite 和 G04 参数展示对新增记录的查询。

### 验证结果

- G05 定向：.venv\Scripts\python.exe -m unittest tests.test_g05_rules tests.test_g05_multi_electricity -v；18/18 通过。
- G02 Canonical/持久化与 G04 参数展示：.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog -v；31/31 通过。
- 全量回归：.venv\Scripts\python.exe -m unittest discover -s tests -t . -v；75/75 通过。
- compileall：.venv\Scripts\python.exe -m compileall -q packages apps tests；成功。
- pip check：.venv\Scripts\python.exe -m pip check；No broken requirements found.
- Canonical 校验：.venv\Scripts\python.exe scripts\validate_canonical.py；valid: 9 standards, 12 sources, 7 parameters, 7 factors。
- 三库从零重建：.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir tmp\g05-third-rework-databases；catalog.sqlite、user.sqlite、records.sqlite 均生成成功，临时目录已清理。
- git diff --check 通过；迁移和 计算表/ 路径均无差异；既有 docs/handoffs/ 保留且未处理。pytest 未执行，项目基线为 unittest。

### 提交与门禁

- 实现与回归测试提交：7173394 fix: complete G05 multi-electricity rework。
- 本轮停止等待 Sol 重新验收；G06 未创建、未执行。

## G05 Sol 第三次正式重新验收结论

**结论：PASS**

- 验收日期：2026-09-13。
- 被验收 HEAD：`f080f115f0d7a31249befc0703cfec132c19e515`；G05 多电力返工实现提交为 `7173394`。
- 直接核对原始 GB/T 32151.34—2024 PDF，SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。物理第30页页脚为印刷页22：D.1.1 规定自发自用和市场化交易购入的非化石能源电力因子为零；D.1.2 规定其余全国平均因子采用生态环境部、国家统计局最新发布值；D.2 分别要求市场化交易合同及结算凭证或 GEC、自发自用月度电量原始记录。
- Canonical 和重建后的 SQLite 均确认独立参数 `electricity_emission_factor_nonfossil` 与零因子 `electricity_nonfossil_zero_gbt32151_34_2024` 真实存在，批准字段完整且仅适用于 `gbt_32151_34_2024`；全国平均参数下不存在该零因子。
- 领域实现确认取得方式与电力属性是两个独立维度；组合场景中的三条电力明细共享企业和核算期，但逐条解析、逐条证明校验、逐条生成带 `detail_id` 的独立快照。
- 普通外购电力使用全国平均因子；外购非化石和自发自用非化石分别按 D.2 对应证明使用零因子。缺少证明时产生 `GEN-VAL-NONFOSSIL-EVIDENCE` ERROR，无推荐值、无快照且无全国平均因子回退。
- 自发自用化石能源电力返回 `DELEGATE_DIRECT_FUEL_PATH`，产生明确阻断问题并转交直接燃料排放路径，不进入外购电力间接排放参数路径。

### Sol 独立执行结果

- 组合场景：`.venv\Scripts\python.exe -m unittest tests.test_g05_multi_electricity.G05MultiElectricityTests.test_same_enterprise_resolves_three_details_independently -v`；1/1 通过。
- G05 定向：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules tests.test_g05_multi_electricity -v`；18/18 通过。
- G02/G04 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog -v`；31/31 通过。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；75/75 通过。
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库重建：`.venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\g05-sol-reacceptance-f080f11 --app-version 0.1.0`；catalog、user、records 均成功生成。随后对真实 `catalog.sqlite` 查询确认零因子所属参数、值、单位、来源、定位、年份、有效期和适用标准均正确；临时目录已清理。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`。
- 分层：`.venv\Scripts\python.exe -m unittest tests.test_g00_layout tests.test_g01_domain_dependencies -v`；3/3 通过。
- 审计说明：首次 SQLite 查询包装命令因 PowerShell 引号导致 Python `SyntaxError`，未形成产品测试结果；随后以相同重建数据库重新执行独立查询并通过，且完成清理。

### 范围和门禁

- 从产品决策提交 `23db8c9` 到被验收 HEAD 的业务变更仅涉及 Canonical、G05 Domain 与相关 G02/G04/G05 测试；未修改 UI、Application、迁移或 `计算表/`。
- 未发现 CAR-F01、CAR-P01～P04、CAR-I01～I04、企业电力排放总量、录入页增删或 G06 公式实现；G06 未创建、未执行。
- 验收结束时临时 PDF/数据库产物已清理，工作区仅有既有未跟踪 `docs/handoffs/`。

G05已通过，允许由用户另行启动G06；本次未启动G06。

## G04 本轮完成

- 新增 `packages/standards/catalog.py` 平台无关的标准、来源、对象、参数、因子读模型与只读 Repository 契约；没有引入 PySide6 或 SQLite 依赖。
- 新增 `packages/persistence/catalog_repository.py`，通过 SQLite `mode=ro` 读取 Canonical 构建的 `catalog.sqlite`，集中完成日期、Decimal、JSON 引用和 G01 领域枚举映射；缺失目录安全返回空结果。
- 新增 `packages/application/catalog_queries.py`，提供标准编号/名称/行业/年份/状态查询，按官方状态与实施/废止日期推导显示状态，组装标准详情和来源关系，并提供参数/因子按对象或来源的全局查询、类型/审核标签和来源追溯。
- 接入桌面应用配置、AppShell 和页面工厂；标准库和参数与排放因子库页面只通过 Application Query Service 读取数据，UI 没有直接打开数据库。
- `StandardLibraryPage` 提供搜索、状态/行业/年份筛选、标准详情、发布单位/主管部门/归口部门、基础标准关系、参数/因子关联和“查看标准原文”官方 URL 动作。只有当前 GB/T 32151.34—2024 的“按此标准核算”按钮可用；其他标准明确显示“核算模块待开发”并禁用入口。
- `ParameterFactorLibraryPage` 提供按对象/按来源视图、对象/来源/参数类型/审核状态/年份筛选、参数值详情、适用标准、来源定位、发布单位和“查看官方来源”动作；缺失官方 URL、缺失目录数据库或空详情字段均安全降级。
- G04 返工修复列表重建后的详情同步：每次搜索/筛选后显式渲染当前首项，旧详情控件先隐藏再销毁；标准详情号、官方 URL、参数详情和核算入口均绑定当前可见记录。
- G04 返工增加 `CatalogValueCategory`，按 Canonical 已有 `ValueType`/审核状态展示“推荐值（标准缺省）”“其他适用值”“历史值”及审核状态；这不是上下文驱动的计算场景推荐服务。
- 只展示 Canonical/SQLite 已有结构化数据；标准正文、PDF、企业数据、规则解析和动态推荐值未被制造或实现。G05 推荐解析、通用规则和计算快照仍未开始。

## G03 历史完成内容（已验收）

- 在 `packages/ui/` 建立可复用的 AppShell、页面路由、共享视觉令牌、平台无关视图模型和 SVG 导航图标加载器；应用层不直接查询数据库。
- 将应用接入固定 248 px 全高左侧导航、120 px 品牌区、顶部 Logo、底部设置入口和独立纵向滚动的主内容区；Logo 保持原比例，最大显示宽度 176 px。
- 建立首页专业工作台：温室气体排放核算标题与说明、开始卡片、最近核算记录空状态、最近使用标准安全空状态和底部辅助摘要；没有 KPI 大卡、图表或假数据。
- 建立首页、标准库、新建核算、Excel 导入、核算记录、参数与因子库、设置七个路由；首页快速入口与左侧导航进入同一路由。
- Excel 导入保留导航和占位页面，文件选择、标准选择、模板下载、下一步和导入等控件全部禁用、不可聚焦且未连接文件或计算动作。
- 标准库、核算、记录、参数与因子库和设置在 G03 交付时仅提供可达占位页；G04 查询已在本轮单独实现，G05 规则、G06 算法、G07 记录和导出仍未实现。
- 按 Sol 验收意见将首页 StartPanel 调整为“新建核算 → Excel 导入（暂未开放）→ 查看标准库”。
- 将 `BRAND_AREA_HEIGHT`、`SIDEBAR_ICON_ACTIVE` 和 `SIDEBAR_ICON_INACTIVE` 作为统一 Design Token 接入 Shell；界面代码不再重复写死品牌高度或导航图标白色。
- 新增两项针对性回归测试，分别锁定首页按钮顺序和 Shell 的 Token 使用；未改变 G03 之外的范围。

## G02 第二次返工内容（历史）

- 将 0.11 tCO₂/GJ 的参数与因子来源改为 GB/T 32150—2025 第7.5.6～7.5.7条，删除钢铁生产附件来源记录，避免把行业专项通知作为通则/炭素模块的共同来源。
- 同步修正热力参数与因子 source_id、source_location、factor_year=2025、valid_from=2026-07-01、适用标准范围和说明；保留标准缺省值语义。
- 测试改为验证标准来源、条款定位、年份、有效日期和双标准适用关系，不再断言钢铁附件。

## G02 首次返工内容（历史）

- Canonical schema、校验器和 catalog SQLite 迁移统一使用 G01 的 OfficialStatus、SourceType、ReviewStatus、ParameterType 和 ValueType 值集合；移除 OFFICIAL_NOTICE、SCIENTIFIC_REPORT、RETIRED、PENDING_REVIEW、OFFICIAL 和 DEFAULT 等旧字符串。
- 标准字段由含义不清的 status/authority 改为 official_status、issuing_authority（发布单位）、competent_authority（主管部门）和 technical_committee（归口部门），构建器与 SQLite 列保持一致。
- 按全国标准信息公共服务平台修正 GB/T 32151.7—2023、.8—2023、.13—2023 的名称；标准来源的 publisher 改为官方发布单位。
- 电力公告来源改为 GOVERNMENT_PUBLICATION，记录生态环境部、国家统计局联合发布机关。
- GB/T 32151.34—2024 只直接关联其附录 C 对应的 3 个天然气专属参数；其余 7 项计划标准仍无参数/排放源引用。
- （已由本轮第二次返工修正）此前曾将 0.11 tCO₂/GJ 指向生态环境部办公厅环办气候函〔2023〕332号附件4；该来源已移除，当前以 GB/T 32150—2025 第7.5.6～7.5.7条为准。

## G02 历史完成内容

### Canonical schema 与校验

- 新增 specs/common/canonical_catalog.schema.json，定义 manifest、sources、subjects、standards、parameters、factors 和 conversion_rules 的结构。
- schema 约束必填字段、未知字段、稳定 ID、枚举值、ISO 日期、官方 URI、Decimal 字符串、整数年份和数组唯一性。
- 新增 packages/reference_data/validation.py，使用标准库 JSON、DecimalPolicy 和 UnitService 执行结构校验、稳定 ID 唯一性、引用完整性、官方 HTTPS URL、单位白名单、数值类型和规范化换算校验。
- 新增 scripts/validate_canonical.py。Canonical 实际采用 JSON 载体；没有在未批准 loader/依赖的情况下静默解释 YAML。

### 首批 Canonical 数据

- 新增 data-source/carbon_accounting/catalog.json。
- 录入 9 个标准：GB/T 32150—2025、GB/T 32151.34—2024，以及 GB/T 32151.1—2015、.4—2026、.5—2026、.7—2023、.8—2023、.13—2023、.41—2024 的官方目录元数据。
- 7 项计划标准只保留官方来源、状态、日期、分类和 URL；没有参数引用、排放源引用、公式或计算规则。GB/T 32151.34—2024 仅关联 3 个标准专属天然气参数，不录入公式。
- 录入 12 条来源。标准官方页面分别来自 [全国标准信息公共服务平台](https://openstd.samr.gov.cn/bzgk/std/newGbInfo)，电力因子来源为 [生态环境部公告2025年第47号](https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202512/t20251231_1139517.html)，CO₂ GWP100 来源为 [IPCC AR6 WGI Chapter 7](https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/)，0.11 热力因子来源为 [GB/T 32150—2025 官方标准页面](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=6E4997D6B3118055931BC13C71B9A452)，条款定位见 Canonical source_location。
- 录入 6 个参数和 6 个因子：天然气 389.31 GJ/10⁴Nm³、0.0153 tC/GJ、0.99 ratio；2023 年全国电力平均因子 0.5306 tCO₂/MWh；热力缺省因子 0.11 tCO₂/GJ；CO₂ GWP100=1。
- 每个数值都保留 source_value/source_unit、normalized_value/normalized_unit、source_id、source_location、factor_year、有效期和 review_status；电力因子明确记录 kgCO₂/kWh 到 tCO₂/MWh 的等值换算。
- 标准全文、PDF 和标准原文没有复制到 Canonical Source 或构建产物。

### 三库迁移与目录构建

- 新增 migrations/catalog/001_initial.sql：catalog_manifest、source_documents、subject_catalog、standard_catalog、parameter_definitions、factor_values、factor_applicable_standards 和 conversion_rules。
- 新增 migrations/user/001_initial.sql：只包含 user_settings 及通用迁移/版本元数据。
- 新增 migrations/records/001_initial.sql：只包含 accounting_records、audit_log 及通用迁移/版本元数据。
- 新增 packages/persistence/sqlite.py：迁移文件按版本发现，未知数据库类型、非法迁移名、重复版本和版本名冲突会失败；迁移使用事务包裹。
- 新增 packages/persistence/catalog_builder.py：先校验 Canonical，再稳定排序、事务插入并原子替换 catalog.sqlite；删除生成库后可以从同一 Canonical 源重建相同逻辑数据。
- 新增 scripts/build_catalog.py 和 scripts/initialize_databases.py。
- 应用版本、schema 版本和 data 版本分开写入每个数据库；catalog 的 data_version 来自 manifest，user/records 使用 not_applicable。

## G02 历史 Scope 控制

- 没有修改 apps/ 或 packages/ui/，没有开始 G03 桌面外壳、首页、导航、Logo 或禁用入口。
- 没有实现 G04 查询页面、G05 规则解析、G06 计算公式、G07 记录闭环或 G08 Windows 交付。
- 没有录入完整 26 种燃料、碳酸盐过程参数、蒸汽焓值或完整 AR6 GWP 表；这些不属于本阶段最小数据集合。
- 没有生成并提交运行时 SQLite 文件；构建产物由 CLI 在指定目录按需创建。
- 计算表/ 下 7 个用户参考文件未修改、未纳入 Git。

## G02 历史测试与检查

### L1：G02 针对性测试

命令：

    .venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence -v

结果：21 个通过，0 个失败，0 个错误，0 个跳过。

覆盖：schema 类型/未知字段、重复稳定 ID、缺失来源、未知单位、浮点数、错误规范化值、G01 枚举集合对齐、标准职责与 2023 版名称、联合发布机关、GB/T 32151.34 专属参数、0.11 原始条款定位、YAML 禁止静默解析、官方 URL、计划标准无规则、三库职责隔离、全新创建、迁移幂等、用户设置保留、目录重建一致性和非法 Canonical 阻断。

### L2：全量回归

命令：

    $env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v

结果：39 个通过，0 个失败，0 个错误，0 个跳过（项目 .venv 为 Python 3.12.14，PySide6 6.11.2）。

备注：系统 Python 全量收集曾因未安装 PySide6 产生 1 个导入错误；按项目 pyproject.toml 使用 .venv 重跑后全量通过，系统环境错误不计为项目测试结果。

### L3：阶段收口

- .venv\Scripts\python.exe scripts\validate_canonical.py：成功，输出 9 standards、12 sources、6 parameters、6 factors。
- .venv\Scripts\python.exe scripts\build_catalog.py --source data-source\carbon_accounting\catalog.json --output tmp\g02-rework-validation.sqlite --app-version 0.1.0：成功，从 Canonical 重建 SQLite。
- .venv\Scripts\python.exe scripts\initialize_databases.py --output-dir 临时目录：成功生成 catalog.sqlite、user.sqlite、records.sqlite。
- .venv\Scripts\python.exe -m pip check：No broken requirements found.
- .venv\Scripts\python.exe -m compileall -q packages/core packages/reference_data packages/persistence tests scripts：成功。
- .venv\Scripts\python.exe -S：成功在无 site-packages 环境导入 Canonical loader 和 MigrationRunner，并验证 9 个标准、1 个 catalog 迁移。
- 分层扫描：packages/core 和 packages/reference_data 未发现 PySide6、sqlite3、win32、winreg 或 QSql。
- 标准全文字段扫描：data-source、specs、packages 未发现 full_text、standard_text 或 full_standard_text 字段。
- G03 越界扫描：本轮差异未包含 apps/ 或 packages/ui/ 文件。
- 生成物扫描：正式运行时数据库未提交；本轮 CLI 验证仅在 tmp\g02-rework-validation.sqlite 和 tmp\g02-rework-databases\ 下生成被忽略的临时 SQLite 产物。
- 用户文件 SHA256：7/7 与既有基线一致。
- 检查时间：2026-09-11。

## G03 测试与检查（历史）

### L1：G03 返工定向 GUI 测试

命令：

    $env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g03_shell -v

结果：8 个通过，0 个失败，0 个错误，0 个跳过。

覆盖：固定 Sidebar 宽度与导航顺序、设置底部锚定、首页标题/工作区/安全空状态、首页三个按钮固定顺序、七路由可达性、首页入口与左侧导航路由一致、Excel 页面全部控件禁用、Logo 比例与尺寸、主内容滚动策略、窗口最小尺寸和紧凑/宽屏边距，以及品牌高度和导航图标颜色使用 Design Token。

### L2：G03 返工与既有功能回归

命令：

    $env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v

结果：47 个通过，0 个失败，0 个错误，0 个跳过（项目 .venv 为 Python 3.12.14，PySide6 6.11.2）。

### L3：G03 阶段收口

- `.venv\Scripts\python.exe -m compileall -q apps packages tests scripts`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`。
- UI/资源探查成功：Logo 原图 3060×759，7 个 SVG 导航图标，应用 Shell 为 `AppShell`。
- G03 边界扫描未发现 `sqlite3`、`QSql`、`QFileDialog`、表格查询控件、报告/导出组件或其他后续业务实现。
- `计算表/` Git 差异为空；未修改用户参考文件。
- 在 G03 交付时 G04 未创建、未执行；该历史状态已由本轮 G04 单独 Goal 更新。G05/G06 业务仍未实施。
- 检查时间：2026-09-12。

## G04 首次交付测试与检查（历史）

### L1：G04 定向测试

命令：

    $env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g04_catalog -v

结果：8 个通过，0 个失败，0 个错误，0 个跳过；随后 Sol 交互验收发现详情同步和多版本分类缺口，已在返工中修复。

覆盖：标准编号/名称/行业/年份/官方状态与日期推导、标准详情和基础标准关系、发布单位/主管部门/归口部门展示、GB/T 32151.34—2024 可核算入口、其他标准“核算模块待开发”禁用入口、对象/来源查询、参数类型/审核状态/年份筛选、来源定位与发布单位、官方 URL 动作、内部稳定 ID 不直接展示，以及缺失目录/缺失官方 URL 的安全降级。

### L2：全量回归

命令：

    $env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v

结果：55 个通过，0 个失败，0 个错误，0 个跳过（项目 .venv 为 Python 3.12.14，PySide6 6.11.2）。

### L3：G04 阶段收口

- `.venv\Scripts\python.exe -m compileall -q apps packages tests scripts`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`。
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：成功，9 standards、12 sources、6 parameters、6 factors。
- `.venv\Scripts\python.exe scripts\build_catalog.py --source data-source\carbon_accounting\catalog.json --output tmp\g04-catalog-validation.sqlite --app-version 0.1.0`：成功从 Canonical 构建查询库。
- G04 边界扫描未发现 `QFileDialog`、`QSql`、`reportlab`、`matplotlib`、G05 或推荐解析入口；UI/应用层没有直接导入 `sqlite3`，SQLite 仅由 persistence 适配器以只读模式访问。
- `计算表/` Git 差异为空；未修改用户参考文件。
- 未启动系统浏览器验证外链，避免测试产生外部副作用；官方 URL 存在时按钮可用、缺失时按钮禁用，以及标准入口路由均由 Qt 定向测试覆盖。
- G05 未创建、未执行；未实施通用规则解析、参数推荐引擎、核算算法、记录闭环、报告/导出或 Windows 安装包。

## G04 Luna 首次交付状态（历史）

**READY_FOR_SOL_REACCEPTANCE**

- G05 通用规则、推荐值与快照基础已形成实现提交 `4419a73`；后续 Sol 正式验收结论为 FAIL。
- 当前工作区只保留既有未跟踪 `docs/handoffs/`；该目录未纳入本轮提交。
- 当前停止在 G04 验收点，等待 Sol 验收；未获 G04 PASS 前不得创建或执行 G05。

## 未执行项及原因

| 项目 | 状态 | 原因 |
|---|---|---|
| G05 通用规则解析、参数推荐和计算快照基础 | 未执行 | G04 当前等待 Sol 验收；未创建或执行 G05 Goal |
| 完整参数库和完整 GWP 表 | 未执行 | 本阶段只允许首批最小集合，后续补充需单独阶段/验收 |
| YAML loader | 未执行 | 当前 Canonical 选用 JSON；环境无已批准 YAML loader，避免静默引入解释差异 |
| 正式数据库运行产物 | 未提交 | SQLite 必须由 Canonical 构建脚本生成，测试使用临时目录 |
| Windows 安装包、企业真实数据和黄金算例 | 未执行 | HANDOFF 明确属于后续阶段或暂不实施范围 |

## Git

- 分支：main。
- 未使用破坏性 Git 操作。
- G02 原收口提交：e4d9b03 feat: establish G02 canonical data and database foundations。
- G02 返工实施提交：ba72f9a fix: address G02 catalog acceptance findings。
- G02 第二次返工实施提交：0cd6ed3 fix: correct G02 heat factor provenance。
- G03 实施提交：`617d982 feat: implement G03 desktop shell`。
- G03 小修提交：`aaefe29 fix: close G03 minor acceptance findings`。
- G04 实施提交：`4419a73 feat: implement G04 catalog query pages`。
- G04 返工实施提交：`00c7ea6 fix: close G04 catalog acceptance findings`。
- 保护范围：计算表/、.venv/ 和既有用户临时文件未修改；本轮只新增被忽略的 tmp 验证数据库，生成数据库不进入 Git。
- 工作区另有未跟踪 docs/handoffs/，非本轮新增或修改，未暂存。

## G02 Sol 正式验收结论（历史）

**结论：PASS**

- 验收日期：2026-09-11。
- 被验收实施基线：`78ff1f6`。
- G02 定向测试：21 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量回归：39 个通过，0 个失败，0 个错误，0 个跳过。
- Canonical 校验通过：9 个标准、12 个来源、6 个参数、6 个因子。
- `catalog.sqlite` 可由 Canonical Source 从零重建；`catalog.sqlite`、`user.sqlite`、`records.sqlite` 可独立初始化，表职责没有混放。
- 直接核对 GB/T 32150—2025 第7.5.6～7.5.7条以及 GB/T 32151.34—2024 第5.2.6.2、表C.3，确认 0.11 tCO₂/GJ 的来源和适用关系正确。
- Canonical schema、校验器、SQLite CHECK 与 G01 领域枚举一致；标准职责字段、三项 2023 版名称、电力公告联合发布机关和 GB/T 32151.34 专属参数关系符合已批准口径。
- 其余 7 项计划标准仍只有目录元数据，没有计算规则；没有提前实施 G03。
- 工作区原有未跟踪 `docs/handoffs/` 已有说明，不属于 G02，也未纳入验收提交。

G02 阶段门禁已解除，允许由用户另行启动 G03 Goal。

## G03 Sol 正式验收结论（初次）

**结论：PASS WITH MINOR FIXES**

- 验收日期：2026-09-12。
- 被验收实施基线：`05a67f4`。
- G03 定向测试：6 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量回归：45 个通过，0 个失败，0 个错误，0 个跳过。
- `compileall` 成功；`pip check` 输出 `No broken requirements found.`。
- 原生 Windows Qt 字体库正常识别 Microsoft YaHei UI；1180×720 和 1920×1080 首页截图未发现 Logo 变形、导航/内容重叠或横向滚动。
- 首页、标准库、新建核算、Excel 导入、核算记录、参数与因子库、设置七个路由均可到达；首页入口与侧栏进入相同路由。
- Excel 导入占位页内部的文件、标准、模板、下一步和导入控件全部禁用、不可聚焦且未连接业务动作。
- 空数据首页、最近记录和最近标准区域安全显示；没有接入 SQLite 查询、计算规则、报告/导出或 G04 查询功能。
- Windows Computer Use 辅助进程因运行环境沙箱初始化错误无法捕获窗口；已使用原生 Qt 窗口截图、控件状态探查及自动化 GUI 测试完成替代核验。该环境问题不计为项目失败。

### 必须修正的小问题

1. `HomePage` StartPanel 当前按“新建核算 → 查看标准库 → Excel 导入”创建按钮；公共框架规范第31节明确要求顺序严格固定为“新建核算 → Excel 导入（暂未开放）→ 查看标准库”。应调整按钮顺序，并在 `tests/test_g03_shell.py` 增加 StartPanel 顺序断言。
2. `packages/ui/shell.py` 仍直接使用 `#FFFFFF` 作为导航图标颜色，未完全遵守公共框架“颜色必须通过全局 Design Token”的要求；`brand_area.setFixedHeight(120)` 也应改用已有 `BRAND_AREA_HEIGHT`，避免公共尺寸在 Shell 中重复写死。

G04 未创建、未执行。G03 修正并重新验收为 PASS 前，阶段门禁保持关闭；修正完成后应发送“重新验收G03”。

## G03 小修交付状态（历史）

**状态：READY_FOR_SOL_REACCEPTANCE**

- 已修正首页三个按钮的冻结顺序：新建核算 → Excel 导入（暂未开放）→ 查看标准库。
- 已将导航图标激活/非激活颜色及品牌区高度统一收敛到 `packages/ui/design_tokens.py`，并删除 Shell 内对应硬编码。
- 返工定向测试 8/8、项目全量回归 47/47、compileall、pip check、G03 边界扫描、Shell 硬编码扫描和 `计算表/` 保护检查均通过。
- 小修交付时 G04 未创建、未执行，并停止等待用户发送“重新验收G03”。

## G03 Sol 正式重新验收结论

**结论：PASS**

- 验收日期：2026-09-12。
- 被验收 HEAD：`e57af51`；其中 G03 小修实施提交为 `aaefe29`。
- 首页 StartPanel 已按冻结规范调整为“新建核算 → Excel 导入（暂未开放）→ 查看标准库”，并新增顺序回归断言。
- Shell 已通过 `BRAND_AREA_HEIGHT`、`SIDEBAR_ICON_ACTIVE`、`SIDEBAR_ICON_INACTIVE` 使用统一 Design Token；验收指出的 `setFixedHeight(120)` 和 `#FFFFFF` 硬编码已从 Shell 移除。
- G03 定向测试命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g03_shell -v`；8 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量回归命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；47 个通过，0 个失败，0 个错误，0 个跳过。
- `.venv\Scripts\python.exe -m compileall -q apps packages tests scripts` 成功；`.venv\Scripts\python.exe -m pip check` 输出 `No broken requirements found.`。
- 七个路由均可到达且页面与路由分离；首页空数据展示安全，未查询数据库。Excel 占位页共有 6 个内部输入/选择/动作控件，全部禁用且不可聚焦，没有导入业务动作。
- 原生 Qt 1180×720 首页与 Excel 占位页视觉复核正常：导航和内容不重叠，Logo 为 176×43、约 4.09:1，无横向滚动；宽屏 1920×1080 布局规则由 GUI 自动化测试覆盖。
- Windows Computer Use 辅助进程经重试和重置后仍因 `windows sandbox failed: helper_unknown_error: setup refresh had errors` 无法连接；已使用原生 Qt 截图、控件状态探查及 GUI 自动化测试完成替代核验，该环境限制不影响项目结论。
- G03 范围扫描未发现 SQLite 查询、文件选择器、查询表格、报告/导出、计算公式或 G04 业务实现；`计算表/` Git 差异为空。
- 工作区只有既有未跟踪 `docs/handoffs/`，未纳入本次验收提交。

G03 已通过，允许由用户另行启动 G04；本次未启动 G04。

## G04 Sol 正式验收结论

**结论：FAIL**

- 验收日期：2026-09-12。
- 被验收 HEAD：`812af02`；其中 G04 业务实施提交为 `4419a73`。
- 定向测试命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g04_catalog -v`；8 个通过，0 个失败，0 个错误，0 个跳过。
- 全量回归命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；55 个通过，0 个失败，0 个错误，0 个跳过。
- Canonical 校验通过（9 standards、12 sources、6 parameters、6 factors），并成功从 Canonical Source 重建临时 `catalog.sqlite`；`compileall` 成功，`pip check` 输出 `No broken requirements found.`。
- 通过项：标准列表及三类筛选存在；9 项标准可查询；状态由官方状态和日期计算；只有 GB/T 32151.34—2024 的核算入口启用；参数/因子支持全局搜索、按对象、按来源和来源追溯；目录或可选 URL 缺失时具备基本安全降级；页面没有直接访问 SQLite；未提前实施 G05。
- 原始来源核对通过：本地 GB/T 32150—2025 第7.5.6～7.5.7条、GB/T 32151.34—2024 第5.2.6.2及表C.1/表C.3支持当前热力与天然气参数；全国标准信息公共服务平台支持标准名称、发布日期、实施日期和状态，生态环境部公告支持 2023 年电力因子的来源机关与公告信息。

### 未满足的 G04 验收项

1. 搜索/筛选后的列表、详情与官方 URL 没有可靠同步。验收级交互探查中，搜索 `32151.34` 后列表只剩 GB/T 32151.34—2024，但详情仍显示 GB/T 32150—2025，点击当前详情的“查看标准原文”传递的也是 32150 官方 URL；搜索“天然气”后列表为 3 项天然气参数，详情仍显示 CO₂ GWP。现有测试只检查行数、按钮启用和路由，没有断言筛选后详情对应当前列表记录，因此 8/8 通过未能发现该错误。这违反“搜索返回正确结果”“标准/参数详情”和“URL按钮状态及目标正确”的验收要求。
2. 未实现同一参数多版本的明确分类。当前读模型与 `CatalogQueryService.search_parameter_factors()` 只返回参数、因子、对象和来源，页面只显示 `ValueType` 与审核状态；没有产生或展示“推荐值、其他适用值、历史值”三类，也没有同一参数多版本并存的测试夹具与断言。这不满足 HANDOFF.md 的明确 MUST。

### Luna 修正要求

1. 修复两类页面的刷新逻辑：每次搜索或筛选重建列表后，应明确选择并渲染当前结果；结果为空时清空详情。官方链接和核算入口必须始终绑定当前可见详情，不能保留筛选前对象。
2. 增加回归测试，至少断言：标准搜索后列表标准号、详情标准号、官方 URL 三者一致；参数搜索后列表对象/参数与详情一致；筛选结果为空时详情清空。
3. 在不启动 G05 场景推荐引擎的前提下，按 G04 边界补齐同一参数多个版本并存的读取、分类和页面展示，明确区分推荐值、其他适用值、历史值及审核状态，并以至少一个多版本测试场景验证。若认为该 MUST 与 G05 边界无法兼容，应按 `BLOCKED` 格式提交给 Sol 决策，不得静默省略。
4. 不得修改 `计算表/`，不得开始 G05；修正后重新执行定向与全量测试，更新实施报告并等待重新验收。

- Windows Computer Use 辅助进程经规定的重试与重置后，仍因 `windows sandbox failed: helper_unknown_error: setup refresh had errors` 无法连接；本次使用原生 Qt 截图、控件状态探查和自动化 GUI 测试替代。该环境限制不是本次 FAIL 的原因。
- 验收临时数据库与截图已清理；工作区原有未跟踪 `docs/handoffs/` 未处理。

G04 未通过，不允许进入 G05。修正完成后应发送“重新验收G04”。

## G04 返工交付状态

**READY_FOR_SOL_REACCEPTANCE**

- 已修复搜索/筛选后的列表、详情与官方 URL 不同步：列表重建后显式渲染当前首项，旧详情控件先隐藏再销毁；标准号、参数名、官方 URL 和核算入口均通过当前详情对象绑定；结果为空时清空详情状态和详情控件。
- 已补齐同一参数多版本的来源元数据分类：`STANDARD_DEFAULT` 显示“推荐值（标准缺省）”，其他来源类型显示“其他适用值”，`HISTORICAL` 或已弃用值显示“历史值”，并同时显示审核状态；未实现上下文驱动的计算场景推荐。
- G04 返工定向测试：9 个通过，0 个失败，0 个错误，0 个跳过；覆盖标准/参数空结果时清空详情。
- G04 返工全量回归：56 个通过，0 个失败，0 个错误，0 个跳过。
- G04 返工 `compileall`、`pip check`、Canonical 校验、SQLite 重建、边界扫描和 `计算表/` 保护检查均通过。
- 返工实施提交：`00c7ea6 fix: close G04 catalog acceptance findings`；空结果回归测试提交：`56cdd60 test: cover G04 empty detail reset`。
- 当前工作区只保留原有未跟踪 `docs/handoffs/`，未纳入提交；G05 未创建或执行。
- 当前停止，等待 Sol 重新验收 G04。

## G04 Sol 正式重新验收结论

**结论：PASS**

- 验收日期：2026-09-12。
- 被验收 HEAD：`28dd8c9`；其中详情同步与多版本分类修复提交为 `00c7ea6`，空结果详情清空测试提交为 `56cdd60`。
- G04 定向测试命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g04_catalog -v`；9 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量回归命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；56 个通过，0 个失败，0 个错误，0 个跳过。
- `.venv\Scripts\python.exe scripts\validate_canonical.py` 通过，输出 9 standards、12 sources、6 parameters、6 factors；`catalog.sqlite` 已从 Canonical Source 在临时目录成功重建；`compileall` 成功；`pip check` 输出 `No broken requirements found.`。
- 首次 FAIL 缺陷 1 已关闭：验收级 Qt 探查确认搜索 `32151.34` 后列表标准号、详情标准号、详情按钮保存的 URL 和点击后实际传给 `QDesktopServices.openUrl` 的 URL 一致，均指向 GB/T 32151.34—2024；搜索“天然气”后列表与详情均为天然气参数；无结果时标准和参数页都会清空旧详情。
- 首次 FAIL 缺陷 2 已关闭：同一参数多版本能力可按 Canonical 已有 `ValueType` 和审核状态明确分类为“推荐值（标准缺省）”“其他适用值”“历史值”，页面同时显示审核状态，三版本测试场景已覆盖。该分类是来源元数据展示，不是 G05 的计算场景推荐解析。
- 标准原始来源复核没有失效：本次返工未修改 `data-source/`、迁移或 schema，也未改变标准状态、日期、网址、参数值、排放因子值及其来源；首次验收中对 GB/T 32150—2025、GB/T 32151.34—2024 原文和官方页面的逐项核对结论继续成立。
- G04 MUST 与验收条件全部满足：标准与参数/因子查询、筛选、详情、状态、官方 URL、唯一开放的 GB/T 32151.34 核算入口、多版本展示、安全降级及 Application Service/Repository 边界均通过检查。
- 范围检查通过：未发现 G05 场景推荐、计算快照或后续阶段实现；没有修改 `计算表/`，没有把标准全文或本地 PDF 打包进软件；原有未跟踪 `docs/handoffs/` 未处理。
- Windows Computer Use 辅助进程经重试和重置后仍因 `windows sandbox failed: helper_unknown_error: setup refresh had errors` 无法连接；本次采用 Qt 离屏控件探查、实际信号目标拦截和原生窗口截图完成替代核验。该运行环境限制不影响 PASS 结论。
- 验收临时数据库和截图在结论形成后清理，不纳入 Git。

G04已通过，允许由用户另行启动G05；本次未启动G05。

## G05 实施报告（2026-09-12）

### 目标与范围

本轮按 `HANDOFF.md` 仅执行 G05，目标是提供 GB/T 32150 通用规则解析、上下文驱动参数推荐、冲突处理、不可变参数快照和通用活动数据契约。没有制作 GB/T 32151.34 输入页面，没有实现 G06 公式、行业专属校验、正式记录持久化、UI 或 SQLite 运行时接入。

### 实现内容

- `packages/core/rules.py`：新增平台无关的 `EffectiveRuleResolver`、规则上下文、适用性、来源/证据状态和解析轨迹；实现 BASE、SPECIALIZE、OVERRIDE、EXTEND、SUPPLEMENT、CONFLICT_REVIEW。未解决的 `CONFLICT_REVIEW` 产生阻断性错误，显式覆盖保留覆盖/继承/冲突解决轨迹。
- `packages/core/parameter_resolution.py`：新增上下文驱动 `ParameterResolver` 和 `ParameterResolutionContext`，覆盖标准、核算期间、地区、行业、对象、参数类型、排放源、气体、电力类型/核算模式、框架、来源模式、实测值和证据上下文；支持行业明确值优先、官方最新值、实测优先/缺省回退、系统 GWP、歧义确认和确认理由。
- `packages/core/models.py`：补充因子年度/备注、活动数据来源等级以及快照的因子版本、来源定位和年度字段；枚举字段拒绝直接传入字符串。
- `packages/core/contracts.py`：新增数据来源证据、活动数据校验契约、来源等级约束、百分比/非负/单位/证据校验和通用 ADD/SUBTRACT/REPORT_ONLY 聚合契约。
- `packages/core/repositories.py` 与 `packages/core/__init__.py`：补充 `RuleRepository` 和 G05 Domain 公共导出。
- `tests/test_g05_rules.py`：使用内存 Parameter/Rule Repository 覆盖六类规则关系、优先级与冲突阻断，宁夏场景下全国电力因子推荐、热力实测与 0.11 回退、歧义确认、参数库更新后快照稳定性、活动数据/来源/聚合契约以及领域枚举字符串拒绝。

### 验证结果

L1 G05 定向测试：

    .venv\Scripts\python.exe -m unittest tests.test_g05_rules -v

结果：8 个通过，0 个失败，0 个错误，0 个跳过。

L2 项目全量回归：

    .venv\Scripts\python.exe -m unittest discover -s tests -t . -v

结果：64 个通过，0 个失败，0 个错误，0 个跳过（项目 `.venv`，Python 3.12.14）。

L3 检查：

- `.venv\Scripts\python.exe -m compileall -q packages apps tests`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`。
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：成功，9 standards、12 sources、6 parameters、6 factors。
- `.venv\Scripts\python.exe scripts\build_catalog.py --source data-source\carbon_accounting\catalog.json --output tmp\g05-catalog-validation.sqlite --app-version 0.1.0`：临时 SQLite 构建成功；Canonical 和迁移文件未修改。
- `git diff --check`：成功；`git diff --name-only -- 计算表/**`：为空。
- G05 Domain/测试禁入扫描未发现 `PySide6`、`sqlite3`、`QSql`、`QWidget`、`QFileDialog`、G06 公式或行业输入页实现。

### 未执行项及原因

- 未执行 G06，也未创建 G06 Goal；G05 不包含行业专属输入页、标准公式、结果持久化或 UI 接入。
- 未新增或修改 Canonical 数据、SQLite 迁移/Repository、计算表或正式运行数据库；G05 只通过内存 Repository 测试 Domain/Application 基础。
- pytest 未作为项目测试命令执行：环境未安装 pytest，项目 README 规定的 unittest 命令已完成定向与全量测试。

### Git 与交付状态

- 实施提交：`e815d50 feat: implement G05 rule resolution foundation`。
- 快照稳定性回归测试提交：`fefcd4d test: verify G05 snapshot stability`。
- 工作区仅保留既有未跟踪 `docs/handoffs/`，未纳入本轮提交；未使用破坏性 Git 操作。
- G05 已完成，当前停止等待 Sol 验收；G06 未创建、未执行。

## G05 Sol 正式验收结论

**结论：FAIL**

- 验收日期：2026-09-13。
- 被验收 HEAD：`cd880f2`；G05 实施提交为 `e815d50`，快照稳定性测试提交为 `fefcd4d`。
- 定向测试命令：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；8 个通过，0 个失败，0 个错误，0 个跳过。
- 全量回归命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；64 个通过，0 个失败，0 个错误，0 个跳过。
- `.venv\Scripts\python.exe -m compileall -q packages apps tests` 成功；`.venv\Scripts\python.exe -m pip check` 输出 `No broken requirements found.`。G05 Domain 不依赖 PySide6 或 SQLite；未修改 Canonical、迁移、UI、`计算表/`，未提前实施 G06。
- 原始标准已直接复核：GB/T 32150—2025 PDF 第13～17页明确活动数据高/中/低优先级、实测或测算因子优先于参考值、电力和热力实测优先、热力可用 0.11 tCO2/GJ、GWP 可参考 IPCC 数据。PDF SHA256 为 `673B85DF6EBEB6CE8894995534EC6EA3E2B7FA4F50B6A03AC0208E2DE34469BC`。冻结映射进一步明确官方电力因子更新后取最新值、规则 ID 命名空间和六类关系解析契约。

### 未满足的 G05 验收项

1. **默认运行规则集未实现冻结映射中的通用规则层和行业关系。** `default_g05_rules()` 只有 3 条通则参数选择规则与 5 条行业参数选择规则；缺少 `GEN-RULE-GHG-SCOPE-001`、`GEN-RULE-BOUNDARY-SYSTEMS-001`、`GEN-RULE-FUGITIVE-EXECUTION-BLOCK-001`、`GEN-RULE-TOTAL-COVERAGE-REQUIRED-001`、`GEN-RULE-TOTAL-001`、`CAR-RULE-TOTAL-001`、`CAR-RULE-FUGITIVE-COVERAGE-001` 等冻结映射规则，实际集合没有任何 `CONFLICT_REVIEW`。因此生产默认解析器无法执行已冻结的边界、总量、逸散冲突阻断及行业覆盖，只在合成测试中证明了通用算法存在。
2. **规则 ID 与冻结映射不一致。** `GEN-PAR-GWP-SYSTEM-001`、`CAR-PAR-NATURAL-GAS-LHV-SELECT`、`CAR-PAR-NATURAL-GAS-CARBON-SELECT`、`CAR-PAR-NATURAL-GAS-OXIDATION-SELECT`、`CAR-PAR-ELECTRICITY-NATIONAL-LATEST`、`CAR-PAR-HEAT-MEASURED-OR-DEFAULT` 均不存在于两份冻结映射；同时 `GEN-PAR-*` 在映射中是参数命名空间，却被作为 `RuleDefinition.rule_id` 使用。`GEN-PAR-GWP-SYSTEM-001` 还被标为 `STANDARD_EXPLICIT/VERIFIED`，但通则原文只允许 GWP 参考 IPCC 数据，冻结映射明确具体 GWP 版本管理属于软件参数结构，不能把未映射策略写成标准明确规则。
3. **“最新官方值”会选择旧的固定因子。** `_rank()` 对规则的 `required_factor_id` 增加 10000 分，远高于 `factor_year`。独立探查同时提供 2023 和 2024 全国官方电力因子时，生产 `OFFICIAL_LATEST` 仍选择 `electricity_national_average_2023`。这违反冻结映射“如更新采用最新数值”和炭素映射“不能把某年度值永久硬编码”的要求，也说明现有 8 项测试没有覆盖参数库更新后的推荐结果。
4. **未解决冲突仍能形成参数快照。** `ParameterResolver.resolve()` 的用户确认分支在 `effective.blocked` 时仍可设置 `recommended`，`ParameterResolution.to_snapshot()` 也不检查阻断错误。独立探查中未解决 `CONFLICT_REVIEW` 已产生 ERROR，但仍成功生成快照。这不满足“未解决的 CONFLICT_REVIEW 必须阻止成功核算”和“不可变快照只记录本次实际采用值”的门禁。
5. **`OVERRIDE` 不要求显式覆盖关系。** 当行业 `OVERRIDE` 没有声明 `supersedes_rule_ids` 时，解析器仍静默丢弃同组 BASE，结果既不阻断，也不把 BASE 记为已覆盖。冻结映射要求行业覆盖必须指向明确被覆盖规则并保留差异原因；现有测试只覆盖了声明正确的路径。

### Luna 修正要求

1. 以两份冻结映射为唯一规则来源，使用正确的规则/参数 ID 命名空间，补齐 G05 实际需要的 CommonRuleSet、IndustryRuleSet、来源定位和已确认冲突政策；不得发明 `STANDARD_EXPLICIT` 规则。若映射不足以转录某项，按 `BLOCKED` 上报，不得自行解释。
2. 修复 `OFFICIAL_LATEST`：先按标准、期间、地区、对象、来源类型等上下文过滤，再在有效官方候选中选择最新版本/年度；固定旧因子 ID 不得压过更新值，同优先级且无法唯一确定时要求用户确认并保存理由。
3. 阻止任何带 ERROR 的解析结果生成推荐快照；用户确认只能解决参数候选歧义，不能绕过未解决规则冲突。为“冲突 + 用户确认”“冲突结果调用 `to_snapshot()`”增加回归测试。
4. 强制 `OVERRIDE` 显式、有效地引用被覆盖规则；未声明、悬空或不完整的覆盖应阻断或保留未被覆盖的 BASE，且只有最终获选的覆盖规则可以解除对应冲突。增加缺失引用、悬空引用和多 BASE 部分覆盖测试。
5. 增加生产默认规则集测试，直接断言冻结映射要求的关键规则 ID、关系、来源和冲突路径存在；增加“2023 + 2024 官方因子必须选 2024”的参数库更新测试。重新执行定向测试、全量回归、分层和保护检查。

G05 未通过，不允许进入 G06。修正完成后应发送“重新验收G05”。

## G05 返工实施报告（2026-09-13）

### 目标与范围

本轮仅返工 HANDOFF.md 的 G05，针对 Sol 的 G05 FAIL 意见修正通用规则集合、参数推荐门禁和 OVERRIDE 解析。没有创建或执行 G06，没有修改 UI、Canonical 数据、SQLite 迁移、正式数据库、行业输入页面、行业计算公式或 `计算表/`。

### 修正内容

- `default_g05_rules()` 依据两份冻结映射重建为 35 条 CommonRuleSet 和 11 条 IndustryRuleSet；加入冻结的引用模式、温室气体范围、实体/系统/辅助/附属边界、纳入源、生物质/移除量、方法、公式、聚合、质量和报告规则。
- 默认集合包含 `GEN-RULE-FUGITIVE-EXECUTION-BLOCK-001`、`GEN-RULE-TOTAL-COVERAGE-REQUIRED-001`、`GEN-RULE-TOTAL-001` 及对应的实际 `CONFLICT_REVIEW` 路径；行业集合以 `CAR-RULE-TOTAL-001`、`CAR-RULE-TOTAL-COVERAGE-001` 和 `CAR-RULE-FUGITIVE-COVERAGE-001` 通过完整 `supersedes_rule_ids` 明确覆盖。
- 参数命名空间 `GEN-PAR-*` / `CAR-PAR-*` 不再被用作规则 ID；删除未在冻结映射中确认的 GWP 默认 `STANDARD_EXPLICIT` 规则。每条生产默认规则均保留 `source_location` 和 `evidence_source_id`，软件派生的阻断/覆盖策略标记为 `SOFTWARE_DERIVED` 并记录 `SM01-DECISION-001/005`。
- `OFFICIAL_LATEST` 不再因规则中的旧 `required_factor_id` 获得固定高分；适用标准、对象、参数类型、来源类型、有效期和其他上下文先过滤，再按官方年度选择最新候选；同优先级仍要求确认。
- `ParameterResolution.to_snapshot()` 对任何 ERROR 统一阻断；用户确认只解决参数候选歧义，不能绕过未解决的 `CONFLICT_REVIEW`。
- `OVERRIDE` 强制校验缺失、悬空和不完整的 `supersedes_rule_ids`。非法覆盖保留同组 BASE 并产生 ERROR；只有唯一且完整获选的覆盖规则能标记被覆盖规则并消解冲突。

### 测试与验证

- G05 定向：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；12 通过，0 失败，0 错误，0 跳过。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；68 通过，0 失败，0 错误，0 跳过（Python 3.12.14，PySide6 已安装）。
- 编译：`.venv\Scripts\python.exe -m compileall -q packages tests apps scripts`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；输出 `No broken requirements found.`。
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；通过，9 standards、12 sources、6 parameters、6 factors。
- SQLite：使用临时目录从 Canonical 从零重建 catalog、user、records 三库；结果为 `sqlite rebuild: PASS catalog, records, user`，未留下正式构建产物。
- 分层边界：`tests.test_g00_layout`、`tests.test_g01_domain_dependencies`、`tests.test_g02_persistence` 共 9 项通过；独立扫描确认 `packages/core` 无 PySide6、sqlite3、Windows API 依赖。
- 保护与差异：`git diff --check` 成功；`git diff --name-only -- '计算表/**'` 为空，`计算表/` 未修改。
- 未作为项目测试命令执行 pytest：当前环境未安装 pytest；项目 README 规定的 unittest 定向和全量测试已在项目 .venv 完成。系统 Python 3.11 的一次测试收集曾因缺少 PySide6 产生 3 个导入错误，该结果不计入验收，随后已用项目 Python 3.12 .venv 完成 68/68 全量回归。

### Git 与交付状态

- 返工实施提交：`549bca0 fix: rework G05 rule resolution acceptance findings`。
- 当前工作区在文档提交前仅有本轮两份文档修改和既有未跟踪 `docs/handoffs/`；`docs/handoffs/` 未处理、未暂存。
- G06 未创建、未执行；当前停止等待 Sol 发送“重新验收G05”。

## G05 Sol 正式重新验收结论

**结论：FAIL**

- 验收日期：2026-09-13。
- 被验收 HEAD：`c83df46`；G05 返工实现提交为 `549bca0`。
- 定向测试命令：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；12 个通过，0 个失败，0 个错误，0 个跳过。
- 全量回归命令：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；68 个通过，0 个失败，0 个错误，0 个跳过。
- 编译命令：`.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests`，成功。
- 依赖检查：`.venv\Scripts\python.exe -m pip check`，输出 `No broken requirements found.`。
- Canonical 校验：`.venv\Scripts\python.exe scripts\validate_canonical.py`，输出 `valid: 9 standards, 12 sources, 6 parameters, 6 factors`。
- 范围检查：返工差异只涉及 G05 Domain、G05 测试和交付文档；没有修改 Canonical、迁移、UI 或 `计算表/`，没有创建或执行 G06。工作区原有未跟踪 `docs/handoffs/` 未处理。

### 已确认通过的返工项

- `OFFICIAL_LATEST` 不再由固定的 2023 因子 ID 压过 2024 官方候选。
- 带 ERROR 的冲突解析结果不能再通过用户确认生成推荐或快照。
- 缺失、悬空或不完整的 `supersedes_rule_ids` 会阻断无效 `OVERRIDE`。
- 六类关系解析、参数候选确认、不可变快照、活动数据校验、聚合契约和 Domain 分层的现有测试全部通过。

### 未满足的 G05 MUST 与验收项

1. **冻结规则清单仍未完整转录。** 两份冻结映射明确包含 `GEN-RULE-ACTIVITY-PRIMARY-001` 和 `GEN-RULE-INDUSTRY-DELEGATION-001`，生产 `default_g05_rules()` 中均不存在。现有测试的 `expected_common.issubset(...)` 只检查部分 ID，无法发现缺项。
2. **行业规则关系与作用对象不正确。** 炭素冻结映射把 `CAR-RULE-NONFOSSIL-POWER-001` 定义为 `OVERRIDE`，生产实现却是 `BASE`。冻结映射把 `CAR-RULE-POWER-HEAT-001` 定义为对电力和热力两条通则的 `SPECIALIZE`，生产实现只绑定 `electricity_emission_factor_national` 与 `ELECTRICITY_EMISSION_FACTOR`，没有热力参数路径。
3. **通则来源定位存在系统性错位。** 直接读取 GB/T 32150—2025 原始 PDF 第13～17页确认：第 7.2.2、7.2.3、7.2.4 分别为排放因子法、物料平衡法、实测法；第 7.5.2～7.5.8 分别为燃料、过程、废弃物、逸散、购入电热、输出电热、总量。当前实现将 `GEN-MTH-MATERIAL-BALANCE-001`、`GEN-MTH-MEASURED-001`、`GEN-FML-FACTOR-001`、`GEN-FML-MATERIAL-BALANCE-001` 以及燃料/过程/废弃物/购入热力/输出电热公式定位到错误条款，甚至引用标准中不存在的第 7.5.9 和 7.5.10 条；`GEN-RULE-TOTAL-COVERAGE-REQUIRED-001` 还引用了通则中不存在的第 5.2.7 条。
4. **炭素电力热力规则来源定位错误。** GB/T 32151.34—2024 原始 PDF 第14～15页和冻结映射均明确购入与输出电力、热力属于第 5.2.6 条；第 5.2.7.1 条是直接排放总量。生产 `CAR-RULE-POWER-HEAT-001` 错误引用第 5.2.7.1 条。
5. 独立映射一致性探针对缺失规则、`CAR-RULE-NONFOSSIL-POWER-001` 的 `OVERRIDE`、行业热力覆盖及 11 组关键来源条款进行断言，命令退出码为 1。既有 12 项 G05 测试未覆盖这些差异，测试全绿不能替代标准与冻结映射核对。

### Luna 再次修正要求

1. 以两份 `FROZEN R5` 映射和原始标准为准，逐项建立“冻结 rule_id → 生产 RuleDefinition”的完整清单测试；补齐缺失规则，禁止只验证子集或用规则总数代替 ID 一致性。
2. 将 `CAR-RULE-NONFOSSIL-POWER-001` 按冻结映射实现为显式 `OVERRIDE`，并明确其覆盖目标；让 `CAR-RULE-POWER-HEAT-001` 同时覆盖电力与热力路径。若当前单个 `RuleDefinition` 无法表达两个目标，不得自行改变数据模型，应按 `BLOCKED` 请求 Sol 决策，或在不改变模型的前提下采用冻结映射允许的可追溯拆分方式。
3. 逐条修正所有生产规则的 `source_location`，并增加原文条款断言；不得把行业标准的第 5.2.7 条复制到通则，不得引用不存在的第 7.5.9、7.5.10 条。
4. 为上述缺失规则、关系、热力路径和来源定位补充失败先行的回归测试；重新执行 G05 定向、项目全量、编译、依赖、Canonical、分层、范围和 `计算表/` 保护检查。
5. 只返工 G05，不得创建或执行 G06。

G05 未通过，不允许进入 G06。修正完成后应发送“重新验收G05”。

## G05 第二次返工实施报告（2026-09-13）

### 目标与范围

本轮仅依据 Sol 对 G05 的再次验收意见返工 `HANDOFF.md` 的 G05 阶段。没有创建或执行 G06，没有修改 UI、Canonical 数据、SQLite 迁移、正式数据库、行业输入页、行业计算公式或 `计算表/`。

### 实现修正

- `default_g05_rules()` 现装载 37 条 CommonRuleSet 与 11 条 IndustryRuleSet；新增冻结缺失的 `GEN-RULE-ACTIVITY-PRIMARY-001` 和 `GEN-RULE-INDUSTRY-DELEGATION-001`。G05 测试改为对完整通用/行业 rule_id 集合做相等断言，不再使用子集断言或仅验证数量。
- `CAR-RULE-NONFOSSIL-POWER-001` 已按冻结映射改为显式 `OVERRIDE`，以 `supersedes_rule_ids=("GEN-RULE-ELECTRICITY-001",)` 保留可追溯覆盖关系；炭素电力因子路径仍可完成有效规则解析。
- `CAR-RULE-POWER-HEAT-001` 使用既有 `RuleDefinition` 的参数 ID、参数类型和 payload 同时关联电力与热力两条通则路径；参数解析器在覆盖/专门化规则不携带独立选值策略时，继续采用同一有效规则集中的显式参数选值策略，因此电力官方最新值和热力实测优先/0.11 缺省回退均保持成立。
- 逐项修正通则来源定位：`GEN-MTH-*` 为 7.2.2/7.2.3/7.2.4；燃料、过程、废弃物、逸散、购入电热、输出电热和总量公式为 7.5.2～7.5.8；购入电力与购入热力均为 7.5.6，输出电力与输出热力均为 7.5.7。`GEN-RULE-TOTAL-COVERAGE-REQUIRED-001` 改为 `SM01-DECISION-005` 与 7.5.8 追溯，不再引用通则不存在的第 5.2.7 条；生产规则不再含 7.5.9/7.5.10。`CAR-RULE-POWER-HEAT-001` 改为 GB/T 32151.34—2024 第 5.2.6 条。
- 回归测试新增完整 ID 清单、非化石 OVERRIDE 目标、电热参数 ID/类型与实际解析路径、全部关键来源条款和错误旧定位排除断言。

### 验证结果

- G05 定向：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；12 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量：`$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；68 个通过，0 个失败，0 个错误，0 个跳过（项目 Python 3.12.14，PySide6 6.11.2）。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；输出 `No broken requirements found.`。
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；输出 `valid: 9 standards, 12 sources, 6 parameters, 6 factors`。
- SQLite：`.venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\g05-second-rework-databases-final --app-version 0.1.0`；临时 catalog、user、records 三库均从 Canonical 从零创建成功，未生成正式运行数据库。
- 分层：`.venv\Scripts\python.exe -m unittest tests.test_g00_layout tests.test_g01_domain_dependencies tests.test_g02_persistence -v`；9 个通过，0 个失败，0 个错误，0 个跳过；`packages/core` 禁止依赖扫描无 PySide6、sqlite3、QSql、QWidget、QFileDialog。
- 范围/保护：`git diff --check` 成功；`git diff --name-only -- 计算表/**` 为空；Canonical、迁移、UI、`计算表/` 和 G06 均未修改或执行。
- 未执行 pytest：项目环境未安装 pytest，项目基线使用 unittest 完成定向与全量测试；未执行 G06、行业专属输入/计算、记录闭环、报告导出或安装包工作。

### Git 与交付状态

- G05 二次返工实现与测试提交：`9e74024 fix: complete G05 frozen rule mappings`。
- `TASK_STATE.md` 与本报告已更新记录本次返工和验证结果；既有未跟踪 `docs/handoffs/` 未处理、未暂存。
- 当前停止等待 Sol 再次验收；G06 未创建、未执行。

## G05 Sol 第二次正式重新验收结论

**结论：FAIL**

- 验收日期：2026-09-13。
- 被验收 HEAD：`1a7bd95`；第二次返工实现与测试提交为 `9e74024`。
- G05 定向测试：`.venv\Scripts\python.exe -m unittest tests.test_g05_rules -v`；12 个通过，0 个失败，0 个错误，0 个跳过。
- 项目全量回归：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；68 个通过，0 个失败，0 个错误，0 个跳过。
- 分层回归：`.venv\Scripts\python.exe -m unittest tests.test_g00_layout tests.test_g01_domain_dependencies tests.test_g02_persistence -v`；9 个通过，0 个失败，0 个错误，0 个跳过。
- `.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests` 成功；`.venv\Scripts\python.exe -m pip check` 输出 `No broken requirements found.`；Canonical 校验输出 `valid: 9 standards, 12 sources, 6 parameters, 6 factors`。
- 范围和保护检查通过：第二次返工只修改 `packages/core/parameter_resolution.py`、`tests/test_g05_rules.py` 和阶段文档；未修改 Canonical、迁移、UI、`计算表/`，未创建或执行 G06。工作区仅有既有未跟踪 `docs/handoffs/`。
- 原始来源复核：GB/T 32150—2025 SHA256 为 `673B85DF6EBEB6CE8894995534EC6EA3E2B7FA4F50B6A03AC0208E2DE34469BC`；GB/T 32151.34—2024 SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。直接读取了通则 PDF 第13～17页和炭素标准 PDF 第9～16、30页。

### 已确认关闭的上次问题

- 已补入 `GEN-RULE-ACTIVITY-PRIMARY-001` 与 `GEN-RULE-INDUSTRY-DELEGATION-001`。
- 通则方法、公式和聚合规则的第 7.2.2～7.2.4、第 7.5.2～7.5.8 定位已按原文纠正，不再引用第 7.5.9、7.5.10。
- `CAR-RULE-NONFOSSIL-POWER-001` 的关系枚举已由 `BASE` 改为 `OVERRIDE`；`CAR-RULE-POWER-HEAT-001` 已列出电力与热力参数 ID。

### 未满足的 G05 MUST 与验收项

1. **非化石电力规则无条件覆盖普通购电。** `CAR-RULE-NONFOSSIL-POWER-001` 的 applicability 只有标准与电力参数类型，没有 `electricity_type` 条件。`RuleApplicability.matches()` 也没有核对 `RuleContext.electricity_type`。独立探针分别传入 `ordinary_purchase` 和 `nonfossil`，两者均选中非化石规则、均覆盖 `GEN-RULE-ELECTRICITY-001`，有效规则集完全相同。
2. **非化石电力采用了错误取值政策。** 炭素标准附录 D.1.1 明确自发自用及市场化交易购入的非化石能源电力因子为零，D.2 要求合同、结算凭证/GEC 或月度原始记录；D.1.2 的“最新全国平均因子”用于不包括市场化交易非化石电量的其余电量。当前非化石 `OVERRIDE` 使用 `OFFICIAL_LATEST`，独立探针在非化石上下文无阻断地推荐全国平均因子 0.5306，没有零因子和证明门禁。该行为违反“行业标准明确值优先于通用更新值”和“未确认参数不得静默选择”。
3. **电热 SPECIALIZE 没有进入解析器关系图。** `CAR-RULE-POWER-HEAT-001` 的 group key 为 `parameter_selection:power_heat`，两条通则规则分别以具体参数 ID 分组；`EffectiveRuleResolver` 只在同一 group key 内处理 SPECIALIZE，且不读取 `payload('specializes', ...)`。热力探针显示通则热力规则轨迹为独立 `SELECTED`，不是 `INHERITED`；行业规则只作为另一组标记存在。新增的 `ParameterResolver`“选择首个带 policy 规则”只能绕过该关系缺口，不能证明 SPECIALIZE 生效。
4. **完整清单测试没有以冻结注册表为源。** FROZEN R5 通则注册表明确列出但生产与测试都缺少 `GEN-RULE-ACTIVITY-PROXY-001`、`GEN-RULE-ACTIVITY-SECONDARY-001`、`GEN-RULE-PRINCIPLE-001`、`GEN-RULE-SOURCE-CATALOG-001`、`GEN-RULE-WORKFLOW-001`；生产与测试却加入冻结注册表不存在的 `GEN-RULE-REPORT-001`。因此测试中的集合相等只证明代码等于测试手写集合，不证明等于冻结映射。
5. **行业规则来源仍有实质错位。** 冻结映射与原文要求 `CAR-RULE-PROCESS-001` 对应第 5.2.2～5.2.5 条，当前写成 5.2.3～5.2.6；`CAR-RULE-FUEL-001` 应追溯第 5.2.1 条及附录 C，当前混入非化石电力附录 D；`CAR-RULE-FUGITIVE-COVERAGE-001` 应追溯行业第 4.2、5.2 条及软件决策，当前仅写第 5.2.7.2 间接排放总量。
6. 现有测试把错误行为固化为通过条件：`electricity_type='ordinary_purchase'` 的测试明确断言结果应包含 `CAR-RULE-NONFOSSIL-POWER-001`，因此 12/12 和 68/68 全绿不能支持 PASS。

### Luna 第三次返工要求

1. 先区分普通购电与附录 D 非化石电力场景：普通购电不得命中非化石 `OVERRIDE`；非化石场景按 D.1.1 采用零因子且必须满足 D.2 证明门禁，不能回落为全国平均因子。分别增加普通购电、市场化绿电、自发自用绿电、缺少证明四类测试。
2. 如果上述修正需要新增 Canonical 参数/因子、改变 `RuleApplicability`/规则关系数据模型或解释冻结映射，必须按 AGENTS.md 使用 `BLOCKED` 请求 Sol 决策，不得继续用 payload 或测试断言模拟业务关系。
3. 让 `CAR-RULE-POWER-HEAT-001` 对 `GEN-RULE-ELECTRICITY-001` 与 `GEN-RULE-HEAT-001` 的 SPECIALIZE 真正被 `EffectiveRuleResolver` 解析并留下继承轨迹；禁止仅存 payload 标记。
4. 以冻结映射注册表生成或逐项核对 G05 应实施的完整 rule_id 清单。对处于 G06 的行业公式规则可以明确排除并记录理由，但不得把未登记 ID 当作冻结规则，通则 G05 规则不得无说明遗漏。
5. 纠正上述行业规则来源定位，并为每条关系、适用条件、选择政策与原文定位增加独立断言。只返工 G05，不得启动 G06。

G05 未通过，不允许进入 G06。修正完成后应发送“重新验收G05”。

## G05 第三次返工（2026-09-13）

### 目标与范围

本轮只处理 Sol 对 G05 第二次正式重新验收提出的六项问题，不创建或执行 G06。没有修改 UI、Canonical JSON、SQLite 迁移、正式数据库、行业输入页、行业计算公式或 计算表/。

### 已完成的安全修正

- 参数适用条件现在读取现有 RuleContext 的显式电力类型和核算模式。CAR-RULE-NONFOSSIL-POWER-001 只在 nonfossil、marketized_green、self_consumed_green 等非化石上下文生效；ordinary_purchase 不再被该 OVERRIDE 覆盖。
- 非化石路径改为 STANDARD_REQUIRED，并增加附录 D.2 证明门禁。解析器只接受值为 0、ValueType.STANDARD_SPECIFIED、带来源且定位到附录 D.1.1 的因子；缺证明或缺零因子均产生 GEN-VAL-NONFOSSIL-EVIDENCE ERROR，不会回退到全国平均 0.5306。
- EffectiveRuleResolver 使用已有 RuleDefinition.parameter_ids 将 CAR-RULE-POWER-HEAT-001 映射到电力和热力两个同域公共规则组，形成真实 SELECTED/INHERITED 轨迹；未读取 payload 来模拟关系。ParameterResolver 从有效继承轨迹取得公共选择策略。
- CommonRuleSet 补齐冻结注册表的 GEN-RULE-ACTIVITY-PROXY-001、GEN-RULE-ACTIVITY-SECONDARY-001、GEN-RULE-PRINCIPLE-001、GEN-RULE-SOURCE-CATALOG-001、GEN-RULE-WORKFLOW-001，并移除冻结注册表不存在的 GEN-RULE-REPORT-001。
- 纠正 CAR-RULE-FUEL-001 到第 5.2.1 条/附录 C、CAR-RULE-PROCESS-001 到第 5.2.2～5.2.5 条、CAR-RULE-FUGITIVE-COVERAGE-001 到行业第 4.2/5.2 条及 SM01-DECISION-001；测试增加关系、条件和来源定位的独立断言。
- 新增失败先行后的四场景回归：普通购电、市场化绿电、自发自用绿电、缺少证明；另验证有证明但没有 D.1.1 零因子时不会错误推荐全国平均因子。

### BLOCKED

问题：有 D.2 证明的市场化绿电或自发自用绿电必须推荐附录 D.1.1 的零因子，但当前 Canonical 因子库没有该有来源因子。

证据：磁盘校验 data-source/carbon_accounting/catalog.json 当前有 6 个因子，value 为 0 且 source_location 包含“附录D.1.1”的因子数量为 0。冻结行业映射同时规定 D.1.1 零因子和 D.2 证明文件。

为什么不能按原方案继续：在不新增 Canonical 因子的情况下，生产解析器只能安全阻断，不能在有证明时形成可追溯的 0 推荐。把 0 写进 payload、代码常量或只写入测试夹具会绕过 Canonical Source 规则，也违背 Sol 明确要求不得用 payload/测试断言模拟业务关系。

可选方案 A：Sol 批准新增一条 Canonical 因子/参数记录，明确稳定 ID、单位、版本、来源 ID、附录 D.1.1 定位和适用标准，然后继续接入和验收。

可选方案 B：Sol 批准将附录 D.1.1 的 0 表达为现有规则模型的标准直接值，并明确其来源快照表达方式；该决定仍需后续实现，不能由 Luna 自行解释。

建议：选择方案 A，使官方数值、来源和 SQLite 重建链路继续以 Canonical Source 为唯一事实源。

需要 Sol 决策的具体问题：是否批准按附录 D.1.1 新增一条 Canonical 零因子（包括稳定 ID、来源 ID、单位、版本和适用标准）？

### 测试

#### L1

命令：.venv\Scripts\python.exe -m unittest tests.test_g05_rules

结果：13 个通过，0 个失败，0 个错误，0 个跳过。覆盖四类非化石/普通购电场景、证明门禁、零因子来源门禁、双参数 SPECIALIZE 继承轨迹、冻结 ID、行业来源和既有 G05 契约。

#### L2

命令：.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'

结果：69 个通过，0 个失败，0 个错误，0 个跳过（项目 .venv，Python 3.12.14，PySide6 已安装）。

命令：.venv\Scripts\python.exe -m unittest tests.test_g00_layout tests.test_g01_domain_dependencies tests.test_g02_persistence

结果：9 个通过，0 个失败，0 个错误，0 个跳过。

#### L3

- .venv\Scripts\python.exe -m compileall -q packages apps tests scripts：成功。
- .venv\Scripts\python.exe -m pip check：No broken requirements found.
- .venv\Scripts\python.exe scripts\validate_canonical.py：通过，9 standards、12 sources、6 parameters、6 factors。
- .venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\g05-third-rework-databases --app-version 0.1.0：成功生成临时 catalog.sqlite、user.sqlite、records.sqlite。
- git diff --check：成功；git diff --name-only -- 计算表/**：为空。
- 系统 Python 的一次全量收集因缺少 PySide6 产生 3 个导入错误，未计入项目结果；随后使用项目 .venv 完成 69/69。
- pytest 未执行，原因是项目环境未安装 pytest；项目基线使用 unittest。
- G06 未创建、未执行；行业专属输入、行业计算公式、记录闭环、报告/导出和安装包均未执行。

### Git

- 代码/测试提交：4ac0e7f fix: harden G05 nonfossil rule resolution。
- 本报告与 TASK_STATE.md 为本轮状态收口文档，既有未跟踪 docs/handoffs/ 未处理、未暂存、未纳入提交。
- 当前工作区只保留本轮两份文档修改及既有 docs/handoffs/；等待 Sol 决策，不启动 G06。

## G06 实施报告（Sol R6 决策后，2026-09-13）

### 阶段与结论

本轮完成 HANDOFF.md G06：GB/T 32151.34—2024 手工录入、专业校验、高精度计算、逐条电力解析、结果展示与内存记录验证。Sol 已批准的 TV-CAR-FML-008 R6 映射测试向量纠错已纳入回归；当前状态为 G06_READY_FOR_SOL_ACCEPTANCE，停止等待 Sol 验收，不开始 G07。

### 本轮完成

- 保留正式标准式（8）的实现，不新增 GTA×GTAVar×K3×44/16 项。R6 映射向量 TV-CAR-FML-008 的预期值为 1.439166666... tCO2。
- 外部映射升为 SM01-2026-09-13-R6，并在第19节记录为映射测试向量纠错；映射状态重新为 FROZEN。本次未标记为标准勘误或 CONFIRMED_CORRECTION。
- G06 Domain 完成十类排放源的高精度计算、单位/适用性/证明和边界校验、默认值警告与快照、C.4/C.5 蒸汽焓值查表和插值，以及产出扣减。G06 不依赖 PySide6、SQLite 或 Windows API。
- 多电力明细按取得方式和电力属性两个独立维度逐条解析；每条明细独立选择因子、校验证明并生成参数快照。外购常规电力使用最新全国平均因子，非化石证明缺失产生 ERROR 且不回退，自发自用化石能源电力只形成直接燃料路径转交阻断，不进入外购电力间接排放路径。
- Application/UI 只负责输入装配、调用 Domain 和展示结果；记录验证使用内存 Record Repository，未实现正式记录持久化、报告/导出或 G07。

### 修改文件

- packages/standards/carbon_material.py
- packages/application/carbon_accounting.py
- packages/ui/carbon_material_page.py
- packages/ui/pages.py
- packages/ui/shell.py
- tests/test_g06_carbon_material.py
- tests/test_g06_page.py

### 验证

#### L1

命令：.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v

结果：20 个通过，0 个失败，0 个错误，0 个跳过。

#### L2

命令：.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v

结果：49 个通过，0 个失败，0 个错误，0 个跳过。

#### L3

- .venv\Scripts\python.exe -m unittest discover -s tests -t . -v：95 个通过，0 个失败，0 个错误，0 个跳过。
- .venv\Scripts\python.exe -m compileall -q packages apps tests：成功。
- .venv\Scripts\python.exe -m pip check：No broken requirements found.
- .venv\Scripts\python.exe scripts\validate_canonical.py：通过，9 standards、12 sources、7 parameters、7 factors。
- .venv\Scripts\python.exe scripts\initialize_databases.py --source data-source\carbon_accounting\catalog.json --output-dir tmp\g06-final-three-databases --app-version 0.1.0：成功生成 catalog.sqlite、user.sqlite、records.sqlite，临时目录已清理。
- git diff --check 通过；git diff --name-only -- 计算表/** 为空；既有 docs/handoffs/ 保留且未处理。
- pytest 未执行，原因是项目测试基线为 unittest。

### Git 与等待状态

- G06 实现提交：bc1f83c feat: implement G06 carbon material calculation。
- R6 测试向量旧值/新值差异证据提交：4d52b32 test: preserve G06 R6 vector correction evidence。
- 外部映射文件不在项目 Git 中；本报告记录其变更前 SHA256 8BC09741DC6E34E4A14D8801D776760BE56336B5499E4B1FFA2F9FDC0E997DD4 和变更后 SHA256 D3023387B04BF20ECF2D9F6CECF1F816EACF995C1C4B0A57AED8D72F7E519F26。
- 工作区提交文档后仅保留既有未跟踪 docs/handoffs/；本报告与 TASK_STATE.md 更新后停止等待 Sol 验收，绝不启动 G07。

## G06 Sol 正式验收结论（2026-09-13）

### 结论

**FAIL**

被验收 HEAD 为 `16e47722e5dfeaf34025460b90c659c260967ee5`。R6 测试向量纠错、Domain 计算和现有回归测试通过，但 G06 的手工录入页面及冻结映射校验契约仍有多项 MUST 未完成，不能进入 G07。

### 已通过核对

- 直接读取原始 GB/T 32151.34—2024 PDF；文件 SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。式（1）～式（16）与当前 Domain 主公式一致；式（8）独立复算为 `1.439166666666666666666666667 tCO2`，R6 修正正确且实现未加入被禁止的 GTA 挥发分项。
- Domain 已覆盖十类排放源的正常、零值、缺失、非法比例、单位不匹配和不涉及工程路径，完成直接/间接/总量聚合、默认值快照、蒸汽焓值查表/内插及错误阻断。
- 同一企业、同一核算期的外购常规、外购非化石和自发自用非化石电力可以逐条解析、计算、快照并汇总；证明缺失不回退全国平均因子；自发自用化石电力可转交燃料直接排放路径并避免进入购电间接排放。
- 计算公式位于 Domain，UI 未包含公式；正式记录 SQLite、报告/导出、安装包和 G07 均未提前实施。`计算表/` 无差异。

### 未满足的验收项及证据

1. **CAR-I03/CAR-I04 无法从手工页面录入。** `packages/ui/carbon_material_page.py:242-249` 只建立燃料、过程、I01 电力和 I02 热力区；`_input()` 到 `packages/ui/carbon_material_page.py:445` 只传 `purchased_heat`，没有传 `exported_electricity`、`exported_heat`。独立页面探针确认两者恒为空，除“是否涉及”下拉框外没有输出电力/热力控件。Domain 测试直接构造对象不能替代页面 MUST。
2. **企业名称必填被静默绕过。** `packages/ui/carbon_material_page.py:428` 将空输入替换为“未填写企业”，导致未填写真实名称也可形成成功内存记录。应让空名称产生明确 ERROR，不能制造占位企业名称。
3. **参数选择器及来源/选择状态未实现。** HANDOFF 要求参数选择器接入 G05 并显示来源和选择状态；当前参数区仅有说明和快照计数，热力因子仍是自由文本框。独立页面探针未发现参数或因子选择控件。应通过 Application Service 暴露候选/推荐、来源、审核状态和选择理由，并保持 UI 不实现选择算法。
4. **式（6）～式（8）的基准元数据未进入页面。** Domain 有 `mass_basis`、`composition_basis`、`normalized_basis`、`component_kind` 和换算证据，但页面无对应输入/确认，构造时一律采用默认收到基/固定碳，未知、基准不一致和干燥基未换算无法从手工路径触发冻结映射第 8.1 节校验。
5. **行业冻结校验 ID 未完整实现。** 映射注册的是 `CAR-VAL-GREEN-ELECTRICITY-EVIDENCE`；当前只透传 `GEN-VAL-NONFOSSIL-EVIDENCE`，前一 ID 在 `packages/` 与 `tests/` 均不存在。应保留 G05 通用问题的来源，同时在 G06 形成冻结的行业校验 ID，或由 Sol 先批准映射 ID 变更；Luna 不得自行改口径。
6. **现有测试未覆盖上述缺口。** `tests/test_g06_page.py` 没有 I03/I04 页面输入、空企业名称、参数选择/来源展示、材料基准元数据和行业校验 ID 的断言，故测试全绿不足以判定阶段通过。

### R6 修正清单复核

- 外部映射磁盘原始 SHA256 确认为 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`（62019 字节、LF）；原报告的 `D3023387B04BF20ECF2D9F6CECF1F816EACF995C1C4B0A57AED8D72F7E519F26` 经独立内存转换确认是 CRLF 规范化哈希。原记录确有口径说明缺失。
- R5 没有历史归档；当前历史目录只有 R4。R6 签署区仍为 2026-09-11 旧签署，且 `TASK_STATE.md` 存在两份相同的历史 G06 BLOCKED 块。
- 这些是证据链和文档整理问题，不改变 R6 数值正确性；由于本次业务验收为 FAIL，未更新外部映射签署、未归档或改动 Git 外文件，也未清理历史块。返工时应补充准确哈希口径；R6 正式签署应留待 G06 重新验收通过后处理。

### 独立测试结果

- G06 定向：`.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`；20/20 通过。
- G02/G04/G05 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`；49/49 通过。
- 项目全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；95/95 通过。
- `.venv\Scripts\python.exe -m compileall -q packages apps tests`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功，验收临时目录 `tmp/sol-g06-acceptance-20260913` 已清理。

### 阶段门禁

G06 未通过，不允许进入 G07。本次只记录验收结论，没有修改业务代码、外部映射或 `计算表/`，也没有创建或执行 G07。修正完成后应发送“重新验收G06”。

## G06 页面返工实施报告（2026-09-14）

### 阶段与范围

本轮只处理 Sol 正式验收指出的 G06 页面缺口、冻结行业校验码和对应回归测试；保留 R6 式（8）口径，不开始 G07，不修改 `计算表/`，不处理既有 `docs/handoffs/`。

### 实现

- 在 `packages/ui/carbon_material_page.py` 增加 I03 输出电力、I04 输出热力/动力控件，并把输出明细接入 `CarbonMaterialInput`，页面输入可完成式（15）的输出扣减路径。
- 企业名称为空时在计算入口直接产生 `GEN-VAL-REQUIRED-MISSING`，不生成“未填写企业”占位名称，不形成记录。
- 通过 `CatalogQueryService` 的只读目录接口接入真实 G05 参数解析器和热力因子选择器。页面展示推荐/其他适用/历史分类、来源 ID、审核状态、来源定位、值/单位和选择理由；人工选择非推荐候选必须保存理由，实际选择值会携带来源/版本/因子 ID进入 Domain。
- 为煅烧、焙烧/炭化、石墨化增加物料基准、成分性质、归一化基准及水分/换算证明入口，默认“未确认”以阻止静默采用收到基/固定碳；缺失非收到基证明时保留 Domain 的 `CAR-VAL-MATERIAL-BASIS-CONVERSION` 阻断。
- 在 G06 电力结果路径将通用非化石证明问题映射为冻结码 `CAR-VAL-GREEN-ELECTRICITY-EVIDENCE`，并由回归测试固定验证；没有通过中文 `source_location` 识别因子。
- `CatalogQueryService` 新增只读 `repository` 和按参数列出因子的接口，未改变 schema、迁移或 SQLite 职责。

### 修改文件

- `packages/application/catalog_queries.py`
- `packages/standards/carbon_material.py`
- `packages/ui/carbon_material_page.py`
- `tests/test_g06_carbon_material.py`
- `tests/test_g06_page.py`

### 验证

#### L1

命令：`.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`

结果：24/24 通过，0 个失败，0 个错误。

#### L2

命令：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`

结果：49/49 通过，0 个失败，0 个错误。

#### L3

- `.venv\Scripts\python.exe -m unittest discover -s tests -v`：99/99 通过，0 个失败，0 个错误。
- `.venv\Scripts\python.exe -m compileall -q packages apps tests scripts apps`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- `.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir tmp\g06-final-dbcheck\databases --app-version g06-rework-check`：catalog.sqlite、user.sqlite、records.sqlite 从零生成成功，临时目录已清理。
- `git diff --check` 通过；`git diff --name-only -- 计算表/**` 为空；pytest 未执行，项目测试基线为 unittest。

### R6 哈希证据

当前外部映射文件原始 LF SHA256 为 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`（62019 字节）。既有报告中的 `D3023387B04BF20ECF2D9F6CECF1F816EACF995C1C4B0A57AED8D72F7E519F26` 是相同内容的 CRLF 规范化哈希；本轮只整理证据，没有修改项目 Git 外的映射文件。

### Git 与等待状态

实现提交：`5d26d20 fix: close G06 page acceptance gaps`。

文档提交完成后停止等待 Sol 重新验收，不启动 G07。

## G06 Sol 正式重新验收结论（2026-09-16）

### 结论

**FAIL**

被验收 HEAD 为 `ea4ff2eb3acb9c5d8c299ce7a09377dbad48ba9a`。首次验收指出的 I03/I04、企业名称必填、热力参数选择器、材料基准默认值和行业绿电校验码已修复；但独立核查仍发现三项 G06 MUST 没有通过完整的手工录入链闭环，因此不能进入 G07。

### 已通过核对

- 原始 GB/T 32151.34—2024 PDF 的 SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。物理第13页式（8）与 R6 的 `TV-CAR-FML-008=1.439166666666666666666666667` 一致；物理第30页（印刷页22）D.1.1、D.1.2、D.2 与电力零因子及证明门禁一致。
- 外部冻结映射版本为 `SM01-2026-09-13-R6`，原始 LF SHA256 为 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`。
- I03/I04 可从页面传入计算；空企业名称被阻断且不生成记录；热力因子候选、来源、审核状态和理由可以显示；材料基准默认未确认；非化石证明缺失使用 `CAR-VAL-GREEN-ELECTRICITY-EVIDENCE`。
- 公式仍位于 Domain，未发现 Domain 依赖 PySide6、SQLite 或 Windows API；未提前实现 G07、报告导出或正式记录持久化。

### 未满足项及修正要求

1. `CalcinationInput`、`BakingInput`、`GraphitizationInput` 各只有一个 `component_kind`，页面也各只有一个选择器，但每个公式同时包含固定碳字段和挥发分字段。当前校验只确认单值属于 `FIXED_CARBON` 或 `VOLATILE_MATTER`，没有执行冻结映射“固定碳字段只能固定碳、挥发分字段只能挥发分”的绑定。应为两类字段分别表达不可混淆的成分性质（或采用等价的逐字段语义模型），错误类型必须产生 `CAR-VAL-MATERIAL-COMPONENT-KIND`，并覆盖 P01/P02/P03 测试。
2. 每条电力明细没有显示其独立因子、来源、审核/选择状态和选择理由；当前新增参数区只解决热力因子。应让普通购电、外购非化石和自发自用非化石三条同时存在时，各自显示后台解析出的因子/来源/状态/理由并保持独立快照，增加不相互覆盖的页面测试。
3. 页面没有“存在其他行业活动”和“存在上下游运输”的声明入口，`_input()` 不能把这两个标志传给 Domain，用户无法触发 `CAR-VAL-OTHER-STANDARD`。应增加明确手工入口、阻断提示和不计入结果/不生成成功记录的测试。

### 独立验证结果

- `.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`：24/24 通过。
- `.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`：49/49 通过。
- `.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`：99/99 通过。
- `.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功；验收临时数据库与 PDF 渲染目录均已清理。
- 独立探针确认：P01 同一输入选择两种单一成分性质均不报字段组错误；电力明细没有参数状态控件；其他行业活动和运输没有页面控件。

### 阶段门禁

本次只记录验收结论，没有修改业务代码、冻结映射或 `计算表/`，未处理既有未跟踪 `docs/handoffs/`，未创建或执行 G07。G06 未通过，不允许进入 G07；修正完成后应发送“重新验收G06”。

## G06 页面缺口返工实施报告（2026-09-16）

### 范围

本轮仅修正 Sol 重新验收列出的三项 G06 阻断问题：P01/P02/P03 固定碳与挥发分字段口径分离、每条电力明细参数状态展示、其他行业活动与上下游运输手工声明。未改变 R6 式（8）口径、Canonical 数据、数据库 schema/迁移或 G05 规则；未制作 G07 页面或计算模块，未修改“计算表/”，未处理既有 `docs/handoffs/`。

### 实现

- `packages/standards/carbon_material.py` 为煅烧、焙烧/炭化、石墨化输入增加 `fixed_carbon_component_kind` 与 `volatile_matter_component_kind`；`_basis()` 按字段组分别验证，错误分别定位到 `.fixed-carbon` 或 `.volatile-matter`，统一使用 `CAR-VAL-MATERIAL-COMPONENT-KIND`。
- `packages/ui/carbon_material_page.py` 将每个过程的共享选择器替换为“固定碳字段性质”和“挥发分字段性质”两个选择器，并把两者独立装配进 Domain 输入。
- 电力明细行增加参数状态、采用因子、来源/审核状态和选择理由四个只读展示区；每次明细编辑后调用 G05 逐条解析，按 `detail_id` 回填对应行。已采用结果展示真实稳定因子 ID、值/单位、来源定位、审核状态和选择理由；证明阻断及自发自用化石路径也显示独立状态，不生成伪快照。
- 核算边界增加其他行业活动和上下游运输两个复选声明，并传入已有 Domain 阻断字段；任一声明后产生 `CAR-VAL-OTHER-STANDARD`，不形成成功结果。
- 新增领域回归 `test_fixed_and_volatile_component_kinds_are_validated_independently`；新增页面回归覆盖三种同时存在的电力明细、逐行因子/来源/状态/理由、两项边界声明和两类错误成分口径。

### 验证结果

- G06 定向：`.venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`；28/28 通过。
- G02/G04/G05 回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`；49/49 通过。
- 全量回归：`.venv\Scripts\python.exe -m unittest discover -s tests -v`；103/103 通过。
- `.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`；成功。
- `.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- `.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir <临时目录>`；三库从零生成成功，临时目录已清理。
- `git diff --check` 通过；`计算表/` 无差异；pytest 未执行，因为项目测试基线为 unittest。

### 提交与等待

- 实现与测试提交：`55bdd1b fix: close remaining G06 page validation gaps`；P01/P02/P03 成分字段回归补强提交：`345b023 test: cover G06 component kinds across process groups`；构造兼容修正提交：`bcb6307 fix: preserve G06 input constructor compatibility`。
- 文档更新后工作区只保留既有未跟踪 `docs/handoffs/`；本轮未创建或执行 G07。
- 本轮完成后停止等待 Sol 重新验收。

## G06 Sol 最终正式重新验收结论（2026-09-16）

### 结论

**PASS**

被验收 HEAD 为 `c2ca02e5453e4b597cc73647f3ae6cba0d2b1842`。上次 FAIL 的三项剩余缺口均已按冻结映射和 HANDOFF 的 G06 MUST 关闭；本轮未发现新的阻断项或下一阶段越界。

### 关键核对事项

- P01/P02/P03 已将固定碳字段和挥发分字段的成分性质分开表达、分开校验；错误分别定位到对应字段组并使用稳定码 `CAR-VAL-MATERIAL-COMPONENT-KIND`。兼容构造路径没有放宽新页面的显式校验。
- 外购常规、外购非化石、自发自用非化石三条电力明细可同时存在，每行显示自己的因子 ID、值/单位、来源定位、审核/选择状态和理由；页面展示来自 G05 逐条解析结果，Domain 快照互不覆盖。
- 其他行业活动和上下游运输具有明确页面声明入口，传入 Domain 后使用 `CAR-VAL-OTHER-STANDARD` 阻断，不形成成功结果或记录。
- 原始 GB/T 32151.34—2024 PDF SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。物理第13页式（8）不包含 GTA 挥发分项；物理第30页（印刷页22）D.1.1、D.1.2、D.2 支持当前普通电力、非化石零因子和证明规则。
- 冻结映射为 `SM01-2026-09-13-R6`，原始 LF SHA256 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`；R6 测试向量及本轮三个关键规则均与实现一致。
- 十类排放源、直接/间接/总量聚合、Decimal 精度、默认值提示和快照、蒸汽焓值、多电力证明门禁、防重复、I03/I04 抵扣、企业名称必填、内存记录以及 UI/Domain 分层均通过既有测试和本次复核。

### 独立测试结果

- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page -v`：28/28 通过，0 失败，0 错误，0 跳过。
- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_rules tests.test_g05_multi_electricity -v`：49/49 通过，0 失败，0 错误，0 跳过。
- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`：103/103 通过，0 失败，0 错误，0 跳过。
- `.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从 Canonical Source 重建成功；临时数据库和 PDF 渲染目录均已清理。

### Git、范围与门禁

验收开始前工作区只有既有未跟踪 `docs/handoffs/`。本次只修改验收文档，不修改业务代码、冻结映射或 `计算表/`，未创建或执行 G07。

G06已通过，允许由用户另行启动G07；本次未启动G07。

## G07 实施报告（2026-09-19）

### 阶段

G07 核算记录与审计闭环。

### 本轮完成

- 按 HANDOFF.md 仅实施 G07；G08 未创建、未执行。
- 计算器成功路径生成唯一记录 ID，并将完整 G06 原始输入通过 records 仓储保存；ERROR 路径不生成成功记录。
- 新增 `migrations/records/002_g07_record_lifecycle.sql`，在不修改 001 初始迁移的前提下增加原始输入快照、有效规则集快照、软删除字段和索引。
- 新增 `SQLiteRecordRepository`：记录与全部 JSON 快照、CREATE 审计在同一 `BEGIN IMMEDIATE` 事务中写入；任一写入失败回滚；读取返回不可变 Domain 对象。
- 有效规则快照保存实际解析到的稳定规则 ID以及参数快照 ID；原始输入快照保存完整 G06 输入对象的 JSON 表示；参数快照保留值、单位、因子、来源、版本、定位、选择方式和理由。
- 支持 `COMPLETED`、`COMPLETED_WITH_WARNINGS`；连续相同输入成功计算生成不同记录 ID；历史记录从不更新覆盖。
- 软删除只更新删除标记并追加 DELETE 审计，默认 `list_all()`/`get()` 隐藏已删除记录，记录 ID 不可复用，审计证据保留。
- 应用正式入口解析用户数据目录 `records.sqlite`；测试和显式无 records 配置使用隔离内存仓储，保持 G06 既有测试边界。
- 新增核算记录台账页面：按企业/记录/标准搜索、按状态筛选、只读详情；详情展示核算身份、标准/算法、来源判断、有效规则、结果分项、参数来源快照、输入快照字段和警告。
- 首页最近核算记录从同一 records 仓储读取；成功生成记录后 Shell 刷新首页和台账。
- 新建核算页面增加未计算输入离开确认；选择丢弃后清理当前输入，不生成记录；删除操作要求二次确认并写审计。

### 未完成

- 无 G07 MUST 未完成。
- Sol 正式验收尚未进行；当前停止等待验收。
- G08、报告/导出、基于记录重新核算、恢复已删除记录 UI、历史记录编辑均未实施，符合 G07 OUT OF SCOPE。

### 与 HANDOFF 的偏差

- 无。未修改 `计算表/`，未处理既有 `docs/handoffs/`，未改变 G06 公式、Canonical 数据或既有 schema_version；仅新增 records 数据库 002 迁移以实现 G07 生命周期。

### 修改文件

- `apps/carbon_accounting_desktop/app.py`
- `apps/carbon_accounting_desktop/config.py`
- `apps/carbon_accounting_desktop/product.py`
- `migrations/records/002_g07_record_lifecycle.sql`
- `packages/core/__init__.py`
- `packages/core/repositories.py`
- `packages/persistence/__init__.py`
- `packages/persistence/records_repository.py`
- `packages/standards/carbon_material.py`
- `packages/ui/carbon_material_page.py`
- `packages/ui/pages.py`
- `packages/ui/shell.py`
- `tests/test_g07_records.py`
- `TASK_STATE.md`
- `IMPLEMENTATION_REPORT.md`

### 数据与算法说明

- Domain 继续只依赖 Python 标准库和既有 Domain 契约；SQLite 适配器位于 `packages/persistence`，Qt 只负责页面和仓储注入。
- 记录行保存 `input_snapshot_json`、`calculation_snapshot_json`、`parameter_snapshot_json`、`warnings_json`、`raw_input_snapshot_json` 和 `effective_rule_set_json`；表中不存可编辑业务状态。
- `accounting_records.deleted_at/deleted_by/deleted_reason` 实现可追溯软删除；`audit_log` 的 CREATE/DELETE 为独立审计证据。
- `standard_version` 继续保存不可变标准版本身份 `standard_id`，与 `algorithm_version`、记录输入和结果一起形成历史追溯键。

### 测试

#### L1

命令：

`.venv\Scripts\python.exe -m unittest tests.test_g07_records -v`

结果：8/8 通过，0 个失败，0 个错误，0 个跳过。覆盖成功/警告状态往返、参数/输入/规则快照、审计写入失败回滚、软删除与不可复用 ID、同输入新记录 ID、ERROR 不落记录、记录列表搜索/状态筛选/只读详情、删除确认和未计算输入离开门禁。

#### L2

命令：

`.venv\Scripts\python.exe -m unittest discover -s tests -v`

结果：111/111 通过，0 个失败，0 个错误，0 个跳过（项目 `.venv`，Python 3.12.14，PySide6 6.11.2）。其中原有 G00–G06 回归 103 项，G07 新增 8 项。

#### L3

- `.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- `.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir <临时目录>`：catalog.sqlite、user.sqlite、records.sqlite 从 Canonical/迁移从零生成成功，临时目录已清理。
- `git diff --check`：通过。
- `git diff --name-only -- 计算表/**`：无输出；`计算表/` 未修改。
- pytest 未执行；项目现有测试基线为 unittest。
- 未执行 G08 Windows standalone 构建、安装产物检查和交付测试；这些属于 G08，不得提前执行。

### Git

- 分支：`main`
- 实现提交：`707c59a feat: implement G07 record lifecycle`
- 文档提交：本报告和 `TASK_STATE.md` 随后单独提交。
- 最终工作区预期：仅保留既有未跟踪 `docs/handoffs/`，未处理、未纳入提交。

### 已知问题

- 无 G07 范围内已知问题。
- 视觉人工验收、Windows standalone 构建和 G08 交付检查未执行，原因是阶段门禁禁止提前执行，不代表 G07 失败。

### 建议 Sol 重点复核

- 计算成功后 records.sqlite 中记录行与 CREATE 审计是否同事务提交，故障时是否无半条记录。
- 原始输入、有效规则 ID、参数快照和警告在修改当前 Catalog 后是否仍保持历史稳定。
- 同一输入连续计算的记录 ID、软删除后默认列表隐藏、DELETE 审计保留和记录 ID 不复用。
- 页面列表搜索/筛选与只读详情、首页最近记录刷新，以及离开未计算页面的二次确认。

### 提交与等待

- G07 实现提交：`707c59a`。
- 文档更新后停止等待 Sol 验收；不创建或执行 G08。

## G07 Sol 正式验收结论（2026-09-19）

### 结论

**FAIL**

被验收 HEAD 为 `8510c2128a43f88605d3f35e8238ab51246bdc37`。SQLite 仓储本身的事务、回滚、不可变记录、软删除和审计基础通过，但真实默认应用没有接入该持久化仓储，且版本追溯、输入详情和未计算输入生命周期仍不满足 G07 MUST。

### 已通过核对

- records 002 迁移从零建立成功；记录、全部 JSON 快照和 CREATE 审计使用同一事务，强制审计失败时没有半条记录。
- ERROR 不落成功记录；两种成功状态可往返读取；相同输入重复计算生成不同 ID，旧记录不覆盖。
- 软删除保留数据库行并追加 DELETE 审计；默认读取隐藏已删除记录，记录 ID 不能复用。
- 台账具备企业/记录/标准搜索、状态筛选和只读文本控件；首页可从已注入的仓储刷新最近记录。
- 原始 GB/T 32151.34—2024 PDF SHA256 为 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`，封面版本为 2024；Canonical 校验通过且对应 `version` 为 `2024`。

### 未满足项及修正要求

1. **默认正式入口必须改为 SQLite。** 当前 `create_shell(AppConfig())` 得到 `InMemoryRecordRepository`，`resolved_records_database()` 没有用于默认仓储装配。应让普通应用启动默认创建/迁移用户数据目录的 `records.sqlite`；内存仓储仅由测试或明确调用者显式注入。增加按默认配置创建窗口、成功计算、关闭并重新创建应用后仍可读取同一记录的测试。
2. **保存真实标准版本。** 当前 `standard_version` 列重复写入标准 ID，页面也用 ID 冒充版本。应从受控标准目录/领域上下文保存真实不可变版本 `2024`（同时保留 `standard_id`），读取模型和详情分别展示标准编号/版本；增加 SQLite 直接断言和 Catalog 变化不改变历史值的测试。
3. **详情必须展示实际输入。** `raw_input_snapshot_json` 已保存完整对象，但页面只显示字段名。应以只读、可理解的分组展示活动数据、排放源状态、电力明细、证明状态和其他 G06 输入的实际快照值；不得回查当前页面输入或当前 Catalog 代替历史快照。增加代表性多电力/过程输入的详情断言。
4. **完整实现丢弃和关闭门禁。** 用户确认离开后应把页面恢复到一个全新的核算状态，包括期间、所有下拉/排放源状态、动态明细行、结果和内部索引；关闭主窗口时脏输入也应提示，拒绝时取消关闭，确认时丢弃。当前探针确认年份和动态行未重置，关闭无提示。增加导航取消/确认、关闭取消/确认和重新进入新核算的测试。
5. **补充缺口测试。** 现有 8 项测试显式注入 SQLite，且仅检查企业名称清空，不能证明真实应用闭环。应把以上四类场景纳入 G07 定向回归。

### 独立测试及探针

- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g07_records -v`：8/8 通过。
- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page tests.test_g02_persistence -v`：34/34 通过。
- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`：111/111 通过。
- `.venv\Scripts\python.exe -m compileall -q packages apps tests scripts`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功，records 迁移 001/002 均存在；本次临时数据库和 PDF 渲染目录已清理。
- 默认入口探针：`default_repository=InMemoryRecordRepository`。
- 标准版本探针：数据库得到 `('gbt_32151_34_2024', 'gbt_32151_34_2024')`，预期版本是 `2024`。
- 详情探针：实际输入值 `12345.678` 与 `PROOF-X` 均未显示。
- 丢弃探针：确认离开后年份仍为 `2030`、电力行仍为 2 条；关闭探针为 `close_accepted=True`、`prompt_calls=0`。

### Git、范围与门禁

验收前工作区仅有既有未跟踪 `docs/handoffs/`；`计算表/` 无差异，未发现 G08 越界。本次只修改验收文档，不修改业务代码、外部标准或用户文件。

G07 未通过，不允许进入 G08；修正完成后应发送“重新验收G07”。

## G07 验收返工实施报告（2026-09-19）

### 范围与结果

本轮仅处理 G07 FAIL 的默认持久化、标准版本、只读详情和未计算输入生命周期问题；实现与测试提交为 `b12a75b`。未创建或执行 G08，未修改 schema_version、数据库迁移或“计算表/”，未处理既有未跟踪 `docs/handoffs/`。

- `create_shell(AppConfig())` 默认装配 `SQLiteRecordRepository(config.resolved_records_database())`，正式应用关闭并重新创建后仍从同一 `records.sqlite` 读取记录；显式仓储注入仍用于隔离测试。
- Domain/SQLite/详情页分离保存并展示稳定标准编号和 Canonical 版本，GB/T 32151.34—2024 的版本为 `2024`，不再把 `standard_id` 冒充版本。
- 记录详情将 `raw_input_snapshot_json` 格式化为只读实际值，展示活动数据、电力明细、证明状态等历史快照，避免只显示字段名或读取当前页面状态。
- 新建核算页面增加完整重置路径，覆盖期间、组合框、排放源状态、材料基准/证明、动态电力行、结果、校验、快照提示和计算索引；Shell 导航与主窗口关闭复用确认门禁，取消会阻止动作。
- 测试补足默认应用闭环、SQLite 重启持久化、真实标准版本、详情快照、完整丢弃、导航取消/确认和关闭取消/确认；既有 GUI 测试显式使用内存仓储避免污染用户数据库。

### 测试与检查

- G07 定向：`.venv\Scripts\python.exe -m unittest tests.test_g07_records -v`；11/11 通过。
- 全量回归：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；114/114 通过。
- `compileall`：`.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`；成功。
- `pip check`：`.venv\Scripts\python.exe -m pip check`；无损坏依赖。
- Canonical：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功并已清理专用临时目录；`git diff --check` 通过；`计算表/` 无差异。
- 未执行 pytest，因为项目测试基线为 unittest；未执行 G08 构建、安装产物或交付测试，因为 G08 尚未获准。

### 提交与等待

- 实现/测试：`b12a75b fix: close G07 persistence and input lifecycle gaps`。
- 文档更新后仅保留既有未跟踪 `docs/handoffs/`，未纳入提交。
- 当前状态为等待 Sol 重新验收 G07；不得开始 G08。

## G07 Sol 正式重新验收结论（2026-09-19）

### 结论

**PASS WITH MINOR FIXES**

被验收 HEAD：`c4677a59f1d09f77d7294cd3bb500a9875815651`。

### 关键核对事项

- 上一轮 FAIL 的四类核心业务缺口已关闭：默认正式入口使用 `records.sqlite`；标准 ID 与真实版本 `2024` 分离保存；详情读取历史实际输入快照；导航离开和关闭主窗口均执行完整丢弃确认。
- SQLite 记录写入与 CREATE 审计处于同一事务；错误路径不生成成功记录；软删除保留记录及 DELETE 审计；相同输入重新计算生成新 ID。
- 历史详情读取记录自身的输入、结果、参数和规则快照，不存在历史记录编辑或覆盖入口；首页最近记录来自 records 仓储。
- 国家标准全文公开系统核对 GB/T 32151.34—2024：标准状态现行，发布日期 2024-08-23，实施日期 2025-03-01；实现保存的标准版本 `2024` 与官方编号一致。
- 从上一轮验收 findings `2abce5d` 到当前 HEAD 只有 `b12a75b fix: close G07 persistence and input lifecycle gaps` 和 `c4677a5 docs: record G07 rework readiness`，未发现 G08 越界。

### 小修项

1. 记录详情目前把历史原始输入以格式化 JSON 整段展示。数据真实、只读且来自冻结快照，但没有按“活动数据 / 排放源 / 电力明细 / 证明状态 / 其他输入”使用中文业务字段分组，未完全达到上一轮 findings 约定的“可理解的分组展示”。只需修改展示层，不得修改记录数据和计算逻辑。
2. G07 定向测试缺少“生成历史记录后改变当前 Catalog 参数，再查看历史记录仍完全不变”的直接回归。代码路径已使用冻结快照，未发现回查当前 Catalog 的实际缺陷，但 HANDOFF 的 G07 验收条件要求该行为被验证，应补一条明确测试。

### 测试与证据

实施方最新记录：
- G07 定向：`.venv\Scripts\python.exe -m unittest tests.test_g07_records -v`；11/11 通过。
- 全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；114/114 通过。
- `compileall` 成功；`pip check` 无损坏依赖；Canonical 为 `valid: 9 standards, 12 sources, 7 parameters, 7 factors`；三库从零重建成功。

Sol 本次独立复验限制：
- 当前验收容器为 Python 3.13.5，项目要求 `>=3.12,<3.13`。
- 当前容器无 PySide6；受网络/DNS 限制，无法下载安装依赖，也无法直接 clone 仓库到运行容器。
- 实际环境探针：`python3 --version` -> `Python 3.13.5`；`import PySide6` -> `ModuleNotFoundError`；`git clone` -> `Could not resolve host: github.com`。
- 因而上述 11/11 与 114/114 作为实施方已落盘的最近测试证据使用，**不是本次 Sol 独立重跑结果**；本次通过 GitHub 当前 HEAD 逐项复核源码、迁移和测试覆盖，并核对官方标准来源。

### Git、范围与阶段门禁

- 验收前 GitHub `main` HEAD：`c4677a59f1d09f77d7294cd3bb500a9875815651`。
- 最近 5 个提交：`c4677a5`、`b12a75b`、`2abce5d`、`8510c21`、`707c59a`。
- GitHub 已提交树未发现临时数据库、测试产物或 G08 实施；`计算表/` 未被纳入本次提交范围。
- GitHub 连接器不能读取用户开发机未提交/未跟踪工作区，所以不能把远端树状态冒充成本地 `git status`。
- 本次仅记录验收文档，不修改业务代码或用户文件。

G07 当前结论为 PASS WITH MINOR FIXES，不允许进入 G08。完成两项小修并在项目规定环境重跑定向测试和必要回归后，应发送“重新验收G07”。

## G07 历史详情小修实施报告（2026-09-19）

### 修正内容

本轮仅处理 G07 剩余两项展示与测试缺口，实现/测试提交为 `d6e4d91`。未创建或执行 G08，未修改 schema_version、数据库迁移或“计算表/”，未处理既有未跟踪 `docs/handoffs/`。

- `RecordLibraryPage` 将 records.sqlite 中的不可变原始输入快照转换为五个业务分组：活动数据、排放源、电力明细、证明状态、其他输入；数量/单位、取得方式、电力属性、证明状态和常见参数字段均使用面向用户的中文标签，未改变历史数据本身。
- `tests.test_g07_records.G07UiTests.test_historical_snapshot_stays_stable_after_catalog_parameter_change` 在独立 Catalog 中修改当前参数名称和来源定位，随后刷新详情并断言完整详情文本不变，锁定历史记录不回查或覆盖当前 Catalog。

### 验证结果

- G07 定向：12/12 通过。
- 全量回归：115/115 通过。
- compileall 成功；pip check 为 `No broken requirements found.`。
- Canonical 校验：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功并清理临时目录；`git diff --check` 通过；`计算表/` 无差异。

### 等待状态

当前停止等待 Sol 重新验收 G07；G08 仍未创建、未执行。


## G07 Sol 最终正式重新验收结论（2026-09-19）

### 结论

**PASS**

被验收 HEAD：`7e3573dfd7fc105cc013c07028c5eb8815836569`。

### 关键核对事项

- 上次 `PASS WITH MINOR FIXES` 的两项要求均已关闭：
  - 历史记录详情从原始 JSON 改为五个面向用户的中文业务分组，实际值仍来自 records.sqlite 冻结快照。
  - 新增 Catalog 变化后的历史详情稳定性回归，历史详情不会被当前 Catalog 参数名称或来源定位变化污染。
- G07 原有记录事务、失败回滚、两种成功状态、唯一新记录 ID、只读历史、参数/规则/输入快照、审计软删除、未计算输入丢弃门禁和首页最近记录路径保持有效。
- 本轮实现提交 `d6e4d91 fix: refine G07 history snapshot details` 只修改 `packages/ui/pages.py` 和 `tests/test_g07_records.py`；后续文档/合并提交保留验收记录，没有修改数据库 schema、Canonical 数据、计算算法或标准参数。
- 未发现 G08、报告导出、历史编辑、基于历史记录重新核算等越界实现。
- 国家标准全文公开系统复核 `GB/T 32151.34-2024` 状态仍为现行，发布日期 2024-08-23，实施日期 2025-03-01；本轮未修改任何标准口径。

### 测试证据

项目本地最新执行记录：

- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest tests.test_g07_records -v`：12/12 通过，0 失败，0 错误，0 跳过。
- `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -m unittest discover -s tests -t . -v`：115/115 通过，0 失败，0 错误，0 跳过。
- `.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`：成功。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`
- `.venv\Scripts\python.exe scripts\validate_canonical.py`：`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库从零重建成功；验收临时目录已清理；`git diff --check` 通过；`计算表/` 无差异。

Sol 当前容器为 Python 3.13.5 且未安装 PySide6，不能在项目冻结的 Python 3.12 + PySide6 环境独立重跑 GUI 测试；GitHub 当前提交也没有 workflow run 可替代。本次没有将上述测试数字冒充为 Sol 本容器执行结果，而是结合项目落盘测试记录、当前 HEAD 源码/测试逐项复核和官方标准来源核对进行最终验收。

### Git、范围与门禁

- 验收前 `main` HEAD：`7e3573dfd7fc105cc013c07028c5eb8815836569`。
- 最近 5 个提交：`7e3573d`、`3766294`、`d6e4d91`、`bcdb661`、`c4677a5`。
- 从上次验收提交 `bcdb661` 到本 HEAD 仅修改 `packages/ui/pages.py`、`tests/test_g07_records.py`、`TASK_STATE.md`、`IMPLEMENTATION_REPORT.md`。
- 本次 Sol 只修改两份验收文档，不修改业务代码、标准数据或用户文件。
- 按用户本轮说明，本地与远端提交一致，`docs/handoffs/` 仍未上传，`计算表/` 未修改。

**G07已通过，允许由用户另行启动G08；本次未启动G08。**
## G08 实施报告（2026-09-20）

### 范围与实现

本轮从已通过的 G07 基线开始，仅执行 HANDOFF.md 的 G08，未创建或执行 G09。恢复检查确认 `main` 与 `origin/main` 已对齐于 `fbe884df0dad890f1be6da945a52b288ea8c8f1c`；实现工作在 `gxx-implementation` 分支完成。既有未跟踪 `docs/handoffs/` 未处理，`计算表/` 未修改。

- `pyproject.toml` 应用版本为 `1.0.0`，新增受控的 `[project.optional-dependencies].build`（PyInstaller 6.22）；Canonical schema 仍为 `1.0.0`，没有新增迁移。Catalog manifest data version 为 `2026.09.20-g08.1`。
- `AppConfig` 支持 frozen onedir 目录内的只读 Catalog；默认 records.sqlite 和 JSON Lines 日志继续使用 Windows `%LOCALAPPDATA%` 用户目录。
- MigrationRunner 拒绝未知未来版本；SQLite 文件无法打开时统一转换为 `MigrationError`。重复初始化保持幂等，应用版本/数据版本元数据保持可追溯。
- `scripts/build_standalone.py` 从 Canonical 重新构建 Catalog，使用 PyInstaller onedir/windowed、独立绝对导入入口 `scripts/standalone_entry.py`，生成 `build-manifest.json`；`scripts/inspect_release.py` 校验文件清单、哈希、版本、Catalog 表和敏感范围。
- PyInstaller 误收集的 Poppler ICU 78 DLL 已在生成的发布目录中排除；这是已定位的 QtGui/Qt6Core 运行时 ABI 冲突修复，不改变业务计算、Canonical 或数据库 schema。
- `scripts/smoke_standalone.py` 在隔离 LOCALAPPDATA 下执行两次启动，验证 exe 不提前退出且 records.sqlite/application.jsonl 均创建；Windows CI 已接入 Canonical、全量测试、构建、审计和双启动步骤。
- `docs/DELIVERY.md` 和 README 补充源码安装、便携式构建、启动、数据目录、卸载数据保留、当前能力边界和故障排查。当前没有 MSI/安装向导、代码签名或自动升级服务，Windows 10 未在本环境实机验证。

### 测试与校验

- 定向：`.venv\Scripts\python.exe -m unittest tests.test_g08_delivery -v`；**7/7 通过，0 失败，0 错误，0 跳过**。
- 相关回归：`.venv\Scripts\python.exe -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_multi_electricity tests.test_g05_rules tests.test_g06_carbon_material tests.test_g06_page tests.test_g07_records -v`；**89/89 通过，0 失败，0 错误，0 跳过**。
- 全量：`.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`；**122/122 通过，0 失败，0 错误，0 跳过**。
- 编译：`.venv\Scripts\python.exe -m compileall -q apps packages scripts tests`；成功。
- 依赖：`.venv\Scripts\python.exe -m pip check`；`No broken requirements found.`
- Canonical：`.venv\Scripts\python.exe scripts\validate_canonical.py`；`valid: 9 standards, 12 sources, 7 parameters, 7 factors`。
- 三库：`.venv\Scripts\python.exe scripts\initialize_databases.py --output-dir <temporary>`；从零生成 catalog/user/records 三个 SQLite，临时输出已清理。
- 交付包：`.venv\Scripts\python.exe scripts\build_standalone.py --output-root dist --clean`；成功；`.venv\Scripts\python.exe scripts\inspect_release.py dist\QingzhouCarbonAccounting`；**PASS，229 files**；`.venv\Scripts\python.exe scripts\smoke_standalone.py dist\QingzhouCarbonAccounting`；**PASS，2 次隔离启动**。
- `git diff --check` 通过；`计算表/` 无差异；既有 `docs/handoffs/` 未纳入。

### 当前门禁

- 候选实现提交：`9aa0625` `feat: complete G08 Windows delivery baseline`。
- 下一步：推送 `gxx-implementation`，创建目标为 `main` 的 Pull Request，等待 GitHub Windows CI 检查完成；当前不启动 G09，待 Sol 预验收。
