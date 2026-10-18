# B-FGD 实施报告

日期：2026-10-18。状态：生产实现收口，进入最终统一head验证与源独立验收；不自行合并。PR49材料已合并，基线main为1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e。最后生产提交为bc55cdcb8c2c2b09ffcf83d86dd64fa998cd95d3；最终head另含治理/测试补充，以当前PR与本地摘要冻结。本报告替换当前工作包报告，PR49原报告和失败历史仍可从Git及PR49收口恢复，不复制成第二路线。

## 平台 / Contract 预检查

实际origin已核实https://github.com/adgo07/GHGTOOL.git，fetch/default main确认后从最新origin/main建立独立codex/b-fgd-integration；根用户脏文件、旧材料及F工作树未改/未删除。业务仓起点1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e；locked central SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。

按locked SHA读取Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；UI v0.2按当前ACTIVE读取。适用MUST：分层/同一业务内核、declared-profile consistency、ambient independence、full-value exact、可追溯版本与历史不漂移。MUST NOT：未声明float、隐式修约/业务epsilon、显示回流、复制算法、自动升级Frozen、Qt form_state成为公共Workspace。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE；无中央冲突、无需修改中央Contract。Unit/Workspace等DRAFT不称Frozen。本包相关Standard Issue016；实施Mapping §9.1/9.3及批准V2第8节已有软件决定，不改变原公式、标准范围或解释。

## 最终实现

- 独立fgd.json机械投影fgd.ratio/factor/conversion，采用GHGTOOL_FGD_R11_V1，SHA 560c7151e797c47aeb0da698440ed773d1335d8498fbda35aac9e2781fa7bce7。原fuel_power.json/material.json及采用身份不改。
- 原Resolver只装配燃料/电力真实关联，13项脱硫登记均PENDING；本包精确补11C.2与通用I/TR真实关联，核实际parameter/factor/asset/table/source、单位/年度/适用期间；保留其他unverified与错资产门禁。resolve_fgd_field同次返回资格上下文、实际factor和resolution；旧FGD手写来源定义/Calculator筛选helper/Excel空值默认退出。
- I单批单有效组分且通用绑定适用才初始化90%；TR通用100%独立物种；EF精确C.2缺省锁定，否则批准实测。实测空白不回默认。可见空行不计业务组分，明确选来源但未完成的行不隐去；单多单保留原草稿，不把旧缺省90%重标实测。
- FGD_V2以facility_id/batch_id/component_id定位，不以显示名替代。按同批整剂分母校验I合计，批次独立，CAL只参与原逐组分公式一次，不归一份额，不跨批加I。新算法CAR-SM01-2026-10-18-FGD.1，原式及Decimal Profile不变。
- codec3实际支持1/2/3，旧输入缺身份保持FGD_V1，不回填。GUI显式升级保留原输入，取消无改动；Canonical升级另存project/unit及新身份，旧SQLite项目不回写。相同净耗量按显式单位归一比较，不以来源引用元数据判成不同量；旧实际用量不同/缺失不猜统一。projects.sqlite与不可变records.sqlite分开，无DB迁移。
- GUI按批次/组分/字段/来源隔离草稿；旧局部ID歧义完整保留各投影、不猜贴、可保存重开。企业设施编号只是业务显示与显式归属，内部键独立。Excel初次入站使用工作簿身份命名空间生成冻结不透明键，原分组定位仅供入站；保存后直接恢复键，不按名称/行号重算身份。
- v7 B.7无I/TR来源，无法表达已选实测空白；必要v8/2.6.0仅机械改sheet7 XML，增K/L来源和M企业设施编号。SHA a8ee7272ee4ac3665997f7ce93f78e8fd78c58cb4215ee477c01b76b6f87dff4。v2—v7原字节保留，Word布局3.0.3仅同步模板身份；材料旧词别名仍仅2.4，新2.5/2.6计算值与方法分离。
- GUI/B.7进入同一Canonical/Application，预览零Record；成功正式计算追加不可变Record，非法整体零Record。Word只读该Record冻结输入/参数/来源/Trace；新FGD显示实际实测/缺省来源与设施/批次，原始来源分类/定位保留审计，旧V1显示不重解释，不回查当前Catalog。
- 打包纳入fgd.json/v8并保留v7及旧模板；沿用VirtualKeyboard/iapws拒绝、路径/外链边界与实际包审计。没有引入烟气模块、热力/物性依赖、外部CO₂、商业发布或中央变更。

## 分工与阶段验证

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

ArtifactTool实际导入并渲染旧v7/newv8 B.7，新增栏可读、源模板其余部件一致；不是原生Office人工验收。最终同head联合组、GitHub Actions全量/exact-head构建与下载实包证据必须实际完成后分别登记于当前PR和本地摘要；旧PR49 CI256仅背书材料受验head，不当本包结果。

## 失败历史与修复

1. M首API夹具SQLite连接清理7ERROR，显式closing后15/15，再扩为最终30/30；不是先前已完整Domain运行失败。
2. C首联合22项4失败记录：尾零显示、旧空行计数断言、旧同名确认重置夹具；第二GUI7项3ERROR为夹具变量初始化顺序；其后48项1FAIL/1ERROR为新隔离格式仍被旧夹具按flat key修改。均已修复保留拒绝断言，65联合通过。
3. 新链3项1ERROR为WorkbookProvenance属性名；17项4FAIL含v8材料辅助路由遗漏、来源证据source标记及旧文字断言；28项1FAIL/14ERROR含退出私有helper后旧测试仍调用及ReportCell来源字段断言。已接真实API、补完整版本分派并让新Word明确显示冻结来源；44联合/9链通过。
4. 51项77.835s有1FAIL：随机入站ID使同一工作簿Canonical比较不同；改为工作簿身份命名空间内稳定键，针对性6/6通过。不用删除ambient比较掩盖问题。
5. 曾拟移除asset_id一致性校验的整条编辑被自动审批拒绝，未执行；采用安全替代保留原门禁，无未决权限阻断。批次/codec正式编辑与M/F协调此前各获Owner本人直接补充授权。

## 未执行与停止边界

本地完整整仓套件不冒称执行；最终GitHub Actions全量结果与本地联合明确区分。原生Excel/WPS v7/v8保存回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机与商业许可履约仍OPEN/NOT_RUN，按现有授权本包不CU。不合并、不删除旧分支/工作树、不接烟气/热力/N/外部CO₂、不宣布SUPPORTED或商业发行就绪。完成最终同head证据后交源独立验收并停止。
