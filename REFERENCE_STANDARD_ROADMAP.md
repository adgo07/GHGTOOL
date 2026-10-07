# GHGTOOL 参考标准与产品成熟路线

状态：**CURRENT ROADMAP — 本仓唯一当前产品级后续路线**
最后更新：2026-10-08（RS03 Excel正式闭环；候选待独立验收）
Module ID：`qz.carbon_accounting`
当前 Reference Standard：`GB/T 32151.34—2024`（本仓当前称“炭素材料生产企业核算模块”，准确标准元数据以正式标准目录为准）
通用规则层：`GB/T 32150—2025`

> 本文件是 GHGTOOL **唯一**的产品级后续路线。
> 不得再建立 `MASTER_PLAN_V2` / `POST_V1_PLAN` / `S0-S6_PLAN` 等平行路线文件。
> 第三方提案只作为本路线的修正输入，不构成新的权威路线。
> 本文件只定义产品成熟路线与阶段出口条件，不授权在治理任务中实施任何阶段。

## 1. 权威层级与读取方式

| 层级 | 文件 | 读取方式 |
|---|---|---|
| 中央 Frozen 基线 | 本仓 `platform-lock.json` + `PLATFORM_BASELINE.md` | 按 locked SHA 读取中央 Frozen 权威文件 |
| 中央 ACTIVE 指南 | 中央 `GUIDE_INDEX` / `PRODUCT_DELIVERY_POLICY_V1` / `STANDARD_DEVELOPMENT_GUIDE_V0.1` / `UI_DESIGN_GUIDELINES_V0.1` | 按中央当前正式合并版本读取，**不是 Frozen Contract** |
| 本仓长期硬规则 | `AGENTS.md` | 长期有效 |
| 本仓当前产品路线 | 本文件 | 唯一当前路线 |
| 本仓当前阶段交接 | `HANDOFF.md` | 当前阶段实施说明 |
| 本仓当前执行状态 | `TASK_STATE.md` | 当前任务与最近稳定状态 |
| 本仓当前实施报告 | `IMPLEMENTATION_REPORT.md` | 当前/最近一个正式工作包 |
| 历史证据 | Git history、`docs/governance/*`、`UI_CURRENT_STATE_AUDIT.md` | 只作证据，**不得覆盖当前状态** |

冲突处理顺序：locked Frozen Contract → 中央 ACTIVE 指南 → 本仓 `AGENTS.md` → 本文件 → `HANDOFF.md` / `TASK_STATE.md`。历史证据不参与当前口径裁决。

## 2. 平台 / Contract 预检查（本路线适用）

| 项目 | 结果 |
|---|---|
| 当前业务仓基线 | 见本文件生成时的 `git rev-parse origin/main`（不把历史 SHA 写死为本文件正文） |
| `platform-lock.json` locked SHA | `Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`，`auto_upgrade=false` |
| Architecture | `V2.1` **FROZEN** |
| Numeric Contract | `v1` **FROZEN / ADOPTED** |
| Numeric Profiles / Conformance Vector | `v1` **FROZEN / ADOPTED** |
| Unit Contract | `v1` **DRAFT**（未采用为 Frozen） |
| Quantity public schema | **NOT FROZEN** |
| Module / Capability | `v1` **DRAFT** |
| Workspace / Attempt / Record / Result | `v1` **DRAFT** |
| qzpack | `v1` **DRAFT** |
| Carbon Numeric Profile | `GHGTOOL_CARBON_DECIMAL40_CURRENT`（Decimal、p40、`ROUND_HALF_UP`、full-value exact comparison、无 global business epsilon）——**项目专属 Profile，不是平台默认** |
| 适用 MUST | Windows-first；Reference Standard first；Product-core-first；Excel-as-adapter；Cross-platform-ready；declared-profile consistency；ambient independence；full-value exact formal comparison；用户可见内容中文优先 |
| 适用 MUST NOT | 不自动跟随中央 `main`；不自动升级 Frozen Contract/baseline；不把 ACTIVE 指南当 Frozen；不把 `44/12`、`44/16`、GWP 当 ordinary unit conversion；不让 display rounding / tolerance 进入正式判定；不在本仓私自定义公共语义 |
| 是否发现冲突 | 否 |
| 是否需要修改中央 Contract | 否 |

