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
