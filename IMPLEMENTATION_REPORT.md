# GHG-EXB01 实施与专项验收报告

日期：2026-10-10。状态：实现已收口，PR #40为Draft；最终整仓回归428/428、Windows构建及审计通过，最终文档Head CI待验证；原生保存验收未闭合，禁止自动合并。

## 平台 / Contract 预检查

canonical origin 已实核为 adgo07/GHGTOOL。初始基线 main@708f78a455790946b4a728029bba768d8fb295fc；续跑同步已合并PR38 main@a51afbcf684e3845369977e42adc938866726d0b，保留其首页/Shell/标准库成果。独立分支 codex/exb01-appendix-b-ingress；当前实现提交 84071c2449fcb036770c0b0f1aa4438dd6497aa1，原用户checkout分支与未跟踪资料不动。

locked central SHA：ee5feb0cc34dbd99790500fadd0c4c932e202a20。已按锁读取 Architecture V2.1、Numeric Contract v1、Numeric Profiles v1（FROZEN）；当前 ACTIVE UI 指南仅约束必要接线。适用 MUST / MUST NOT：共享 Canonical→Application→Domain→Calculator；词法证据与Decimal p40/HALF_UP保持；显示修约不反馈；项目与不可变Record分库；不重算历史Record；不升级公共锁/Contract。项目/Record公共Contract仍DRAFT。本包为本地Adapter修复，无中央公共缺口或Contract修改。

相关Standard Issue001～008保持；本包不改变标准解释、公式或适用范围。B.8遵守PR37已批准V2第138～144行：非化石属性用于购入，输出不适用购入属性，按适用输出因子扣减；修复早期错误映射假设，不新增非化石输出自动零规则。K1/K2/K3与脱硫I/TR只补现有核验目录绑定的Resolver桥接，值和解释不改。

## 实际删除、保留与新增

- 删除 `packages/excel/r2.py` 的R2专属模板生成、下载和新文件解析；生产代码及新测试不再导入旧模块。
- 新增 `packages/excel/templates.py` 和正式资源；轻量登记标准/模板ID/版本/路径/SHA，下载精确复制，不运行openpyxl重新保存。
- 新增 `packages/excel/ingress.py` 保留并迁移OOXML数值词法、Decimal、工作簿哈希、单元格定位及预览数据模型。
- 新增 `packages/excel/appendix_b.py`：B.1不读活动数据；B.2～B.9一次形成一个完整Canonical Input。保留自定义名称、燃料直接/计算两路径、物料碳/挥发配对质量只计一次、多碳酸盐、正式电力方向/地区因子与蒸汽路径。歧义及坏输入定位错误，不省略出错排放源后宣布成功。
- `packages/application/carbon_accounting.py` 仅补正文5.2.2/5.2.3/5.2.4/5.2.5.2中已有核验参数的选参桥接，所有缺省仍由正式Resolver选择。B.6无核验目录缺省，不能凭记忆补值。
- `packages/ui/pages.py` 只改Excel必要接线：显式期间/可选企业和地区/边界，预览→保存项目→明确正式核算；打开项目时锁定新导入字段、显示实际保存期间，失败新导入清除旧项目计算能力。输出属性原文及说明进入保存的warnings来源证据。
- `scripts/build_standalone.py`、`scripts/inspect_release.py`、`pyproject.toml` 精确列入批准模板、Logo和7个图标；模板路径与SHA核验，其他工作簿/用户资料拒绝加入。
- 保留Canonical codec、现有数据库结构与迁移、Application正式计算/持久化、项目恢复/pending-link恢复、Record追加和历史EXCEL_R2来源身份。未改Domain公式、Numeric/Frozen Contract、Word模型/renderer，未执行P3-C/D/E/F。
- 迁移原Excel/UI/报告相关测试，新增模板、GUI与Excel正式结果一致、Resolver默认及附录B专项测试。重要R2数值/原始词法/Record业务断言迁入新版，不保留旧模板生成测试路径。

## 母版与资源证据

