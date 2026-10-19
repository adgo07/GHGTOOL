# 当前任务状态 — B-HEAT / PR52-F01

更新：2026-10-19。状态：READY_FOR_INDEPENDENT_ACCEPTANCE；修复、新CI/实际包已完成，待源最终独立验收。

产品补丁提交dea45cd8c198d74d22d10a371696c62c01312856，完整受验代码/制品head `1843157a8bc9d78fa442c93b4094a076f562d788`（184补齐Mapping定义绑定）；CI283实际merge `f083dd6caeed54bb5e7c2ee0a4b92cc8565bb298`。最终文档回执head为本提交（以PR52最新head为准），增量只含文档/原始证明，不能把184制品改标为回执head。

## 平台 / Contract 预检查

业务base `a1aeebc1b6809397e61a2ffa7a2333a3b440c756`，工作树origin实际核实为adgo07/GHGTOOL且已fetch；当前任务分支codex/b-heat-integration。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，相关Frozen为Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；ACTIVE UI指南按中央正式main适用版读取。MUST：分层、共享Application、declared-profile consistency、ambient independence、full-value exact、原输入/规范/物性工作/显示值分开、Record/Word冻结。MUST NOT：业务epsilon、显示修约回流、隐式物性回退、Qt状态充当公共Workspace、自动升级Frozen。Carbon Decimal40/ROUND_HALF_UP是ALLOWED PROJECT DIFFERENCE；binary64物性子Profile单独声明，不冒称p40物性精度。C3资格漏项、工作Pa/K门禁不足均LOCAL DEFECT，不需改中央Contract。相关Standard Issue005/006/015/017/019；本包执行已经批准的软件决定，没有新增标准解释、标准范围或Frozen变更。

F01是共享冻结显示投影LOCAL DEFECT，不改中央Contract、公式、物性Profile、DB或专业解释，非新增Standard Issue；关联017既有方法/Record约束。读已锁Architecture/Numeric，显示换算不得回流正式值。


## 新CI与实际包证据

产品补丁提交dea45cd8c198d74d22d10a371696c62c01312856，完整受验代码/制品head `1843157a8bc9d78fa442c93b4094a076f562d788`（184补齐Mapping定义绑定）；CI283实际merge `f083dd6caeed54bb5e7c2ee0a4b92cc8565bb298`。最终文档回执head为本提交（以PR52最新head为准），增量只含文档/原始证明，不能把184制品改标为回执head。

[CI283/run39264926043](https://github.com/adgo07/GHGTOOL/actions/runs/39264926043)整体SUCCESS；merge-ref job118101913478全量 `python -m unittest discover -s tests -t . -v`：**1014/1014，1695.552s，零失败/错误，skipped=0**。exact-head job118117880702执行 `python -m unittest tests.test_g08_delivery -v`：**18/18，12.315s**；Canonical/编译/pip check/数据库/UIR04/缩放/构建/审计/ZIP/provenance/2隔离启动通过。这是GitHub Actions实际证据，不是本地执行。

实际artifact **12195361432**，ZIP SHA256 **b1febe11d53271ea798a027a89ea5b27c853f3cb9a0772d064c7b9d2842549f7**，75710032bytes；manifest321文件、ZIP322文件。下载后逐文件size/SHA、许可原文/来源清单与PE x64核验通过；source_commit/pr_head均184、tested_merge为上述merge。C本地对这个实际CI包审计/ZIP回读/2启动及 `python -B docs/ci/B_HEAT_PACKAGE_VERIFIER.py <实际CI包> <全新输出> 1843157a8bc9d78fa442c93b4094a076f562d788 <实际CI273旧数据>` 通过，exit0，无nanobind/Traceback；从实际EXE/PYZ及包内CP/NP/Qt读取，禁止业务源码回退。6组单位/相态双方向正式Record→B.9→Word、冻结禁Calculator/Resolver/物性、原证据不变及既有完整热力链均通过。完整证明B_HEAT_F01_CI_PACKAGE_PROOF.json、B_HEAT_F01_CI_RECEIPT_PROOF.json。

同一增强验证器对真实旧CI280包exit1，准确抓Pa/K报告3500.00/300.00错误，负例完整日志入B_HEAT_F01_CI280_NEGATIVE_PROOF.json；本地184新包也exit0、无诊断，但仅是LOCAL_BUILD，单独保留B_HEAT_F01_LOCAL_PACKAGE_PROOF.json，不冒称CI。实际CI273旧模型/Word比较显式固定同次导出编制日期2026-10-18，业务证据和旧正文不漂移，原DB不变；编制日期是导出补充信息，不回写Record。

源已独立运行本轮4项正式链测试4/4、7.962s，定向F01通过，不替代最终新包独立验收。新旧重叠套件不相加。旧CI280整体1010/18通过及原B-HEAT证据只作历史，796技术PASS已撤回，不能背书本补丁。

完整实现、必要本地回归、机械审阅四件套保留性及所有失败对账见IMPLEMENTATION_REPORT和B_HEAT_F01_*PROOF.json。旧796技术PASS撤回，旧CI280/fca只历史。当前独立最终验收待完成，不合并、不开始下一包；原生/企业/目标机/商业履约OPEN。
