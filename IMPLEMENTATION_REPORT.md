# 中央 UI 指南呈现收口实施报告

2026-11-10。基于已合并 PR62 / `origin/main@224442530fcc61d8224c45e486688b2c27ec9324`，分支 `codex/ui-guideline-closeout`。本轮完成有限呈现增量；父代理已完成代码与范围内 Qt 回归独立检查，原生桌面仍 OPEN。未 push、未创建PR、未合并、未发布；无 Goal。

## 平台 / Contract 预检查

实际核验工作树、origin、fetch、默认分支main、branch、head、status；origin 为 `https://github.com/adgo07/GHGTOOL.git`。从最新main建立独立worktree，原checkout未跟踪资料和其他任务工作区均未修改。基线业务仓SHA见上；最终交付head由提交回执锁定，产品/测试源文件已由[manifest](docs/ui/guideline-closeout/capture-manifest.json)绑定。

锁定中央 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 保持不变。**本任务不涉及中央公共 Contract。** Architecture V2.1、Numeric v1/Profile v1不升级；相关MUST/MUST NOT为维持分层、显示修约不得回流、Decimal输入不得损失、正式Record与项目存储分离、历史快照不重算。本轮仅Presentation，未改Application/Domain/Calculator、Canonical、DB schema/迁移、参数/来源绑定、受控Excel母版或Word逻辑，无Contract冲突、无中央修改或adoption。

已读取本仓AGENTS、唯一路线、TASK_STATE/HANDOFF、STANDARD_ISSUES_REGISTER及platform-lock。Standard Issue：无本轮新增/需改变的问题；不改变既有软件解释、正式结果或支持范围。通则详情描述的是软件配套使用方式，不写成标准原文。

中央当前已合并ACTIVE指南已读取（均2026-11-10适用，不是Frozen）：GUIDE_INDEX blob `b2e0ac8089d2ae3776255ca38b01cda243f3500e`；家族规格 `95859d52ce925e5ed42facdc86933412df9a6708`；指南v0.2 `6b32e91510718c07ab7d9a3cb14985b9095a56a3`；验收清单 `29cd984c29a71c665684ca8d707d59f9771bbf8a`。

## 批准范围逐项对照

| 范围 | 结果与保留原因 |
|---|---|
| 公共呈现 | 页头说明变成可选；原动作区保留。新增本仓InfoTip：默认收起、中文可访问名称、40DIP外框/2DIP焦点、鼠标/键盘打开、Escape或按钮关闭并恢复焦点。未新增跨仓运行时包。 |
| 首页 | 删除空态重复段落；一句空态+新建核算，读取失败原因直接可见+重试；复用已有导航/刷新。保留五入口说明中的任务/能力范围、独立设置、Logo与成熟窗口行为。 |
| 标准列表 | 删重复页头和常驻操作复述，使用就近ⓘ；保持五列、单标准状态筛选、编号/名称入口。实施且registry匹配仍为原条件，仅显示“已实现，待验收”；其他行业显示“未开放”。第五列加宽160容纳完整文案，不改枚举/门禁。 |
| 通则角色 | 名称/详情写“配套通则”，支持列“—”；可访问ⓘ说明作为行业核算配套规则、不单独发起核算、未单独给支持等级。不新增第四等级；其正式独立支持等级映射保持OPEN。 |
| 标准详情 | 原单页三连续分区与官方原文动作不变；保留“软件实现说明，不是标准原文要求”限定。通则三行说明改为真实配套用途，避免称其为未建立的行业算法。 |
| 记录 | 删重复页头，导出动作简为“导出报告（Word）”。首次无记录/筛选无结果/读取失败分别配新建/清除筛选/重试；读取失败显示“记录数量暂不可用”，不假称0条。全量搜索可达、独立详情严格两页签、无重新开展/审计入口均保留。冻结值/完整值/旧记录依据/Word数据逻辑不改。 |
| 参数与因子库 | 页头保留必要“只读”；删模式复述，说明进就近ⓘ。已有数值/单位/适用条件与来源展开保持，未新增编辑能力。 |
| 设置 | 删复述页头；导出说明与软件技术信息收进标题同行ⓘ；默认仅真实产品/平台与导出位置，未造空备份/高级功能；路径/读取失败/保存后果保持。 |
| 新建核算 | 仅3处文字：顶部“检查并计算”改为“计算并生成记录”，底部两处初始/恢复提示改“计算通过后自动新增正式记录”。同一回调、校验/声明/来源/默认输入/保存逻辑不变。原复杂表单、灰底、原生SpinBox等局部样式保留，未假称全部统一。 |
| 导入 | 仅删除与处理区重复的页头流程描述；四区“模板与说明/文件选择/数据预览与检查/处理结果”及预览→保存项目→主动核算→新增记录直接说明保持。上下文、边界、关联失败提示均保留，不为精简隐藏正确输入要求。 |
| 局部样式/页脚 | InfoTip纳入既有design_tokens；标准详情名称22→20与共享基准对齐。其余成熟窗口/Logo/按钮/表格继承PR62；复杂业务局部样式不全面重构。无新增免责声明或通用更新时间，不为凑页脚增加信息；业务日期仍在原对象。 |

