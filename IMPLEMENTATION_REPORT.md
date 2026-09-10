# IMPLEMENTATION_REPORT

## 阶段

G01 领域基础与公共契约（返工）

## 初次验收结论

- G00 已获 PASS。
- G01 初次验收失败，Sol 指出：
  1. `kWh/MWh` 与 `kJ/GJ` 被错误地分别按数值 1 作为同一能量基准，跨体系换算结果错误。
  2. 多个 `str, Enum` 字段缺少运行时实例校验，原始字符串可进入领域对象；其中 `ValidationProblem.level` 可能绕过 ERROR 阻断判断。
- 本报告记录上述返工，不代表已进入 G02。

## 本轮完成

- 修复能量单位基准：统一以 kJ 为能量维度共同基准，定义 `1 kWh = 3600 kJ`、`1 MWh = 3600000 kJ`、`1 GJ = 1000000 kJ`，因此 `1 MWh = 3.6 GJ`，并保持同量纲换算可逆。
- 修复领域枚举字符串绕过：增加统一运行时枚举实例校验，所有 G01 领域枚举字段拒绝等值原始字符串；`ValidationProblem.level` 也必须是 `IssueLevel` 实例。
- 覆盖的枚举字段包括标准状态、来源类型、审核状态、参数类型、因子值类型、活动数据来源、核算周期类型、参数选择方法、记录状态和问题级别。
- 增加能量跨体系换算回归测试，以及覆盖全部枚举字段的原始字符串拒绝回归测试。
- 保持 Domain 纯 Python，不引入 PySide6、sqlite3、Windows API 或新的主要依赖。
- 未进入 G02，未创建数据库页面、Canonical Source、迁移、标准目录数据或计算规则。
- 未修改或纳入 Git 的 `计算表/` 7 个用户参考文件继续保持原状。

## 未完成

- G01 返工范围内无未完成项。
- G01 重新验收尚未完成，等待 Sol 给出新的验收结论。
- G02～G08 未开始。

## 与 HANDOFF 的偏差

- 本次返工是对初次 G01 验收失败项的纠正，不改变 HANDOFF 的阶段范围或技术边界。
- 无新增 Scope；仍未实施 G02。

## 修改文件

- `packages/core/units.py`
- `packages/core/errors.py`
- `packages/core/models.py`
- `tests/test_g01_decimal_units.py`
- `tests/test_g01_models.py`
- `TASK_STATE.md`
- `IMPLEMENTATION_REPORT.md`

未修改：`计算表/` 及其 7 个用户参考文件、外部 Logo 源文件、G00 桌面骨架和 G01 其他未涉及实现。

## 数据与算法说明

- 本轮没有录入官方标准全文、标准参数、排放因子、GWP 或其他 Canonical Source 数据。
- 本轮没有创建 SQLite 表、迁移、数据库页面或记录持久化实现。
- 能量换算常数集中在 `UnitService` 的单位定义中，不再把 kWh 和 kJ 当作同一基准；没有在页面或数据库中散落换算逻辑。
- 44/12 C/CO₂ 换算保持不变，仅作为 G01 要求的显式单位桥接能力。

## 测试

### L1：针对性返工回归

命令：`.venv/Scripts/python.exe -m unittest tests.test_g01_decimal_units tests.test_g01_models -v`

结果：12 个测试通过，0 个失败，0 个错误，0 个跳过。新增测试验证 `kWh↔kJ`、`MWh↔GJ` 跨共同基准换算，以及 ValidationProblem、Standard、SourceDocument、Parameter、Factor、ActivityData、AccountingPeriod、ParameterSnapshot、AccountingRecord 的原始字符串枚举输入均被 `DomainValidationError` 拒绝。

### L2：全量回归与边界核验

命令及结果：

- `$env:QT_QPA_PLATFORM='offscreen'; .venv/Scripts/python.exe -m unittest discover -s tests -t . -v`：18 个通过，0 个失败，0 个错误，0 个跳过。
- `.venv/Scripts/python.exe -m pip check`：`No broken requirements found.`
- `.venv/Scripts/python.exe -S -c "from packages.core import DecimalPolicy, UnitService; ..."`：成功在无 site-packages 环境导入 Domain，并验证 `1 kWh = 3600 kJ`。
- `.venv/Scripts/python.exe -m compileall -q packages/core tests`：成功。
- 扫描 `packages/core` 的 PySide6、sqlite3、win32、winreg、QSql：0 个匹配。
- 扫描 `migrations/`、`data-source/`、`specs/` 的 G02 业务标记：0 个匹配。
- `git ls-files -- 计算表/**`：0 个跟踪文件；参考表仍被 `.gitignore` 忽略。

### L3：返工收口复核

- 完整测试、依赖检查、隔离导入、编译和边界扫描均已真实执行并成功。
- 针对性测试和全量测试均没有失败、错误或跳过项。
- 未执行数据库迁移、Canonical 数据构建、GUI 新页面、Windows 安装包和 G02 验收；这些属于后续阶段或被本轮明确禁止。
- 测试时间：2026-09-10。

## Git

- 分支：`main`。
- 初次 G01 收口提交：`12dc1b2 docs: record G01 acceptance state`。
- 本次修复代码、回归测试、`TASK_STATE.md` 和本报告已形成 G01 返工提交。
- 返工提交后已复核 Git status 为 clean。

## 已知问题

- 当前没有未解决的返工缺陷；G01 仍等待 Sol 重新验收。
- G01 有意不提供数据库、标准目录数据、正式 UI、行业核算规则和报告导出。
- 本机 `py.exe` 未发现已注册的 Python，但项目虚拟环境使用的 Python 3.12.14 x64 已验证可用。

## 建议 Sol 重点复核

- 能量单位是否均以 kJ 为共同基准，特别是 `1 kWh = 3600 kJ` 和 `1 MWh = 3.6 GJ`。
- 所有领域枚举字段是否拒绝原始字符串，且 `ValidationProblem.level` 不再绕过 ERROR 记录阻断。
- 新增针对性回归测试和 18/18 全量测试结果。
- 本次返工是否保持 G01 范围且没有提前进入 G02。
