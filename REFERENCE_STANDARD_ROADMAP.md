# GHGTOOL 参考标准与产品成熟路线

状态：**CURRENT ROADMAP — 本仓唯一当前产品级后续路线**
最后更新：2026-10-03（GHG-GOV-R1）
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

RS04 PASS 后可以达到：`READY_FOR_RELEASE`。

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
| 标准库 | `DONE` | 标准目录、标准详情、官方来源与适用范围治理已具备；GB/T 32151.34 是唯一当前完整可计算行业标准，其余标准 catalog-only |
| 企业信息 | `PARTIAL` | 核算所需基础字段可用；企业主数据/企业层级未实施，不阻断单次正式核算 |
| 核算周期 | `DONE` | 年度/月度/自定义周期语义已进入正式记录快照 |
| 核算边界 | `DONE` | 按本行业核算边界运行；其他行业活动/上下游运输只提示需要其他标准 |
| 排放源 | `DONE` | UIR02 卡片化后的启用/输入模式，经 Application/Domain 校验进入同一 Calculator |
| 活动数据 | `DONE` | 手工录入为正式主路径，不依赖 Excel |
| 参数和因子 | `DONE` | Canonical → `catalog.sqlite` 的参数/因子来源、版本、trace 进入正式计算链 |
| 校验 | `DONE` | 点击计算前执行业务/致命校验；致命错误不生成 Record |
| Calculator | `DONE` | GB/T 32151.34 为当前唯一完整行业 Calculator |
| 分项排放 | `DONE` | 包含各排放源/分项结果与 trace |
| 总排放 | `DONE` | 正式聚合总排放并进入不可编辑记录 |
| 结果解释 | `PARTIAL` | 已能展示结果、输入/规则/参数快照与追踪信息；“计算依据 + 标准依据/来源 + 面向用户解释”需在 RS01 / RS02 集中收口 |
| 正式记录 | `DONE` | 成功计算自动新增不可编辑记录；标准版本/规则/输入/参数/结果快照落库；致命失败不生成记录 |
| 历史记录 | `DONE` | 列表/详情/只读快照、审计与删除治理已通过 G07 |
| Windows | `DONE` | G08 已建立 Windows 离线交付基线；RS05 仍需按正式版 Gate 复核 |
| Excel | `NOT STARTED` | 当前仅禁用入口与占位说明；正式实现属于 RS03 |
| Conformance | `DONE` | N01-C 最终 Independent Re-Acceptance PASS；R1 PROFILE propagation / ambient independence / Unit-Quantity-coefficient 向量与 Numeric v1 adoption 均有执行证据 |
| 下一标准准备状态 | `NOT STARTED` | 其他计划标准保持 catalog-only；须在 RS01～RS05 之后进入 RS06+ |

参考标准总体状态：**`PARTIAL`**（主要缺口为“结果解释集中收口”与“Excel 正式闭环”，分别对应 RS01/RS02 与 RS03）。

## 8. 当前阶段与下一步

- 当前阶段：**路线与治理收口完成，尚未启动任何 GHG-RS 阶段**。
- 下一正式产品阶段：**GHG-RS01 — GB/T 32151.34 完整参考标准业务收口**。
- 第二标准不得早于 **RS05**。

## 9. 相关治理登记项的归属

| 登记项 | 归属 |
|---|---|
| `GHG-UI-001`（超长工作页，结果可达性） | RS01 / RS02 |
| `GHG-UI-002`（普通提示出现内部编号） | RS01 / RS02 |
| `GHG-UI-003`（Excel 双入口） | RS03（随 Excel 正式闭环自然解决） |
| `GHG-UI-004`（`AppRoute` 展示结构硬冻结） | 非阻塞技术债，在适当 UI 工作包中解除，不单独开路线 |
| `GHG-UI-005`（普通结果使用 `ET` 等符号） | RS01 / RS02 |
| `STANDARD_ISSUES_REGISTER.md` | 长期保留；发现标准问题按中央 Standard Development Guide 登记 |
| Standard Mapping 纳入仓库 | RS01 明确前置工作 |

## 10. 本文件不做的事

- 不授权实施 RS01～RS06+ 中的任何实现工作；
- 不修改 Calculator、Canonical、Rule、SQLite schema/迁移、UI 业务语义或标准解释；
- 不修改 `platform-lock.json`、`PLATFORM_BASELINE.md` 或任何中央 Contract；
- 不把 `DRAFT` / `NOT FROZEN` 描述成 `FROZEN`；
- 不建立第二套产品路线。
