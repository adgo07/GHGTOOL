# B-HEAT 实施报告（回归收口中）

更新：2026-10-18。当前结论：本地共享热力链已接入，相关回归继续；不是正式验收PASS。

## 平台 / Contract 预检查

业务base为PR51 merge `a1aeebc1b6809397e61a2ffa7a2333a3b440c756`；实际origin为adgo07/GHGTOOL，已fetch。中央锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，按该SHA采用Architecture V2.1、Numeric v1及Profiles v1；ACTIVE UI指南按中央正式main读取。MUST：分层、共享Application、声明Profile一致与ambient独立、full-value exact、输入/工作/显示值分开、Record/Word冻结。MUST NOT：业务epsilon、显示修约回流、隐式物性回退、Qt状态充当公共Workspace、自动升级Frozen。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE；C3资格漏项为LOCAL DEFECT，不需改中央Contract。相关Standard Issue005/006/015/017/019；没有新标准解释，017具体实现更换已获直接授权。

## 最终候选行为

- 当前算法`CAR-SM01-2026-10-18-HEAT.1`；codec5兼容读取1—4，无数据库迁移。旧项目保留未知边界，重新正式计算需明确事实；旧Record不回填、不重算。
- 015先判热源边界。内部且供热燃料已计入时不重复购热，不要求无关HM/因子，原燃料全值保持；未知/冲突阻断。输出热力按原公式独立扣一次。
- 独立已知焓只消费明确数值/单位，不依赖P/T、旧表或自动物性；有限非正值沿既有WARNING保留原值和采用值。GUI仅两项已知焓允许该输入，其余字段负值门禁不变。
- 自动焓固定CoolProp8.0.0/NumPy2.3.3、revision ae81610e7d23efc57f9d051c8e70a4d66e87537f，显式IF97Backend。方法CAR-HEAT-IF97-017.1、物性子Profile GHGTOOL_COOLPROP_IF97_PROPERTY_V1为binary64，非p40物性精度；原输入/规范值/实际工作Pa-K/Q/库Jkg词法/采用焓/真实phase/库身份冻结，失败不回旧表或HEOS。
- heat.factor只用同一次真实Resolver选择核资格、采用值和快照。R11基础加Canonical小增量准确补齐C3绑定，仍保留来源/期间条件，不能靠0.11相同冒认来源。实测空/非法不回默认，合法零保留。
- GUI有中文边界/燃料声明、已知/自动方式、草稿恢复和对应提示；Excel B.9 v10/2.8同链，预览零Record，明确保存Canonical项目后正式成功每次追加记录；Word只消费冻结证据，新自动B.9注明方法，不改旧Word正文。
- v10 SHA `705a9326f6910bceaad34ce955975a6150731fa8ed2b50ddfe8c2c5188deb729`，仅sheet9改变，旧v2-v9原字节不变；报告布局元数据3.0.5。热力独立资源SHA `2f472b6a4774076472e0fae19e552986d67f4ed3ca29f63cd496d31002f215de`，原材料/燃料/FGD/烟气资源不改。
- 构建固定物性运行身份探针、CoolProp delvewheel hook、14份原始通知/来源及哈希包审计。当前工程候选不等于商业许可履约完成；详见DELIVERY和docs/ci两份原始候选证据。

## 实际验证与失败对账

