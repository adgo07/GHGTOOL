# 五个业务页面 UI V2 — 视觉退修稳定断点

当前完成本地局部修复，待astra新源复核、完整回归与独立PR。没有合并、发布或宣布标准正式支持。PR59已由源会话验收合并，本包基于其新main继续，证据不相互冒用。

## 基线与受控范围

实际origin adgo07/GHGTOOL；4230226原断点干净，fetch后main d7159f77ddb103376f5ca6bdd3a9532c101433e3，正常merge仅冲突两份阶段文档，协调后恢复head1520fb9629efdb86a5505abccafa0653b9e8f0ae。原包仅在旧基线6旧blob/10目标符合后受控应用，原包hash及输出保留；不重套、不改预期hash、不整文件覆盖生产源。

只改catalog_pages、pages指定呈现方法、excel_import_components、record_tables的Qt显示，以及一个局部business_page_style模块；开发捕获和相关测试配套。所有未授权方法AST与main相同，8个核算/壳源无差异；Excel原构造与新构造+布局的connect AST多重集合19/19相同。Application/Core/Calculator/持久化/Canonical资源/依赖/workflow零改动。HomePage及其余pages类受protected_tree保护。

## 本轮局部修复

- 原模型文本保留供选择/辅助功能，仅在已有cellWidget覆盖的单元格避免重复绘制；不为隐藏重字清空状态数据。
- 标准编号按最终字体及字重测量，名称按最终列宽换行。三张业务表仅在自身列宽/show/resize及既有刷新调用中重排行高，不加定时器或后台状态。
- 参数搜索的Qt提示高度未含足实际末行绘制空间，额外留白只用于该表；守卫按实际文字换行高度检查，覆盖两尺寸、模式和同宽查询刷新。来源按钮恢复中文，实际展开来源正文补证。
- 记录企业/标准列保留弹性，日期/状态/操作重新分配；状态徽标紧凑，按实际文字测量最小宽度，原文本和数据不改。
- 冻结B.9等表头仅按原有文字测量可读列宽，完整显示kJ/kg，不改合并、表式、报告投影、模板或Word。
- 捕获对内层布局先处理事件再定位；软件补充在现有输入/依据页签，保持业务路由。实际记录正值20.00/软件合计28.62与待填/未形成分别补图，原标准ET截图显示8.62（合成案例、冻结完整值仅作显示修约）。不再生成相同标准详情顶/底重复截图；没有删除旧原件。
- 原主题与业务局部样式的原生QCheckBox离屏对照，指示器SHA完全相同，全局design_tokens与main一致；不顺手改变全局勾形。

## 本地验证（数量重叠，不累计）

Windows/Python3.12.14/Qt6.11.2/offscreen，全部合成输入及隔离库。开发捕获/特定字体运行器只登记本机已有Windows字体，不新增产品字体包。原始日志留build/ui-five-pages-check。

| 命令或范围 | 实际结果 | 身份/边界 |
|---|---|---|
| python -B build/ui-five-pages-check/run_with_windows_fonts.py（最终九模块） | 74/74，178.555s | README原九模块加4个可读性守卫；原断言保留 |
| python -B -m unittest tests.test_rs03_excel_project_workflow tests.test_rs03_excel_entrypoints tests.test_b_external_chain tests.test_rpt02_appendix_b -v | 39/39，166.620s | 实际Excel/项目/失效/Record/冻结Word保护；未操作Office |
| 4项新增可读性专项 | 4/4，17.726s | 包含同宽查询刷新、实际文字高度和完整冻结单位字串 |
| 原70项恢复组 | 70/70，123.275s | 增补4项前，不冒称新完整组 |
| 首次74项 | 73通过/1失败，169.852s | 徽标实际104px小于108px，补足字体测量宽度后修复；原日志保留 |
| 原包protected_tree＋保护源＋connect AST | 全部通过，19/19接线相同 | resumed-scope-proof.json；实际对main，不放宽原允许方法 |
| r7开发捕获 | 58个页面状态＋2对照图，两尺寸，回调异常0 | dirty=true、父head1520+实际29源hash；不是最终干净head送验图 |

R4捕获错误地到summary找补充，R5把横向报告区标题的尾部空白当作必须完全入屏，均保留FAILED原件。修脚本定位既有input/basis及实际绘制文字，不移动数据、不放宽正式字段检查。R6虽完成捕获，目视发现提示高度断言仍不足以发现参数/B.9裁切，故继续局部修复后才得r7；不把R6列为视觉通过。原423断点的早期70/39及缺字r1/中间r2/r3HOLD均保留历史身份，不重标本轮。

## 平台 / Contract预检查

业务入口4230226，恢复head1520fb9，当前main d7159f77ddb103376f5ca6bdd3a9532c101433e3。中央origin再次核对并fetch，适用当前合并c5fc6d4的UIv0.2、产品规格与清单；locked中央ee5feb0cc34dbd99790500fadd0c4c932e202a20的Architecture V2.1保持。适用MUST/MUST NOT：分层，Domain不依赖Qt/SQLite/Windows；显示不回流计算；历史Record只消费冻结快照，不查当前Catalog补算；UI state不作为公共Workspace；不改变来源资格和标准状态。无冲突、偏差、adoption或中央修改。本任务不涉及中央公共 Contract。

相关Standard Issue：有，既有004/016/018、017、020；改变软件解释：否；无新标准问题。整体标准状态仍由独立门禁决定，本UI不宣称SUPPORTED。

## 尚未完成

astra对最终干净源及新图复核、本包完整回归、独立范围PR/CI/精确包和源独立验收未完成。原生桌面/鼠标/系统DPI/IME/Office/企业真实样例未执行；离屏不冒称原生验收。工作包不自行合并或发布，用户参考文件与原包只读。接续先保存稳定代码再重采，不把截图父head、实际源hash与后续证据提交混为一个身份。

## 完整回归异常后的稳定断点

代码652301a的r8：astra只读视觉复验PASS，原60张PNG/29源哈希匹配，五项HOLD关闭；该结论限原截图范围。其后原始完整CLI运行1297.813s，在第340项附近访问冲突0xC0000005退出，无最终测试摘要，不计完整通过。原始日志SHA 1b4d9b0170093feb84020cc119673fef9d554e06562abfa5e9d009517e17ff53，全部源哈希未变。

单一崩溃位置用例1/1通过8.608s；相邻27项未复现访问冲突，但26通过/1失败136.004s：标准列表行高54px低于原提示断言63px。首次仅补最终提示仍失败（27项26通过/1失败177.421s；同源74项通过220.792s），原件保留。诊断显示列宽信号回调在Qt表头布局未完成时测量；局部改用Qt排队连接，在最终宽度下重排并保留原提示最小高度。不加定时器，不改原断言/阈值/业务或受保护源。此修复不宣称已证明访问冲突原因，下一轮完整原始CLI启用PYTHONFAULTHANDLER=1捕获故障栈。

修后实际本地：27/27，164.197s（crash-adjacent-queued-final.log）；74/74，207.860s（visual-targeted-queued-final.log）。这两组数量重叠，不累计。当前须提交稳定源后重新生成两尺寸截图、交astra复验，并完成完整回归；旧r8不直接背书改后源码。原始失败、开发图和日志不覆盖。

软件补充截图的8.62/20.00/28.62仅为冻结完整值的显示修约，不改变Record或正式计算。
