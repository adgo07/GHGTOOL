# AGENTS.md

## 项目名称与当前目标

本仓库当前只开发“青舟温室气体排放核算软件”Windows V1。

第一条完整业务链只实现：

- GB/T 32150—2025 通用规则；
- GB/T 32151.34—2024 炭素材料生产企业核算模块。

其余七项计划标准本阶段只允许建立标准目录和状态信息，不得实现、猜测或复用计算规则。

## 模型分工

本项目采用“Sol 决策与验收，Luna Max 实施”的分工。

Luna Max 必须以根目录 `HANDOFF.md` 为当前实施基线，按其中阶段顺序逐个 Goal 执行。一个阶段只能建立一个 Goal；当前阶段未完成、未提交实施报告或存在 BLOCKED 时，不得进入下一阶段。

## 开工与恢复检查

每个 Goal 开始前以及任何中断恢复后，必须依次检查：

1. `AGENTS.md`；
2. `HANDOFF.md`；
3. `TASK_STATE.md`；
4. `git status`；
5. `git diff`；
6. 最近 5 个 commit（仓库存在 Git 时）；
7. 当前阶段直接相关的源码、数据和测试；
8. 上一次测试是否真正执行完毕。

以磁盘、Git 和测试结果为准，不得以上一次对话的文字推断完成状态。

## 长期不可偏离规则

- Windows V1 使用 Python、PySide6/Qt Widgets、SQLite，目标为 Windows x64。
- 保持 Presentation、Application、Domain、Infrastructure 分层。
- Domain 不得依赖 PySide6、SQLite、Windows API、页面控件或桌面弹窗。
- UI、计算、校验、数据访问必须分离；数据访问通过 Repository 接口。
- 标准和参数的 Canonical Source 必须是可校验的 JSON/YAML；SQLite 只是 Windows 查询与部署格式。
- 官方标准与参数放入 `catalog.sqlite`，用户设置放入 `user.sqlite`，成功核算记录放入 `records.sqlite`。
- 碳核算 V1 不向用户提供 `.qzproj` 项目文件，不设置项目保存、草稿、审批状态或恢复未计算输入。
- 点击“计算排放量”并通过致命校验后，立即生成一条不可编辑的新核算记录；再次计算不得覆盖旧记录。
- 记录只允许 `COMPLETED` 或 `COMPLETED_WITH_WARNINGS`；致命错误不生成核算记录。
- 删除核算记录必须二次确认并留下审计日志；不得直接修改历史记录。
- 当前实现中 Excel 导入仍只保留禁用入口和占位说明；这描述的是**当前产品状态**，不是永久豁免。后续必须按 `REFERENCE_STANDARD_ROADMAP.md` 和中央产品交付 Policy 在软件核心闭环后单独完成 Excel 适配器，本治理任务不启用或实现该功能。
- 当前 V1 的报告与导出、企业档案完善、企业层级、企业真实输入基准和黄金算例仍未实施；其中后续 Reference Standard 所需的必要导出按中央产品交付 Policy 单独规划，本治理任务不顺手实现。
- 标准全文不得复制或打包进软件；“打开标准原文”只能调用官方网址。
- GB/T 32151.34 遇到其他行业活动或上下游运输时只提示需要其他标准，不得猜算、套算或并入当前结果。
- 内部使用十进制高精度计算；中间结果默认不舍入；最终界面默认显示 2 位小数，标准明确要求除外。
- 官方参数、排放因子、标准状态和网址不得凭记忆或搜索摘要录入，必须能追溯到原始来源。
- 不得修改、删除或覆盖 `计算表/` 中的用户参考文件。

## Scope 规则

- MUST：`HANDOFF.md` 当前阶段明确要求的事项。
- MAY：默认不做，只有 `HANDOFF.md` 明确允许时才能实施。
- OUT OF SCOPE：不得实施，包括顺手重构、扩大标准范围、改变计算口径、增加云端服务或新的主要技术栈。

## 停止并上报条件

遇到下列情况，停止相关工作，不得自行作重大决定：