## 3. 最终产品目标

> **完成一个正式 Windows 版本，使软件完整、可信地支持 GB/T 32151.34—2024 的正式核算业务。**

“完整支持”指：

> **标准要求的软件支持链完整。**

“完整支持”**不**自动等于以下外围能力：

- 完整企业主数据系统；
- 企业组织层级管理 / CRM；
- 多用户与审批流；
- 云端服务；
- Word/PDF 全套报告系统；
- 全部未来碳核算标准；
- 移动端。

上述能力缺失**不得**被用来把 GB/T 32151.34 永久标成“不完整”。凡标准正式使用与中央 Product Delivery Policy 未要求的，一律不纳入本路线的“完整支持”定义。

## 4. 产品成熟路线总览

路线统一采用产品成熟逻辑，**不复制** ECQuota / EquipEffi 的阶段编号：

```text
GHG-RS01  GB/T 32151.34 完整参考标准业务收口
     ↓
GHG-RS02  生命周期 / Record / 结果解释 / Trace 最终闭环
     ↓
GHG-RS03  Excel 正式闭环
     ↓
GHG-RS04  Golden / Formal Support Candidate Gate
     ↓
GHG-RS05  Windows 正式版 Release Gate
     ↓
GHG-RS06+ 第二标准及后续演进
```

阶段顺序不得颠倒；每阶段必须形成可核验证据并经独立验收后才能进入下一阶段。

## 5. 阶段定义

### GHG-RS01 — GB/T 32151.34 完整参考标准业务收口

一句话目标：回答“**标准要求的软件业务能力是否完整落地**”。

RS01内部工作包（不是新产品阶段）：

- **RS01-A**：专业依据入仓、核心功能审计、Standard Completeness Matrix及Gap Register；不修改业务实现。R1已将准确冻结SM01-R6原样纳入 `specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md`，Matrix位于同目录CORE_CHECK，缺口见GAPS。
- **RS01-B**：按已验收Gap修复标准核心业务能力并增加对应测试；B1/B2是其内部工作包，不是新产品阶段。
- **RS01-B1 — Calculation Safety & Reference Data Closure**：单条业务输入下消除非法ParameterValue和未确认碳酸盐造成的错误结果，接通标准参考数据并使参数来源可追溯。已合并到main。
- **RS01-B2 — Multi-entry Business Input Closure**：同一核算单元支持多过程/多能源来源逐项录入、逐项计算和按标准汇总。已合并到main；最新合并提交为 `8724a39cb7139aa9ae5eeeee9db7455e8be5a939`。
- B1关闭GAP-002/003/005/006/007/010；B2关闭GAP-001/004/008/011。GAP-009为不阻止实施的provenance debt。
- 历史4条已确认标准问题正式登记为RESOLVED，均为项目执行口径，非官方勘误；本轮无新增未解决Standard Issue Gap。GAP-009仅剩历史批准附件provenance debt，不阻止B，也不要求重新确认既有R6解释；未来变更解释前须加强证据或重新确认。

必须建立并逐项填写 **Standard Completeness Matrix**：

```text
标准条款 / 附录
  → Standard Mapping
  → Canonical / reference data
  → 用户输入
  → 自动参数
  → Validation
  → Rule
  → Formula / Calculator
  → Result
  → Trace
  → UI
  → Record
  → Test / Golden
```

正式输入：

- 仓库内**当前可追溯的** `GB/T 32151.34—2024` Standard Mapping；
- `STANDARD_ISSUES_REGISTER.md`；
- 现有 Canonical / Rule / Calculator / 测试现状；
- `UI_CURRENT_STATE_AUDIT.md` 中归属本阶段的登记项。

前置工作（若当前权威 Mapping 尚未纳入仓库）：

- 把权威 Mapping 纳入仓库**必须标为 RS01 的明确前置工作**，不得假装已完成；
- 不得继续长期只依赖某台电脑上的历史外部路径。

