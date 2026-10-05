# TASK_STATE

状态：CURRENT STATE；更新：2026-10-06。

## 当前工作包与基线

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- 工作包：GHG-UAT01-B — 多物料过程与蒸汽热力简化闭环。
- Base / 开工时最新 `origin/main`：`d11d21a79cc89d291ebe4cc2cc5162a75018b1af`；PR #28（UAT01-A）合并结果已进入main。分支：`codex/ghg-uat01-b-material-steam`；由该main独立创建；PR #27没有用作基线或被修改。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定 SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`，未升级。
- 平台 / Contract 预检查：按锁定 SHA 读取 Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；Domain保持独立于PySide6/SQLite/Excel，数值运算沿用项目 Carbon Decimal Profile，由Calculator显式策略驱动归一化及C.4/C.5插值。本任务未修改中央公共Contract或本地baseline；不存在Contract冲突。
- Standard Issue：涉及既有 `GHG-STD-32151-34-003`（C.4异常键）；仍按已批准的1.70/1.80 MPa项目解释，保留原始异常证据，不称官方勘误。本任务不改变此既有决定、不新增标准问题。
- PR #27：GitHub状态为 `OPEN / UNMERGED`；仅读取其 `carbon_material_normalization.py` 的纯Python可复用能力作为参考，未基于其分支开发、未修改该PR。

## 实现状态

- UAT01-B：`IMPLEMENTED / AWAITING ACCEPTANCE`；本包独立PR及其最终head的GitHub Actions仍是交付门槛。
- 新增共享纯Python物料归一化：多行质量汇总、质量加权固定碳/挥发分、副产品碳质量求和、空白与显式0区分；兼容PR #27参考的 `MaterialAmount`、`weighted_fraction`、`carbon_mass` 基础能力，GUI经同一标准化器传入现有 `CarbonMaterialInput`。式(6)～(8)公式本身未变。
- 普通过程录入新增物料行、类别/名称、数量、固定碳/挥发分和各自数据来源；目前无适用 Canonical 标准缺省值，默认实测，可选化学计算，不造默认值；标准需计算的组成缺失或数值非法则 Domain 阻断。
- 蒸汽录入改为吨与绝压 MPa。饱和/过热蒸汽焓由既有版本化Domain Calculator查C.4/C.5并沿用线性/双向内插；允许手动焓值覆盖，差异和表外参考状态仅警告，自动模式缺值/超范围才阻断。热力因子0.11由现有Canonical参数Resolver提供，实测值可覆盖。
- 结果/Trace保存并呈现手动/自动焓值来源、自动参考值、压力/温度插值端点、热力因子来源；业务排放公式、C.4/C.5正式表值及Canonical数据未更改。
- 旧Project通过现有`form_state_json`作加法兼容；旧蒸汽kg输入换算回吨，原手动焓值恢复为手动模式，旧聚合物料字段在用户填写新物料行前仍可读。没有破坏性迁移。成功计算继续新建不可变Record；历史Record不重算、不改写。
- 没有实现新的多过程/多热源/多电力行模型，没有修改Excel模板或Excel导入流程；RS03-B、Golden Freeze、Release及第二标准未启动。

## 本地验证

- 聚焦：`python -m unittest tests.test_g06_carbon_material tests.test_uat01b_material_steam -v`，30/30通过；覆盖式(6)～(8)多物料手算对照、零值/缺项、C.4/C.5节点与内插、吨转kg、手动焓值及历史Record快照。
- 全量：`python -m unittest discover -s tests -t . -v`；145项实际运行，11个Qt UI测试模块在导入时因本机缺少`PySide6`报错；其余已运行用例通过。全量回归不记为通过，等待Windows/Python 3.12 CI覆盖。
- GUI/缩放验收：未能本机执行，原因同为当前Python环境未安装`PySide6`。
- Canonical：`python scripts/validate_canonical.py`通过：9 standards、12 sources、98 parameters、98 factors（本包未改Canonical）。
- 编译：`python -m compileall -q apps packages scripts tests`通过。
- 依赖：`python -m pip check`通过，无损坏依赖。
- 隔离数据库：`python scripts/initialize_databases.py --output-dir <临时目录>`通过，创建catalog、user、records、projects四库；本包无数据库迁移。
- Windows standalone：`python scripts/build_standalone.py --output-root <临时目录>`未通过，当前本地Python缺少`PyInstaller`；本机也缺少`PySide6`，未产出可运行版，因此release archive审计和smoke启动未执行。
- `git diff --check`：截至报告草稿前通过；提交前复核。
- GitHub Actions：尚待独立PR与最终head创建后验证，不能引用历史head结果。

## 治理状态与停止点

- UAT01-A由PR #28合并进入main；当前UAT01-B已实现，等待最新PR head CI与独立验收。
- RS03-A USER UAT：`PENDING`；PR #27：`OPEN / UNMERGED`且只读。
- RS03-B：`NOT STARTED`；GB/T 32151.34—2024：`NOT SUPPORTED`。
- 本包PR不合并；完成最新head Windows CI验证后停止，等待独立验收。
