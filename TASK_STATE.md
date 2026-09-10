# TASK_STATE

## 当前工作包

G01 领域基础与公共契约

## 状态

READY_FOR_SOL_ACCEPTANCE

## 验收前提

- 用户已明确确认 G00 验收结论为 PASS。
- 已创建且仅创建本阶段 G01 Goal。
- 本轮仅执行 HANDOFF.md 的 G01；没有提前执行 G02。

## 已完成

- G00 工程治理、目录骨架、依赖配置、最小 PySide6 空应用、Logo 副本、结构化日志基础和 G00 测试已完成并获 PASS。
- 已实现纯 Domain 层 `DecimalPolicy`：默认 40 位精度（满足至少 28 位要求）、严格十进制输入、禁止二进制浮点输入、内部不做显示舍入、默认显示 2 位小数，并支持标准要求的舍入模式覆盖；默认 `ROUND_HALF_UP`。
- 已实现纯 Domain 层 `UnitService`：`kg/t`、`kWh/MWh`、`kJ/GJ`、`Nm³/10⁴Nm³`、百分数/比例，以及 C/CO₂ 的 44/12 转换；包含单位维度和不兼容单位校验。
- 已实现核心领域模型：Standard、SourceDocument、Parameter、Factor、AccountingInput、ValidationProblem、CalculationResult、ParameterSnapshot、AccountingRecord 及所需周期、活动数据、设置等类型。
- 已实现领域不变量：稳定 ID/版本字段、十进制值规范化、不可变快照/记录、年度/月度周期约束、ERROR 阻止记录、记录状态仅允许 `COMPLETED` 或 `COMPLETED_WITH_WARNINGS`。
- 已实现 Standard/Parameter/Record/Settings Repository 的纯 Python Protocol 契约，并以测试替身验证接口形状。
- 已添加 G01 的十进制、单位、模型、仓储契约和 Domain 依赖边界测试。
- 已确认 G02 的数据库、Canonical Source、迁移和正式页面等工作未开始。
- 已确认 `计算表/` 中 7 个用户参考文件未修改、未纳入 Git。

## 正在进行

- 无。G01 已完成，等待 Sol 验收。

## 未开始

- G02～G08 全部实施工作；必须在 G01 获得 Sol 验收后才能进入 G02。

## 最后测试

- 命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
- 结果：16 个测试通过，0 个失败，0 个错误，0 个跳过。
- 依赖核验：`.venv/Scripts/python.exe -m pip check` 输出 `No broken requirements found.`。
- 隔离导入：`.venv/Scripts/python.exe -S` 成功导入 `packages.core`，确认 Domain 可在无 site-packages 环境下加载。
- 编译核验：`.venv/Scripts/python.exe -m compileall -q packages/core tests` 成功。
- 依赖边界：`packages/core` 未发现 PySide6、sqlite3、Windows API 或 QSql 导入；G02 边界目录无非占位实现。
- 时间：2026-09-10。

## Git

- 当前分支：`main`。
- G01 实现检查点：`1f12608 feat: add G01 domain foundations`。
- 本文件与 `IMPLEMENTATION_REPORT.md` 将在 G01 收口提交中更新；提交后须复核状态为 clean。
- `计算表/`、`tmp/` 和 `.venv/` 仍由 `.gitignore` 保护。

## 已知问题

- G01 不包含 SQLite、Canonical JSON/YAML 数据、正式 UI 页面、GB/T 32151.34 计算规则或报告导出；这些均不属于本阶段。
- 本机 `py.exe` 未发现已注册的 Python，但项目虚拟环境使用的 Python 3.12.14 x64 已验证可用。
- `D:/MD仓库/杂/碳排放计算软件/资料缺口清单.md` 包含过时状态判断，不作为当前实施基线。

## 阻塞项

- 无。等待 Sol 验收 G01。

## 下一步

1. Sol 验收 G01 并给出 PASS、PASS WITH MINOR FIXES 或 BLOCKED。
2. 在 G01 获得明确验收结论前，不进入 G02。
