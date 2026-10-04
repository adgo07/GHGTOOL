# TASK_STATE

状态：GHG-RS03-A 实施与本地验证完成；PR #27 保持开放，latest-head CI 状态以 PR Checks 为准；等待独立重新验收。更新：2026-10-04。

## 当前工作包与基线

- 仓库：adgo07/GHGTOOL；origin 已核实为 `https://github.com/adgo07/GHGTOOL.git`。
- 工作包：GHG-RS03-A — Excel 模板、数值入口与多核算单元导入基础。
- Base：最新 `origin/main` `058d176a8a461b758db1a1d62395b032889d9b2a`；PR #26 合并结果已在该 main 中。
- 新分支：`codex/ghg-rs03-a-excel-ingress`，从该 Base 创建；任务工作树创建时干净。
- platform-lock.json SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定 SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 未升级。
- Contract 预检查：Architecture V2.1、Numeric Contract v1、Numeric Profiles v1 按锁定版本为 Frozen；Excel / openpyxl Decimal 词法互操作语义仍为中央 OPEN。本包使用本地入口策略，不升级 baseline / platform-lock，也不定义中央 Contract。
- 标准治理：沿用既有冻结 Mapping 与项目口径；未改变标准解释、计算公式或标准适用范围；无新增 Standard Issue。标准仍为 `NOT SUPPORTED`。

## 已完成范围

- 添加 `packages/excel/gbt32151_34_v1.py` 纯 Python 适配器和运行时模板；模板对应 GB/T 32151.34—2024，一个工作簿可登记多个独立全厂/工序/其他核算单元，不保存模板资产。
- 按已保存 OOXML 数值文本直接解析 Decimal；仅接受有限数值单元格，拒绝文本数字、公式、日期、非有限数、超过15位有效数字；保留工作表/单元格、类型、值表示、保存数值词法和 Decimal 入口证据。数值格式不改变比例语义。
- 单元级独立校验与部分成功预览；每个有效核算单元构造既有 `CarbonMaterialInput` 并交由既有 `CarbonMaterialCalculator`，展示直接、净间接与总排放。不同单元不互相汇总；不写 Project / Workspace / Record。
- 增加 `openpyxl` 运行依赖；首页和导航的 Excel 入口已从禁用占位改为运行时模板及导入预览入口。没有修改业务公式、Canonical 数据、数据库迁移、标准 Mapping、平台锁或 Frozen Contract。
- 新增 `specs/carbon_accounting/GHGTOOL_EXCEL_INGRESS_V1.md` 与 `GB_T_32151_34_2024_EXCEL_SCHEMA_V1.md`；Roadmap、HANDOFF、UI Audit同步至 RS03-A；RS03-B NOT STARTED。

## 本地验证

- RS03-A / Shell 定向：`python -m unittest tests.test_excel_rs03_a tests.test_g03_shell -v`；24/24 通过。
- 全量回归：`python -m unittest discover -s tests -t . -v`；261/261 通过（Python 3.12，Windows，offscreen Qt）。
- Canonical：`python scripts/validate_canonical.py` 通过；9 standards、12 sources、98 parameters、98 factors。
- 编译：`python -m compileall -q apps packages resources scripts tests` 通过。
- 依赖：`python -m pip check` 通过；No broken requirements found。
- 数据库：`scripts/initialize_databases.py --output-dir build/databases/rs03-a-check` 成功生成隔离的 catalog/user/records/projects 四库。
- UI acceptance：`scripts/uir04_manual_gui_acceptance.py` 场景A—E均PASS；`scripts/uir04_scale_acceptance.py --scale 1.25` 与 `--scale 1.5` 均PASS。
- Windows standalone：本地构建成功；`scripts/inspect_release.py` PASS（287 files），`scripts/verify_release_archive.py` PASS（288 visible files），`scripts/smoke_standalone.py` PASS（2次隔离启动）。
- `git diff --check` 通过。运行库为 Python 3.12 venv，加上本机 bundled dependency path 提供 openpyxl 3.1.5；PySide6 / PyInstaller 使用项目 venv。

## 停止边界

PR Checks 页面持续显示当前 head 的 Windows CI；每次推送均须以最新 head 两项 Windows/Python 3.12 workflow success 为验收证据。PR 保持开放等待独立验收；不合并PR，不进入RS03-B，不做Project / Record持久化、正式Excel导出或Golden Freeze。GB/T 32151.34—2024继续 `NOT SUPPORTED`。
