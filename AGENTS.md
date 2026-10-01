# AGENTS.md — 青舟温室气体排放核算软件（GHGTOOL）

本文件只保留**本仓专属规则**与**青舟中央治理入口**；中央规则完整正文只在中央仓 `Qingzhou-contracts` 保留，本仓不复制。冲突时以本仓 `platform-lock.json` 锁定的 Frozen 权威文件为准。

## 1. 仓库身份

- Module ID `qz.carbon_accounting`；产品：青舟温室气体排放核算软件（Windows V1.1.0）；技术栈/平台：Python 3.12 + PySide6/Qt Widgets + SQLite，Windows x64。
- 当前 Reference Standard：`GB/T 32151.34—2024`（本仓当前称“炭素材料生产企业核算模块”，准确标准元数据以正式标准目录为准），并继续受 `GB/T 32150—2025` 通用规则约束。
- 当前主要产品阶段：Post-V1 — Windows 离线产品已交付，参考标准核心纵向闭环接近完整；缺口为“结果解释的 Reference Standard 集中产品验收”与“正式 Excel 闭环”，真实状态以 `REFERENCE_STANDARD_ROADMAP.md` 为准。
- 实施基线 `HANDOFF.md`（稳定断点同步 `TASK_STATE.md`）；Sol 决策验收、Luna Max 实施，一个阶段只能建立一个 Goal。

第一条完整业务链只实现 `GB/T 32150—2025` + `GB/T 32151.34—2024`；其余七项计划标准本阶段只允许建立标准目录和状态信息，不得实现、猜测或复用计算规则。

## 2. 本仓专属硬规则

**必须完整保留，不得删除或弱化。**

### 2.1 产品与交付边界

- Windows-first：本仓当前只开发 Windows V1 桌面产品。
- Excel 导入当前只保留禁用入口和占位说明；这是**当前产品状态**，不是永久豁免。后续按 `REFERENCE_STANDARD_ROADMAP.md` 与中央产品交付 Policy 在软件核心闭环后单独完成 Excel 适配器，本治理任务不启用或实现。
- 当前 V1 的报告与导出、企业档案完善、企业层级、企业真实输入基准和黄金算例仍未实施；必要导出按中央 Policy 单独规划，本治理任务不顺手实现。
- 标准全文不得复制或打包进软件；“打开标准原文”只能调用官方网址。
- `GB/T 32151.34` 遇其他行业活动或上下游运输只提示需要其他标准，不得猜算、套算或并入当前结果。
- 官方参数、排放因子、标准状态和网址不得凭记忆或搜索摘要录入，必须可追溯到原始来源。
- 不得修改、删除或覆盖 `计算表/` 中的用户参考文件。

### 2.2 架构与分层

- 保持 Presentation / Application / Domain / Infrastructure 分层；Domain 不得依赖 PySide6、SQLite、Windows API、页面控件或桌面弹窗；UI、计算、校验、数据访问必须分离，数据访问通过 Repository 接口。
- 标准和参数的 Canonical Source 必须是可校验的 JSON/YAML，SQLite 只是 Windows 查询与部署格式：官方标准与参数入 `catalog.sqlite`，用户设置入 `user.sqlite`，成功核算记录入 `records.sqlite`。
- Canonical-first **不等于**“所有碳核算算法都必须 JSON DSL 化”：复杂标准公式、查表/插值继续允许保留在**版本化 Domain Calculator** 中，缺口补在 Contract / reference data / Conformance。

### 2.3 Numeric / Unit 语义（本仓专属）

- 本仓 Numeric Profile 为 `GHGTOOL_CARBON_DECIMAL40_CURRENT`（Decimal/DecimalPolicy、precision 40、`ROUND_HALF_UP`、full-value exact formal comparison、无 global business epsilon），是**项目专属 Profile，不是青舟平台默认**，不得把 p40/p50/HALF_UP/HALF_EVEN 任一配置描述成平台统一默认。
- **declared-profile consistency**：authoritative Calculator 必须消费自己声明的 Profile，helper/service 不得 silent fallback；**ambient independence**：caller ambient `Decimal` context 不得改变同一 declared Profile 的正式结果。
- 内部十进制高精度计算，中间结果默认不舍入，界面默认显示 2 位小数（标准明确要求除外）；显示修约只是 Presentation，不得回流 calculation / comparison 或影响正式判定。
- `44/12`、`44/16` 是 quantity transformation + stoichiometric/formula coefficient，**不是** ordinary unit conversion；GWP 属 characterization/equivalence factor，不得把它们重新描述成普通 Unit multiplier。
- `is_close()` / numerical tolerance 只用于测试与非判定性验证，**不得**控制正式业务结论；正式业务比较使用 full-value exact comparison。

