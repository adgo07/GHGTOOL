# GHG-UI-P3-C 验收记录

状态：本地验证、Windows构建及PR #42 run 198通过；等待独立验收。当前PR head的CI状态以PR Checks为准。

## 基线与范围

- 启动时main：`029ebe6fa6081e3d742ba3900e641e4c4f6aecf0`。
- PR40/PR41在任务执行期间合并；验证基线：`4792d30bf0f31a7bb55d5cb5c13e0cae86bd7813`。
- 只改记录页Presentation与对应测试/证据；正式Record和Word业务实现不改。
- RPT02公共导出一致性与保护文件证据见`evidence/scope-and-rpt02-proof.json`。

## 验收场景

| 场景 | 目标 | 状态 |
|---|---|---|
| 列表 | 搜索、状态筛选、全部记录可访问、可键盘进入 | 已通过 |
| 详情 | 独立只读页面；两个指定页签；第二页签连续内容 | 已通过 |
| 审计与删除 | 普通界面无审计详情入口；取消删除不变；确认删除保留审计 | 已通过 |
| 快照与Word | 展示冻结依据；复用RPT02公共Word入口；不回算/不改快照 | 已通过 |
| Windows界面 | 六组尺寸/缩放原生Qt自动检查，截图与Word样例 | 115项通过；人工作业系统DPI仍需独立确认 |
| 全量与打包 | 本地456/456通过；PR #42 run 198 merge-ref全量、UIR04、PR-head构建/审计、ZIP往返及2次smoke全通过 |

## 屏幕与文档证据

本目录现有30张记录列表、搜索、结果摘要和连续依据页签截图，六份Windows Qt检查JSON，以及`P3-C_FormalRecord_Appendix_B.docx`。六组共115项均通过。演示Record由正式Application创建，仅用于界面与报告链验收，不代表企业实测数据；公共导出Word与相同RPT02模型和renderer的参考Word主体XML一致，导出前后Record快照及数量不变。

## 遗留验收边界

原生人工鼠标/键盘操作与Windows系统DPI切换未由自动脚本完成；PR38/39既有独立验收中的OPEN事项不冒充本包已关闭。本地定向回归69/69通过，全量回归456/456通过（均0失败/错误/跳过），Python3.12.14；项目环境17包依赖兼容，compileall退出码0。Windows standalone构建来源提交6ad85afc123dc3e09e8f0cd87147f885ad65155f：PyInstaller 6.22.3，264文件构建PASS，审计PASS，265文件ZIP往返PASS，2次隔离启动PASS。GitHub run 198在head 7023b279624fbc75a1a41ba7d01320b3cc8e15a0通过：merge-ref全量456项、UIR04、exact-head standalone构建及审计均PASS；产物source_commit与PR head一致。PR最新head的检查持续以GitHub状态为准。
