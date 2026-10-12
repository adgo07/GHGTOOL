# 当前任务状态

状态：GHGTOOL HTML V4 正式落地 — PR1 已合并（PR #44）；PR2 独立 PR #45 已创建，等待 Windows CI 与最终视觉验收。

最后更新：2026-10-12。工作分支：`codex/ghg-html-v4-pr2`；基线为 `origin/main@204dded5d03853617f79a1f05693e89b619df9d1`。原 `codex/ghg-ui-p3-df` 脏工作区保持未动。

- Owner 已确认首页样板；已按反馈移除入口卡片上方的小字，并用隔离项目/Record夹具确认“继续工作”和“最近核算”展示实际内容。
- 首页样板已按 Owner 意见移除卡片上方小字；有真实临时 Project/Record 的截图确认“继续工作”和“最近核算”均显示具体内容。
- 公共页面沿用中性标准文案；标准分发仅允许 `STANDARD_ID` 进入炭素材料专属核算页。记录列表改为 V4 七列表，记录详情保持两个页签；八类源卡片为炭素材料模块专属四列布局。
- 全页 Windows Qt 截图和 HTML→Qt 映射说明位于 `docs/ui/v4-evidence/` 与 `docs/ui/HTML_V4_QT_MAPPING.md`。已检查 1600×900、1366×768、1920×1080；当前环境 DPR 1.0 / 96 logical DPI，125% Windows 设置未更改或伪称已验收。
- 定向回归 84 项通过，后续相关复测 6 项通过；GitHub Windows 全量测试与 standalone CI 等待 PR 触发。
- 本任务未修改 Frozen Contract、计算语义、Excel 导入规则、数据库 Schema 或正式报告业务；PR2 独立提交，不自动合并。原 `codex/ghg-ui-p3-df` 脏工作区保持未动。

中央 Frozen baseline 继续锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。
