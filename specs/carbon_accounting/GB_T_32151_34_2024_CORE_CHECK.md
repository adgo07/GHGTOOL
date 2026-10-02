# GB/T 32151.34—2024 Core Function Check

工作包：GHG-RS01-A，R1证据与审计收口；日期：2026-10-02。只核对已有核心链，不修改实现，不宣布正式 `SUPPORTED`。

## 1. 使用的专业依据

- 标准原文：`34.GB_T 32151.34-2024 温室气体排放核算与报告要求 第34部分：炭素材料生产企业.pdf`，43 页；本次执行环境位于 `D:/标准  规范/06_温室气体（碳排放）/组织层面/国家标准/`。SHA-256：`60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`。
- 已验证 Mapping：`GB T 32151.34—2024 炭素材料生产企业映射方案.md`，`SM01-2026-09-13-R6`、文件声明 `FROZEN`；本次执行环境位于 `D:/MD仓库/杂/碳排放计算软件/`。SHA-256：`01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`。选择当前文件，不合并 `历史版本/SM01-R4_2026-09-11/`。R6 修订仅纠正式（8）向量；旧签署日期仍为 R5 的 2026-09-11，不冒充 R6 新签署。
- 确认依据：Mapping §17.1、§19，外部 `IMPLEMENTATION_REPORT_SM01.md` 的 R5 PASS/FROZEN 及 `G06_R6_修正清单_给Sol_2026-09-13.md`；Git 中 G06 最终 PASS 历史（`5b8d35d:TASK_STATE.md`，验收对象 `c2ca02e5453e4b597cc73647f3ae6cba0d2b1842`）。独立确认记录的失效链接另列 GAP-009。
- 当前代码基线：`adgo07/GHGTOOL`，最新 `origin/main@c8f7a8ce2139e21b239ce54fac6cbbb9c25aae72`；该提交为 PR #21 合并。任务分支 `codex/ghg-rs01-a-core-check`。
- 实际读取核心条款第 1、3、4、5 章、C.1～C.5、D；逐式视觉核验 PDF 12～15 页，核验 C.1/C.2/C.4/C.5/D 对应表页。标准全文和 PDF 不入仓、不入程序包。

原文与批准执行决定分开：燃料含碳量单位、式（4）符号、C.4 两个压力键、收到基固定碳口径沿用既有批准 Mapping，不宣称官方勘误。没有重新作标准解释。

R1已将准确R6原样复制为 [仓库 Mapping](GB_T_32151_34_2024_MAPPING.md)，源文件与复制件SHA256均为上述 `01FB34…E36A080B`。冻结正文未改写，其中历史外部路径仅保留为原始证据。历史原始批准附件缺失仍登记009（provenance debt），不再阻止RS01-B；4项历史执行决定正式登记于根目录 `STANDARD_ISSUES_REGISTER.md`，均RESOLVED、非官方勘误。本轮新增未解决STANDARD_ISSUE Gap仍为0。

## 2. 核心核对

下表 `OK` 表示本项核对范围内已有能力；`GAP` 不表示整项完全缺失。Gap 编号完整定义见 [GAPS](GB_T_32151_34_2024_GAPS.md)。

