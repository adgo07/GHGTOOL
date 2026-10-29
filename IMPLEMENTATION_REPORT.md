# 新建核算第二批实施报告（视觉复核中，2026-10-29）

R7候选断点：698ba17受影响回归R27共40/40通过478.760s，R6综合70+旧项目22抓图均成功、源稳定/回调0；燃料下部与添加按钮已完整显示、灰块清理。自查发现目录旧泛用background:white覆盖集中后的标题蓝底；当前仅把该规则限定面板本身，恢复同一tokens原配色，不恢复逐对象样式重编译。准备新清洁head R7同组新图复验；原R5/R6图不改标。以下旧断点保留历史，最终阶段报告会统一重写。

最新稳定断点：R24天然气宽1440→窄1180→宽1440的完整氧化率控件/换算值/添加按钮及原嵌套布局2/2通过37.773s，状态/Record不变。R26原三档缩放父测试1/1通过171.652s；实际DPR1/1.25/1.5分别55.946/56.274/56.461s，均在原60秒子进程限制内，断言/预算不改。已集中页面局部重复样式、批量迁移原控件、对非wheel事件等价False快速放行，显示/隐藏配对注册与wheel保护保留。R5 astra已逐图92/92复核，原图/source/script哈希一致，仅旧燃料宽转窄HOLD待新图关闭；灰块非阻断亦已在新候选清理。当前准备新清洁候选R6同组图、受影响回归与astra复验，尚未完整回归/新PR/CI/打包。

前序真实失败：R20 1.0超60秒，1项失败67.757s；R21剖析单档几何通过93.055s但不是原60秒门禁通过；集中样式R22仍失败63.095s；布局批处理R25虽59.827s输出PASS但进程未在60秒退出，仍失败62.647s。全部原日志/阶段输出保留，未改标成功。燃料裁切的实测根因是内容649高而viewport滞留539高，修复仅通知自然高度变化，不靠硬编码高度或取景掩盖。

当前修订断点：R5复核发现旧燃料宽转窄内部裁切HOLD；已定位内容649高而viewport仍539高。具体ScrollArea尺寸通知修复及原嵌套边界R24共2/2通过37.773s，form_state/Record不变。R20原三档父测试第一档60秒超时（67.757s）；R21单档剖析93.055s几何通过但不代替60秒门禁，139次重复框架累计26.640s，其中278次局部样式14.421s。集中样式后R22仍超时（63.095s，dynamic57.405/geometry59.469）；现进一步批量迁移布局，原60秒上限/断言不改，R25运行中。原失败和R5全部原件保全。当前新修订未提交，后文4552afa/R5为前一候选历史，不能当最新视觉已过。待性能验证、定向回归稳定后新清洁head重新抓R6并送astra；完整回归/新PR/CI/包仍未运行。

## 平台 / Contract 预检查

业务仓canonical origin已实核为`adgo07/GHGTOOL`；沿用`codex/new-accounting-page-v2`工作树，保留e8776de既有成果，非破坏性合并最新main `224442530fcc61d8224c45e486688b2c27ec9324`。PR60、PR62均已合并，原未合并依赖假设失效。中央Frozen锁`ee5feb0cc34dbd99790500fadd0c4c932e202a20`不变；当前正式中央main `a389ac1de63c4f331f3b04e5e7b7a17ef02ed111`的ACTIVE UI v0.2（2026-10-26视觉默认值）与产品家族规格已读取。相关Architecture V2.1要求Presentation/Application/Domain分层、显示不回流正式计算；Qt控件状态不能成为未来跨平台Workspace Contract。本任务不涉及中央公共 Contract，不需修改中央Frozen；整合缺陷属于LOCAL DEFECT。Carbon p40/HALF_UP为本项目Profile，不是平台默认。

相关Standard Issue015/016/017/020存在，本任务不改变既有软件解释、公式、正式结果、标准范围或SUPPORTED状态。母版、Word、Canonical、Schema、迁移及不可变Record语义保持。不得据本次UI优化宣称正式Windows发布。

## 本批范围与家族兼容

- 八类源由用户明确点击目录启用；已启用再点击仅浏览。程序切换、恢复、错误定位不启用。小屏原生下拉同样区分activated与setCurrentIndex。
- 外部CO₂为第九独立软件补充入口；访问不勾选同边界/同期/未重复计入声明，不并入标准ES/EI/ET。
- 燃料“含碳量数据来源”保留HEAT_CONTENT/DIRECT路径与参数来源维度。电力地区紧邻、精确所选候选值与年份/来源分别显示；保留五表/OTHER/真实零/冲突/无适用阻断，不隐式回退。
- 热力采用Owner批准的“常用外购入口简化，特殊情况可展开，旧值保留”；新行外购/未计燃料默认不覆盖旧未知、内部、输出草稿，不改变Issue015消重。
- 重复父对象/明细有独立标题、父对象名、边界、所属增删及折叠；不克隆原输入。新增定位、实际问题树首次定位与取消过期请求；旧烟气时长/升级、旧FGD不同用量10/2、旧材料汇总100/80继续可读/可编辑且不创建替代物料。
- 当前项目/单元/保存上下文前置，管理渐进展开；报告三小节分组，核算动作统一“核算并生成记录”。未来各标准补充入口仅记既有路线产品意图，不新增规则。

