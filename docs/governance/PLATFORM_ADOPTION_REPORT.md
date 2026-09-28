# PLATFORM_ADOPTION_REPORT

## 1. 当前仓信息

```text
repo: adgo07/GHGTOOL
default_branch: main
adoption_base_head: bbc753c9ad5e662b9d294cda7611a1e4e4bf8dd8
adoption_branch: chore/qingzhou-contracts-adoption
current_stage: Post-V1 — 新建核算实用性与多核算单元已合并；本任务仅执行 QZC-A01 公共治理接入
adoption_date: 2026-09-28
```

本次公共基线锁定：

```text
Qingzhou-contracts repository: https://github.com/adgo07/Qingzhou-contracts.git
release/tag: none
baseline_status: pre-release / bootstrap baseline
commit_sha: 0cd74d783fa23add6dc881b408a8c8ba8503f8e8
Architecture: V2.1 FROZEN
```

中央仓当前尚无正式 release/tag；Numeric、Unit、Module/Capability、Workspace/Attempt/Record/Result、qzpack Contract 均为 **DRAFT / NOT YET RELEASED**。本项目只锁定上述精确 SHA，不实时采用中央 `main` 后续变化。

## 2. 已满足

### Domain / Application 与 UI 分离

**已基本满足。**

- 现有工程长期治理明确要求 Presentation、Application、Domain、Infrastructure 分层；
- `packages/standards/carbon_material.py` 的核心炭素计算 Domain 不依赖 PySide6 或 SQLite；
- 数据访问通过 Repository/适配器边界完成；
- UI 层通过 Application/Domain 服务调用业务能力，而不是把正式公式写入页面。

这与 Architecture V2.1 的“公共外围 Contract + 自治业务 Domain”及分层原则一致。

### Canonical-first（标准/参数/reference data 侧）

**已有成熟基础。**

- `data-source/carbon_accounting/catalog.json` 是当前标准目录、来源、参数和因子的 Canonical Source；
- `packages/persistence/catalog_builder.py` 对 Canonical JSON 先校验，再确定性构建 `catalog.sqlite`；
- SQLite 是运行时查询/部署格式，不是上述标准/reference data 的事实源；
- 已有来源、版本、有效期、审核状态和标准适用关系等追溯字段。

### 正式 Record 不可变与历史不漂移基础

**已基本满足。**

- 成功核算形成新的不可编辑 Record；
- `records.sqlite` 保存输入、计算结果、参数快照、有效规则集及审计信息；
- 重新计算新增 Record，不覆盖旧 Record；
- 项目删除/核算单元删除不得级联删除历史 Record；
- 当前 Catalog 变化不应反向改变历史快照。

### Workspace 与 Record 的运行时分离

**已满足当前 Windows Runtime 的分离目标。**

- Post-V1 已新增独立 `projects.sqlite` 保存可变项目和未完成输入；
- 正式成功记录继续单独写入 `records.sqlite`；
- 项目保存与正式 Record 生命周期分离；
- 成功记录已形成后，即使项目关联失败，也不得撤销已成功 Record。

这与公共 Contract 中“可编辑 Workspace / 不可变 Record”的方向兼容。

## 3. 部分满足

### Numeric

**部分满足。**

已有：

- `DecimalPolicy` 为平台无关 Domain 数值策略；
- 默认 Decimal 精度为 40；
- 正式解析明确拒绝 Python binary `float` 和 `bool`；
- 提供 Decimal add/subtract/multiply/divide；
- 显示修约与原始 Decimal 值分离。

差距：

- `carbon_material.py` 的部分权威公式仍直接执行 Decimal 的 `* / + -`，没有全部通过统一 Numeric 操作边界；
- 当前存在 `DecimalPolicy.is_close()` 的默认 tolerance，而中央 Numeric v1 DRAFT 将 `eq` 定义为 exact decimal equality，并且 tolerance 的公共使用边界尚未冻结；
- 因此不能宣称已完整实现 Qingzhou Numeric Contract v1。

本任务只记录，不修改任何计算算法。

### Unit

**部分满足。**

已有：

- `UnitService` 集中管理 kg/t、kWh/MWh、kJ/GJ、Nm³/10⁴Nm³、ratio/percent 等；
- 统一使用 DecimalPolicy 做转换；
- 有量纲兼容检查。

差距：

- `carbon_material.py` 仍存在 `1e-6`、`1e-9` 等与单位尺度相关的常数直接进入计算路径；
- 当前 UnitService 将 C↔CO₂ 的 44/12 作为跨 dimension bridge，而 Architecture V2.1 / Unit Contract v1 DRAFT 要求进一步区分“真正单位换算”和“标准公式/化学计量固有系数”；
- C / CO₂ / CO₂e 应建模为单位、quantity type 还是其他公共语义，中央 DRAFT 本身仍未冻结。

### Workspace

**部分满足。**

当前 `ProjectWorkspace` 和 `AccountingUnitWorkspace` 已能真实保存项目、多核算单元、输入和记录关联；但 `form_state` 是 `dict[str, object]`，实际保存了 Qt `objectName()`、`QComboBox.currentIndex()` 等 Windows Presentation State。

