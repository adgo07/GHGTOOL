# HANDOFF — GHGTOOL 当前阶段实施交接

状态：**CURRENT HANDOFF**
最后更新：2026-10-07（GHG-RPT01）
Module ID：`qz.carbon_accounting`
当前 Reference Standard：`GB/T 32151.34—2024`

> 本文件是**当前阶段实施交接**，不是历史全文档案。
> 产品级后续路线以 `REFERENCE_STANDARD_ROADMAP.md` 为准；长期硬规则以 `AGENTS.md` 为准。
> G00～G08、UIR01～UIR04、Post-V1、N01-C/R1、Numeric v1 adoption 的完整过程保存在 Git history 与 `docs/governance/*`，本文件不再复制。

## 1. 本文件的作用与边界

| 文件 | 管什么 |
|---|---|
| `AGENTS.md` | 本仓长期硬规则与中央治理入口 |
| `platform-lock.json` + `PLATFORM_BASELINE.md` | 锁定的中央 Frozen 基线与 Carbon Numeric Profile |
| `REFERENCE_STANDARD_ROADMAP.md` | 唯一当前产品路线（GHG-RS01～RS06+） |
| **本文件** | **当前阶段的实施范围、约束与门禁** |
| `TASK_STATE.md` | 当前执行状态与最近稳定断点 |
| `IMPLEMENTATION_REPORT.md` | 当前/最近一个正式工作包的实施报告 |

规则：

