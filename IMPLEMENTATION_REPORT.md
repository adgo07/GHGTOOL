# GHG-PF01 — 参数与因子注册库基础架构 + 页面重构

状态：`IMPLEMENTED / AWAITING ACCEPTANCE`。实现、全量本地回归和Windows standalone构建已完成；独立PR #30保持OPEN / UNMERGED，等待独立验收。PR最新Head的Windows CI以GitHub PR Checks为准；本报告不内嵌Head或run SHA，最终精确证据见交付回复，避免自引用提交。

## 1. 基线与平台 / Contract 预检查

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- Base：开工时最新 `origin/main` `c61b29baa2f5d75deae5fc243874d2b1d947bf4a`，含已合并的UAT01-B。分支：`codex/pf01-parameter-factor-library`。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；锁定中央SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`；未升级。
- 按锁定SHA核对Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；并读取中央当前ACTIVE UI指南。执行分层隔离、Canonical可校验、内部ID不泄露、目录只读且不得取代计算Resolver、Record快照不漂移等要求。
- 本任务不涉及中央公共Contract；无Contract冲突，不改 `platform-lock.json` 或 `PLATFORM_BASELINE.md`。
- 相关Standard Issue：是，既有 `GHG-STD-32151-34-003`、本次已处理的`GHG-STD-32151-34-005`及待逐项核查的OPEN项`GHG-STD-32151-34-006`。C.4/C.5既有解释不变；005记录用户对标准实施日期与C.3因子自身有效期的产品裁定，不称官方解释。
- PR #27保持 `OPEN / UNMERGED`且未修改；未从PR #27分支派生。

## 2. 实现内容

### 注册数据与可追溯关系

- Canonical catalog升至schema `1.1.0`、data version `2026.10.06-pf01.1`。
- 新增14张来源表、98个不可变参考数据资产、100条来源绑定；因新增C.3热力缺省候选，Factor由98增至99，Parameter仍为98。Canonical校验通过：9个标准、12个来源、98个参数、99个因子。
- C.1登记26个燃料表项，C.2登记完整11个碳酸盐表项；简单标准参考数据通过来源表结构、资产和绑定展示。等值多来源可共享资产并保留各自定位；来源值不同使用独立资产版本；没有权重字段。
- 为GB/T 32151.34—2024 C.3新增0.11 tCO₂/GJ正式缺省因子候选，定位附录C表C.3（PDF第27页、印刷页19）。本次直接核对原始PDF（SHA256=`60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`）：封面实施日期为2025-03-01，但C.3未给该因子独立的起始有效日期。已把C.3因子及其来源绑定的`valid_from`改为`null`，保留标准目录的实施日期；不宣称标准官方认可追溯适用。它与GB/T 32150—2025通用缺省的数值相同但保留独立来源适用信息；资产按相同值复用。
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
- 本次用户产品裁定下，所选标准的实施日期经Catalog查询层交给版本化Calculator。核算期间完全早于或跨越实施日时，Calculator追加一条结构化、非阻断WARNING；该提醒进入CalculationResult、成功Record及普通页面的“数据质量”提示，并使新Record状态按既有规则为`COMPLETED_WITH_WARNINGS`。实施日后不追加这条提醒。C.3历史期间仍为候选，`accounting_period`继续筛选真正有期间适用性的因子（例如年度官方电力因子）。不改Resolver Selection Policy、正式公式、历史Record或数据库schema。
- 范围边界：本次原始来源核对与前/跨/后三例只证明C.3热力路径。收尾审计发现Canonical另有95条适用于本标准的因子仍标记`valid_from=2025-03-01`；其日期是否只是标准实施日尚未逐项核实，部分其他排放源的早期期间仍可能被候选过滤。已登记`GHG-STD-32151-34-006`，不机械更改这些因子，不把本次结果称为“全场景历史期间已支持”。

### 数据库与兼容

- Catalog迁移002只新增来源表、参考数据资产、来源绑定三张表及索引，无删除或重建旧表；不修改Project或Record存储。
- 从迁移001状态升级到002的隔离检查通过，旧来源记录仍保留。
- 未改Calculator正式排放公式、Numeric Contract、历史Record快照或PR #27。

## 3. 测试预期与计数变更

**Canonical / 数据契约变化：**本包从Canonical schema `1.0.0`升至`1.1.0`；Catalog数据库迁移从`001`升至`002`；因增加C.3热力因子候选，Factor断言由98改为99。新增资产/表/绑定真实计数为98/14/100。同步更新了Canonical校验测试、持久化计数、release audit与归档审计夹具；这些更新对应正式数据和版本增加，不是删除旧测试。

**行为预期变化：**热力因子解析现携带已有核算期间，使既有有效期规则在Calculator链路真正生效；选择政策未变。本次再区分标准实施日期与C.3因子有效期，并让早于/跨越实施日的选择产生非阻断提醒。旧UI测试原先要求2025全年成功结果完全没有质量提醒，已按新裁定改为核对提醒可见且不阻断。全库搜索新增标准和来源文件结果，因此界面测试按结果类别选择参数项/表项，不再把结果数量当作固定常量。未改变公式或Resolver选择顺序。

## 4. 本地验证

以下均由Windows Python 3.12.14项目虚拟环境实际执行：

- `python -m unittest tests.test_g02_canonical -q`：20/20通过，覆盖共享资产多定位、不同值版本及标准实施日与C.3因子有效期分离。
- `python -m unittest tests.test_g04_catalog -v`：14/14通过，覆盖页面、动态表结构、标准/来源/表格内容与资产搜索、蒸汽Calculator Adapter及来源链接。
- `python -m unittest tests.test_g06_carbon_material.G06CalculatorTests.test_c3_heat_default_resolves_for_standard_effective_dates_and_custom_periods tests.test_g06_page tests.test_uir04_finalization -q`：36/36通过，覆盖完全早于、跨越、实施日后及购入/输出热力、普通页面提醒、Record状态。
- `python -m unittest discover -s tests -t . -q`：265/265通过，0失败、0错误、0跳过。首次复跑暴露旧UI“成功后质量区必须隐藏”断言，更新为核对本次合法非阻断提醒后重新全量通过。
- `python scripts/validate_canonical.py`：通过（9 standards、12 sources、98 parameters、99 factors）。
- `python -m compileall -q apps packages scripts tests`：通过。
- `python -m pip check`：通过，无损坏依赖。
- `python scripts/initialize_databases.py --output-dir build/pf01-period-check`：通过，隔离创建catalog/user/records/projects四库，临时库随后清理。Catalog 001→002保留检查为PF01前次已执行结果，本次未重复。
- `python scripts/build_standalone.py --output-root build/pf01-period-standalone`：通过，本次构建输出随后清理。
- `python scripts/smoke_standalone.py build/pf01-period-standalone/QingzhouCarbonAccounting`：通过，两次隔离启动。
- GitHub Actions：PR #30必须由当前最新Head通过Windows/Python 3.12 `Merge-ref Full Tests`与`PR-head Standalone Audit`；最终精确Head和两项结果以GitHub PR Checks及交付回复为准，不在本文件重复记录run SHA。

## 5. 治理状态与停止点

- GHG-PF01：`IMPLEMENTED / AWAITING ACCEPTANCE`；交付独立PR，等待最终Head exact-head Windows CI及独立验收；不自行合并。
- PR #27：`OPEN / UNMERGED`，未修改；RS03-A USER UAT：`PENDING`；RS03-B：`NOT STARTED`。
- Golden Freeze、Release Gate及第二标准未启动；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。
