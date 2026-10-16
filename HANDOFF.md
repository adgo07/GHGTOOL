# HANDOFF — GHGTOOL 当前阶段实施交接

状态：**原 PR47 合并前有限小修**
最后更新：2026-10-17
Module ID：qz.carbon_accounting
当前 Reference Standard：GB/T 32151.34—2024

本文件是当前阶段交接，不是历史档案。产品路线以 REFERENCE_STANDARD_ROADMAP.md 为准，长期约束以 AGENTS.md 为准，当前执行状态以 TASK_STATE.md 为准。历史过程可由 Git history 恢复，本文件不保留旧状态覆盖段。

## 1. 当前工作包与真实证据

当前在既有 PR47 上做合并前有限小修，包含两个 JSON 的 base / 11 个 basis 人读澄清、现有 HTML 范围提示、checks 生成脚本入仓与复现步骤；审阅产物已按当前源定义同源重生，最终哈希与新 head / CI 由送验评论定位。不接生产、不合并 PR。已核验修复基线为 4e7306992335e213fc0c3baf897022dd174e3acf；origin/main 已同步至 b0c1aa723391772f9aef026b4c0a8619eb61a65b。中央 platform-lock.json 仍锁定 ee5feb0cc34dbd99790500fadd0c4c932e202a20。

本次有限小修的本地 Python 3.12 七模块联合100/100通过，0 failure、0 error，20.402秒；正式交付路径资产测试20/20通过，14.136秒。25个本地 ArtifactTool 意见回收场景通过；新Python CLI测试验证无Node运行、真实Canonical输入、意见保留和混源拒绝。61行（29/21/11）、649技术组合（281有效、368受阻）、442个唯一意见范围保留。原批准V1.2及固定历史电力证据字节不变。

独立Luna/max静态复核确认混源HTML检查缺口已关闭，无剩余阻断。新head及其Windows CI由最终送验评论确认；不使用旧CI237为本次背书，本地未声明完整构建或全软件重验。

审阅表原生 Office 验证为 **NOT_RUN / DEFERRED**。Owner 已同意延期至下一阶段首次正式使用审阅表之前；届时只需小范围完成原生打开、填写意见、表头排序、保存重开和意见回收。此项是延期，不是通过或豁免；CU Esc 仍有效，不自动启动 computer use，也不因此要求全软件重验。

## 2. 业务语义、候选与审阅范围

标准事实、技术判断与软件决定由现行 R11 Mapping（R8 为 PR48 合并历史基线）及 STANDARD_ISSUES_REGISTER.md 分开表达。014、018、019、020 的 Owner 批准软件决定继续有效；019 中的原文错误确认是软件决定，不是官方勘误。机器 CANDIDATE 仅表示执行接入尚未完成。PR47 候选、审阅投影及消费者替换仍未接生产；不改变公式、标准范围、Numeric 或历史记录，也不据此宣布标准正式支持。

Owner 已决定减轻审阅负担：该决定取代原批准 V1.2 第 11 节的全字段可见性盘点要求。不得恢复 GUI 镜像；纯导航、折叠和 advanced 展示设置不作为业务来源规则。仍影响业务适用性的条件必须按 Mapping / STANDARD_SEMANTICS_POLICY.md 记录并执行；减负决定不免除这些条件，也不修改原批准 V1.2 文件。

本任务不涉及中央公共 Contract 修改。Frozen 中央基线保持不变；标准台账不新增、不关闭或重释问题。

## 3. 当前有效的长期产品决定

### 3.1 产品范围

- 当前只交付一个碳核算 Windows 程序；工程结构保留未来 Monorepo 与公共 packages 的扩展位置。
- 第一条完整业务链只实现 GB/T 32150—2025 通用规则与 GB/T 32151.34—2024 炭素材料模块。
- 其余计划标准只允许出现在标准目录并标记核算模块待开发，本阶段不得实现、猜测或复用其计算规则。
- GB/T 32150—2025 作为通用规则层，不作为独立行业核算页面。
- 其他行业活动或上下游运输提示需要适用标准；不得猜算、套算或并入当前标准结果。
- 标准全文与本地 PDF 不进入程序包；打开标准原文只能调用官方网址。

### 3.2 数值与单位

- 输入先以字符串接收并严格解析，禁止先转二进制浮点再进入领域层。
- Domain 使用十进制高精度；中间步骤不舍入（标准明确要求除外）；界面默认显示 2 位小数。
- 正式业务比较使用 full-value exact comparison；is_close() / numerical tolerance 只用于测试与非判定性验证。
- Display rounding 只是 Presentation，不得回流 calculation / comparison。
- Carbon Numeric Profile 为 GHGTOOL_CARBON_DECIMAL40_CURRENT（p40 / ROUND_HALF_UP），是项目专属 Profile，不是平台默认。
- 44/12、44/16 是 quantity transformation 使用的 stoichiometric / standard-formula coefficient；GWP 是 characterization / equivalence factor。三者都不是 ordinary unit conversion multiplier。
- 单位换算通过 UnitService；算法模块不散落手写换算常数。

