# PR-B：C＋A 三业务区布局已实施，待视觉验收

Owner 已确认紧凑对齐样板。本轮将布局接入实际核算页，仅限燃料、电力、原料煅烧；保留应用侧栏、项目区、其他业务区和正式计算入口。未 push、未建 PR、未触发 CI、未启动原生桌面。

- 排放源目录只切换查看，不改变启用状态或输入。启用仍需显式操作；错误定位会打开对应目录。
- 燃料三列分组，实测报告同排对齐；电力方向与来源、煅烧来源采用轻量单选外观。选项仍来自原 combo/业务规则。
- 煅烧新增和恢复条目使用同一布局；换算区域保留。编辑区固定起点、内部滚动。
- 真实页面截图及捕获记录：`docs/ui/ca-layout/review.html`、`summary.json`。捕获来自本地工作区，以父提交、脚本和源文件哈希绑定，不冒充精确提交制品。

验证详见 `IMPLEMENTATION_REPORT.md`。原生鼠标/IME/系统 DPI、Office、企业样例与交付门仍 OPEN。下一步先检查本轮实际页面效果，再决定 PR-B 后续推广；不自动扩大到其他业务区。

## 平台 / Contract 预检查

本仓 origin 已核实为 `adgo07/GHGTOOL`，已 fetch；复用隔离分支 `codex/ui-business-layout`，基线含 PR58 合并。中央 Frozen lock `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，已读当前 UI 指南 v0.2。本任务不涉及中央公共 Contract；不改变标准解释、来源资格、Calculator、Canonical 或 Record，无新增 Standard Issue。
