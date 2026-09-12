# IMPLEMENTATION_REPORT

## 阶段

G04 标准库与参数因子库查询

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

- G04 标准库与参数因子库查询已形成实现提交 `4419a73`；后续 Sol 正式验收结论为 FAIL。
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
