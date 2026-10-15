# 标准业务规则统一A包实施报告

状态：PR #47 在 dfe2ba4 的独立验收退回后，按 A-R1～A-R4 修复候选定义与证据。当前仍待新 head 独立复验，不能据专项或CI自行宣布阶段PASS。仅A，不接管生产，不实施B/N、不合并PR。

## 平台 / Contract预检查

实核origin为adgo07/GHGTOOL，任务分支codex/ghg-business-rules-a；fetch后main仍为204dded5d03853617f79a1f05693e89b619df9d1。原主工作区用户文件与修改保留。PR46 head77d36a155323bc82199cb516c4ac58a2e1c60309仍open未合并，是后续明确依赖，不能当成main生产事实。

批准V1.2原字节SHA256：98abf84ea7f7af3887d60c3c1e128c272d73ccbf73892d76581ad1771bfad876，保持不变。中央lock ee5feb0cc34dbd99790500fadd0c4c932e202a20；已按lock读取Architecture V2.1、Numeric v1/Profiles v1 Frozen，并读取当前ACTIVE UI v0.2。适用MUST：分层、既有共享Calculator/Resolver、lossless Decimal、declared-profile consistency/ambient independence、exact比较、项目/Record分离、历史不漂移。MUST NOT：第二算法、显示回流、隐式修约/epsilon、自动升级Frozen、重写历史。Carbon p40/HALF_UP为合法项目差异。本包不涉及中央公共Contract修改，无DB结构、公式、Numeric Profile或标准支持范围变化。详见PREFLIGHT.md。

相关Standard Issue：012/C01、013/C02已批准，不重复请求确认；014供电单位实测/企业测算专业适用资格仍OPEN，只阻断相关候选路径。表2/4/5另依赖PR46/Issue010组合；来源binding VERIFIED不等于软件适用性已获批准。A不改变生产解释。

## 真实交付

Common 41/Industry 10条现有G05对象保持main等价；行业固定采用Common修订与成员，不隐式扩围。109 GUI FieldSpec、11标准参数政策字段、36类333个Domain/输入来源/Record/Report投影，共453个定义；数字不是新增产品字段或完整标准覆盖率。Industry/Software修订升至candidate-2026-10-15-a3，Common仍main固定快照。41策略、18操作、12变化；1090条件审阅行（585 READY/505 BLOCKED），结构异常0。BLOCKED包括待核资格、技术待核与非法来源，不是505个生产错误。

A仅维护Canonical候选、严格loader/schema、只读求值/审阅工具、消费者清单和三页审阅表。未改生产GUI、正式Excel模板/Adapter、Calculator、项目/Record、Word、DB、运行参数或打包资源；candidate无生产import。旧活动路径保留，B接管/退出尚未实施。开发期Artifact Tool与schema校验器不是新增运行依赖。

## 退回修正对照

| 项目 | 最终修正与证据 |
|---|---|
| A-R1 | 同一确认身份重复选择/失焦/刷新保留已确认实测、来源、计量路径与草稿；main/PR46旧重置只作历史差异依据。真A→B/离开后重选用新身份初始化；恢复/导入禁初始化。新增明确变化记录和独立资产预期；A不实施生产状态机。 |
| A-R2 | 每字段强制显式default_source：NONE/FIXED/POLICY/PENDING，与合法来源集合、数值default及binding分开。只读initialize_context检验目录燃料、自定义、FGD单/多组分；无匹配碳酸盐EF按Owner既有批准默认MEASURED、数值NONE由用户填写，匹配STD锁定、PENDING不改判；禁止数组首项推默认。NEW_SELECTION已有来源只读保留；身份变化/重选带business_source明确拒绝，必须由未来B服务传新身份fresh context，不猜或删除来源归属。RESTORE/IMPORT/SAME/BLUR/REFRESH禁止初始化。审阅合取保留已有来源，不用默认来源覆盖合法实测或隐藏非法来源。 |
| A-R3 | GUI/Excel FOX、FGD含量/转化率为%，Domain ratio；MaterialInputLine原始百分数与归一化ratio分开。电量MWh；蒸汽GUI/Excel/HeatInput为t、Calculator用现有UnitService转kg。燃料活动路径及main/PR46 Excel位置分别登记；HEAT只记disabled/hidden legacy恢复，不新增可选路径。因子ID/资格枚举不再伪装成因子数值；实际模块级控件与legacy消费者分开。独立测试直接核真实模板、AST和现有换算/物料服务，原始输入不变。 |
| A-R4 | toggle_emission_source单列业务操作：INVOLVED/NOT_INVOLVED改变Canonical纳入状态、mark dirty/stale，保留草稿；导航/折叠/纯view刷新才是Presentation。独立AST核实真实调用链。 |

