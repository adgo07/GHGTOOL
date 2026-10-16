# 当前任务状态 — PR47 合并前有限小修

> 更新：2026-10-17。当前为既有 PR47 的合并前有限小修；本次有限小修包括两个 JSON 的 base / 11 个 basis 人读澄清、现有 HTML 范围提示、checks 生成脚本入仓与复现步骤，以及状态、交接与语义范围文档同步；审阅产物已按当前源定义同源重生，最终哈希与新 head / CI 由送验评论定位。候选尚未接入生产，PR47 未合并。已核验修复基线为 4e7306992335e213fc0c3baf897022dd174e3acf；本次有限小修形成的新 head 与 CI 待最终送验评论确认，以下旧证据不为新 head 背书。

## 仓库身份与平台 / Contract 预检查

- 实际 origin 为 https://github.com/adgo07/GHGTOOL.git；分支 codex/ghg-business-rules-a；开工 HEAD 为 4e7306992335e213fc0c3baf897022dd174e3acf，开工时工作区干净。origin/main 已同步至 b0c1aa723391772f9aef026b4c0a8619eb61a65b。
- platform-lock.json 锁定中央 SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20，未修改。本任务不涉及中央公共 Contract；既有 Frozen MUST / MUST NOT 继续适用，无冲突、无中央变更。
- Standard Issue：本次没有新建、关闭或重释问题条目。修改只记录 Owner 已批准的审阅范围减负决定；不改变标准事实、Mapping 或既有软件解释。
- 当前状态文件只保留唯一执行入口；历史过程由 Git history 恢复，不另建归档文档。

## 当前有限小修验证

- 本地 Python 3.12 七模块联合：100/100通过，0 failure、0 error，20.402秒；正式交付路径资产测试20/20通过，14.136秒。命令及范围见 IMPLEMENTATION_REPORT.md。
- 当前同源投影、工作簿、HTML、目录快照、manifest 和夹具绑定通过；25/25本地 ArtifactTool 意见回收场景通过。新增 Python CLI 回归不依赖 Node，验证实际 Canonical 输入、意见保留和错误投影/技术摘要/HTML/意见范围的拒绝。
- 61行（29/21/11）、649技术组合（281 READY/368 BLOCKED）、442唯一意见范围保留；没有新增固定条数门禁。原批准V1.2和历史电力证据字节未改。
- 独立 Luna/max 静态复核无剩余阻断；其发现的混源HTML检查缺口已修并重跑。Git diff --check通过，仅CRLF标准化提示。
- 新 head 的 Windows CI 尚待最终送验评论确认；旧CI237不为本次背书。无本地完整构建/全软件重验声明。

## 当前待交付与停止边界

- 本次小修的新 head、对应 CI 和最终送验评论仍待确认；不得沿用 4e730699 的 CI 为新 head 背书。
- EXB01 输入 Adapter 原生 Excel / WPS 保存后回导仍未验证，按路线 RS03 单独跟踪；与本次审阅表 Office 检查分开，不能由其延期状态一并豁免。
- 原生 Office 审阅表验证状态为 NOT_RUN / DEFERRED，延期至下一阶段首次正式使用审阅表之前。届时只做原生打开、填写意见、按表头排序、保存后重开、回收意见的小范围检查；不记为通过或豁免。CU Esc 仍有效，不自动启动 computer use，也不由此要求全软件重验。
- 已批准的标准事实与软件决定继续由 Mapping / 问题台账表达；PR47 的规则候选、审阅投影及消费者替换仍未接生产，不宣称正式标准支持。
- 正式 Record、历史兼容入口和计算表/中的用户参考文件继续保护；不改历史 Record，不破坏既有兼容。
- PR47 不由执行代理合并；最终合并由源会话负责。PR46、B、N 均未获启动授权。
