# IMPLEMENTATION_REPORT

任务：**GHG-GOV-R1 — Reference Standard Roadmap Consolidation & Repository Governance Cleanup**
任务性质：治理收口 / 路线修正（不修改正式业务代码）
报告日期：2026-10-03

> 本文件是**当前/最近一个正式工作包的实施报告**，不是历史任务的永久追加日志。
> 历史任务的报告由 Git history 与 `docs/governance/*REPORT.md` 保存，不再向本文件追加。

## 1. Baseline

| 项目 | 值 |
|---|---|
| repository | `https://github.com/adgo07/GHGTOOL.git`（`adgo07/GHGTOOL`） |
| default branch | `main` |
| base SHA | `cae2ff33b2f09d115db950fae4b0829f698ec8fa`（本分支创建时的 `origin/main`，`git fetch origin` 后确认） |
| execution branch | `governance/consolidate-reference-standard-roadmap-and-current-state` |
| execution head | 见 PR / 交付回执（本报告提交后由最新 PR head 确认） |
| changed files | `AGENTS.md`、`HANDOFF.md`、`TASK_STATE.md`、`IMPLEMENTATION_REPORT.md`、`REFERENCE_STANDARD_ROADMAP.md`、`README.md`、`UI_CURRENT_STATE_AUDIT.md` |

范围：只修改治理文档、路线、当前状态文件与 README / 导航类说明。**未修改任何业务代码、Calculator、Canonical、SQLite schema/迁移、Excel、UI 业务语义或标准解释。**

## 2. Before — 本任务发现的主要陈旧 / 冲突类别

不逐条列历史 SHA，只列类别：

1. **历史绝对路径作为当前身份**：`HANDOFF.md` 把 `D:\project\碳排放核算工具`、`D:\MD仓库\...` 等写成当前项目目录与必读文件路径，与 `AGENTS.md §1.1`（绝对路径不是仓库身份）冲突。
2. **多份文件同时声称“当前唯一基线”**：`HANDOFF.md` 自称“唯一当前交接基线”，`TASK_STATE.md` 又在正文中承载全部历史状态，`IMPLEMENTATION_REPORT.md` 承载全部历史任务，彼此口径不一致且无权威顺序。
3. **旧数据库模型表述**：“三个物理隔离的 SQLite 数据库”已成为旧口径；当前实际为 `catalog` / `user` / `records` / `projects` 四库（`projects.sqlite` 由 Post-V1 批准引入）。
4. **Project 保存的旧禁令**：旧正文写“不实现项目文件入口，不实现保存项目，不实现草稿”，与当前已批准的 `projects.sqlite` 本地项目保存、跨启动恢复冲突。
5. **Excel 永久 OUT OF SCOPE 的旧表述**：与中央 Product Delivery Policy 已把 Excel 定为 Reference Standard 后续正式闭环冲突。
6. **历史 Numeric / Unit 旧口径风险**：旧正文把 `44/12` 与普通单位换算并列出现在同一批单位定义语境中，容易被读成 ordinary unit conversion。
7. **历史状态膨胀**：`TASK_STATE.md`（约 160 KB）与 `IMPLEMENTATION_REPORT.md`（约 190 KB）成为历史流水账，包含大量已失效的 FAIL/返工/中间 PR head/“PR 未合并”等文字。
8. **过度人工审批**：旧规则容易演变为“普通 UI 文案、删除内部编号、治理旧路径、结果区排版”等事项都要停下来请求产品负责人批准。
9. **SHA 流程仪式**：旧纪律要求反复记录最近若干 commit、历史阶段 SHA 与本地中央 clone 差异。
10. **UI 盘点被隐含升格为路线**：`UI_CURRENT_STATE_AUDIT.md` 的登记项（`GHG-UI-001` ～ `005`）缺少与产品阶段的明确归属。
11. **路线缺位**：仓库没有统一的后续产品路线；G00～G08 的 9 月计划仍被当作“当前完整产品路线”。

## 3. Authority model after cleanup

merge 后权威层级与冲突顺序如下（同时写入 `AGENTS.md`、`REFERENCE_STANDARD_ROADMAP.md`、`HANDOFF.md`）：

