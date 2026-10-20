# 业务规则消费者盘点

2026-10-20：B 总体收口只读盘点；生产基线 `348077cd972a27b6eeb80b77b712e7cb35375988`（PR53 已合并）。此表列本次核对范围及代码/既有测试证据，不替代 Mapping、Standard Completeness Matrix、Golden 或正式支持验收。源独立验收本包之前只称盘点完成候选，不宣布整个标准 SUPPORTED。

## 当前共同链

GUI `CarbonMaterialAccountingPage._input/_run_calculation` 与附录B `AppendixBWorkbookImporter.import_preview` 装配同一 `CarbonMaterialInput`。Excel 预览使用无 Record Repository 的 `CarbonAccountingPreviewUseCase`；`ExcelImportPage._save_preview_as_project/_calculate_selected_unit` 明确保存 Canonical 项目后调用同一 `CarbonAccountingUseCase`，成功才 `create_with_details` 新增不可变 Record。GUI form_state 与 Excel Canonical 项目各自恢复，不将 Canonical 项目静默转成空 GUI 表单。

`carbon_material_input_codec.py` 行业 payload6 读1—6，通用封套2，并核对内外版本一致。`projects.sqlite` 与 `records.sqlite` 分离。`build_saved_record_report` → 注册标准 ReportModel → `word_renderer.py` 只读同 Record 冻结输入/参数/Trace/Provenance/Reporting；不调当前 Calculator/Resolver 补算。结果页和 Word 共用该模型；新软件补充 Schema3.1.0，缺节点旧记录保留3.0.0。当前输入 v11/2.9.0，旧 v2—v10 原字节保留，未知未来模板版本拒绝。

## 逐项渠道对账

下列“已核”指当前代码入口和对应既有回归的只读核对；本轮没有重跑全部业务测试。既有最终执行见 PR53 / CI288（1036 项），来源身份与本轮 N 实测另列，不能据测试数代替条款覆盖。

