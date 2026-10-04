# GHG-RS02-A — Record Evidence & Reporting Data Closure

状态：实施和本地可执行验证完成；等待本工作包 PR 最新提交的 Windows CI 及独立验收。RS02-B 未启动。本报告不写入自身所在提交的 Head SHA，最终验收对象由 PR 最新 Head 与 Actions 绑定。

## 1. 基线与平台预检查

- 仓库：adgo07/GHGTOOL；origin 为 https://github.com/adgo07/GHGTOOL.git。
- Base / origin/main：8724a39cb7139aa9ae5eeeee9db7455e8be5a939，包含 PR #24 合并结果。
- 分支：codex/ghg-rs02-a-record-evidence-closure，从当时同步的最新 origin/main 创建；初始工作区干净。
- platform-lock.json SHA-256：4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D；locked Central SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20 未改变。
- 按 locked SHA 对照 Architecture V2.1、Numeric Contract v1、Numeric Profiles v1 Frozen 要求。Workspace/Attempt/Record/Result v1 为 DRAFT / NOT YET RELEASED；仅作为兼容参考。本地快照不宣称为中央 Contract。本任务不涉及中央公共 Contract，不改 baseline。
- 标准问题台账：沿用 4 条历史 RESOLVED 决策，不改变任何标准解释；未新增 Standard Issue；GAP-009 provenance debt 保持开放且非阻塞。

## 2. 实际变更与范围

- 在修改业务实现之前创建 GB_T_32151_34_2024_RS02_COVERAGE.md。逐项核对第6章、第7.1—7.6、附录B.1—B.9、必要附录D/E；正式标准 PDF 仍在仓库外。
- Coverage Audit 共27项：EXISTING 12、DERIVED 1、SOFTWARE_DATA 11、ENTERPRISE_OFFLINE 1、RS02-B 1、LATER_STAGE 1。11项 SOFTWARE_DATA 均在本包建立本地结构化落点；企业制度、人员责任、设备维护仍按线下管理归类。
- 新增 migrations/records/003_rs02_record_evidence.sql，仅给 records 表增加四个 JSON 快照字段；无旧行 UPDATE、backfill 或破坏性 Project migration。
- 输入与证据：扩展标准单元输入，结构化保存可选报告主体/边界/产品工艺/排放源说明；可复用活动数据与实测因子证据块通过引用关联输入和新 Record。标准默认值使用已有标准来源，不要求企业重复登记。
- Trace：新 Record 写入本地 trace schema v1，含来源/过程 instance identity、公式步骤、输入变量、参数引用和使用快照、标准条款/Mapping位置、Rule、逐项结果/小计、ES/EI/ET 与 calculation lines。
- Provenance：保存标准及版本、Mapping 版本、算法版本、有效规则集快照/身份、当次 Catalog/reference-data 稳定身份、Numeric Contract/Profile 的本地来源信息；没有新增中央公共字段或 Frozen Contract。
- 历史核验：新增 record-only 汇总验证器，读取已保存的 CalculationResult lines 和 Trace 汇总值，核对分项小计与 ES/EI/ET；不运行当前 Calculator，不查询 Catalog。
- 年度报告资格：实现 CAR-VAL-ANNUAL-REPORT-PERIOD 的独立 report qualification。MONTHLY/CUSTOM 仍可计算并新增正式 Record，同时持久化 eligibility=false 与资格 ERROR；ANNUAL 不产生该资格 ERROR。资格校验不进入 Calculator fatal errors。
- 历史详情：仅从 Record 快照渲染；缺 Trace 明示“该记录生成时未保存完整计算过程快照。”，其他缺项显示“历史记录未保存该信息。”。不从当前 Catalog 填补旧 Record。普通视图不展示内部证据 ID。
- Project 兼容沿用既有 form_state，无 Project migration；保留原输入。soft delete/audit 既有机制不改。完整结果页与 B.1—B.9 UI、报告导出留给 RS02-B 或后续路线。

## 3. 测试、数据契约与治理同步

- 新增/强化测试覆盖：Trace/Provenance/报告数据持久化与重开；实例身份；记录仅使用自身快照进行算术核验；Catalog/reference identity 保存；月度/自定义资格与年度对照；fatal error 不生成 Record；旧 Record 缺少 Trace 的兼容路径；Project form-state 保存恢复；历史展示禁查 Catalog。
- 修正影响到的 UI / Record / Project / Domain 测试纳入 PR-head Windows CI；未修改 Canonical 数据、计算公式、Numeric Contract、Catalog schema、项目生命周期或多行结构。
- 完整结果页和报告解释呈现归 RS02-B；RS02-B NOT STARTED。未启动 Excel、Golden Freeze、Formal Support、Release 或第二标准。
- CORE_CHECK Matrix 为26行：OK 23、GAP 0、later-stage 3（RS02-B 1、RS03 1、RS04 1）、独立 N/A 0；审计行状态依据实现证据更新。GAPS 未修改，GAP-009 继续 non-blocking provenance debt。
- Roadmap、HANDOFF、TASK_STATE、IMPLEMENTATION_REPORT 与 CORE_CHECK / RS02_COVERAGE 已同步 RS02-A completed / awaiting acceptance。整体标准仍 PARTIAL，不宣称 SUPPORTED。

## 4. 本地验证结果

- 定向命令：python -m unittest tests.test_rs02_record_evidence tests.test_g06_carbon_material -v；28/28 通过。
- 全量命令：python -m unittest discover -s tests -t . -v；在当前 bundled Python 3.12 环境运行到 135 项，11 个依赖 PySide6 的测试模块因 ModuleNotFoundError: No module named PySide6 在导入时失败。故本机全量回归未通过/未完成，不把它记为实现失败或通过；要求由 Windows/Python 3.12 CI 覆盖。
- Canonical：python scripts/validate_canonical.py 通过，9 standards、12 sources、98 parameters、98 factors。
- Compile：对 apps/packages/scripts/tests 下 83 个 Python 文件执行 compile(source, filename, exec) 内存语法编译，全部通过。compileall 无法写入环境受限的 __pycache__，因此不宣称 compileall 已通过。
- Dependencies：python -m pip check 通过，No broken requirements found。
- 新增 SQLite 记录迁移由定向持久化测试实测：创建新 Record、关闭/重开存储并比较 trace/provenance/reporting/qualification 快照通过；没有执行独立的空数据库重建专项。
- git diff --check 在提交前执行；最终 PR-head CI 结果以 GitHub Actions 绑定的 exact head 为准。

## 5. 完成与停止边界

GHG-RS02-A 实施完成，等待独立重新验收。本包不合并 PR；RS02-B NOT STARTED；GB/T 32151.34—2024 标准状态 NOT SUPPORTED。
