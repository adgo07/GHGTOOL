# TASK_STATE

状态：CURRENT STATE；更新：2026-10-06。

## 当前工作包与基线

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- 工作包：GHG-PF01 — 参数与因子注册库基础架构 + 页面重构。
- Base / 开工时最新 `origin/main`：`c61b29baa2f5d75deae5fc243874d2b1d947bf4a`；该提交包含已合并的UAT01-B。分支：`codex/pf01-parameter-factor-library`；未从PR #27派生，PR #27未修改。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`，未升级。
- 平台 / Contract预检查：按locked SHA核对Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；中央ACTIVE UI指南按当前正式版本核对。适用要求为分层隔离、Canonical JSON可校验、只读界面不替代Resolver、普通界面隐藏内部标识、历史Record不可漂移。本任务不涉及中央公共Contract；无冲突、无baseline变更。
- Standard Issue：涉及既有 `GHG-STD-32151-34-003`，C.4/C.5只读展示复用Calculator数据并继续既有1.70/1.80 MPa项目解释；本任务不改变解释、不新增问题。
- 交付：本分支创建独立PF01 PR；PR最终Head的Windows/Python 3.12 CI成功后等待独立验收，不合并。

## 实现状态

- GHG-PF01：`IMPLEMENTED / AWAITING ACCEPTANCE`；完成注册数据模型、Canonical校验、SQLite只读投影、查询服务与注册库页面重构。
- Canonical schema `1.1.0` / data version `2026.10.06-pf01.1`：14张来源表、98个参考数据资产、100条来源绑定、99个因子候选。C.1/C.2与其他简单参数表使用正式Canonical；C.4/C.5由版本化Calculator只读提供。
- 同值多来源共用同一不可变资产并保留多个独立定位；值不同使用独立版本；无权重字段。Resolver继续作为计算默认选择唯一入口，不因目录排序或展示发生变化。
- 新增Catalog迁移002，仅新增来源表、参考数据资产、来源绑定三张表与索引；无破坏性迁移。
- 查询层支持来源/表/资产的动态结构、跨库搜索（含表格实际单元格内容）及按资产去重展示多来源。页面提供“按标准/文件查看”和“全库搜索”，不显示内部ID。
- 热力缺省0.11按既有有效期经Resolver使用；Calculator此前未把核算期间传入Resolver，已补传期间上下文，不改变选择策略。C.3在2025有效期和2026通用默认均由Resolver取得；购入/输出热力共用既有解析路径。
- 不改正式排放公式；成功Record快照和历史Record不漂移规则保持不变；PR #27仍为 `OPEN / UNMERGED`且只读；RS03-A用户UAT `PENDING`，RS03-B `NOT STARTED`；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。

## 本地验证

- 使用Python 3.12.14项目虚拟环境（PySide6 6.11.2）；Qt测试临时目录位于隔离工作副本内。
- `python -m unittest tests.test_g02_canonical -v`：19/19通过，含共享资产多定位、不同值不同版本校验。
- `python -m unittest tests.test_g04_catalog -v`：14/14通过，含目录页面、表结构、全库搜索、蒸汽表和单位表单元格检索。
- `python -m unittest tests.test_g06_carbon_material.G06CalculatorTests.test_c3_heat_default_resolves_for_standard_effective_dates_and_custom_periods -v`：1/1通过，覆盖2025/2026、年度/自定义期间及购入/输出热力。
- `python scripts/validate_canonical.py`：通过，9 standards、12 sources、98 parameters、99 factors。
- `build_catalog_database()`隔离构建通过：14张来源表、98个数据资产、100条绑定、13条转换规则；迁移002成功。
- `python -m unittest discover -s tests -t . -v`：264/264通过。
- `python -m compileall -q apps packages scripts tests`：通过；`python -m pip check`：通过。
- `python scripts/initialize_databases.py --output-dir build/pf01-isolated-db-final`：catalog/user/records/projects四库从零隔离构建通过；单独验证Catalog迁移001→002保留原来源记录。
- `python scripts/build_standalone.py --output-root build/pf01-standalone-final`：通过，含release审计与ZIP归档往返审计；`python scripts/smoke_standalone.py build/pf01-standalone-final/QingzhouCarbonAccounting`：通过，两次隔离启动。
- 首次本地热力回归发现Calculator调用漏传核算期间；通过传递既有输入期间修复，不更改Resolver候选优先级。注册库搜索加入标准和来源文件后再次运行全量回归通过。

## 治理状态与停止点

- UAT01-A/B、RS01与RS02已合并进入main。PF01完成后须以独立PR的最终Head和精确head CI为准，之后等待独立验收，不自行合并。
- RS03-A USER UAT：`PENDING`；PR #27：`OPEN / UNMERGED`且保持只读；RS03-B：`NOT STARTED`。
- Golden Freeze、Release Gate及第二标准未启动；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。
