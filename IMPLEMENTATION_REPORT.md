# B-FGD 实施报告

日期：2026-10-18。状态：源独立验收发现旧B.7兼容回归，本次已定向修复，送源复验；尚未取得最终验收结论。基线main为1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e。本次最后生产提交为c52a3be86090069b1507c1e727ce4cc97196046c；后续仅同步状态/报告，最终PR head及对应CI、实际包身份在PR50与本地摘要按head冻结。旧7b43c23及CI260为历史送验证据，不能替代本次修复验证。不合并、不进入其他包。

## 平台 / Contract 预检查

实际origin已核实https://github.com/adgo07/GHGTOOL.git，fetch/default main确认后从最新origin/main建立独立codex/b-fgd-integration；根用户脏文件、旧材料及F工作树未改/未删除。业务仓起点1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e；locked central SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。

按locked SHA读取Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；UI v0.2按当前ACTIVE读取。适用MUST：分层/同一业务内核、declared-profile consistency、ambient independence、full-value exact、可追溯版本与历史不漂移。MUST NOT：未声明float、隐式修约/业务epsilon、显示回流、复制算法、自动升级Frozen、Qt form_state成为公共Workspace。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE；无中央冲突、无需修改中央Contract。Unit/Workspace等DRAFT不称Frozen。本包相关Standard Issue016；实施Mapping §9.1/9.3及批准V2第8节已有软件决定，不改变原公式、标准范围或解释。

## 最终实现

- 独立fgd.json机械投影fgd.ratio/factor/conversion，采用GHGTOOL_FGD_R11_V1，SHA 560c7151e797c47aeb0da698440ed773d1335d8498fbda35aac9e2781fa7bce7。原fuel_power.json/material.json及采用身份不改。
- 原Resolver只装配燃料/电力真实关联，13项脱硫登记均PENDING；本包精确补11C.2与通用I/TR真实关联，核实际parameter/factor/asset/table/source、单位/年度/适用期间；保留其他unverified与错资产门禁。resolve_fgd_field同次返回资格上下文、实际factor和resolution；旧FGD手写来源定义/Calculator筛选helper退出；v8按显式来源处理空白，旧schema既有空白约定通过同一Resolver恢复并明确告警。
- I单批单有效组分且通用绑定适用才初始化90%；TR通用100%独立物种；EF精确C.2缺省锁定，否则批准实测。实测空白不回默认。可见空行不计业务组分，明确选来源但未完成的行不隐去；单多单保留原草稿，不把旧缺省90%重标实测。
- FGD_V2以facility_id/batch_id/component_id定位，不以显示名替代。按同批整剂分母校验I合计，批次独立，CAL只参与原逐组分公式一次，不归一份额，不跨批加I。新算法CAR-SM01-2026-10-18-FGD.1，原式及Decimal Profile不变。
- codec3实际支持1/2/3，旧输入缺身份保持FGD_V1，不回填。GUI显式升级保留原输入，取消无改动；Canonical升级另存project/unit及新身份，旧SQLite项目不回写。相同净耗量按显式单位归一比较，不以来源引用元数据判成不同量；旧实际用量不同/缺失不猜统一。projects.sqlite与不可变records.sqlite分开，无DB迁移。
- GUI按批次/组分/字段/来源隔离草稿；旧局部ID歧义完整保留各投影、不猜贴、可保存重开。企业设施编号只是业务显示与显式归属，内部键独立。Excel初次入站使用工作簿身份命名空间生成冻结不透明键，原分组定位仅供入站；保存后直接恢复键，不按名称/行号重算身份。
- v7 B.7无I/TR来源，无法表达已选实测空白；必要v8/2.6.0仅机械改sheet7 XML，增K/L来源和M企业设施编号。SHA a8ee7272ee4ac3665997f7ce93f78e8fd78c58cb4215ee477c01b76b6f87dff4。v2—v7原字节保留，Word布局3.0.3仅同步模板身份；材料旧词别名仍仅2.4，新2.5/2.6计算值与方法分离。
- GUI/B.7进入同一Canonical/Application，预览零Record；成功正式计算追加不可变Record，非法整体零Record。Word只读该Record冻结输入/参数/来源/Trace；新FGD显示实际实测/缺省来源与设施/批次，原始来源分类/定位保留审计，旧V1显示不重解释，不回查当前Catalog。
- 打包纳入fgd.json/v8并保留v7及旧模板；沿用VirtualKeyboard/iapws拒绝、路径/外链边界与实际包审计。没有引入烟气模块、热力/物性依赖、外部CO₂、商业发布或中央变更。