本批相对main仅改7个UI生产文件；17项正式输入/保存/恢复/期间/核算方法AST相同。保护Application/Core/标准/持久化/Excel/资源/模板/Word/工作流/依赖/中央锁及原五页/Shell，保留PR62共享design_tokens、40DIP、窗口几何/高DPI品牌、小屏、控件wheel_guard、核算页show/hide配对过滤器及40分钟CI预算。新增借用项目夹具完整接入只读catalog class生命周期与结束hash校验，逐例可变库/Records/控件仍独立。

## 当前本地验证与失败保全

Python3.12.14、PySide6/Qt6.11.2、Windows Qt offscreen、隔离合成数据库。以下组有重叠，不累计为全量；全部为本地执行，不是GitHub Actions。

| 原始日志后缀 / 命令模块 | 实际结果 |
|---|---|
| main-integration-r15 / controls、entry_layout、repeated_entries、energy_presentation、source_directory、PR59 navigation | `python -B -m unittest <6模块> -v`，37项36通过/1焦点失败，508.654s |
| compact-r16 / compact_activation | 原生popup/Return、程序导航及外部补充，1/1，11.374s |
| conversion-800-r17 / PR59实际折叠换算方法 | 1180×800、1180×850、1680×1000真实问题树点击，1/1，56.900s |
| reentrant-width-r18 / entry_layout、compact_activation、PR59主动启用取消旧焦点 | 3/3，54.539s；原焦点断言保留，新增电力完整标签横向边界与目录互斥 |
| family-integration-r19 / 旧文案、已启用源浏览、compact双视口、40DIP/精度/wheel、无无关全局事件 | 5/5，57.512s；只同步批准文案/已启用夹具，原业务和几何断言全部保留 |
| Canonical / compileall / pip check，4552afa | `python scripts/validate_canonical.py`：9标准/12来源/102参数/138因子；`python -m compileall -q apps packages resources scripts tests`：0；`python -m pip check`：0，无破损依赖 |
| scope-4552afa | 17方法AST及受保护层相对main一致，7个UI文件允许范围内 |

R15焦点诊断发现宽818时导航与compact同时可见，适配同步resize重入后焦点落编辑滚动区；通过重入保护及导航焦点交接修复，未放宽原测试。电力长候选撑宽由下拉最小宽约束修复，完整值/出处仍在原换行标签显示。前序R7～R10布局失败、R11/12/13/14通过及所有中断日志均保全；原控件迁移删除旧QWidgetItem才创建新布局项，失败的通用高度监听已全部移除。详见前序Git断点及最终证据索引，不能把旧局部组改标当前全量。

## 视觉证据及未完成交付

产品源候选`4552afada1c43db5038056b2869e9ad4e1c07bb4`：R5综合70张、完整171项apps/packages/resources工作文件与Git blob SHA全部原始字节一致，Qt回调0、合成Record0；R5旧项目22张、回调0、源hash稳定，`13-shared-result`实际1条合成Record，其余场景为0，不能统称全0。显式外部补充勾选图与最后未勾选状态分列。两档1180×800/1440×1000，包含报告勾选/未勾选/年焦点、三小节、源状态、重复对象及旧值。直接reveal图不是问题树点击证明，实际树点击由R17及旧项目图覆盖。

[代表图集](docs/ui/new-accounting-v2/README.md)原样选23图、3080014字节，[图像/源码清单](docs/ui/new-accounting-v2/capture-manifest.json)绑定源head、原始图和两份summary摘要。完整92图、脚本、日志及所有失败原件在本次私有证据目录保全；不上传用户库或标准全文。R3 legacy真实viewport失败保留；R4综合exit1、仅14图且异常hook未留下确切主异常，截图可见横向裁切，不能凭推断宣称退出原因已证实；R4旧项目22图成功仅为前一候选历史证据。

Owner已直接授权本批及后续迭代发送原astra会话。R5两包均已发送，视觉结论待返回；不得因已发图宣称通过。当前本批完整回归、新required CI、精确候选包及源独立验收尚未完成；未push、未建新PR、不自动合并或发布。后续先关闭视觉HOLD，再冻结源码执行完整回归，通过后稳定批次push/new PR、复用同head必要CI与精确包交源验收。

未执行原生桌面、Office/IME、人工多屏DPI切换、企业样例、干净机。仅Qt offscreen，不使用变通桌面控制。根用户工作簿未动；不把主线CI318或PR60旧包当成本批结果。
