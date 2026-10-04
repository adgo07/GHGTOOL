# GB/T 32151.34—2024 Core Function Check

RS01核心核对及RS02-A记录证据收口；更新：2026-10-04。RS01-B2已并入main；本次补充新Record的Trace/Provenance/报告数据快照与周期资格证据，不重做完整结果页、不启动RS02-B、RS03、Golden Freeze或第二标准。

## 1. 专业依据与执行基线

- 标准原文：34.GB_T 32151.34-2024 温室气体排放核算与报告要求 第34部分：炭素材料生产企业.pdf；GB/T 32151.34—2024；43页；PDF保持仓库外。SHA-256：60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738。
- 冻结Mapping：本仓 specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md；SM01-2026-09-13-R6，FROZEN；原件SHA-256与入仓副本一致：01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B。未以R4/R5或重制文本替代。
- R6对式（8）、C.4/C.5压力键及材料基准的项目执行口径按冻结Mapping执行；历史决策见根目录STANDARD_ISSUES_REGISTER.md中4条RESOLVED登记，均是项目批准口径，不宣称标准发布机构官方勘误。
- B2分支从已含PR #23的origin/main 24537ba766579db17ef5012151b5cd788724afe9创建。platform-lock.json SHA-256为4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D；锁定中央SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20，未升级。
- Canonical目前98个参数、98个因子；GB/T 32151.34正式参数引用95项：C.1 26种燃料×3项、C.2 11项、K1/K2/K3 3项、脱硫缺省2项及既有非化石电力项。行业Catalog有10项业务排放源引用。标准PDF未入仓。
- C.4/C.5完整表、查表与插值保留在版本化Domain Calculator；Canonical来源元数据记录标准版本、PDF/印刷页定位、R6压力键修正与代表性验证锚点。原文异常1.40 MPa/195.04 ℃、1.40 MPa/204.3 ℃、1.50 MPa/207.1 ℃均保留；后两项按已批准的1.70/1.80 MPa口径执行，非官方勘误。
- 有明确量纲语义的ParameterValue在Domain集中门禁：非负量允许0且不得小于0；比例允许0至1；只执行标准明确范围，不增设经验上限。致命ERROR不生成成功Record。

## 2. 核心能力核对

| 能力 | B2结果与证据 | 当前判定 |
|---|---|---|
| 适用范围 | GB/T 32151.34入口；其他行业与运输转其他标准 | OK |
| 核算边界 | Rule定位为4.1条、PDF第10页、印刷页2；未改边界计算语义 | GAP-010 CLOSED |
| C.1燃料 | 26种具体燃料的LHV/单位热值含碳量/氧化率进入Canonical；单条质量、体积、热量路径可用；标准值和有来源的实测值分流 | GAP-003/005/006 CLOSED |
| 煅烧、焙烧/炭化、石墨化 | 每类可逐项添加/删除多个实例；每实例独立验证、计算、Trace与求和；K1/K2/K3=0.35快照 | GAP-004 CLOSED |
| 烟气焚烧 | 多装置逐项输入、逐项公式和逐行结果；参数统一走Domain门禁 | GAP-004 CLOSED |
| 烟气脱硫 | 多设施、多碳酸盐组分分别录入；每设施独立核验组分率并计算；C.2全表与0.90/1.00标准缺省保持 | GAP-002/004/006 CLOSED |
| 购入电力 | 目录解析、证明门禁及逐行计算保持 | OK |
| 输出电力 | 每一来源独立录入电量、适用/实测因子、来源证明及行ID；逐行结果后汇总抵扣 | GAP-011 CLOSED |
| 购入与输出热力 | 两种方向均可录入多个来源；每行实测因子优先，无实测值才用适用0.11默认；C.4/C.5输入与算法保留 | GAP-001/004 CLOSED |
| 目录状态 | 现有Catalog枚举IMPLEMENTED只表示本地Calculator可用；不表示中央标准SUPPORTED或阶段验收通过；10项排放源引用完整 | GAP-007 CLOSED |
| 历史Project / Record | 旧单条Project仍可打开；多过程/能源输入身份跨保存、删除、重开稳定；正式Record仍按历史快照只读、不重算 | GAP-008 CLOSED；记录快照回归通过 |
| 总量与结果 | 所有逐项源结果按标准路径汇总至直接、间接和总排放；致命错误不生成Record | GAP-001/004/008/011 CLOSED |

