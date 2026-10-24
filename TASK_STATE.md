# 五个业务页面 UI V2 — 恢复实施 / 视觉 HOLD

2026-10-25恢复核查：实际origin为adgo07/GHGTOOL，已fetch，默认main，原分支干净且HEAD确为4230226d9969bdba6ba44811349bffc5add9fdba；最新origin/main为PR59合并提交d7159f77ddb103376f5ca6bdd3a9532c101433e3。五页与main的生产文件无重叠，正常merge只冲突当前两份阶段文档；按本阶段语义协调文档，保留原断点历史，不整文件覆盖生产源码、不重套原包或修改预期hash。PR59限定验收/CI306/精确6026包证据仍属PR59，不背书五页。中央origin再次核实并fetch，当前UI指南v0.2仍适用；locked ee5feb0不变。五页HOLD具体意见已从astra原会话重新读取，待逐项修正。


状态：恢复实施 / VISUAL HOLD。PR59 已经源会话独立验收并合并；复用 codex/ui-five-business-pages-v2 的4230226安全断点，保全既有源码和原始证据，五页仍未推送或建立PR。

实际 fetch 后基线 origin/main@092604639cd5b2b61fef1523f87fcd711d8aefea。原包只检查6旧文件哈希全部匹配，10目标与受保护AST/信号接线预检通过，再按原工具应用；未改预期hash、未叠加旧标准库包。当前所有源码、开发脚本、原始日志和截图均保留。

最新相关真实Qt组70/70通过，37.694s（原README九模块＋6补充守卫，在同一进程登记本机既有Windows字体；原断言未减）。真实Excel/项目/失效及冻结Record/Word保护39/39通过68.485s，执行于后续冻结ET标签/参数详情最小高度调整前；业务实现字节未变，不将它冒称修后全量。Canonical 9/12/102/138、compileall、pip check和diff检查通过。尚未运行本包完整回归、CI或独立构建。

r3真实Qt60图在build/ui-five-pages-after-r3/，含两尺寸、源码SHA、字体/DPR/Qt/图片hash，回调异常0。astra核28源/60图hash全部匹配，但视觉HOLD：标准列表徽标叠字和编号/名称省略；参数长行裁切、来源展开入口/正文不足；记录列表裁切；B.9表头单位截断；需补补充量区域和核对复选框勾形。尚未实施这些后续修正。r1缺字图明确INVALID；r2仅中间稿，均不作最终视觉证据。

本次已吸收PR59合并后的最新main；首页/全局导航/shell/新建核算等保护源保持与新main一致，五页相对新main不修改这些文件。业务、Catalog、Schema、模板、Word业务和依赖不改。详细边界、已执行项及剩余问题见IMPLEMENTATION_REPORT.md。

平台 / Contract预检查：locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，已核中央origin并读取其当前已合并UI指南v0.2/产品家族规格/验收清单及locked Architecture V2.1。保持分层、展示不回流计算、历史Record不重算、UI state非公共Workspace；无冲突、adoption或中央修改。本任务不涉及中央公共 Contract。相关既有Issue004/016/018、017、020，不改变软件解释，无新标准问题。原生桌面/Office/IME未授权；本包不合并、不发布。
