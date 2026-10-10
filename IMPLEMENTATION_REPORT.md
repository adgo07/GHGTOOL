# PR #40 — EXB01 / RPT02合并前整合报告

日期：2026-10-10。状态：代码整合、本地完整验证与独立审查完成；原PR40待最终检查，不自动合并。最终PR Head及线上CI以原PR实时验收记录核对；本提交只更新报告和TASK_STATE。

## 平台 / Contract预检查

origin已确认adgo07/GHGTOOL。整合前head6c9280b70e1575ca0a5d9cca5af1645ef9cabd2e；main029ebe6fa6081e3d742ba3900e641e4c4f6aecf0（PR39 RPT02）。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20，按既有锁定Architecture V2.1/Numeric v1/Profile v1执行：Decimal p40/HALF_UP、ambient independence、显示值不反馈、冻结Record不漂移、分层与唯一共享Calculator。无Frozen adoption或中央Contract变化，无新标准解释；相关Standard Issue001～008保持。

## 整合要求及冲突

按PR40评论6090608221在原分支merge最新main。实际6个Git冲突：HANDOFF.md、IMPLEMENTATION_REPORT.md、REFERENCE_STANDARD_ROADMAP.md、TASK_STATE.md、scripts/build_standalone.py、specs/reporting/GB_T_32151_34_2024_REPORT_SCHEMA.md。治理整合已合并RPT02+待合EXB01事实；Schema保留RPT02 v2.0.0正式表式，说明新九表输入/B.1只读/旧R2仅历史兼容。打包冲突由专项核对同时保留布局JSON和唯一批准模板。

重叠但自动合并的docs/architecture/REPORT_OUTPUT_ARCHITECTURE.md、pyproject.toml及三个集成测试已逐项核对，不以Git自动合并代替业务验证。Word renderer/冻结映射保持已合并main实现；不删除报告测试或放松精确比对，不恢复R2新入口。

## 验证与证据

本轮已执行的本地定向验证（QT_QPA_PLATFORM=offscreen，Python 3.12）：

| 命令 | 实际结果 |
|---|---|
| `python -m unittest tests.test_exb01_ingress tests.test_exb01_template_acceptance tests.test_exb01_resolver_defaults -q` | 21/21，0 fail/error |
| `python -m unittest tests.test_main_integration_ui tests.test_rpt01_report_excel tests.test_rs03_excel_entrypoints tests.test_exb01_rpt02_integration` | 21/21，0 fail/error；新增联合用例单独1/1 |
| `python -m unittest tests.test_rpt02_appendix_b` | 10/10，0 fail/error |
| `python -m unittest discover -s tests -p test_g08_delivery.py -v` | 最终14/14，0 fail/error；首轮13 pass/1 error，旧归档夹具未包含新必需布局JSON，补齐夹具后通过 |
| `python scripts/validate_canonical.py` | exit0；9标准/12来源/102参数/138因子 |
| `python -m pip check` | exit0；无损坏依赖 |
| `python scripts/initialize_databases.py --output-dir build/exb01/rpt02-integration-databases` | exit0；隔离四库 |
| `python scripts/uir04_manual_gui_acceptance.py` | A～E五场景通过 |
| `python scripts/uir04_scale_acceptance.py --scale 1.25` 和 `--scale 1.5` | 两种缩放通过；offscreen，不是原生Excel/WPS验证 |

最终代码Head本地完整回归442/442及Windows构建/审计/ZIP/两次冷启动已完成，见后文；最终PR Head线上CI由本报告提交后推送触发，实际终态补入原PR，不把旧CI当作新证据。先前EXB01 428/428及RPT02 415/415和两包原CI只作历史，不替代本次整合结果。最终命令、实际pass/fail/error与diff/head在收尾时补齐。

## 保留与未闭合项

冻结Record只读Word报告、B.1～B.9布局JSON、双Word入口/原子保存/导出审计全部保留。附录B工作簿→预览零Record→Canonical项目→正式Application→不可变Record保留；Decimal/OOXML词法、来源与历史EXCEL_R2兼容不变。下载资源SHA e6a070bf28adb47939e24713f676136b5a023017d6f695e0031c68d51c389c3d，原母版SHA c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4。

原生Excel/WPS保存后回导仍OPEN；旧Computer Use初始化失败不构成通过。本轮不扩大业务范围、不改Formula/Numeric/DB/历史Record/标准范围，不执行P3-C/D/E/F。完成等待最终检查，不自行合并。

## 11个重叠文件逐项处理

