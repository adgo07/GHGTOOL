# B-FUME PR51-F01 小问题修复报告

日期：2026-10-18。状态：本地定向与相关验证完成，新源码CI273及精确head实际包已通过，等待源独立最终验收及合并。前轮CI268仅为历史阶段证据，不背书本修复。沿用原PR51、原独立树与分支，C不执行合并。

## 问题、Owner决定与最终行为

独立报告PR51-F01证明：原秒级起止允许1/5/10分钟，但d/h有限Decimal不能满足原整数比精确校验；增加小数位不能解决。Owner本次明确烟气精确到小时足够，按此改变软件输入精度决定，不采纳报告保留分钟/秒支持的建议，不把整小时说成标准原文限制。

正式FUME_V2起止均须整小时，分钟/秒/微秒非零明确拒绝，不截断/舍入/改写。旧细时间dataclass、codec与项目仍可读保存原值，新正式计算清楚提示限制。区间精确得整数小时；h录入值全值等于整数小时，d录入值全值等于声明Profile下hours/24的规范化日值，不声称有限d与物理有理时长绝对相等。两路统一消费同一日值；真不一致继续阻断，无epsilon/display回流。原录入与实际采用日值分别冻结，原式(9)、参数来源政策、其他排放源不改。

方法CAR-FUME-SEGMENTS-020.2、算法CAR-SM01-2026-10-18-FUME.2。GUI/B.6推荐小时填写，避免手抄循环小数。v9/2.7.0只机械修改sheet6提示；当前hash 0fa20cbc126fadd2807fe02bea9b26b4a8855285e6b90fc171985557a895fae9，旧v2-v8原字节不变。Word只消费冻结值，布局业务结构不变。

## 平台 / Contract 预检查

业务退修起点cdbec9588d39533d26dd6a50f6476478547f3ff9，实际origin adgo07/GHGTOOL、fetch、main8d054d2480d744882f4f11f56b59e68df91dc50f、分支和干净原树已核。中央origin已实际核验并fetch，locked ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；按locked Architecture2.1/Numericv1/Profilesv1，ACTIVE UIv0.2按已合并origin/main入口读取。

MUST：共享Canonical/Application/Domain、声明Profile传播、ambient独立、full-value exact、原值/规范化值/显示值区分、历史冻结。MUST NOT：float/默认epsilon/display回流/复制算法/公共Workspace复制Qt状态/自动Frozen升级。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE。F01为LOCAL DEFECT，Owner批准小时产品精度解决表示边界；无中央缺口或修改。相关Standard Issue020已先登记；本次改变软件实现决定：是（整小时精度与规范化值比较），不改标准公式或发布机构解释。

## 资源装配与历史证据

