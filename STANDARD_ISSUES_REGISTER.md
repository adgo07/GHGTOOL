# 标准问题与解释台账

状态：**ACTIVE REGISTER**

本台账用于记录标准原文事实、技术判断与软件实现决定。不得用本台账改写标准原文，也不得把内部判断或软件选择表述成发布机构正式解释。

## 1. 类型代码

| type code | 中文解释 |
|---|---|
| `TYPO` | 疑似笔误 |
| `AMBIGUITY` | 歧义 |
| `CONFLICT` | 条款、公式或表格冲突 |
| `MISSING` | 标准未规定 |
| `TERM` | 术语或现实对象对应不清 |
| `REFERENCE` | 引用标准、版本或外部依据问题 |
| `IMPLEMENTATION` | 软件实现解释问题 |

## 2. 状态代码

| status code | 中文解释 |
|---|---|
| `OPEN` | 待解决 |
| `PROVISIONAL` | 已有临时处理口径 |
| `RESOLVED` | 已有充分依据确认 |

`RESOLVED` 不自动等于发布机构官方确认；是否有官方解释必须在“确认程度”中单独说明。

## 3. 登记规则

- 问题编号采用 `GHG-STD-<标准号简写>-NNN`，一旦使用不得改号或复用。
- 每个问题必须分开记录“标准原文事实”“当前技术判断”“软件当前处理方式”。
- 无法准确复制标准原文时，不得凭记忆补写；应记录准确定位、事实摘要或“未复制原文”，并保留证据来源。
- 影响正式业务结果的问题必须可追踪：`Standard Issue → Software Decision → Rule / Calculator → Test / Golden Case`。
- 后续修改既有解释时，必须检查相关测试和历史结果兼容性。
- 当前只登记已有明确证据的问题，不重新审计全部标准，也不为填表制造问题。

## 4. 当前问题

当前登记数量：**6**；RESOLVED 6 / OPEN 0 / PROVISIONAL 0。前四项为既有项目决定；第五项记录标准实施日期与具体因子自身有效期的产品裁定；第六项记录按C.1、C.2、C.3及§5.2参数分组完成的来源核查。中央Numeric/Unit/Quantity议题不混入本台账。

共同证据：GB/T 32151.34—2024《温室气体排放核算与报告要求 第34部分：炭素材料生产企业》原始PDF，43页，文件名及SHA256见[CORE_CHECK §1](specs/carbon_accounting/GB_T_32151_34_2024_CORE_CHECK.md)；[冻结SM01-2026-09-13-R6 Mapping §17/17.1](specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md)。Mapping原样入仓SHA256=`01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`。G06最终PASS历史 `5b8d35db65375907ccef18d426fba9ec4319aa64:TASK_STATE.md`、验收对象 `c2ca02e5453e4b597cc73647f3ae6cba0d2b1842`佐证采用口径。独立原始批准附件缺失按GAP-009保留为provenance debt；本轮用户明确沿用这些历史决定。

日期口径：既有确认日期2026-09-11（Mapping记录，首次发现日期无独立原件可核）；本台账首次登记/最后更新2026-10-02。正式Golden尚未冻结，以下测试是软件执行口径回归，不是发布机构确认。

### GHG-STD-32151-34-001 — 含碳量单位与44/12

| 字段 | 记录 |
|---|---|
| 标准版本及定位 | GB/T 32151.34—2024；5.2.1式（1）（2），PDF12/印刷4 |
| 标准原文事实 | FCV/FCm打印单位为tCO2/活动量，而公式继续乘44/12；记录事实摘要，不覆盖原文 |
| 类型/问题 | CONFLICT；含碳量单位与后续碳→CO2系数量纲冲突 |
| 当前技术判断 | 执行含碳量采用tC/活动量后，乘44/12形成CO2量 |
| 软件当前决定 | 采用tC/活动量，保留44/12；Mapping SM01-DECISION-002 |
| 确认程度 | RESOLVED为项目冻结Mapping已批准；不是发布机构官方勘误，无官方回复记录 |
| 业务影响 | 影响体积/质量燃料路径；R1只登记，不改变现有结果或历史Record |
| 关联Calculator/测试 | carbon_material.py：fuel_volume_emission/fuel_mass_emission；test_g06_carbon_material.test_fuel_paths_and_energy_mapping_vectors；Golden N/A — RS04未冻结 |
| 支持证据/状态/日期 | 共同证据及Mapping §17.1；RESOLVED；日期见共同日期口径 |