该Mapping入仓前置已由RS01-A-R1完成，源文件与复制件SHA256一致；标准PDF保持外置，仅记录文件名、页码与SHA256。冻结Mapping正文中的历史路径不作为当前仓库身份或第三方执行前提。

本阶段的边界规则（重要）：

> **没有证据时不得顺手改；发现真实标准功能缺陷时必须修。**

因此 RS01 **不得**被缩窄成“只改结果解释 UI”。如果 Standard Completeness Matrix 证实存在：

- 标准条款遗漏；
- 排放源遗漏；
- 输入字段遗漏；
- Canonical / reference data 缺失；
- Validation 错误；
- Rule / Calculator 缺失或错误；

则 RS01 的后续**实施任务**允许修改这些内容（仍须遵守相应授权与冻结 Contract）。

本路线**不预先永久规定**“RS01 不得修改 Calculator / Canonical / Rule”。

出口条件：Standard Completeness Matrix 有可核验证据；发现的差异已分类（本地实现缺陷 / 标准问题 / 公共 Contract 缺口）并记录去向；本仓只保留一套当前口径。

### GHG-RS02 — 生命周期 / Record / 结果解释 / Trace 最终闭环

一句话目标：让正式结果**可追溯、可复现、可解释**，并且历史不漂移。

RS02内部工作包（不是新产品阶段）：

- **RS02-A — Record Evidence & Reporting Data Closure**：为新Record固定结构化Trace、Provenance、报告/证据数据及报告周期资格；已实现并合并于PR #25。
- **RS02-B — Result Explanation & Presentation Closure**：面向普通用户的结果依据解释与B.1～B.9展示；已由PR #26合并进入main；不代表标准已SUPPORTED。

本阶段**不是**重新开发 Record。重点收口：

- 成功核算产生正确正式 Record；
- 致命失败不生成正式 Record；
- Record 不可编辑、每次成功计算新增一条；
- 参数 / 因子 / Rule / Calculator version 可追踪；
- 历史 Record 不随新 Catalog / Calculator 自动漂移；
- Project / Workspace 与正式 Record 明确分离；
- 软件关闭并重新进入后结果正确恢复；
- 用户能理解“为什么得到这个结果”；
- 标准依据、公式依据、参数与因子来源可读；
- 必要的专业 Trace 保留；
- 普通用户层不泄露无意义内部 ID。

本阶段承接 `UI_CURRENT_STATE_AUDIT.md` 中 `GHG-UI-001`、`GHG-UI-002`、`GHG-UI-005` 的收口。**不再启动 UIR05 / UIR06 等平行路线。**

出口条件：上述各项均有可核验证据；普通层/专业层信息层级符合中央 UI 指南的渐进展示方向；技术审计能力未被删除。

### GHG-RS03 — Excel 正式闭环

一句话目标：让 Excel 成为**同一个业务内核的 Import / Export Adapter**，而不是第二套算法。

RPT01的R2输入模板与严格逐单元预览已合入main；PR #34的Application UseCase收口也已获用户接受并合并。当前用户授权执行RS03正式闭环：有效单元明确保存为Canonical本地项目、跨启动恢复、明确正式核算追加Record，以及记录页导出冻结Excel报告。用户已批准projects.sqlite可空字段增量迁移003；旧GUI项目兼容，不改变records.sqlite Schema或公式。当前候选等待独立验收；公共Excel Decimal交换规则仍OPEN / PARTIAL。PR #27继续CLOSED / UNMERGED、只读，不移植旧V1实现。

Excel 设计、实现、GUI↔Excel Conformance 属于**同一产品阶段内部工作包**，不拆成独立产品阶段。

正式结构必须是：

```text
GUI ─────┐
         │
Excel ───┼→ Canonical Input
         │        ↓
         │   Application
         │        ↓
         └→ Domain / Calculator
                  ↓
                Result
                  ↓
                Record
```

必须覆盖：

