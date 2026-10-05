# TASK_STATE

状态：GHG-RS03-A-R1 本地实施与验证完成；仍在 PR #27 上，等待本轮提交的 latest-head Windows CI、独立技术验收与用户模板 UAT。更新：2026-10-05。

## 当前工作包与基线

- 仓库：adgo07/GHGTOOL；origin 已核实为 `https://github.com/adgo07/GHGTOOL.git`。
- 工作包：GHG-RS03-A-R1 — Excel 模板简化与用户验收候选版；继续 PR #27，不另建 PR，不合并。
- 分支：`codex/ghg-rs03-a-excel-ingress`；Base / 最新 `origin/main`：`058d176a8a461b758db1a1d62395b032889d9b2a`。
- R1 前 head：`10c13871a4b7d12985b0d9cf8510c5d970b49394`。本轮新 head 和 exact-head CI 以 PR #27 当前 head 与 `IMPLEMENTATION_REPORT.md` 的最终记录为准。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定 SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 未升级。
- Contract 预检查：Architecture V2.1、Numeric Contract v1、Numeric Profiles v1 按锁定版本为 Frozen；Excel / openpyxl Decimal 词法互操作仍为中央 OPEN。本包继续使用本地入口策略，不升级 baseline / platform-lock，不定义中央 Contract。
- 标准治理：沿用冻结 Mapping 与已批准口径；不改变标准解释、计算公式或适用范围；无新增 Standard Issue。标准仍为 `NOT SUPPORTED`。

## R1 范围

- 将用户模板收敛为四个可见页签：填写说明、核算单元、燃料与能源、过程排放；模板版本元数据保留在隐藏页。
- 业务区域按标准条款分组；物料、电力和热力逐行录入并进入既有 Domain / Calculator；不创建 Excel 公式算法或新 reference-table 架构。
- 从数据派生排放源状态；单元错误隔离；预览包含排放源分项、直接排放、净间接排放和总排放。
- 用户验收候选 `.xlsx` 由最终代码生成至忽略的本地构建目录，不提交仓库。
- 本轮不进入 RS03-B 的 Project / Record 正式导入闭环，不合并 PR #27。

## 停止边界

`RS03-A-R1 IMPLEMENTED`、`TECHNICAL ACCEPTANCE PENDING`、`USER TEMPLATE UAT PENDING`；只有技术独立验收与用户模板 UAT 完成后再考虑 RS03-B。`RS03-B NOT STARTED`，GB/T 32151.34—2024 继续 `NOT SUPPORTED`。
