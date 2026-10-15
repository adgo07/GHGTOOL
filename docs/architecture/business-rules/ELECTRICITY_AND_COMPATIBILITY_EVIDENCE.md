# 电力路径与版本兼容性证据

A 包只读核验记录；不是运行时 Canonical 规则，也不表示代码已实施/验收。证据截止 2026-10-15。C01、C02 已批准。本文记录 Issue 008/010 的候选审查证据；当前 A 候选继承 main@204dded5 的 G05 规则等价，不依赖仅存在于 PR46 的 Issue 010。Issue 014 已登记 OPEN，仅影响尚未核验的企业因子输入路径。

核验对象 origin：https://github.com/adgo07/GHGTOOL.git；A worktree HEAD d279f505951b68750db133cf4279b2b76e0323bb；main 基线 204dded5d03853617f79a1f05693e89b619df9d1；PR46 依赖 head 77d36a155323bc82199cb516c4ac58a2e1c60309。Owner 批准方案 V1.2 SHA-256：98ABF84EA7F7AF3887D60C3C1E128C272D73CCBF73892D76581AD1771BFAD876。

|证据|原始文件、SHA-256、定位|官方来源|
|---|---|---|
|通则|01.GBT+32150-2025 工业企业温室气体排放核算和报告通则.pdf；673B85DF6EBEB6CE8894995534EC6EA3E2B7FA4F50B6A03AC0208E2DE34469BC；§7.4表4 PDF15/印刷9；§§7.5.6–7.5.7 PDF16/印刷10；附录B PDF19/印刷13|[国家标准状态页](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=6E4997D6B3118055931BC13C71B9A452)|
|行业|34.GB_T 32151.34-2024 温室气体排放核算与报告要求 第34部分：炭素材料生产企业.pdf；60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738；§5.2.6.1 PDF14–15/印刷6–7；§5.2.6.3 PDF15/印刷7；附录D PDF30/印刷22；表B.8 PDF25/印刷17|[国家标准状态页](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=E32D6CB8AF14D795CC640F8BBC85538D)|
|冻结 Mapping|specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md；01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B；SM01-R6 FROZEN|§3.1 将不注日期 GB/T 32150 引用解析为2025版；§8.4、§9.4 电力字段/关系|
|五表公告|生态环境部、国家统计局公告2025年第47号《 关于发布2023年电力二氧化碳排放因子的公告》|[公告正文](https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202512/t20251231_1139517.html)；[官方附件 PDF](https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202512/W020251231726284332528.pdf)|

## 标准事实和路径决定

|路径|事实与条件|
|---|---|
|通则一般因子|GB/T 32150-2025 §7.4表4将企业直接测量、能量平衡、物料平衡等取得的实测/测算因子列为高优先级，参考值优先级低，并要求说明来源。这一一般优先级不能单独证明行业 EF2 接受任意企业自测、测算或手工覆盖。|
|通则电力|§§7.5.6–7.5.7：购入/输出电量乘电力因子；优先供电单位实测，也可用生态环境部和国家统计局全国平均；非化石按附录B。供电单位测值与企业自行测值须分开。|
|行业购电|.34 §5.2.6.1：QGe 是电网电力实测消耗量，EGe=QGe×EF2；EF2 应采用生态环境部、国家统计局发布的最新全国平均数据；非化石转附录D。冻结 Mapping 将 QGe 标为实测消耗量，将 EF2 标为最新官方值或附录D；CAR-RULE-POWER-HEAT-001 SPECIALIZE 通则电力。实测的是电量，不是因子。|
|行业输出电|§5.2.6.3 输出余能按式(12)换算并从间接排放扣除；式(15)为购入电/动力减输出电/动力。每个输出行独立记来源，不能当作购入电正向相加。Issue010 将购入、输出都接通五表是软件决定，不是标准优先级。|
|非化石|附录D.1.1规定自发自用和市场化购入使用的非化石电力消费因子为零；D.1.2指向不包括市场交易非化石电量的全国平均；D.2列交易合同/结算凭证或GEC、自发自用月度原始记录。零因子独立于普通目录；同一电量与普通因子互斥。Issue007 批准软件不自动核验证明真伪、不因证明状态阻断 Resolver，但保留资料要求/证据状态，不得声称证明已核验；零因子缺失仍阻断且不回退表1。|
|待核企业因子|通则有供电单位实测条款；行业 EF2 专属文字指最新官方全国平均，未明列企业自行测算因子。Issue014 OPEN：供电单位实测是否被行业 EF2 排除、企业自行测算是否有专属依据。两者均 UNVERIFIED/PENDING；只阻断被选争议路径，不影响已核验目录或非化石零因子。|
|任意手填/历史标签|C02 已批准目录只读、企业输入逐路径有依据、禁止兜底。新输入不得以 USER_PROVIDED/MANUAL_OVERRIDE 任意覆盖；不得改名 MEASURED。历史标签与快照原样兼容读取。附录B表B.8脚注允许多来源分行；每行一个来源，不平均、不跨表混用、不静默回退、不叠加目录值与企业值。|