pyproject漏v9已用限定excel_templates/*.xlsx修复。G08根据实际模板目录核package-data声明，新增真实wheel/sdist构建和wheel安装后逐字节校验全部8份模板，并检查无用户数据库/计算表。脚本scripts/verify_distribution_templates.py隔离复制代码/资源，运行副本随验证结束，不把副本当正式源码。CI252通过git ls-files确认仅docs/ci/CI252_SUMMARY.json，PR50已迁移，未重复或改旧证据。

scripts/verify_frozen_record_word.py接受实际历史SQLite/ID/既有Word，复制数据库后mock禁止Calculator/Resolver重算，比较document.xml并验证原库hash/记录数；可从完整checkout以python -m运行，不内置历史真值或用户库。当前实际执行：旧b4烟气与两份脱硫正文不变；另用实际CI268旧EXE/PYZ生成其当时合法3分钟Record，新代码读取模型hash 01d740a44a7765c7543c936cb64e53ea2e325b43312a454fe12707811fe48b77、正文XML hash 520b5173479093e0e1e1d577b191b64eb7bca2a976f18bf42be919e5112da13f均保持，count1原库不变。作者实包生成与仓内读验脚本分别记录，不冒称源会话重跑。

## 本地执行

Python3.12.14，离屏Qt、隔离SQLite/临时目录；未做原生CU或Office操作。

| 命令 | 结果 |
|---|---|
| python -B -m unittest tests.test_b_fume_segments tests.test_b_fume_chain tests.test_g08_delivery -v | 66/66，64.768s；小时与d路径1/5/10/24/48、Profile/ambient、分钟/秒/微秒拒绝、真不一致、相邻覆盖、旧codec/SQLite、GUI/Excel正式冻结与零新增 |
| python -B -m unittest tests.test_b_fgd_specialist tests.test_b_material_chain tests.test_rpt02_appendix_b tests.test_p3_c_records_ui tests.test_qzc_n01_c_numeric_unit_pilot tests.test_main_integration_excel tests.test_exb01_ingress tests.test_standard_dispatch tests.test_g08_delivery.G08DeliveryTests.test_actual_wheel_sdist_and_installed_templates_keep_every_current_resource -v | 最终135/135，62.699s；包含CI271修复前验证脚本 |
| python -B -m scripts.verify_distribution_templates --output-dir tmp/b-fume/hour-distribution-final | PASS：真实wheel/sdist及安装资源8份模板字节一致，无用户库/参考目录 |
| python -B -m scripts.verify_frozen_record_word --records <隔离历史SQLite> --record-id <ID> --expected-docx <既有Word> | 4个实际历史对象PASS；不作为4项unittest累加 |
| python -B -m compileall -q apps packages scripts tests；python -B -m pip check；python -B -m scripts.validate_canonical；python -B scripts/project_appendix_b_v9.py | PASS；Canonical9标准/12来源/102参数/138因子 |

原相关134项133通过/1失败、50.025s：手动装配副本被全仓Numeric扫描认为额外代码；保留移至仓外并改短生命周期，不削弱原Numeric测试。其次135项134通过/1ERROR、49.652s：验证脚本替换import误改探针字符串；修正并编译后最终135通过。生产公式未改，原始日志hour-related.log/hour-related-pass.log/hour-related-final.log保留。当前B.6由Artifact Tool只读渲染核验，整小时提示可读，不重导出模板。

## CI / 实包 / 停止边界

新CI与精确head实际包均完成，固定证据已在docs/ci/B_FUME_SUMMARY.json补齐；CI268及旧P→D关系保留pre_hour_stage，不能背书小时修复。原生Office回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机、商业履约继续OPEN/NOT_RUN。完成新CI/实包交源独立验收，合并由源执行；C不合并、不CU、不扩热力蒸汽/其他包、不清理旧树和根用户文件。

## CI271 验证器定向修复

CI271/run39113048982实际全量942项，941通过/1ERROR、1532.572s；唯一为新G08 installed-resources来源路径断言，standalone跳过，无新制品。原CI未打印路径，不能声称已实证8.3或editable具体成因。本地有效非规范临时目录别名复现同一断言：实际从wheel安装目录导入，但子路径resolve/父路径未resolve误判。验证器现统一resolve，并用-I/-S隔离安装探针，打印实际资源与安装根诊断；严格来源及8份模板字节断言保持。回归同时注入路径别名与sitecustomize预导入源码resources。

python -B -m unittest tests.test_g08_delivery tests.test_qzc_n01_c_numeric_unit_pilot -v：首次38项37通过/1ERROR、32.766s为回归覆盖既有PYTHONPATH致本机构建缺setuptools；保留原构建路径并额外注入后38/38、18.961s。实际wheel/sdist/安装资源证明再次PASS。原小时业务/模板未改；此前66/135属验证器修复前范围。原始失败/复现/最终日志保留，后续新head全量CI与精确包结果见最终节，不借CI271失败或CI268旧证据放行。

## 小时边界词法必要补漏

c8实际入口补核发现datetime.fromisoformat将第7位非零小数秒静默截掉：2025-01-02 00:00:00.0000001变为整小时，GUI与B.6正式链合计生成2条隔离Record。before证据submicrosecond-before.log保留；源确认此为本次“不截断、明确拒绝非整小时”决定内普通Bug，立即补漏，不新增标准解释。

GUI/B.6共用parse_fume_timestamp，在datetime解析前检查所有点/逗号小数（含Python实际接受的小时/分钟后小数形态）；六位之后任何非零数字明确拒绝，超位全零才与可表达时间同一物理时刻。原可表达分钟/秒/微秒仍能构造/保存，正式整小时门禁不变；不改公式/Profile/算法版本/codec/模板。python -B -m unittest tests.test_b_fume_segments tests.test_b_fume_chain tests.test_g08_delivery -v：68/68、70.196s，包含真实渠道零Record与全零对照、旧细时间保留。diffcheck发现docstring空行空白已在提交前规范化；无功能改动。

CI272对应补漏前c8；即使其后通过，也不能背书本补丁。当时继续新head CI及精确包；最终结果已在下节收口，尚未启动下一包。

## 新CI与实际包最终结果

固定源码 bbb1d5bd953d463013f135c1047de33fc37fcc59；测试merge c5f71d437a30f4b98803349054d4fbd27a6b754b。GitHub Actions CI273/run39116916157 SUCCESS（非本地全量）：job117644463932 执行 python -m unittest discover -s tests -t . -v，944/944、1573.998s；精确head job117649889623 G08 18/18、9.817s，GUI/缩放/编译/依赖/DB/构建/清单/归档/来源审计及两次隔离EXE启动PASS。源独立3ee阶段小时66/66、97.937s、c8阶段装配1/1、15.882s、当前head词法2/2、8.858s通过，不冒称源重跑作者包内探针。

实际下载artifact12133602018；ZIP SHA256 40cfd4632226474853e5ab320323edb2c734b9b974460002b9dd7b59133b6005；manifest 0561ed757065469edcbea9ab40328fe9a04dfce01a3c3a4214c22b6bb2864330；EXE e3dce0a1041f86ae1bde798ec23d6de00529cd6ce2d440a611a50cb505c79dea。manifest source/pr_head均固定源码，merge一致；278登记/279可见文件的全部尺寸/hash匹配，129PE普通/延迟导入审计通过，VirtualKeyboard/iapws排除；逐DLL原始版本见摘要，当前v9hash核验通过。

实际包命令见摘要actual_package_business_proof，exit0：原烟气整链、点/逗号及小时/分钟/秒后超精度文本六种反例零新增、全零尾数两渠道对照、1/5/10/24/48小时h/d规范化与Profile/ambient、分钟/秒/微秒/真不一致零新增、实际GUI/Excel小时同结果、旧细时间GUI保存/新窗口恢复仍保留原值、新正式核算明确拒绝；实际旧CI268三分钟Record模型/Word XML保持，旧b4烟气及两份脱硫冻结正文也保持。Domain旧烟气基线3成功记录、小时专属10成功记录、原烟气/小时GUI各1成功，独立词法全零对照GUI库2成功；非零词法反例0新增，分别计数，不混作测试数量。业务仅EXE/PYZ，资源/Qt来自包，宿主验证工具边界不变；不是原生人工操作。验证后inspect_release再次PASS，制品未改。

原始CI日志、包证明、所有hash和失败原因详见固定摘要；后续仅三证据文档提交不冒充CI273制品head。源核对应身份后依用户授权合并；C不合并，合并确认前不写下一包代码。

当前bbb源码的本地实际wheel/sdist/安装模板证明已重新保留于tmp/b-fume/final-distribution-ci273（8份模板全字节一致），与CI273 G08分别标记来源。实际包v9 hash确为0fa20cbc126fadd2807fe02bea9b26b4a8855285e6b90fc171985557a895fae9，v2-v8逐字节匹配受控源。首次本地下载TLS EOF且无ZIP，审计未成功；系统curl重试后digest及全审计通过，此为网络工具失败，不计为测试失败。CI272已API观察SUCCESS，但属于补漏前c8阶段，不背书最终bbb制品。源独立最终身份/包验收及合并尚待完成。