| 业务组 | 唯一当前决定/求值入口 | GUI / Excel | Canonical / 项目恢复 | 正式核算 / Record / Word | 旧定义退出及保留边界；定位证据 |
| --- | --- | --- | --- | --- | --- |
| 燃料 | `evaluate_fuel_power_field` 的4字段；真实 `fuel_source_context` / Resolver 决定缺省资格和值 | GUI `carbon_material_fuel` / `_refresh_fuel_row`；B.2 `_parse_fuels`，都经薄来源适配 | 燃料身份、路径、显式来源及草稿恢复；旧未确认身份不借先前绑定重算 | `_fuel` 核来源/单位，快照采用值；B.2读冻结值 | 旧手写字段资格已由共享策略替代；历史来源可读≠当前允许选项；`test_b1_fuel_consumers/lifecycle` |
| 购入/输出电力 | 同一资源 `electricity.factor`、`electricity_source_context`、`ParameterResolver.resolve_electricity_details` | GUI统一能源行；B.8 `_parse_power`，五表及其他来源同资格 | 方向独立、其他来源草稿/目录身份保留 | 统一Calculator；购入非化石与输出扣减分开，B.8只取冻结行 | 五表与“其他来源”遵守010/014已批准软件选择，不称与原文依据无差异；`test_b_electricity_channels/queries/table5_policy` |
| 材料 | `evaluate_material_field` 两字段；`normalize_material_inputs` 按声明方法归一 | GUI `_material_inputs`；B.3—B.5 `appendix_b_processes` | 原检测基准/采用值及实例/行身份可恢复，显式升级留副本 | `MATERIAL_V2` 原行和收到基采用值冻结，报告不重归一 | 旧“仅实测”资格退出；合法旧 `MATERIAL_V1` 明确兼容，非V2失败回退；`test_b_material_chain/gui_excel/identity/draft_scope` |
| 煅烧/焙烧/石墨化工艺 | 版本化 Domain Calculator；K1—K3及既有式保留，非另建JSON公式引擎 | 多实例工艺行与B.3—B.5装配相同物料角色 | 多实例删除/重开身份稳定，旧scalar/共同含量仅明确旧组合 | V2煅烧CC/UCC/DU各角色碳量直接求和；每实例/来源汇总冻结 | V2不经过旧跨角色wfc_c平均；旧字段存在用于读取/允许的历史组合，不等于未接管；`test_b_material_chain/policy`、`test_accounting_projects_ui` |
| 脱硫 | `evaluate_fgd_field` 三字段；`resolve_fgd_field` 同次 context/factor/resolution | GUI `_fgd_source_policy`；B.7 `_parse_fgd`，整剂批次同分母 | 设施/批次/组分稳定身份，旧版本读取与显式升级分开 | 共享Calculator按批校验整剂用量/分数并冻结；B.7消费原记录 | 旧私有绑定筛选/Excel空值猜默认退出，13项绑定资格局部接管；未知绑定仍阻断；`test_b_fgd_chain/legacy_templates/acceptance_fixes` |
| 烟气焚烧 | 专属 `evaluate_fume_segments` / Issue020，非套用fuel.*字段策略 | GUI监测段与B.6 `_parse_fumes` → 同一FUME_V2 | 同源/计量边界内整小时段，旧细时间可读保存、非法新算拒绝 | 逐段式(9)、源/边界覆盖与缺口冻结；B.6不年化或再聚合 | 当前V2退出旧报告期时长放大路径；FUME_V1仅明确旧组合且不补造覆盖；未新增焦油参数策略。`test_b_fume_segments/chain` |
| 热力/蒸汽 | `evaluate_heat_factor/heat_source_context`；边界 `classify_heat_boundary`；已知焓与固定CoolProp8/IF97独立方法 | GUI购/出热行；B.9 `_parse_heat_v28`，同Canonical | 热源边界/燃料已计/因子模式与草稿保留，实测空不回退 | 真实同次Resolver资格和值；内部已计燃料不重复购热；原/工作/采用物性及因子冻结，Word单位从冻结值投影 | 新自动焓不调用旧C.4/C.5查表/内插或失败回退；旧表仅历史/查询、已知焓独立。`test_b_heat_runtime/if97/chain/report_units` |
| 外部CO₂ | `evaluate_external_co2_supplement`，Issue016软件补充 | GUI三项/B.1后独立软件补充页（非B.10）；声明仅提醒 | 禁用草稿、待补、0、正值及历史None分别恢复；PR52缺省指纹兼容 | 原ET不变，只由producer求和一次冻结；结果/Record/Word消费同节点 | 原声明即ERROR/确认清除声明退出；旧Record不补节点/0，合法外部量不能填平烟气缺口；`test_b_external_runtime/chain/excel/review/status_copy` |

## 接管范围及仍开放项

- 受控运行投影 `fuel_power.json`（5字段）、`material.json`（2）、`fgd.json`（3）、`heat.json`（1）合计11字段，各有采用身份/资源哈希/来源绑定。Resolver仍是参数候选和值唯一入口，JSON不构成第二套Catalog。烟气Issue020、外部016及工艺公式通过版本化Domain接管，不把11字段采用夸成全业务JSON DSL。
- 本次限定清单内未识别新增的活动渠道分叉或必须修业务Bug；这是只读结论，不是对全部条件组合无缺陷的证明。历史方法、旧模板结构/种子识别及旧来源身份是受控兼容，不做删旧分支式“收口”。原R6骨架身份和R11字段采用身份分别追踪，不能静默改标。
- `CORE_CHECK` / `GAPS` 的原B2观察保持历史身份；GAP-009仍非阻塞附件provenance debt。当前整体标准仍 `PARTIAL / NOT SUPPORTED`；正式Golden/支持Gate及Windows Release分别在RS04/RS05，未授权进入。
- 原生Office回导（按模板版本）、真实鼠标/中文IME/人工DPI、企业实样、干净目标机/原生正常退出及全产品第三方许可履约继续OPEN。CI离屏/缩放、历史模板v4的局部Office证据均不能代替当前v11的这些门禁。
- N只在同一冻结生产基线测代表性性能，协议/原始样本/限制见 `docs/performance/n-baseline/`，不做优化，不替代本盘点或上述业务/交付Gate。

