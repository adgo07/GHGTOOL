# GHG-UAT01-B — 多物料过程与蒸汽热力简化闭环

状态：`IMPLEMENTED / AWAITING ACCEPTANCE`。本地可运行的定向验证已通过；当前执行环境缺少PySide6和PyInstaller，GUI/standalone本地验收未完成。独立PR latest-head Windows CI和独立验收仍为交付门槛。UAT01-A已合并；RS03-A USER UAT `PENDING`；PR #27 `OPEN / UNMERGED`且未修改；RS03-B `NOT STARTED`；标准仍为 `NOT SUPPORTED`。最终Head与exact-head CI结果见最终交付回复和PR Checks，本报告不写自身提交SHA以避免自引用提交。

## 1. 基线与平台 / Contract 预检查

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- Base / 开工时最新 `origin/main`：`d11d21a79cc89d291ebe4cc2cc5162a75018b1af`，包含PR #28的UAT01-A合并结果。分支：`codex/ghg-uat01-b-material-steam`；PR #27未作为Base。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央Locked SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`。
- 按locked SHA读取Architecture V2.1、Numeric Contract v1、Numeric Profiles v1。适用要求：分层隔离；Domain不得依赖Qt、SQLite或Excel；权威数值必须消费声明的Numeric Profile，helper不得静默切换ambient/default配置，调用方ambient context不得改变同一Profile的结果。项目Carbon Decimal Profile继续由既有`DecimalPolicy`负责。本任务不涉及中央公共Contract，未修改Frozen Contract、`platform-lock.json`或`PLATFORM_BASELINE.md`，无Contract冲突。
- 相关Standard Issue：是，既有 `GHG-STD-32151-34-003`。继续保留C.4原始重复键事实并使用项目已批准的1.70/1.80 MPa执行解释；非官方勘误。本任务未改变既有软件解释、未新增标准问题。
- PR #27当前仍为OPEN、未合并；仅读取其纯Python `carbon_material_normalization.py` 作为可复用能力参考，没有使用其分支作为Base或修改该PR。

## 2. Base→Final Head的实际改动

本报告对应本包PR中的最终Base→Head diff；准确提交数、变更文件数、增删行与Head SHA由Git和最终PR记录确定，不把Head写回此文件。改动集中在Domain物料归一化、Carbon Material UI/输入元数据、相关Domain与UI测试，以及Roadmap、HANDOFF、TASK_STATE和本报告；没有修改Canonical数据、数据库迁移、`platform-lock.json`、`PLATFORM_BASELINE.md`、Excel模板或PR #27。最终回复列出逐文件名称与精确diff统计。

### B.3–B.5多物料

- 新增 `packages/standards/carbon_material_normalization.py`：纯Python接收现实物料行，并提供可复用质量汇总、质量加权固定碳/挥发分、碳质量合计和按标准公式变量映射。参考PR #27中`MaterialAmount`、`weighted_fraction`、`carbon_mass`能力，扩展过程角色与问题定位；UI与Domain共用此模块，未来Excel可以复用；物料CalculationTrace另记`CAR-MATERIAL-NORMALIZATION-V1`，与Calculator Numeric Profile版本分开追溯。
- 煅烧、焙烧/炭化、石墨化录入真实物料类别/名称/质量/固定碳/挥发分及独立来源，软件显示汇总值并映射至既有`CarbonMaterialInput`字段。公式(6)～(8)未修改；多行物料在每一过程实例内聚合，不更改实例/多能源数据模型。
- 当前Canonical没有可适用于过程物料组成的标准缺省值，故默认实测、允许化学计算，不复制硬编码默认值。显式0是零；空白是未提供/不存在。必需物料缺失、正质量缺少组成或非法数值时，Domain返回错误，不生成成功Record。

### B.9蒸汽热力