| 核对项 | 标准 / Mapping 要求 | 当前软件 | 结论 |
|---|---|---|---|
| 适用范围 | 第1、3.3、4.1条；炭素企业核算与报告，其他行业及上下游运输转其他标准 | 唯一行业入口为本标准；其他行业/运输声明致命阻断，不套算；目录范围为必要摘要 | OK |
| 全厂 / 工序核算边界 | 第4.1条、附录A；正式企业生产系统边界；工序选择见 Mapping §5 | 单元标签区分全厂、生产工序、其他核算范围；状态、结果各自保存，不跨单元自动分摊或相加。其他范围是软件工作区分类，不是新增标准正式边界 | OK |
| 化石燃料燃烧 | 第4.2.1、5.2.1条；体积/质量/热量三路径，必要时式（4）（5）换热量 | 多行启用、中文输入及三路径存在；式（1）～（5）一致。只自动带天然气热量路径参数，其余 C.1 缺省值和热值换算未接入用户路径（005） | GAP |
| 原料煅烧 | 式（6）、（14）；固定碳及挥发分两项，多个过程分别求和 | 一组投入/产出可填写，收到基与换算证明门禁存在，式（6）正确；多过程入口缺失（004） | GAP |
| 焙烧 / 炭化 | 式（7）、（14）；含填充料、坯料及碳输出 | 必要字段、中文单位可填；碳输出按 tC，公式正确；多过程入口缺失（004） | GAP |
| 石墨化 | 式（8）、（14）；挥发分只含保温/电阻料，不含炉体烧损 | 必要字段可填，公式没有额外待石墨化品挥发分项；Domain 有炉体烧损阻断；多过程入口缺失（004） | GAP |
| 烟气焚烧 | 式（9）、（11）；烟气量、浓度、热值、含碳量、氧化率、天数 | 全部可启用和填写；24、10⁻⁹、44/12 及单位一致；仅一组治理过程（004） | GAP |
| 烟气脱硫 | 式（10）（11）、C.2；按实际碳酸盐取因子，含量/转化率缺省90%/100% | 单组可填；公式乘项正确；因子留空无种类确认便取0.44（002），多组分/装置无法在界面逐项填写（004） | GAP |
| 购入电力 | 式（12）、C.3、D；适用官方因子；非化石零因子须证明 | 多行、取得方式/属性/证明独立；解析器按已安装目录选择，缺证或缺零因子阻断。此结论验证取值机制，不宣称目录联网实时更新 | OK |
| 购入热力 | 式（13）、C.4/C.5；优先供热单位实测因子，缺测用0.11 | kg、焓值或温压查表/内插可用；界面只提供目录0.11，实测因子无录入路径（001）；多来源只有一行（004） | GAP |
| 输出电力 | 第5.2.6.3条、式（12）（15）、表B.8；多来源分行后从间接量扣除 | Domain tuple与Calculator逐行计算已有；UI只构造一行且不能逐行选择适用因子（011）。现有单行扣减正确 | GAP |
| 输出热力 | 第5.2.6.3条、式（13）（15）；从间接量扣除 | 计算及扣减正确；界面与购热共用因子，无法提供各自实测因子（001），仅一行（004） | GAP |
| 参数与默认值 | Mapping §8、9、15；缺省、实测、派生量、公式系数应区分 | K=0.35、含量90%、转化率100%均有警告及快照；热力/天然气现有值一致。真实正式参考表未完整由Canonical承载（006）；目录状态陈旧（007）；证据链接和条款定位有缺口（009、010） | GAP |
| Validation | Mapping §12、16.2；缺失、负数、百分比、口径、证明、重复、范围及参数门禁 | 常见输入门禁和不生成错误记录已有回归；明确非负参数缺少Domain门禁，可生成非法成功记录（003）；必要负例缺失（008） | GAP |
| 分项结果 | 第5.1、5.2.7条、B.1；主要分项、直接、间接、状态 | 十项源有分项，直接/间接/总量及提醒可见；烟气治理合计是内部汇总，不是第十一排放源 | OK |
| 总排放 | 式（14）～（16）；直接加间接，输出电热扣除；多过程不漏计 | 现有单组算法加减及燃料/电力逐行求和正确，无烟气汇总重复计入；全厂多过程不能直接完整表达（004） | GAP |

核对计数：**OK 4 / GAP 12 / NEEDS_CONFIRMATION 0 / N/A 0**。没有需要本轮新选取的标准解释；这不替代后续正式标准支持验收。

### 公式简核

| 核算项 | 标准 / Mapping | 当前实现 | 结论 |
|---|---|---|---|
| 燃料、热量换算 | 式（1）～（5），批准含碳单位与式（4）符号修正 | `carbon_material.py:625` 起 helper，正式Calculator调用前三路径；换热量helper未接UI | 公式一致，入口缺口005 |
| 煅烧 / 焙烧 / 石墨化 | 式（6）～（8）；44/12、44/16及各碳输出扣除 | `carbon_material.py:645`～`graphitization_emission`；R6石墨化向量1.439166… | 单组公式一致，多过程缺口004 |
| 烟气治理 | 式（9）～（11） | `fume_incineration_emission`、`fgd_emission`；烟气合计只纳入直接量一次 | 公式一致，参数002、覆盖004 |
| 电热及汇总 | 式（12）～（16） | `purchased_*`、`direct_emission`、`indirect_emission`、`total_emission` | 单组正负及汇总一致，热力来源001、多过程004、输出电力多行UI011 |