原用户母版保持不变：SHA256 `c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4`，25919 bytes。
按任务第3节授权只在受控副本删除B.2 J4:J18、B.6 G3、B.7 G3:G5、B.8 E3:E4共21结果公式及空缓存；未用openpyxl保存生产模板。
受控无公式正式资源SHA256 `e6a070bf28adb47939e24713f676136b5a023017d6f695e0031c68d51c389c3d`，23335 bytes。模板ID `GHGTOOL_GBT_32151_34_2024_APPENDIX_B`，版本1.0.0。
独立核对30个ZIP成员中26个payload不变，4个XML只删除指定f/v；九表顺序/合并/验证/样式/单位/脚注及其他值保持。下载哈希须与授权去公式资源一致，不能冒称与含公式原始文件字节一致。

## 本地实际验证

执行环境为Windows/Python3.12，导入路径指向任务worktree；下列均为本地证据，不能冒充GitHub Actions。

| 命令 / 检查 | 实际结果 |
|---|---|
| `python scripts/validate_canonical.py` | PASS：9 standards / 12 sources / 102 parameters / 138 factors |
| `python -m compileall -q apps packages resources scripts tests` | PASS，exit0 |
| `python -m pip check` | PASS，无依赖冲突 |
| `python scripts/initialize_databases.py --output-dir build/exb01/databases-final` | PASS，四库仅在隔离测试目录生成 |
| `python -m unittest tests.test_g03_shell -v`（PR38合并后） | 11 tests / 11 passed / 0 fail / 0 error |
| `python -m unittest tests.test_exb01_resolver_defaults -q` | 2 tests / 2 passed / 0 fail / 0 error |
| `python -m unittest discover -s tests -t . -v` | 前轮efc8fe7：426/426，0 fail、0 error，1226.024s；最终实现84071c2：428/428，0 fail、0 error、0 skip，1194.369s，exit0；日志 `build/exb01/full-regression-84071c2.log` |
| `python scripts/build_standalone.py --output-root build/exb01/windows-final` | PASS，exit0；日志 `build/exb01/windows-build-84071c2.log`；manifest三项提交均为84071c2449fcb036770c0b0f1aa4438dd6497aa1 |
| `python scripts/inspect_release.py build/exb01/windows-final/QingzhouCarbonAccounting` | PASS，exit0：263目录文件，目录/目录数据/manifest/范围检查通过 |
| `python scripts/verify_release_archive.py build/exb01/windows-final/QingzhouCarbonAccounting` | PASS，exit0：264归档可见文件，ZIP往返manifest保持 |
| `python scripts/smoke_standalone.py build/exb01/windows-final/QingzhouCarbonAccounting` | PASS，exit0：两次隔离启动；包内唯一Excel资源SHA e6a070…匹配 |
| `python scripts/uir04_manual_gui_acceptance.py`；`python scripts/uir04_scale_acceptance.py --scale 1.25` / `--scale 1.5` | 三命令exit0：A～E五场景PASS，1366×768动态行与两缩放PASS；offscreen，不代替Excel原生保存 |

早期定向组合21项为20通过、1测试错误（快照键大小写断言），已更正；此前还发现并修复了夹具插行后解除合并的KeyError、单位入口区分、过程缺省桥接及无失败原因展示问题。七模块更正后命令末尾统计未可靠回收，不猜测数量，以完整回归日志为最终依据。

## 未闭合验收项

1. 原生Excel/WPS保存后读取：Astra 6/low通过受支持Computer Use入口三次尝试，最新2026-10-10 01:13:20～21北京时间仍报 `trusted Node process exited unexpectedly; kernel reset, rerun your request`。未操作Excel/WPS、未修改文件、无原生保存产物。离屏/openpyxl重存均不能替代本项。
2. 最终文档Head的GitHub Actions待完成。实现提交84071c2的本地428/428、Windows构建/发布与归档审计/两次冷启动已通过；不能把本地结果冒充CI。
3. 独立AI复核实现提交84071c2：无新增代码阻断；专项17/17及模板2/2独立复跑通过。最终文档Head由独立AI复核；原生保存与最终CI仍是完整交付验收缺项；PR #40保持Draft，不得自动合并。

## 独立复核收尾

