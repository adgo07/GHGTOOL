# PLATFORM_ADOPTION_REPORT

> 状态：**HISTORICAL-SUPERSEDED（QZC-A01 接入当时的上位基线记录）**
>
> 用途：Qingzhou-contracts 公共治理首次接入（QZC-A01）的历史 adoption 证据与当时的兼容差距记录
>
> 注意：不得作为当前正式规则依据。本报告记录的 `commit_sha: 0cd74d78…` 与“Numeric Contract 为 v1 DRAFT”属于 QZC-A01 历史口径；本仓其后已通过独立 Numeric Contract v1 compatibility/adoption 升级基线，`platform-lock.json` / `PLATFORM_BASELINE.md` 是唯一当前权威。
>
> 当前权威：根目录 `platform-lock.json`、`PLATFORM_BASELINE.md`、`docs/governance/NUMERIC_CONTRACT_V1_ADOPTION_REPORT.md`

## 1. 当前仓信息

```text
repo: adgo07/GHGTOOL
default_branch: main
adoption_base_head: bbc753c9ad5e662b9d294cda7611a1e4e4bf8dd8
adoption_branch: chore/qingzhou-contracts-adoption
adoption_pr: #14
adoption_date: 2026-09-28
current_stage: Post-V1；QZC-A01 只执行公共治理接入
```

本次上位基线：

```text
repository: https://github.com/adgo07/Qingzhou-contracts.git
release/tag: none
baseline_status: pre-release / bootstrap baseline
commit_sha: 0cd74d783fa23add6dc881b408a8c8ba8503f8e8
Architecture: V2.1 FROZEN
```

截至本次接入，Qingzhou-contracts 没有正式 release/tag。Numeric、Unit、Module / Capability、Workspace / Attempt / Record / Result、qzpack Contract 均为 **v1 DRAFT / NOT YET RELEASED**。本仓只锁定上述精确 SHA，不实时采用中央 `main` 后续变化。

## 2. 已满足

### Domain / Application 与 UI 分离

**已基本满足。** 当前工程保持 Presentation、Application、Domain、Infrastructure 分层；核心炭素计算 Domain 不依赖 PySide6 或 SQLite，数据访问通过 Repository/适配器边界完成。这与 Architecture V2.1 的“公共外围 Contract + 自治业务 Domain”方向一致。

### Canonical-first（标准、参数与 reference data）

**已有成熟基础。** `data-source/carbon_accounting/catalog.json` 是当前标准目录、来源、参数和因子的 Canonical Source；构建链先校验 Canonical，再确定性生成 `catalog.sqlite`。SQLite 是运行时查询/部署格式，而不是上述标准/reference data 的事实源。

### 不可变正式 Record 与历史不漂移基础

**已基本满足。** 成功核算形成新的不可编辑 Record；`records.sqlite` 保存输入、结果、参数快照、有效规则集和审计信息；重新计算新增 Record，不覆盖旧 Record；当前 Catalog 变化不应反向改变历史快照。

### 当前 Windows Runtime 的 Workspace / Record 分离

**已满足当前平台运行目标。** Post-V1 已使用独立 `projects.sqlite` 保存可变项目和未完成输入，正式成功记录继续写入 `records.sqlite`。项目保存与正式 Record 生命周期分离；成功 Record 已形成后，项目关联失败不得撤销该 Record。

## 3. 部分满足

### Numeric

已有 `DecimalPolicy`，正式解析拒绝 binary `float`，并区分高精度计算与显示修约；但部分权威公式仍直接使用 Decimal 运算，且现有 `DecimalPolicy.is_close()` 的 tolerance 与中央 Numeric v1 DRAFT 的 exact equality 语义尚未完成公共边界收口。因此只能判定 **部分满足**，本任务不修改计算算法。

### Unit

已有集中式 `UnitService` 和量纲兼容检查；但部分计算路径仍存在 `1e-6`、`1e-9` 等尺度常数，且 C↔CO₂ 的 44/12 当前被 UnitService 作为跨 dimension bridge，而中央 Unit v1 DRAFT 要求进一步区分真正单位换算与标准公式/化学计量系数。因此为 **部分满足**。

### Module ID / Capability

