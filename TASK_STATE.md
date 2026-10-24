# PR-B：整页V2本地完整回归PASS，待PR/CI与独立验收

2026-10-24：原始unittest完整1074/1074通过，0失败/错误、未列跳过，2741.635秒。运行期间源码/测试/资源SHA无变化，未处理的已删除Qt对象异常0。原100ms几何、45秒模态、每档60秒缩放限制均未改。完整身份/原始log/资源曲线见docs/ui/whole-page-review/integration/qt-lifecycle/full/。

## 完成范围与修复

已完成新建核算整页：八来源目录/十个身份、四态入口、3/2/1响应、真实控件/来源/草稿保留、单正文滚动、公共问题/结果/快照、错误定位。正式计算、来源资格、Canonical、数据库、Record/项目模型及标准支持状态不变，标准库提案未进入本变更。

正式集成发现并修复燃料原始source combo误显：只对已被SegmentedChoiceControl接管的data combo保持隐藏，真实按钮和未包装combo原行为保留。生命周期专项发现只close的测试窗口累积；11个每次setUp拥有的夹具在原断言/close后正确派发已请求的DeferredDelete，检查自身确实销毁，不关闭其他活窗口。销毁揭露两个排队回调访问已删除滚动区；shell构造和SourceCard展开各补QObject上下文，由Qt取消已销毁所有者的任务，不吞异常。新增2个先失败后通过的生命周期用例。生命周期收口相对cd4的原test_*方法AST不改、不删；几何辅助等待保留100ms与全部精确断言，按连续稳定完整状态返回，不强制刷新。

13用例同探针对照：旧前序缩放1.0超60秒、父进程13主窗口/约1561MiB；回收后13/13通过250.470秒，三档均0，结束主窗口/顶层对象0、启动子进程前约614MiB。插桩有开销且成功运行执行三档，不把总时间当性能提升。无探针完整1074全绿才是本轮正式本地证明。源码8哈希新2图由astra局部视觉PASS；旧151/42图/7图仍只背书各历史源。

## 当前交付状态

完整回归通过后按用户要求提交唯一PR，由源会话设计/最终验收；当前尚未push/PR/CI/实包/合并。接续只允许稳定批次、复用既有workflow、核同head运行、保全精确PR-head包，不改费用/工作流，不先合并。PR/CI/制品身份写对应回执，不将CI结果写成本地执行。原生桌面/鼠标/IME/系统DPI、Office、企业真实样例未执行。

当前报告IMPLEMENTATION_REPORT.md；新证据入口integration/qt-lifecycle/README.md与fuel-capture/review.html。原1071/1072完整失败和cd4 HOLD断点保留，Numeric副本污染已移出工作树且原扫描复验通过；没有采用绕本地门禁的方案B。源会话主动wait/read，无需重试先前被拒的跨聊天状态消息。

平台 / Contract预检查：业务仓受验父提交cd4d32d0f09b2e9f3f2a0e27146a20e750166900，实际worktree/origin/HEAD/status均已核；origin为adgo07/GHGTOOL，最新fetch后origin/main仍092604639cd5b2b61fef1523f87fcd711d8aefea且为当前分支祖先，默认main，不需合并调整。沿用codex/ui-business-layout，不重置成果。中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20，已核中央origin、锁定Architecture V2.1及当前UI指南v0.2。适用MUST/MUST NOT：保持Presentation/Application/Domain/Infrastructure分层，Domain不依赖Qt/SQLite/Windows；展示不回流正式计算；UI State不冒充公共Workspace；不可变Record与参数快照不漂移。无公共Contract冲突或需分类的新增偏差，无中央修改或Frozen adoption。本任务不涉及中央公共 Contract。相关Standard Issue：有，既有004/016/018、017、020；本任务改变既有软件解释：否；无新标准问题。
