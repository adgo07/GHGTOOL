# 新建核算整页V2正式集成实施报告（HOLD）

## 结果与范围

八类业务目录/十个底层身份、四态启用入口、真实业务控件、3/2/1响应重排、唯一正文滚动、公共外部补充/问题/结果/快照及跨源错误定位已实施。沿用原Canonical、Calculator、来源资格、项目/Record与正式核算链；未改标准业务解释或支持状态、数据库/依赖/模板/报告规则，标准库提案未进入本变更。

正式集成尚未完成。最终稳定完整回归1072项有1失败1错误，不能以局部PASS宣称全绿。没有push、PR、CI、当前head实包或合并，不宣布Windows正式发布。

## 本次限定增量

增强真实控件边界检查发现四个原始燃料source combo被刷新误显。新增_set_fuel_source_visibility：仅父为SegmentedChoiceControl且父.combo为原对象时隐藏内部data combo；真实来源按钮继续消费原combo/itemData/信号，未包装combo保持原可见性。保留缺省/实测、仅DIRECT合法计算、禁用资格、精度草稿和报告。生产仅carbon_material_page.py这处16行差异，完整diff由Git审阅。

三个旧布局断言更新为唯一公共区及顺序、完整可见压力单位标题、原控件/选项身份与响应重排。20行测试使用正常processEvents/DeferredDelete、真实2秒截止和至少8观测且连续3轮稳定，不强制activate/产品refresh；严格保留高度/scroll max下降、剩余身份、行与可见控件父内边界、无重叠与Qt异常检查。

## 本地执行结果

环境Python3.12.14、Qt6.11.2/offscreen、合成输入/临时数据库。原命令、输出、诊断脚本及受验文件哈希见docs/ui/whole-page-review/integration/。

| 执行 | 实际结果 | 证据边界 |
|---|---|---|
| 首轮python -B -m unittest discover -s tests -t . -v | 1071项；1065通过、3失败3错误；2994.432秒 | full-tests.log及initial-failures.txt完整保留 |
| 最终稳定树同命令 | 1072项；1070通过、1失败1错误；3021.448秒；未列跳过 | final-full-tests.log、final-discover-identity.json；开始/结束源码/测试/资源哈希无变化；运行器3104.688秒含退出，不混用 |
| 三处旧结构定向模块/单项 | 12/12，23.321秒 | updated-layout-tests.log；保留业务断言 |
| 20行增强边界中间运行 | 1失败，发现原始combo geometry超父容器 | twenty-rows-updated.log不伪作通过 |
| 四combo直接hide中间方案受影响回归 | 16/16，121.164秒 | fuel-adapter-fix-tests.log；后增加owner guard，非最终guard完整证明 |
| 最终guard四来源真实交互宽窄专项 | 1/1，32.511秒 | fuel-proxy-policy-wide-narrow.log；与全量重叠不累加 |
| 原包装器隔离模态/缩放 | 各1/1，3.805秒/94.690秒 | modal-isolated.log、scale-test-isolated.log；原45/60秒限制 |
| 最终候选原child独立输出 | modal12.485秒；scale1.0/1.25/1.5为52.797/39.484/44.813秒；均0 | exact-children/；只证明隔离未复现 |
| 移出诊断副本后原Numeric扫描单项 | 1/1，4.157秒 | numeric-scan-clean.log；不修改扫描规则 |
| faulthandler缩放1.0定时栈诊断 | 38.968秒，退出0，仍60秒限制 | scale-trace.*；诊断运行，不是原包装器结果或失败运行调用栈 |
| 最终compileall apps/packages/resources/scripts/tests与git diff --check | 均退出0 | final-compile.log及本地Git检查；当前源码 |
| 早期53a canonical/pip check/隔离数据库/5GUI及1.25/1.5离屏缩放 | 均通过；canonical9标准/12来源/102参数/138因子 | 对应初始日志；非当前head CI、非原生人工，script含manual字样不改变此边界 |

最终完整套件中，本次14项来源目录、20行严格增删、公共结果区、Canonical选项/别名、热力单位标题及45秒中文模态均通过。不能把1070通过与任何重叠专项累加声称更多独立用例。

## 原六项问题及未关闭项

详细分类见integration/README.md：三处旧结构断言已按批准V2更新；20行即时1ms假设有current/main自然事件对照，并新增边界发现/修复实际combo缺陷；模态原45秒本轮完整通过；缩放1.0原60秒在两次完整套件仍超时，OPEN。原脚本/超时/CI工作流未改，没有以删除字段、强制刷新或提高时间阈值获取通过。

