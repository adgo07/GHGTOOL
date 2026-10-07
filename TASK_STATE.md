# TASK_STATE

状态：CURRENT STATE；更新：2026-10-07。

## 当前工作包与基线

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- 工作包：GHG-PF01 — 参数与因子注册库基础架构 + 页面重构。
- Base / 开工时最新 `origin/main`：`c61b29baa2f5d75deae5fc243874d2b1d947bf4a`；该提交包含已合并的UAT01-B。分支：`codex/pf01-parameter-factor-library`；未从PR #27派生，PR #27未修改。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`，未升级。
- 平台 / Contract预检查：按locked SHA核对Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；中央ACTIVE UI指南按当前正式版本核对。适用要求为分层隔离、Canonical JSON可校验、只读界面不替代Resolver、普通界面隐藏内部标识、历史Record不可漂移。本任务不涉及中央公共Contract；无冲突、无baseline变更。
- Standard Issue：涉及既有 `GHG-STD-32151-34-003`；`GHG-STD-32151-34-005/006`已按用户裁定和原始标准分组核查解决。C.1 78条、C.2 11条、§5.2 6条共95条因子及对应来源绑定不再把标准实施日重复记作自身有效期；SourceDocument实施日仍保留。核算期间早于、跨越或晚于实施日均继续核算并产生非阻断Warning。真正具有自身适用期间的年度官方电力因子仍由Resolver按期间筛选。不宣称发布机构认可标准追溯适用。
- 交付：PR #30保持OPEN / UNMERGED；GitHub当前head仍为`4d5d7bc42336afa6d80a9894297454a43f8706d6`。候选已迁入D盘独立恢复工作区并在`4d5d7bc`上验证；远端`main`已同步至`4f2e1c3d40f91b05e7eaa0dc245aad7e5d019f95`，尚待合入、复测、推送及最新head CI，不得将本地测试称为PR验收。

## 实现状态

- GHG-PF01：`IMPLEMENTED / AWAITING ACCEPTANCE`；完成注册数据模型、Canonical校验、SQLite只读投影、查询服务与注册库页面重构。
- Canonical schema `1.1.0` / data version `2026.10.07-pf01.2`：14张来源表、98个参考数据资产、100条来源绑定、99个因子候选。C.1/C.2与其他简单参数表使用正式Canonical；C.4/C.5由版本化Calculator只读提供。
- 同值多来源共用同一不可变资产并保留多个独立定位；值不同使用独立版本；无权重字段。Resolver继续作为计算默认选择唯一入口，不因目录排序或展示发生变化。
- 新增Catalog迁移002，仅新增来源表、参考数据资产、来源绑定三张表与索引；无破坏性迁移。
- 查询层支持来源/表/资产的动态结构、跨库搜索（含表格实际单元格内容）及按资产去重展示多来源。页面提供“按标准/文件查看”和“全库搜索”，不显示内部ID。
- 热力缺省0.11继续经Resolver使用，Calculator传入核算期间，不改变选择策略。C.3因子和来源绑定不再把标准实施日2025-03-01记作自身`valid_from`，故用户明确选择本标准核算较早期间时仍有候选；标准元数据实施日期保留，真正具有期间适用性的年度电力因子日期不变。购入/输出热力共用既有解析路径。
- 对完全早于、跨越或晚于所选标准实施日的期间，新计算均给出非阻断WARNING，成功Record随之为`COMPLETED_WITH_WARNINGS`并保留提醒。正式公式、Resolver Selection Policy和历史Record均未修改。
- 按C.1、C.2、C.3及§5.2参数分组核对原始标准，移除了无具体值独立适用期证据的95条因子及对应来源绑定上的重复日期；年度官方电力因子自身有效日期保留并有前后期间解析回归。
- 不改正式排放公式；成功Record快照和历史Record不漂移规则保持不变；PR #27仍为 `OPEN / UNMERGED`且只读；RS03-A用户UAT `PENDING`，RS03-B `NOT STARTED`；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。

## 本地验证

- 使用Python 3.12.14项目虚拟环境（PySide6 6.11.2）；Qt测试临时目录位于隔离工作副本内。
- `python -m unittest tests.test_g02_canonical -q`：20/20通过，新增标准实施日与C.3因子有效期分离断言。
- `python -m unittest tests.test_g04_catalog -v`：14/14通过，含目录页面、表结构、全库搜索、蒸汽表和单位表单元格检索。
- `TEMP/TMP=build/pf01-test-tmp; python -m unittest tests.test_g02_canonical tests.test_g02_persistence tests.test_g05_multi_electricity tests.test_g06_carbon_material.G06CalculatorTests.test_c3_heat_default_resolves_for_standard_effective_dates_and_custom_periods tests.test_g06_page tests.test_g07_records tests.test_g08_delivery tests.test_uir03_advanced_details tests.test_uir04_finalization -q`：104/104通过；覆盖三种实施日期关系、参数筛选、记录、交付及相关UI回归。
- `TEMP/TMP=build/pf01-test-tmp; python -m unittest tests.test_g04_catalog -q`：14/14通过。
- `python scripts/validate_canonical.py`：通过，9 standards、12 sources、98 parameters、99 factors。
- `build_catalog_database()`隔离构建通过：14张来源表、98个数据资产、100条绑定、13条转换规则；迁移002成功。
- `TEMP/TMP=build/pf01-test-tmp; python -m unittest discover -s tests -t . -q`：266/266通过（75.605秒）。
- `python -m compileall -q apps packages scripts tests`：通过；`python -m pip check`：通过。
- `python scripts/initialize_databases.py --output-dir build/pf01-final-databases`：catalog/user/records/projects四库从零隔离构建通过；隔离库在最终清理时删除。PF01原有Catalog迁移001→002保留检查沿用原报告，本次未重复执行。
- Windows standalone构建与smoke：候选迁移前曾在C盘只读工作树构建通过并双启动；D盘迁移且合入最新`origin/main`后的构建尚未执行，必须在最终候选上重跑后才能作为最终交付证据。
- 首次在默认TEMP/TMP目录运行持久化测试遇沙箱AppData写入拒绝；改用隔离的`build/pf01-test-tmp`后，定向与全量测试均通过。此环境限制及实际命令均已如实记录。
- 首次本地热力回归发现Calculator调用漏传核算期间；通过传递既有输入期间修复，不更改Resolver候选优先级。注册库搜索加入标准和来源文件后再次运行全量回归通过。

## 治理状态与停止点

- UAT01-A/B、RS01与RS02已合并进入main。PF01完成后须以独立PR的最终Head和精确head CI为准，之后等待独立验收，不自行合并。
- RS03-A USER UAT：`PENDING`；PR #27：`OPEN / UNMERGED`且保持只读；RS03-B：`NOT STARTED`。
- Golden Freeze、Release Gate及第二标准未启动；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。