## 当前旧B.7模板兼容修复

预检查业务仓SHA为本次生产提交`c52a3be86090069b1507c1e727ce4cc97196046c`；中央锁/Contract、来源集合、公式、Numeric、模板字节和历史Record均未改变。本任务是既有兼容保护的本地实现缺陷修复，不是标准解释变更，无需修改中央Contract。未唤醒M/F，未扩大其他工作组。

源独立验收发现：新适配器对全部版本要求J来源，并将旧无I/TR来源列schema的空白统一当必填实测。实际main1ed基线源码与当前版分别导入真实v2—v7母版12个合法文件，main12/12可算、原实现7回归；另用受控v1历史结构fixture（不是原始母版）2场景补充，总14场景main14/14、原实现9回归。母版/fixture SHA及原始失败探针保留于`tmp/fgd-final-evidence/legacy-template-{main,current}-all/probe.json`。没有Owner授权收紧这些旧路径的依据。

修复仅在Adapter按版本表达来源：1.0/2.0无J列，精确C.2目录身份走既有缺省路径；2.1及以上仍要求原J来源。旧无I/TR来源列版的真正空白按既有约定选择缺省，经同次`resolve_fgd_field`和共享来源求值器验证，冻结真实factor并显式`EXB01_STANDARD_DEFAULT_APPLIED`告警。已填值仍为实测，0不换缺省；非法非空不补值；多组分I空白、错/缺真实绑定、v8显式实测空白/未选来源继续拒绝。未声明的旧自定义EF不被重标实测，不恢复库外计算来源。

新增`tests/test_b_fgd_legacy_templates.py`共10方法、104子场景（22合法/82拒绝）：

| 测试方法 | 覆盖 |
|---|---|
| test_old_real_masters_and_v1_fixture_keep_filled_ratios | 7版本填I/TR合法；真实v2—v7六例+v1 fixture一例 |
| test_old_real_masters_and_v1_fixture_keep_blank_qualified_defaults | 7版本真正空白适用缺省、真实来源与2条告警 |
| test_old_present_invalid_ratios_never_become_defaults | 7版本×I/TR×文本/空格/布尔，共42拒绝 |
| test_old_zero_is_measured_and_not_default | 7版本零值仍实测，结果0 |
| test_old_multi_component_blank_i_is_rejected | 7版本多组分空白I拒绝 |
| test_old_blank_requires_real_generic_binding | 7版本×缺/错实际I/TR绑定，共14拒绝；SQL断言确实改坏绑定 |
| test_current_explicit_measured_blank_still_rejects_and_zero_stays_measured | v8显式实测I/TR空白2例、未选来源2例拒绝，零值1例合法 |
| test_old_catalog_factor_mismatch_is_not_relabelled | 7版本C.2值不匹配拒绝 |
| test_existing_factor_source_selectors_remain_required | v3—v8六版已有J来源仍必选 |
| test_undeclared_legacy_custom_factor_does_not_become_measured | v1/v2未声明自定义EF来源2例拒绝，不猜实测 |

提交前受影响联合（与上述生产提交代码一致）91/91、87.795s，0FAIL/0ERROR；日志`tmp/fgd-final-evidence/legacy-template-affected.log`：

```text
python -B -m unittest tests.test_b_fgd_legacy_templates tests.test_exb01_ingress tests.test_main_integration_excel tests.test_pr46_parameter_source_policy tests.test_exb01_template_acceptance tests.test_g08_delivery tests.test_exb01_rpt02_integration tests.test_b_fgd_chain.FGDChainTests.test_excel_gui_parity_project_reopen_formal_record_and_frozen_word -v
```