独立AI审阅efc8fe7实际diff并用临时副本复现P1：B.7批次名`A Sample Batch`被通用`a `前缀误认脚注，导致脱硫漏读；同时指出B.2自定义名称的同类边界风险。已在84071c2改为批准母版全宽合并结构与受限脚注标记识别。新增B.2合法燃料名及B.7合法批次/真实脚注停止回归；专项17/17、与主集成组合23/23通过。最终全量428/428，0 fail、0 error、0 skip；重建/目录审计/ZIP审计/两次隔离启动已通过。预览重复提醒已在UI去重，原来源证据字段保留兼容。

## 用户14项专项验收对照

| 项 | 证据与状态 |
|---|---|
| 1 下载哈希 | PASS：与任务授权去公式受控母版e6a070…一致，原用户c805e4…文件保留 |
| 2 九表/表式/指定区域无公式 | PASS：独立模板2/2及ZIP成员差异检查 |
| 3 Excel/WPS原生保存后可读 | 未执行成功：Computer Use初始化失败，验收缺项 |
| 4 B.2自定义/双含碳路径 | 专项通过，保留原词法和高精度；未登记名称不借缺省 |
| 5 B.3～B.5不重复计量 | 专项通过，配对碳/挥发分物料只计一次；冲突定位阻断 |
| 6 B.7多组分 | 专项通过，含手算分项和缺省百分比超100%阻断 |
| 7 B.8方向/非化石/选参 | 专项通过，输出无购入属性零规则 |
| 8 B.9蒸汽/热力 | 专项通过，正式焓值参考路径/Resolver因子 |
| 9 Excel与GUI正式一致 | 实际Qt页面测试通过，ES=0、ET=6.17；同一共享正式Calculator |
| 10 ES/ET | 全来源手算分项及ES/ET断言通过，不仅与自身实现互相比较 |
| 11 预览零Record/正式一次一条 | 项目工作流与GUI一致性测试通过；写失败不声称完成 |
| 12 历史R2项目/Record/来源 | 原有恢复/追加/快照断言迁移并保留EXCEL_R2身份，不迁移数据库 |
| 13 无可触达R2新入口 | 删除r2.py与生产新导入/下载路径；历史身份字符串有意保留 |
| 14 构建/审计/全回归/最终Head CI | 本地428/428及最终构建与发布/ZIP/冷启动通过；最终文档Head CI待收口 |

## 实际变更文件清单

相对当前主线（含PR38）的33个文件，A新增、M修改、D删除：

```text
M	AGENTS.md
M	HANDOFF.md
M	IMPLEMENTATION_REPORT.md
M	README.md
M	REFERENCE_STANDARD_ROADMAP.md
M	TASK_STATE.md
M	docs/DELIVERY.md
M	docs/architecture/REPORT_OUTPUT_ARCHITECTURE.md
A	docs/exb01/APPENDIX_B_INPUT_DESIGN.md
M	packages/application/carbon_accounting.py
A	packages/excel/appendix_b.py
A	packages/excel/ingress.py
D	packages/excel/r2.py
A	packages/excel/templates.py
M	packages/ui/pages.py
M	pyproject.toml
A	resources/excel_templates/gb_t_32151_34_2024_appendix_b_v1.xlsx
M	scripts/build_standalone.py
M	scripts/inspect_release.py
M	specs/reporting/GB_T_32151_34_2024_REPORT_SCHEMA.md
A	tests/exb01_fixture_helper.py
A	tests/test_exb01_gui_parity.py
A	tests/test_exb01_ingress.py
A	tests/test_exb01_resolver_defaults.py
A	tests/test_exb01_template_acceptance.py
M	tests/test_g03_shell.py
M	tests/test_g08_delivery.py
M	tests/test_main_integration_excel.py
M	tests/test_main_integration_ui.py
M	tests/test_rpt01_report_excel.py
M	tests/test_rs03_excel_entrypoints.py
M	tests/test_rs03_excel_project_workflow.py
M	tests/test_rs03_pending_link_recovery.py
```

最终报告提交只更新本文件和TASK_STATE.md，运行时代码与本地验证的84071c2完全一致；当前PR head与CI证据在PR #40持续记录，避免把文档提交SHA冒作本地构建source_commit。
