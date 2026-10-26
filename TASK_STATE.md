# UI 设计资料整理完成

2026-10-26：按 Owner 明确指令合并 PR #60，合并提交 `6fc5909646b855494abee55cff6fd95f8d18b4be`。合并前精确 head 的两个 required Windows checks 均 success；合并不等于补做源独立验收或关闭原生/Release缺项。

本次从最新 origin/main 创建 `codex/ui-reference-design`，完成 [碳排放软件 UI 设计参考](docs/ui/GHGTOOL_UI_DESIGN_REFERENCE.md)，供 ECQuota-Insight、EquipEffi 后续设计使用。范围为资料、来源和现状整理，不改变产品代码、计算口径、标准支持状态或中央 lock。新建核算后续整页改进未实施。原 PR60 实施报告保留在 [历史报告](docs/ui/reference-baseline/PR60_IMPLEMENTATION_REPORT.md)。本次检查见 IMPLEMENTATION_REPORT.md；资料送独立审阅后停止，不自动实施另外两个软件。

下列为 PR60 合并前交接原文，保留待办与证据；其中“未合并”已被上述 Owner 操作取代，不代表当前 PR 状态。

---
# PR60五页收口候选：待源独立验收

产品代码 `fb56ad737b6d0a676e5f594f689e08e88f14aaa3`，origin `adgo07/GHGTOOL`，分支 `codex/ui-five-business-pages-v2`。本地裸字体完整运行 **1121通过/1失败，5371.075s**，受控代码/测试/资源前后hash不变；astra r3限定视觉PASS（92图/29源、回调异常0、四项HOLD关闭）。证据及失败/中止记录见IMPLEMENTATION_REPORT和docs/ui/business-pages-v2/refinements-r3。字体环境复现与QA前置修正后21/21（119.918s）另列，测试断言与产品源码不变；旧完整结果不改标。原始大文件独立保留，旧版本不覆盖、不改标。

已收口：普通记录冻结业务依据与旧记录回退、B2/B8/B9脚注呈现、导入四区/重检/已保存上下文、本次及历史记录分别查看、成功主查看、来源长名/短搜索详情、紧凑记录与局部宽表、路径起点、局部勾选状态。保留原启动日志OSError安全退出；真实用户路径访问原因仍未确定，不改用户数据/ACL。Application/Domain/Adapter/DB/受控母版/Word及中央锁均不变；本任务不涉及中央公共 Contract，无标准解释变化。

工程流水线与精确候选包结果、正式最新PR head以PR60及最终交付回执单独锁定；不得复用e336/CI309/旧包替代当前版本。验收顺序为本地稳定验证→同head required CI→真实精确包及本地审计/隔离启动→源独立验收。源验收未完成，PR保持未合并、不发布。原生桌面、真实用户路径负例、IME/Office/人工DPI/企业样例/干净机仍未执行。

后续独立新建核算范围尚未实施：手动访问未启用8源卡才启用，已启用仅浏览；程序导航/错误定位/恢复不启用；外部CO₂第九卡为软件补充，访问不自动同意边界声明；未来标准仅产品计划。含碳量数据来源不混同HEAT_CONTENT/DIRECT路径；电力五表/OTHER/零/候选冲突/无适用不回退保留。热力Owner已批准常用入口简化、特殊情况可展开、旧值保留，内部/输出不得强改外购、015防重复计碳及未知边界不变、不因折叠改dirty或强写默认。当前先完成PR60独立验收，不重复问同一决定。
