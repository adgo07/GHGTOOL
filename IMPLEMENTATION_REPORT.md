# 新建核算第二批实施报告（视觉与本地完整复验通过）

2026-10-29。产品源a0dabc8ca49e744ef73704a126c2eaae2fc314dc；本报告冻结前本地证据与后续GitHub精确head证据分别记录，不预填CI通过。

## 平台 / Contract预检查

canonical origin实际核对adgo07/GHGTOOL；复用codex/new-accounting-page-v2，非破坏性整合PR60/PR62已合并main224442530fcc61d8224c45e486688b2c27ec9324。中央Frozen锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；按锁读取Architecture V2.1，MUST保持分层、显示不回流计算、Qt状态不成为公共Workspace。已读正式中央main a389ac1de63c4f331f3b04e5e7b7a17ef02ed111的ACTIVE UI v0.2与家族规格。本任务不涉及中央公共 Contract，无需改中央；UI缺陷分类LOCAL DEFECT，Carbon p40/HALF_UP仍为项目Profile。相关Standard Issue015/016/017/020存在，本任务未改变既有软件解释、公式、标准范围或SUPPORTED状态。

## 实现与保护范围

八源用户点击启用、已启用再点击只浏览；程序/恢复/错误导航不启用。外部CO₂第九入口独立，访问不自动声明，不并入ES/EI/ET。燃料改为含碳量数据来源，保留路径与来源维度。电力地区/精确候选值/年份来源分列，保留五表/OTHER/真实0/无适用阻断。热力按Owner批准简化常用外购入口、特殊展开、旧未知/内部/输出保留，Issue015不变。

父子对象标题/归属/增删/折叠、新增及首次错误定位保留原控件、ID、草稿。旧FGD用量10/2、零替代物料的汇总100/80、烟气旧时长/显式升级保持。项目/单元/保存上下文前置，报告三小节分组，核算动作统一核算并生成记录。未来其他标准补充仅记既有路线意图，不加算法。

相对main仅7个UI生产文件；17个正式输入/保存/恢复/期间/核算方法及show/hide两方法AST相同。Application/Core/标准/持久化/Excel/资源/母版/Word/依赖/workflow、原五页/Shell保护不变。保留家族tokens、40DIP、窗口品牌/DPI/小屏、控件wheel_guard、核算页show/hide配对过滤器及40分钟CI预算。新增借用夹具完整接入只读catalog class初始化/结束hash校验，逐例可变库/Record/控件隔离。原测试方法全部保留，新增17项，实际全量数以最终footer为准。

重复样式集中本页面并批量迁移原控件；non-wheel等价False快速放行，wheel路径/配对注册不改。燃料高度修复只通知自身内容自然高度变化，不硬编码高度；实测旧内容649高而viewport滞留539高。目录面板底色只作用自身，保留蓝底；删除旧未使用facility布局的游离重复caption，不换真实selector。

## 本地定向验证

Python3.12.14 / Qt6.11.2 / Windows offscreen / 合成隔离库。以下组重叠不累计，定向测试在稳定提交前工作树执行、随后提交相同源码，不描述成最新Git head或GitHub已执行。命令均为python -B -m unittest 加下列模块/方法及-v；完整原命令/日志由私有证据索引保全。

| 范围 / 日志后缀 | 实际结果 |
|---|---|
| controls、entry_layout、repeated_entries、energy_presentation、source_directory、PR59六模块 / r15 | 37项36通过/1焦点失败，508.654s |
| tests.test_accounting_compact_activation / r16 | 1/1，11.374s |
| PR59实际折叠换算方法 / r17 | 1/1，56.900s，1180×800/1180×850/1680×1000真实树点击 |
| entry_layout、compact_activation、PR59主动启用取消旧焦点方法 / r18 | 3/3，54.539s |
| UIR04状态及Family小屏/双视口/40DIP/wheel/无无关窗口事件 / r19 | 5/5，57.512s |
| tests.test_uir04_finalization.UIR04FinalizationTests.test_common_windows_scale_factors_keep_controls_visible / r20 | 第一档原60秒超时，1失败67.757s；后两档未执行 |
| 同原父测试 / r22 | 1失败63.095s |
| tests.test_accounting_entry_layout / r24 | 2/2，37.773s |
| 同原三档父测试 / r25 | 1失败62.647s；虽59.827s输出PASS，未按时退出，保留失败 |
| 同原三档父测试 / r26 | 1/1，171.652s；实际DPR1/1.25/1.5各55.946/56.274/56.461s，原60秒/断言不改 |
| controls、repeated_entries、energy_presentation、source_directory、PR59、compact及Family三方法 / r27 | 40/40，478.760s |
| tests.test_accounting_entry_layout / r28 | 2/2，34.274s，含caption唯一及原几何/零Record断言 |