### GHG-STD-32151-34-002 — 式（4）FFh/AFh

| 字段 | 记录 |
|---|---|
| 标准版本及定位 | GB/T 32151.34—2024；5.2.1式（4），PDF12/印刷4 |
| 标准原文事实 | 打印FFh = AFV × HV，相邻公式及变量定义使用AFh |
| 类型/问题 | TYPO；公式左端符号与邻接定义不一致 |
| 当前技术判断 | 该式对应体积换热量，应沿用相邻热量变量AFh |
| 软件当前决定 | 采用AFh；Mapping SM01-DECISION-003，未建立FFh业务字段 |
| 确认程度 | 项目冻结Mapping批准，非官方勘误，无官方回复记录 |
| 业务影响 | 体积转热量字段统一；R1不接通新入口、不改公式 |
| 关联Calculator/测试 | carbon_material.py：fuel_energy_from_volume；test_g06_carbon_material.test_fuel_paths_and_energy_mapping_vectors；Golden N/A — RS04未冻结 |
| 支持证据/状态/日期 | 共同证据及Mapping §17.1；RESOLVED；日期见共同日期口径 |

### GHG-STD-32151-34-003 — C.4压力键异常

| 字段 | 记录 |
|---|---|
| 标准版本及定位 | GB/T 32151.34—2024；C.4，PDF27～28/印刷19～20 |
| 标准原文事实 | 原始行含1.40MPa/195.04℃，又有1.40MPa/204.3℃、1.50MPa/207.1℃；原始事实保留 |
| 类型/问题 | CONFLICT；压力键重复及序列异常 |
| 当前技术判断 | 运行查表需要唯一压力键，不能静默删除重复行 |
| 软件当前决定 | 保留首行1.40；后两项采用已批准1.70/1.80MPa解释，温度/焓值不改；Mapping SM01-DECISION-004 |
| 确认程度 | 项目冻结执行口径，非官方勘误，无官方回复记录 |
| 业务影响 | 蒸汽查表/内插结果；现有解释不变，历史Record不重算 |
| 关联Calculator/测试 | carbon_material.py：saturated_steam_enthalpy；test_g06_carbon_material.test_electricity_heat_and_steam_mapping_vectors；Mapping TV-CAR-PAR-001；Golden N/A — RS04未冻结 |
| 支持证据/状态/日期 | 共同证据及Mapping §9.5/17.1；RESOLVED；日期见共同日期口径 |

### GHG-STD-32151-34-004 — 物料成分性质与基准

| 字段 | 记录 |
|---|---|
| 标准版本及定位 | GB/T 32151.34—2024；5.2.2～5.2.4式（6）～（8），PDF12～13/印刷4～5；B.3～B.5，PDF23～24/印刷15～16 |
| 标准原文事实 | 原文写碳含量/挥发分含量，未将软件执行所需收到基、固定碳及挥发分基准全部明确到可直接执行程度 |
| 类型/问题 | AMBIGUITY；物料质量与成分性质/基准需明确一致口径 |
| 当前技术判断 | 必须统一物料质量及成分基准，避免不同检测基准直接相乘 |
| 软件当前决定 | 收到基物料质量+收到基固定碳+收到基挥发分；其他基准先换算并留证；Mapping SM01-DECISION-006 |
| 确认程度 | 项目所有者批准的软件执行口径，不宣称国家标准官方解释 |
| 业务影响 | 煅烧/焙烧/石墨化输入门禁和结果；R1不改变既有口径 |
| 关联Rule/Calculator/测试 | CAR-RULE-MATERIAL-BASIS-001；carbon_material.py物料基准校验及三个过程helper；test_g06_carbon_material.test_material_basis_and_duplicate_output_validation；Mapping TV-CAR-BASE-001～005；Golden N/A — RS04未冻结 |
| 支持证据/状态/日期 | 共同证据及Mapping §8/12/17.1；RESOLVED；日期见共同日期口径 |

### GHG-STD-32151-34-005 — 标准实施日期与热力缺省因子有效期

