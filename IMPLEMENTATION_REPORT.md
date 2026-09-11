# IMPLEMENTATION_REPORT

## 阶段

G02 Canonical 数据与 SQLite 基础（第二次返工）

## 前置验收与阶段边界

- G00 验收结论：PASS。
- G01 初次验收为 FAILED；能量单位共同基准和领域枚举字符串绕过问题已完成修复。
- G01 重新验收结论：PASS（本轮用户已明确确认）。
- 本轮只创建并执行 G02 Goal；G03 未创建、未执行。
- G02 首次验收结论：FAILED；本轮仅处理 Sol 指定的 Canonical/SQLite/G01 枚举、标准职责、来源定位和参数引用返工，未开始 G03。
- 返工后状态：READY_FOR_SOL_REACCEPTANCE，等待 Sol 重新验收。
- G02 再次验收结论：FAILED；Sol 指出 0.11 热力因子仍引用钢铁生产附件，本轮完成第二次返工，未开始 G03。

## G02 第二次返工内容

- 将 0.11 tCO₂/GJ 的参数与因子来源改为 GB/T 32150—2025 第7.5.6～7.5.7条，删除钢铁生产附件来源记录，避免把行业专项通知作为通则/炭素模块的共同来源。
- 同步修正热力参数与因子 source_id、source_location、factor_year=2025、valid_from=2026-07-01、适用标准范围和说明；保留标准缺省值语义。
- 测试改为验证标准来源、条款定位、年份、有效日期和双标准适用关系，不再断言钢铁附件。

## G02 首次返工内容

- Canonical schema、校验器和 catalog SQLite 迁移统一使用 G01 的 OfficialStatus、SourceType、ReviewStatus、ParameterType 和 ValueType 值集合；移除 OFFICIAL_NOTICE、SCIENTIFIC_REPORT、RETIRED、PENDING_REVIEW、OFFICIAL 和 DEFAULT 等旧字符串。
- 标准字段由含义不清的 status/authority 改为 official_status、issuing_authority（发布单位）、competent_authority（主管部门）和 technical_committee（归口部门），构建器与 SQLite 列保持一致。
- 按全国标准信息公共服务平台修正 GB/T 32151.7—2023、.8—2023、.13—2023 的名称；标准来源的 publisher 改为官方发布单位。
- 电力公告来源改为 GOVERNMENT_PUBLICATION，记录生态环境部、国家统计局联合发布机关。
- GB/T 32151.34—2024 只直接关联其附录 C 对应的 3 个天然气专属参数；其余 7 项计划标准仍无参数/排放源引用。
- （已由本轮第二次返工修正）此前曾将 0.11 tCO₂/GJ 指向生态环境部办公厅环办气候函〔2023〕332号附件4；该来源已移除，当前以 GB/T 32150—2025 第7.5.6～7.5.7条为准。

## 本轮完成

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

## Scope 控制

- 没有修改 apps/ 或 packages/ui/，没有开始 G03 桌面外壳、首页、导航、Logo 或禁用入口。
- 没有实现 G04 查询页面、G05 规则解析、G06 计算公式、G07 记录闭环或 G08 Windows 交付。
- 没有录入完整 26 种燃料、碳酸盐过程参数、蒸汽焓值或完整 AR6 GWP 表；这些不属于本阶段最小数据集合。
- 没有生成并提交运行时 SQLite 文件；构建产物由 CLI 在指定目录按需创建。
- 计算表/ 下 7 个用户参考文件未修改、未纳入 Git。

## 测试与检查

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

## 未执行项及原因

| 项目 | 状态 | 原因 |
|---|---|---|
| G03 桌面外壳与导航 | 未执行 | HANDOFF 阶段门禁要求先完成 G02 Sol 验收 |
| 完整参数库和完整 GWP 表 | 未执行 | 本阶段只允许首批最小集合，后续补充需单独阶段/验收 |
| YAML loader | 未执行 | 当前 Canonical 选用 JSON；环境无已批准 YAML loader，避免静默引入解释差异 |
| 正式数据库运行产物 | 未提交 | SQLite 必须由 Canonical 构建脚本生成，测试使用临时目录 |
| Windows 安装包、GUI 视觉验收、企业真实数据和黄金算例 | 未执行 | HANDOFF 明确属于后续阶段或暂不实施范围 |

## Git

- 分支：main。
- 未使用破坏性 Git 操作。
- G02 原收口提交：e4d9b03 feat: establish G02 canonical data and database foundations。
- G02 返工实施提交：ba72f9a fix: address G02 catalog acceptance findings。
- G02 第二次返工实施提交：0cd6ed3 fix: correct G02 heat factor provenance。
- 保护范围：计算表/、.venv/ 和既有用户临时文件未修改；本轮只新增被忽略的 tmp 验证数据库，生成数据库不进入 Git。
- 工作区另有未跟踪 docs/handoffs/，非本轮新增或修改，未暂存。

## Sol 重新验收重点

1. 复核 Canonical schema、校验器、SQLite CHECK 与 G01 五组领域枚举完全一致，且没有旧字符串绕过。
2. 复核三项 2023 版标准名称、发布单位/主管部门/归口部门和电力公告联合发布机关。
3. 复核 GB/T 32151.34—2024 只关联其标准专属参数，7 项其他计划标准仍保持目录元数据范围。
4. 复核 0.11 tCO₂/GJ 的来源为 GB/T 32150—2025 第7.5.6～7.5.7条，适用于通则与炭素材料模块，以及 21 个定向测试、39 个全量测试和 L3 检查记录。
5. G02 重新 PASS 前不得启动 G03；Luna 已停止，不会自动进入 G03。
