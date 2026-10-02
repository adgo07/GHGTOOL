# GB/T 32151.34—2024 Core Function Check

工作包：GHG-RS01-B1 — Calculation Safety & Reference Data Closure；日期：2026-10-02。仅处理单条业务输入的计算安全、标准参考数据和参数接通；不实施多过程/多来源输入、RS02、RS03、Golden Freeze或第二标准。

## 1. 专业依据与执行基线

- 标准原文：34.GB_T 32151.34-2024 温室气体排放核算与报告要求 第34部分：炭素材料生产企业.pdf；GB/T 32151.34—2024；43页；PDF保持仓库外。SHA-256：60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738。
- 冻结Mapping：本仓 specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md；SM01-2026-09-13-R6，FROZEN；原件SHA-256与入仓副本一致：01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B。未以R4/R5或重制文本替代。
- R6对式（8）、C.4/C.5压力键及材料基准的项目执行口径按冻结Mapping执行；历史决策见根目录STANDARD_ISSUES_REGISTER.md中4条RESOLVED登记，均是项目批准口径，不宣称标准发布机构官方勘误。
- B1分支从PR #22合并后的origin/main 1bad93c66bb98fb5a6d23c29b3d7b135258ebe9d创建。platform-lock.json SHA-256为4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D；锁定中央SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20，未升级。
- Canonical目前98个参数、98个因子；GB/T 32151.34正式参数引用95项：C.1 26种燃料×3项、C.2 11项、K1/K2/K3 3项、脱硫缺省2项及既有非化石电力项。行业Catalog有10项业务排放源引用。标准PDF未入仓。
- C.4/C.5完整表、查表与插值保留在版本化Domain Calculator；Canonical来源元数据记录标准版本、PDF/印刷页定位、R6压力键修正与代表性验证锚点。原文异常1.40 MPa/195.04 ℃、1.40 MPa/204.3 ℃、1.50 MPa/207.1 ℃均保留；后两项按已批准的1.70/1.80 MPa口径执行，非官方勘误。
- 有明确量纲语义的ParameterValue在Domain集中门禁：非负量允许0且不得小于0；比例允许0至1；只执行标准明确范围，不增设经验上限。致命ERROR不生成成功Record。

## 2. 核心能力核对

| 能力 | B1结果与证据 | 当前判定 |
|---|---|---|
| 适用范围 | GB/T 32151.34入口；其他行业与运输转其他标准 | OK |
| 核算边界 | Rule定位为4.1条、PDF第10页、印刷页2；未改边界计算语义 | GAP-010 CLOSED |
| C.1燃料 | 26种具体燃料的LHV/单位热值含碳量/氧化率进入Canonical；单条质量、体积、热量路径可用；标准值和有来源的实测值分流 | GAP-003/005/006 CLOSED |
| 煅烧、焙烧/炭化、石墨化 | K1/K2/K3=0.35由Canonical解析并快照；现有单组公式不变 | 多过程GAP-004 OPEN |
| 烟气焚烧 | 现有单条公式；参数统一走Domain门禁 | 多治理过程GAP-004 OPEN |
| 烟气脱硫 | C.2完整11项；明确种类取对应因子；90%含量及100%转化率为独立标准缺省；未知种类/因子ERROR且不成Record | GAP-002/006 CLOSED；多组分GAP-004 OPEN |
| 购入电力 | 目录解析、证明门禁及逐行计算保持 | OK |
| 输出电力 | Domain/Calculator逐行能力保持；当前UI仍单行 | GAP-011 OPEN |
| 购入与输出热力 | C.4/C.5算法及缺省来源可追溯；企业实测因子仍未单独录入 | GAP-001 OPEN；多热源GAP-004 OPEN |
| 目录状态 | 现有Catalog枚举IMPLEMENTED只表示本地Calculator可用；不表示中央标准SUPPORTED或阶段验收通过；10项排放源引用完整 | GAP-007 CLOSED |
| 历史Project / Record | 缺碳酸盐种类的旧Project可打开、原输入保留，重算时阻断；正式Record按历史快照只读不漂移 | 测试覆盖 |
| 总量与结果 | 单条能力仍按现有直接/间接/总量公式；不宣称完整企业多过程覆盖 | GAP-001/004/011 OPEN |

### 公式与参考数据策略