### 公式与参考数据策略

| 项目 | 标准依据 | B1结果 |
|---|---|---|
| 燃料 | 式（1）～（5）、C.1 | 质量/体积用适用低位发热量换热；热量路径直接使用单位热值含碳量；无泛称煤猜值 |
| 煅烧/焙烧/石墨化 | 式（6）～（8）、C.1及K1/K2/K3 | 每过程独立计算后求和；标准参数来源快照不变 |
| 烟气治理 | 式（9）～（11）、表C.2 | 多焚烧装置、多脱硫设施及设施内多组分分别计算后按标准汇总 |
| 电力与热力来源 | 表B.8/B.9、式（12）/（13）、C.3～C.5 | 购入/输出逐行因子、来源和结果；每行后汇总；热力双方向多来源支持 |
| 饱和/过热蒸汽 | C.4/C.5及R6批准修正 | 查表与插值仍为版本化Domain Calculator；来源、锚点和R6解释可追溯 |
| 参数校验与聚合 | Mapping §11/§12/§16.2 | ParameterValue统一语义门禁；逐实例ERROR可定位并阻断总Record；合法0保留 |

## Standard Completeness Matrix

模块短名：Mapping=冻结R6；Canonical=catalog.json；UI=carbon_material_page.py；Domain/Calculator=carbon_material.py；Rule=parameter_resolution.py；测试文件名省略tests/前缀。状态计数按每行主状态归类，closed gap仍保留在对应能力行作为完成证据。