1. 历史阶段正文已从本文件移除，其权威副本在 Git history 与 `docs/governance/*`；
2. 确需引用的少量仍有长期价值的产品决定，只以“当前有效结论”形式保留（见第 3 节），不复制历史过程；
3. 任何历史文档都不得覆盖当前文件的口径；
4. 本文件不写固定绝对路径（`C:\` / `D:\` / `E:\` / `G:\`）作为仓库身份；仓库身份以 GitHub owner/repository + `git origin` 为准。

## 2. 当前阶段

- 已完成并合并：RS01-A-R1及RS01-B1。
- 当前工作包：`GHG-RPT01 — 统一报告模型 + Word核算报告 + Excel R2正式导入模板`；以开工时最新 `origin/main` `c61b29baa2f5d75deae5fc243874d2b1d947bf4a` 为 Base 创建独立分支，没有从 PR #27、PF01 或 UAT02 派生。并行的 UAT02 后续经 PR #31 合并至 `main`（`880d5515e8c48cc01294926f7727de4270f73a66`）；本分支已合入该最新 main 并完成冲突收口。Word 报告、R2模板和逐单元只读预览已实现，本地验证完成；当前等待独立验收。最终 PR head 与 CI 证据见最终交付回复和 PR Checks。
- UAT01-A/B及UAT02已合并；PF01 PR #30 仍为 `OPEN / UNMERGED`，未并入本分支；GHG-RPT01：`IMPLEMENTED / AWAITING ACCEPTANCE`。RS03-A USER UAT：`PENDING`；PR #27：`OPEN / UNMERGED`且本工作包只读参考；RS03-B：`NOT STARTED`。GHG-RPT01 不合并主线，独立验收前保持未验收。
- RS01与RS02已完成并合入main；Golden Freeze、Release Gate和第二标准均未启动；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。
- 本工作包仍须遵守：

```text
1. 用户明确启动对应工作包（一个阶段只建立一个 Goal）；
2. 重新读取 AGENTS.md、REFERENCE_STANDARD_ROADMAP.md、TASK_STATE.md；
3. 使用仓库内当前可追溯、已冻结的 GB/T 32151.34—2024 Standard Mapping；
4. 确认 platform-lock.json 的 locked SHA 未变（未经独立治理批准不得升级baseline）。
```

- 一个阶段未完成、未形成报告或存在 BLOCKED 时，不得进入下一阶段。

## 3. 当前有效的长期产品决定（提炼保留）

### 3.1 产品范围

- 当前只交付一个碳核算 Windows 程序；工程结构保留未来 Monorepo 与公共 packages 的扩展位置。
- 第一条完整业务链只实现 `GB/T 32150—2025` 通用规则 + `GB/T 32151.34—2024` 炭素材料模块。
- 其余计划标准只允许出现在标准目录中并显示“核算模块待开发”，本阶段不得实现、猜测或复用其计算规则。
- `GB/T 32150—2025` 作为通用规则层，不作为独立行业核算页面。
- 遇其他行业活动或上下游运输只提示需要其他标准，不得猜算、套算或并入当前结果。
- 标准全文与本地 PDF 不进入程序包；“打开标准原文”只能调用官方网址。

### 3.2 数值与单位

- 输入数值先以字符串接收并严格解析，禁止先转二进制浮点再进入领域层。
- Domain 使用十进制高精度类型；中间步骤不舍入（标准明确要求除外）；界面默认显示 2 位小数。
- 正式业务比较使用 **full-value exact comparison**；`is_close()` / numerical tolerance 只用于测试与非判定性验证。
- Display rounding 只是 Presentation，不得回流 calculation / comparison。
- Carbon Numeric Profile：`GHGTOOL_CARBON_DECIMAL40_CURRENT`（p40 / `ROUND_HALF_UP`），是**项目专属 Profile，不是平台默认**。
- `44/12`、`44/16` 是 quantity transformation 使用的 stoichiometric / standard-formula coefficient；GWP 是 characterization / equivalence factor。三者都**不是** ordinary unit conversion multiplier。
- 单位换算只能通过 `UnitService`；算法模块不得散落手写换算常数。

### 3.3 未计算输入与记录生命周期

本节描述当前真实行为；任何“离开页面即提示未计算数据丢失”的表述都是已废弃的旧 G07 语义，不再是本仓当前规则。

- 未点击计算前不生成 Record；输入保持在页面状态中。
- **在同一运行期内离开新建核算页面不弹确认框，输入完整保留**：切换到其他页面再返回后，企业名、核算期、边界、排放源状态、燃料与多电力明细等输入仍然存在（回归：`tests/test_g07_records.py::test_leaving_uncomputed_page_preserves_every_input_without_confirmation`）。
- 明确保存的项目与未完成输入写入独立 `projects.sqlite`，可在应用重启后恢复。
- 关闭软件时只在存在**尚未保存的项目修改**时询问“保存 / 放弃 / 取消”；没有未保存修改或没有项目服务时直接关闭（回归：`tests/test_g07_records.py::test_closing_uncomputed_page_closes_without_confirmation`）。
- 项目内多个核算单元之间切换使用各自的单元状态，不做隐式合并或分摊。

记录生命周期本身保持不变：

- 致命校验失败：不执行完整计算，**不生成** Record。
- 成功计算：立即写入一条新的不可编辑 Record；无警告为 `COMPLETED`，有非致命警告为 `COMPLETED_WITH_WARNINGS`。
- 历史 Record 只读，不允许原地修改或覆盖；再次计算必须新增 Record。
- 删除必须二次确认并留审计日志，不得直接修改历史记录。
- 正式 Record 保存输入、结果、参数快照、有效规则集与审计信息；Catalog / 算法升级不得使历史 Record 自动漂移。

### 3.4 数据存储与 Project / `.qzproj`

- Canonical Source 是可校验的 JSON（`data-source/carbon_accounting/catalog.json`）；SQLite 只是 Windows 查询与部署格式。
- 数据库物理隔离：`catalog.sqlite`（官方标准与参数）、`user.sqlite`（用户设置）、`records.sqlite`（成功核算记录）、`projects.sqlite`（可变项目与未完成输入）。
- **Project 保存与 `.qzproj` 是两件事，必须区分**：

```text
.qzproj 可移植项目文件：当前仍不提供（公共交换格式尚未冻结）
本地项目保存：已支持，使用独立 projects.sqlite（含未完成输入跨启动恢复）
```

- 可变 Project / Workspace 状态只写入 `projects.sqlite` 及独立迁移目录 / Repository，**不得混入**不可变 `records.sqlite`。
- 项目或单元删除不得级联删除 Record 或审计。
- runtime `form_state` 只是 Presentation State（含 Qt `objectName()`、`currentIndex()`），不得作为跨平台 Workspace Contract。

### 3.5 Excel 的当前状态与最终定位

- **当前状态**：GHG-RPT01 增加 R2 标准输入模板下载与逐核算单元只读预览，采用与桌面共用的 Domain / Calculator；预览不保存 Project / Workspace / Record。正式 Excel 写入、结果导出尚未实现，模板入口处于 RPT01 独立验收中。
- **最终定位**（中央 Product Delivery Policy）：Excel 是 Import / Export Adapter，必须与 GUI 进入同一 Canonical Input → 同一 Application → 同一 Domain / Calculator → 同一 Result。
- Excel 完整闭环仍属于 `REFERENCE_STANDARD_ROADMAP.md` 的 **GHG-RS03**。

### 3.6 架构与分层

- 保持 Presentation / Application / Domain / Infrastructure 分层；Domain 不得依赖 PySide6、SQLite、Windows API、页面控件或桌面弹窗。
- 数据访问通过 Repository 接口。
- Canonical-first **不等于**所有碳核算算法都必须 JSON DSL 化：复杂标准公式、查表/插值允许保留在版本化 Domain Calculator 中。

## 4. 阶段执行流程（每次启动一个 Goal）

```text
开始
  → 从最新 origin/main 创建任务分支
  → 读取 AGENTS.md / REFERENCE_STANDARD_ROADMAP.md / TASK_STATE.md / STANDARD_ISSUES_REGISTER.md
  → 按 platform-lock.json 的 locked SHA 读取相关 Frozen Contract
  → 执行平台 / Contract 预检查（见 AGENTS.md）
  → 只实施本阶段范围

