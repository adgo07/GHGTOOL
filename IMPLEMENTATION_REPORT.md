# B-FUME 实施报告

日期：2026-10-18。状态：生产接管与本地定向验证已实施，最终CI、精确head实包与源独立验收待完成。本包不自行合并或扩下一包。

## 问题与最终行为

按Issue020已批准的软件决定将P04A从无区间逐行输入接到真实源/计量边界的监测分段完整链。逐段配对Q/QVar/时长/参数，复用原式(9)与声明Decimal Profile后求和，不分别平均相乘，不重复小时/天系数。覆盖完整才能表达该实例/边界完整期间；合法缺口保存已覆盖合计与WARNING并明确总量不代表完整期间；同源同边界重叠、倒置、坏段、INVOLVED无段整体致命拒绝，不过滤坏段后成功。跨真实实例/边界同期独立，报告期与段时间不回填。

Canonical尾字段fume_segments与FUME_V1/V2；codec4兼容1/2/3，无数据库迁移。GUI维护稳定源/边界/段身份及显示名，支持新增段、共享源/边界、删除前段、新窗口/新服务SQLite恢复。旧GUI显式升级保留原输入副本，取消不写回；旧Canonical升级另存项目/单元副本、保留无区间原值，不伪造段，缺区间仍正式拒绝，需要当前模板补齐后预览另存。读取、保存和正式计算资格分开。旧组合兼容核算明确无覆盖证据，历史Record永不重算。

模板v9/2.7.0 SHA256 0adf62e4c0d60685b68de78111ed4cd6b5241b96d4f08035230d8506501460fb，仅机械改v8 B.6 XML。旧v2～v8原字节保留。H/I/J企业编号映射稳定namespace身份，K/L真实文字区间，M d/h。非法行不暴露过滤后可正式提交的部分Canonical；原燃料/材料/FGD来源栏继承同一版本规则。预览不写Record，项目保存后共享Application每次成功新增不可变Record。

新Record冻结输入、同次FCh采用快照、逐段结果、独立窗口、完整性/缺口、方法与算法版本。布局3.0.4沿用七列表，逐源/边界表、行区间说明、段时长、冻结小计和缺口；Record/Word不重算、不回查实时目录。旧历史表头/模型/正文不改。FUME_V1新核算的无区间限制与旧历史冻结对象区分，不给旧Record补判断。

## 平台 / Contract 预检查

业务base/main 8d054d2480d744882f4f11f56b59e68df91dc50f（PR50已合并），实际origin/fetch/分支/干净独立工作树已核。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；中央origin已实际验证，按locked读取Architecture2.1/Numericv1/Profilesv1，ACTIVE UIv0.2按已合并入口读。MUST：分层/共享内核、声明Profile传播、ambient independence、full-value exact、历史不漂移。MUST NOT：隐式float、业务epsilon、display回流、44/12当普通单位转换、复制算法、Qt状态成为公共Workspace、自动Frozen升级。Carbon默认p40/HALF_UP属ALLOWED PROJECT DIFFERENCE，不是平台默认；显式测试Profile配置传播且快照身份与实际精度/rounding一致。无中央冲突/缺口，不改中央Contract/锁。

相关Standard Issue：是，020；Mapping§7.2/§8/§12、TV017/018。不改变既有标准解释或原式(9)。新Trace明确采用R11-CANDIDATE中的Owner批准020软件决定，不把候选Mapping升Frozen；原R6骨架身份保持原义。不扩P04A焦油参数来源政策/默认绑定、不套燃料来源；FCh复用原公共ParameterValue门禁。三个字段运行资源和燃料/材料/FGD采用身份均原样保留。

## 实施与文件分工

C独占共享实现、资源/版本、模板登记、冻结输出、构建、治理与整链。F专属ca8aa1fda54504eb09b208e79055c6795368cfa4基于最新main，两文件单次restore取用，未cherry-pick旧链/造影子接口；F报告本地33+8通过只作专属准备。C重新执行41项纯Domain/映射/Numeric，41/41、0.043s。本包算法CAR-SM01-2026-10-18-FUME.1，专属方法CAR-FUME-SEGMENTS-020.1；所有共享消费者复用该专属实现。

## 本地验证与原始失败

Python3.12.14，offscreen，独立tmp/app-data/SQLite；没有原生CU。命令均从本工作树执行，未借CI冒称本地全量。

