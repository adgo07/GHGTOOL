# TASK_STATE

## 当前工作包

G01 领域基础与公共契约（返工）

## 状态

READY_FOR_SOL_ACCEPTANCE

## 验收状态

- G00 验收结论：PASS。
- G01 初次验收：FAILED。
- Sol 指出两项问题：能量单位共用基准错误；领域枚举字段允许原始字符串绕过运行时校验。
- 两项问题已修复并完成返工测试，当前等待 Sol 重新验收 G01。
- 本轮没有开始 G02。

## 已完成

- 将能量单位统一到 kJ 共同基准：`1 kWh = 3600 kJ`、`1 MWh = 3600000 kJ`、`1 GJ = 1000000 kJ`，并验证跨 kWh/kJ 与 MWh/GJ 的双向换算。
- 为所有 G01 领域枚举字段增加运行时实例校验，原始字符串不再被接受；包括问题级别、标准状态、来源类型、审核状态、参数类型、因子值类型、活动数据来源、周期类型、参数选择方法和记录状态。
- 保持 `ValidationProblem.level` 必须是 `IssueLevel`，避免字符串值绕过 ERROR 阻断逻辑。
- 补充能量单位基准回归测试和全部领域枚举原始字符串拒绝回归测试。
- G01 原有 DecimalPolicy、UnitService、领域模型、Repository 契约和 Domain 依赖边界继续通过。
- 已确认 G02 的数据库、Canonical Source、迁移和正式页面工作未开始。
- 已确认 `计算表/` 中 7 个用户参考文件未修改、未纳入 Git。

## 正在进行

- 无。G01 返工已完成，等待 Sol 重新验收。

## 未开始

- G02～G08 全部实施工作；G01 重新获得明确验收结论前不得进入 G02。

## 最后测试

- 针对性命令：`.venv/Scripts/python.exe -m unittest tests.test_g01_decimal_units tests.test_g01_models -v`
- 针对性结果：12 个测试通过，0 个失败，0 个错误，0 个跳过。
- 全量命令：`$env:QT_QPA_PLATFORM='offscreen'; .venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
- 全量结果：18 个测试通过，0 个失败，0 个错误，0 个跳过。
- 依赖核验：`.venv/Scripts/python.exe -m pip check` 输出 `No broken requirements found.`。
- 隔离导入：`.venv/Scripts/python.exe -S` 成功导入 `packages.core`，并验证 `1 kWh = 3600 kJ`。
- 编译核验：`.venv/Scripts/python.exe -m compileall -q packages/core tests` 成功。
- 依赖边界：`packages/core` 未发现 PySide6、sqlite3、Windows API 或 QSql 导入。
- G02 边界：`migrations/`、`data-source/`、`specs/` 无业务标记或实现文件。
- 时间：2026-09-10。

## Git

- 当前分支：`main`。
- 初次 G01 收口提交：`12dc1b2 docs: record G01 acceptance state`。
- 本次修复、回归测试和两份状态文档已形成 G01 返工提交；当前提交后状态为 clean。
- `计算表/`、`tmp/` 和 `.venv/` 仍由 `.gitignore` 保护。

## 已知问题

- 当前没有未解决的 G01 返工项；G01 仅等待 Sol 重新验收。
- G01 不包含 SQLite、Canonical JSON/YAML 数据、正式 UI 页面、GB/T 32151.34 计算规则或报告导出。
- 本机 `py.exe` 未发现已注册的 Python，但项目虚拟环境使用的 Python 3.12.14 x64 已验证可用。
- `D:/MD仓库/杂/碳排放计算软件/资料缺口清单.md` 包含过时状态判断，不作为当前实施基线。

## 阻塞项

- 无。等待 Sol 重新验收 G01。

## 下一步

1. Sol 复核能量单位共同基准和领域枚举运行时校验。
2. Sol 给出 G01 的重新验收结论。
3. 在明确验收通过前保持停止，不进入 G02。
