# GHG-UI-P3-DF 验收记录

本包仅参数与因子库（D）和新建核算视觉收敛（F），不是新的产品路线。按 D实现→D专项测试→F实现→F专项/联合回归顺序交付一个PR，不自行合并、不启动C/E。

## 前置与平台 / Contract 预检查

- 仓库origin核实为 https://github.com/adgo07/GHGTOOL.git，默认分支main；执行时fetch后base为 `a51afbcf684e3845369977e42adc938866726d0b`，独立分支 `codex/ghg-ui-p3-df`。
- GitHub认证API确认PR37 merged=true（2026-10-09T06:56:57Z），PR38 merged=true（2026-10-09T14:17:01Z）；PR38 merge commit就是本包base。未复用AB分支，不重复AB改造。
- 开工tracked工作树干净；既存未跟踪Office参考文件、其他工作树、.codex-run和旧临时参考目录保护，不提交、不清理。
- Locked central `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变。本任务不涉及中央公共 Contract，不修改Frozen、platform-lock、PLATFORM_BASELINE。相关Architecture V2.1 Frozen要求Presentation/Application/Domain/Infrastructure分层，Qt状态留在Presentation，不增加公共PySide6包或跨仓运行时依赖。
- MUST：来源浏览/全库搜索/只读详情保留；值、单位、条件、来源期间、数据类型和来源定位仍可查；UAT03 V2作为业务基线，八类开关、动态明细、输入精度、来源、参数门禁、计算、项目/单元/历史Record行为不变。
- MUST NOT：修改Application、Domain、Repository、Schema、Migration、Canonical、Catalog、Reference Data、Resolver、计算候选、公式、Numeric、Calculator、Project保存恢复、Record生命周期、报告生成或导出业务；不改AB、C/E和未合并EXB01/RPT02实现。
- Standard Issue：当前台账8项均RESOLVED；本包不改变标准事实或既有软件解释，不增加正式标准支持范围。无新标准疑义；若发现真实业务问题只单独记录。

## 中央指南与并行任务

已核实中央origin并fetch，只读取正式合并 `854b544563260f9e79c73e714c85f6589e0f19b3` 的UI v0.2、家族规格、验收清单、Phase2 INTERACTION_SPEC / VISUAL_SPEC / PYSIDE6_REFERENCE。ACTIVE / EVOLVING不作为Frozen adoption；旧原型截图/HTML及其历史产品基线不替代当前源码。

EXB01已在独立 `codex/exb01-appendix-b-ingress` 工作树实施（相对当前main有33个变更路径，未合并），RPT02独立 `codex/ghg-rpt02` 有37个变更路径，未合并。只核对状态和路径，不取未合并实现。前者UI交集候选为pages.py，后者为record_experience.py，本DF均不修改；catalog_pages.py/carbon_material_page.py未见其改动，但F仍避开报告按钮及组件。四份共享治理文件需后续按真实工作包状态整合，不覆盖其他工作树的修改。

本仓HANDOFF/路线仍称AB当前，是已合并阶段的文档滞后；用户已明确授权DF，属于本地阶段记录更新，不是Frozen冲突。无实质Contract冲突，无需中央变更；不升级正式支持状态或启动RS04/05。

## 自动化、离屏与原生证据边界

本地测试、GitHub Actions、Qt离屏截图、原生窗口操作分别记录。截图使用隔离临时Catalog和测试项目/Record，正式计算截图仅由明确测试输入调用现有计算路径生成，不读取用户数据、不伪造结果。

原生Windows检查 **OPEN**：2026-10-10通过Computer Use正式入口初始化，node_repl返回 `windows sandbox failed: helper_unknown_error: setup refresh had errors`，未能操作真实窗口。不能把离屏或Qt scale模拟称为100%/125%/150%系统DPI实机通过。独立验收须补两种分辨率的原生鼠标、键盘、滚动和缩放检查。

## 当前实施与验证

D与F实现已完成，按下文记录验证；本地完整回归结果与最终head CI分别记录，不混用证据。不沿用AB旧截图或旧测试结果冒充本包证据。

## D 与 F 的实现及验证

D 稳定断点先通过 `.venv/Scripts/python.exe -m unittest tests.test_g04_catalog tests.test_p3_df_factors -v`：17项、63.953秒、OK，之后才开始 F。截图发现搜索表挤压详情后，限定列宽为可调、详情最小320逻辑像素；再次执行 `tests.test_p3_df_factors -v`：3项、4.364秒、OK。

F 新增 `tests.test_p3_df_accounting -v`：3项、8.262秒、OK。覆盖长标准换行、结果位于依据前、动态行高精度与来源保留，以及计算入口可达。既有定向命令 `python -m unittest tests.test_g06_page tests.test_uat03_page tests.test_uat03_responsive_fields tests.test_uir02_source_cards tests.test_accounting_projects_ui tests.test_project_workspaces tests.test_g07_records -v`：102项、1073.570秒、OK。隔离git archive b8fc4bc执行 `python -m unittest discover -s tests -t . -v`：410项、1759.922秒，409通过/1失败。失败为电力2023详情缺少独立“地区”标签；信息并未丢失但展示兼容破坏，已在a267881恢复原字段。最终head的全量绿色结论以PR Windows CI为准，不把本地首次失败改写为通过。

本地公共检查：

| 命令 | 实际结果 |
|---|---|
| `python scripts/validate_canonical.py` | 9标准、12来源、102参数、138因子，valid |
| `python -m compileall -q apps packages resources scripts tests` | 通过（PYTHONPYCACHEPREFIX指向临时目录） |
| `uv pip check --python .venv/Scripts/python.exe` | 17包，全部兼容 |
| `python scripts/initialize_databases.py --output-dir tmp/p3-df/databases` | 隔离生成catalog/user/records/projects四库 |
| `python scripts/uir04_manual_gui_acceptance.py` | A–E五场景PASS；属于Qt自动化，脚本历史名称不代表本轮人工操作 |
| `python scripts/uir04_scale_acceptance.py --scale 1.25`、`--scale 1.5` | 两组PASS，1366×768控件/动态行无重叠 |

截图命令：对 `(1366,768)`、`(1920,1080)` 分别执行 `python scripts/p3_df_ui_acceptance.py --width W --height H --scale S --output-dir tmp/p3-df/final-evidence`，S为1.0、1.25、1.5。实际6组均PASS，每组65检查/8图，共390检查/48图。证据复制到 `evidence/`；6份JSON包含逻辑/物理尺寸、DPR和LF规范源码SHA256，均已与交付源码核对一致。目录初次直接写入受本机Python目录权限限制，改写临时输出后复制；没有把失败的初次运行计入通过结果。

每组覆盖来源浏览、搜索详情、完整来源追溯、空搜索、空核算、多明细、真实正式结果、分项结果。真实计算夹具只用于验证正式路径与显示一致性，不能代替标准Golden Case。原生系统DPI验收仍OPEN。

已人工查看本轮离屏图中的1366×768/100%详情与空核算、1366×768/150%真实结果、1920×1080/125%来源追溯，检查阅读顺序、长内容与下标字形。其余矩阵由自动断言验证；不冒充逐图原生验收。

## 中央 UI A 类规范对应

| 要求 | 本包落实 |
|---|---|
| 统一品牌与视觉层级 | 复用AB现有tokens，不改Shell、首页、标准库；页面局部样式 |
| 中文、业务语言、技术信息渐进展示 | D参数值/单位/条件优先，完整追溯折叠；F结果优先、依据保留 |
| 真实数据与能力边界 | 不复制原型演示数据，不新增计算能力；值与来源均读现有目录 |
| 清晰状态与可访问操作 | 八类已有状态用边框/文字/底色区分；搜索与追溯支持键盘；只读保持 |
| 长内容与缩放 | 可调列、换行、工具提示、双向滚动；六组离屏证据；实机OPEN |
| 分层与可维护性 | 仅两个Presentation页面；不增加公共包、业务模型或运行时依赖 |

## 未解决项与交付门禁

没有在本包扩展业务修复。窄屏长来源表和八类选择条采用现有滚动方式；没有删除专业信息来缩页。原生实机检查OPEN，须由独立验收补齐。Windows CI结果仅以最终PR head的GitHub Actions为准，不能用本地结果替代；本地全量首次失败及修复、独立构建来源见本记录；最终PR正文记录完整Windows CI链接、最终head及结论。

独立程序本地检查：build_standalone成功（source_commit=b8fc4bc8e2b3e587235f5b1df1641ccc31776b17）；inspect_release PASS（264文件）；verify_release_archive PASS（265可见文件，ZIP往返）；smoke_standalone PASS（2次隔离启动）。本地manifest的tested_merge_sha回退为当前HEAD，不是GitHub实际merge-ref；远端合并引用证据只由最终PR的CI提供。

补充离屏查看：1366×768/100%多燃料/电力明细可滚动至底部并操作新增、删除和计算；燃料多列的长单位标签仍较密集。保留UAT03既有表单布局，原生验收须继续核对字体、缩放及长标签可读性；本包未因此重做燃料业务录入。

修复后专项：python -m unittest tests.test_electricity_2023_catalog tests.test_g04_catalog tests.test_p3_df_factors -v：22项、88.366秒、OK。未修改已有测试期待来绕过失败。六组离屏证据已按a267881修正源码重新执行，所有JSON源码hash需一致后才提交。
