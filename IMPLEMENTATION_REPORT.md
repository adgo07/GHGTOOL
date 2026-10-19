# B-HEAT / PR52-F01 实施报告

更新：2026-10-19。状态：FIX_IN_PROGRESS / 新CI与精确head实包待验。源复验发现Pa/K正式输入在冻结B.9被错标为MPa/℃，此前796技术PASS已撤回；用户源会话直接消息01a1546a-24ef-7f21-a60d-f7d6d54cc394授权继续原PR52定向修复，已实际读取。独立报告已完整读取，不新建PR、不自行合并。

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

## 代码 / 文档 / 制品与下一步

开工head79695cc665e8d03a45ef20bf3bb88e5c4ccccdd4，原分支codex/b-heat-integration；本轮新产品补丁以本提交/原PR52最新head为准，尚未产出新制品。旧CI280的fca代码/321文件实包及1010/18通过只作历史，不能背书F01新补丁；旧证据保留于B_HEAT_CI280_*、此前原始失败对账仍在B_HEAT_SUMMARY和各原始proof。当前验收工具新增6组合双方向真实Record→B.9→Word反例，并在旧CI273历史比较显式固定同次导出日期。

下一步：push原PR52→新merge-ref全量CI/精确head实际包→更新最终回执，双列代码/文档/制品head→源独立验收后停止。原生Office/鼠标IME/人工DPI/企业样例/干净目标机/原生EXE人工正常关闭/商业履约OPEN。不CU、不商业发布、不宣布SUPPORTED、不纳入外部CO2/N、不改用户原脏树与计算表。