## 历史观察（截至各旧工作包；不是当前待办）

以下原文保留PR45/46与各分段当时观察及来源。历史“候选、待接管、N不启动”仅属于其当时时点；当前生产及本包授权以上述2026-10-20盘点与当前HANDOFF为准。

> 2026-10-17当前入口：PR46已合并、PR45已关闭。原表与PR45/46只读取证是固定历史观察；当前生产接管范围以TASK_STATE/IMPLEMENTATION_REPORT为准，不再把后续消费者写入责任归已收口PR46。

> 本轮以PR48已合并R8为业务基线；以下运行消费者是既有main/PR46的固定观察，不代表候选已接生产。015已批准不再待决；014按Owner最新电力“其他来源”软件决定RESOLVED，原标准专业依据差异保留，不伪称等价。来源细则唯一见Mapping §9.1/9.8；五表软件选择另按台账010的固定批准与取代关系，旧候选PENDING描述由本轮R8政策取代。25组盘点只在实施报告定位，不另立总账。

# 业务规则消费者简表

本表按稳定业务概念索引当前消费者，不再逐项复制 453 个字段和内部包装类型。纯技术字段不再复制到长期政策或默认审阅；必要时才从代码自动盘点。现有业务策略继续由候选JSON表达，完整条件组合由测试核验；本表不替代标准 Mapping，也不代表候选已接入生产。本表旧消费者的固定观察基线为 main `204dded5`，不表示当前 main；现行业务依据为已合并 R8，PR47/A 仍为候选。