## Standard Completeness Matrix

下表按主要业务能力列25行，不与上方16项核心核对计数混同。`GAP-xxx`均指GAPS中同号；Mapping均指本仓冻结R6。模块短名：Calculator=`carbon_material.py`；UI=`carbon_material_page.py`；Rule=`parameter_resolution.py`；Canonical=`catalog.json`；Test=`test_g06_carbon_material`/`test_g06_page`，另用`test_g05_rules`验证参数规则。结果/Trace与Record已存在并不表示RS02正式闭环已验收。

| 标准条款/附录 | Mapping | Canonical/参数 | 用户输入 | Validation | Calculator | 结果/Trace | UI/Record | Test | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| 1、3.3 适用范围 | §3/5 | catalog标准范围 | 行业/运输声明 | Rule范围阻断 | Calculator范围检查 | 错误原因 | UI；错误不成Record | test_g05_rules | OK |
| 4.1、A 核算边界 | §5 | GAP-010定位 | 单元边界/声明 | 范围门禁 | 单元隔离 | 边界快照 | UI/Record | test_project_workspaces | OK（边界语义；定位010） |
| 5.2.1 式1～5 化石燃料 | §7/8/9/10 | GAP-005/006 | UI多燃料三路径 | GAP-003 | fuel_* | 分行/参数快照 | 热值入口GAP-005 | test_g06_carbon_material | GAP-003/005/006 |
| 5.2.2 式6 煅烧 | §7/8/9/10/12 | K；GAP-006 | 单过程GAP-004 | 收到基门禁 | calcination_emission | EC/Trace | 单组Record | test_g06_carbon_material | GAP-004/006 |
| 5.2.3 式7 焙烧/炭化 | §7/8/9/10/12 | K；GAP-006 | 单过程GAP-004 | 收到基门禁 | baking_emission | EB/Trace | 单组Record | test_g06_carbon_material | GAP-004/006 |
| 5.2.4 式8 石墨化 | §7/8/9/10/12 | K；GAP-006 | 单过程GAP-004 | 基准/烧损门禁 | graphitization_emission | EG/Trace | 单组Record | test_g06_carbon_material | GAP-004/006 |
| 5.2.5.1 式9 烟气焚烧 | §7/8/10 | 企业参数；GAP-003 | 单装置GAP-004 | 数量/单位 | fume_incineration_emission | EV/Trace | 单组Record | test_g06_carbon_material | GAP-003/004 |
| 5.2.5.2 式10 脱硫 | §8/9.3/10 | C.2 GAP-006 | UI单组GAP-004 | 种类门禁GAP-002 | fgd_emission | ED/Trace | 单组Record | GAP-008 | GAP-002/004/006/008 |
| 5.2.5.3 式11 烟气治理汇总 | §10/11 | N/A — 分项派生值 | N/A — 从焚烧/脱硫输入派生 | 多装置GAP-004 | gas_control汇总 | EL/Trace | RS02合计命名 | test_g06_carbon_material | GAP-004 |
| 5.2.6.1 式12 购入电力 | §8/9.4/10/13 | Rule/电力目录 | 多行/取得方式 | 非化石证明门禁 | purchased_electricity_emission | EGe/分行Trace | 多行UI/Record | test_g05_rules/test_g06_page | OK |
| 5.2.6.3、B.8 输出电力 | §8/10/13、TV-CAR-REPORT-003 | 逐行factor已有 | 单行GAP-011 | 逐行单位/来源 | exported tuple逐行 | ESe/逐行Trace | GAP-011 | 单行扣减；GAP-008 | GAP-011 |
| 5.2.6.2 式13 购入热力 | §8/9.4～9.6/10 | 实测优先GAP-001 | 单热源GAP-004 | 参数GAP-003 | purchased_heat_emission | EGd/Trace | GAP-001/004 | GAP-008 | GAP-001/003/004 |
| 5.2.6.3 输出热力 | §8/10/13 | 各源实测GAP-001 | 单热源GAP-004 | 参数GAP-003 | exported_heat逐行 | ESd/Trace | GAP-001/004 | test_g06_carbon_material；GAP-008 | GAP-001/003/004 |
| 5.2.7 式14 直接排放 | §11 | N/A — 分项派生值 | N/A — 从各直接源派生 | 多过程GAP-004 | direct_emission | ES/Trace | 分项/Record | test_g06_carbon_material | GAP-004 |
| 5.2.7 式15 间接排放 | §11 | N/A — 分项派生值 | N/A — 从购入/输出派生 | 因子/覆盖Gap | indirect_emission | EI/Trace | 分项/Record | test_g06_carbon_material | GAP-001/004/011 |
| 5.2.7 式16 总排放 | §11 | N/A — 分项派生值 | N/A — 从直接/间接派生 | 致命不成Record | total_emission | ET/Trace | UI/不可编辑Record | test_g06_carbon_material | GAP-001/002/003/004/011 |
| C.1 燃料缺省表 | §9.2 | GAP-005/006 | 燃料/路径 | Rule取值 | fuel_* | 参数快照 | GAP-005 | test_g06_carbon_material | GAP-005/006 |
| C.2 碳酸盐表 | §9.3 | GAP-006 | 种类/因子GAP-002 | GAP-002 | fgd_emission | 参数快照 | GAP-002/004 | GAP-008 | GAP-002/004/006 |
| C.3 电力/热力因子 | §9.4 | 电力目录；热力GAP-001 | 能源/适用因子 | Rule/实测优先 | 电热helper | 来源快照 | GAP-001 | test_g05_rules；GAP-008 | GAP-001 |
| C.4/C.5 蒸汽焓表 | §9.5/9.6、决定004 | 代码查表；GAP-006 | 温度/压力/焓 | 查表/内插边界 | steam_enthalpy | 焓/Trace；RS02 | UI/Record | test_g06_carbon_material | GAP-006 |
| D 电力因子规则 | §9/12 | 电力目录/Rule | 方式/属性/证明 | 非化石证据门禁 | 适用factor | 来源/参数快照 | UI/Record | test_g05_rules/test_g06_page | OK（机制；非实时更新） |
| 6 数据质量管理 | §12/15 | 参数来源快照 | 现有证据字段 | 基础门禁；RS02证据链 | N/A — 管理要求无独立公式 | RS02 | RS02 | RS02 | RS02 |
| 7、B 报告内容/表B.1～B.9 | §13、TV-CAR-REPORT | 已有参数快照 | 核算字段；001/004/011 | 已有基础门禁 | N/A — 报告本身无新公式 | RS02 | RS02必要审计呈现；非全套导出 | RS02 | RS02（输入Gap归RS01-B） |
| B 数据表的Excel适配 | §13/15 | 同一Canonical输入 | RS03 | RS03 | N/A — 复用同一Calculator | RS03 | RS03 | RS03 | RS03（产品适配非标准强制Excel） |
| 标准全链正式支持验证 | §16 | 版本化来源 | 企业案例Candidate | RS04 | 现有Calculator | RS04 | RS04 | RS04 Golden Candidate | RS04（产品验收门禁） |