| 命令/日志 | 实际结果与边界 |
|---|---|
| python -B -m unittest tests.test_b_fume_segments tests.test_pr48_mapping_arithmetic tests.test_numeric_contract_v1_adoption -q | 41/41，0.043s |
| python -B -m unittest tests.test_b_fume_chain -v；third-chain.log | 当时9/9，35.630s；后扩展至15项，后续结果按最终日志 |
| affected-first.log：烟气/FGD退修/链/材料GUI/来源/模板/G08联合 | 97项，96通过、1失败，224.466s；旧布局版本断言3.0.3未同步3.0.4，已修正。执行中有后续局部补齐，不外推为最终代码全绿 |
| python -B -m unittest tests.test_b_fume_chain tests.test_exb01_ingress tests.test_main_integration_excel tests.test_g08_delivery -v；affected-second.log | 76/76，121.482s；包含当时14项烟气整链、全源B.6与G08 |
| final-targeted.log：烟气15项、原多实例GUI、Numeric pilot、FGD专属、材料、codec | 82项，81通过、1失败，70.891s；旧单实例结果ID断言未升级为源/边界/段关系，已改为业务身份Trace核对 |
| final-corrections.log：多实例GUI+G08 | 18项，17通过、1测试属性拼写错误，18.598s；outcome.trace已修正traces，不是生产失败 |
| python -B -m unittest tests.test_g06_page.G06PageTests.test_ui_builds_multiple_instances_for_every_process_source -v；final-gui-correction.log | 1/1，9.725s |
| python -B -m unittest tests.test_b_fume_chain tests.test_g06_page.G06PageTests.test_ui_builds_multiple_instances_for_every_process_source tests.test_qzc_n01_c_numeric_unit_pilot tests.test_b_fgd_specialist tests.test_b_material_chain tests.test_canonical_project_inputs -v；final-targeted-pass.log | 最终82/82，69.983s；稳定业务代码实际重新执行 |
| python -B -m compileall -q apps packages scripts tests；python -B -m pip check；python -B scripts/project_appendix_b_v9.py | PASS；编译首次因默认沙箱不能写本工作树__pycache__失败，提升同一隔离树权限后exit0；无依赖冲突，投影字节匹配 |
| python -B -m scripts.validate_canonical | PASS：9标准、12来源、102参数、138因子 |

首次整链导入用错既有Word renderer路径，1加载ERROR；接线纠正后9项1FAIL/3ERROR、30.965s（把dict再json.loads、把GUI当表格页、有限位独立算例用精确比较）。测试接线和仅测试数值参考断言纠正后9/9；正式full-value与运算顺序不改。所有原失败日志位于tmp/b-fume，未删改。

后续最终联合命令/结果、CI、包按固定受验对象的仓内摘要及PR说明补证，不令摘要提交自指制品head。

## 兼容与视觉证据

实际复用已验收b4/CI263包的EXE/PYZ生成隔离旧烟气Record/Word（不是旧源码假扮旧包）。新代码读取时mock Calculator禁止重算，输入hash、ReportModel、Word document.xml hash一致，记录数保持1；证据tmp/b-fume/actual-old-b4-fume/created-proof.json与read-proof.json。原PR49/FGD历史保护继续按固定证据和受影响测试验证，新精确head包还须重复核。

Artifact Tool CLI只读渲染B.6新旧母版，新增表头/单位/提示可读，未重导出模板；实际OOXML仅sheet6变更。node_repl内部依赖node:process不可用，改用已提供CLI运行时，不绕过模板校验。GUI离屏预览先发现offscreen无中文字体，再仅在预览进程显式加载Windows字体复核，布局正常、0Record；未改生产字体、不冒称原生IME/DPI通过。

## 保留的OPEN与停止边界

PR50 F01—F03技术独立PASS与CI263固定证据保留，旧工作树不清理。根用户工作簿/参考文件未动。原生Office保存回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机和商业履约仍OPEN/NOT_RUN。未新增热力/外部CO₂/N/第二标准、无主要依赖/DB迁移/标准全文打包，不自动合并或商业发布；完成本包CI/实包送源后停止。

## 只读记录投影补齐

交付复核发现ReportRow.note虽被Word消费，但既有Qt表卡/文本/HTML未消费，故补齐三个只读显示消费者，使每段真实区间在记录页同样可见；增强既有烟气整链中的实际ReportTableCard与文本/HTML断言。未改算法、Canonical、模板或来源。源指示同步纠正专属模块顶部“尚未接入”的陈旧职责说明，F原算法内容不变。

python -B -m unittest tests.test_b_fume_chain tests.test_p3_c_records_ui tests.test_rpt02_appendix_b -v：首次40项39通过/1失败、58.526s，原Word表头保护测试把v9输入段时长栏与旧报告期栏混比；现明确核对新输入栏、历史Word栏及其余全部表头不变。最终40/40、58.024s，日志tmp/b-fume/final-record-projection-pass.log。该次包含全部15项烟气整链与真实记录表卡；原本地82项仍按其实际执行边界记录。

CI266只对应被替代的e1715fc，不作为最新head的CI/制品；送验以该小修后的新head CI与实包为准，不混用旧结果。