| 业务概念 | 已有 Mapping ID / 章节 | PR46 当前来源、默认与锁定判断位置 | 后续唯一策略与待退出位置 | 受影响入口 |
| --- | --- | --- | --- | --- |
| 排放源启停、边界与结果汇总 | §§4–7、§6.2、§7.1、§13.1；Mapping 已登记十个源ID，包括 `CAR-SRC-FUEL-001`、`CAR-SRC-FGD-001`、`CAR-SRC-PURCHASED-ELECTRICITY-001`、`CAR-SRC-EXPORTED-ELECTRICITY-001`；总覆盖规则 `CAR-RULE-TOTAL-COVERAGE-001`。UI 启停操作没有专属 Mapping ID。 | GUI：`CarbonMaterialAccountingPage._toggle_source_group/_source_states`；Excel：`AppendixBWorkbookImporter._parse_fuels/_parse_power/_parse_heat/_parse_processes/_parse_fumes/_parse_fgd`；Domain：`EmissionSourceState`、`CarbonMaterialInput.status_for`。 | A 的 `software_policy.json` 将 `toggle_emission_source` 与纯展示操作分开；启停引用既有稳定源身份，不维护每个内部`source_status`属性的政策镜像。B 由单一业务操作更新 Canonical 状态；UI只投影，Excel只适配。Domain 的正式状态/结果校验保留。 | 排放源卡片；GUI核算；附录B预览/导入；Canonical输入、核算、Record及Word报告。 |
| 燃料身份、计量路径、活动量及参数来源 | §§8–10、§§9.1–9.2、§12；`CAR-FLD-F01-FCV`、`CAR-FLD-F01-FCM`、`CAR-FML-FUEL-VOLUME-001`、`CAR-FML-FUEL-MASS-001`、`SM01-DECISION-002`、`SM01-DECISION-003`。现行R8 §9.1同时定义来源类别及逐字段资格/默认/锁定政策；燃料参数按该字段政策表及Issue016对齐，不能沿用旧映射缺少逐字段政策的描述。 | 共用 helper：`carbon_material_input_policy.parameter_source_policy/fuel_input_policy`。GUI：`_on_fuel_type_changed/_refresh_fuel_row/_apply_source_policy/_fuel_default_factors/_canonical_default_factor`；Excel：`AppendixBWorkbookImporter._parse_fuels/_parameter_with_source`；Domain：`CarbonMaterialCalculator._append_source_policy_problem/_fuel`；Catalog候选：`ParameterResolver.resolve`、`UAT03ParameterQueries.fuel_defaults`。 | A 候选 `fuel.direct_carbon`、`fuel.lhv`、`fuel.fch`、`fuel.oxidation` 的 `source_qualification/default_source/default/locking` 是目标政策。B让GUI、Excel和Domain消费同一策略；逐步退出UI默认/只读分支、Excel逐字段来源分支和Domain资格重复推导。Resolver仍负责精确Catalog匹配；Domain数值、单位与来源快照校验保留。 | 燃料GUI行；main及PR46版附录B；Calculator与燃料参数快照。 |
| 工艺物料、固定碳/挥发分及基准 | §§8.1、§12；`SM01-DECISION-006`、`CAR-RULE-MATERIAL-BASIS-001`、`TV-CAR-BASE-001`–`005`。另有 `CAR-FLD-P01-K1`、`CAR-FLD-P02-K2`、`CAR-FLD-P03-K3`、`CAR-VAL-K1-DEFAULT`、`CAR-VAL-K2-DEFAULT`、`CAR-VAL-K3-DEFAULT`、`TV-CAR-VAL-003`；逐字段来源资格/锁定没有对应Mapping ID，现行政策定位以已合并R8相关段落为准。 | 共用来源helper；GUI：`CarbonMaterialAccountingPage._material_inputs`及工艺行；Excel：`AppendixBWorkbookImporter._parse_processes`；Domain：`normalize_material_inputs`、`CarbonMaterialCalculator._append_source_policy_problem`。K1/K2/K3的一般0.35和提醒由Mapping指定，属于既有规则默认，不等同来源资格。 | A 候选 `material.fixed_carbon`、`material.volatile_matter` 统一来源和锁定；B退出GUI/Excel/Domain各自判定来源资格的分支。收到基换算、工艺公式与K1/K2/K3默认仍按Mapping/Domain规则执行。 | 煅烧、焙烧/炭化、石墨化GUI行；附录B.3–B.5；共享规范化与Calculator。 |
| 烟气焚烧（P04A） | §§6.2、8、9.1–9.2、12；`CAR-SRC-FUME-INCINERATION-001`、`CAR-FML-FUME-INCINERATION-001`、`CAR-FLD-P04A-Q`、`CAR-FLD-P04A-QVAR`、`CAR-FLD-P04A-HM`、`CAR-FLD-P04A-FCH`、`CAR-FLD-P04A-FOX`、`CAR-FLD-P04A-T`。逐参数来源资格/默认/锁定没有对应Mapping ID，现行政策定位以已合并R8相关段落为准。 | PR46 GUI走 `CarbonMaterialAccountingPage._build_material_controls` 的 `fume` 路径；Excel：`AppendixBWorkbookImporter._parse_fumes`；Domain：`FumeIncinerationInput`、`fume_incineration_emission`、`CarbonMaterialCalculator.calculate`。共用 `parameter_source_policy` 不接受P04A字段。 | 当前11个A目标参数政策没有P04A字段；不把 `fuel.*` 规则套给焦油参数。保留专属Mapping关联，不套fuel；逐字段计算方法未定义时不自行扩权，后续受影响实现归PR46。 | 烟气焚烧GUI行；附录B.6；Calculator及B.1/B.6报告投影。 |
| 脱硫碳酸盐 I、EF1、TR | §§9.1、9.3、§12；C.2已登记 `CAR-PAR-C2-CACO3`、`CAR-PAR-C2-MGCO3`、`CAR-PAR-C2-NA2CO3`、`CAR-PAR-C2-NAHCO3`、`CAR-PAR-C2-FECO3`、`CAR-PAR-C2-MNCO3`、`CAR-PAR-C2-BACO3`、`CAR-PAR-C2-LI2CO3`、`CAR-PAR-C2-K2CO3`、`CAR-PAR-C2-SRCO3`、`CAR-PAR-C2-CAMGCO3-2`；缺省向量 `TV-CAR-VAL-004/005`。单/多组分来源资格、默认与锁定没有对应Mapping ID，现行政策定位以已合并R8相关段落为准。 | 共用helper；GUI：`_fgd_source_policy/_fgd_default_ratio/_on_fgd_factor_mode_changed`；Excel：`AppendixBWorkbookImporter._parse_fgd/_parameter_with_source`；Domain：`CarbonMaterialCalculator._carbonate_default_binding/_append_source_policy_problem`与Resolver。 | A 候选 `fgd.ratio`、`fgd.factor`、`fgd.conversion` 按组分数量、精确C.2 binding和来源统一资格/默认/锁定。B退出三渠道的独立分支；保留Catalog身份与Domain精确值、单位、快照校验。 | 脱硫单/多组分GUI；附录B.7；C.2解析与核算。 |
| 购入/输出电力因子 | §§9.4、§12、§13；`CAR-PAR-C3-ELECTRICITY-LATEST`、`TV-CAR-FML-012`、`TV-CAR-VAL-008`；现行软件边界见R8 §9.8、§17.2及台账010/014：010批准五表选择并取代008仅全国/省级候选的软件限制，008其他地区/目录决定保留；014电力“其他来源”产品选择已批准并RESOLVED，原文专业依据差异保留。逐字段资格/默认/锁定见§9.1，不虚构专属Mapping ID。 | `UAT03ParameterQueries.electricity_options/electricity_catalog_options`、`ParameterResolver.resolve_electricity_details`；GUI：`_refresh_unified_energy_row/_electricity/_exported_electricity`；Excel：`AppendixBWorkbookImporter._parse_power`；Domain：`CarbonMaterialCalculator._resolve_parameter`。购电属性/证明与输出因子分开，`NONFOSSIL_ZERO`仅购入方向。 | A 候选 `electricity.factor` 统一来源资格、缺省与锁定；B让GUI和Excel消费同一资格结果，Resolver继续精确选目录因子，Domain继续核验方向、来源和快照。Issue014最新已批准软件决定见HANDOFF；本轮候选按R8对齐产品选择，生产接入仍待PR46。 | GUI购电/输出电力行；附录B.8；Resolver、Calculator与Record。 |
| 购入/输出热力、蒸汽与参数来源 | §§9.4–9.7、§10、§12；`CAR-PAR-C3-HEAT-011`、`CAR-PAR-C4-SATURATED-STEAM`、`SM01-DECISION-004`、`TV-CAR-FML-013`；C.4/C.5及SM01-DECISION-004是旧消费者的历史查表/压力键依据，保留追溯，不作为当前新自动焓或失败回退。现行自动焓按R8 §9.7及Issue017的IAPWS97替代边界，合法独立已知焓路径保留；生产接入仍待PR46。来源资格/缺省/只读见§9.1，C.5历史表见§9.6，不虚构专属Mapping ID。 | GUI：`_refresh_heat_factor_details/_heat/_refresh_unified_energy_row`；Excel：`AppendixBWorkbookImporter._parse_heat`；`ParameterResolver.resolve`；Domain：`CarbonMaterialCalculator._heat_factor/_steam_reference/_enthalpy`。 | A 候选 `heat.factor` 统一来源、缺省和锁定。B退出GUI/Excel对因子来源模式的重复分支；新自动焓按R8/017待PR46接入IAPWS97，旧C.4/C.5仅历史；已知焓独立，单位/状态校验留Domain。 | GUI购入/输出热力行；附录B.9；Resolver、Calculator与Record。 |
| 模板导入、正式核算与报告 | §13.1已登记B.1–B.9报告字段；如 `CAR-RPT-B1-FUEL`、`CAR-RPT-B8-ELECTRICITY`、`CAR-RPT-B9-HEAT`。字段来源细节见§§8、10、12。 | PR46 `AppendixBWorkbookImporter.import_preview`解析为共享Canonical输入/预览；正式核算经Application写入不可变Record，Word报告读取Record；模板版本词法仍由Excel Adapter处理。 | 来源策略由同一字段策略提供，不在模板或ReportModel再设业务规则。B保持Excel为适配器，Word只消费冻结Record；A不改模板、Report或生产接线。 | GUI保存/核算；main及PR46版输入模板/预览；Application、RecordRepository、WordRenderer。 |