### 2.4 Workspace / Record

- 碳核算 V1 不向用户提供 `.qzproj` 项目文件，不设置项目保存、草稿、审批状态或恢复未计算输入。
- runtime `form_state` 只是 **Presentation State**（含 Qt `objectName()`、`currentIndex()` 等），不得成为跨平台 Workspace Contract，也不得被未来 `.qzproj` / Suite / Mobile 直接复制。
- 点击“计算排放量”并通过致命校验后，立即生成一条不可编辑的新核算记录，再次计算不得覆盖旧记录；记录只允许 `COMPLETED` 或 `COMPLETED_WITH_WARNINGS`，致命错误不生成核算记录；删除记录必须二次确认并留审计日志，不得直接修改历史记录。
- 不可变正式 Record 与参数快照：正式记录保存输入、结果、参数快照、有效规则集和审计信息，Catalog / 算法升级不得使历史正式 Record 自动漂移。

### 2.5 Scope 与执行纪律

- MUST = `HANDOFF.md` 当前阶段明确要求；MAY = 默认不做，仅 `HANDOFF.md` 明确允许才实施；OUT OF SCOPE = 不得实施（顺手重构、扩大标准范围、改变计算口径、增加云端服务或新的主要技术栈）。
- 小工作包、小测试、小提交；不覆盖用户已有修改，不使用破坏性 Git 操作；每个稳定断点更新 `TASK_STATE.md`，每阶段完成后生成或更新 `IMPLEMENTATION_REPORT.md`，然后停止等待 Sol 验收。
- 以磁盘、Git 和测试结果为准，不得以上一次对话的文字推断完成状态；不得仅写“测试通过”，必须记录命令、通过/失败数量、未执行项和原因。

### 2.6 停止并上报条件

遇下列情况停止相关工作，不得自行作重大决定：文档内部或与实际代码存在关键冲突；需改变数据模型、架构、计算公式、标准解释或阶段范围；原始标准或官方来源无法支持准备录入的值；需新增一级模块或主要依赖；公共接口修改会影响另外两套软件；无法满足当前阶段验收条件；测试证明批准方案存在逻辑错误。

上报格式：

```md
## BLOCKED

问题：
证据：
为什么不能按原方案继续：
可选方案 A：
可选方案 B：
建议：
需要 Sol 决策的具体问题：
```

## 3. 青舟中央治理入口

中央仓：`https://github.com/adgo07/Qingzhou-contracts.git`。当前批准公共基线只以 `PLATFORM_BASELINE.md` 与 `platform-lock.json` 为准，中央变化在本项目显式升级 baseline 前不生效：当前显式锁定 `Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20` —— Architecture `V2.1`、Numeric Contract `v1` 为 **FROZEN**（Numeric v1 已由本项目单独 compatibility/adoption 采用）；Unit、Module/Capability、Workspace/Attempt/Record/Result、qzpack v1 继续 **DRAFT**；Quantity public schema 继续 **NOT FROZEN**。

- **Frozen 权威文件**（Frozen Contract / Schema / Conformance / Architecture Frozen）：按**本仓 `platform-lock.json` 的 locked SHA** 读取，不得自动跟随中央 `main`。
- **ACTIVE / ACTIVE-EVOLVING 指南**：按中央 `docs/GUIDE_INDEX.md` 与中央仓**当前正式合并的适用版本**读取，不受 locked SHA 限制。

**三条“不得”：** 不得自动升级 Frozen Contract 或 baseline；不得把 ACTIVE / ACTIVE-EVOLVING 指南当作 Frozen Contract；不得用中央 Guide 覆盖本仓 locked Frozen Contract（冲突时以 locked Frozen 为准）。

