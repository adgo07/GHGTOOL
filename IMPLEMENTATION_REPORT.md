# IMPLEMENTATION_REPORT — 2023年电力因子完整收录与地区展示

状态：候选待独立验收
日期：2026-10-08
分支：`codex/electricity-factors-2023-regions`
代码及测试提交：`e2b75c36d59abbc1501cc8d871c8e0ba764dac8d`

## 1. 范围与结果

按用户指定的《2023年电力二氧化碳排放因子.xlsx》补齐参数与因子库：五张来源表、40条数据（保留原全国平均1条，新增39条），增加地区列，并在全库搜索标题与参数详情中展示地区。没有西藏、香港、澳门、台湾条目，未补猜。全国三个不同口径分表保留，不合并或互相替代。

| 官方表 | 内容 | 条数 |
|---|---|---:|
| 表1 | 全国电力平均 | 1 |
| 表2 | 区域电力平均 | 7 |
| 表3 | 省级电力平均 | 30 |
| 表4 | 全国电力平均（不包括市场化交易的非化石能源电量） | 1 |
| 表5 | 全国化石能源电力 | 1 |

原有全国平均因子 `electricity_national_average_2023=0.5306` 的完整数据对象及其参数不变。新四类使用独立参数，只用于目录收录；不接入现有核算规则、不自动选择地区因子。本包不改变Calculator、Resolver、Numeric Profile、Unit规则、标准适用范围或历史Record，不启动新路线阶段。原表、用户参考文件、既有未跟踪文件和用户数据库均未修改。

## 2. 来源与全量核对

- 原表仅Sheet1，52行、2列，文件SHA256：`fcb2ddbae83f90f22c8f75a8277f92080297c68df3f13941b32febab92dd82ed`。只读提取原始XML数值，使用Decimal核对，不经过二进制浮点进入Canonical。
- [官方公告：生态环境部、国家统计局2025年第47号](https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202512/t20251231_1139517.html)，发布日期2025-12-31；数据年份2023。
- [官方原始附件表1～表5](https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202512/W020251231726284332528.pdf)。子agent独立核对原表与官方附件、Canonical与原表，均40/40精确一致。
- 原始单位`kgCO₂/kWh`，沿用现有规范化单位`tCO₂/MWh`，数值等价；公告四位小数以十进制字符串保留，华东显示`0.5500`。
- 原有99因子、98参数、98资产、44对象、9标准、13换算规则全部语义不变。无关原始JSON文本格式保留；`git diff --minimal`可消除重复JSON结构导致的差异匹配噪声。

## 3. 平台 / Contract 预检查