## PR45 与 PR46 历史只读取证（不重复祖先核验）

- 历史取证时 `refs/pull/45/head` 为 `9cdbcaa6e7e88914036535a65f80b11d26d8839e`（open）；`refs/pull/46/head` 为 `77d36a155323bc82199cb516c4ac58a2e1c60309`（open）。两者都以 `main@204dded5d03853617f79a1f05693e89b619df9d1` 为merge-base；相对该基线分别ahead 12/34、behind 0。
- GitHub compare显示PR45改动50个路径、PR46改动279个路径，PR45的50/50个路径均出现在PR46改动集中。`docs/ui/HTML_V4_QT_MAPPING.md` 两边blob SHA同为 `61adb3676f50cc3ec9cfd01d915f6572aba05e07`；`packages/ui/design_tokens.py` 两边blob SHA同为 `f7d3f8a366d25e30a4dd2a9e02164ac46835ca6a`。
- 已核对的PR45成果在PR46保留：可见期间事件过滤器仍限本页控件，并由 `tests/test_uat02_usability.py::test_accounting_page_event_filter_follows_page_visibility` 覆盖；工艺默认行索引由PR46迁到 `packages/standards/carbon_material_process_inputs.py`，煅烧/焙烧/石墨化仍为4/6/8行，旧保存索引兼容注释保留；参数库仍有“按标准/文件查看”和“全库搜索”，`tests/test_g04_catalog.py`继续覆盖来源浏览/搜索。PR46正文也声明PR45视觉成果已整合。
- 结论仅限refs、改动路径、已比对代码和测试声明；本任务未重跑两条PR测试、未逐像素重验所有截图或人工系统DPI。路径相同不等于内容完全相同；blob与上述实际功能点是已核对证据。