**边界：** 读 ACTIVE 指南**不修改** `platform-lock.json`、**不构成** Frozen Contract adoption、**不得覆盖** locked Frozen Contract、**不得改变** Calculator / Rule / 标准原文业务语义。公共 Contract 不得覆盖更具体且有权威依据的标准原文、已批准标准映射、标准专属业务规则与本模块合法自治范围；普通产品 Bug、单标准公式/解释、业务 UI、产品特有数据库字段与模块自治问题留在本仓解决；跨产品/跨平台公共缺口（Numeric / Unit / Module-Capability / Workspace-Record-Result / qzpack / Conformance）不得私自定义同名公共规则，应整理业务证据作为 RFC Candidate 返回中央仓。中央仓 `DRAFT / NOT YET RELEASED` 内容不得描述成 `FROZEN`；`PRODUCT_DELIVERY_POLICY_V1.md` 是 **ACTIVE** 治理指南（不是 Frozen Contract），统一 Windows-first / Reference Standard first / Product-core-first / Excel-as-adapter / Cross-platform-ready / 逐标准扩展，完整正文只在中央保留。本地历史治理文本陈旧与公共 Contract 差距统一记录于 `docs/governance/PLATFORM_ADOPTION_REPORT.md`，该报告不授权实施其中的后续迁移。

## 4. 开工前最小必要读取（Minimum Necessary Reading）

```text
1. 本仓 AGENTS.md → 2. platform-lock.json（取得 locked SHA）
→ 3. HANDOFF.md / TASK_STATE.md（当前阶段与真实状态）
→ 4. 当前任务直接相关的本仓文件（源码 / Canonical / Mapping / 测试），
     含 git status / git diff / 最近 5 个 commit / 上次测试是否真正执行完毕
→ 5. 中央 docs/GUIDE_INDEX.md（阅读路由）
→ 6. 只读 GUIDE_INDEX 为当前任务路由到的中央文件
     （Frozen 按 locked SHA 读；ACTIVE 按中央当前合并版本读）
```

**不得要求每个普通业务 Bug、UI 调整或单标准专有业务问题都通读整个 `Qingzhou-contracts`**；只有确认涉及公共语义（Numeric / Unit / Module-Capability / Workspace-Record-Result / qzpack / Conformance）才扩大中央读取范围，且只有任务明确要求升级中央 Contract 时才允许通过独立治理变更 `PLATFORM_BASELINE.md` / `platform-lock.json`。

## 5. 青舟平台开发前置检查（Contract Preflight，压缩入口）

适用于设计、开发、重构、修复、标准接入、Calculator、Numeric、Excel、Record、数据库、Schema、Module、Package、跨平台与导入导出任务。核心流程（完整中央正文见 `PRODUCT_DELIVERY_POLICY_V1.md` 第 12 节）：

```text
读取 platform-lock.json → 确认锁定 SHA
→ 按 locked SHA 读相关 Frozen Contract → 提取适用 MUST / MUST NOT
→ 检查冲突并按 §6 分类 → 确认后再设计或编码
```

正式 Design / Execution / Acceptance Report 必须包含“平台 / Contract 预检查”（业务仓 SHA、locked central SHA、相关 Frozen Contract、适用 MUST / MUST NOT、冲突及分类、是否需改中央 Contract）；与中央公共语义无关时也必须写明 `本任务不涉及中央公共 Contract。`

**中文优先**：在不破坏稳定机器接口的前提下，面向人的内容（UI、治理文档、路线、报告、PR/Issue、提示、结果解释）优先中文，机器字段与稳定技术标识保持英文（完整规则见中央 Policy §2）。

## 6. Contract 冲突分类

- `LOCAL DEFECT`：本地实现违反已采用 Frozen Contract；修本地。
- `ALLOWED PROJECT DIFFERENCE`：中央明确允许项目级差异，例如 Carbon p40/HALF_UP Profile；不得为表面统一强改。
- `REGISTERED DEVIATION`：已登记但未关闭的偏差；按治理状态处理。
- `CENTRAL CONTRACT GAP`：真实业务需求无法被当前中央 Contract 表达；不得在 GHGTOOL 永久私自定义另一套公共规则，应整理业务证据/案例/缺口/Candidate 返回 Qingzhou-contracts。

