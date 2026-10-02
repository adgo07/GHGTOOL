# TASK_STATE

状态：**CURRENT STATE**
最后更新：2026-10-03（GHG-GOV-R1）

> 本文件是**当前状态文件**，不是历史流水账。
> 每次历史 FAIL / 返工 / PR head / 中间 SHA 的完整过程保存在 Git history 与 `docs/governance/*`，本文件不再复制。
> 一个稳定的当前断点只在“当前状态”“当前工作包”“最近验收”“下一步”四处同步。

## 1. 当前基线

| 项目 | 值 |
|---|---|
| 仓库 | `https://github.com/adgo07/GHGTOOL.git`（`adgo07/GHGTOOL`） |
| 默认分支 | `main` |
| 当前 base | 本分支创建时的 `origin/main`（以 Git 为准，不在本文件写死历史 SHA） |
| 当前任务分支 | `governance/consolidate-reference-standard-roadmap-and-current-state`（已推送到 `origin`） |
| PR | 需在 GitHub 手动创建（本机无 `gh`）：`https://github.com/adgo07/GHGTOOL/pull/new/governance/consolidate-reference-standard-roadmap-and-current-state` |
| Module ID | `qz.carbon_accounting` |
| `platform-lock.json` locked SHA | `Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`（`auto_upgrade=false`，本任务未修改） |
| 应用版本 | `1.1.0`（Windows V1.1.0） |
| Canonical | `data-source/carbon_accounting/catalog.json`（SQLite 由其构建） |

## 2. 当前产品阶段

- 阶段：**路线与治理收口完成，尚未启动任何 `GHG-RS` 产品阶段**。
- 当前唯一产品路线：`REFERENCE_STANDARD_ROADMAP.md`（`GHG-RS01` ～ `GHG-RS06+`）。
- 参考标准总体状态：**`PARTIAL`**（缺口：结果解释集中收口、Excel 正式闭环）。

## 3. Reference Standard 状态

| 项目 | 值 |
|---|---|
| 当前 Reference Standard | `GB/T 32151.34—2024` |
| 通用规则层 | `GB/T 32150—2025` |
| 当前完整可计算行业标准 | 仅 `GB/T 32151.34—2024` |
| 其他计划标准 | 仅目录与状态信息（catalog-only） |
| 中央 Standard Development Guide 支持状态 | 尚未达到 `SUPPORTED`；须经 `GHG-RS01`～`GHG-RS05` 后由 RS05 判定 |

## 4. 当前已完成的重要能力（摘要）

- 标准库：目录、详情、官方来源与适用范围治理；可核算入口仅对 GB/T 32151.34 开放。
- 参数与因子库：Canonical → `catalog.sqlite` 的来源、版本、trace 与展示。
- 新建核算：字段语义层、类型化输入、排放源卡片、渐进展示、多燃料与多电力明细、核算周期、核算单元。
- 校验与计算：业务/致命校验 → `CarbonMaterialCalculator`（GB/T 32150—2025 + GB/T 32151.34—2024）→ 分项与总排放。
- 记录：成功计算立即新增不可编辑 Record；参数/规则/输入/结果快照与审计；历史只读查看；删除二次确认并留审计。
- Project：独立 `projects.sqlite` 的本地项目保存、打开、多核算单元与未完成输入跨启动恢复；与 `records.sqlite` 严格分离。
- Windows：PyInstaller onedir 便携式交付基线，发布审计、归档校验与启动 smoke。
- 数值平台：Numeric Contract v1 compatibility/adoption（`GHGTOOL_CARBON_DECIMAL40_CURRENT`，declared-profile consistency、ambient independence、exact comparison）。
- 治理：中央治理接入与 locked baseline、Numeric v1 adoption、参考标准 Roadmap、Standard Issues 台账、UI 现状盘点。

## 5. 历史里程碑（精简）

```text
G00-G08                              complete（Windows V1 分阶段交付，均经独立验收）
UIR01-UIR04                          complete（新建核算 UI 重构，均经独立验收）
Post-V1 Project persistence          complete（PR 已合并）
CATUI01                              complete（标准库页面收口，PR 已合并）
N01-C / R1                           PASS（Numeric / Unit / Quantity 试点）
Numeric Contract v1 adoption         PASS（locked baseline 升级并 adopted）
Governance streamline                complete
GHG-GOV-R1                           in progress（本次：路线与治理收口）
```

详细验收过程、历史 FAIL、返工记录与中间 PR head 见 Git history 与 `docs/governance/*`。

## 6. 当前工作包

**GHG-GOV-R1 — Reference Standard Roadmap Consolidation & Repository Governance Cleanup**

范围：

- 只修改治理文档、路线、当前状态文件与 README / 导航类说明；
- 建立唯一当前产品路线（`REFERENCE_STANDARD_ROADMAP.md`，GHG-RS01～RS06+）；
- 清理陈旧状态、失效规则、历史绝对路径、重复叙事与过度审批要求。

明确不做：Calculator / Canonical / Rule / SQLite / Excel / UI 业务语义 / 标准解释的修改；不启动 GHG-RS01。

## 7. 当前 Roadmap 阶段

- 已完成阶段：无（GHG-RS 系列尚未启动）。
- 下一正式阶段：**GHG-RS01 — GB/T 32151.34 完整参考标准业务收口**。
- RS01 前置：仓库内需有当前可追溯的 `GB/T 32151.34—2024` Standard Mapping；若尚未纳入仓库，先作为 RS01 第一个工作包。

## 8. 已知 blocker

- 无阻塞当前治理任务的问题。
- 环境事实（不属于产品阶段，不阻塞路线）：正式验证证据可来自本地测试或 GitHub Actions（Windows / Python 3.12）；报告须如实区分来源。本机对 Python 子进程在已存在的 `build/`、`*/__pycache__/` 目录内的写入有限制，`compileall` 需通过 `PYTHONPYCACHEPREFIX` 改写缓存目录，详见 `IMPLEMENTATION_REPORT.md` §7。

## 9. 最近一次正式验收状态

| 项目 | 状态 |
|---|---|
| 最近已完成的正式产品阶段 | Post-V1 治理与 Numeric v1 adoption（均已合并进入 `main`） |
| 当前任务的验收状态 | 待独立验收（本任务完成后停止） |
| 本任务实施报告 | `IMPLEMENTATION_REPORT.md`（本工作包报告） |

## 10. 下一步

1. 等待本次治理收口任务（GHG-GOV-R1）的独立验收。
2. 验收通过后，由用户明确启动 **GHG-RS01**；启动时重新读取 `AGENTS.md`、`REFERENCE_STANDARD_ROADMAP.md`、`HANDOFF.md`、`TASK_STATE.md` 与 `STANDARD_ISSUES_REGISTER.md`，并创建一个 Goal。
3. 不得在本任务或后续任务中提前实施其他 `GHG-RS` 阶段或第二标准。