详细技术条件仅供测试；内部属性不继续复制进JSON或默认审阅表，必要时由代码自动盘点。本表不维护逐个内部字段清单，不以字段数、条件行数或测试数代替Mapping覆盖结论。此任务没有切换、合并、修改或关闭PR45/PR46。

Report Schema的结构、类型、版本、必填性及渠道投影仍有必要；业务含义引用Mapping，布局仅排版。资源登记不替代独立文件/来源和实际发布产物验证。


## B-MATERIAL 当前消费者增量

材料来源资格唯一提供者为`carbon_material_business_policy.evaluate_material_field`，从R11机械投影的`material.json`采用，不改原`fuel_power.json`身份。`parameter_source_policy`是薄适配；`normalize_material_inputs`在正式入口同样调用该资格并核必要基准/数值/方法。GUI不再保留“仅实测”隐藏来源，v6 Excel只映射原始输入，Domain统一归一化；旧模板只读取其明确历史表结构。

`MATERIAL_V2`的煅烧输出直接消费`output_carbon_cc/ucc/du/total`，不经过跨角色wfc_c平均。旧wfc_c键仅`MATERIAL_V1`明确组合和原scalar共同含量入口保留兼容；未知组合不可正式执行，读取不补默认。旧项目的明确升级保留原输入副本/另存Canonical项目，取消不写回。Record冻结原行与收到基采用值，B.3—B.5/Word只读同Record Trace采用事实，不重算或回查目录。

