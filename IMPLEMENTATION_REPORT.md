# 家族 UI 统一实施候选

日期：2026-10-28。Owner 本轮统一设计为实施依据；候选完成后停止，等待协调者独立验收，初次不建 PR。

## 平台 / Contract 预检查

- 业务仓origin已实际确认为 `https://github.com/adgo07/GHGTOOL.git`；远端默认分支main，fetch后基线 `6fc5909646b855494abee55cff6fd95f8d18b4be`。原工作区有无关修改，全部保留。
- locked central SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`；读取其Architecture V2.1 Frozen。适用MUST：Presentation与Application/Domain分离；显示不得改变正式计算；历史Record不得漂移；Presentation State不得成为跨平台Workspace。全部保持。
- 本任务不涉及中央公共 Contract 语义修改，不修改platform-lock、baseline、Calculator、Canonical、数据库迁移或标准支持范围；无Frozen冲突，无需改中央Contract。
- 读取已验证中央origin/main的GUIDE_INDEX、现行UI指南v0.2、产品家族规格及轻量验收清单；v0.1按仓规则读取但识别为历史。Owner本轮设计及中央候选 `e1486fb20c1dda33b7344ca860ff8f303c2183ee` 是本轮实施输入，不声称候选已发布。Qt高DPI参考：https://doc.qt.io/qt-6/highdpi.html 。
- Standard Issue相关：否；既有8项台账已读，本任务不改变任何既有软件解释。

## 改动

- `design_tokens.py`为共享字体、输入、按钮、页签、表格样式唯一来源；`business_page_style.py`保留表格换行/表面组件与兼容入口，移除重复控件QSS；新建、标准详情、记录局部覆盖同步清理。输入内容高36+两侧2px边框=最终40；focus只改边框颜色，不跳尺寸。导航局部规则为内容44+两侧1=46。
- 正文最大1440不含外边距；margin按未施加边距的业务可用宽clamp计算。页头提供actions槽；首页设置右上；由首页打开设置保留无侧栏并可回首页，由业务打开设置保留侧栏。
- 窗口首次1280×800客户区目标，非最大化，含系统边框收进当前工作区并居中。以后从现有user.sqlite的独立产品偏好key恢复正常几何/最大化；损坏偏好安全回退，掉屏/工作区变更收回。没有修改项目恢复。
- 已有Logo资源本身与指定3060×759 RGBA原图hash相同，无需制造资产diff；BrandLogo每次按当前DPR从原图缩放，不放大缩略图。统一图标保留中央phase2的24×24/1.7几何；原生QIcon SVG engine读取随包调色SVG，不固定18物理像素。首页装饰图标直接矢量绘制。资源加入setuptools与现有严格打包白名单。
- 表格默认48、最低44，长文动态增高；标准/记录改完整换行，计数在列表底部。导入四区改为模板与说明/文件选择/数据预览与检查/处理结果，真实项目保存与正式核算能力不变。
- 主按钮#116FAE、hover#0D6097，次文字#526A7D；主/次/轻量/危险角色状态统一。下拉/步进框折叠状态滚轮不改业务值。Decimal保持文本与空值，不切换QDoubleSpinBox。
- 标准生命周期、软件支持与配套通则角色未批量替换；保留有依据的“已实现核算”“核算未开放”等现词，不声称正式验收已完成。

## 实际验证

最终本地环境：Python **3.13.3**、PySide6 **6.11.1**、Qt offscreen；不冒充要求的Python3.12或原生桌面/EXE。

| 命令 | 最终结果 |
|---|---|
| `python -m unittest tests.test_g03_shell tests.test_p3_c_records_ui tests.test_uir01_field_semantics -v` | 31通过/0失败，28.944s |
| `python -m unittest tests.test_family_ui -q` | 8通过/0失败，26.084s |
| `python -m unittest tests.test_main_integration_ui.MainIntegrationUiTests.test_repeated_success_appends_and_failed_input_preserves_saved_records -v` | 1通过/0失败，14.071s |
| `python -m compileall -q packages/ui apps/carbon_accounting_desktop scripts/run_family_ui_review.py` | exit0 |
| `python -c "from scripts.build_standalone import _validate_approved_template_inputs; _validate_approved_template_inputs()"` | 资源白名单/原模板hash检查通过 |
| `git diff --check` | exit0 |

新用例覆盖：屏幕工作区含边框约束、首次非最大化与最大化恢复、坏偏好、设置上下文、40/46最终外框、Decimal长文本/空值、键盘焦点几何、滚轮、禁用主按钮、中文长行、Logo原图hash与DPR2、SVG透明与DPR。

初次25项有1项旧1180×720最小尺寸断言失败，按本轮批准尺寸更新。新用例初次6通过/2失败（导航QSS将固定46压至38、QLabel.pixmap按当前屏幕DPR返回180），分别修正导航有效QSS和检查传给Qt的DPR2原图pixmap。后续自定义Python QIconEngine在回收时出现0xc0000374，已移除，改为原生SVG engine并重跑上述31+8通过。旧导入区标题/栅格pixmap断言按已批准UI改动同步，不删业务断言。

尝试现有`.venv` Python3.12.14/PySide6 6.11.2，8项均在创建临时目录时初始化错误；其进程对临时目录及本worktree文件写入被拒。没有调整系统ACL。生产main离屏检查使用3.13时中文翻译资源版本校验降级并等待提示，已终止；未把QA脚本可启动算成生产main通过。上述环境限制交协调者用真实桌面支持环境验证。

离屏四图在`build/family-ui-views-native-svg/`（首页/标准库/新建/记录详情）；DPR2抽查在`build/family-ui-views-dpr2/`，1280×800 DIP输出2560×1600像素。只作参考；初期缺中文字体的调试图不作为证据。CI、全量业务回归、EXE构建/启动、真实多屏热插拔与桌面验收均未执行。

## 协调者串行桌面验收入口

当前执行环境worktree：`C:/Users/WANGWEI/.codex/worktrees/ghg-family-ui/GHGTOOL`；此绝对路径仅为本次环境记录，不是仓库身份。

先进入该目录。两个入口都移除可能残留的`QT_QPA_PLATFORM`、`QT_SCALE_FACTOR`，使用支持的本机Python3.12；本次可用可执行文件为 `G:/Python Project/GHGTOOL/.venv/Scripts/python.exe`（若该环境仍被拒写，请由协调者使用其已验证桌面运行环境，不更改系统权限）。

```powershell
Set-Location 'C:/Users/WANGWEI/.codex/worktrees/ghg-family-ui/GHGTOOL'
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
Remove-Item Env:QT_SCALE_FACTOR -ErrorAction SilentlyContinue
# QA：明确的隔离目录，自动构建catalog，含一条synthetic G07示例记录。
& 'G:/Python Project/GHGTOOL/.venv/Scripts/python.exe' scripts/run_family_ui_review.py --data-dir "$env:TEMP/ghg-family-ui-qa-20261028"
```

QA入口不等同生产main()全启动，导入测试夹具时恢复原QPA环境。四页步骤：首页→标准库→新建核算→核算记录打开“G07示例企业”。额外抽查：首页右上设置返回首页，业务侧栏设置保持侧栏；Tab焦点、项目展开/收起、输入小数、列表长中文、DPR Logo、无选择/无文件/取消态。

```powershell
# 生产入口：build/databases/catalog.sqlite已由本轮构建；不依赖测试夹具。
$env:LOCALAPPDATA = "$env:TEMP/ghg-family-ui-production-20261028"
& 'G:/Python Project/GHGTOOL/.venv/Scripts/python.exe' -m apps.carbon_accounting_desktop
```

生产入口应检查首次首页、1280×800/工作区限制、关后恢复及最大化恢复；不要使用真实用户数据目录。真实桌面结果由协调者补充，不由离屏结果代替。

候选本地提交后停止；等待明确验收意见，再按指令创建并attach PR；不自动合并。


## Python 3.12 定向补验（2026-10-28）

按协调者要求，仅补跑 `tests.test_family_ui`，被测产品head为 `7bc2ff238faf45ab3b4652fdea767a2e2f4d8b68`。本地实际环境：Python **3.12.14** / PySide6 **6.11.2** / Qt offscreen。命令以 `require_escalated` 执行，TEMP/TMP指向本轮单独可写目录，未改ACL、真实业务数据或测试范围。

```powershell
$testTempRoot = 'G:/Python Project/GHGTOOL/.accept-tmp/family-ui-python312-20261028'
New-Item -ItemType Directory -Path $testTempRoot -Force | Out-Null
$env:TEMP = $testTempRoot
$env:TMP = $testTempRoot
$env:QT_QPA_PLATFORM = 'offscreen'
$env:PYTHONDONTWRITEBYTECODE = '1'
& 'G:/Python Project/GHGTOOL/.venv/Scripts/python.exe' -u -m unittest tests.test_family_ui -v
```

结果：**8通过 / 0失败 / 0错误，52.857s，exit0**。坏JSON偏好用例的预期回退日志已出现，对应用例通过。此前默认临时目录的8项初始化错误仍作为历史尝试保留；该限制已通过本轮隔离TEMP/TMP解决，不再是这8项Python3.12测试的阻塞。

本次仅更新报告与状态，没有产品代码变化；不将这8项结果扩大为31项既有UI、记录保护、生产main、真实桌面、EXE或CI的Python3.12通过。继续等待根协调者最终验收，未创建PR。


## 根协调者源码有限范围验收（2026-10-28）

根协调者明确对head `768a667de878ce680a29b627a14de728a8171063` 给出本轮源码UI有限范围验收通过，并授权push、创建并attach PR，不合并。其已复核核心diff、最终四页离屏图、执行者Python3.13定向40项、根独立8项及执行者Python3.12新增8项通过；根独立结果来自协调者回执，不冒充本会话执行。

桌面CU接口两次读取挂起，未完成GHG真实交互；生产main全启动、跨屏、EXE仍未验。不将此次源码验收写成全量桌面或发行验收。此文档提交仅同步验收状态，不更改已验产品代码；此前待验收描述作为历史记录保留。


## PR62 / CI313 缩放探针修复（2026-10-28）

GitHub Actions证据：[run40668806658](https://github.com/adgo07/GHGTOOL/actions/runs/40668806658)，job122750042242，head `0bb10a7362052db165a62c043cc39ee0e443f785`。失败发生在`uir04_scale_acceptance.py --scale 1.25/1.5`，其余业务manual五场景PASS；全量unittest步骤尚未执行，Standalone Audit因needs跳过，不称全量测试失败列表已取得或Standalone已审计。

根因：Qt offscreen默认800×800物理屏，缩放后工作区只有640/533 DIP。新增窗口收回规则使旧探针要求的1366×768客户区被正确缩小，导航进一步挤压编辑区至106/53 DIP。根据[Qt6.11 offscreen源码配置接口](https://github.com/qt/qtbase/blob/6.11/src/plugins/platforms/offscreen/qoffscreenintegration.cpp)，探针显式配置2560×1600物理虚拟屏，并验证真实客户区1366×768及外框在配置工作区内。Windows平台参数的盘符冒号会被拆分，初始化时使用配置文件的相对路径并恢复cwd。测量前显式展示目标分区，避免读取隐藏页面旧几何。没有删除/降低原行数、最小尺寸、边界、重叠或删除断言，没有修改workflow/required checks。

小工作区实际图片还暴露了字段裁剪，不能仅靠row host宽度断言宣布可用：排放源目录在窄宽下使用紧凑下拉，编辑区以420 DIP最小内容宽度及可达的局部滚动承载；普通宽度保留原目录。紧凑导航纯展示，排除于form_state和dirty tracking，原排放源状态与输入不变。small探针补充活动量输入垂直可见、左右端分别可达及编辑区右端可达断言；宽输入不要求在极窄视口同时显示两端。生产窗口工作区约束保持。

本地实际Python3.12.14/PySide6 6.11.2，offscreen，沿用隔离TEMP/TMP：

- `python scripts/uir04_scale_acceptance.py --scale 1.25`：PASS，client1366×768。
- `python scripts/uir04_scale_acceptance.py --scale 1.5`：PASS，client1366×768。
- `python -m unittest tests.test_family_ui -q`：9通过/0失败，52.796s（紧凑目录阶段）。
- 初次目录组+新状态测试：14通过/1失败，152.617s，失败为既有source_adapters响应式列数集合仅{2}；局部滚动完成后保持原“两种列数”断言重新通过，未改该测试。
- 最终`python -m unittest tests.test_accounting_source_directory.SourceDirectoryTests.test_fuel_source_adapters_stay_hidden_while_real_choices_change_original_data tests.test_family_ui.FamilyUiTests.test_compact_directory_navigation_preserves_business_source_state -q`：2通过/0失败，25.229s。新增状态测试同时确认完整form_state及dirty标记不变。
- 最终`python scripts/uir04_scale_acceptance.py --scale 1.5 --work-area small --screenshot <本轮可写目录>/ci313-small-fuel-final.png`：PASS，client531×531；原几何断言及实际控件滚动可达断言全部执行。中间截图写本worktree被3.12进程拒绝，另一次新加“宽文本框需同时完整容纳于窄视口”的不适用检查失败；分别改用已验证可写G盘隔离目录和真实的左右端分别可达检查，不改原业务断言。最终只有这一张作为本修复的视觉参考，非真实桌面证据。
- compileall与`git diff --check`：exit0；未重复14项、全量回归或扩展其他业务。

最终图片当前环境位置：`G:/Python Project/GHGTOOL/.accept-tmp/family-ui-python312-20261028/ci313-small-fuel-final.png`。这是本次临时证据位置，不是仓库固定路径。源代码修复不涉及公共Contract、算法、标准支持、正式记录/项目保存或审计规则。更新同一PR后等待新head实际CI；此前源码有限验收不外推本轮真实桌面或EXE通过。


## CI314超时定位与事件过滤器生命周期修复（2026-10-28）

GitHub Actions [run40672239566](https://github.com/adgo07/GHGTOOL/actions/runs/40672239566)，job122761662456，head `8d0ed1f815986d2bece4ae125d142a2c0c0cf8e1`。check annotations明确为“The job has exceeded the maximum execution time of 40m0s”，不是手动取消。前置manual及125%/150%探针均通过，全量unittest运行中超时；Standalone Audit依赖该job因而skipped，没有Standalone通过证据。

比较[基线CI311](https://github.com/adgo07/GHGTOOL/actions/runs/40302567376)：main `6fc5909646b855494abee55cff6fd95f8d18b4be`的同一workflow全量1122项用时2107.461s并成功。CI314全量从10:30:31 UTC开始，到40分钟job预算取消时只取得176条测试记录。相邻日志时间差显示后段FGD场景从基线约7～18秒增长到60～158秒，且随GUI窗口数量增长；这些是日志间隔估计，不冒充精确测试计时。不能按既有预算不足处理。

本地同进程隔离窗口探针定位到本轮引入的`CarbonAccountingMainWindow`应用级滚轮过滤器：创建即安装，隐藏/关闭后仍留在QApplication。已有测试会显式`deleteLater()`后调用`processEvents()`；DeferredDelete未派发时旧QObject还存在，后续所有窗口事件继续经过旧过滤器。旧版前6轮每轮过滤回调数为314371、628742、943112、1257484、1571851、1886228，呈线性增长；已取得证据后只停止本轮该探针的两级Python进程，没有终止其他会话进程。

修复仅在窗口显示时安装、隐藏时移除，取消关闭时仍保持保护，重新显示时恢复。初始化隐藏窗口不再监听全局事件；项目关闭确认及几何保存流程不变。不修改业务算法、测试夹具销毁方式、测试范围、原断言或CI40分钟配置，不盲目重跑旧head。

本地Python3.12.14 / PySide6 6.11.2、offscreen、既有隔离TEMP/TMP验证：

- 同负载新进程5轮窗口创建/关闭探针：每轮回调311871、311869、311871、311869、311870；每轮14.879、14.729、13.319、16.039、15.759秒。保留了同样未派发DeferredDelete的条件，回调不再随已关闭窗口累积。这是带回调计数的定向探针，不外推CI全量用时。
- `python -m unittest tests.test_family_ui.FamilyUiTests.test_closed_window_stops_observing_global_events_and_reopen_restores_it tests.test_family_ui.FamilyUiTests.test_shared_input_outer_size_precision_focus_and_wheel -v`：**2通过/0失败，26.572s**。新增行为测试实际向外部widget发送事件，确认显示/重开接收、隐藏/关闭不再接收；原Decimal、空值、最终40高度、焦点与滚轮保护断言保持。
- 用unittest.TestSuite在同进程连续运行原`tests.test_b_fgd_chain.FGDChainTests.test_explicit_source_on_unfinished_row_is_not_hidden`三次，业务断言不变：**3通过/0失败，60.514s**，独立计时19.782、25.738、14.981秒；未出现随轮数持续增长。
- `compileall`（修改的app与测试）及`git diff --check`：exit0。未重复全量或额外页面/DPI矩阵。GitHub新head全量/Standalone仍需实际完成，不能以本地定向证据替代。

本修复提交并推送同一PR62，等待根复核与新CI；真实桌面、生产main全启动、跨屏及EXE未验边界保持。


## CI315剩余失败与测试桌面条件收口（2026-10-28）

[CI315 run40696760849](https://github.com/adgo07/GHGTOOL/actions/runs/40696760849)，job122845485486，head `3ef90556205558fdeb3349f4775ab44b16df5d09`，仍由40m预算取消。完整日志2569行，1113条顶层测试记录，最后在`test_nonfossil_electricity_needs_no_proof_to_complete`执行中被中断；不是测试结束后的退出挂起，也没有完整汇总。对比CI314仅176条、基线CI311全量1122项2107.461s：前次过滤器生命周期修复有效，但不能当作最终问题解决。CI315日志本地在`build/ci315-job.log`；GitHub连接器连续传输失败后才使用现有Git认证只向GitHub API读取，未输出凭据。

取消时栈中仍有多次MainWindow全局filter（测试保留的可见窗口也会监听别的窗口事件），故最终取消该类应用级监听，改为实际QComboBox/QAbstractSpinBox上的本地guard；弹出选择/日历仍可正常处理滚轮。guard归属控件且幂等安装，不持有窗口、不访问业务值；动态核算字段保留原页面滚轮实现。

日志中8个明确失败入口已单独复现：来源目录单滚动的旧限定、记录长文本三行上限、两个标准表54行高旧断言、两个20行动态布局入口、两个真实错误定位入口（含宽窄子场景）。后四项实测窗口都被默认800物理屏收回至796宽，原本1180/1680桌面测试意外转入紧凑内层滚动；不是放宽业务校验。测试包仅在`QT_QPA_PLATFORM`恰为裸`offscreen`时配置2560×1600虚拟工作区，显式small/scale配置或真实平台不覆盖。新增JSON仅为测试fixture，不打包运行，不改变产品窗口约束。动态行增删、范围收敛、真实错误项点击/焦点、旧值/状态/无Record断言均保留。

按Owner当前视觉设计同步三处旧断言：54改48；固定三行高度上限改Qt完整换行hint+8有限留白（保留完整身份/徽标/来源/数量断言）；完全禁止局部滚动改为只允许唯一具名编辑视口并检查其滚动策略（保留导航不改变form_state与dirty）。没有删除测试或降低正式业务断言。另外修复实际960窄窗口定位：先将目标滚入内层编辑视口，再定位外层正文，验证实际第四物料字段在两个viewport完整可见且有焦点。

本地Python3.12.14/PySide6 6.11.2、offscreen、既有隔离TEMP/TMP：

- CI315八入口定向unittest：8通过/0失败，188.909s，命令及完整结果在`build/ci315-targeted-final.log`；涉及SourceDirectory、BusinessPageVisual、P3ABStandards、StandardLibraryPilot、UAT02Geometry、UAT02Usability、PR59CompatibilityNavigation的上述已知失败单项，不扩大其他测试。
- `tests.test_family_ui.FamilyUiTests.test_windows_never_observe_unrelated_global_events` + `test_shared_input_outer_size_precision_focus_and_wheel`：2通过/0失败，79.985s。实际外部事件确认显示/隐藏/重开/关闭均没有窗口级全局监听；输入精度/空值/焦点/滚轮保护仍通过。
- `tests.test_family_ui.FamilyUiTests.test_compact_target_navigation_reveals_inner_and_outer_viewports`：1通过/0失败，15.455s，实际960窗口/第四物料字段，不用合成不可见目标放宽检查。
- compileall及`git diff --check`：exit0。当前没有修改workflow40分钟预算，未盲目重跑旧head、未重新截图矩阵或跑无关全量。上述分段验证不代替新head全量/Standalone CI；实际是否仍需合理预算调整须由新运行证据判断。