| 字段 | 记录 |
|---|---|
| 标准版本及定位 | GB/T 32151.34—2024；封面实施日期，PDF1；附录C.3热力缺省值，PDF27/印刷19 |
| 标准原文事实 | 封面写实施日期2025-03-01；C.3给出热力缺省值0.11 tCO₂/GJ，未在该值处另行规定因子自身从2025-03-01起生效。原文事实不等于标准官方认可溯及适用。 |
| 类型/问题 | IMPLEMENTATION；软件将标准实施日期写入C.3因子及其绑定的`valid_from`，使用户选择该标准核算较早期间时解析不到该缺省值。 |
| 当前技术判断 | 标准实施日期与因子自身期间有效性是不同概念。`accounting_period`仍须参与真正具有期间适用性的因子解析，例如年度官方电力因子。 |
| 软件当前决定 | 按用户裁定区分来源文件实施日期与具体数据自身适用期：用户明确选择本标准时，核算期间完全早于、跨越或晚于实施日期均继续核算并产生非阻断提醒；SourceDocument保留实施日期，C.3因子及绑定不把该日期重复记作`valid_from`。不改正式公式、Resolver Selection Policy或既有历史Record。 |
| 确认程度 | 项目所有者批准的软件产品口径，不是发布机构对标准追溯适用性的官方解释。 |
| 业务影响 | 新计算的热力参数候选资格、核算状态及新Record告警；历史Record不重算、不迁移。 |
| 关联Rule/Calculator/测试 | Canonical `heat_default_gbt32151_34_c3`及对应binding；所选标准期间提醒；G06前/跨/后实施日三类回归。 |
| 支持证据/状态/日期 | 原始PDF SHA256=`60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`；用户2026-10-06明确裁定；RESOLVED；2026-10-06。 |

### GHG-STD-32151-34-006 — 标准实施日期与因子自身适用期分离

| 字段 | 记录 |
|---|---|
| 标准版本及定位 | GB/T 32151.34—2024；Canonical `data-source/carbon_accounting/catalog.json` 中C.1、C.2、C.3及§5.2相关参数分组；原始标准定位见各条`source_location` |
| 标准原文事实 | 直接核对原始PDF后，C.1燃料表项、C.2碳酸盐表项、C.3热力值及§5.2相关参数未规定各具体数值自2025-03-01起单独生效；该日期是标准实施日期。年度全国电力因子来自独立官方年度发布，具有自身发布/适用日期。 |
| 类型/问题 | IMPLEMENTATION；Canonical曾将来源标准的实施日期复制到具体因子及来源绑定的`valid_from`，与标准元数据实施日期重复，导致较早核算期间的候选资格被错误过滤。 |
| 当前技术判断 | SourceDocument实施日期与具体数据自身适用期是两个不同语义。只有来源对具体值另有独立时间适用要求时，Factor/Binding才应保留期间边界；`accounting_period`仍用于真正按期间适用的数据筛选。 |
| 软件当前决定 | 按用户裁定按来源分组核查并移除无独立适用期证据条目的重复日期：C.1 78条、C.2 11条、§5.2 6条，共95条Factor及对应95条`FACTOR_SOURCE` binding；C.3 `STANDARD_REFERENCE`绑定的重复标准实施日期也清除。保留SourceDocument `effective_from=2025-03-01`用于标准适用性提醒；保留官方年度电力因子的自身有效日期。早于、跨越、晚于实施日均继续核算并形成Warning。 |
| 确认程度 | RESOLVED为项目数据治理和产品口径；不宣称发布机构作出了标准追溯适用的官方解释。 |
| 业务影响 | 使所选标准实施日期不再错误地充当所有标准默认参数的因子级过滤门槛；真正按自身期间适用的数据仍由Resolver筛选。历史Record不迁移、不重算。 |
| 关联Rule/Calculator/测试 | Canonical C.1/C.2/§5.2分组计数与来源绑定一致性测试；实施日前/跨日/实施日后三类Warning与Record测试；年度官方电力因子前后期间筛选测试。 |
| 支持证据/状态/日期 | GB/T 32151.34—2024原始PDF SHA256=`60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`；标准实施日期2025-03-01保留；按原始表项分组检查；RESOLVED；2026-10-07。 |