- Excel 模板；
- Sheet / 字段识别；
- 多燃料；
- 多电力明细；
- 核算期间；
- 核算边界；
- 参数 / 因子；
- 单元格原始类型；
- Decimal ingress；
- 空值；
- 百分数；
- 日期；
- 科学计数法；
- 公式单元格；
- 中文文本数字；
- 单位；
- 错误输入；
- GUI ↔ Excel 同输入同业务结果；
- 正式 Record。

约束：

- 不得建立第二套 Excel 算法；
- 不得因为 Excel 库返回 Python `float` 就认为满足精确十进制要求；
- 若 Excel Decimal ingress 仍存在中央 OPEN 项，**如实记录 `OPEN` / `PARTIAL`**，不得在 GHGTOOL 私自冻结平台规则。

出口条件：同一组业务输入的 GUI 与 Excel 得到相同的输入语义、状态、等级/结论与核心业务结果；正式 Record 语义与 GUI 完全一致。

### GHG-RS04 — Golden / Formal Support Candidate Gate

一句话目标：证明 GB/T 32151.34 不是“代码看起来能运行”，而是真正具备**正式支持条件**。

必须形成少量但权威的 **Golden Cases**。

Golden Case 预期值来源只允许：

- 标准事实；
- Standard Mapping；
- 人工独立计算；
- 明确业务依据。

**禁止**用当前 Calculator 自动产生结果，再把这个结果反过来当作 Golden truth。

Golden 至少应逐步覆盖：

- 典型完整核算；
- 主要排放源；
- 多燃料；
- 多种电力来源；
- 非化石能源电力；
- 煅烧；
- 焙烧；
- 石墨化；
- 烟气焚烧；
- 蒸汽 / 热力；
- 零值；
- 缺失；
- 错误；
- 边界；
- 不属于本标准范围的活动；
- 参数来源与版本；
- 历史记录稳定性；
- GUI ↔ Excel parity。

RS04 PASS 表示 Golden / Formal Support Candidate Gate 完成，**允许进入 RS05**。

本阶段**不新增任何标准支持状态**。标准支持状态仍只使用中央 `STANDARD_DEVELOPMENT_GUIDE_V0.1` 定义的五种合法状态（`CATALOG_ONLY` / `MAPPING` / `READY_FOR_IMPLEMENTATION` / `IMPLEMENTED` / `SUPPORTED`），RS04 完成后通常仍为 `IMPLEMENTED`，只有 RS05 正式验收通过后才推进为 `SUPPORTED`。

但**不得**在 Windows 正式版 Gate 之前仅凭单元测试宣布最终 Release 完成。

### GHG-RS05 — Windows 正式版 Release Gate

本阶段**不是重做 G08**。G08 已证明 Windows delivery baseline 存在；RS05 要证明的是“**完整 GB/T 32151.34 产品能够作为正式 Windows 产品交付**”。

至少覆盖：

- Windows 10 / 11；
- 正常启动、正常退出；
- 中文界面、中文路径、中文企业名；
- 高 DPI；
- 数据库首次初始化；
- 用户数据目录；
- Project 保存 / 恢复；
- 正式 Record / 历史 Record；
- Excel；
- 错误输入不崩溃；
- 无开发环境的目标机器；
- 正式构建；
- 发布包审计；
- Golden；
- Full regression。

RS05 PASS 后才允许把 `GB/T 32151.34—2024` 标记为当前软件的正式支持状态。

具体状态枚举必须读取**中央当前 Standard Development Guide**，不得自行发明。

### GHG-RS06+ — 第二标准与后续演进

只有 RS01～RS05 完成后，才进入新的主要行业标准。

第二标准同时承担**架构扩展验证**：如果新增一个标准需要重写 AppShell、Record、Excel framework、Calculator framework、数据库基本结构或标准库基本结构，必须判断“是**新标准真实特殊**，还是**第一标准留下了错误抽象**”。

但**不得**为了未来标准提前做大型通用框架。

第二标准本身必须走中央 `STANDARD_DEVELOPMENT_GUIDE_V0.1` 的四阶段（Stage A 标准整理 → Stage B 软件接入设计 → Stage C 实现 → Stage D 正式验收），顺序不得颠倒；支持状态按 `CATALOG_ONLY → MAPPING → READY_FOR_IMPLEMENTATION → IMPLEMENTED → SUPPORTED` 逐级推进，**不得无证据跳级**。

