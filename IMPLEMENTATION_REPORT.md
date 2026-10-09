# GHG-RPT02 附录B Word报告实施报告

日期：2026-10-10。状态：实现及样例交付候选，等待独立验收；不自动合并。PR：[#39](https://github.com/adgo07/GHGTOOL/pull/39)。最终Head和最终CI证据以该PR的head/checks及正文为准，本报告提交后的复跑结果不冒充提交前已通过。

## 平台 / Contract预检查

本仓origin已实际核验为adgo07/GHGTOOL，默认main；启动时从最新origin/main@708f78a独立创建codex/ghg-rpt02，复用已合并PR37，不取EXB01/P3-AB未合并代码。交付期间PR38已正式合并，接收其origin/main；冲突仅HANDOFF、路线与TASK_STATE，保留P3-AB成果、暂停C/D/E/F，本包不实施P3-C。原checkout用户修改和原批准模板未覆盖。

中央Frozen锁定`ee5feb0cc34dbd99790500fadd0c4c932e202a20`不变。已读相关Architecture V2.1 / Numeric v1：MUST保持分层、只消费冻结Record、显示转换显式采用Decimal策略；MUST NOT让UI/当前Catalog/重算改变历史结果，显示修约不得回流Calculator。本任务不修改中央公共Contract，无冲突、偏差升级或CENTRAL CONTRACT GAP。当前ACTIVE UI指南只用于已有中文说明，不当Frozen。相关Standard Issue004、007、008的既有解释保持，不新增/改变标准解释、公式、p40精度、适用范围或正式支持状态。

## 实现与修改文件

| 文件 | 改动 |
|---|---|
| packages/application/reporting/model.py | 保留唯一ReportModel，新增通用布局字段；ES/EI/ET冻结总量共用读取；删除重复旧附录映射。 |
| packages/application/reporting/appendix_b.py、appendix_b_layout.json | 当前标准专属映射/批准布局版本；九表列序、分组、合并、单位、脚注、扩行和冻结采用值。 |
| packages/infrastructure/reporting/word_renderer.py | 原renderer扩展可编辑表格、多层重复表头、合并、字号/方向/分页、黑色边框、末行与脚注相邻；多过程独立起页。 |
| packages/ui/record_experience.py | B.1和记录摘要复用冻结总量解释；审计查看保留，无视觉重构。 |
| pyproject.toml、scripts/build_standalone.py | 打包静态报告布局JSON；Word运行时不依赖原Excel。 |
| tests/test_rpt02_appendix_b.py、test_rpt01_report_excel.py、test_rs03_excel_entrypoints.py、test_main_integration_ui.py | 模板/原生表格/历史回退/来源碰撞/零值/比例/扣减/同Record双入口一致性及既有导出回归。 |
| scripts/rpt02_acceptance_samples.py、rpt02_wps_acceptance.ps1 | 仅验收辅助：真实UseCase Record样例、冻结证据、现有R2导入及WPS只读PDF。合成builder明确只作映射单测/分页QA。 |
| docs/批准模板xlsx、docs/rpt02/ | 清理21公式副本；3份DOCX及WPS PDF、完整正式Record快照、哈希与验收证据。JSON按仓库LF策略写入，避免Git换行导致哈希漂移。 |
| REPORT_OUTPUT_ARCHITECTURE、REPORT_SCHEMA、HANDOFF、REFERENCE_STANDARD_ROADMAP、TASK_STATE、本报告 | 架构/Schema/当前状态同步；不建立第二套路线。 |

未修改Calculator、正式Record模型/数据库迁移、当前参数库、EXB01导入器、共享文件保存/确认/审计流程。原子写入、覆盖确认、文件哈希及report_export_history继续由PR37入口处理。

## 九表与数值结论

B.1分别列ES、ET，EI不替代第二总量；B.3～B.5按碳与挥发分投入/产出分组；B.9保持七列，冻结逐条排放量及参考焓值列于表后。多源真实Record含2燃料、各2过程/设施、34物料明细、购入/输出电热各2；ES/ET显示606.02/679.08，输出电力-1.00/-0.50、热力-0.03/-0.15。

ratio→percent、kg→t、kWh→MWh仅显示转换，零不变成空值。历史缺失字段、未启用、未填写与可选无物流分开；未冻结的派生燃料含碳量、逐碳酸盐排放不补算，不从今天Catalog推断来源。方向归属不足的同IID自动电力来源快照安全提示无法唯一关联，不能猜造。

原始/清理后模板SHA256、列序/分组/单位/标准脚注与WPS逐页结论见[专项验收证据](docs/rpt02/ACCEPTANCE.md)。原模板对照：值差异仅21公式、样式0差异、合并0差异。

## 本地命令与真实结果

以下Python命令使用本仓Python3.12.14 venv；GUI设置QT_QPA_PLATFORM=offscreen。此节明确是本地执行，非GitHub Actions。

| 命令/证据 | 实际结果 |
|---|---|
| python -m unittest discover -s tests -t . -v → tmp/full-tests.log（前轮） | 395项：390 pass、4 fail、1 error、0 skip；1476.509秒。旧列位置/数值单位断言和来源映射问题，不能写成全量通过。 |
| 同命令 → tmp/full-tests-verified.log（续跑） | 404项：404 pass、0 fail、0 error、0 skip；1799.496秒。开跑时基于619b527；后续main整合、分页小修和新增双入口测试由最终Head另行复跑，此日志不冒充最终Head一致性证据。 |
| python -m unittest tests.test_rpt02_appendix_b tests.test_rpt01_report_excel tests.test_uat03_rules tests.test_main_integration_ui.MainIntegrationUiTests.test_both_word_entrypoints_export_identical_business_content_for_same_record -q | 最终分页代码29项：29 pass、0 fail/error/skip；25.413秒，tmp/rpt02-focused-29.log。 |
| python scripts/validate_canonical.py | 通过：9 standards、12 sources、102 parameters、138 factors。 |
| python -m compileall -q apps packages resources scripts tests | exit0。 |
| bundled python -m pip --python repo-venv-python check | No broken requirements found。 |
| python scripts/initialize_databases.py --output-dir build/databases/rpt02-final-check | 四个隔离库初始化成功。 |
| python scripts/uir04_manual_gui_acceptance.py | A～E五场景PASS；自动Qt检查，不冒充人工操作。 |
| python scripts/uir04_scale_acceptance.py --scale 1.25 / --scale 1.5 | 两档均PASS，1366×768控件无横向滚动/重叠。 |
| python scripts/build_standalone.py --output-root build/rpt02-integrated-dist | 本地集成候选554f7fd构建exit0；最终分页修正后须由最终Head构建再绑定。 |
| inspect_release.py / verify_release_archive.py / smoke_standalone.py 对上述目录 | 265文件审计PASS、266可见文件ZIP往返PASS、2次隔离启动PASS。 |
| python scripts/rpt02_acceptance_samples.py；--refresh-from-saved-records；--multi-source-sample | 3条演示输入生成正式不可变Record；后续仅由已有Record重渲染，原DB和快照业务值不变。 |
| scripts/rpt02_wps_acceptance.ps1 | WPS COM12.0：3份最终Word为11/10/14页，35页已目视核对；原生可编辑表格、中文、合并及重复表头正常，无空白正文页。 |
| 合成80燃料行压力QA；WPS编辑副本保存/复读 | 22页/21表格页均重复双层表头、80行完整；编辑副本成功，原交付文件哈希未改。 |

两次中途全量运行因随后发现来源关联和分页问题而主动终止，没有最终summary，不计作pass或fail。Documents技能的LibreOffice渲染器因本机无soffice未执行；实际WPS PDF+Poppler页图完成替代检查。

## CI及独立复核

集成候选554f7fd的[Actions 37967479912](https://github.com/adgo07/GHGTOOL/actions/runs/37967479912)两项job成功；它不是最终分页修正Head的证据。最终提交后重新等待PR #39全部checks：merge-ref全量、PR-head交付测试/Windows构建/清单溯源/ZIP审计/隔离启动。最终完整SHA、实际pass/fail/error/skip及运行链接记录于PR正文，不能把旧Head的绿色状态当最终通过。

独立AI已对619b527实际diff、批准模板、正式Record和Word做只读复核，未发现阻断映射缺陷；识别同IID来源安全降级限制。最终Head仍须独立复核后签收；实现方不自行宣布正式验收通过。

## 未闭合验收项

- 独立验收人在最终Head逐项签收及原生Windows系统DPI人工验收仍OPEN；不以离屏测试冒充人工验收。
- 现有R2真实导入及同输入业务内容一致已覆盖；EXB01合并后的新导入链整合联测待其合并后补做。
- 历史没有冻结的字段和无法唯一关联的来源保持明确缺失；本包不迁移/补造历史Record。
- 本报告提交时最终Head本地全量及CI正在复跑，交付时以PR #39的最终Head结果留证；未绿前不能声明该项关闭。

独立复核补充（2026-10-10）：最终冻结前收口历史电力来源安全边界。单个候选也须与冻结EF精确匹配；购入/输出同编号且仅剩一个无方向证据的快照时标记无法唯一关联；已转交直接燃料路径的自用化石电力不参与购电来源碰撞判断。新增回归连同定向套件30项通过（tmp/rpt02-focused-30.log）；cbaba59全量因本次安全修正主动停止、无完整summary，不计为通过。修正后重新冻结Head并执行全量、构建与CI，最终结果记于PR39正文。
