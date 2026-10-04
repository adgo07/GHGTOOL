# GHG-RS03-A — Excel 模板、数值入口与多核算单元导入基础

状态：本地实施与本地验证完成；PR #27 保持开放等待独立重新验收。Windows/Python 3.12 exact-head CI 按最新 head 在 [PR Checks](https://github.com/adgo07/GHGTOOL/pull/27/checks) 跟踪；报告不记录自身所在提交 SHA，完成回复将给出最后通过的 run 与 `head_sha`。

## 1. 基线与平台预检查

- 仓库：`adgo07/GHGTOOL`；origin 已验证为 `https://github.com/adgo07/GHGTOOL.git`。
- Base：从最新 `origin/main` `058d176a8a461b758db1a1d62395b032889d9b2a` 新建 `codex/ghg-rs03-a-excel-ingress`；该 main 已含 PR #26 合并结果，分支起始干净。
- platform-lock.json SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定 SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变。
- Contract 预检查：Architecture V2.1、Numeric Contract v1 和 Numeric Profiles v1 按锁定版本为 Frozen；Excel / openpyxl Decimal ingress 词法互操作仍为中央 OPEN。本地策略未改变或覆盖中央 Contract，未升级 baseline / platform-lock。
- Standard Issue：无新增事项；沿用已批准 Mapping、公式和计算口径，本工作包未改变标准解释、计算公式或适用范围。GB/T 32151.34—2024仍为 `NOT SUPPORTED`。

## 2. 实际改动

- 新增 `packages/excel/gbt32151_34_v1.py` 纯 Python Excel adapter 和 `packages/excel/__init__.py`。运行时生成一个标准专用 `.xlsx` 模板；模板包含核算单元、明确排放源状态、报告信息、燃料、过程、烟气治理、电力、热力、共享证据和版本元数据工作表。没有把 `.xlsx` 资产或标准 PDF 放入仓库/安装包。
- 入口载入保留公式类型，并从工作表 OOXML 读取文件保存的数值词法后直接构造 Decimal，不经二进制浮点计算。只接受有限数值单元格；拒绝文本数字、公式、日期、非有限值及超过15位有效数字。0合法；比例按保存的`0..1`值解释，显示格式不决定含义；入口证据保留表、格、类型、库读值表示、序列化数值文本与Decimal。
- 同一工作簿支持多个全厂/工序/其他核算单元独立校验和预览。有效单元复用现有 `CarbonMaterialInput` 与 `CarbonMaterialCalculator`；一项失败不阻断其他有效单元，也不跨单元汇总。预览显示直接排放、净间接排放和总排放；不写Project、Workspace或正式Record。
- 新增运行时依赖 `openpyxl>=3.1.5,<4`。首页与导航Excel入口可操作；错误用中文显示，并保留工作表/单元格定位、隐藏内部校验码与 `CAR-*` ID。
- 新增 `specs/carbon_accounting/GHGTOOL_EXCEL_INGRESS_V1.md` 与 `GB_T_32151_34_2024_EXCEL_SCHEMA_V1.md`；同步 Roadmap、HANDOFF、TASK_STATE、UI Audit。RS03-B仍为 `NOT STARTED`。
- 本包未修改 Canonical、数据库迁移、计算器、标准 Mapping、核心业务包、Golden 或平台锁。Canonical仍为9 standards、12 sources、98 parameters、98 factors；计数没有改变。
- 用户提供的“碳谷 负极材料 计算表(2).xlsx”参考样表在当前仓库/文档执行环境未找到，未假称已读取，也未用于推导字段或标准含义；模板依据冻结标准Mapping、现有Canonical与当前Domain输入构造。

## 3. Excel / Calculator / 兼容性

