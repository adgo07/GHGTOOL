# PR63 整合回归完成，待当前 head CI

2026-11-11。在已合并 PR64 的 main `d7a053b8354b98ab5ea3ad53618cf7de657a8809` 上整合 PR63 原 head `f4ed05d3195ba5d5edfe4172e00dffbd96a691cf`。独立分支 `codex/pr63-integration-review`；用户授权解决冲突、保留 PR64、完成回归及 CI，全部通过后合并。正式最新 head、CI 和最终合并状态以 [PR63](https://github.com/adgo07/GHGTOOL/pull/63) 回执为准；以下历史记录不表示当前未合并 PR64。

## 本次整合与保护

- 解决三份交接文档、核算页及 UIR04 测试冲突。保留 PR64 简洁状态提示，顶部/底部统一“计算并生成记录”，去掉重复操作说明。保留 PR64 首页/记录空态、失败重试、可访问提示气泡与标准库窄窗列宽，相关生产文件相对 main 无差异。
- 按中央最新精简规则缩短目录、电热卡说明；因子补充解释复用可鼠标/键盘打开的 ⓘ。停用影响、热源边界、外部补充声明、输入错误等必要信息直接显示。新表单的“历史来源”误称改为“当前来源”，原值/过滤/确认规则不改。
- 原 PR63 CI 曾超过 40 分钟；本轮本地也复现缩放 60 秒超时。性能测量发现重复条目逐控件重挂载及工序构造反复继承样式的开销：改为整体转移原布局，工序在接入页面前完成构造。保留控件身份、原值、信号、折叠和父子归属；不提高测试时限、不改 CI 配置。
- Application / Core / Standards / Persistence、受控资源/Excel/Word、Frozen lock 和工作流相对 main 无差异。保留每次正式成功追加 Record、致命错误不生成 Record、项目/记录分离和显示修约不回流计算。

## 平台 / Contract 预检查

本任务不涉及中央公共 Contract。业务基线见上，Frozen lock 保持 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。不升级 Frozen、不改变 Calculator/标准解释/支持范围/持久化模型，无 CENTRAL CONTRACT GAP。既有 Standard Issue 015/016/017/020 的防重复计碳、外部补充、热力及材料边界继续保留；本次未改变既有软件解释。

重新读取中央 main 的 GUIDE_INDEX、产品家族规格、UI 指南和验收清单。UI 指南 blob `6b32e91510718c07ab7d9a3cb14985b9095a56a3`；其余分别为 `b2e0ac8089d2ae3776255ca38b01cda243f3500e`、`95859d52ce925e5ed42facdc86933412df9a6708`、`29cd984c29a71c665684ca8d707d59f9771bbf8a`。ACTIVE 规则不作为 Frozen adoption。没有新设通用免责声明/更新时间；必要限制和字段校验属于直接可见例外。

## 本地验证（Windows / Python 3.12.14 / Qt 6.11.2）

命令均从本次工作区使用项目 `.venv` Python 执行；Qt 回归设置 `QT_QPA_PLATFORM=offscreen`。各批含重叠，不累加为唯一用例数。完整发现 1156 项、导入错误 0；本轮本地未重跑全量，当前 head 全量由 required CI 执行，不挪用历史 1150/1139 结果。

| 命令/日志 | 真实结果 |
|---|---|
| `python -m unittest tests.test_accounting_controls tests.test_accounting_compact_activation tests.test_accounting_repeated_entries tests.test_accounting_entry_layout tests.test_accounting_source_directory tests.test_pr59_compatibility_navigation tests.test_compact_choices tests.test_uir04_finalization tests.test_ui_copy_presentation tests.test_standard_library_pilot -v`；regression.log | 首轮 61 项，59 通过/2 失败，542.031s；失败是本地缺物性依赖及缩放超时，未冒称该轮全通过 |
| `python -m pip install -r requirements-build.txt` | 补齐既定 CoolProp 8.0.0 / NumPy 2.3.3，build hooks 同步锁定 2026.8；不改版本清单 |
| `python -m unittest tests.test_accounting_energy_presentation tests.test_accounting_source_directory.SourceDirectoryTests.test_heat_edit_commit_refreshes_only_existing_readonly_preview tests.test_g06_page.G06PageTests.test_heat_and_exported_power_rows_keep_factors_and_sources_independently tests.test_g06_page.G06PageTests.test_heat_defaults_to_canonical_factor_and_automatic_steam_enthalpy tests.test_b_heat_runtime tests.test_compact_choices -v`；heat-final.log | 25/25，66.023s；关闭缺依赖失败并保护旧值/热力规则 |
| `python -m unittest tests.test_accounting_repeated_entries tests.test_accounting_entry_layout -v`；framing-detached.log | 最终性能修改后 7/7，53.474s；身份/旧汇总/子归属/dirty/错误展开/宽窄布局 |
| `python -m unittest tests.test_uir04_finalization.UIR04FinalizationTests.test_common_windows_scale_factors_keep_controls_visible -v`；scale-detached.log | 最终 1/1，131.000s；三个子进程各自仍限 60s，100%/125%/150%分别42.965/41.370/45.600s，全部退出0。此前首次修复后125%仍超时115.671s，已继续修复而非放宽门槛 |
| `python -m unittest tests.test_accounting_energy_presentation tests.test_accounting_source_directory.SourceDirectoryTests.test_directory_switches_preserve_complete_state_and_real_controls tests.test_accounting_source_directory.SourceDirectoryTests.test_validation_opens_conversion_and_external_disclosures_without_input_changes tests.test_uir04_finalization.UIR04FinalizationTests.test_ui_result_matches_independent_domain_calculation_and_record tests.test_uir04_finalization.UIR04FinalizationTests.test_domain_error_keeps_result_hidden_even_when_result_object_exists tests.test_g06_page.G06PageTests.test_heat_and_exported_power_rows_keep_factors_and_sources_independently tests.test_g06_page.G06PageTests.test_heat_defaults_to_canonical_factor_and_automatic_steam_enthalpy -v`；final-behavior.log | 最终 10/10，66.182s；正式结果/记录与独立Domain一致、致命错误、热力及导航 |
| `python scripts/validate_canonical.py`、`python -m compileall -q apps packages resources scripts tests`、`python -m pip check`、`git diff --check` | 通过：9标准/12来源/102参数/138因子，无依赖冲突及编译/空白错误 |

本地原始日志在工作区 `tmp/pr63-review/`。性能测量 `cProfile` 原方案64.387s（含测量开销），几何断言通过但超过测试期限；其耗时不可与无测量版本当作严格基准比较。正式关闭超时依据是上表同一原测试三档全部通过。

## 原生验收与交付边界

Astra 以独立合成数据从本工作区实际启动原生窗口；精简文案、因子提示鼠标/Space/Escape、燃料/电力/热力/煅烧代表增删折叠、外部补充访问不自动声明、热力实际预览、宽窄切换及 PR64 标准表回归通过。性能修改后重复条目及最终工序/物料重新启动复验，父代理复核原图。[本轮原图及来源](docs/ui/new-accounting-v2/integration-review/README.md)。

这不是正式 Release/全标准 SUPPORTED/EXE/Office/真实企业数据/系统多屏DPI验收，相关原有 OPEN 继续保留。GitHub 当前新 head 尚待推送后检查；仅在全量与 Standalone required checks 均成功、head 未变化时合并，不绕过保护、不付费提高额度。

---

## PR63 原实施记录（历史证据）

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
