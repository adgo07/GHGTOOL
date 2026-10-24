# PR-B：正式集成HOLD，交接缩放超时定位

沿用既有codex/ui-business-layout；不重做已认可UI、不创建替代分支、不重置成果。唯一生产追加为page中带适配所有权检查的燃料来源combo隐藏：仅父为SegmentedChoiceControl且owner.combo是原对象时隐藏data combo；真实按钮/原对象/itemData/信号/资格/草稿不变，未包装combo沿用旧visible。三个旧结构断言按V2更新，动态20行用正常事件/真实2秒期限/连续稳定观测，并严格验证边界、滚动下降及身份。

最终稳定全套1072项：1070通过、1失败1错误，3021.448秒，代码/测试哈希无变化，见integration/final-full-tests.log和final-discover-identity.json。新增Numeric扫描失败来自我方放入工作树的main诊断源码副本，现完整移到工作树外且原用例1/1通过4.157秒；不要修改扫描规则掩盖。缩放1.0在完整套件再次超60秒，仍OPEN。

原阈值隔离三档通过；faulthandler诊断38.968秒退出0，10/20/30秒采样位于页面/物料构建，无模态等待证据，但不等同失败运行栈或根因证明。原完整失败、两次隔离、定时栈和诊断命令均保留。不要继续盲目全量重跑、增加阈值、削弱断言或在未决门禁下push/触发CI。

7张当前燃料Qt图（含DIRECT未参与参数展开1680/1180）已由astra局部视觉PASS，7源哈希匹配；page bb1208c2a829e3715423440d0bdfe0da7124fe3e4e9fbac37fb04ebad421612e。真实代理功能专项1/1通过32.511秒，完整套件中业务/几何/草稿/记录相关用例通过；视觉不能代替总体验收。旧53a源会话独立13/13、151主回归/8行定位补丁和42图只背书旧源，不重标新增量。

Owner已授权后续稳定批次PR、必要CI与当前head实包，尚未执行，需先处理当前门禁或取得具体放行决定。接续受控决定：A继续专项定位完整执行后的时间问题；B明确允许以本地仍有60秒超时为已知限制，推当前head做一次既有CI比较，不调整费用/工作流。当前停止发布，未合并；原生CU/鼠标/IME/DPI/Office/企业样例未执行。标准库提案不在本PR范围。

证据入口：docs/ui/whole-page-review/integration/README.md、fuel-capture/review.html。三份当前治理文档以本轮结果为准。跨源聊天状态发送曾被自动审批拒绝，不能自行重试绕过；最终回执如需发送，应取得具体授权。

平台 / Contract预检查：起始业务仓53a3ae83256aeb6ee8b95f426fb6d7297493b65c，实际origin为adgo07/GHGTOOL；当轮fetch核main为092604639cd5b2b61fef1523f87fcd711d8aefea且为祖先，沿用codex/ui-business-layout。锁定中央ee5feb0cc34dbd99790500fadd0c4c932e202a20，已核中央origin、锁定Architecture V2.1及当前UI指南v0.2。分层、展示不回流、Presentation State隔离、历史Record不漂移保持，无冲突、无中央修改，不升级Frozen baseline。本任务不涉及中央公共 Contract。相关既有Standard Issue004/016/018、017、020；无新增解释或标准适用范围变化。
