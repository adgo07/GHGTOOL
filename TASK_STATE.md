# 当前任务状态

状态：WAIT_INDEPENDENT_ACCEPTANCE — GHG-UI-P3-AB（Shell + 标准库联合改造）
最后更新：2026-10-09

PR #37 已合并，最新 main baseline 为 `708f78a455790946b4a728029bba768d8fb295fc`；独立分支 `codex/ghg-ui-p3-ab`。A、B 实施及独立复核完成，交付单一 PR，不自行合并。最终 head 与 Windows CI 结果以 PR body / checks 为准；本状态提交时 CI 待运行，需完成最终 head 验证后交付。

A 定向9/9后进入B，保护回归68/68，B最终22/22。AB代码快照全量404项：403通过、1临时SQLite文件清理错误；补充DeferredDelete/gc严格清理后相关模块5/5。不得描述为本地全量通过。Canonical、编译、依赖、四库初始化、自动五场景、三档Qt缩放、standalone构建/审计/ZIP/两次启动通过；六组离屏90/90、24PNG+6JSON。命令、数量、前序失败及证据来源见 IMPLEMENTATION_REPORT.md 与 docs/ui/p3-ab/ACCEPTANCE.md。

修改限定于Presentation、相关测试、截图和治理记录；RecordLibraryPage及因子库类不变，ExcelImportPage仅标题。正式业务输入、项目保存恢复、Calculator、Record、解析、报告、Canonical和Frozen基线不变。locked central仍为 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。

RPT02开工时BLOCKED，交付前已在独立codex/ghg-rpt02工作树恢复；当前业务文件无交集，TASK_STATE等治理文件可能冲突，不取未合并代码。EXB01未找到启动证据。用户参考文件及其他工作树保留。

原生Windows两种分辨率、100%/125%/150%系统DPI的人工操作验收仍OPEN：工具初始化失败；Qt离屏不替代原生。AB完成并合并后Phase3暂停，C/D/E/F按新任务及EXB01/RPT02真实状态另行开展，本轮不实施。
