# HANDOFF — GHGTOOL 当前阶段实施交接

状态：**CURRENT HANDOFF**
最后更新：2026-10-07（GHG-PF01）
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

- 已合并进入main：RS01-A-R1、RS01-B1/B2、RS02-A/B、UAT01-A/B、UAT02与GHG-RPT01（RPT01仍待独立验收）。
- 当前工作包：`GHG-PF01 — 参数与因子注册库基础架构 + 页面重构`；以开工时最新 `origin/main` `c61b29baa2f5d75deae5fc243874d2b1d947bf4a` 为Base，独立分支 `codex/pf01-parameter-factor-library`。不从PR #27派生且不修改PR #27。
- PF01实现Canonical来源表/资产/绑定注册、只读查询投影、标准/文件浏览与全库搜索；Resolver选择策略、正式公式、历史Record语义不变。实现状态：`IMPLEMENTED / AWAITING ACCEPTANCE`；PR #30保持OPEN / UNMERGED，等待独立验收，当前最新Head的Windows CI以PR Checks为准。
- PR #30候选已按13个实际变更文件迁入D盘独立克隆，起点核对为原PR head `4d5d7bc42336afa6d80a9894297454a43f8706d6`，候选文件与只读来源逐字节一致。候选提交`405c34a`已与最新`origin/main` `4f2e1c3d40f91b05e7eaa0dc245aad7e5d019f95`合并，当前本地合并提交为`3b9545952561c929955a05bc5bb9eabfbfa741e3`。合并后定向回归129/129、全量282/282、Canonical/compileall/pip check/四库初始化、Windows standalone发布审计/归档审计及双启动均通过。PR远端仍停在`4d5d7bc`，合并后的候选尚未推送；下一步只更新原PR分支并等待精确head CI，不得把本地测试视为独立验收。
- PF01增量裁定：明确区分来源文件实施日期与具体数据自身适用期。用户选择GB/T 32151.34—2024时，无论核算期间完全早于、跨越或晚于2025-03-01实施日，均继续按所选标准核算并产生非阻断Warning，提醒进入计算状态与新Record。标准实施日期保留在标准元数据；只有来源对具体值另有独立时间适用要求时，Factor/Binding才保留自身有效期。C.1、C.2、C.3及§5.2分组复核已清除无独立适用期证据的95条因子及对应来源绑定的重复`valid_from`；C.3热力缺省因子保持候选资格。真正按期间适用的外部数据（如年度官方电力因子）仍按`accounting_period`筛选。依据与软件决定登记于`GHG-STD-32151-34-005/006`。
- 本包增量不升级 `platform-lock.json` 或 `PLATFORM_BASELINE.md`；标准仍为 `NOT SUPPORTED`。
- RS03-A USER UAT：`PENDING`；PR #27：`OPEN / UNMERGED`；RS03-B：`NOT STARTED`。本包完成后停止，等待独立验收。

PF01范围约束：

```text
1. 来源文件、来源表、参数概念、参考数据资产、来源绑定各自保留明确责任；
2. 相同值可共用不可变数据资产并绑定多处独立来源定位；不同值创建新资产版本，不设置来源权重；
3. Resolver继续决定计算候选与默认值；目录页面只读，不能成为计算真值源；
4. C.4/C.5蒸汽表从版本化Domain Calculator只读展示，不复制第二份数值表；
5. Catalog数据库仅增量新增注册表，不重写Project或历史Record。
6. 本次期间裁定不修改正式公式、Resolver Selection Policy或既有历史Record；须覆盖完全早于、跨实施日、实施日后三类非阻断Warning回归，并确认自身有效期数据仍按期间筛选。
```

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

- **当前状态**：Excel 导入只保留禁用入口与占位说明，未实现。
- **最终定位**（中央 Product Delivery Policy）：Excel 是 Import / Export Adapter，必须与 GUI 进入同一 Canonical Input → 同一 Application → 同一 Domain / Calculator → 同一 Result。
- 正式实现属于 `REFERENCE_STANDARD_ROADMAP.md` 的 **GHG-RS03**；本阶段不得启用或实现。

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

本文件当前对应工作包 **GHG-PF01 — 参数与因子注册库基础架构 + 页面重构**：

- Canonical注册来源表、参考数据资产和来源绑定；同值可共用资产并保留多处定位，不同值分开版本化，不设来源权重；
- SQLite只增量增加只读查询投影；页面按标准/文件查看与全库搜索，按登记表结构显示并隐藏内部标识；
- C.4/C.5仅通过版本化Calculator的只读Adapter展示，不复制蒸汽表；
- Resolver继续独占计算默认候选选择；本包不改变选择策略、正式公式或历史Record语义；
- 明确区分所选标准实施日期与具体因子自身适用期；早于/跨越/晚于实施日均只作非阻断提醒并写入新Record，C.1/C.2/C.3/§5.2中无独立期间证据的重复日期已清除；真正自身具有期间适用性的年度外部因子仍由Resolver按核算期间筛选；
- 状态：`IMPLEMENTED / AWAITING ACCEPTANCE`。PR #27继续 `OPEN / UNMERGED`且未修改；RS03-A用户UAT `PENDING`；RS03-B `NOT STARTED`；标准仍为 `NOT SUPPORTED`。