R21为python -B -m cProfile scripts/uir04_scale_acceptance.py --scale 1.0 --work-area desktop：单档几何93.055s通过，含剖析开销，不替代60秒门禁。139次框架累计26.640s含278次局部样式14.421s，性能修正在UI层。R15焦点根因为尺寸适配重入，原焦点断言保留。前序布局失败/中断及所有R20/R22/R25原日志保留，不改标成功。

最终源a0dabc8：python scripts/validate_canonical.py为9标准/12来源/102参数/138因子；python -m compileall -q apps packages resources scripts tests、python -m pip check均exit0。17正式方法、两生命周期及受保护层机械核对通过。

## 视觉门禁与后续交付

astra R8视觉门禁通过，可以完整回归：本轮实际查看18张代表图，结合R5全部92张审查及R6燃料复核，已关闭裁切、配色/父子边界、灰块、重复标签，旧项目/换算定位代表场景正常。92/92图片、171/171全页源码、148/148旧项目源码及两脚本hash吻合；hash核验不等于本轮逐张查看。原会话回执已保全。

[25张原样代表图](docs/ui/new-accounting-v2/README.md)共3342938字节，[清单](docs/ui/new-accounting-v2/capture-manifest.json)绑定R8原图及源a0dabc8，含原HOLD的燃料宽/窄两图。完整70+22图：全页Record0；legacy仅13-shared-result为1条合成Record，其余0。显式声明图True与结束False分列。直接reveal图不冒称树点击；真实树点击由PR59/R17及legacy覆盖。R1～R8原件/所有失败保留；早期视觉ZIP370文件38881505字节SHA256=79eaaddd1768f45eeccf0f7bd978c41e5c020a80424859e09794ea392c7922cb仅为历史快照，不冒称含后续全量/CI/制品。

本地 `python -B -m unittest discover -s tests -t . -v` 首轮在 f1b75ab 中断，缺少退出码和汇总。日志末尾热力用例单独复跑 1/1，5.959 秒。第二轮 dd276bb 完整运行 1150 项，4395.666 秒，4 项失败、2 项报错，退出码 1。原始日志和 375 项源码哈希已保全。

复验前修复购热的默认空白占位行误判和 Qt 销毁期事件过滤异常。保留特殊热源未填写时的校验和已填行的转换规则。更新三项既有文案断言，工序新增用例检查来源启用后按钮可见且点击实际追加实例。`python -B -m unittest -v` 定向运行 `tests.test_compact_choices` 和另五个失败用例，10/10，58.930 秒，退出码 0。R8 图册继续对应 a0dabc8 的视觉证据。复验修复没有改动截图中的布局和文字。

第三轮 6036f11 单进程 discover 在末组缩放期间退出，原日志有 1142 个通过标记，缺少整轮退出码及汇总。第四轮使用同一冻结提交，从 `unittest.defaultTestLoader.discover("tests", top_level_dir=".")` 得到完整 1150 项清单，按发现顺序分五段使用独立进程与隔离目录执行。各段 130、150、240、280、350 项，全部通过，退出码均为 0，累计 3238.659 秒，包含三档缩放。每段核对发现清单与同一组 375 个源文件哈希，保留日志、退出码及摘要。

交付断点为推送独立 PR 并取得 required CI 和精确包。GitHub 实际 head、run、job、artifact、日志、ZIP、manifest 和离屏启动回执在 PR 上登记。本批停在送验。

未执行原生桌面、Office/IME、人工DPI/多屏、企业样例、干净机；根用户工作簿不动。视觉门禁不替代完整回归或正式产品验收，不宣布SUPPORTED。
