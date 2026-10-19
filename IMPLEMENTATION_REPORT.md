# B-HEAT / PR52-F01 实施报告

更新：2026-10-19。状态：READY_FOR_INDEPENDENT_ACCEPTANCE；新CI/精确包验证已完成，待源最终独立验收。源复验发现Pa/K正式输入在冻结B.9被错标为MPa/℃，此前796技术PASS已撤回；用户源会话直接消息01a1546a-24ef-7f21-a60d-f7d6d54cc394授权继续原PR52定向修复，已实际读取。独立报告已完整读取，不新建PR、不自行合并。

## 平台 / Contract 预检查

业务base `a1aeebc1b6809397e61a2ffa7a2333a3b440c756`，工作树origin实际核实为adgo07/GHGTOOL且已fetch；当前任务分支codex/b-heat-integration。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，相关Frozen为Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；ACTIVE UI指南按中央正式main适用版读取。MUST：分层、共享Application、declared-profile consistency、ambient independence、full-value exact、原输入/规范/物性工作/显示值分开、Record/Word冻结。MUST NOT：业务epsilon、显示修约回流、隐式物性回退、Qt状态充当公共Workspace、自动升级Frozen。Carbon Decimal40/ROUND_HALF_UP是ALLOWED PROJECT DIFFERENCE；binary64物性子Profile单独声明，不冒称p40物性精度。C3资格漏项、工作Pa/K门禁不足均LOCAL DEFECT，不需改中央Contract。相关Standard Issue005/006/015/017/019；本包执行已经批准的软件决定，没有新增标准解释、标准范围或Frozen变更。

F01是共享冻结显示投影LOCAL DEFECT，不改中央Contract、公式、物性Profile、DB或专业解释，非新增Standard Issue；关联017既有方法/Record约束。读已锁Architecture/Numeric，显示换算不得回流正式值。


## 修复与兼容

共享Application B.9优先消费该Record按CAR-HEAT-IF97-017.1冻结的规范压力MPa/温度℃词法；缺规范证据时只按冻结原值明确单位作显示换算。压力MPa/kPa/Pa/bar和温度C/°C/℃/degC/K沿正式链既有支持；K减273.15是带偏移换算，不作为UnitService倍率。未知/缺失单位明确标记，无Calculator/Resolver/CoolProp调用，不写回Record或从当前目录补值。按既有算法/方法身份保持pre-HEAT旧报告路径，饱和温度仍不适用。没有改公式、数值/物性Profile、DB、Canonical输入、中央锁或专业决定。

新增tests/test_b_heat_report_units.py从真实正式服务写入SQLite Record，再经共享build_report_model及Word renderer检查B.9：购入/输出均覆盖过热MPa/C、Pa/K、Pa/C、MPa/K与饱和MPa/Pa；核对固定表头/单元格数值和Word XML，禁Calculator/Resolver/物性，原始快照/Trace/DB字节不变。另覆盖已知焓显式单位、缺/未知单位、非有限证据和pre-HEAT兼容。

DELIVERY的旧iapws/267文件/v8段标明历史并指当前CoolProp/v10；Mapping头部补FUME/HEAT接管及PR52退修事实，旧iapws/Profile预案明确历史，不改原文事实或历史修订记录。README/PREFLIGHT补固定依赖安装/核对；缺库标准discover明确_FailedTest/ImportError/FAILED与非零退出码，22用例折1加载错误可少21，不是静默成功。

Mapping更新后按既有PREFLIGHT机械重生同R11四件套，三Canonical原字节不变；新旧工作簿全部单元格/样式/Table身份/ref/行列设置相同，3表61行、450原有scope、8隐藏技术列/表、最大344pt，仓内该previous意见0→0，不推断用户附件。只改变定义资产绑定，HTML/fixture原字节不变；完整hash见B_HEAT_F01_REVIEW_PROOF.json。

## 实际本地验证（不是CI）

| 命令/来源 | 结果 |
|---|---|
| python -B -m unittest tests.test_b_heat_report_units.HeatReportUnitTests.test_formal_auto_unit_matrix_both_directions_shared_report_and_word -v（修前） | 1项/4subtest FAIL，4.410s，Pa/K等缺陷真实复现 |
| python -B -m unittest tests.test_b_heat_report_units -v（修后） | 4/4，8.705s，OK |
| python -B -m unittest tests.test_b_heat_report_units tests.test_b_heat_runtime tests.test_b_heat_chain.HeatQtTests tests.test_b_heat_chain.HeatExcelTests tests.test_rpt02_appendix_b tests.test_g08_delivery -v | 59/59，59.668s，OK；重叠不相加 |
| scripts/verify_frozen_record_word.verify，实际旧CI273两条合成记录，禁Calculator/Resolver/物性 | 固定同次导出编制日期2026-10-18后，两个模型及Word document.xml SHA原值一致，原DB不变 |
| 既有ArtifactTool builder + test_business_rules_review.mjs | 25真实场景PASS，本地作者工具，不是CI或原生Office |
| python -B -m unittest tests.test_business_rules_candidate_assets tests.test_b_material_source_review -v（stage绑定） | 23/23，17.154s，OK |