| 项目 | 标准依据 | B1结果 |
|---|---|---|
| 燃料 | 式（1）～（5）、C.1 | 质量/体积用适用低位发热量换热；热量路径直接使用单位热值含碳量；无泛称煤猜值 |
| 煅烧/焙烧/石墨化 | 式（6）～（8）、C.1及K1/K2/K3 | 标准参数经Canonical与Domain ParameterValue路径接通；多过程仍属B2 |
| 脱硫 | 式（10）、表C.2 | 完整碳酸盐因子、90%/100%正式缺省；未选种类不再fallback为0.44 |
| 饱和/过热蒸汽 | C.4/C.5及R6批准修正 | 查表与插值仍为版本化Domain Calculator；来源、锚点与R6解释可追溯 |
| 参数校验 | Mapping §12/§16.2 | ParameterValue统一语义门禁；负因子/负含碳量/比例越界阻断，合法0保留业务含义 |

## Standard Completeness Matrix

模块短名：Mapping=冻结R6；Canonical=catalog.json；UI=carbon_material_page.py；Domain/Calculator=carbon_material.py；Rule=parameter_resolution.py；测试文件名省略tests/前缀。状态计数按每行主状态归类，closed gap仍保留在对应能力行作为完成证据。

| 标准条款/附录 | Mapping | Canonical/参数 | 用户输入 | Validation | Calculator | 结果/Trace | UI/Record | Test | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| 1、3.3适用范围 | §3/5 | 标准范围 | 行业/运输声明 | 范围阻断 | scope | 错误原因 | 致命错误无Record | test_g05_rules | OK |
| 4.1、A核算边界 | §5 | Rule source_location | 边界声明 | 范围门禁 | 单元隔离 | 边界快照 | UI/Record | test_g05_rules | OK；GAP-010 CLOSED |
| 5.2.1式1～5化石燃料 | §7～10 | C.1 26种×3参数 | 单条质量/体积/热量 | ParameterValue门禁 | fuel_* | 参数快照 | 当前多燃料行 | test_g06_carbon_material/test_g06_page | OK；GAP-003/005/006 CLOSED |
| 5.2.2式6煅烧 | §7～12 | K1=0.35 | 单过程 | 收到基/参数门禁 | calcination_emission | EC/Trace | 当前单组 | test_g06_carbon_material | GAP-004 |
| 5.2.3式7焙烧/炭化 | §7～12 | K2=0.35 | 单过程 | 收到基/参数门禁 | baking_emission | EB/Trace | 当前单组 | test_g06_carbon_material | GAP-004 |
| 5.2.4式8石墨化 | §7～12 | K3=0.35 | 单过程 | 基准/烧损门禁 | graphitization_emission | EG/Trace | 当前单组 | test_g06_carbon_material | GAP-004 |
| 5.2.5.1式9烟气焚烧 | §7～10 | 企业参数 | 单装置 | 数量/参数门禁 | fume_incineration_emission | EV/Trace | 当前单组 | test_g06_carbon_material | GAP-004 |
| 5.2.5.2式10脱硫 | §8～10 | C.2全表；90%/100% | 种类/因子 | 未确认即阻断 | fgd_emission | ED/Trace | 当前单组 | test_g02_canonical/test_g06_page/test_g06_carbon_material | GAP-004；GAP-002/006 CLOSED |
| 5.2.5.3式11烟气治理汇总 | §10/11 | N/A — 分项派生值 | N/A — 从焚烧/脱硫派生 | 多装置GAP-004 | gas_control汇总 | EL/Trace | 结果呈现RS02 | test_g06_carbon_material | GAP-004 |
| 5.2.6.1式12购入电力 | §8～13 | 电力目录 | 电力明细 | 非化石证明门禁 | purchased_electricity_emission | EGe/逐行Trace | UI/Record | test_g05_rules/test_g06_page | OK |
| 5.2.6.3、B.8输出电力 | §8/10/13 | 每行Factor已有 | 当前单行 | 单行因子门禁 | exported tuple逐行 | ESe/逐行Trace | 多来源UI待补 | test_g06_carbon_material | GAP-011 |
| 5.2.6.2式13购入热力 | §8～10 | 默认0.11；实测入口待补 | 当前单热源 | ParameterValue门禁 | purchased_heat_emission | EGd/Trace | 实测因子待补 | test_g06_carbon_material | GAP-001/004 |
| 5.2.6.3输出热力 | §8/10/13 | 默认0.11；实测入口待补 | 当前单热源 | ParameterValue门禁 | exported_heat_emission | ESd/Trace | 实测因子待补 | test_g06_carbon_material | GAP-001/004 |
| 5.2.7式14直接排放 | §11 | N/A — 各直接源派生 | N/A — 从直接源输入派生 | 致命错误阻断 | direct_emission | ES/Trace | 分项/Record | test_g06_carbon_material | GAP-004 |
| 5.2.7式15间接排放 | §11 | N/A — 购入/输出派生 | N/A — 从电热输入派生 | 来源覆盖Gap | indirect_emission | EI/Trace | 分项/Record | test_g06_carbon_material | GAP-001/004/011 |
| 5.2.7式16总排放 | §11 | N/A — 直接+间接派生 | N/A — 从分项派生 | 致命错误不成Record | total_emission | ET/Trace | UI/不可编辑Record | test_g06_carbon_material/test_g07_records | GAP-001/004/011 |
| C.1燃料缺省表 | §9.2 | 26种LHV/含碳量/氧化率 | 具体燃料 | Rule取值/Parameter门禁 | fuel_* | 来源快照 | 单条输入可选 | test_g02_canonical/test_g06_page | OK；GAP-005/006 CLOSED |
| C.2碳酸盐表 | §9.3 | 11项因子 | 明确种类 | 未确认阻断 | fgd_emission | 来源快照 | 当前单组分 | test_g02_canonical/test_g06_page | OK；GAP-002/006 CLOSED |
| C.3电力/热力因子 | §9.4 | 电力目录/热力0.11 | 能源及适用因子 | Rule/Parameter门禁 | 电热helper | 来源快照 | 实测热力待补 | test_g05_rules | GAP-001 |
| C.4/C.5蒸汽焓 | §9.5/9.6；决策003 | 来源/页码/R6键/锚点 | 温度/压力/焓 | 表状态边界 | steam_enthalpy | 焓/Trace | UI/Record | test_g06_carbon_material | OK；GAP-006 CLOSED |
| D电力因子规则 | §9/12 | 电力目录/Rule | 方式/属性/证明 | 非化石证据门禁 | 适用Factor | 来源/快照 | UI/Record | test_g05_rules/test_g06_page | OK |
| 6数据质量管理 | §12/15 | 参数来源快照 | 现有证据字段 | 审计链完善RS02 | N/A — 管理要求无独立公式 | RS02 | RS02审计呈现 | GAP-008 | RS02 |
| 7、B报告内容/表B.1～B.9 | §13 | 已有参数快照 | 核算输入字段 | 基础门禁 | N/A — 报告无新增计算式 | RS02 | 非全套导出 | GAP-008 | RS02 |
| B.8/B.9数据表Excel适配 | §13/15 | 同一Canonical输入 | RS03 | RS03 | N/A — 复用同一Calculator | RS03 | RS03 | RS03 | RS03 |
| 标准完整支持与正式验收 | §16 | 版本化来源 | 完整企业案例Candidate | RS04 | 现有Calculator | RS04 | RS04 Golden Candidate | RS04 | RS04 |

Matrix共25行：GAP 13；OK 8；N/A独立状态0；later-stage 4（RS02 2、RS03 1、RS04 1）。列内N/A均附原因。B1已关闭002/003/005/006/007/010；仍开放001/004/011，以及GAP-008的B2测试覆盖和009非阻塞provenance debt。业务输入GAP-001/004/011不因报告呈现归RS02而推迟。

## 3. 总体判断

- 单条输入参数安全、C.1/C.2/C.4/C.5来源与默认值接通、未知碳酸盐阻断、目录本地计算能力状态和边界Rule定位均有实现与回归证据。
- 仍未完整表达同一核算单元内多过程、多热源和多输出电力来源。GAP-001/004/011继续开放到RS01-B2。
- GAP-008本轮B1安全、参考数据、目录、旧Project及记录快照验证已补；仅保留B2对应测试覆盖。GAP-009只剩历史附件provenance debt，不阻止B2。
- 历史Record只读展示其既有输入、参数与结果快照，不按当前Catalog或Calculator重算；已有回归验证变更Catalog参数后快照保持稳定。
- 报告/导出、Excel、完整结果解释、企业主数据、Golden Freeze、第二标准、正式SUPPORTED与Windows Release均未在B1实施。**RS01-B2 NOT STARTED**。