## 五表官方数值与上下文

公告2025年第47号于2025-12-31发布；官方单位 kgCO₂/kWh，换为 tCO₂/MWh 数值不变。数据年2023，不等于企业核算年度。PR46 77d36a1 的 SRC-ELEC-2023-47 标为 VERIFIED、登记40项。

|表|值|上下文/限制|
|---|---|---|
|1 全国平均|全国 0.5306|全国|
|2 区域平均|华北 0.6361；东北 0.5122；华东 0.5500；华中 0.5271；西北 0.5543；南方 0.4042；西南 0.2472|区域精确匹配；软件候选，不宣称标准强制区域优先|
|3 省级平均|北京 0.5554；天津 0.6796；河北 0.6516；山西 0.6634；内蒙古 0.6479；辽宁 0.4878；吉林 0.4671；黑龙江 0.5229；上海 0.5737；江苏 0.5827；浙江 0.4974；安徽 0.6553；福建 0.4211；江西 0.5836；山东 0.6191；河南 0.5897；湖北 0.4044；湖南 0.4976；广东 0.4419；广西 0.4476；海南 0.3648；重庆 0.5581；四川 0.1564；贵州 0.5683；云南 0.1333；陕西 0.6335；甘肃 0.4471；青海 0.1796；宁夏 0.6187；新疆 0.6021|省份精确匹配，无值不回退全国|
|4 不含市场化交易非化石电量的全国平均|全国 0.6096|与附录D.1.2对应，显式选择，不自动补位|
|5 全国化石能源电力|全国 0.8273|仅化石口径，显式选择，不自动补位|

Issue010 是软件候选决定，不是标准排序：表1/2/3 可为基础候选，表4/5 不自动补位；失效选择须重选。目录只读并冻结来源/年份/上下文；不平均、不跨表回退。表4与同一电量的零因子互斥，表5不能用于非化石电。

候选阻断原因（用于编码讨论，不代表现有运行时错误码）：ELECTRICITY_CATALOG_SELECTION_REQUIRED、ELECTRICITY_CATALOG_CONTEXT_MISMATCH、ELECTRICITY_CATALOG_FACTOR_UNRESOLVED、ELECTRICITY_FACTOR_PATH_PENDING_014、NONFOSSIL_ZERO_FACTOR_UNRESOLVED、ELECTRICITY_FACTOR_UNSUPPORTED_SOURCE。只阻断失败行/路径。

## Adapter 与项目/报告兼容

批准方案 §8.2：不信任未核实公式缓存；缺失缓存不是零；输入公式不支持时定位单元格并要求固定值；覆盖公式、缺失/陈旧缓存回导。PR46 77d36a1 Excel Adapter 以 data_only=False 读取，输入公式报 EXB01_FORMULA_REJECTED；忽略结果公式不构成输入。现有测试代码 test_result_formula_is_ignored_but_input_formula_blocks 覆盖前两种行为。初次静态盘点未运行测试；后续已补实际OOXML缓存回导证据，见文末，不把它等同原生Excel/WPS保存。

项目 codec：main 204 是 ghgtool.carbon_material_input v1；PR46 77 是 ghgtool.standard_input 外层 v2，明确 standard_id、standard_version、input_version；旧 codec 仅凭显式身份兼容到 .34@2024；未知身份/版本拒绝，不按值猜测。两版均有 projects_repository.py。按 AGENTS，项目写 projects.sqlite，成功 Record 追加至 records.sqlite 且不可编辑；form_state 是 Presentation State；.qzproj 不支持。