Architecture V2.1 已冻结永久 Module ID：

```text
qz.carbon_accounting
```

本次已在治理 baseline 中登记，但当前业务对象、Workspace、Result/Record 外围尚未全面携带 `module_id`；正式 Capability Manifest 也尚未建立。不得因此伪称 Module / Capability Contract 已实现。

### Workspace

当前 `ProjectWorkspace` / `AccountingUnitWorkspace` 已能保存项目、多核算单元和记录关联；但 `form_state` 仍包含 Qt `objectName()`、`QComboBox.currentIndex()` 等 Windows Presentation State。它是有效的 Windows runtime persistence，但不是 Architecture V2.1 所定义的跨平台 Business Workspace Contract。

### Attempt / Record

正式 Record 的成功结果与不可变语义较成熟；致命校验失败不形成正式碳核算 Record，与中央 records DRAFT 对 GHGTOOL 的兼容方向一致。但尚未建立独立、版本化的公共 Attempt Envelope。

### Result

已有 `CalculationResult`、参数快照、校验问题和规则追溯基础，但尚未形成公共 Result/Record Envelope，例如 `contract_version`、`module_id`、`rule_version`、`calculator_version`、`numeric_contract_version`、`package_hash` 等。Architecture V2.1 明确不要求当前数据库立即迁移，因此 QZC-A01 不修改 records schema。

### Canonical Business Truth

标准元数据、参数和因子已 Canonical-first；复杂炭素公式、蒸汽查表等仍部分存在于版本化 Python Domain Calculator。该状态本身不违反 V2.1，因为复杂标准允许 Specialized Domain Calculator；未来缺口是 Contract、reference data 和 Conformance，而不是把全部算法强制 DSL 化。

## 4. 尚未实施

以下公共能力尚未正式实施，不能因为 Architecture V2.1 已存在就描述为完成：

- 正式 Capability Manifest；
- 平台无关 Conformance Vectors；
- qzpack Package Manifest / activation / rollback / signature 生命周期；
- 跨平台 Business Workspace / `.qzproj`；
- 公共 Attempt Envelope；
- 完整公共 Result/Record Envelope。

当前仓已有丰富工程测试，但不能把现有 unittest / GUI / delivery tests 冒充为中央尚未发布的正式 Conformance Vectors。

## 5. 当前冲突与偏差

### C-01 — 历史 AGENTS / README 与最新已批准 Workspace 治理不一致

**类型：本地治理文本陈旧，不是 Architecture V2.1 硬冲突。**

旧治理仍保留“不提供项目保存、草稿或跨启动恢复”的 V1 表述；但最新 `HANDOFF.md §22` 已批准独立 `projects.sqlite`、显式项目保存和跨启动恢复，PR #12 也已合并到 `main@bbc753c9ad5e662b9d294cda7611a1e4e4bf8dd8`。

QZC-A01 不借公共治理接入偷偷重写该历史决策。后续如清理，应作为独立治理维护任务处理。

### C-02 — TASK_STATE 历史主体仍保存 PR #12 合并前状态

**类型：历史状态记录，不是当前基线冲突。**

QZC-A01 已在 `TASK_STATE.md` 顶部增加当前接入状态，明确 PR #12 已合并、中央 baseline 已锁定，并说明下方旧“当前工作包 / 未合并”等文字仅作为历史审计记录保留。没有重写既有阶段历史。

### C-03 — Runtime Workspace 与跨平台 Workspace 尚未分离成公共 Contract

**类型：实现差距，不是接入阻断。**

当前 Qt Presentation State 可以继续作为平台本地运行状态，但不得被描述成未来跨平台 Business Workspace；未来 `.qzproj` / Suite / Mobile 不应直接复制该结构。

### 硬冲突判断

**未发现导致 QZC-A01 无法接入的硬冲突。** Architecture V2.1 允许先锁定 Contract，再渐进兼容，不要求本业务仓现在迁移数据库、重写 UI 或替换 Domain Calculator。

## 6. RFC Candidates

以下只记录候选，不直接修改 Qingzhou-contracts。

### RFC-CANDIDATE-01 — Carbon quantity / Unit 语义

