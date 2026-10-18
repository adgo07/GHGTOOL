# B-HEAT 当前交接

更新：2026-10-18。状态：READY_FOR_INDEPENDENT_ACCEPTANCE。

受验代码及实际制品head：`fca06e14a8526a968c27e3859888205079729864`；CI280 merge：`d21e84149b2110051e3d6e2da46e52e7a2ac8a99`。本回执提交只同步文档/证明，最新文档head以PR52为准，不能把制品来源改标为文档head。私有[PR52](https://github.com/adgo07/GHGTOOL/pull/52)保持OPEN、未合并。

最新实际CI280全量1010/1010，1912.733s；精确head G08 18/18，11.422s。构建/包审计/清单/provenance/2启动通过。实际下载CI包验证器退出0并通过共享热力链、工作状态折叠阻断、相邻合法值、旧CI273冻结记录/Word不漂移；完整身份/命令/失败对账见IMPLEMENTATION_REPORT.md、B_HEAT_SUMMARY.json和B_HEAT_CI280_RECEIPT_PROOF.json。

业务base `a1aeebc1b6809397e61a2ffa7a2333a3b440c756`，工作树origin实际核实为adgo07/GHGTOOL且已fetch；当前任务分支codex/b-heat-integration。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，相关Frozen为Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；ACTIVE UI指南按中央正式main适用版读取。MUST：分层、共享Application、declared-profile consistency、ambient independence、full-value exact、原输入/规范/物性工作/显示值分开、Record/Word冻结。MUST NOT：业务epsilon、显示修约回流、隐式物性回退、Qt状态充当公共Workspace、自动升级Frozen。Carbon Decimal40/ROUND_HALF_UP是ALLOWED PROJECT DIFFERENCE；binary64物性子Profile单独声明，不冒称p40物性精度。C3资格漏项、工作Pa/K门禁不足均LOCAL DEFECT，不需改中央Contract。相关Standard Issue005/006/015/017/019；本包执行已经批准的软件决定，没有新增标准解释、标准范围或Frozen变更。

等待源独立验收；不自行合并、不启动下一包、不纳入M外部CO₂、不改PR49/50/51。原生Office、鼠标/中文IME/人工DPI、企业真实样例、干净目标机和商业许可履约OPEN；程序化Qt离屏/ArtifactTool可读性不替代原生验收。不CU、不商业发布、不宣布SUPPORTED，不改Frozen/路线/用户原脏树/计算表。

完整原始证明见docs/ci/B_HEAT_*PROOF.json及B_HEAT_IF97_CANDIDATE*_RAW.json；本次CI实际日志和本地全部执行日志在tmp/b-heat保留，摘要不隐藏失败。nanobind退出诊断与退出码/条件的最小核查见B_HEAT_EXIT_DIAGNOSTIC_PROOF.json。