PR63已核实OPEN/未合并，head `f4ed05d3195ba5d5edfe4172e00dffbd96a691cf`，基于同一main；未合并、未修改该分支。产品重叠仅 `packages/ui/carbon_material_page.py` 上述3处文案，不接管其布局/来源/输入重构；后续整合逐处保留这3项呈现目标，不能自动覆盖PR63。新增测试不修改PR63的测试文件；HANDOFF/TASK_STATE/报告属于届时需人工整理的交接文档。

## 本地验证与失败记录

Windows源码，Python3.12.14/PySide6 6.11.2，导入已核对来自本轮worktree。作者使用 `QT_QPA_PLATFORM=offscreen`，TEMP/TMP改为工作树内 `tmp/ui-tests`，`python -B -u -m unittest ... -v`。以下分批存在重叠，**不得直接累加为唯一用例数**；测试名用于复现。

| 实际命令（均unittest -v） | 结果 |
|---|---|
| `tests.test_p3_ab_standards tests.test_p3_c_records_ui tests.test_export_directory_ui` | 24例23通过/1失败，20.419s；唯一失败为旧固定列宽124断言，产品已按新文案扩为160。更新该断言后在下一批精确复验通过，其余原23例均通过。 |
| `tests.test_ui_copy_presentation tests.test_family_ui tests.test_g03_shell` | 28/28通过，52.485s，第一稳定批次。覆盖共享40DIP/禁用/焦点、Decimal长文本/空白、滚轮、布局导航与导入四区等。 |
| `tests.test_ui_copy_presentation tests.test_p3_ab_standards.P3ABStandardsTests.test_search_controls_headers_and_support_are_limited_to_the_standard_catalog tests.test_g03_shell.G03ShellTest.test_home_is_a_safe_empty_workbench tests.test_rs03_excel_project_workflow tests.test_accounting_projects_ui.AccountingProjectUiTests.test_single_calculation_action_shows_domain_problem_then_creates_record tests.test_accounting_projects_ui.AccountingProjectUiTests.test_changed_input_marks_result_stale_after_switch_save_and_reopen` | 18/18通过，48.403s；包括预览/保存不写Record、正式重复核算追加记录、冻结导入证据、关联保存失败、上下文编辑失效、结果过期/切换保存恢复。 |
| `tests.test_g04_catalog tests.test_standard_library_pilot` | 22例21通过/1旧列宽断言失败，28.747s；同步pilot中剩余124→160后复验 `tests.test_standard_library_pilot` **6/6通过，1.301s**，原有效目录/来源/门禁断言保留。 |
| 最终 `tests.test_ui_copy_presentation` | 5/5通过，0.083s；新增首页真实点击新建及读取失败→重试恢复，保留此前ⓘ/记录三态回归。 |
| 父代理独立 `tests.test_ui_copy_presentation tests.test_business_pages_visual` | 25/25通过，15.471s（较早稳定批，copy当时4例）。 |
| 父代理最终独立 `tests.test_ui_copy_presentation tests.test_export_directory_ui` | 9/9通过，0.561s（copy已5例）。两组相互重叠，不称34唯一用例。 |
| `git diff --check`、当前修改Python文件语法编译 | 通过，无改业务层。 |

初始默认受限TEMP导致既有家族/壳夹具PermissionError，另一个无输出会话中止；改隔离TEMP后正常。父代理初次默认通道无输出会话亦中止，改可用执行方式后得到上列独立证据。未计中止/未完成运行通过。

新增测试两次夹具问题如实保留：首次4例3通过/1错误，mock不存在的list_summaries，改为实际list_all后4例通过；新增首页测试首次10例9通过/1错误，遗漏HomePage显式刷新前置，补其生产壳已有调用后最终5/5与父代理9/9通过。无修改产品来迎合夹具。两处既有固定列宽断言失败与抓图首次调用不存在helper失败均已修复并重跑；未重复全量取绿。

## 视觉证据、OPEN与交付

[8张图、复现脚本与manifest](docs/ui/guideline-closeout/README.md)，均1280×800 / DPR1 **Qt离屏源码**，作者实际逐张看图；父代理已独立查看代表图。设置路径使用虚构值。不能据此宣布原生桌面或EXE通过。

指定GPT-6 Astra medium代理完整读computer-use及必要文档，三次sky调用（含reset）都提示helper已有active request；未获得窗口、输入或截图，按技能停止。启动PID11652后续精确查询未发现，无其他进程被终止。原生鼠标/键盘桌面、IME、多屏/人工DPI、Office/干净机/企业真实样例、本轮打包EXE及全量回归继续OPEN/未执行；范围不要求本轮补齐这些门禁。

既有目录32151.5行实施日期2026-10-01仍显示“即将实施”，需按权威目录证据另核验，未按系统时钟改源数据。本轮只核验支持文字与角色映射，不宣称全标准生命周期准确性通过。通则独立支持等级映射OPEN。

本轮未执行GitHub Actions，未复用PR63 CI320超时/无包结果，不修改40分钟预算/required checks或付费配置。尚无精确head构建包。原生及正式发布验收不由本地呈现回归替代，不宣布标准SUPPORTED、不进入RS04/RS05/第二标准。代码/范围内本地Qt回归可供独立验收，父代理后续统一决定PR与CI。