- 业务仓已实际核对origin为`https://github.com/adgo07/GHGTOOL.git`、默认分支main；从最新`origin/main`（`40f7dd76c81fc551c07bbfd2e04e6041f53fd445`）新建分支，开工时tracked文件干净，未纳入用户未跟踪文件。
- 锁定中央SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`，未修改`platform-lock.json`或`PLATFORM_BASELINE.md`。
- 已按锁定SHA读取Architecture V2.1 Frozen：§5分层；§9 Canonical、有效期和来源；§17 SQLite为查询与部署投影；§19历史Record不漂移；§26不打包标准全文/PDF。
- 适用MUST：Canonical数据可校验且来源精确；SQLite由Canonical构建；Presentation/Application/Domain/Infrastructure职责分离；官方数值以Decimal/字符串保存；用户可见内容中文。
- 适用MUST NOT：不得自动升级Frozen基线、让Domain依赖Qt/SQLite、将展示修约回流计算、改变既有正式默认候选或历史记录、猜测缺失地区或复制标准全文。
- 地区是本仓来源绑定的可选目录字段；本任务不涉及中央公共Contract。无Contract冲突或CENTRAL CONTRACT GAP，不需要修改中央Contract；Numeric/Unit语义未变，不扩大读取无关Contract。
- 当前UI指南按中央正式main `9a6e6c1a82c44d425069e499f511e91f8c046ca1`读取（ACTIVE/EVOLVING）：§5分层、§7中文、§8不泄露内部ID、§15保留审计、§26不静改业务结果。
- 相关Standard Issue：既有`GHG-STD-32151-34-005/006`期间与来源裁定继续有效；原全国因子及绑定有效期保持不变。无新增标准歧义，无新增解释问题，不改变既有软件解释。

## 4. 实现与兼容

Canonical新增4参数、39因子、39资产、39绑定、4来源表；目录数据版本为`2026.10.08-electricity2023.1`。五张表沿用只读浏览，地区来源定位可追溯；新增表按原表地区次序展示。

`reference_data_bindings.region`为可选字段，DTO默认None。Catalog新增非破坏`003`迁移，仅追加可空TEXT列；构建器写入地区，Repository兼容读取不含地区字段的旧`002`目录且不写库。User/Records/Projects迁移目录不变。同步发布构建/审计的catalog版本断言及受影响旧测试的目录数量/版本预期。

## 5. 本地验证（Windows / Python 3.12.14）

| 命令 / 检查 | 结果 |
|---|---|
| `.venv/Scripts/python.exe -m unittest tests.test_electricity_2023_catalog tests.test_electricity_region_persistence tests.test_g02_persistence tests.test_g04_catalog tests.test_g05_multi_electricity -q` | 36通过、0失败；39.769秒 |
| `.venv/Scripts/python.exe -m unittest tests.test_g02_canonical tests.test_g08_delivery tests.test_electricity_region_persistence -q` | 33通过、0失败；8.677秒，子agent本地执行 |
| 两个新增测试文件（含于上述集合） | 8通过、0失败：40条精确值/地区、五表次序、搜索口径、默认候选、GUI地区、旧目录兼容、无损幂等迁移 |
| `.venv/Scripts/python.exe -m unittest discover -s tests -t . -q` | 执行313项：311通过、1失败、1错误；419.401秒。两项均为本地旧目录/权限影响，干净提交副本复验2/2通过；未冒称原工作区全量零失败 |
| `.venv/Scripts/python.exe scripts/validate_canonical.py` | 通过：9标准、12来源、102参数、138因子 |
| 设置`PYTHONPYCACHEPREFIX`至任务临时目录后`.venv/Scripts/python.exe -m compileall -q apps packages resources scripts tests` | 通过，退出0 |
| `uv pip check --python .venv/Scripts/python.exe` | 17包兼容，通过 |
| `.venv/Scripts/python.exe scripts/initialize_databases.py --output-dir tmp/electricity-2023/isolated-databases` | Catalog/User/Records/Projects四库隔离初始化通过 |
| `.venv/Scripts/python.exe scripts/uir04_manual_gui_acceptance.py` | 既有5场景通过（offscreen自动操作） |
| `.venv/Scripts/python.exe scripts/uir04_scale_acceptance.py --scale 1.25`及`--scale 1.5` | 两档通过，1366×768 |
| 电力五表离屏截图，1280×900 | 全部已视检：中文、地区、四位小数和来源定位可读，省级表支持滚动；长口径完整显示于表标题及参数列 |
| `git diff --check` / `git diff --cached --check` | 通过 |

全量回归两项环境问题：`test_c3_heat_default_resolves_for_standard_effective_dates_and_custom_periods`在既有`build/pf01-test-tmp` mkdir被拒；`test_tolerance_taxonomy_is_test_only_for_confirmed_is_close_call`扫描到既有忽略目录`tmp/pf01-base-wt`。使用`git archive HEAD`创建干净副本后，Python3.12按原测试名运行两项，2通过/0失败（0.975秒）。不删除旧临时副本，不修改这两项测试。

初次新增GUI测试漏传navigate，已修正测试调用；相关旧公告搜索单值断言更新至完整40条，定向重跑通过。第一次compileall受现有缓存目录写权限限制失败，改用临时缓存通过。venv未提供pip模块，`python -m pip check`未执行成功，改用uv检查同一venv，未安装或改变依赖。第一次离屏截图缺默认字体，验证脚本显式加载本机微软雅黑后重新渲染；没有修改产品字体。

## 6. 远端证据与未执行项

本地不制作正式发布包；Windows standalone构建、发布审计与启动由PR-head GitHub Actions验证，不能表述为本地已执行。报告提交时远端尚未执行；正式PR最新head及Windows CI结果以本PR Checks为准。CI作为独立远端证据，不与本地回归混写。

截图及GUI脚本为离屏验证，不声称完成原生人工鼠标验收。既有Word分页/长标题等观察项保留，不扩充本任务范围。交付PR后停止，等待独立验收，不自行合并。
