# GHG-PF01 — 参数与因子注册库基础架构 + 页面重构

状态：`IMPLEMENTED / AWAITING ACCEPTANCE`。实现、全量本地回归和Windows standalone构建已完成；独立PR #30保持OPEN / UNMERGED，等待独立验收。PR最新Head的Windows CI以GitHub PR Checks为准；本报告不内嵌Head或run SHA，最终精确证据见交付回复，避免自引用提交。

## 1. 基线与平台 / Contract 预检查

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- Base：开工时最新 `origin/main` `c61b29baa2f5d75deae5fc243874d2b1d947bf4a`，含已合并的UAT01-B。分支：`codex/pf01-parameter-factor-library`。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；锁定中央SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`；未升级。
- 按锁定SHA核对Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；并读取中央当前ACTIVE UI指南。执行分层隔离、Canonical可校验、内部ID不泄露、目录只读且不得取代计算Resolver、Record快照不漂移等要求。
- 本任务不涉及中央公共Contract；无Contract冲突，不改 `platform-lock.json` 或 `PLATFORM_BASELINE.md`。
- 相关Standard Issue：是，既有 `GHG-STD-32151-34-003`。C.4/C.5仍由版本化Calculator提供并延续已批准的1.70/1.80 MPa项目解释；不改变既有软件解释、不新增Standard Issue、不称官方勘误。
- PR #27保持 `OPEN / UNMERGED`且未修改；未从PR #27分支派生。

## 2. 实现内容

### 注册数据与可追溯关系

- Canonical catalog升至schema `1.1.0`、data version `2026.10.06-pf01.1`。
- 新增14张来源表、98个不可变参考数据资产、100条来源绑定；因新增C.3热力缺省候选，Factor由98增至99，Parameter仍为98。Canonical校验通过：9个标准、12个来源、98个参数、99个因子。
- C.1登记26个燃料表项，C.2登记完整11个碳酸盐表项；简单标准参考数据通过来源表结构、资产和绑定展示。等值多来源可共享资产并保留各自定位；来源值不同使用独立资产版本；没有权重字段。
- 为GB/T 32151.34—2024 C.3新增0.11 tCO₂/GJ正式缺省因子候选，定位附录C表C.3（PDF第27页、印刷页19），有效期从2025-03-01开始。它与GB/T 32150—2025通用缺省的数值相同但保留独立来源适用信息；资产按相同值复用。
- C.4/C.5蒸汽表没有复制进Canonical。只读Adapter调用版本化Calculator的 `steam_reference_table_rows()`；插值、算法及正式表值均不变。
- 对C.4/C.5相关问题继续执行 `GHG-STD-32151-34-003`：原始重复/异常压力键事实保留，后两项沿用批准的1.70/1.80 MPa软件解释，非官方勘误。

### 查询与页面

- 新增只读查询模型及SQLite投影，按登记列布局浏览来源表；C.1/C.2显示Canonical登记数据，C.4/C.5显示Calculator只读数据。
- 页面提供“按标准/文件查看”和“全库搜索”。全库检索覆盖标准目录项、来源文件/政策/公告、来源表元数据与单元格内容、参考数据资产；共享资产按ID和版本去重，详情列出多处来源定位。
- 详情使用侧栏式分栏呈现，提供已登记官方页面链接；普通页面不显示内部主键或数据库字段。
- 在 `AGENTS.md` 增加一条简短长期规则，明确Canonical登记职责与Resolver单一选择权；同步更新 `docs/DELIVERY.md` 中Canonical schema与Catalog/User/Records迁移版本。

### 热力因子适用期接通

- 回归发现既有热力Resolver按日期选取候选，但Calculator调用时漏传核算期间，导致有效期候选无法按核算期间判定。现将既有输入期间传入 `ParameterResolutionContext`；Resolver优先级与选择策略未改。
- 年度与自定义核算期间、2025/2026适用日期、购入与输出热力均由既有Resolver取得适用0.11候选；没有在UI硬编码标准值。

### 数据库与兼容

- Catalog迁移002只新增来源表、参考数据资产、来源绑定三张表及索引，无删除或重建旧表；不修改Project或Record存储。
- 从迁移001状态升级到002的隔离检查通过，旧来源记录仍保留。
- 未改Calculator正式排放公式、Numeric Contract、历史Record快照或PR #27。

## 3. 测试预期与计数变更

**Canonical / 数据契约变化：**本包从Canonical schema `1.0.0`升至`1.1.0`；Catalog数据库迁移从`001`升至`002`；因增加C.3热力因子候选，Factor断言由98改为99。新增资产/表/绑定真实计数为98/14/100。同步更新了Canonical校验测试、持久化计数、release audit与归档审计夹具；这些更新对应正式数据和版本增加，不是删除旧测试。

**行为预期变化：**热力因子解析现携带已有核算期间，使既有有效期规则在Calculator链路真正生效；选择政策未变。全库搜索新增标准和来源文件结果，因此界面测试按结果类别选择参数项/表项，不再把结果数量当作固定常量。未改变公式或Resolver选择顺序。

## 4. 本地验证

以下均由Windows Python 3.12.14项目虚拟环境实际执行：

- `python -m unittest tests.test_g02_canonical -v`：19/19通过，覆盖共享资产多定位和不同值版本。
- `python -m unittest tests.test_g04_catalog -v`：14/14通过，覆盖页面、动态表结构、标准/来源/表格内容与资产搜索、蒸汽Calculator Adapter及来源链接。
- `python -m unittest tests.test_g06_carbon_material.G06CalculatorTests.test_c3_heat_default_resolves_for_standard_effective_dates_and_custom_periods -v`：1/1通过，覆盖2025/2026、年度/自定义期间及购入/输出热力。
- `python -m unittest discover -s tests -t . -v`：264/264通过。
- `python scripts/validate_canonical.py`：通过（9 standards、12 sources、98 parameters、99 factors）。
- `python -m compileall -q apps packages scripts tests`：通过。
- `python -m pip check`：通过，无损坏依赖。
- `python scripts/initialize_databases.py --output-dir build/pf01-isolated-db-final`：通过，隔离创建catalog/user/records/projects四库；另验证Catalog 001→002旧行保留。
- `python scripts/build_standalone.py --output-root build/pf01-standalone-final`：通过；release文件范围/哈希/数据库审计与ZIP归档往返审计均由构建流程执行。
- `python scripts/smoke_standalone.py build/pf01-standalone-final/QingzhouCarbonAccounting`：通过，两次隔离启动。
- GitHub Actions：PR #30必须由当前最新Head通过Windows/Python 3.12 `Merge-ref Full Tests`与`PR-head Standalone Audit`；最终精确Head和两项结果以GitHub PR Checks及交付回复为准，不在本文件重复记录run SHA。

## 5. 治理状态与停止点

- GHG-PF01：`IMPLEMENTED / AWAITING ACCEPTANCE`；交付独立PR，等待最终Head exact-head Windows CI及独立验收；不自行合并。
- PR #27：`OPEN / UNMERGED`，未修改；RS03-A USER UAT：`PENDING`；RS03-B：`NOT STARTED`。
- Golden Freeze、Release Gate及第二标准未启动；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。