### 3.3 未计算输入与记录生命周期

- 未点击计算前不生成 Record；同一运行期内离开新建核算页面不弹确认框，返回后输入完整保留。
- 明确保存的项目与未完成输入写入独立 projects.sqlite，可在应用重启后恢复。
- 关闭软件时只在存在尚未保存的项目修改时询问保存、放弃或取消；项目内多个核算单元使用各自状态，不做隐式合并或分摊。
- 致命校验失败不生成 Record；成功计算立即新增不可编辑 Record，状态仅为 COMPLETED 或 COMPLETED_WITH_WARNINGS。
- 历史 Record 只读，不原地修改或覆盖；再次计算必须新增 Record。删除须二次确认并留审计日志。
- 正式 Record 保存输入、结果、参数快照、有效规则集与审计信息；Catalog 或算法升级不得使历史记录漂移。

### 3.4 数据存储与 Project / .qzproj

- Canonical Source 是可校验 JSON；SQLite 是 Windows 查询与部署格式。
- 数据库物理隔离：catalog.sqlite 存官方标准与参数，user.sqlite 存用户设置，records.sqlite 存成功核算记录，projects.sqlite 存可变项目与未完成输入。
- 当前不提供 .qzproj 可移植项目文件；本地项目保存已支持，通过独立 projects.sqlite 恢复。
- 可变 Project / Workspace 状态只写入 projects.sqlite 与独立迁移目录 / Repository，不混入不可变 records.sqlite。
- 删除项目或单元不得级联删除 Record 或审计；runtime form_state 只是 Presentation State，不作为跨平台 Workspace Contract。

### 3.5 Excel 与报告

- Excel 输入 Adapter 对真实工作簿严格校验并整体预览；预览不持有 Record Repository。用户明确保存有效输入为本地项目后，再由同一正式 Application UseCase 核算并追加 Record。
- 项目恢复不依赖原始 Excel 文件；修正输入应重新预览工作簿并保存新项目，不把 Canonical 输入丢失地映射到 Qt 表单。
- Excel 是输入 Adapter，与 GUI 共用 Canonical Input → Application → Domain / Calculator → Result；不形成第二套算法，不新增结果 Excel 导出。
- Word 报告只消费已保存 Record 的冻结 ReportModel，不重算历史。
- EXB01 输入工作簿经原生 Excel / WPS 保存后回导仍未验证，按 [路线中的 RS03 Excel 正式闭环](REFERENCE_STANDARD_ROADMAP.md) 单独跟踪；这与本次审阅表原生 Office 检查不同，不能由其延期状态一并豁免。

### 3.6 架构与分层

- 保持 Presentation / Application / Domain / Infrastructure 分层；Domain 不依赖 PySide6、SQLite、Windows API、页面控件或桌面弹窗。
- 数据访问通过 Repository 接口。正式核算由 Application UseCase 编排并显式注入 Record Repository；纯 Domain Calculator 不持有 Repository。
- SQLite Repository 由 apps 组合根构造；UI 不创建持久化 Adapter 或隐式降级为内存保存。预览通过无 Repository 的 Preview UseCase。
- Canonical-first 不要求所有碳核算算法 JSON DSL 化；复杂标准公式、查表与插值允许保留在版本化 Domain Calculator 中。

### 3.7 参数因子资产与期间判断

- 来源文件、来源表、参数概念、参考数据资产与来源绑定各自保留明确责任。相同值可共用不可变数据资产并绑定多处独立来源定位；不同值使用单独资产版本，不设来源权重。
- Resolver 是计算候选与默认值的唯一入口；目录页面只读，不能成为计算真值源。C.4 / C.5 蒸汽表由版本化 Domain provider 提供，不复制第二份数值表。
- Catalog 数据库仅增量新增注册表，不重写 Project 或历史 Record。
- 对完全早于、跨越及晚于实施日的三个期间分别作非阻断 Warning 分类；自身有效期内的参数仍按现有适用期间筛选。期间裁定不改正式公式、Resolver Selection Policy 或历史 Record。

## 4. 执行边界

- 本地候选与正式生产能力分开；不改正式 Calculator、数据库迁移、不可变 Record、历史兼容行为或用户参考文件。
- PR47 不由执行代理合并；最终合并由源会话负责。PR46、B、N 未授权启动。
- 本次有限小修的新 head 与 CI 须在最终送验评论中确认。Office 延期项在下一阶段首次正式使用审阅表之前完成，不扩大为全软件重验。
