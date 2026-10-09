# HANDOFF — GHGTOOL 当前阶段实施交接

状态：**CURRENT HANDOFF**
最后更新：2026-10-10（PR35/36/37/38已合并；GHG-EXB01实施中）
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

- PR35/36/37/38已合并；当前包为 **GHG-EXB01 附录B正式Excel模板与输入**。本分支以 `main@708f78a455790946b4a728029bba768d8fb295fc` 为初始基线，正在纳入最新 `origin/main@a51afbcf684e3845369977e42adc938866726d0b`。具体预检查、批准母版与去公式授权差异见 `docs/exb01/APPENDIX_B_INPUT_DESIGN.md`。
- 批准九表母版成为唯一正式输入模板；原样保留布局，仅按授权移除指定结果公式。软件下载复制受控文件字节；轻量模板注册不引入数据库或通用DSL。
- B.2～B.9形成一次完整核算，仍共享Canonical/Application/Domain。预览零Record；用户明确保存项目后正式核算，成功持久化才提示完成。
- 删除R2专属模板生成/下载/新解析路径；保留OOXML原始词法、Decimal、来源证据、Canonical项目保存恢复和历史EXCEL_R2项目/Record读取。
- 期间、地区与自定义燃料单位不能从静态表头猜测；多物料配对不重复质量，无法唯一表达多实例或批次时定位错误。默认因子只来自正式Catalog/Resolver，不伪造用户提供值来源。
- 不改正式Calculator公式、Numeric、历史Record、数据库结构、Word模型/版式、标准范围；不执行P3-C/D/E/F。当前UI指南只用于Excel页面必要接线。
- 必须专项独立AI按最终diff/head验收；Windows构建/审计、完整回归、CI和原生Excel/WPS保存证据分开。新PR不得自动合并。

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

- **当前状态**：附录B工作簿先严格校验与整体预览，预览不持有Record Repository；用户明确保存有效输入为本地项目，再由同一正式Application UseCase核算、追加Record。项目恢复无需原始Excel文件；修正输入应重新预览工作簿并保存新项目，不把Canonical输入丢失地映射到Qt表单。
- **最终定位**：Excel是输入 Adapter（含输入模板导出），与GUI共用Canonical Input → Application → Domain / Calculator → Result；报告输出只消费已保存Record的冻结ReportModel。
- EXB01当前候选待专项独立验收；Excel词法策略是模块内实现，中央Excel Numeric交换保持OPEN / PARTIAL。PR #27保留历史意图、CLOSED / UNMERGED，不移植旧V1 runtime或四页规范。

### 3.6 架构与分层

- 保持 Presentation / Application / Domain / Infrastructure 分层；Domain 不得依赖 PySide6、SQLite、Windows API、页面控件或桌面弹窗。
- 数据访问通过 Repository 接口。
- 正式核算由 Application UseCase 编排，并要求显式注入正式 Record Repository；纯 Domain Calculator 不持有Repository。预览通过无Repository的 Preview UseCase；SQLite Repository 由 apps 组合根构造，UI不得创建持久化Adapter或隐式降级为内存保存。
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

当前只实施 GHG-EXB01。PR35/36/37/38 的合并属于历史依赖，不替代本包验证；不得沿用旧任务合并授权。必要模板/数值入口与 Record 安全采用专项独立验收，未通过不得宣告支持完整。范围与停止条件见本文件第2节、AGENTS.md和 `docs/exb01/APPENDIX_B_INPUT_DESIGN.md`。

Word 报告版式/分页继续延期，核算结果 Excel 导出已取消；不执行 P3-C/D/E/F，不新增标准、数据库结构、主要依赖或 Frozen adoption。完整实际命令、数量、失败闭环和未执行原因写入 `IMPLEMENTATION_REPORT.md`；当前断点写入 `TASK_STATE.md`。完成后提交独立 PR 等待验收，不自动合并。

### 已合并基线（非当前包）

PR35/36与PR37的业务实现和验收属于历史基线。GHG-UAT03 V2 的需求副本见 `docs/uat03/NEW_ACCOUNTING_V2_REQUIREMENTS.md`；省级电力选择及取消非化石自动证明前置等既有决定，继续按标准问题台账、规则版本与来源快照追踪，不改变冻结 Mapping。

PR #38 的 GHG-UI-P3-AB 已合并。其实现、测试、截图证据及原生人工验收仍为 OPEN 的边界见 `docs/ui/p3-ab/ACCEPTANCE.md`。AB 合并后 Phase 3 暂停；本包不启动 P3-C/D/E/F。