| 层级 | 文件 | 管什么 | 读取方式 |
|---|---|---|---|
| 中央 Frozen 基线 | `platform-lock.json` + `PLATFORM_BASELINE.md` | 锁定的中央 Frozen Contract / Architecture / Conformance 与 Carbon Numeric Profile | 按 locked SHA 读中央 Frozen 权威文件 |
| 中央 ACTIVE 指南 | 中央 `GUIDE_INDEX` / `PRODUCT_DELIVERY_POLICY_V1` / `STANDARD_DEVELOPMENT_GUIDE_V0.1` / `UI_DESIGN_GUIDELINES_V0.1` | 怎么做、按什么流程做 | 按中央当前正式合并版本读取；**不是 Frozen Contract** |
| 本仓长期硬规则 | `AGENTS.md` | 仓库身份、产品边界、架构、Numeric/Unit、Workspace/Record、执行授权 | 长期有效 |
| 本仓当前产品路线 | `REFERENCE_STANDARD_ROADMAP.md` | 唯一当前产品级路线（GHG-RS01～RS06+） | 唯一路线，不得建平行文件 |
| 本仓当前阶段交接 | `HANDOFF.md` | 当前阶段的实施范围与门禁 | 当前阶段说明 |
| 本仓当前执行状态 | `TASK_STATE.md` | 当前基线、阶段、工作包、blocker、最近验收、下一步 | 当前状态 |
| 本仓当前实施报告 | `IMPLEMENTATION_REPORT.md` | 当前/最近一个正式工作包 | 每阶段重写 |
| 标准问题台账 | `STANDARD_ISSUES_REGISTER.md` | 标准原文事实 / 技术判断 / 软件实现决定 | 长期保留 |
| 历史证据 | Git history、`docs/governance/*`、`UI_CURRENT_STATE_AUDIT.md` | 历史与专项证据 | 只作证据，**不得覆盖当前状态** |

冲突处理顺序：locked Frozen Contract → 中央 ACTIVE 指南 → `AGENTS.md` → `REFERENCE_STANDARD_ROADMAP.md` → `HANDOFF.md` / `TASK_STATE.md`。历史证据不参与当前口径裁决。

## 4. Roadmap

`REFERENCE_STANDARD_ROADMAP.md` 已成为本仓**唯一**当前产品级后续路线：

| 阶段 | 一句话目标 |
|---|---|
| `GHG-RS01` | GB/T 32151.34 完整参考标准业务收口（Standard Completeness Matrix，回答标准要求的软件业务能力是否完整落地） |
| `GHG-RS02` | 生命周期 / Record / 结果解释 / Trace 最终闭环（结果可追溯、可复现、可解释，历史不漂移） |
| `GHG-RS03` | Excel 正式闭环（Excel 作为同一业务内核的 Import / Export Adapter） |
| `GHG-RS04` | Golden / Formal Support Candidate Gate（用权威 Golden Case 证明正式支持条件，达到 `READY_FOR_RELEASE`） |
| `GHG-RS05` | Windows 正式版 Release Gate（证明完整产品可作为正式 Windows 产品交付，之后才可标记正式支持状态） |
| `GHG-RS06+` | 第二标准及后续演进（同时承担架构扩展验证；不得早于 RS05） |

同时明确：

- 本地 Python 环境修复属于 **Development Environment Maintenance**，不是 `GHG-RS00`，不进入路线编号，也不阻塞路线；
- RS01 不得被缩窄为“只改结果解释 UI”；正确规则是“没有证据时不得顺手改；发现真实标准功能缺陷时必须修”；
- Standard Mapping 是 RS01 Standard Completeness Matrix 的正式输入；若尚未纳入仓库，标为 RS01 明确前置工作；
- Golden 明确纳入 RS04；第二标准明确不得早于 RS05；
- 第三方提案（S0～S6）只作为修正输入，其合理内容已吸收进 `REFERENCE_STANDARD_ROADMAP.md`，未建立任何平行路线文件。

## 5. Removed / corrected obsolete rules