批准方案取消核算结果 Excel 导出，保留基于冻结 Record 的 Word。PR46 报告从所选 Record 快照生成，不调用 Calculator、不查实时目录。版本区别：
- main 204：REPORT_SCHEMA_VERSION=2.0.0（reporting/model.py）；附录B layout version=2.0.0（appendix_b_layout.json）。
- PR46 77：REPORT_SCHEMA_VERSION=3.0.0（reporting/types.py）；附录B layout version=3.0.1（appendix_b_layout.json）。
3.0.0 是 ReportModel 数据 schema，3.0.1 是附录B布局；两字段角色独立。Word renderer 分别使用 schema_version 与 layout/template 元数据。

独立期望用例见旁边 JSON。上述段落记录证据子任务的初次静态盘点；A包后续验证见下文。生产业务路径始终未修改。

## 复核补充：main 与 PR46 的电力 Resolver 资格（2026-10-15）

- **Issue 010 的版本边界更正：** `origin/main@204dded5d03853617f79a1f05693e89b619df9d1` 的 `STANDARD_ISSUES_REGISTER.md` 未包含 `GHG-STD-32151-34-010`；该条目及其 2026-10-14 PR46 电力五表决定见 `PR46@77d36a155323bc82199cb516c4ac58a2e1c60309:STANDARD_ISSUES_REGISTER.md`。因此此前任何将 Issue 010 描述为 main 已采用或 A 当前依赖的说法均由本补充更正；保留上述 PR46 审查史仅作来源记录。A 当前规则仍以 main 的 G05 等价为准。
- **main 的省级表3实测结果：** 从精确 `origin/main@204dded5` 导出只读临时副本，用 PR46 worktree 的 Python 3.12.14 执行 `python -m unittest tests.test_uat03_rules.UAT03RuleTests.test_region_selection_is_exact_and_unselected_region_keeps_national_route tests.test_uat03_rules.UAT03RuleTests.test_unbound_provincial_factors_are_not_candidates_for_any_region`，结果 `Ran 2 tests ... OK`。第一项通过 main 的 `create_g06_parameter_resolver` 与 UAT03 查询/解析路径，验证宁夏省级 2023 因子 `electricity_provincial_average_2023_29`、值 `0.6187`、来源 `SRC-ELEC-2023-47` 可按所选地区解析且 Resolver 未阻断；无匹配地区仍阻断，不回退全国。第二项验证缺少 VERIFIED 省级绑定时该路径无候选。main 代码实际为省级绑定构造 `.34` `FactorApplicability` 并将省级参数列为 required applicability；GEN 电力规则含省级参数，CAR 专属规则的参数列表不含省级参数。该结论是 main 上实际测试所得，不是从目录列表推断。
- **PR46 五表实测结果：** 在干净 PR46 worktree（`77d36a1`，Python 3.12.14）定向运行表1期间边界、五表目录、地区/口径选择与冻结 Resolver 快照、地区精确匹配共 4 个 `UAT03RuleTests`，结果 `Ran 4 tests ... OK`；测试后 `git status --short` 为空。PR46 G06 resolver 另为区域参数创建 `FactorApplicability`，并把区域和省级参数均列为 required applicability；该实现及 Issue 010 五表软件决定都不是 main@204 的已采用内容。
- **A 候选资格结论：** 省级表3的 2023 main Resolver 路径有上述实测资格证据；区域表2和全国表4/5的 A 候选正式适用资格标为 `PENDING`，原因是当前 A 依赖未包含 PR46/Issue 010 的相应选择规则与 Resolver 扩展。此待核验状态只针对适用资格，不改变其来源绑定的 `VERIFIED` 来源审查状态。不要将空 `applicable_standard_ids` 单独解释成 .34 的肯定授权，也不要将 PR46 通过结果反推为 main 已支持。

## A包补充：真实公式缓存回导

root在A工作树使用Python3.12运行 `python -m unittest tests.test_business_rules_excel_evidence -v`：2/2通过，4.683s。测试以临时母版副本构造合法业务输入，再直接改ZIP/OOXML公式节点与缺失或陈旧 `<v>` cache：B.2!B4输入公式两种缓存均定位拒绝 `EXB01_FORMULA_REJECTED`，无预览计算；B.2!J4结果公式两种缓存均忽略，正式输入逐项完整Decimal值与无公式版本一致。不读取缓存作为正式值，不对批准母版重存。此为程序构造OOXML证据，不是原生Excel/WPS保存测试；A不对PR46原生验证进行冒认。