## 6. 开发环境维护不属于产品阶段

本地 Python 环境、虚拟环境、依赖可用性问题属于 **Development Environment Maintenance**：

- 不是 `GHG-RS00`；
- 不进入本路线编号；
- 不得因为本机 Python / venv 暂时不可用而阻塞产品路线。

正式验证证据允许来自：本地测试、GitHub Actions（Windows / Python 3.12）。

但报告**必须如实区分证据来源**，不得把 CI 结果写成“本地已执行”，也不得把本地未执行项隐去。

## 7. 当前真实能力盘点

状态取值只允许：`DONE` / `PARTIAL` / `NOT STARTED` / `BLOCKED`。

| 项目 | 状态 | 证据与说明 |
|---|---|---|
| 标准库 | `PARTIAL` | 标准目录/详情已具备；本地calculation_status=IMPLEMENTED只表示当前Catalog可用Calculator，不是中央标准支持状态，也不表示标准完整支持；GAP-007已关闭；PF01注册库（PR #30）已合并进入main；其余catalog-only |
| 企业信息 | `PARTIAL` | 核算所需基础字段可用；企业主数据/企业层级未实施，不阻断单次正式核算 |
| 核算周期 | `DONE` | 年度/月度/自定义周期语义已进入正式记录快照 |
| 核算边界 | `DONE` | 按本行业核算边界运行；其他行业活动/上下游运输只提示需要其他标准 |
| 排放源 | `DONE` | 同一核算单元内多煅烧/焙烧/石墨化/烟气治理实例及输出电力来源可逐项录入和计算；GAP-004/011已关闭；不等于正式标准SUPPORTED |
| 活动数据 | `PARTIAL` | 多过程、多物料和购入/输出热力及电力来源逐行输入已实现；UAT02仅修录入交互与长表单可用性，完整标准支持仍待后续门禁 |
| 参数和因子 | `DONE` | C.1/C.2/K1-K3/脱硫缺省值已进入Canonical；购入/输出热力支持逐来源实测因子并保留适用默认及来源 |
| 校验 | `DONE` | Domain ParameterValue门禁及多实例错误定位/整体阻断均有回归；GAP-003/008已关闭 |
| Calculator | `DONE` | 核心单组公式一致；燃料质量/体积换热、C.4/C.5查表与插值由版本化Calculator执行。此DONE只指已审计计算路径，不等于多过程UI覆盖或标准完整支持 |
| 分项排放 | `DONE` | 包含各排放源/分项结果与 trace |
| 总排放 | `DONE` | 多实例直接排放与多来源间接排放按标准逐项汇总并写入不可编辑记录；Record详情展示直接、净间接及含间接排放总量 |
| 结果解释 | `DONE` | Record详情以已保存快照呈现标准报告数据、逐项结果和来源依据；RPT01（PR #32）已合入main，增加基于同一不可变Record快照的Word报告导出；不重算、不查询当前Catalog，不等同于标准SUPPORTED |
| 普通核算录入与错误反馈 | `PARTIAL` | UAT01-A/B及UAT02已合并进入main（PR #28/#29/#31）；UAT02收口滚轮、动态布局、失败定位、来源提醒和结果查看；不改变正式公式或Record生命周期 |
| 正式记录 | `DONE` | 新核算继续新增不可编辑Record；新增Record含Trace/Provenance/报告与资格快照，致命失败不生成Record；本地扩展不代表中央DRAFT Contract |
| 历史记录 | `DONE` | 只读展示Record自身输入、参数、结果、报告和Trace快照；旧记录缺失、空值及损坏状态有明确提示，不查询当前Catalog补历史值 |
| Windows | `DONE` | G08 已建立 Windows 离线交付基线；RS05 仍需按正式版 Gate 复核 |
| Excel | `PARTIAL` | RS03候选已实现严格R2预览、有效Canonical项目保存/恢复、同UseCase正式核算追加Record及冻结Excel报告导出；用户批准迁移003，旧项目兼容；独立验收待完成，中央Excel Numeric交换仍OPEN / PARTIAL |
| Conformance | `DONE` | N01-C 最终 Independent Re-Acceptance PASS；R1 PROFILE propagation / ambient independence / Unit-Quantity-coefficient 向量与 Numeric v1 adoption 均有执行证据 |
| 下一标准准备状态 | `NOT STARTED` | 其他计划标准保持 catalog-only；须在 RS01～RS05 之后进入 RS06+ |

