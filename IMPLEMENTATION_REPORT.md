# 新建核算整页V2实施与本地验证报告

## 结果

本地完整回归已通过：1074/1074，0失败、0错误、未列跳过，2741.635秒。运行期间源码、测试和资源SHA无变化，未处理的已删除Qt对象错误0。当前准备稳定提交/唯一PR与既有CI，不自动合并。发布/CI/候选包实际身份另以本提交的PR和本地交付回执记录，不把旧CI/包改标为当前head。

## 实施范围

八类业务来源目录复用十个原Domain身份和全部真实控件；导航不启停、不计算、不改dirty/指纹/草稿。四态入口、顶部项目/当前单元/检查计算、公共外部补充/问题/结果/快照、跨源错误定位及3/2/1列自然重排完成，保留品牌与全局侧栏、唯一正文滚动。燃料DIRECT未参与热参数可展开且保值，电力五表/OTHER/零因子和来源资格完整；三工序物料、烟气区间、脱硫设施—批次—组分、热力边界/焓方式继续原规则。

没有改变计算公式、来源资格、Canonical、数据库/迁移、正式Record/项目模型、依赖、模板或报告规则，没有实现标准库提案或其他页面业务/布局。成功正式核算仍追加不可变Record，失败零Record；显示/导航不回流计算，输入改变后旧结果出口仍受门禁保护，未升级SUPPORTED。

## 集成收口

- 燃料4个原data combo被刷新误显，增强真实控件边界发现后修复：仅父为SegmentedChoiceControl且owner.combo是原对象时隐藏；真实按钮、原对象/itemData/信号、资格、精度草稿、输入/报告保留，未包装combo仍遵循原visible逻辑。
- 完整运行两次出现scale1.0原60秒超时。分段13前序在原数据/断言/60秒下诊断复现并采到实际进度/栈：55秒在能源行构建、60秒Qt事件，不是模态等待。前序遗留13关闭但未销毁主窗口、2487顶层对象、约1561MiB私有内存。正确销毁相同夹具后13/13通过250.470秒，三档均0，套件结束主窗口/顶层对象均0，启动子进程前约614MiB。探针有开销、失败只执行第一档而成功执行三档，不将总时间对比为性能提升或把诊断当原命令验证。
- 限定修复11处每次setUp拥有而只close的测试夹具。原断言与close照常，之后请求对象删除，正常派发已请求的DeferredDelete并检查自身销毁；不关闭其他活窗口、不复用旧数据/结果/缓存、不跳验证。仅测试生命周期辅助函数与调用处变化。
- 真正销毁后揭露两个排队回调访问已删除ContentScrollArea。shell构造回调、SourceCard展开回调各补一个QObject上下文，让Qt取消已销毁所有者任务，不catch/吞RuntimeError。两个新增用例均先失败后通过，保存红绿日志。
- 原100ms几何等待在最后额外一轮未观测事件后失配4069/3831；失败后两轮正常事件即正确3831并稳定。只把等待辅助函数改为至少8次观测、连续3次完整状态相同且高度精确匹配，保留100ms及原行数/增删/保值/滚动断言，不activate或调用产品refresh。6前序39.100秒通过、Qt异常0。

生命周期收口相对cd4的旧test_* AST没有改写或删除，只新增2生命周期用例；早期按批准V2更新的3处陈旧结构断言另见原诊断分类，仍保留Canonical选项/别名、真实公共区/顺序、可见单位及响应完整性。原20行测试2秒正常稳定观测仍保留，原45秒模态和每档60秒缩放从未提高。

## 执行与证据

环境：Windows、Python3.12.14、Qt6.11.2、offscreen，合成输入/隔离临时库。下表均本地执行，不是GitHub Actions或原生人工。

| 命令/范围 | 实际结果 | 证据 |
|---|---|---|
| python -B -m unittest discover -s tests -t . -v（当前稳定树） | 1074/1074 OK，0失败/错误、未列跳过，2741.635秒 | qt-lifecycle/full/full-tests.log及identity.json；源码/测试/资源变更0、未处理Qt已删除对象错误0 |
| 原始全量运行器与资源观测 | 退出0，2760.297秒含进程退出，不混同测试耗时；原测试及子进程未注入探针 | full/runner.py、resources.jsonl；外部仅只读采样 |
| 导航/销毁回归模块 | 5/5 OK，0.580秒，含2个先红后绿用例 | diagnostics/navigation-final.log及lifecycle/card红绿日志 |
| 前序6项几何回归 | 6/6 OK，39.100秒，Qt异常0 | diagnostics/geometry-prefix-after-wait-v2/ |
| 同13前序资源回收诊断 | 旧0失败1错误/187.395秒；回收后13/13、250.470秒，三档均0 | diagnostics/prefix-uir03/与prefix-uir03-disposed/；含插桩，不冒称原CLI性能 |
| 最终compileall apps/packages/resources/scripts/tests、diff --check | 均退出0 | diagnostics/compile-final.log、diff-check-final.log；暂存/提交再核 |
| 燃料真实代理宽窄专项（cd4前） | 1/1 OK，32.511秒，默认/实测/仅DIRECT计算/禁用/草稿/报告/旧combo兼容 | integration/fuel-proxy-policy-wide-narrow.log；与全量重叠不累加 |
| 原失败1071全量 | 1065通过、3失败3错误，2994.432秒 | integration/full-tests.log与initial-failures.txt，不覆盖 |
| cd4前1072全量 | 1070通过、1失败1错误，3021.448秒 | integration/final-full-tests.log与final-discover-identity.json，不覆盖 |
| 诊断副本移出后原Numeric扫描 | 1/1 OK，4.157秒，不改规则 | numeric-scan-clean.log；最终1074全量亦通过 |
| 早期canonical/pip/隔离库/5GUI/离屏1.25与1.5 | 均通过，canonical9标准/12来源/102参数/138因子 | integration对应日志；早期53a身份，非当前CI，脚本名manual不代表原生人工 |

