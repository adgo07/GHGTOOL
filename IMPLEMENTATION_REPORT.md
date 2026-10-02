# GHG-RS01-A 实施报告

日期：2026-10-02；工作包：GB/T 32151.34—2024 Core Function Check。
状态：**GHG-RS01-A审计及交付完成，待独立验收**；最终文档head仍须等待其实际CI回执。

## 1. 基线与范围

- origin实际为 `https://github.com/adgo07/GHGTOOL.git`，默认main。执行 `git fetch origin` 后从最新main建立 `codex/ghg-rs01-a-core-check`。
- Base：`c8f7a8ce2139e21b239ce54fac6cbbb9c25aae72`；Git合并记录及GitHub PR元数据均确认PR #21已合并。
- 开工跟踪文件无改动。既有未跟踪 `docs/handoffs/`、`docs/青舟工业能源软件架构与产品一致性规范.md` 保留、不提交。
- 用户明确启动RS01-A，附件限定本包只核对；覆盖HANDOFF §7上一治理工作包“不启动RS01”的旧范围。Roadmap所要求Mapping纳入仓库仍为明确前置，登记009，本轮不假装完成。
- 仅提交CORE_CHECK、GAPS、TASK_STATE、本报告四份Markdown。不修改Calculator、Rule、Canonical正式数据、UI业务、正式测试、数据库/迁移、baseline或用户计算表。
- 当前PR/head由Git/PR提供，不预写自引用最终SHA。未实施Excel、报告导出、Golden、新标准或Release。

## 2. 实际专业来源

| 依据 | 实际使用 |
|---|---|
| 标准 | `34.GB_T 32151.34-2024 温室气体排放核算与报告要求 第34部分：炭素材料生产企业.pdf`，43页；SHA256 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738` |
| Verified Mapping | `GB T 32151.34—2024 炭素材料生产企业映射方案.md`，SM01-2026-09-13-R6、FROZEN；SHA256 `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B` |
| 历史批准证据 | 外部 `IMPLEMENTATION_REPORT_SM01.md`、`G06_R6_修正清单_给Sol_2026-09-13.md`；`5b8d35db65375907ccef18d426fba9ec4319aa64:TASK_STATE.md`记录G06最终PASS（验收对象c2ca02e）及R6原始LF哈希，与本次文件一致 |

本次本机实际路径见CORE_CHECK §1，只是执行来源，不作为仓库身份。提取PDF文字并视觉核验核心公式、C.1/C.2/C.4/C.5/D表页，临时提取物在忽略目录 `tmp/rs01-a/`；标准全文/PDF不入Git、不进程序包。未从代码反推标准或重新制作大型Mapping。

沿用Mapping批准的含碳量单位、式（4）符号、蒸汽压力键及收到基固定碳决定，不称官方勘误。当前R6不与历史R4合并。独立确认记录链接缺失为009；不把用户未跟踪R4反馈冒充完整批准原件。没有新增需要选取的标准解释，台账仍0条。

## 3. 平台 / Contract 预检查

- 业务base见§1；中央locked SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`，auto_upgrade=false，未升级。
- 实际按locked SHA读取Architecture V2.1 FROZEN、Numeric Contract v1 FROZEN、Numeric Profiles v1 FROZEN对应文件。
- 读取中央当前合并版本Standard Development Guide v0.1、UI Design Guidelines v0.1，均ACTIVE/EVOLVING，不作为新Frozen adoption。
- MUST：确定性十进制、有效Profile贯穿helper/单位换算/汇总、ambient independence、full-value exact comparison、版本/来源可追溯；保持分层及Canonical参考数据/版本化Calculator分工。
- MUST NOT：binary float静默成权威值、显示修约回流、隐含业务epsilon、混淆44/12及44/16与普通单位转换、历史Record自动重算；不把p40/HALF_UP当平台默认。
- ALLOWED PROJECT DIFFERENCE：Carbon使用 `GHGTOOL_CARBON_DECIMAL40_CURRENT`。已读取 `_numeric_authority.py`、`standards/__init__.py`安装的实际权威入口及Conformance，未仅凭旧helper正文误报Profile泄漏。
- 本次缺口均为本地软件/证据问题，新增CENTRAL CONTRACT GAP为0；不修改公共Contract。Unit、Workspace/Result/Record、qzpack仍DRAFT，Quantity未冻结。
- Standard Issue新增0，相关新增编号无；本轮不改变既有软件解释。009相关解释修改前必须补证。

## 4. 审计模块与交付

| 链路 | 实际审计 |
|---|---|
| 输入/校验/计算/汇总/快照/记录 | `packages/standards/carbon_material.py`、`_numeric_authority.py`；`packages/core/models.py`、`decimal_policy.py`，现有Numeric测试 |
| Rule / 参数选择 | `packages/core/rules.py`、`parameter_resolution.py`的default_g05_rules与解析器；`packages/application/carbon_accounting.py` |
| 用户录入 / 单元 | `packages/ui/carbon_material_page.py`、`field_specs.py`；`packages/application/project_workspaces.py`及Project Repository/UI回归 |
| Canonical / 入口 | `data-source/carbon_accounting/catalog.json`、`packages/application/catalog_queries.py`及目录回归 |
| tests | G06 Calculator/Page、G05、Project Workspace/UI、Numeric v1 adoption/N01-C及全量 |