Matrix计数：**25行；OK 4；GAP 17；N/A独立行0；later-stage 4（RS02 2、RS03 1、RS04 1）**。列内N/A均给理由；后续阶段未实施，Golden未冻结。表B.8/B.9的多来源业务输入属于RS01-B，不因报告呈现归RS02而推迟。

## 3. 总体判断

- 已完整的部分：十项源的基本可计算路径；单组核心公式；燃料及购电多行；非化石证明门禁；单元隔离；高精度与显示分离；成功记录新增、致命错误不成记录；用户可查看直接、间接、总量与分项。
- 存在 Gap 的部分：实测热力因子、未知碳酸盐fallback、Domain参数合法性、多过程/多热源及输出电力多来源覆盖、标准缺省取值入口、Canonical参考数据治理、状态与证据，以及对应测试。
- 需标准解释确认的部分：本轮没有新增未解决问题；4项历史决定已RESOLVED入台账。009仅剩历史附件provenance debt，不阻止RS01-B；未来改变这些解释须先加强证据或重新取得项目所有者确认。
- 留到 RS02：结果卡可达性、普通层I02/I03/I04与ET、烟气合计显示成“其他排放源”、trace展示及历史记录单元辨识；这些不改变现有算术值，不扩成RS01-A UI重构。
- 报告/导出、Excel、企业主数据、Golden Freeze、第二标准、Windows Release均未实施。**GHG-RS01-B NOT STARTED**。