| 类别 | 处理 |
|---|---|
| 历史绝对路径（`D:\project`、`D:\MD仓库`） | 从当前正文移除；`AGENTS.md` 增加“不得写进当前治理正文”的规则，历史路径只允许作为历史证据 |
| Project 保存旧冲突 | 统一为“**项目保存与 `.qzproj` 是两件事**”：`.qzproj` 仍不提供；`projects.sqlite` 本地项目保存与跨启动恢复已支持；可变状态不得混入 `records.sqlite` |
| 数据库数量旧表述 | 由“三个物理隔离数据库”修正为实际四库：`catalog` / `user` / `records` / `projects` |
| Excel V1 OUT OF SCOPE 与未来 Roadmap 的区别 | 明确“当前未实现、仅占位”与“RS03 正式闭环”是同一能力的不同阶段状态，避免被读成永久排除 |
| `44/12` / `44/16` / GWP 口径 | 统一为 Numeric Contract v1 语义：quantity transformation + stoichiometric/standard-formula coefficient / characterization-equivalence factor，**不是** ordinary unit conversion |
| 历史 PR / SHA 噪声 | 从当前状态文件移除；`AGENTS.md §12` 明确保留与不再作为长期负担的两类 SHA |
| 人工审批过度 | `AGENTS.md §11` 新增“可直接执行（无需逐项批准）”清单与“必须停止并询问”的 8 类条件 |
| HANDOFF / TASK_STATE / IMPLEMENTATION_REPORT 历史膨胀 | HANDOFF 重写为当前阶段交接；TASK_STATE 重写为当前状态文件 + 精简里程碑表；IMPLEMENTATION_REPORT 重写为本工作包报告，并确立“每阶段重写、不无限追加”的规则 |
| G00～G08 阶段正文与失效验收门禁 | 从当前正文移除（Git history 保存）；仅保留精简里程碑摘要 |
| UI 盘点项缺少归属 | 在 Roadmap 第 9 节建立 `GHG-UI-001`～`005` 与 RS01/RS02/RS03/技术债的归属；不再规划 UIR05～UIRxx |
| 路线缺位与平行路线风险 | 建立唯一 Roadmap，并在 `AGENTS.md` 明确禁止平行路线文件 |
| README | 同步当前 Reference Standard、支持状态、Windows 交付状态、Excel 当前状态与下一产品阶段；未提前宣称“完整正式支持” |

## 6. Preserved evidence

以下资产**未删除、未重写为历史替代品**：

- `platform-lock.json`、`PLATFORM_BASELINE.md`（locked SHA 与 Carbon Numeric Profile 未变）；
- `STANDARD_ISSUES_REGISTER.md`（保持 `ACTIVE REGISTER`，当前登记数量仍为 0，未人为制造问题）；
- `UI_CURRENT_STATE_AUDIT.md`（保留为专项 UI 盘点证据，只新增阶段归属说明，不升级为 Roadmap）；
- `docs/governance/NUMERIC_CONTRACT_V1_ADOPTION_REPORT.md`、`PLATFORM_ADOPTION_REPORT.md`、`QZC_N01_C*_EXECUTION_REPORT.md`（历史专项证据保持原状）；
- `docs/decisions/DEC-2026-09-13-multi-source-electricity.md`、`docs/DELIVERY.md`；
- `conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json` 与全部 Canonical / standard source；
- `knowledge/` 落点；
- G00～G08、UIR01～UIR04、Post-V1、N01-C/R1、Numeric v1 adoption 的全部历史记录（Git history 与既有报告）。

## 7. Tests

本任务只修改 Markdown 治理文档，测试的目的是证明治理清理未误伤产品。

### 7.1 本地实际执行（EXECUTED）

环境：本地新建 Python **3.12.14** 虚拟环境（`uv venv --python 3.12 .venv`，`uv pip install -e .`，PySide6 6.11.2）。`.venv/` 已在 `.gitignore` 中，未纳入提交。