实施
  → 小工作包、小测试、小提交
  → 不覆盖用户已有修改；不使用破坏性 Git 操作
  → 不修改、删除或覆盖 计算表/ 中的用户参考文件

结束
  → 更新 TASK_STATE.md（当前状态文件，不追加历史流水账）
  → 重写 IMPLEMENTATION_REPORT.md 为本次工作包报告
  → 运行本阶段要求的验证命令并记录真实结果
  → 提交、推送分支、创建目标为 main 的 PR
  → 等待最新 PR head 的 Windows / Python 3.12 GitHub Actions
  → 停止，等待独立验收
```

## 5. 测试层级与证据纪律

| 层级 | 内容 |
|---|---|
| L1 | 本工作包定向单元测试 |
| L2 | 相关模块回归（Calculator / Record / UI / 持久化） |
| L3 | 全量 `unittest discover`、`compileall`、`pip check`、Canonical 校验、数据库从零初始化、（涉及交付时）standalone 构建与发布审计 |

证据纪律：

- 以磁盘、Git 与测试结果为准，不得以上一次对话的文字推断完成状态；
- 不得只写“测试通过”，必须记录命令、通过/失败数量、未执行项与原因；
- 必须明确区分**本地执行**与**GitHub Actions 执行**的证据来源，不得冒充本地运行；
- 报告中的检查结论必须绑定被检查的 commit / PR head。

## 6. 停止并上报条件

遇下列情况停止相关工作，不得自行作重大决定：

- 标准原文存在真实歧义，需要选择软件解释；
- 会改变正式业务计算结果或标准适用范围；
- 会改变正式产品范围；
- 需要破坏性数据库迁移；
- 需要修改已经采用的 Frozen Contract；
- 文档内部或与实际代码存在关键冲突；
- 原始标准或官方来源无法支持准备录入的值；
- 需要新增一级模块或主要依赖（影响架构或另外两套软件时必须先确认）；
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
需要决策的具体问题：
```

## 7. 当前阶段范围声明

本文件当前对应工作包 GHG-RPT01 — 统一报告模型 + Word 核算报告 + Excel R2 正式导入模板：

- ReportModel 位于 Application 层，只读一条不可变 AccountingRecord 已保存的输入、结果、参数、Trace、Provenance、Reporting 与资格快照；不调用 Calculator、不查当前 Catalog、不更改历史 Record。Word renderer 输出 DOCX；补充信息写入 records.sqlite 新增追加式报告导出历史表，并记录审计事件。
- 报告按 B.1–B.9 展示快照中的业务输入、参数来源、逐项结果与追溯说明；旧快照不足时提示缺失，不补算、不伪造。Word 报告不展示内部 Rule、Trace、参数或 Record 编号。
- Excel R2 有十张中文可见表和隐藏模板元数据页，B.2–B.9 分页录入，支持动态行、空白/显式零区分及严格 OOXML Decimal 词法入口；每个核算单元单独复用当前 Domain / Calculator 预览，不写 Project / Workspace / Record，不提供 Excel 结果导出。
- PR #27 只作只读参考；共享物料标准化能力在本任务 Base 中已经存在并继续复用。报告、R2 导入预览与企业文件输出由本工作包实现，未引入 PR #27 未合并代码作为正式依赖。
- 并行集成：在执行期间 `origin/main` 从开工 Base 前进至 PR #31 的合并提交 `880d5515e8c48cc01294926f7727de4270f73a66`。已确认远端目标分支仍为本包 head 后，将最新 main 合入本分支；仅 HANDOFF、IMPLEMENTATION_REPORT、REFERENCE_STANDARD_ROADMAP、TASK_STATE 有文档冲突，按 RPT01 当前状态与 main 已合并的 UAT02 状态合并；`packages/ui/pages.py` 自动合并，其他 UAT02 源码与测试由 main 带入。
- 未修改计算公式、Canonical 标准数据、中央 Frozen Contract、`platform-lock.json`、正式记录生命周期或用户目录 `计算表/`；没有启动 RS03-B、Golden、Release 或第二标准。
- GHG-RPT01：`IMPLEMENTED / AWAITING ACCEPTANCE`；RS03-A USER UAT：`PENDING`；PR #27：`OPEN / UNMERGED` 且保持只读；RS03-B：`NOT STARTED`；Excel 结果导出：`NOT STARTED`；GB/T 32151.34—2024 仍为 `NOT SUPPORTED`。
