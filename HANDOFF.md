# HANDOFF — GHGTOOL 当前阶段实施交接

状态：**PR46燃料B1与电力B执行中**；更新：2026-10-17。
Module ID：qz.carbon_accounting；当前Reference Standard：GB/T 32151.34—2024。

路线以REFERENCE_STANDARD_ROADMAP.md为准，长期规则以AGENTS.md为准，当前进度与真实证据见TASK_STATE.md / IMPLEMENTATION_REPORT.md。历史过程由Git恢复，不堆叠旧覆盖段。

## 1. 当前授权与基线

基线整合已由源会话验收PASS（限定范围）；Owner授权继续燃料B1和电力B。原PR46工作树为唯一共享集成工作树，两条专属实现线在独立工作树提交小补丁；最终仍由源会话验收，不另邀第三方。

实际origin为adgo07/GHGTOOL，分支codex/ghg-standard-input-unification；原head77d36a155323bc82199cb516c4ac58a2e1c60309，整合main d0c26351200099a8e62c8adabadac266c77f7c8c。PR47/A已合并，R11有效Mapping和已批准决定保留；A的执行候选不是已生产采用的共享提供者。

本轮只做燃料B1与电力B正式闭环及相应已批准来源修正。不合并PR46、不关闭PR45，不实施材料/过程/烟气/蒸汽等其他业务段或N，不改公式、Numeric、数据库结构、历史Record或标准范围。

## 2. 能力保留与当前差异

- 保留PR46已有标准分派、逐字段来源政策、燃料确认/草稿、过程与FGD、五表查询/Resolver/三级选择、Canonical项目恢复、Record/Word冻结投影、视觉与导航优化。
- 正式模板v4/2.2.0逐字节下载及v2/v3历史兼容保留；现有模板、Catalog和发布白名单不因整合而重写或放开。
- Issue010明确批准全国表1/4/5、区域表2、省级表3；全国表4/5不自动补位，失效选择要求重选。014 OTHER与官方五表独立，非化石零因子及输出扣减不扩解释。
- 已定位PR47冻结G05快照两类与PR46生产五类的两条parameter_ids差异。已仅按010对齐候选范围并同修订重生派生资产；不以Python实现充当批准权威。PR47固定提交及原工作树的证据/意见保留，当前派生视图不能伪称历史原件。
- 生产共用Canonical提供者的接管仍留B。现有Python政策与R11之间燃料LHV/FCh、DIRECT、材料、014 OTHER、017/018/020等待接入差异按各批准决定逐段迁移，不在本基线整合中隐式改变结果，也不宣称已经生产同源。
- PR46既有导航计时与v4原生回导是旧head证据；本轮定向/全量/CI必须单列真实结果，不能沿用旧绿色CI。

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
- 当前PR46模板v4/2.2.0已有旧head的WPS TEMP保存回导17/17及17项数据验证语义证据；本轮保留模板原字节，未重新执行原生Office。此历史证据不替未来模板修订背书，也不替PR47规则审阅表原生验证背书。

### 3.6 架构与分层

- 保持 Presentation / Application / Domain / Infrastructure 分层；Domain 不依赖 PySide6、SQLite、Windows API、页面控件或桌面弹窗。
- 数据访问通过 Repository 接口。正式核算由 Application UseCase 编排并显式注入 Record Repository；纯 Domain Calculator 不持有 Repository。
- SQLite Repository 由 apps 组合根构造；UI 不创建持久化 Adapter 或隐式降级为内存保存。预览通过无 Repository 的 Preview UseCase。
- Canonical-first 不要求所有碳核算算法 JSON DSL 化；复杂标准公式、查表与插值允许保留在版本化 Domain Calculator 中。

### 3.7 参数因子资产与期间判断

- 来源文件、来源表、参数概念、参考数据资产与来源绑定各自保留明确责任。相同值可共用不可变数据资产并绑定多处独立来源定位；不同值使用单独资产版本，不设来源权重。
- Resolver 是计算候选与默认值的唯一入口；目录页面只读，不能成为计算真值源。
- 蒸汽焓按现行 Mapping §9.7 / GHG-STD-32151-34-017 的已批准软件决定：后续新自动焓采用 `iapws.IAPWS97`；C.4 / C.5 及旧查表/内插仅保留为历史证据，不允许旧表回退。生产接入仍待 PR46；合法独立已知焓路径保留，不因辅助自动求焓失败误阻断，不静默改选来源。本次只整理交接，不安装依赖、不改生产或历史 Record。
- Catalog 数据库仅增量新增注册表，不重写 Project 或历史 Record。
- 对完全早于、跨越及晚于实施日的三个期间分别作非阻断 Warning 分类；自身有效期内的参数仍按现有适用期间筛选。期间裁定不改正式公式、Resolver Selection Policy 或历史 Record。


## 4. 后续共享文件与最小接口

燃料B1与电力B由执行1担任唯一共享集成负责人。两执行分支只改各自专属模块/测试，共享文件的小补丁交集成负责人，不同时维护公共规则。