参考标准总体状态：**`PARTIAL`**。既有11条Gap中10条已关闭，GAP-009仍为非阻塞provenance debt。PR #33/#34已获用户批准合入main；当前执行用户授权的RS03 Excel正式闭环，候选验证见IMPLEMENTATION_REPORT与TASK_STATE，等待独立验收。原生鼠标视觉、Excel/WPS打印、Word分页和长标题可读性仍待独立验收；Golden/正式标准支持及Release门禁留在RS04/RS05。PR #27保持CLOSED / UNMERGED。既有6条RESOLVED标准解释不变；GB/T 32151.34—2024仍为NOT SUPPORTED。

## 8. 当前阶段与下一步

- 当前工作包：**GHG-RS03 Excel正式闭环（步骤4）**，用户已启动并批准Canonical项目存储；PR #34已接受合并作为主线依赖。本包候选待独立验收，不自动合并新PR。
- GUI与Excel共用配置一致的Calculator / Preview UseCase / 正式UseCase；预览和项目保存零Record，正式成功追加不可变Record与导入来源快照。项目库增量迁移003，记录库Schema、公式、Numeric及Resolver不变。
- 报告通过冻结ReportModel输出Word/Excel；Excel仅输出显示字符串、没有第二套算法或公式，不是R2可重导入模板。中央Numeric交换规则仍OPEN / PARTIAL。
- 验证见IMPLEMENTATION_REPORT与TASK_STATE；原生鼠标视觉、Excel/WPS打印、Word分页和长标题仍需独立验收。RS04～RS06+未启动，不宣布标准SUPPORTED。
- PR #27保持CLOSED / UNMERGED且只读；其旧V1 runtime和四页规范不移植。

## 9. 相关治理登记项的归属

| 登记项 | 归属 |
|---|---|
| `GHG-UI-001`（超长工作页，结果可达性） | RS01 / RS02 |
| `GHG-UI-002`（普通提示出现内部编号） | RS01 / RS02 |
| `GHG-UI-003`（Excel 双入口） | RS03（随 Excel 正式闭环自然解决） |
| `GHG-UI-004`（`AppRoute` 展示结构硬冻结） | 非阻塞技术债，在适当 UI 工作包中解除，不单独开路线 |
| `GHG-UI-005`（普通结果使用 `ET` 等符号） | RS01 / RS02 |
| `STANDARD_ISSUES_REGISTER.md` | 长期保留；发现标准问题按中央 Standard Development Guide 登记 |
| Standard Mapping 纳入仓库 | RS01明确前置，A-R1已完成准确R6入仓；历史附件债见GAP-009 |

## 10. 路线与实施授权边界

- 路线不自行授权未来阶段；本轮用户明确启动RS03（步骤4）并批准Canonical项目模型与增量迁移，RS04～RS06+未获启动；
- Excel预览保持无Record写入；明确保存项目和正式核算通过共享Application完成，结果导出读取冻结Record；当前候选待独立验收；
- PR #27保留历史验收意图，保持CLOSED / UNMERGED且只读，不修改、重新打开或合并；旧V1 runtime/四页规范已被main中的R2替代，不移植为生产代码。R2既有6条集成测试为历史证据；
- PF01的期间裁定及测试历史继续按其合入实现和`GHG-STD-32151-34-005/006`追溯；本次不改变正式公式、Resolver策略或历史Record；
- 不修改 `platform-lock.json`、`PLATFORM_BASELINE.md` 或任何中央 Contract；
- 不把 `DRAFT` / `NOT FROZEN` 描述成 `FROZEN`；
- 不建立第二套产品路线。