因此：

- 它是有效的当前 Windows runtime Workspace；
- 它**不是** Architecture V2.1 所定义的跨平台 Business Workspace Contract；
- 未来 `.qzproj` / Suite / Mobile 不应直接复制当前 `form_state`。

### Attempt / Record

**部分满足。**

- Record 的不可变成功结果语义较成熟；
- 致命校验失败不形成正式碳核算 Record，与中央 records DRAFT 对 GHGTOOL 的兼容说明一致；
- 但当前尚未建立独立、版本化的公共 `Attempt` Envelope，也没有显式区分所有公共 candidate business outcome 与 execution error 的统一外围对象。

### Result

**部分满足。**

已有 `CalculationResult`、参数快照、问题和计算 trace/规则信息等业务资产，但尚未形成 Architecture V2.1 候选公共 Result/Record Envelope，例如：

```text
contract_version
module_id
rule_version
calculator_id / calculator_version
numeric_contract_version
result_contract_version
package_id / package_version / package_hash
provenance
```

Architecture V2.1 明确不要求当前数据库立即大迁移，因此本任务不修改 records schema。

### Canonical Business Truth

**部分满足。**

标准元数据、参数和因子已 Canonical-first；但复杂炭素公式、蒸汽查表等仍有大量内容存在于版本化 Python Domain Calculator 内。

这本身不违反 V2.1，因为复杂标准允许 Specialized Domain Calculator；需要补的是未来 Rule/Calculator Contract、reference data 和 Conformance，而不是把全部碳核算算法强制 JSON DSL 化。

## 4. 尚未实施

### Module ID 落地

Architecture V2.1 已冻结永久 Module ID：

```text
qz.carbon_accounting
```

但当前 GHGTOOL 业务对象、Record/Result 外围、Workspace 与 package 中尚未正式携带 `module_id`。本次只在治理基线中记录，不修改业务模型。

### Capability Manifest

当前仓库尚无正式 Module / Capability Manifest，也没有按 module/profile/standard/feature/platform/status 形成机器可读能力声明。

### Platform-independent Conformance Vectors

当前仓库已有较丰富的单元、Domain parity、GUI、持久化和交付回归测试，但没有形成中央 Contract 所定义的、跨语言/跨平台共享的一套权威 Conformance Vectors。

中央 `Qingzhou-contracts/conformance/carbon_accounting/` 当前也只有 GB/T 32151.34 试点范围说明，尚未发布正式 vector set。因此不得把现有工程测试伪称为已经完成公共 Conformance。

### qzpack

当前仓库尚未实施 qzpack、Package Manifest、独立 package activation/rollback 或 package hash/signature 生命周期。

这是 V2.1 的后续试点，不是本次接入前置条件。

### 跨平台 Business Workspace / `.qzproj`

尚未实施。当前 `projects.sqlite` 主要服务 Windows Runtime，`.qzproj` 物理格式在中央治理中也仍未冻结。

## 5. 当前冲突

### C-01 — 旧 AGENTS / README 与最新已批准 Workspace 治理不一致

**类型：本地治理文本陈旧，不是 Architecture V2.1 硬冲突。**

旧 `AGENTS.md` 和 README 仍写有“不设置项目保存、草稿或跨启动恢复未计算输入”等 V1 禁令；但最新 `HANDOFF.md §22` 已由 Sol 明确批准独立 `projects.sqlite`、显式项目保存和跨启动恢复，并且 PR #12 已合并到当前 `main@bbc753c9...`。

本次不借公共治理接入重写该业务决策。执行时应以最新已批准的 `HANDOFF.md §22` 和实际合并代码为准；后续可安排单独治理清理任务，避免 Agent 被历史禁令误阻塞。

### C-02 — TASK_STATE 对 PR #12 的状态陈旧

**类型：本地状态文档陈旧。**

当前 `TASK_STATE.md` 顶部仍记录 PR #12 等待验收/未合并语义，但当前默认分支已是 PR #12 merge commit `bbc753c9ad5e662b9d294cda7611a1e4e4bf8dd8`。

本次仅增加 QZC-A01 接入状态，不重写历史验收记录。

### C-03 — 当前 runtime Workspace 与跨平台 Workspace 的语义边界尚未实现

**类型：实现差距，不是必须立即修复的冲突。**

当前 `form_state` 直接保存 Qt 控件状态。V2.1 允许 platform-local `presentation_state`，但禁止将其宣称为未来跨平台 Business Workspace。现有实现可继续运行；未来建立跨平台 Contract 时应保持旧项目兼容。

### 硬冲突判断

**未发现导致 QZC-A01 无法接入的硬冲突。**

Architecture V2.1 明确允许先冻结 Contract、再增量兼容，不要求当前业务仓立即迁移数据库、重写 UI 或重做 Domain。

## 6. RFC Candidates

以下仅记录候选，不修改 Qingzhou-contracts 正式 Contract。

### RFC-CANDIDATE-01 — Carbon quantity / Unit 语义

**问题**