最终新增Numeric扫描失败来自我方git archive main诊断副本位于工作树build目录，ROOT.rglob把副本中的测试/decimal_policy当作生产命中。副本及原ZIP完整保留，副本移至工作树外的workspace临时目录；原扫描规则不变单项通过。这是诊断落点污染，不是产品Numeric语义问题，不更改Numeric guard。

缩放诊断10秒栈位于页面燃料输入构建，20/30秒位于动态物料layout.addWidget；该运行继续完成，没有模态等待的栈证据。但未捕获完整套件那次超时子进程栈，也未确认导致两次全量超时的原因，不能宣称环境原因、确定性卡死或根治。没有机械进行第三次完整discover或推远端绕过本地门禁。

## 视觉、身份及历史证据

新候选完整42图重采后，归档5张受影响燃料图与2张DIRECT展开宽窄图于integration/fuel-capture/review.html，summary.json/expanded-summary.json绑定7UI源与脚本；父HEAD53a与实际工作区源哈希分列。page SHA256 bb1208c2a829e3715423440d0bdfe0da7124fe3e4e9fbac37fb04ebad421612e。astra逐图7张局部视觉PASS，现场7/7UI哈希匹配，展开两图另核page一致。无来源裁切/报告截断/原combo残影或重叠，DIRECT展开的未参与参数及灰化来源完整可读。

捕获脚本自动守卫：原控件/输入保留、浏览不改form_state、失败零Record/一次成功追加一条/输入改后出口禁用，展开代理可见禁用/raw combo隐藏、可见控件父内边界、宽窄完整form_state不变、零Record、回调异常0。astra仅目视，不冒称亲自运行自动守卫。本轮7图不重验或重标旧151测试/42图。

历史53a3ae83256aeb6ee8b95f426fb6d7297493b65c有源会话独立13/13（80.675秒），回执final/independent_acceptance.md；旧151项394.851秒对应最后定位前哈希，最后8行定位补齐由13项79.044秒及重叠1项7.929秒覆盖，原tested_151_identity.json与error_locator_final_delta.patch保留。当前新增适配器差异超出8行，不能将旧151宣称全部在当前增量执行。

## 平台 / Contract预检查

平台 / Contract预检查：起始业务仓53a3ae83256aeb6ee8b95f426fb6d7297493b65c，实际origin为adgo07/GHGTOOL；当轮fetch核main为092604639cd5b2b61fef1523f87fcd711d8aefea且为祖先，沿用codex/ui-business-layout。锁定中央ee5feb0cc34dbd99790500fadd0c4c932e202a20，已核中央origin、锁定Architecture V2.1及当前UI指南v0.2。分层、展示不回流、Presentation State隔离、历史Record不漂移保持，无冲突、无中央修改，不升级Frozen baseline。本任务不涉及中央公共 Contract。相关既有Standard Issue004/016/018、017、020；无新增解释或标准适用范围变化。

受验工作区身份以final-discover-identity.json逐文件SHA256为准，最后本地提交由Git HEAD/交付回执给出，避免文档自引用SHA。没有修改Frozen Contract或baseline，也无跨产品接口变更。

## BLOCKED

问题：当前正式集成要求的本地完整回归未全绿，缩放1.0仍超60秒。
证据：两次完整原始日志；最终1072项/1失败1错误；Numeric落点污染已定向关闭；原阈值隔离及栈诊断不能替代完整结果。
为什么不能按原方案继续：本仓Delivery要求先处理已知失败再稳定批次push；当前不能诚实声称满足验收，不自行更改原阈值或CI门禁。
可选方案A：继续专项定位完整套件执行后该子进程耗时，并在证据支持下提出限定修复。
可选方案B：Owner明确批准将该本地超时保留为已知限制，允许当前head一次既有CI比较；不改费用/工作流，不将CI证明回写为本地通过。
建议：优先A；若选择B，须明确此次门禁例外，保留当前HOLD与真实失败。
需要决策的具体问题：是否继续A，或批准B；在决定前停止push/PR/CI/实包。

未执行：当前head Actions与standalone实包、原生桌面/鼠标/IME/系统DPI、Office与真实企业样例。未合并、未发布、不升级SUPPORTED。跨聊天发送状态被自动审批拒绝，若需向“方案设计”发送本轮回执，需明确具体发送授权。
