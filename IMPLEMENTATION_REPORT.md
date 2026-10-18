# B-FUME 实施报告

日期：2026-10-18。状态：生产接管、本地定向验证、CI268及精确head实际包验证已完成；等待源独立最终验收。本包不自行合并或扩下一包。

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

## 最终显示修复与独立复验

冻结ReportRow.note原先仅Word消费，已补齐Qt记录卡/文本/HTML消费者，真实区间同样可见。只读投影联合40/40、58.024s；首次40项39通过/1失败、58.526s为新输入时长栏与历史Word栏的保护断言混比，已分别核对，旧Word表头保持。

63182共享身份名称旧候选覆盖问题先真实复现1FAIL、5.129s，再按稳定ID同步各行候选与已选名称；不按同名合并、不改ID/数值。联合命令 python -B -m unittest tests.test_b_fume_chain tests.test_p3_c_records_ui tests.test_rpt02_appendix_b -v：41/41、70.491s。强化同名不同ID、source/boundary切换、未保存No、新窗口服务SQLite单项1/1、12.783s；生产不再改变。python -B -m unittest tests.test_g06_carbon_material tests.test_standard_dispatch tests.test_exb01_rpt02_integration -v：37/37、9.437s。原日志与阶段边界见docs/ci/B_FUME_SUMMARY.json。

源实际独立证据：旧e171的41/41、69.341s与63182的18/18、9.907s仅背书各自当时范围；b0e42f0名称回归1/1、14.525s通过。最终CI/实包验收仍由源独立决定，不自行宣布独立PASS。

## GitHub Actions 与固定制品

受验源码 b0e42f069ee479840b2508bfa7080724d1336fef，算法 CAR-SM01-2026-10-18-FUME.1。CI268 / run39106389790 SUCCESS：
- Merge job117613028826，merge 2d91747cef7cca85204e714918f98c4cea5cbac3：python -m unittest discover -s tests -t . -v，935/935、1597.245s。
- Exact-head standalone job117618533685：python -m unittest tests.test_g08_delivery -v，17/17、6.902s；Canonical/编译/依赖/DB/GUI/缩放/构建/清单/归档/来源检查均PASS，实际EXE两次隔离启动PASS。

以上为GitHub Actions执行，不冒称本地全量。CI266/e171、267/63182不背书本最终制品。原始日志ci268-merge-raw.log与ci268-standalone-raw.log保存于tmp/b-fume，hash入仓内摘要。

实际下载artifact12129870161，59,903,387 bytes；ZIP SHA256 e01ca2272650e2d751f6bf79575d185037066ae67882b3a324fe3bef2b7dff4c；manifest SHA256 c6017e1c07081460c6b0dc1762e62d72193b27946a8230b4aec5c4623783f190；EXE SHA256 3edb91a6e7a94da6ea08956560bc62a8c0079c34e4d5e4fdf4d5b5e6f2472d12。manifest source_commit/pr_head_sha均为固定源码，tested_merge_sha为上述merge。安全解包后278清单条目/279可见文件的尺寸与hash全匹配；129PE普通/延迟导入共114名称，VirtualKeyboard与iapws路径/导入均0。Qt原始版本逐DLL入摘要（含Qt6Pdf 6.140.0.0），不假称全部一致。

## 实际包业务与兼容证明

命令：python -B tmp/b-fume/package-proof.py tmp/b-fume/ci268-package tmp/b-fume/package-proof-ci268-r3 b0e42f069ee479840b2508bfa7080724d1336fef tmp/b-fume/actual-old-b4-fume tmp/b-fume/actual-old-b4-fgd；exit0、proof.json完整生成。业务模块仅从实际EXE/PYZ读取，阻止源码回退；资源与Qt来自实际包，宿主Python/验证工具/工作簿写入器用于程序化离屏证明，不是原生人工界面操作。

部分合计0.2112、完整25.696、缺口25.344；Domain成功3条，GUI成功1条。重叠/缺Q/缺FCh/时长不配/明确INVOLVED空段不新增Record。两段同源边界、h/d、改名稳定ID/同名不同ID/切换、未保存No、实际新窗口新服务SQLite恢复、旧升级取消及不造区间、B.6合法预览不写Record/坏行不暴露部分Canonical、codec1/2/3读取/4往返、旧模板v2～v8、实际记录表卡区间与缺口、冻结Word禁止重算/回查均PASS。

实际旧b4/CI263 EXE/PYZ生成烟气Record，由新包读取时模型/Word正文XML保持，记录数1不变。实际旧b4脱硫历史副本两份Word正文XML同样逐字节保持，记录总数3不变。原旧树和用户数据未修改。原始旧记录hash与proof全部见仓内摘要。

首次证明exit1：合成source_reference用中文说明，不满足稳定标识，正式门禁正确拒绝。第二次exit1：脚本遗漏INVOLVED却断言空源失败。仅修忽略目录中的证明脚本、每次新输出目录，未改生产源码/制品；两次原始日志保留。最终通过后 python -B -m scripts.inspect_release tmp/b-fume/ci268-package 再次PASS（278文件），确认制品未被验证修改。

## 视觉、OPEN与停止边界

Artifact Tool CLI只读渲染新旧B.6，未重导出模板；仅sheet6机械变更。GUI离屏预览在预览进程加载Windows中文字体后可读，未改生产字体。无原生CU。原生Office保存回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机和商业履约仍OPEN/NOT_RUN。

仅本报告/TASK_STATE/仓内摘要补证据；文档提交不冒充已测试制品head。完整统计、source LF hash、制品/原始日志hash与执行边界以docs/ci/B_FUME_SUMMARY.json追溯。PR51保持未合并，交源独立最终验收后停止；不扩下一包/热力/外部CO₂/N/第二标准，不清理旧树或根用户文件，不商业发布。