|所有者|文件或范围|最小接口与约束|
|---|---|---|
|共享集成负责人|core/parameter_resolution.py、application/carbon_accounting.py、carbon_material_input_policy.py、Canonical规则JSON与加载边界、Mapping/台账、状态文档|固定rule_set/revision和具体采用成员；只抽确有生产消费者的来源资格/默认/锁定求值，不把审阅render/compact/HTML搬入生产|
|共享集成负责人|ui/carbon_material_page.py、excel/appendix_b.py、Canonical codec/Project/report公共结构、模板注册/资源/打包|燃料与电力函数段用小补丁集成；版本兼容和历史Record独立，不让两个会话整文件覆盖|
|燃料B1执行|ui/carbon_material_fuel.py、燃料专属政策消费者与测试；共享文件仅提交燃料段补丁|GUI/Excel共用源资格结果及正式Canonical；精确身份/单位/路径和分来源草稿，避免新建/恢复混同|
|电力B执行|五表查询/绑定专属消费者与测试；共享文件仅提交电力/B.8段补丁|复用electricity_catalog_options及electricity_regions_by_level和现有UAT03FactorOption；值、参数、因子、地区、年度同步，Catalog绑定不能冒充Record已冻结字段|

建议优先保留现有内部签名：`parameter_source_policy(field_id, origin, has_resolver_binding, carbonate_component_count, input_basis) -> ParameterSourcePolicy`（合法来源、初始来源、锁定、精确绑定要求），`fuel_input_policy(origin, direct_carbon, heat_activity, carbon_source_kind) -> FuelInputPolicy`（必要参数/缺省资格/可编辑性）。B由共享负责人把它们变为Canonical执行表达的薄适配，而不是让燃料和电力分别重写来源集合。电力继续复用`electricity_catalog_options(level, region, period)`及`electricity_regions_by_level(period)`；所有正式入口仍消费同一Resolver/Canonical/Application。

现有Record已冻结parameter_id、factor_id、factor_year、source/location和采用值，模型没有独立binding_id字段。当前Catalog可对账绑定/来源表，但不能回查Catalog冒充历史Record已冻结binding；若B需要扩展来源快照，先明确最小版本化兼容方案，不在本基线整合扩模型。

Word继续只读冻结Record。实际公共提供者和业务来源策略由共享集成负责人一次接管；不并行新增两套允许运算来源或规则缓存。

### 4.1 当前最小接口断点

`core.business_field_policy.evaluate_field`执行原Canonical四属性及最终来源/锁定纠错；候选审阅调用同一实现。`standards.carbon_material_business_policy.evaluate_fuel_power_field(field_id, context)`仅支持燃料四字段与electricity.factor，返回default_source/default/source_qualification/locking/status/problems，与候选最终结果相同；它不验证调用者声称的绑定。缺上下文/多匹配/非法来源保持明确阻断，不自动切源。

`adopted_binding_conditions(field_id)`返回Canonical精确绑定条件的副本；`electricity_catalogue_parameters()`返回(table_number, parameter_id, geography_tag)元组，从同一来源资格表达推导，不另维护五表字典。

仅`resources/business_rules/fuel_power.json`受控部署，由`scripts/project_fuel_power_rules.py`从三包已采用修订机械投影、检查依赖和当前源哈希，构建及测试核再生，运行及发布审计核固定资源哈希。无审阅render/compact/HTML/Schema运行依赖，不放开整个data-source。

此断点尚未替换生产消费者。`ParameterResolver.reference_binding_for(resolution)`只关联同一次真实选定结果，返回ReferenceBindingResolution(status, bindings)，状态VERIFIED/ABSENT/AMBIGUOUS/PENDING；不取首尾，不重选因子。旧无配置构造明确PENDING且resolve旧行为保留。`reference_parameter_id(subject_id, parameter_type)`只查询精确登记概念，不由名称拼ID。组合层逐项核Factor/Asset/Table/Source/Parameter/标准元数据，未知/未验证与真实缺失分开。

`fuel_source_context(field_id, resolver=..., origin=..., subject_id=..., accounting_period=..., selected_factor_id=None)`产生真实燃料上下文；当前有明确选择时传selected_factor_id，只有初始化/显式回缺省才省略。`electricity_source_context(resolver, resolution, direction=..., attribute=...)`从实际选定结果投影电力上下文，方向/属性不被期望条件覆盖；调用者再把当前business_source加入context求值，不将default_source当写命令。Core不依赖Catalog实现或GUI字段。

GUI/Excel/Domain逐入口一起迁移，不因旧调用没新ID而静默取消合法缺省。历史Record不重解。

## 5. 验证与停止边界

原生规则审阅表验证为NOT_RUN/DEFERRED，至下一阶段首次正式使用审阅表前补验；CU Esc有效，本轮不启动电脑操作。实际Windows鼠标/中文输入/人工系统DPI及Owner企业样例仍为明确缺项，不以自动截图或旧证据替代。

本地正式路径完整回归705/705、0失败/错误/跳过，687.989秒；候选+新保护103项与25场景夹具通过。Windows CI对应最终提交单列原PR送验评论；本地与CI、merge-ref与exact-head分别记录。完成后交源会话验收并停止，执行代理不合并PR46或关闭PR45。