完整原始log SHA256：bb87c7ac200458d16a6af08bbb7fdb7a84dc748f97f175702aeea8dbb4ee7302。受验父HEAD为cd4d32d0f09b2e9f3f2a0e27146a20e750166900；工作树实际身份由逐文件SHA清单确定，不把父HEAD当无差异受验提交。提交后核源码身份，最终发布head见PR/交付回执，避免文档自引用SHA。log/json/jsonl/txt按目录属性保留原始字节，代码与资源身份分列。

完整分支差异检查随后只清理开发截图生成器scripts/capture_accounting_ca.py末尾多余空行；AST与有效token完全等价，运行程序、测试、Canonical资源字节仍与受验清单一致，见qt-lifecycle/post-full-capture-eof.json。不为无语义EOF清理机械重跑1074；截图历史脚本身份保留，不改旧摘要。原始统计日志自带末尾空行按证据属性保存，不修改日志字节。

## 视觉范围

当前8源绑定入口：integration/qt-lifecycle/fuel-capture/review.html，1680/1180真实Qt展开图；摘要绑定8个UI源及捕获脚本，销毁后异常0、代理/边界/保值/零Record守卫通过。astra实际逐张局部视觉PASS，8/8源哈希匹配，未见来源/报告/未参与参数层次的视觉回退、裁切或重叠；astra只目视，自动守卫属于脚本执行，不冒称其亲自跑测试。

原7张燃料图、42张整页图、53a源会话独立13/13（80.675秒）、旧151主回归394.851秒及最后8行定位补丁/13项79.044秒/重复1项7.929秒保留各自身份与边界，不重标当前源或累加测试数量。旧151并非全部在53a或当前head执行；当前1074完整回归是新的本地功能证据。

## 诊断与证据限制

Numeric旧失败来自我方main源码诊断副本位于工作树build目录，ROOT.rglob误计为生产命中；已完整移到工作树外并保留原ZIP，不改扫描规则，单项及最终全量通过。不是产品Numeric语义问题。

前两版采样/faulthandler探针出现访问异常，v1未声明Win32句柄类型导致进程内存字段0；这些弃用诊断原件保留，不用0值分析，也不把访问异常定性为产品根因。实际前后对照使用v3主线程进度和正确外部计数。cProfile两次未在60秒内完成，局部统计不用于优化产品；最终完整命令无这些探针。

较早一份11项代表性运行日志因同名后续输出被覆盖，不能称该份原文件仍完整。终端摘录为11项/1失败/0错误、187.178秒、4069/3831及两条已删除滚动区异常；后续同故障的完整11项日志已独立保留（204.797秒），两个核心完整失败原件均保留。证据限制与各诊断版本见qt-lifecycle/README.md；后续独立目录/排他创建，原完整日志SHA已核，不把摘录冒充原字节文件。

## 平台 / Contract预检查

平台 / Contract预检查：业务仓受验父提交cd4d32d0f09b2e9f3f2a0e27146a20e750166900，实际worktree/origin/HEAD/status均已核；origin为adgo07/GHGTOOL，最新fetch后origin/main仍092604639cd5b2b61fef1523f87fcd711d8aefea且为当前分支祖先，默认main，不需合并调整。沿用codex/ui-business-layout，不重置成果。中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20，已核中央origin、锁定Architecture V2.1及当前UI指南v0.2。适用MUST/MUST NOT：保持Presentation/Application/Domain/Infrastructure分层，Domain不依赖Qt/SQLite/Windows；展示不回流正式计算；UI State不冒充公共Workspace；不可变Record与参数快照不漂移。无公共Contract冲突或需分类的新增偏差，无中央修改或Frozen adoption。本任务不涉及中央公共 Contract。相关Standard Issue：有，既有004/016/018、017、020；本任务改变既有软件解释：否；无新标准问题。

现有项目专属GHGTOOL_CARBON_DECIMAL40_CURRENT（precision40/ROUND_HALF_UP/full-value exact比较）不变，不描述为平台默认。没有中央公共规则/RFC新缺口，没有修改Frozen Contract、baseline或其他两套软件接口。原100ms/45/60秒限制和业务保护未改，没有采用绕本地门禁的B方案。

## 交付边界

本提交发起时尚未执行本轮PR/CI/当前head standalone实包；获本地完整通过后沿既有workflow一次稳定批次执行，实际结果写对应PR及独立本地交付回执，不将CI写成本地证据、不将旧包改标新head。若失败先读日志定位再必要重试，不无变化rerun、不改费用/工作流。未执行原生鼠标/IME/系统DPI、Office与真实企业样例；未合并、未正式发布，不据UI与工程候选宣布SUPPORTED升级。