| 文件 | 处理与保留 |
|---|---|
| HANDOFF.md | 冲突；同时记录已合并RPT02和当前EXB01 |
| IMPLEMENTATION_REPORT.md | 冲突；重写本次整合报告，旧证据不冒用 |
| REFERENCE_STANDARD_ROADMAP.md | 冲突；唯一路线中同步两包状态 |
| TASK_STATE.md | 冲突；当前整合状态与缺项 |
| docs/architecture/REPORT_OUTPUT_ARCHITECTURE.md | 自动合并后核对；保留冻结Record只读映射，清理旧R2现行描述 |
| pyproject.toml | 自动合并后核对；reporting JSON与批准Excel资源同时保留 |
| scripts/build_standalone.py | 冲突；白名单/模板哈希与reporting JSON收集同时保留 |
| specs/reporting/GB_T_32151_34_2024_REPORT_SCHEMA.md | 冲突；保留RPT02表式，新增EXB整工作簿边界 |
| tests/test_main_integration_ui.py | 自动合并后核对；双Word入口内容相等、冻结Record不变；补B1-B9精确断言 |
| tests/test_rpt01_report_excel.py | 自动合并后核对；保留全部Word测试；仅替换四个R2专属模板/解析测试，重要业务断言迁移EXB模块；来源/行数/结果精确核对 |
| tests/test_rs03_excel_entrypoints.py | 自动合并后核对；新附录B入口与Word输出精确结果，项目/旧来源兼容继续覆盖 |

额外处理RPT02验收样例脚本对已删除R2导入器的依赖：新样例走正式附录B入口；历史样例只读冻结Record，不恢复旧R2新导入。历史docs/rpt02样例、证据和布局JSON与main一致，不重写历史验收结论。

两份受控派生文件不能混同：EXB下载ZIP手术副本SHA为e6a070…c389c3d；RPT02既有布局JSON记录的formula_free_sha256为78042e02b57701cfcb3b4a3fb86dbb6ec8e4fa66ec74cfed768433153d5fdc7e。两者均追溯相同原母版c805e4…c1d9e4；本次不强改既有RPT02布局版本/历史元数据。

## 整合独立复核后的修正

实现合并提交032a5aca2252b55856330df8bae6f239a077b1a3已保留两套能力。独立AI发现历史样例refresh构造SQLiteRepository会初始化数据库元数据，因此修为只读连接备份到临时副本，再在副本上初始化/读快照；原证据数据库与冻结bundle不写入、不重算。

新增HistoricalReportRefreshSafetyTests，从已跟踪冻结bundle恢复临时历史夹具（不是原生Excel验证），验证旧EXCEL_R2身份/历史parity保留、DB和bundle字节不变，并禁止Calculator/Resolver/Importer调用。首轮1 test/1 error为Windows源连接未显式关闭导致临时文件锁；改为contextlib.closing后联合`python -m unittest tests.test_exb01_rpt02_integration tests.test_rpt02_appendix_b -v`为12/12、0 fail/error。历史docs/rpt02文件未改。

032a5ac全量已主动中断，不作为通过证据；日志rpt02-integration-full-pre-fix.log，待修正代码提交后重新全量。该Head本地Windows构建exit0、目录审计264 files、ZIP265 visible files、2次隔离启动PASS仅作修正前证据；最终代码Head已另行重建，见下表。两个EOF空白行一并清理，不改运行逻辑。

## 最终代码Head本地Windows交付验证

代码Head：0cc0dd378aed4b6f0a36b9fc91d6f3c52fad642f（后续若只有本报告和TASK_STATE更新，代码证据仍绑定此Head；最终PR Head由线上元数据与CI核对）。

| 命令 | 本地实际结果 |
|---|---|
| `python -m compileall -q apps packages resources scripts tests` | exit0 |
| `python scripts/build_standalone.py --output-root build/exb01/rpt02-final-windows` | exit0；build log：build/exb01/rpt02-final-build.log |
| `python scripts/inspect_release.py build/exb01/rpt02-final-windows/QingzhouCarbonAccounting` | PASS，264 files |
| `python scripts/verify_release_archive.py build/exb01/rpt02-final-windows/QingzhouCarbonAccounting` | PASS，265 visible files |
| `python scripts/smoke_standalone.py build/exb01/rpt02-final-windows/QingzhouCarbonAccounting` | PASS，2 isolated starts |

manifest的source_commit/pr_head_sha/tested_merge_sha均为0cc0dd378aed4b6f0a36b9fc91d6f3c52fad642f。reporting JSON字节与源码一致，SHA fe212e5f7f238802683e834ea249f14b6ca3ee572a7c60c750c1258f96135358；唯一XLSX为批准EXB模板，SHA e6a070bf28adb47939e24713f676136b5a023017d6f695e0031c68d51c389c3d。没有docs/rpt02样例进入产物。