## 7. 标准问题与解释治理（入口 + 本仓增量）

开工前必须读取根目录 `STANDARD_ISSUES_REGISTER.md`。

- **先登记再实现**：在标准映射、软件设计、Calculator、Golden Case、测试、Excel、用户实际使用或标准更新中发现新的标准疑似笔误、歧义、冲突、未规定、术语、引用或软件实现解释问题时，必须先登记台账，再完成正式实现说明。
- **必须保持三层分开**：“标准原文事实”“技术判断”“软件实现决定”；不得把内部判断或软件选择写成标准明文，不得静默纠正标准。
- 影响正式业务结果的问题必须可追踪：`Standard Issue → Software Decision → Rule / Calculator → Test / Golden Case`；解释变化须同步检查测试与历史结果兼容性。
- 报告预检查须补充：是否存在相关 Standard Issue（是/否）、涉及问题编号、本任务是否改变既有软件解释（是/否）。

完整治理规则见中央 `PRODUCT_DELIVERY_POLICY_V1.md` 第 20 节与 `STANDARD_DEVELOPMENT_GUIDE_V0.1.md`。

## 8. 新标准开发入口

任何**新增标准**或**实质修改既有标准支持范围**的任务，必须按中央 `docs/governance/STANDARD_DEVELOPMENT_GUIDE_V0.1.md`（**ACTIVE / EVOLVING**，读中央当前正式合并版本）执行：

```text
Stage A 标准整理 → Stage B 软件接入设计 → Stage C 实现 → Stage D 正式验收
```

阶段顺序不得颠倒。**不得：** 拿到 PDF 就直接写 Calculator；跳过 Standard Mapping；在 Mapping 中静默纠正标准；UI 先发明业务规则；Excel 建第二套算法；未经正式验收就宣布 `SUPPORTED`（进入标准库、Calculator 能跑、单个单元测试通过都不构成正式支持）。

标准支持状态、四阶段出口条件、Golden Case 与公共约束检查等详细规则**不复制**在本文件，一律以中央指南为准。

## 9. 知识沉淀入口

- 标准开发 / Mapping / Calculator / 测试 / UI / Excel 等任务中若产生“**有长期价值 + 已有证据支持**”的专业知识，允许顺手记录到本仓 `knowledge/` 落点；新条目默认 `DRAFT`。
- 不要求每个任务必须产生知识；不得为了 Knowledge 明显扩大主任务。
- 必须区分标准原文事实 / 官方资料 / 专业解释 / 工程实践建议；不得把技术判断写成标准明文，不得把工程经验写成强制标准要求。
- 知识不是 Calculator 真值源，不得在运行时解析 Markdown 知识文章决定业务结果；详细规则见中央 `STANDARD_DEVELOPMENT_GUIDE_V0.1.md` 知识沉淀部分。

## 10. UI 设计前置原则（短入口 + 本仓要点）

涉及桌面 UI 的 Design / Execution / Acceptance 必须读取中央 `docs/ui/UI_DESIGN_GUIDELINES_V0.1.md` 的**当前适用版本**（**ACTIVE / EVOLVING**，不是 Frozen Contract）。本仓要点：① 当前 Windows Desktop 默认 UI 技术栈为 PySide6，用户可见内容中文优先；② 普通 UI 不得默认泄露内部 `key / field / field_id / rule_id / internal_id`、Python 变量、内部枚举或调试标识；③ 简单业务 `One-page first`，复杂核算不强制单屏或单步骤，技术 trace / Numeric Profile / Calculator version / 内部 Rule 渐进展示且不删除审计能力；④ UI 优先满足真实用户任务，不按数据库 / JSON / 代码结构组织普通页面；⑤ AI 不得因 v0.1 的推荐 AppShell、页面示意或当前实现而拒绝合理页面改进，也不得把当前七项导航误当永久冻结结构。

该指南不改变 `platform-lock.json` 的 Frozen Contract 锁定语义，也不授权本任务修复 `UI_CURRENT_STATE_AUDIT.md` 中记录的问题。