新建 `specs/carbon_accounting/GB_T_32151_34_2024_CORE_CHECK.md` 与 `GB_T_32151_34_2024_GAPS.md`。

- 核对16项：OK5 / GAP11 / NEEDS_CONFIRMATION0 / N/A0。
- Gap10条：IMPLEMENTATION_GAP7 / TEST_GAP1 / EVIDENCE_GAP2 / STANDARD_ISSUE0 / CENTRAL_CONTRACT_GAP0。
- YES4：001实测供热因子、002未知碳酸盐fallback、003负参数成功记录、004同单元多过程/热源覆盖；NO5；UNKNOWN1（009原始批准附件）。YES均绑定原文/Mapping，不修复、不做新增解释。
- RS02展示问题独立列于CORE_CHECK，不扩成UI重构。没有宣布完整支持或RS01整体完成。

## 5. Local — 已实际执行

Windows，仓库 `.venv/Scripts/python.exe` 3.12.14；Qt使用QT_QPA_PLATFORM=offscreen；测试PYTHONDONTWRITEBYTECODE=1。代码树绑定本包base，文档改动不改变被测实现。

| 命令 | 实际结果 |
|---|---|
| `.venv/Scripts/python.exe -m unittest tests.test_g06_carbon_material tests.test_g06_page tests.test_g05_rules tests.test_accounting_projects_ui tests.test_project_workspaces tests.test_numeric_contract_v1_adoption tests.test_qzc_n01_c_numeric_unit_pilot -v` | 88/88，0失败/错误/跳过，21.085秒，exit0 |
| `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v` | 214/214，0失败/错误/跳过，21.563秒，exit0 |
| `.venv/Scripts/python.exe scripts/validate_canonical.py` | exit0；9 standards / 12 sources / 7 parameters / 7 factors |
| `.venv/Scripts/python.exe -m compileall -q apps packages resources scripts tests` | exit0，PYTHONPYCACHEPREFIX指向本次tmp新目录 |
| `.venv/Scripts/python.exe -m pip check` | exit0，No broken requirements found |
| `.venv/Scripts/python.exe scripts/initialize_databases.py --output-dir tmp/rs01-a/databases --app-version rs01-a-audit` | exit0，catalog/user/records/projects四库从零创建，用户库未触碰 |
| `git diff --check` | 已通过；提交前再核对 |

实际等待测试进程结束并核对Ran/OK/exit0，没有把启动当完成。日志在忽略目录tmp/rs01-a/core-tests.log、full-tests.log。

只读探查（不是新增正式测试）：Domain脱硫只填10t→3.9600成功记录；负含碳量→-0.733333…、负热力因子→-0.308，均成功且无错误；GUI脱硫只填10t→3.96并生成1条记录，热力选项仅0.11无实测入口。只用内存Record或本轮隔离数据库。探查首次错取结果字段输出中断，修正为total_amount后重跑exit0，未把首次失败计作通过。另观察K=1.01可接受，但原文/Mapping无明确上限证据，未制造K上限Gap或修复要求。

未执行新的Golden、企业真实基准、Excel parity：本包明确排除；未本地重建standalone：纯文档未改发布能力，PR已有CI会执行发布审计。

## 6. GitHub Actions — 与Local分开

任务PR：[PR #22](https://github.com/adgo07/GHGTOOL/pull/22)，目标main、保持open，不自行合并。

已实际完成的CI证据：[Windows CI run 36971166108](https://github.com/adgo07/GHGTOOL/actions/runs/36971166108)，绑定审计提交 `47bae76785b0526e593ce61da857994adde23d45`。

| Job | 结果 |
|---|---|
| Merge-ref Full Tests，110725244478 | success；日志Ran 214 tests in 31.935s / OK；Canonical、compileall、pip check、四库重建、GUI A～E、125%/150%均成功 |
| PR-head Standalone Audit，110725575929 | success；精确审计head构建、Canonical、compileall、pip check、四库重建、GUI/缩放、G08 delivery、standalone build、release audit、archive manifest、provenance、isolated smoke和artifact upload全部成功 |

上表是GitHub Actions，不是Local。首次报告提交时本任务确实尚无PR/run，未预写CI通过。该CI证据写入产生新文档head后，仍须等待PR最新head的实际两项检查；最终run/head以PR与交付回执为准，不把47bae76的成功自动当作新head通过。

## 7. 停止点

审计只发现Gap，没有关闭业务Gap。PR不得自行合并，交付后停止等待独立验收。

**GHG-RS01-B NOT STARTED**。
