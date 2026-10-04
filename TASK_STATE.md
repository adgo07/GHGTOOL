# TASK_STATE

状态：CURRENT STATE；更新：2026-10-04。

## 当前工作包与基线

- 仓库：adgo07/GHGTOOL；origin 已核实为 https://github.com/adgo07/GHGTOOL.git。
- 工作包：GHG-RS02-A — Record Evidence & Reporting Data Closure。
- Base / origin/main：8724a39cb7139aa9ae5eeeee9db7455e8be5a939，包含已合并的 RS01-B2 / PR #24。新分支 codex/ghg-rs02-a-record-evidence-closure 从该 main 创建；初始工作区干净。
- platform-lock.json SHA-256：4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D；中央 Frozen 锁定 SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20 未升级。
- 平台预检查：Architecture V2.1、Numeric Contract v1、Numeric Profiles v1 为锁定 Frozen；Workspace/Attempt/Record/Result v1 仍为 DRAFT。本地扩展不宣称为中央 Record Contract；本任务不修改中央 Contract、baseline 或 platform-lock。
- 标准问题：保留 4 条历史 RESOLVED 执行口径；未改变标准解释、未新增标准问题；GAP-009 继续保留为非阻塞 provenance debt。

**RS02-A 实施与本地可执行验证已完成，等待本分支 PR 的 latest-head Windows CI 与独立重新验收。RS02-B NOT STARTED；不合并 PR。**

## 已交付范围

- 在既有 AccountingRecord / records.sqlite 上新增只增列迁移，保存新 Record 的 Trace、Provenance、报告/证据数据和报告周期资格快照；不回填、不重算、不修改历史记录。
- 新 Record Trace 固化稳定过程实例身份、公式步骤、变量、参数/因子引用与快照、标准/Mapping/Rule 定位、分项/小计和 ES/EI/ET；提供仅读取 Record 快照的汇总算术核验。
- Provenance 保存标准与冻结 Mapping 版本、算法、规则集身份、参考数据稳定身份及 Numeric Profile 来源。可复用活动数据/实测因子证据与输入建立关联；可选报告主体和说明沿用既有 Project 表单状态。
- 月度/自定义周期仍可计算并保存 Record；另存年度标准报告资格 ERROR，不混入 Calculator 致命校验。年度周期不产生该资格错误。
- 历史详情使用 Record 自身快照；无完整 Trace 显示“该记录生成时未保存完整计算过程快照。”，其他缺项显示“历史记录未保存该信息。”；不通过当前 Catalog 补旧值。
- Coverage Audit 覆盖 27 项，分类计数及落点已写入审计文件。CORE_CHECK Matrix 保持 26 行，更新为 OK 23、GAP 0、later-stage 3、独立 N/A 0。GAPS / GAP-009 未改动。

## 本地验证

- 定向：tests.test_rs02_record_evidence + tests.test_g06_carbon_material，28/28 通过。
- 全量：python -m unittest discover -s tests -t . -v；本机运行 135 项，11 个测试模块因运行环境缺 PySide6 而在导入时 ERROR；未将其计为通过。Windows/Python 3.12 PR CI 负责完整 GUI 与全量回归。
- Canonical：python scripts/validate_canonical.py 通过，9 standards、12 sources、98 parameters、98 factors。
- Python 语法：对 apps/packages/scripts/tests 下 83 个 Python 文件执行内存编译，全部通过；本机 compileall 写入 __pycache__ 受限。
- 依赖：python -m pip check 通过，No broken requirements found。
- git diff --check 通过（提交前再次执行）。
- PR latest-head Merge-ref Full Tests 与 PR-head Standalone Audit 尚待此分支 PR 创建后的 Actions；以最终 head SHA 检查，不引用旧 head 的 CI。

完成状态：GHG-RS02-A completed / awaiting independent acceptance。RS02-B NOT STARTED；标准状态 NOT SUPPORTED。
