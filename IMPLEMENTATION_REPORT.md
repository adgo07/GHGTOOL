# IMPLEMENTATION_REPORT

## 阶段

G01 领域基础与公共契约

## 验收前提与阶段边界

- 本轮开始前已完整读取根目录 `AGENTS.md`、`HANDOFF.md` 和 `TASK_STATE.md`，并完成 Git、磁盘、环境、源码和测试现状核查。
- 用户已确认 G00 验收结论为 PASS，因此创建本阶段唯一 Goal 并开始 G01。
- 严格按 HANDOFF.md 执行 G01；没有提前执行 G02，也没有创建数据库页面、标准库数据或 G02 计算实现。

## 本轮完成

- 实现纯 Python `DecimalPolicy`：默认 40 位精度，满足至少 28 位要求；拒绝 binary float、bool、非有限值和不严格的十进制文本；内部计算不做显示舍入；默认显示 2 位小数；默认 `ROUND_HALF_UP`，支持显式舍入模式覆盖。
- 实现纯 Python `UnitService`：支持 `kg/t`、`kWh/MWh`、`kJ/GJ`、`Nm³/10⁴Nm³`、比例/百分数和 C/CO₂ 的 44/12 转换；统一进行别名解析、维度检查、可逆换算和不兼容单位报错。
- 实现核心领域类型：`Standard`、`SourceDocument`、`Parameter`、`Factor`、`AccountingInput`、`ValidationProblem`、`CalculationResult`、`ParameterSnapshot`、`AccountingRecord`，以及活动数据、核算周期、排放源选择、设置等配套类型。
- 在领域模型中落实稳定 ID/版本字段、Decimal 规范化、不可变快照和记录、年度/月度周期不变量、ERROR 阻止记录、仅允许 `COMPLETED` 或 `COMPLETED_WITH_WARNINGS` 的记录状态。
- 实现 `StandardRepository`、`ParameterRepository`、`RecordRepository`、`SettingsRepository` 的纯 Python Protocol 契约；测试中使用内存替身验证契约形状。
- 添加 G01 十进制策略、单位服务、领域模型、仓储契约和 Domain 依赖边界测试。
- 保持 Domain 不依赖 PySide6、sqlite3、Windows API、页面控件或桌面弹窗；UI、数据库和公式均未移入 Domain。
- 未修改或纳入 Git 的 `计算表/` 7 个用户参考文件继续保持原状。

## 未完成与后续阶段

- G01 MUST 范围内无未完成项。
- G02～G08 未开始；只有 Sol 明确验收 G01 后才允许进入 G02。
- SQLite、Canonical JSON/YAML 标准/参数数据、标准规则、正式首页、核算页面、报告导出和真实业务输入均按阶段边界保留到后续阶段。

## 与 HANDOFF 的偏差

- 无。

## 修改文件

- `packages/core/decimal_policy.py`
- `packages/core/units.py`
- `packages/core/errors.py`
- `packages/core/models.py`
- `packages/core/repositories.py`
- `packages/core/__init__.py`
- `tests/test_g01_decimal_units.py`
- `tests/test_g01_models.py`
- `tests/test_g01_repositories.py`
- `tests/test_g01_domain_dependencies.py`
- `TASK_STATE.md`
- `IMPLEMENTATION_REPORT.md`

未修改：`计算表/` 及其 7 个用户参考文件、外部 Logo 源文件、G00 桌面骨架和 G00 既有功能。

## 数据与算法说明

- 本阶段没有录入官方标准全文、标准参数、排放因子、GWP 或其他 Canonical Source 数据。
- 本阶段没有创建 SQLite 表、迁移、数据库页面或记录持久化实现。
- 44/12 仅作为 HANDOFF 要求的显式 C/CO₂ 单位换算能力；没有据此实现行业核算公式。
- DecimalPolicy 的中间运算保留 Decimal 精度，最终显示格式化与内部数值分离；UnitService 的换算因子以 Decimal 定义。

## 测试

### L1：G00 回归与 G01 单元测试

命令：`$env:QT_QPA_PLATFORM = 'offscreen'; .venv/Scripts/python.exe -m unittest discover -s tests -t . -v`

结果：16 个测试通过，0 个失败，0 个错误，0 个跳过。覆盖 G00 桌面/日志回归，以及 G01 的严格十进制输入、舍入和显示、单位双向换算与 44/12 桥接、错误/警告问题、模型不变量和不可变记录、Repository Protocol 以及 Domain 依赖边界。

### L2：环境、隔离导入和静态边界

命令及结果：

- `.venv/Scripts/python.exe -m pip check`：`No broken requirements found.`
- `.venv/Scripts/python.exe -S -c "from packages.core import DecimalPolicy, UnitService; ..."`：成功导入核心 Domain，确认无 site-packages 依赖；精度为 40，换算结果为 `1 kg = 0.001 t`（等价于 `1 t = 1000 kg`）。
- `.venv/Scripts/python.exe -m compileall -q packages/core tests`：成功。
- 扫描 `packages/core` 的 `PySide6`、`sqlite3`、Windows API 和 `QSql`：无匹配。
- 检查 G02 边界目录 `migrations/`、`data-source/`、`specs/`：没有非占位实现，没有新增 SQLite、数据库、JSON/YAML 或 SQL 业务产物。

### L3：阶段收口复核

- 使用 Python 3.12.14 x64 项目虚拟环境执行完整测试和上述边界核验，结果均成功。
- Git 工作区在 G01 实现检查点 `1f12608 feat: add G01 domain foundations` 后保持可审计；用户参考文件不在 Git 跟踪范围内。
- 测试时间：2026-09-10。

## Git

- 分支：`main`。
- G01 实现检查点：`1f12608 feat: add G01 domain foundations`。
- 本状态文件和本报告作为 G01 收口文档提交；提交后复核 Git status 应为 clean。

## 已知问题

- G01 有意不提供数据库、标准目录数据、正式 UI、行业核算规则和报告导出；这些不是本阶段缺陷。
- 本机 `py.exe` 未发现已注册的 Python，但项目虚拟环境使用的 Python 3.12.14 x64 已验证可用。
- 外部资料缺口清单包含过时状态判断，不作为当前实施基线；当前基线以根目录 HANDOFF.md、磁盘、Git 和实际测试为准。

## 建议 Sol 重点复核

- `DecimalPolicy` 是否满足精度、禁止 binary float、显示舍入与舍入模式要求。
- `UnitService` 的维度边界、首批单位和 C/CO₂ 44/12 转换是否符合 G01。
- 核心模型的稳定 ID/版本、快照不可变性、ERROR 阻断和记录状态约束。
- Domain 依赖边界及 G02 尚未启动的阶段纪律。