- **问题**：GHGTOOL 同时使用 `tC`、`tCO₂`、组合单位及 44/12、44/16 等系数，当前 UnitService 还允许 C↔CO₂ 跨 dimension bridge。
- **为什么属于公共问题**：未来 Python/Kotlin/Swift/ArkTS 实现相同 Capability 时，需要统一区分单位转换、quantity type 与化学计量/公式系数。
- **影响 Contract**：Unit Contract，可能同时影响 Numeric / Rule / Result trace。
- **真实案例**：GB/T 32151.34 燃料、物料碳量到 CO₂ 排放量路径。
- **建议**：提出 RFC；本业务仓不私自冻结公共答案。

### RFC-CANDIDATE-02 — Numeric tolerance / `is_close` 公共边界

- **问题**：现有 `DecimalPolicy.is_close()` 有默认 tolerance，而中央 Numeric v1 DRAFT 将公共 `eq` 定义为 exact decimal equality。
- **为什么属于公共问题**：若 tolerance 可进入正式判断，各产品和平台必须统一；若只允许测试/非判定验证，也应明确。
- **影响 Contract**：Numeric Contract。
- **真实案例**：`packages/core/decimal_policy.py::DecimalPolicy.is_close`。
- **建议**：提出 RFC，优先级中等；本任务不改实现。

### RFC-CANDIDATE-03 — 既有 Presentation-State Project 的跨平台迁移/共存

- **问题**：现有 `projects.sqlite` 用户项目的 `form_state` 依赖 Qt 控件状态，而未来要求 Business Workspace 与 Presentation State 分离。
- **为什么属于公共问题**：独立版、Suite、Mobile 的 Workspace 交换需要统一的兼容原则。
- **影响 Contract**：Workspace / Attempt / Record / Result，未来也可能影响 `.qzproj` transport profile。
- **真实案例**：`AccountingUnitWorkspace.form_state` 与页面 `_capture_form_state()`。
- **建议**：作为低优先级 RFC Candidate 保留；不为未来格式提前重写现有项目持久化。

## 7. 当前最小预留

近期只需保持以下低成本原则，不构成本次实施授权：

1. 新增公共外围对象时使用稳定 `qz.carbon_accounting`，不另创同义公共 Module ID；
2. 不把新的 Qt objectName/index 设计成跨平台业务 Contract；
3. 新增正式数值规则继续避免 binary float、隐式修约和显示值参与判定；
4. 新增单位换算优先走 UnitService，并区分单位尺度转换与标准公式固有系数；
5. 新增标准/reference data 继续保持 Canonical-first 与来源追溯；
6. 新增 Record 字段避免与 V2.1 Result/Record Envelope 语义冲突，但不为未冻结 DRAFT 提前大迁移；
7. GB/T 32151.34 后续跨平台试点优先沉淀 candidate Conformance Vectors，而不是复制 Python 实现作为唯一权威；
8. 公共语义缺口进入 RFC Candidate，不在 GHGTOOL 永久发明同名不同义公共 Contract。

## 8. 当前不做

QZC-A01 明确不实施：

- 不合仓；
- 不开发 Suite；
- 不开发 Android / HarmonyOS / iOS / 小程序；
- 不重写 Native Core；
- 不把复杂算法全部 DSL 化；
- 不全量 qzpack 化；
- 不因为统一架构重写成熟 UI；
- 不修改业务公式、正式数值结果或标准解释；
- 不修改标准 Canonical 数据；
- 不修改数据库 schema/migration；
- 不抽公共 Python package；
- 不添加 Git Submodule；
- 不 vendor Qingzhou-contracts；
- 不修改 Qingzhou-contracts 中央 Contract；
- 不把任何 DRAFT 描述为 FROZEN。

## 9. Adoption 结论

**QZC-A01 可接入，未发现需要 BLOCKED 的上位治理硬冲突。**

本次只建立稳定、版本锁定的上位治理关系。当前中央仓没有正式 Contract release/tag，因此本仓锁定 `Qingzhou-contracts@0cd74d783fa23add6dc881b408a8c8ba8503f8e8`，状态明确为 `pre-release / bootstrap baseline`；未来中央变化只有在本仓显式升级 `PLATFORM_BASELINE.md` 与 `platform-lock.json` 后才生效。