审阅表新增“默认来源”，数值默认与绑定另列；STANDARD_DEFAULT显示“缺省值”，VERIFIED显示“来源登记已核验”。三页为字段与条件规则、操作与影响、本次变化；稳定键、反馈列、筛选、D6冻结保留。最终数据/工作簿哈希及意见保留结果见evidence/review-artifact-checks.json，审阅投影LF SHA256 7f56056df731938e390ae2415b3a51740ddc5f1f7aa21516a80a1e474b86e1a4。Windows原JSON文件hash与LF规范投影分开记录。

## 本地实际验证

使用Python3.12，在A工作树执行；不是GitHub Actions。最终联合结果如下；远端完整回归与构建单独按最终head登记PR评论，避免为回写CI改变受验head。本次不重复30分钟本地全量；以最终head Windows CI完整套件为准，不冒充本地执行。

| 命令/检查 | 真实结果 |
|---|---|
| `python -m unittest tests.test_business_rules_candidate tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_assets tests.test_business_rules_excel_evidence tests.test_business_rules_candidate_revisions -v` | 最终63/63通过、0失败/错误、9.443s（loader36、业务路径10、资产9、OOXML2、四项独立预期6）。日志build/business-rules-authoring/a3-final-targeted.log。 |
| `python scripts/validate_business_rules_candidate.py --review-json build/business-rules-authoring/review.json data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json data-source/carbon_accounting/business-rules/software_policy.json` | 加载成功；1090/18/12，585 READY/505 BLOCKED，UNCOMPOSABLE/AMBIGUOUS/MISSING_CONTEXT等结构异常0。 |
| Artifact Tool构建、三页PNG查看、readonly工作簿检查、6意见重排/删除定义回导 | 完成：三页已查看；稳定键/哈希/D6/筛选/验证正确，0公式/0错误；6/6审阅意见原样保留，删除定义1条迁入变化页，字面PENDING未改。最终交付无QA意见；XLSX SHA256 5bd80a288f6373b88746dc9995caf1d38e28c286db0a471b8c2bb53d6e3f5cc5。 |
| `python scripts/validate_canonical.py` | 成功：9标准/12来源/102参数/138因子。 |
| `python -m compileall -q apps packages resources scripts tests` / `python -m pip check` | 成功；No broken requirements found。 |
| 开发期Draft202012 schema三包/正负例 | a3 Draft202012 check_schema 1/1、实际三包3/3通过；a2独立焦点例FIXED合法、self-source条件拒绝、nested POLICY拒绝均符合预期，Schema未改。Python3.13仅开发schema检查，不作为正式回归。 |

两项OOXML缓存测试仍保留：临时母版副本中输入公式缺失/陈旧cache定位拒绝，结果公式cache忽略，Decimal原始值不变；这是程序证据，不冒充原生Excel/WPS。生产隔离、完整109/36类盘点、Common adoption、真正默认/来源分离及全条件组合断言保留。

历史失败如实保留：旧dfe阶段虽51/51专项与516/516 Windows CI通过，正式独立验收仍退回4项，旧绿色不是本次PASS。此前早期全量488项为487通过/1失败/0错误；后续本地快照515/515不冒充新head。此次开发中两次独立试跑各出现1error（非法binding TOKEN、依赖a1/a2闭包不匹配），5项先4pass/1error后全过；审阅器发现467 UNCOMPOSABLE已修，未删非法来源分支或放松校验。单位测试最初缺必需产物行导致1fail，修fixture加显式零产物后通过。252a71d复验关闭R1/R3/R4，但指出无匹配EF1误设初始NONE且测试固化错误；已按Owner既有原话纠正为MEASURED（numeric NONE），独立新增匹配/无匹配/PENDING/恢复例。a3独立定向2/2通过，真实审阅表3条无匹配行均显示MEASURED。最终完整回归/Windows构建、审计、启动均以新head CI及真实日志另记，不引用旧run背书。另一次独立修复diff审查15/15通过（Python3.12.14，1.049s），R1～R4无剩余阻断；范围不替代完整A阶段验收。

## 缺项、决定与停止条件

真正专业待决为Issue014（影响未来相关企业电力路径；A只显式PENDING）；C01/C02已批准，不重新询问。PR46与表2/4/5组合是后续依赖/整合验证，不能靠关闭014混同；显隐/复杂集合等未逐项核实仍明确PENDING。A不做生产GUI状态机、原生鼠标/DPI、Excel/WPS保存或无源码新规则部署验收，不冒充已执行。

Owner授权A完成后自动送“方案设计”精确head复验继续有效；最新Owner原话“A包验收通过后先不要继续，提交PR，并告诉我是否还有需要我确认的部分，我要再次独立验收”已覆盖旧自动继续授权。修复更新原PR47、不另建PR、不合并。方案设计PASS后仍停止，交Owner精确head、证据与决策清单，等待再次独立验收及后续明确指令；不得自动B/N或Frozen变更。