- 文档内部或文档与实际代码存在关键冲突；
- 需要改变数据模型、架构、计算公式、标准解释或阶段范围；
- 原始标准或官方来源无法支持准备录入的值；
- 需要新增一级模块或主要依赖；
- 发现公共接口修改会影响另外两套软件；
- 无法满足当前阶段验收条件；
- 测试证明批准方案存在逻辑错误。

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

## 实施纪律

- 小工作包、小测试、小提交。
- 不覆盖用户已有修改，不使用破坏性 Git 操作。
- 每个稳定断点更新 `TASK_STATE.md`。
- 每个阶段完成后生成或更新 `IMPLEMENTATION_REPORT.md`，然后停止并等待 Sol 验收。
- 不得仅写“测试通过”；必须记录命令、通过/失败数量、未执行项和原因。

# Qingzhou Contracts 上位治理

本项目是青舟工业能源软件体系三个业务产品之一，受公共规范权威仓库 `https://github.com/adgo07/Qingzhou-contracts.git` 的上位公共架构与 Contract 治理约束。

1. 当前批准的公共基线只以根目录 `PLATFORM_BASELINE.md` 和 `platform-lock.json` 锁定内容为准。
2. 不得实时采用或自动跟随 `Qingzhou-contracts/main`；中央仓后续变化在本项目显式升级 baseline 前不自动生效。
3. 只有经过显式 baseline 升级、版本/兼容性核对和本项目批准后，新的公共 Contract 才对本项目生效。
4. 普通产品 Bug、单标准公式/解释、业务 UI、产品特有数据库字段及本模块自治问题继续在本仓库解决。
5. 如果发现跨三个产品或跨平台的 Numeric、Unit、Module/Capability、Workspace/Attempt/Record/Result、qzpack、Conformance 等公共 Contract 缺口，不得在本项目永久私自定义同名公共规则。
6. 上述公共缺口应先记录为 RFC Candidate，并按 Qingzhou-contracts 变更流程提交中央仓统一处理；在公共语义未冻结前只允许明确、可逆且不冒充公共规范的本地试验。
7. Qingzhou-contracts 中状态为 `DRAFT / NOT YET RELEASED` 的内容不得在本项目描述成 `FROZEN` 或已发布正式 Contract。
8. 公共 Contract 不得覆盖更具体且有权威依据的标准原文、已批准标准映射、标准专属业务规则和当前业务模块合法自治范围；发生真实冲突时按本仓现有 BLOCKED 流程记录，不得偷偷改掉现有治理。
9. 当前 QZC-A01 接入只建立治理关系和版本锁，不要求重构业务代码、修改计算算法、迁移数据库、抽公共代码或重写 UI。
10. 已发现的本地历史治理文本陈旧或公共 Contract 差距统一记录于 `docs/governance/PLATFORM_ADOPTION_REPORT.md`；该报告本身不授权实施其中的后续迁移。

当前显式锁定基线已升级为 `Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`。Architecture `V2.1` 与 Numeric Contract `v1` 为 **FROZEN**；Numeric v1 已通过本项目单独 compatibility/adoption 任务采用。Unit、Module/Capability、Workspace/Attempt/Record/Result 与 qzpack v1 继续为 **DRAFT**，Quantity public schema 继续 **NOT FROZEN**。具体状态以 `PLATFORM_BASELINE.md` 与 `platform-lock.json` 为准。

# 青舟平台开发前置检查（Qingzhou Platform Contract Preflight）

本节统一约束后续设计、开发、重构、修复、标准接入、Calculator、Numeric、Excel、Record、数据库、Schema、Module、Package、跨平台和导入导出任务。

## 1. 开工前必须检查锁定中央规则

```text
读取本仓 platform-lock.json
→ 确认锁定的 Qingzhou-contracts commit SHA
→ 按 locked SHA 读取相关 Frozen Contract
→ 提取适用于本任务的 MUST / MUST NOT
→ 检查是否冲突并分类
→ 确认后再开始设计或编码
```

不得直接把 Qingzhou-contracts 最新 `main` 当成本仓新基线。只有任务明确要求升级中央 Contract 时，才允许通过独立治理变更 `PLATFORM_BASELINE.md` / `platform-lock.json`。

中央产品交付治理文件：