失败真实保留：旧CI273首轮直接使用当天编制日期，Word字节比较失败；逐字节核实唯一区别为2026-10-18→2026-10-19的导出补充日期。固定同一导出日期后模型/正文全值一致，未修改产品日期行为或Record。首轮只读资产比对脚本宿主未设openpyxl搜索路径，ModuleNotFoundError；加既有site路径后全保留性检查通过，不改产品依赖。初始历史回放失败、修前F01失败及所有本地日志在tmp/b-heat，证明不隐去失败。

## 新CI与实际包证据

产品补丁提交dea45cd8c198d74d22d10a371696c62c01312856，完整受验代码/制品head `1843157a8bc9d78fa442c93b4094a076f562d788`（184补齐Mapping定义绑定）；CI283实际merge `f083dd6caeed54bb5e7c2ee0a4b92cc8565bb298`。最终文档回执head为本提交（以PR52最新head为准），增量只含文档/原始证明，不能把184制品改标为回执head。

[CI283/run39264926043](https://github.com/adgo07/GHGTOOL/actions/runs/39264926043)整体SUCCESS；merge-ref job118101913478全量 `python -m unittest discover -s tests -t . -v`：**1014/1014，1695.552s，零失败/错误，skipped=0**。exact-head job118117880702执行 `python -m unittest tests.test_g08_delivery -v`：**18/18，12.315s**；Canonical/编译/pip check/数据库/UIR04/缩放/构建/审计/ZIP/provenance/2隔离启动通过。这是GitHub Actions实际证据，不是本地执行。

实际artifact **12195361432**，ZIP SHA256 **b1febe11d53271ea798a027a89ea5b27c853f3cb9a0772d064c7b9d2842549f7**，75710032bytes；manifest321文件、ZIP322文件。下载后逐文件size/SHA、许可原文/来源清单与PE x64核验通过；source_commit/pr_head均184、tested_merge为上述merge。C本地对这个实际CI包审计/ZIP回读/2启动及 `python -B docs/ci/B_HEAT_PACKAGE_VERIFIER.py <实际CI包> <全新输出> 1843157a8bc9d78fa442c93b4094a076f562d788 <实际CI273旧数据>` 通过，exit0，无nanobind/Traceback；从实际EXE/PYZ及包内CP/NP/Qt读取，禁止业务源码回退。6组单位/相态双方向正式Record→B.9→Word、冻结禁Calculator/Resolver/物性、原证据不变及既有完整热力链均通过。完整证明B_HEAT_F01_CI_PACKAGE_PROOF.json、B_HEAT_F01_CI_RECEIPT_PROOF.json。

同一增强验证器对真实旧CI280包exit1，准确抓Pa/K报告3500.00/300.00错误，负例完整日志入B_HEAT_F01_CI280_NEGATIVE_PROOF.json；本地184新包也exit0、无诊断，但仅是LOCAL_BUILD，单独保留B_HEAT_F01_LOCAL_PACKAGE_PROOF.json，不冒称CI。实际CI273旧模型/Word比较显式固定同次导出编制日期2026-10-18，业务证据和旧正文不漂移，原DB不变；编制日期是导出补充信息，不回写Record。

源已独立运行本轮4项正式链测试4/4、7.962s，定向F01通过，不替代最终新包独立验收。新旧重叠套件不相加。旧CI280整体1010/18通过及原B-HEAT证据只作历史，796技术PASS已撤回，不能背书本补丁。

## 失败对账及停止边界

首个dea45产品提交漏stage Mapping，检查后立即184补齐，首个不完整CI282被取代；实际结果以B_HEAT_F01_CI_RECEIPT_PROOF.json的superseded_ci282记录为准，不把未知统计或旧CI当通过。全部实际失败（修前4subtest、历史导出日期跨日、宿主openpyxl设置）保留，未用全局放宽校验/改公式掩盖。

PR52已push并更新说明，送源独立验收后停止，不自行合并或启动外部CO2/N。原生Office/鼠标IME/人工DPI/企业样例/干净目标机/原生EXE人工正常关闭/商业履约OPEN。不CU、不商业发布、不宣布SUPPORTED。中央锁、专业决定、用户原脏树、计算表不变。
