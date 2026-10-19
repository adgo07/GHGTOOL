# 当前任务状态 — B-HEAT / PR52-F01

更新：2026-10-19。状态：REQUIRES_FIX / FIX_IN_PROGRESS。796技术PASS因冻结B.9 Pa/K数值与MPa/℃表头错配撤回，原PR52继续定向修复；不合并、不启动下一包。原工作树origin实际核实并fetch，分支codex/b-heat-integration、开工head79695cc665e8d03a45ef20bf3bb88e5c4ccccdd4、状态干净。

## 平台 / Contract 预检查

业务base `a1aeebc1b6809397e61a2ffa7a2333a3b440c756`，工作树origin实际核实为adgo07/GHGTOOL且已fetch；当前任务分支codex/b-heat-integration。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，相关Frozen为Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；ACTIVE UI指南按中央正式main适用版读取。MUST：分层、共享Application、declared-profile consistency、ambient independence、full-value exact、原输入/规范/物性工作/显示值分开、Record/Word冻结。MUST NOT：业务epsilon、显示修约回流、隐式物性回退、Qt状态充当公共Workspace、自动升级Frozen。Carbon Decimal40/ROUND_HALF_UP是ALLOWED PROJECT DIFFERENCE；binary64物性子Profile单独声明，不冒称p40物性精度。C3资格漏项、工作Pa/K门禁不足均LOCAL DEFECT，不需改中央Contract。相关Standard Issue005/006/015/017/019；本包执行已经批准的软件决定，没有新增标准解释、标准范围或Frozen变更。

F01是共享冻结显示投影LOCAL DEFECT，不改中央Contract、公式、物性Profile、DB或专业解释，非新增Standard Issue；关联017既有方法/Record约束。读已锁Architecture/Numeric，显示换算不得回流正式值。

## 当前断点

用户源会话直接消息01a1546a-24ef-7f21-a60d-f7d6d54cc394授权“开始修复吧，要求和之前一样”，已实际读取。独立报告E盘文件完整读取，修前正式SQLite Record→共享B.9→Word矩阵1测试/4subtest失败，4.410s。修后4项正式链测试8.705s全通过：购入/输出、饱和/过热、MPa/C、Pa/K、Pa/C、MPa/K，禁Calculator/Resolver/物性后投影导出，原证据/DB不变、缺未知单位不猜。

生产修复优先本Record方法标记的规范词法，缺该证据时从原值明确单位做显示转换，K减273.15；旧方法路径保留。正在同步文档、按PREFLIGHT机械重生审阅四件套及必要回归。旧CI280及实包仅历史，不背书新代码。代码/文档/制品head后续分别列明；需新全量CI及精确head实际包。

原生Office/真实交互/企业样例/干净目标机/人工正常退出/商业履约OPEN。不CU、不商业发布、不宣布SUPPORTED、不纳入外部CO2/N、不改用户脏树或计算表。完成新回执后送源独立验收并停止。
