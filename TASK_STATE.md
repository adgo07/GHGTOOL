# 当前任务状态

状态：VALIDATING — GHG-UI-P3-C 核算记录与报告界面统一
最后更新：2026-10-10

基线事实：启动任务时 origin/main 为 `029ebe6fa6081e3d742ba3900e641e4c4f6aecf0`，其后PR40/PR41合并；最终验收前已整合最新origin/main `4792d30bf0f31a7bb55d5cb5c13e0cae86bd7813`。任务分支为 `codex/ghg-ui-p3-c`。正确origin为`https://github.com/adgo07/GHGTOOL.git`。原工作树另一会话的未提交内容未修改。

已合并前置：P3-AB PR38、RPT02 PR39、EXB01 PR40、P3-DF PR41。中央Frozen锁定SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`不变；本任务不涉及中央公共Contract。无新增Standard Issue或软件解释变化，既有004/007/008保持。

本包仅改记录页Presentation及展示测试/证据。目标：可搜索、可筛选、完整访问的记录列表；独立详情且恰好两个页签；第二页签连续呈现完整输入与计算依据；普通界面无审计详情入口但底层Trace/Provenance/审计保留；删除二次确认和Word公共导出操作继续有效。

保护边界：不改正式Record、Calculator、Canonical、Schema、历史快照、RPT02报告模型/模板/renderer/export helper、新建核算、参数因子库、表格导入和公共Shell。整合主线后重新检查保护文件哈希及非目标页面AST，证据位于`docs/ui/p3-c/evidence/scope-and-rpt02-proof.json`。

最新主线验证：定向回归69/69、完整回归456/456通过，均0失败/错误/跳过；六组Windows原生Qt共115项通过，30张截图和正式Record Word样例已生成；Python3.12.14 compileall退出码0，项目依赖17包兼容。Windows构建与提交后PR head CI尚待执行。自动Qt验证不等同于人工鼠标/键盘/操作系统DPI验收；本PR不得自动合并，不启动P3-E。
