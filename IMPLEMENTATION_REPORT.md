# 标准业务规则统一A包实施报告

状态：候选实现与本地专项收口完成；最终完整回归/Windows CI结果在本分支PR的精确head验收评论登记，未收到独立验收PASS前不宣布A通过。生产未接管，B/N未实施，不自行合并任何PR。

## 平台 / Contract预检查

仓库origin实核为adgo07/GHGTOOL；独立分支codex/ghg-business-rules-a从fetch后的main `204dded5d03853617f79a1f05693e89b619df9d1`建立。原主工作区的用户文件和修改保留。PR46 `77d36a155323bc82199cb516c4ac58a2e1c60309`仍open未合并；其生产成果作为明确依赖分层盘点，不并入A。

Owner批准V1.2原字节SHA256：`98ABF84EA7F7AF3887D60C3C1E128C272D73CCBF73892D76581AD1771BFAD876`，仓内批准副本与原件一致。中央锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`；按锁读取Architecture V2.1、Numeric v1/Profiles v1 Frozen，并读取当前ACTIVE UI v0.2入口。适用MUST：分层、共享Calculator/Resolver、lossless Decimal、声明Profile与ambient independence、exact比较、项目/Record分离和冻结历史；MUST NOT：第二算法、显示回流、隐式修约/epsilon、自动升级Frozen、重写历史。Carbon p40/HALF_UP为合法项目差异。本包无中央Contract冲突/升级，无数据库结构、公式、Numeric Profile或标准支持范围变更。详细预检查见 `docs/architecture/business-rules/PREFLIGHT.md`。

标准问题：012/C01与013/C02已批准，不重复询问。014为通则与行业企业电力因子路径适用关系OPEN；供电单位实测及企业实测/计算路径在候选中保持PENDING，仅停受影响路径。表2/4/5的适用资格另依赖PR46/Issue010，不借来源binding的VERIFIED状态当作适用授权。A不改变任何现行生产解释。

## 实际交付与范围

- 维护入口：`STANDARD_SEMANTICS_POLICY.md`、既有路线/AGENTS/HANDOFF/台账同步；未建立平行产品路线。批准全文保持原字节。
- Canonical候选：Common 41、Industry 10条现有G05 RuleDefinition对象与main等价；行业采用固定Common修订、固定规则/组成员，新增上游或其他行业不隐式扩围。41+10不是完整标准覆盖率。
- 字段盘点：109个实际GUI FieldSpec、11个参数政策字段、36类333个Domain/输入来源/Record/ReportModel投影，共453定义；30项默认/来源/锁定策略、17项操作、8项变化。字段数不是新增产品功能，也不是专业依据或测试覆盖率。
- 消费者与兼容：`CONSUMER_INVENTORY.md`记录真实调用、旧活动路径、依据与测试、main/PR46差异、模板/报告绑定和未来受控运行资源组合。main为carbon_material_input v1、输入模板v1/1.0.0、Report schema/layout 2.0.0；PR46为外层standard_input v2、模板v4/2.2.0、Report schema 3.0.0/layout 3.0.1。未来B复用精确允许清单和build-manifest，不在A新增manifest或部署候选资源。
- 严格候选加载器/schema/CLI：显式空值状态、重复/未知/悬空/环拒绝、采用范围、类型与有限Decimal检查、真实条件交集、整数计数域、字段局部阻断和固定审阅键。复用现有EffectiveRuleResolver，不实现新公式引擎。策略结果必须终态，不允许嵌套POLICY假装已解析。Schema负责结构；跨引用字段kind/采用范围等语义由loader负责，不能以单独schema通过代替完整候选验证。
- 条件默认：仅STANDARD_DEFAULT可暴露目录BINDING；实测/计算为NONE，不借目录数值改标签。来源资格独立决定；非法来源仍明确SOURCE_NOT_ALLOWED，不因NONE获得填写资格。目录来源值只读，已批准合法来源可显式切换；自定义对象不借其他对象缺省。
- 审阅表：`docs/architecture/business-rules/evidence/业务规则审阅表.xlsx`仅一个交付工作簿，字段与条件规则1090行、操作与影响17行、本次变化8行。规范LF投影SHA256 `ee75a2fc62e68d55d5a8f2d70c5b37b471d0fe25ed0d93fb3f4e5f002275a5ff`；XLSX字节SHA256 `e7df707fae24774eb37b7004c2dbc396b93b357bb8de2e43094eee3c8597f7fd`。原始Windows CRLF JSON文件hash与规范投影hash单独登记，不混用。
- 表格工具为开发期Artifact Tool生成，不新增运行依赖；三页均检查首部渲染，实际文件核验稳定键、D6冻结、筛选表、意见/状态/编号列、无公式/错误单元格。6条意见跨三页重排原样保留，删除定义的旧意见明确进入变化页；QA意见不进入交付文件。

A没有修改GUI、正式Excel模板/Adapter、Domain Calculator、项目/Record代码、Word模型/renderer、打包清单或运行参数。候选模块无生产import；旧活动定义不在A删除，退出由B逐块实施。

## 本地实际验证

正式本地验证使用Python3.12，`QT_QPA_PLATFORM=offscreen`；下列命令在A工作树执行，不是GitHub CI证据。

| 命令/检查 | 真实结果 |
|---|---|
| `python -m unittest tests.test_business_rules_candidate tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_assets tests.test_business_rules_excel_evidence -v` | 最终51/51通过，0失败/错误，9.460s：loader30、独立业务路径10、资产覆盖/组合9、Excel缓存2。 |
| `python scripts/validate_business_rules_candidate.py --review-json build/business-rules-authoring/review.json data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json data-source/carbon_accounting/business-rules/software_policy.json` | 三包加载成功；1090/17/8；READY585、BLOCKED505，UNCOMPOSABLE/AMBIGUOUS/MISSING_CONTEXT等结构异常0。BLOCKED包括待核技术/资格与非法来源，不是505个正式软件错误，也不宣称其已被业务实现。 |
| `node build_business_rules_review.mjs --input review.json --output 业务规则审阅表.xlsx`及`--previous qa-seeded.xlsx` | 实际Artifact Tool生成/导出成功；三页渲染已查看。稳定键和0公式/0错误检查通过；6/6意见保留，1条被删除定义意见转入变化页，字面PENDING未被翻译改写。脚本在开发临时目录解析工具依赖，输出检查摘要见review-artifact-checks.json。 |
| `python -m unittest discover -s tests -t . -v`（本地收口快照，候选语义对应1d120ea） | 后台本地执行；通过/失败/错误数量与日志在正式PR验收评论登记。最后binding状态修复由51项专项及最终精确head CI完整回归确认，不以这次修复前的本地快照冒充最终全量。 |
| `python scripts/validate_canonical.py` | 成功：9标准/12来源/102参数/138因子。 |
| `python -m compileall -q apps packages resources scripts tests` / `python -m pip check` / `git diff --check` | 编译成功，依赖无损坏，diff格式检查通过。 |
| 开发期Draft202012Validator.check_schema +实际三JSON +8个聚焦schema正负例 | 均通过；开发校验器未加入生产依赖，不替代loader的跨引用语义校验。 |
| 独立main归档Resolver / PR46 checkout定向 | 2/2与4/4通过，完整命令/边界见电力证据文档；依赖测试不反推为main已采用表2/4/5。 |

本地全量早期失败如实保留：开发中488项，487通过/1失败/0错误，1795.228s，失败为当时资产字段尚未补齐的覆盖断言，后来已修，不称该次全绿。新增覆盖测试曾错归CalculationTrace模块产生1error，修正测试导入；目录binding测试曾过强假设所有binding显式声明标准ID导致156子例失败，经实际Resolver证据区分登记与资格后修正。独立审查发现nested POLICY、schema/runtime边界与连续计数问题均修复；最终投影又发现200个电力非法来源默认分支无法合取，补NONE且保留资格阻断，新增整表断言，最终结构异常0。随后独立资产复核发现表2/4/5将来源登记状态混写为适用性PENDING，已恢复真实VERIFIED条件、保留资格/结果PENDING及精确绑定理由，新增六个方向子例；未放开专业资格。失败不会通过删重要断言、放松正式来源规则或改公式掩盖。

公式缓存2项以临时母版业务副本直接改ZIP/OOXML：输入公式缺失/陈旧cache均定位拒绝，不产生预览计算；结果公式两种cache均忽略，完整Decimal输入不变。此为程序OOXML证据，不是原生Excel/WPS验证。

## A出口、已知待核与送验

当前全部FieldSpec与36类投影可查，重要操作与main/PR46旧消费者可查；冲突/缺项有明确状态、位置与证据。候选加载/求值/审阅可运行，生产切换为零。本报告固定本地专项与资产证据；最终CI、本地全量及独立head验收结果另附正式PR验收评论，避免为回写CI而改变受验head。不能据本地51项自行宣布A PASS。

保留未闭合项：Issue014专业资格；表2/4/5对应PR46依赖组合；自定义期间/电力逐条件显隐和部分报告投影呈现未全核。FieldSpec advanced的31 true/78 false（135 GUI projections中33 true）只是元数据，不是运行显隐权威；period_start/end未独立登记FieldSpec已列清单缺口，不隐藏。复杂集合/未声明字段策略明确PENDING，不生成猜测默认。A不做原生鼠标/系统DPI、Excel/WPS和源码隔离安装包业务验收；这些不冒充已执行。Windows CI/发布审计完成后以精确PR head及日志另附，PR46历史结果不充作A证据。

依据Owner直接授权，A完成后自动送“方案设计”（01a13325-68df-70f1-b39a-ad523c62e3a2/local）精确head/PR/真实diff与证据，等待独立PASS。PASS后方可继续已批准的B先完整燃料链；N独立。此授权不含PR46或本PR合并、新专业解释、标准扩围、破坏性迁移或Frozen升级。