`docs/governance/PRODUCT_DELIVERY_POLICY_V1.md`

它是 Architecture V2.1 下的 **ACTIVE GOVERNANCE POLICY**，用于统一产品优先级与交付顺序；不是 Frozen Contract，不自动改变本仓 Contract lock。

## 2. 当前产品交付优先级

- **Windows-first**：Windows Desktop 是当前第一正式交付、GUI、测试、打包、文件/Excel 和用户验收平台；
- **Reference Standard first**：当前参考标准为 `GB/T 32151.34—2024` 炭素材料生产企业核算模块，并继续受 GB/T 32150—2025 通用规则约束；
- **Product-core-first**：先确认现有软件核心纵向闭环完整，再补参考标准 Excel；
- **Excel-as-adapter**：后续 Excel 必须作为 Import/Export Adapter 进入同一 Canonical input / Application / Domain / Calculator / result model，不得形成第二套碳核算算法；
- **Cross-platform-ready**：当前不全面开发 Android/iOS/HarmonyOS，但 Domain/Application 不得依赖 Windows UI/API；
- **逐标准扩展**：Reference Standard + Excel 闭环正式验收前，七个计划行业标准继续 catalog-only，不得批量启动新 Calculator。

当前 Reference Standard 真实状态统一见：

`REFERENCE_STANDARD_ROADMAP.md`

## 3. Contract 冲突分类

发现本仓与中央规则不一致时，必须使用：

- `LOCAL DEFECT`：本地实现违反已采用 Frozen Contract；修本地；
- `ALLOWED PROJECT DIFFERENCE`：中央明确允许项目级差异，例如 Carbon p40/HALF_UP Profile；不得为了表面统一强改；
- `REGISTERED DEVIATION`：已登记但未关闭的偏差；按治理状态处理；
- `CENTRAL CONTRACT GAP`：真实业务需求无法被当前中央 Contract 表达；不得在 GHGTOOL 永久私自定义另一套公共规则，应整理业务证据/实际案例/Contract 缺口/Candidate 返回 Qingzhou-contracts。

## 4. 正式报告必须包含平台预检查

后续正式 Design、Execution Report、Acceptance Report 至少记录：

- 当前业务仓 SHA；
- `platform-lock.json` / locked central SHA；
- 本任务相关 Frozen Contract；
- 适用 MUST / MUST NOT；
- 是否发现冲突及其分类；
- 是否需要中央 Contract 修改。

如果任务确实与中央公共语义无关，也必须明确写：`本任务不涉及中央公共 Contract。`

## 5. 中文优先

在不破坏稳定机器接口、JSON/YAML/schema/API/enum/Module ID/Contract ID、Python 标识符、自动化测试和跨平台兼容的前提下：

> 用户界面、治理文档、路线、执行/验收报告、PR/Issue 描述、错误/校验提示、结果解释和面向人的说明优先使用中文。

机器字段与稳定技术标识保持英文；人阅读时优先使用“中文名称（英文标识）”。

## 6. 标准问题与解释治理

开工前必须读取根目录 `STANDARD_ISSUES_REGISTER.md`，确认当前任务是否涉及已有 Standard Issue。

正式 Design、Execution Report、Acceptance Report 的“平台 / Contract 预检查”必须增加：

```text
是否存在与当前任务相关的 Standard Issue：是 / 否
涉及的问题编号：……
本任务是否改变既有软件解释：是 / 否
```

在标准映射、软件设计、Calculator、Golden Case、测试、Excel、用户实际使用或标准更新过程中发现新的标准疑似笔误、歧义、冲突、未规定、术语、引用或软件实现解释问题时，必须先登记台账，再完成正式实现说明。

每个问题必须区分“标准原文事实”“技术判断”“软件实现决定”。不得把内部判断或软件选择写成标准明文，不得静默纠正标准。影响正式业务结果的问题必须能追踪：

```text
Standard Issue
→ Software Decision
→ Rule / Calculator
→ Test / Golden Case
```

解释变化时必须同步检查测试和历史结果兼容性。本治理同步不授权修改碳核算公式、数据库、Excel、UI 或启动其他行业标准 Calculator。