临时样例CLI也已执行成功：`python scripts/rpt02_acceptance_samples.py --output-dir <临时目录>/docs --evidence-dir <临时目录>/evidence`，exit0，独立DB恰2条交付Record（GUI_CANONICAL_INPUT、EXCEL_APPENDIX_B_PREVIEW_TO_FORMAL_USE_CASE）；相同Canonical输入B1～B9的GUI/Application与Excel业务区段哈希均为f01f511ba0e88dfe1eb6c5c5490ffdcd76d0d8c6d2613664f806c7dd78262965，临时对照Record未加入交付DB。这是程序生成样例验证，不是原生Excel/WPS保存验证。真实命令临时根为系统Temp/rpt02-exb01-smoke-9237aa9cbad44dcc85220a531aec225e，未触碰已提交历史docs/rpt02。

## EXB01专项14项覆盖与缺项

| 项 | 验证落点 / 当前状态 |
|---|---|
| 1 下载字节一致 | template acceptance、入口精确哈希复制；受控去公式副本与原母版差异明确 |
| 2 九表/表式/指定结果区无公式 | template acceptance与资源SHA校验 |
| 3 原生Excel/WPS保存后读取 | **OPEN**，此前Computer Use初始化失败；无真实原生保存证据 |
| 4 自定义燃料/双含碳路径 | EXB ingress、Resolver defaults、GUI parity |
| 5 B.3～B.5不重复物料计量 | ingress按手算逐分项断言 |
| 6 B.7多组分 | ingress多碳酸盐与词法/脚注回归 |
| 7 电力方向/非化石/因子 | ingress与Resolver；输出不借用购入非化石零因子规则 |
| 8 蒸汽与热力 | ingress与GUI parity |
| 9 Excel/GUI正式结果相同 | GUI parity、新联合链路与样例B1～B9 parity |
| 10 ES/ET | ingress逐分项手算、RPT02冻结总量及联合Word断言 |
| 11 预览零Record/正式恰一条 | 新联合测试、project workflow、entrypoints |
| 12 历史R2项目/Record/快照 | pending recovery、项目兼容；新只读refresh测试验证DB/bundle字节不变 |
| 13 无可触达R2新下载/导入 | r2.py删除、UI入口/模板测试；仅历史身份保留 |
| 14 Windows/发布/完整回归/最终CI | 本地构建/审计/启动已通过；全量442/442通过；最终PR Head线上CI由原PR实时验收核对（本报告提交时待推送） |

独立AI已核对11重叠文件、报告核心/历史样例相对main无差异，并绑定0cc0dd3确认只读修正闭合。完整专项验收不能因代码检查通过而隐去第3项；保持Draft，等待最终检查，不自行合并。

独立发布包审计也已按0cc0dd3执行上述目录与归档命令，分别exit0 / 264 files与exit0 / 265 visible files；复核manifest三项身份、两份资源哈希、仅catalog.sqlite、无历史样例/用户数据/旧R2工作簿，结论通过。

## 最终完整回归及交付状态

- 代码Head：0cc0dd378aed4b6f0a36b9fc91d6f3c52fad642f；基线main029ebe6fa6081e3d742ba3900e641e4c4f6aecf0，推送前重新fetch确认未变化。
- 实际命令：`QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -t . -v`（Windows PowerShell设置环境变量后调用项目Python 3.12）。
- 实际结果：**Ran 442 tests in 814.593s / OK；442 pass、0 fail、0 error、0 skip；exit0**。外层实际耗时824.87s。日志：`build/exb01/rpt02-integration-full.log`。
- 早期032a5ac全量是主动中断，日志单独保留为`rpt02-integration-full-pre-fix.log`；不计作通过。
- 最终文档提交相对0cc0dd3只含IMPLEMENTATION_REPORT/TASK_STATE，不改已验证代码。线上Windows两项Job必须绑定最终文档Head，完成后在原PR追加实际run、merge-ref、exact-head及文件计数；不为记录CI再改变已通过Head。
- 独立代码复核与独立包审计均通过，严格只读refresh问题闭合；无Numeric、Canonical正式算法、持久化结构或历史Record漂移。
- 专项人工验收仍只有原生Excel/WPS保存后回导未闭合（OPEN）；当前继续Draft、等待最终检查，不自行合并。原有审查结论保留其旧Head绑定，不改写成新Head结论。