未重复源已完成的未变M/GUI/Numeric组作为旧路径证明。新head针对性、CI及实际下载包结果只按实际完成后记录于PR50和本地摘要，不外推原873绿色。

失败证据：临时探针首次context位置参数错误，改关键字后得到真实对照；新增8方法首轮70ERROR为测试对空预览对象直接访问，修正夹具后2正例方法实际9FAIL（4.354s），证明回归。生产修复后8方法7通过/1ERROR（24.333s）为负例SQL误用不存在的binding.parameter_id，改为实际factor_id关联并断言rowcount后针对性1/1、4.406s；最终扩为10方法并纳入91项联合通过。原日志均保留，未放宽拒绝断言。

## 历史分工与阶段验证（原送验断点）

C单写公共消费者/模板/资源/构建/治理及整链；M只提交test_b_fgd_specialist.py，5ea3e9/4859d85单次引入为37807b1/73a7bc5；F烟气557f2c6只准备，最新main静态接口核对后停止，未进入本PR。

本地Python3.12.14、offscreen、隔离临时数据目录；完整命令和最终固定head结果由当前PR说明及本地tmp/fgd-final-evidence/summary.json冻结，不将阶段统计累加成最终测试量：

| 命令 | 实际结果 | 证据边界 |
|---|---|---|
| python -B -m unittest tests.test_b_fgd_specialist -v（M） | 30/30，3.858s | 11C.2独立预期、2.8174/11.88、错绑定/缺值/重复身份零Record、p50实际传播/ambient6/70、旧codec1/2不补键；作者本地 |
| python -B -m unittest tests.test_b_fgd_specialist tests.test_g06_fgd_ui tests.test_g06_carbon_material tests.test_g08_delivery -v | 65/65，61.022s | 当时接口/GUI/Domain/交付断点，不背书后续代码 |
| python -B -m unittest tests.test_b_fgd_chain tests.test_pr46_parameter_source_policy tests.test_b_fgd_specialist -v | 44/44，32.185s | 正式链与原政策保护断点 |
| python -B -m unittest tests.test_b_fgd_chain -v | 9/9，58.304s | 实际Qt/SQLite/表格/正式Record/冻结DOCX、升级与旧歧义/未完成行，tmp/fgd-legacy-final.log |
| python -B -m unittest tests.test_exb01_ingress.AppendixBIngressIntegrationTests.test_ambient_low_precision_does_not_change_canonical_input_or_result tests.test_exb01_template_acceptance -v | 6/6，1.767s | 修复入站身份确定性及新栏可编辑，tmp/fgd-ingress-identity.log |
| python -B -m scripts.project_fgd_rules；python -B -m scripts.project_appendix_b_v8 | PASS | 同源资源及v8机械原字节核验 |
| 既有审阅validator/builder/fixture/checks pipeline | 25/25场景、意见0→0、29/21/11行、652组合/450条件，hash核验PASS | 同版本四件套机械重生；不扩大审阅范围/不改变Canonical规则 |

补充阶段联合30模块352/352，361.249s（tmp/fgd-5af702d-joint.log，生产断点5af702d及当时治理工作区，不能背书随后bc55兼容补强）；源要求的真实重复导入/两独立SQLite项目隔离反例1/1，6.690s（test_b_fgd_chain.py:test_reimport_keeps_ingress_identity_but_saved_projects_have_independent_unit_ids）。同填表入站键可相同，保存后project_id/unit_id各自不同；来源importer_unit_id只作定位，两个项目重开成功且零Record。不改现有项目存储实现。

ArtifactTool实际导入并渲染旧v7/newv8 B.7，新增栏可读、源模板其余部件一致；不是原生Office人工验收。各head的本地联合、GitHub Actions及下载实包证据分别登记于PR50和本地摘要。7b43c23本地357/357、430.886s，CI260全量873/873、1370.590s与G08 17/17、6.741s以及实包核验均已完成，现仅作原送验历史；本次兼容修复以新head证据为准。旧PR49 CI256不当本包结果。