| 标准条款/附录 | Mapping | Canonical/参数 | 用户输入 | Validation | Calculator | 结果/Trace | UI/Record | Test | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| 1、3.3适用范围 | §3/5 | 标准范围 | 行业/运输声明 | 范围阻断 | scope | 错误原因 | 致命错误无Record | test_g05_rules | OK |
| 4.1、A核算边界 | §5 | Rule source_location | 边界声明 | 范围门禁 | 单元隔离 | 边界快照 | UI/Record | test_g05_rules | OK；GAP-010 CLOSED |
| 5.2.1式1～5化石燃料 | §7～10 | C.1 26种×3参数 | 单条质量/体积/热量 | ParameterValue门禁 | fuel_* | 参数快照 | 当前多燃料行 | test_g06_carbon_material/test_g06_page | OK；GAP-003/005/006 CLOSED |
| 5.2.2式6煅烧 | §7～12 | K1=0.35 | 多煅烧实例 | 收到基/参数门禁/实例定位 | calcination_emission逐项 | EC逐项/Trace | 多实例Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_ui_builds_multiple_instances_for_every_process_source | OK；GAP-004 CLOSED |
| 5.2.3式7焙烧/炭化 | §7～12 | K2=0.35 | 多焙烧实例 | 收到基/参数门禁/实例定位 | baking_emission逐项 | EB逐项/Trace | 多实例Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_ui_builds_multiple_instances_for_every_process_source | OK；GAP-004 CLOSED |
| 5.2.4式8石墨化 | §7～12 | K3=0.35 | 多石墨化实例 | 基准/烧损/参数门禁 | graphitization_emission逐项 | EG逐项/Trace | 多实例Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_ui_builds_multiple_instances_for_every_process_source | OK；GAP-004 CLOSED |
| 5.2.5.1式9烟气焚烧 | §7～10 | 企业参数 | 多焚烧装置 | 数量/参数门禁/实例定位 | fume_incineration_emission逐项 | EV逐项/Trace | 多实例Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_ui_builds_multiple_instances_for_every_process_source | OK；GAP-004 CLOSED |
| 5.2.5.2式10脱硫 | §8～10 | C.2全表；90%/100% | 多设施/多碳酸盐组分 | 未确认即阻断；设施内合计校验 | fgd_emission逐组分/逐设施 | ED逐项/Trace | 多实例Record | test_fgd_ui_keeps_multiple_components_scoped_to_each_unit/test_ui_builds_multiple_instances_for_every_process_source | OK；GAP-002/004/006 CLOSED |
| 5.2.5.3式11烟气治理汇总 | §10/11 | N/A — 分项派生值 | N/A — 从焚烧/脱硫多实例派生 | 逐项错误阻断 | gas_control逐项汇总 | EL/Trace | Record；说明视图RS02 | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging | OK；GAP-004 CLOSED |
| 5.2.6.1式12购入电力 | §8～13 | 电力目录 | 电力明细 | 非化石证明门禁 | purchased_electricity_emission | EGe/逐行Trace | UI/Record | test_g05_rules/test_g06_page | OK |
| 5.2.6.3、B.8输出电力 | §8/10/13 | 每行适用/实测Factor | 多输出电力来源 | 各行因子/来源门禁 | exported tuple逐行 | ESe逐行/Trace及汇总 | 多来源UI/Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_heat_and_exported_power_rows_keep_factors_and_sources_independently | OK；GAP-011 CLOSED |
| 5.2.6.2式13购入热力 | §8～10 | 默认0.11；每来源实测 | 多购热来源/逐行因子 | 来源与因子门禁 | purchased_heat逐行 | EGd逐行/Trace及汇总 | 多来源UI/Record | test_heat_and_exported_power_rows_keep_factors_and_sources_independently | OK；GAP-001/004 CLOSED |
| 5.2.6.3输出热力 | §8/10/13 | 默认0.11；每来源实测 | 多售热来源/逐行因子 | 来源与因子门禁 | exported_heat逐行 | ESd逐行/Trace及汇总 | 多来源UI/Record | test_heat_and_exported_power_rows_keep_factors_and_sources_independently | OK；GAP-001/004 CLOSED |
| 5.2.7式14直接排放 | §11 | N/A — 各直接源派生 | N/A — 从各直接源逐项输入派生 | 任一实例错误阻断 | direct_emission汇总 | ES/逐项Trace | 分项/不可编辑Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_g07_records | OK；GAP-004 CLOSED |
| 5.2.7式15间接排放 | §11 | N/A — 购入/输出派生 | N/A — 从购入/输出多行能源派生 | 任一能源行错误阻断 | indirect_emission汇总 | EI/逐行Trace | 分项/不可编辑Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_heat_and_exported_power_rows_keep_factors_and_sources_independently | OK；GAP-001/004/011 CLOSED |
| 5.2.7式16总排放 | §11 | N/A — 直接+间接派生 | N/A — 从分项逐项输入派生 | 致命错误不成Record | total_emission逐项求和 | ET/Trace | UI/不可编辑Record | test_multi_entry_processes_calculate_each_instance_then_sum_without_merging/test_g07_records | OK；GAP-001/004/011 CLOSED |
| C.1燃料缺省表 | §9.2 | 26种LHV/含碳量/氧化率 | 具体燃料 | Rule取值/Parameter门禁 | fuel_* | 来源快照 | 单条输入可选 | test_g02_canonical/test_g06_page | OK；GAP-005/006 CLOSED |
| C.2碳酸盐表 | §9.3 | 11项因子 | 明确种类 | 未确认阻断 | fgd_emission | 来源快照 | 当前单组分 | test_g02_canonical/test_g06_page | OK；GAP-002/006 CLOSED |
| C.3电力/热力因子 | §9.4 | 电力目录/热力0.11及实测值 | 能源来源/适用因子 | Rule/Parameter门禁 | 电热helper逐行 | 来源快照 | 多来源UI/Record | test_heat_and_exported_power_rows_keep_factors_and_sources_independently/test_g05_rules | OK；GAP-001/004/011 CLOSED |
| C.4/C.5蒸汽焓 | §9.5/9.6；决策003 | 来源/页码/R6键/锚点 | 温度/压力/焓 | 表状态边界 | steam_enthalpy | 焓/Trace | UI/Record | test_g06_carbon_material | OK；GAP-006 CLOSED |
| D电力因子规则 | §9/12 | 电力目录/Rule | 方式/属性/证明 | 非化石证据门禁 | 适用Factor | 来源/快照 | UI/Record | test_g05_rules/test_g06_page | OK |
| 6数据质量管理 | §12/15 | 报告/证据快照 | 可复用活动/实测证据 | 证据与报告资格独立校验 | N/A — 管理要求无独立公式 | 质量说明/Trace | 新Record报告快照；说明呈现RS02-B | test_rs02_record_evidence | OK；RS02-B补普通用户解释 |
| 7、B报告内容/表B.1～B.9 | §13 | 报告/参数快照 | 可选主体与报告说明 | 年度资格独立校验 | N/A — 报告无新增计算式 | ES/EI/ET、逐项Trace与证据快照 | Record已持久化；完整结果页RS02-B | test_rs02_record_evidence/test_g07_records | RS02-B |
| 7.3年度报告期间与总量单位 | §13；CAR-VAL-ANNUAL-REPORT-PERIOD | 已存期间 | 年度资格快照 | 月度/自定义报告资格ERROR，不阻断核算 | N/A — 报告资格，无独立公式 | 年度ET/tCO2、资格状态 | Record资格快照 | test_rs02_record_evidence | OK；报告说明页RS02-B |
| B.8/B.9数据表Excel适配 | §13/15 | 同一Canonical输入 | RS03 | RS03 | N/A — 复用同一Calculator | RS03 | RS03 | RS03 | RS03 |
| 标准完整支持与正式验收 | §16 | 版本化来源 | 完整企业案例Candidate | RS04 | 现有Calculator | RS04 | RS04 Golden Candidate | RS04 | RS04 |