GHGTOOL 同时使用质量量纲、`tC`、`tCO₂`、组合单位（如 `tC/t`、`tC/GJ`、`tCO₂/MWh`）以及 44/12、44/16 等化学计量/标准公式系数。当前 UnitService 还允许 C↔CO₂ 的跨 dimension bridge。

**为什么属于公共问题**

未来 Python/Kotlin/Swift/ArkTS 实现同一碳核算 Capability 时，需要一致区分“单位转换”“quantity type”“化学计量/公式系数”。这不是单个 UI 或单条标准公式的局部问题。

**影响 Contract**

`Qingzhou Unit Contract v1`，并可能影响 Numeric/Rule/Result trace 表达。

**当前产品真实案例**

GB/T 32151.34 中燃料/物料碳量与 CO₂ 排放量转换，以及 `UnitService` 中 mass_carbon ↔ mass_co2 bridge。

**建议是否提出 RFC**

建议：**是**。在 Unit Contract v1 冻结前作为试点证据提交；本业务仓暂不私自冻结公共答案。

### RFC-CANDIDATE-02 — Numeric tolerance / `is_close` 的公共边界

**问题**

GHGTOOL 的 `DecimalPolicy.is_close()` 当前提供默认 tolerance；中央 Numeric v1 DRAFT 则将公共 `eq` 定义为 exact decimal equality，并且 tolerance 的正式适用范围仍待决。

**为什么属于公共问题**

如果 tolerance 可以进入正式判定，不同模块/平台必须采用同一语义；如果只允许测试或非判定数值验证，也应明确，避免以后被误用于等级/合规边界。

**影响 Contract**

`Qingzhou Numeric Contract v1`。

**当前产品真实案例**

`packages/core/decimal_policy.py::DecimalPolicy.is_close`。

**建议是否提出 RFC**

建议：**是，优先级中等**。在 Numeric v1 冻结前明确用途；本次不改现有实现。

### RFC-CANDIDATE-03 — 既有 Presentation-State Project 的跨平台迁移/共存方式

**问题**

当前 GHGTOOL 已存在真实 `projects.sqlite` 用户项目，内部 `form_state` 依赖 Qt `objectName/currentIndex`。V2.1 未来要求跨平台 Business Workspace 与 Presentation State 分离。

**为什么属于公共问题**

未来独立版 ↔ Suite ↔ Mobile 的 Workspace 交换会涉及“既有平台本地 Workspace 如何迁移、映射或共存”的公共兼容原则。

**影响 Contract**

Workspace / Attempt / Record / Result Contract，未来可能影响 `.qzproj` transport profile。

**当前产品真实案例**

PR #12 合并后的 `AccountingUnitWorkspace.form_state` 与 `CarbonMaterialAccountingPage._capture_form_state()`。

**建议是否提出 RFC**

建议：**作为低优先级候选保留**。待 Workspace v1 DRAFT 更稳定后提出，不应现在为了未来格式重写已有项目持久化。

## 7. 当前最小预留

为了避免后续继续走偏，近期只需要保持以下低成本原则，不等同于本次实施任务：

1. 新增公共外围对象时预留稳定 `qz.carbon_accounting` Module ID，而不是另创产品私有公共 ID；
2. 不把新的 Qt objectName/index 设计成跨平台业务 Contract；
3. 新增正式数值规则继续避免 binary float、隐式修约和显示值参与判定；
4. 新增单位换算优先走 UnitService，并区分单位尺度转换与标准公式固有系数；
5. 新增标准/reference data 继续保持 Canonical-first 和来源追溯；
6. 新增 Record 字段时避免与 V2.1 Result/Record Envelope 语义冲突，但不为尚未冻结的 DRAFT 提前大迁移；
7. GB/T 32151.34 后续跨平台试点优先沉淀 candidate Conformance Vectors，而不是复制现有 Python 实现作为权威预期；
8. 公共语义缺口进入 RFC Candidate，不在 GHGTOOL 永久发明同名不同义公共 Contract。

## 8. 当前不做

QZC-A01 明确不实施：

- 不合并三个业务仓库；
- 不开发 Suite；
- 不开发 Android / HarmonyOS / iOS / 小程序；
- 不重写 Rust/C++/其他 Native Core；
- 不把 `CarbonMaterialCalculator` 或其他复杂算法全部 DSL 化；
- 不全量 qzpack 化；
- 不因为统一架构重写成熟 UI；
- 不修改业务公式、正式数值结果或标准解释；
- 不修改标准 Canonical 数据；
- 不修改数据库 schema/migration；
- 不抽取公共 Python package；
- 不添加 Git Submodule；
- 不 vendor Qingzhou-contracts；
- 不修改 Qingzhou-contracts 中央 Contract；
- 不把任何 DRAFT 描述为 FROZEN。

## 9. Adoption 结论

**QZC-A01 可接入，不构成业务重构门禁。**

本次应建立版本锁定和上位治理关系；现有实现差距保持为 Adoption backlog / RFC Candidate。后续中央 Contract 只有在发布并由本业务仓显式升级 `PLATFORM_BASELINE.md` 与 `platform-lock.json` 后，才成为本项目新的批准基线。