## 失败历史与修复

1. M首API夹具SQLite连接清理7ERROR，显式closing后15/15，再扩为最终30/30；不是先前已完整Domain运行失败。
2. C首联合22项4失败记录：尾零显示、旧空行计数断言、旧同名确认重置夹具；第二GUI7项3ERROR为夹具变量初始化顺序；其后48项1FAIL/1ERROR为新隔离格式仍被旧夹具按flat key修改。均已修复保留拒绝断言，65联合通过。
3. 新链3项1ERROR为WorkbookProvenance属性名；17项4FAIL含v8材料辅助路由遗漏、来源证据source标记及旧文字断言；28项1FAIL/14ERROR含退出私有helper后旧测试仍调用及ReportCell来源字段断言。已接真实API、补完整版本分派并让新Word明确显示冻结来源；44联合/9链通过。
4. 51项77.835s有1FAIL：随机入站ID使同一工作簿Canonical比较不同；改为工作簿身份命名空间内稳定键，针对性6/6通过。不用删除ambient比较掩盖问题。
5. 曾拟移除asset_id一致性校验的整条编辑被自动审批拒绝，未执行；采用安全替代保留原门禁，无未决权限阻断。批次/codec正式编辑与M/F协调此前各获Owner本人直接补充授权。

## 未执行与停止边界

本地完整整仓套件不冒称执行；最终GitHub Actions全量结果与本地联合明确区分。原生Excel/WPS v7/v8保存回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机与商业许可履约仍OPEN/NOT_RUN，按现有授权本包不CU。不合并、不删除旧分支/工作树、不接烟气/热力/N/外部CO₂、不宣布SUPPORTED或商业发行就绪。完成最终同head证据后交源独立验收并停止。


## V1正式入口校验补漏

7146115撤回最终候选身份：其同head本地30模块356/356、552.628s只保留原断点；CI258也仅背书该旧断点。补充实际探针发现旧FGD_V1同组CAL=10t/20t仍成功新增Record（4.8920），属于本包批准校验遗漏。依据Mapping §9.1/§9.3，同组组分共享整剂分母；旧FGDInput group同样是这一组，不能因缺新身份跳过。现将归一实际CAL的精确一致性校验移至V1/V2共同入口；不同旧group独立，不猜合并/拆批。读取codec1/2仍成功、不补身份；旧Record不重写，原排放公式与Numeric不变。这是落实已批准业务约束，不是新标准解释或公式变更。

C新增真实codec1/2→Application反例，首次1项2FAIL/1ERROR：两个不等量正式入口确实漏拒绝，ERROR为测试误用record.result属性；修后1项2ERROR为测试反馈字段误用rule_id，均修正夹具而不放宽断言。最终该项1/1、11.194s（tmp/fgd-v1-fixed.log）：不等量零Record，同量10t/10000kg且来源不同可算3.326；原合法V1仍可算；两个独立旧group各10t/20t算4.892；SQLite既存V1 Record和冻结Word在Calculator/Resolver禁用下照原读取、记录数不增加。此处为V1校验补漏历史，随后7b43c23联合与CI260已完成；本次旧B.7适配器修复另按新head验证。


6e417b4同head30模块实际357项、487.480s，356通过/1FAIL（tmp/fgd-final-6e417b4-joint.log）：既有G06多实例合法汇总夹具把同一fgd-a组的整剂CAL写成10t/2t，被新共同校验正确拒绝。该测试目的是实例独立计算后汇总，不是批准同组不同分母；现保留两组和混合组分，把fgd-a两组分统一10t，新增独立预期fgd-a=4.329、fgd-b=1.8675。V1不等量零Record反例不删除/不放宽。两项针对性2/2、7.347s（tmp/fgd-v1-fixture-fixed.log）。7b43c23当时仅测试/治理同步，生产断点为6e417b4；CI259实际873项1FAIL、1398.171s且构建SKIPPED，7b随后联合与CI260通过。该段为历史断点，当前最后生产提交见报告开头。