| 来源/命令 | 实际结果 |
|---|---|
| C本地 `python -B -m unittest tests.test_g06_carbon_material tests.test_uat01b_material_steam tests.test_b_heat_runtime tests.test_b_heat_if97 -v`（当时版本） | 59/59，6.596s；旧表工具历史用例保留，新正式自动路径改IF97 |
| C本地 `tests.test_g08_delivery tests.test_exb01_template_acceptance`及两个既有模板失败项 | 25/25，23.019s；修复旧v6/v8空B9误判，更新当前版本夹具 |
| C本地 `autoWord单项 + tests.test_qzc_n01_c_numeric_unit_pilot tests.test_exb01_ingress tests.test_main_integration_excel` | 66/66，76.226s；新自动Word方法说明、Numeric/Excel共享链 |
| C本地四个GUI失败项 + known非正值冻结新测试 | 5/5，22.471s；明确合法夹具边界、IF97来源/无表、绝压错误提示、WARNING/原值/采用值冻结 |
| C本地“所有字段拒负”旧断言修复单项 | 1/1通过；仅已知焓两项允许有限负值，其他字段拒负 |
| C本地Word停顿定位：独立用户数据目录单项 | 1/1，9.057s；广组合停顿原因未确认，不能据此声明组合通过 |
| 实际CI273旧EXE/PYZ生成两条热力Record/Word，当前reader禁Calculator/Resolver重放 | 模型SHA及Word document.xml字节相同，原DB不变；不是新CI或新包证明 |
| 受控模板机械生成/ZIP比较、ArtifactTool只读render | 仅B.9变化，前后中文标签/说明可读；不是原生Excel/WPS回导 |

不相加重叠测试数量。广Qt/项目/报告组合首轮出现5个旧热力/负值断言失败后，停在Word入口，人工终止无最终统计；保留`tmp/b-heat/heat-legacy-gui-report.log`。四热力失败独立重现4/4失败，修后见上；其他门禁保留。此前领域夹具日期/字段/全值、目录单位别名、旧B9种子识别及自动Word方法缺失均已修；新增WARNING测试初写severity错误产生两subtest ERROR，改真实level字段后通过。F低压PT初报成功已撤回，实际后端报超域，不设置绕行。

最终本地联合`tests.test_b_heat_if97 tests.test_b_heat_specialist tests.test_b_heat_runtime tests.test_b_heat_chain.HeatQtTests tests.test_b_heat_chain.HeatExcelTests tests.test_numeric_contract_v1_adoption tests.test_g08_delivery`：**85/85，65.099s，0失败/错误/跳过**。独立用户数据目录`tests.test_main_integration_ui tests.test_rpt01_report_excel tests.test_rpt02_appendix_b tests.test_p3_c_records_ui tests.test_rs03_excel_entrypoints`：**46/46，135.016s，0失败/错误/跳过**。Canonical校验9标准/12来源/102参数/138因子、热力投影、v10机械生成均通过；当前reader再次核实际CI273两条旧记录模型/XML不变。实际生产热力行按控制器刷新后离屏组件截图可读；不是原生鼠标/IME验收。新私有PR、全量Windows CI、精确head构建及实际新包尚未执行，不宣称本地全仓通过。

## 历史热力兼容证据

实际CI273旧包源码bbb1d5bd953d463013f135c1047de33fc37fcc59生成：known-with-old-reference模型29a564bbbdc221c5a34c223c39e8001352d853f3f60d2a1d8fa65c675d7ddc2c / XML e93c2ef859cc44a547a16b9a3e02a756426e1d09089126f13caf194bbb5955fe；old-auto-table模型0578d13aead197d0b8f14f6c9a344be3946236e76fd4729b40a4d6d6802d6bb1 / XML51735e78cf9571f0d074010ba26e4be6ee504b96ab0a1ab230de097e980d4df5。均为程序化构造样例，不冒称企业真实样例；不把新Calculator重跑当旧Record证明。

## 停止边界

C独占共享消费者、资源、GUI、构建和治理；F仅交热力helper/tests，M外部CO₂准备分支不纳入本包，N不启动。原用户脏树、旧工作树和计算表不改。源会话原始用户消息01a14ee7-32ba-7283-ab49-ad6b89b633aa“全部同意”及紧前解释已实际读取，原版本/C3/017授权待决已解除；本会话补充的源交接、PR49、M/F及脱硫授权已收悉，PR49/50/51均已合并，不回到旧阶段或改旧PR。

下一步：相关回归及失败对账→稳定提交→新私有热力PR并attach→merge-ref全量CI和精确head实包→源独立验收后停止。不得自行合并/启动下一包。原生Office、鼠标/中文IME/人工DPI、企业样例、干净目标机和商业许可履约保持OPEN；不CU、不商业发布、不宣布SUPPORTED，不改Frozen基线或另建路线。