烟气专属分段模块仅在独立F分支准备，不在本材料包生产采用。热力/外部CO₂及其余R11消费者留后续明确包，不因候选READY宣布已接管。


## B-FGD 当前消费者增量

FGD资格/默认/锁定由fgd.json三字段机械投影及evaluate_fgd_field唯一提供。resolve_fgd_field返回同次真实Resolver的context/factor/resolution；生产装配只核验对应13项真实来源绑定，保留其他unverified门禁。parameter_source_policy为薄适配，不再持有FGD手写资格；旧Calculator私有绑定筛选和旧Excel空值默认实现退出。

Domain按批整剂分母校验，FGD_V2尾字段表达设施/批次/组分；GUI和v8 B.7进入同一Canonical/Application。codec3兼容1/2，旧输入不补键，显式升级保留原输入；projects.sqlite与不可变records.sqlite继续分开。新Word读取冻结输入/参数/来源，不查询当前Catalog。原燃料/电力和材料采用身份原样保留，烟气等未接管。完成状态及真实测试以TASK_STATE/当前PR为准。

## B-FUME 当前消费者增量

Issue020由版本化Domain专属evaluate_fume_segments接管，正式Calculator局部调用同一实现；GUI、B.6、项目与Application全部传递同一Canonical监测段，不保留分段版的旧按报告期时长逐行计算入口。旧FUME_V1只按明确旧组合兼容且提示无覆盖证据，不作为分段失败回退。覆盖按真实源/计量边界分别判定，不跨实例补缺口。

本包不增加P04A焦油参数字段政策，不套fuel.*来源，不新增默认绑定。FCh沿用既有公共ParameterValue单位/数值/来源元数据门禁，同次采用值与参数快照传给专属算法；专属纯数值模块不是来源放行入口。原fuel_power/material/fgd机械运行资源及采用身份不变。本包采用对象是Issue020操作与版本化Calculator，不伪称新增11字段采用范围；新Trace分别冻结R11候选映射中Owner已批准020软件决定与方法身份，原R6 Frozen骨架元数据不重新赋义。

codec4兼容1/2/3，v9仅改B.6 XML；新Record冻结逐段输入/采用/结果/完整性/缺口，Word只读冻结表。原材料包/FGD包正文中的“烟气未接管”是各包当时范围，当前状态以本增量及TASK_STATE/IMPLEMENTATION_REPORT为准。


## B-EXTERNAL 当前消费者与B收口候选

当前唯一提供者为版本化Domain `evaluate_external_co2_supplement`（CAR-EXTERNAL-CO2-016.1），共享Calculator EXTERNAL.1在得到原ET后按同一声明Profile只求和一次。GUI三项输入、v11软件补充页、Canonical项目统一进入Application；其他行业/运输声明不再ERROR、确认提示不清空声明。无其他行业算法、无标准伪造行。

新Record冻结独立software_supplement；结果卡、记录详情及Word只读同节点。禁用非法草稿可恢复，纳入空白为PENDING，真实0与正值分别冻结；旧payload1—5缺失为None，新payload6显式保留。旧Record/Word无节点保持原样。监测缺口与外部待补独立；不承诺验证完整企业结果。

前述材料/脱硫/烟气各包的“后续未接管”是历史范围说明。当前燃料电力GHGTOOL_FUEL_POWER_R11_V1、材料GHGTOOL_MATERIAL_R11_V1、脱硫GHGTOOL_FGD_R11_V1、烟气Issue020、热力GHGTOOL_HEAT_R11_C3_V2及软件补充Issue016已在共享链接线；本轮仅清理与本包直接冲突的旧阻断分支，不做全仓抽查或顺手重构。B收口为送验候选，实际测试/制品/独立验收以当前TASK_STATE和IMPLEMENTATION_REPORT为准；后续N抽查与RS04/RS05不得在本包启动。
