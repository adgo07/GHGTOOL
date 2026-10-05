# GHG-RS03-A-R1 — Excel 模板简化与用户验收候选版

状态：`RS03-A-R1 IMPLEMENTED`；`TECHNICAL ACCEPTANCE PENDING`；`USER TEMPLATE UAT PENDING`。PR #27 保持开放、不合并。RS03-B `NOT STARTED`；GB/T 32151.34—2024 仍为 `NOT SUPPORTED`。

## 基线与平台预检查

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- Base / `origin/main`：`058d176a8a461b758db1a1d62395b032889d9b2a`。
- R1 起始 head：`10c13871a4b7d12985b0d9cf8510c5d970b49394`；本轮最终 PR head 及 exact-head CI 以 PR #27 当前最新 head 和完成回复为准。
- 分支：`codex/ghg-rs03-a-excel-ingress`；PR #27：GHG-RS03-A，未合并。此工作包没有另开 PR。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定 SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 未改变。
- Architecture V2.1、Numeric Contract v1、Numeric Profiles v1 使用锁定 Frozen 版本。Excel / openpyxl Decimal ingress 仍为中央 OPEN；本任务只沿用本地入口策略，不改变 Frozen Contract 或 baseline。
- 无新增标准问题；沿用冻结 Mapping、标准公式与现有 Calculator。未修改标准适用范围或正式业务解释。

## 实际改动

- 将模板收敛为四个可见页签：`填写说明`、`核算单元`、`燃料与能源`、`过程排放`；保留隐藏 `__metadata__`。移除独立排放源、报告信息和证据登记表。项目企业/期间/公共边界只录一次，核算单元清单按行维护。
- 燃料与能源页按 B.2、B.8、B.9 分区；过程排放页按 B.3–B.7 分区。物料、电力和热力可按标准行式输入；B.3–B.5 使用新增纯 Python Decimal 加权归一化模块构造现有 Domain 输入，没有加入 Excel 业务公式或第二套 Calculator。
- 排放源状态根据有效业务数据行派生；错误输入使对应启用单元失败。停用、未知和未关联数据提示并忽略。预览增加燃料、生产过程、烟气治理、购入电力/热力、输出能源抵扣分项，并保留直接、净间接与总排放结果。
- 标准 C.1/C.2、K1/K2/K3、脱硫缺省继续通过 Canonical resolver 取得。C.2 11 项完整因子、未知碳酸盐阻断、来源追溯、C.4/C.5 查表锚点均有测试；C.4/C.5 仍由既有版本化 Domain Calculator 负责。
- 新增忽略目录中的 UAT 候选模板 `GB_T_32151_34_2024_Excel模板_UAT.xlsx`，由最终模板生成器生成并自带简明用户步骤；此文件不提交仓库。没有修改 `计算表/`、Canonical 数据、数据库迁移或 `platform-lock.json`。
- 同步 Excel Schema、入口策略、Roadmap、TASK_STATE、HANDOFF 与 UI audit；RS03-B 保持未启动。

## 测试变更与验证

**数据 / 契约变化：**本包未增改 Canonical 参数或因子，不涉及数据集计数变化。模板机器结构收敛为四个可见页签，Excel Schema 已同步。

**行为预期变化：**替换了与旧 14 页模板和人工排放源状态绑定的 Excel 测试，改为直接录入新四页模板；验证派生状态、来源行、单元隔离和分项预览。没有改动计算公式以迎合测试。

**本地验证（Windows / Python 3.12.14）：**

- 定向：`python -m unittest tests.test_excel_rs03_a tests.test_g03_shell -v`，22/22 通过。
- 全量：`python -m unittest discover -s tests -t . -v`，259/259 通过。
- Canonical：`python scripts/validate_canonical.py` 通过：9 standards、12 sources、98 parameters、98 factors。
- 编译：`python -m compileall -q apps packages resources scripts tests` 通过。
- 依赖：`python -m pip check` 通过，无损坏依赖。
- 隔离数据库重建：`scripts/initialize_databases.py --output-dir build/databases/rs03-a-r1-check` 成功生成 catalog/user/records/projects 四库。
- UI acceptance：`scripts/uir04_manual_gui_acceptance.py` 的 A–E 五项通过；`scripts/uir04_scale_acceptance.py --scale 1.25` 和 `--scale 1.5` 均通过。
- Standalone：Windows onedir 构建成功；构建脚本内置 release audit 与上传 ZIP 往返审计通过；`scripts/smoke_standalone.py` 两次隔离启动通过。最终提交后会再次构建，以便本地 release provenance 指向提交代码。
- `git diff --check`：通过。

以上均为本地证据，不代表 GitHub Actions。推送后必须确认 PR #27 最新 head 的 Windows/Python 3.12 `Merge-ref Full Tests` 和 `PR-head Standalone Audit` 均 success，且 CI `head_sha` 等于最终 PR head。CI run 与 head 在最终完成回复中记录，避免把 CI 元数据写入会触发新一轮 CI 的提交。

## 停止边界

完成本地实施后停在 `RS03-A-R1 IMPLEMENTED`。等待 exact-head CI、独立技术验收和用户打开候选 Excel 的 UAT；不合并 PR #27，不启动 RS03-B，不冻结 Golden，不宣称标准 `SUPPORTED`。