| 命令 | 结果 |
|---|---|
| `python -m unittest discover -s tests -t . -v` | **Ran 214 tests — OK，0 失败、0 错误、0 跳过**（68.740 s，exit 0） |
| `python scripts/validate_canonical.py` | `valid: 9 standards, 12 sources, 7 parameters, 7 factors` |
| `python scripts/initialize_databases.py --output-dir tmp/ggh-gov-r1/dbs` | `catalog` / `user` / `records` / `projects` 四库从零重建成功 |
| `python scripts/uir04_manual_gui_acceptance.py` | 场景 A～E 全部 PASS（exit 0） |
| `python scripts/uir04_scale_acceptance.py --scale 1.25` | PASS：1366×768 控件可见且无横向滚动 |
| `python scripts/uir04_scale_acceptance.py --scale 1.5` | PASS：1366×768 控件可见且无横向滚动 |
| `python -m unittest tests.test_g08_delivery` | Ran 10 tests — OK |
| `uv pip check` | All installed packages are compatible |
| `python -m compileall -q apps packages resources scripts tests` | **exit 0（129 个 .pyc 全部生成）**，但必须先设置 `PYTHONPYCACHEPREFIX` 指向工作区内的新目录；直接写入工作区已有 `__pycache__` 会收到环境写入限制（见 7.2） |

**环境限制说明（如实记录，不冒充成功）**：本机对 Python 子进程在**已存在的** `build/`、`*/__pycache__/` 目录内创建或改名文件返回 `Permission denied`（`build/probe.tmp`、`packages/__pycache__/probe.tmp` 均失败，而新建目录 `tmp/probe-dir` 成功）。这是**本机执行环境限制**，不是仓库缺陷，也不是本任务引入的回归。因此：

- `compileall` 通过 `PYTHONPYCACHEPREFIX` 改写到新建目录后 exit 0；
- 数据库从零初始化改写到 `tmp/` 下成功；
- 其余验证均为直接执行结果。

### 7.2 GitHub Actions（待最新 PR head）

```text
GitHub Actions (Windows / Python 3.12):
EXECUTED — 见本任务 PR 最新 head 的 Windows CI（merge-ref full tests + exact PR-head standalone audit）。
```

`windows-ci.yml` 实际执行的检查：Canonical validation、`compileall`、`pip check`、四库从零初始化、UIR04 GUI 验收场景 A～E、1.25 / 1.5 缩放验收、全量 `unittest discover`、G08 delivery tests、standalone 构建、发布审计、归档清单校验、provenance 校验、启动 smoke。

范围证据：`git diff --name-only` 确认改动仅限 Markdown 治理文档，未触及 `apps/`、`packages/`、`migrations/`、`scripts/`、`tests/`、`data-source/`、`conformance/`。

本地临时产物（已清理，不进入提交）：`tmp/ggh-gov-r1/`、`.venv/`。

## 8. Next step

> **GHG-RS01 — GB/T 32151.34 完整参考标准业务收口**

本 PR 不启动 RS01，不修改 Calculator / Canonical / Rule / Database / Excel / UI 业务语义，完成后停止等待独立验收。

## 9. 本任务发现但不在本任务修改的问题

| 发现 | 证据 | 分类 | 为什么不在本任务修改 | 建议去向 |
|---|---|---|---|---|
| 本机 Python 子进程对已存在 `build/`、`*/__pycache__/` 目录的写入限制 | 见 §7.1 环境限制说明 | Development Environment Maintenance | 不属于产品路线阶段，且已通过 `PYTHONPYCACHEPREFIX` 与 `tmp/` 输出目录绕过 | 独立环境修复工作（不占路线编号） |
| 中央 `D-011`（Quantity / coefficient 公共边界）与 Excel lossless ingress 仍 OPEN | 中央 `DECISIONS_NEEDED.md`、`NUMERIC_CONTRACT_V1_FROZEN.md` §16 | `CENTRAL CONTRACT GAP` | 本仓不得私自冻结公共规则 | RS03 中如实标 `OPEN` / `PARTIAL`，必要时形成 RFC Candidate 返回中央 |
| 中央 `D-013`（Presentation State vs Business Workspace）仍 OPEN | 中央 `DECISIONS_NEEDED.md` | `CENTRAL CONTRACT GAP` | 不要求返工现有 `projects.sqlite` | Workspace Contract 阶段处理 |
| `GHG-UI-004`（`AppRoute` 展示结构硬冻结） | `UI_CURRENT_STATE_AUDIT.md` | 非阻塞技术债 | 本任务不改业务代码 | 适当 UI 工作包内解除 |

以上均**未阻塞**本任务建立一致 Roadmap。