- 用户输入蒸汽吨数与绝压MPa；过热蒸汽额外输入温度。Domain通过现有`UnitService`将吨转换为公式要求的kg。
- 饱和蒸汽从版本化Domain Calculator的C.4表取值并线性内插；过热蒸汽从C.5表取值并沿用当前压力/温度插值。C.4/C.5完整表、既有表格查找架构与正式数值未改；继续执行`GHG-STD-32151-34-003`已批准的1.70/1.80 MPa解释，不称官方勘误。
- 自动计算是默认焓值模式。用户可手动覆盖；正式Calculator使用手动焓值。手动值与参考值明显不同、或状态超出表范围导致无自动参考时仅警告；自动模式缺压力/温度/可计算状态时阻断。Result/Record Trace区分来源，保存自动参考、焓值、表号、压力/温度节点和插值版本。
- 热力缺省因子0.11来自现有Canonical参数Resolver；实测因子可以覆盖，来源说明可选，缺失时提示但不阻止合法计算。没有新增硬编码标准值或C.4/C.5 reference-table架构。

## 3. 兼容与历史稳定性

- Project：使用现有`form_state_json`兼容路径加法保存新物料行，没有破坏性数据库迁移。已有聚合字段继续读取；用户填写新物料明细前保持原数据可用。旧蒸汽kg值恢复为吨输入，已有焓值恢复为手动模式。
- Record：新的输入与焓值来源进入Trace/快照；成功计算仍追加新的不可变正式Record。历史Record不重算、不改写、不重新读取当前Canonical数据；定向测试验证后续新核算不改变先前Record。
- 业务标准解释与正式公式没有变化；没有修改Numeric Contract或平台基线。

## 4. 测试变更与本地验证

**行为预期变化：**新物料行由共享归一化器生成既有公式变量；未选择合法自动焓值来源时由表数据确定，手工焓值覆盖并保留来源。没有修改测试来掩盖结果，也未改排放公式。

**定向测试：**`python -m unittest tests.test_g06_carbon_material tests.test_uat01b_material_steam -v`，30/30通过。覆盖三种过程多物料独立手算对照、质量加权、必需与可选物料、空白与显式0、C.4/C.5表节点与内插、吨转kg、自动超范围阻断、手动偏差警告/覆盖、来源Trace和既有Record不漂移。

**全量测试：**`python -m unittest discover -s tests -t . -v`共运行145项，其中11个Qt UI模块由于当前Python环境缺少`PySide6`而在导入时失败；其余已运行用例通过。故本地全量回归未通过/未完整执行，不计为PASS。GUI字段、界面中文、旧Project UI恢复和布局需由Windows/Python 3.12 CI执行确认。

- `python scripts/validate_canonical.py`：通过，9 standards、12 sources、98 parameters、98 factors；本包未改Canonical。
- `python -m compileall -q apps packages scripts tests`：通过。
- `python -m pip check`：通过，无依赖问题。
- `python scripts/initialize_databases.py --output-dir <临时目录>`：通过，隔离创建catalog/user/records/projects四库；未新增迁移。
- GUI acceptance / 1.0、1.25、1.5缩放：未执行，本地缺少`PySide6`。
- Windows standalone构建：已尝试，因本地缺少`PyInstaller`失败，未生成构建产物；release archive审计和smoke启动因此未执行。
- `git diff --check`：提交前检查；最终结论以最终Head的检查结果为准。
- GitHub Actions：等待本包独立PR完成后验证Windows/Python 3.12 `Merge-ref Full Tests` 与 `PR-head Standalone Audit`；必须确认两项的`head_sha`等于最终PR Head。结果在最终交付回复记录，不将CI元数据反写到触发新Head的本文档。

## 5. 停止边界

UAT01-B达到实现状态后等待latest-head CI和独立验收，不合并本包PR。RS03-A USER UAT保持`PENDING`；PR #27继续`OPEN / UNMERGED`且只读；RS03-B `NOT STARTED`；GB/T 32151.34—2024继续为`NOT SUPPORTED`。独立验收通过并合并后，由用户先重新人工测试软件本体，再决定是否回到PR #27继续Excel工作。