Matrix共26行：OK 23；GAP 0；N/A独立状态0；later-stage 3（RS02-B 1、RS03 1、RS04 1）。列内N/A均附原因。RS01-B1已关闭002/003/005/006/007/010；RS01-B2已关闭001/004/008/011；RS02-A补齐第6章及报告数据快照和年度资格。GAP-009保留为不阻塞实施的provenance debt。

## 3. RS02-A 记录证据与报告数据收口

- Coverage Audit 共27项：EXISTING 12、DERIVED 1、SOFTWARE_DATA 11、ENTERPRISE_OFFLINE 1、RS02-B 1、LATER_STAGE 1。11项 SOFTWARE_DATA 均已建立本地结构化落点；第6章制度/人员/设备治理不扩成企业管理系统。
- records.sqlite 通过只增列的 003_rs02_record_evidence.sql 保存新Record的 trace、provenance、reporting/evidence 与 qualification JSON；迁移没有回填或更新历史行。
- 新Record trace schema v1 固化逐项来源与稳定实例ID、输入变量、参数引用/快照、公式步骤、条款/Mapping定位、分项/小计及 ES/EI/ET。Provenance 固化标准、冻结Mapping、算法、规则集身份、参考数据身份及Numeric Profile来源。
- 活动数据与企业实测因子证据块可复用并通过引用固定到新Record；标准默认值不要求重复登记来源。可选报告主体及核算边界/产品工艺/排放源说明与Project既有表单状态一起保存。
- 月度/自定义周期继续成功计算并保存Record，独立保存 CAR-VAL-ANNUAL-REPORT-PERIOD 报告资格错误；年度周期不触发该资格错误。报告资格不进入Calculator致命错误集合。
- 旧Record不补算、不覆写、不查当前Catalog；缺失Trace明确显示“该记录生成时未保存完整计算过程快照。”。历史算术核对仅使用已保存的Trace与CalculationResult，不调用当前Calculator或Catalog。
- 仅建立报告/证据数据落点和只读记录快照；RS02-B完整结果解释页与B.1～B.9呈现仍未启动。本地本次验证及Windows exact-head CI见 IMPLEMENTATION_REPORT.md 与PR检查。

## 4. 总体判断

- RS01-B1与B2实现了标准核心输入、逐项计算、来源快照和聚合；B2的多过程/多能源输入及对应GAP-001/004/008/011回归证据已补齐。
- C.4/C.5完整表和查表/插值仍由版本化Domain Calculator执行；R6批准的压力键解释可追溯，原文异常仍保留，不称官方勘误。
- GAP-009仍记录历史批准附件provenance debt；冻结Mapping、G06 Git历史和正式验收记录证明当前执行口径，不阻止实施且不要求重新确认既有解释。
- 历史正式Record只读展示既有输入、参数与结果快照，不按当前Catalog或Calculator重算；B2项目兼容和历史快照回归通过。
- 年度报告资格与必要证据已在RS02-A形成持久化落点；完整结果解释页归RS02-B，Excel归RS03，Golden Freeze、正式SUPPORTED及Release Gate归RS04/RS05。本表不宣称标准已SUPPORTED。