- 模板 ID `GHGTOOL_GBT_32151_34_2024`，模板版本 `1.0.0`，标准 ID/版本来自现有标准目录，入口策略 `GHGTOOL_EXCEL_INGRESS_V1`；导入预览记录工作簿 SHA-256、模板/标准/策略版本与UTC导入时间。
- 燃料、过程、烟气治理、购入/输出电力和热力均映射既有 Domain 输入类型。过程行与来源明细逐条进入现有单元计算器；没有建立第二套公式。
- C.4/C.5 仍由既有版本化 `CarbonMaterialCalculator` 查表/插值；入口提供代表性锚点回归，没有新增 reference-table/DSL 架构，也没有更改冻结 Mapping 的C.4修正或标准解释。
- 标准参数和来源解析复用现有 ParameterResolver / Canonical；未扩大Canonical，不改变历史 Record，也不执行 Project 或 Record 迁移。预览采用内存结果，历史正式 Record 生命周期保持不变。
- UI 测试确认等价 GUI / Excel 输入使用相同 Calculator、结果和现有输入指纹；错误展示改为业务中文，工作簿单元格位置用于修正输入。

## 4. 测试变更分类

**数据 / 契约变化：**添加 openpyxl 依赖及模板/入口机器契约；Canonical 数据没有变更，所以没有因数据集扩大而修改任何标准数据计数断言。

**行为预期变化：**`tests/test_g03_shell.py` 将 Excel 入口从“暂未开放 / reserved”切换为启用的模板与导入预览，并更新首页文案、路由和控件断言；这是 RS03-A 新能力的预期行为。没有为测试通过而修改 Calculator 结果或公式。

**新验证：**`tests/test_excel_rs03_a.py` 覆盖运行时模板/元数据、数值单元格类型和OOXML词法、公式/文本/日期/非有限值拒绝、有效数字上限、零和比例语义、证据回链、多单元部分成功隔离、燃料 C.1 参数、完整 C.2 项目、C.4/C.5 锚点、GUI输入与Calculator parity、多燃料/过程/FGD/电力/热力明细、无持久化Record以及普通UI结果/错误呈现。

## 5. 本地验证

- 定向 RS03-A / G03 Shell：`python -m unittest tests.test_excel_rs03_a tests.test_g03_shell -v`；24/24通过。
- 全量回归：`python -m unittest discover -s tests -t . -v`；261/261通过，Windows / Python 3.12 / offscreen Qt。
- Canonical：`python scripts/validate_canonical.py` 通过（9 standards、12 sources、98 parameters、98 factors）。
- 编译：`python -m compileall -q apps packages resources scripts tests` 通过。
- 依赖：`python -m pip check` 通过；No broken requirements found。
- 隔离数据库：`scripts/initialize_databases.py --output-dir build/databases/rs03-a-check` 成功生成catalog、user、records、projects四库。
- UI：`scripts/uir04_manual_gui_acceptance.py` 场景 A—E 均 PASS；`scripts/uir04_scale_acceptance.py --scale 1.25`、`--scale 1.5` 均 PASS。
- 本地 Windows standalone 构建通过；发布目录审计 PASS（287 files）；ZIP往返审计 PASS（288 visible files）；standalone smoke PASS（2次隔离启动）。
- `git diff --check` 通过。
- 本地Python来自项目Python 3.12 venv；openpyxl 3.1.5由workspace bundled dependency path提供，PySide6与PyInstaller使用项目venv。以上均为本地运行结果，不冒充GitHub Actions。

## 6. 阶段边界与CI门禁

RS03-A使用新建的 PR #27，不复用此前PR且不合并。每个当前最新 `head_sha` 都必须有 Windows / Python 3.12 `Merge-ref Full Tests` 与 `PR-head Standalone Audit` 两项 Actions success，且 standalone provenance 指向精确PR head，才可停止并报告完成。GitHub执行状态只以PR当前Checks及完成回复记录，不将此前head结果当作新head证据。

PR保持开放等待独立验收。RS03-B `NOT STARTED`；本阶段不做正式Project / Record持久化、Excel导出、Golden Freeze、第二标准或 `SUPPORTED` 宣告。
