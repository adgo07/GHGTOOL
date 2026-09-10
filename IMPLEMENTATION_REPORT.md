# IMPLEMENTATION_REPORT

## 阶段

G00 工程治理与最小可启动骨架

## 本轮完成

- 按要求完整读取根目录 `AGENTS.md`、`HANDOFF.md` 和 `TASK_STATE.md`，并在开工前完成 Git、磁盘、环境、源码/测试现状核查。
- 创建本地 Git 仓库，分支为 `main`；用 `.gitignore` 明确保护 `计算表/`、`tmp/` 和 `.venv/`。
- 建立 `pyproject.toml`、README、应用/共享包/规范/数据源/资源/迁移/脚本/测试目录骨架。
- 声明 Python 3.12 x64 与 `PySide6>=6.8,<7` 项目依赖，并在隔离 `.venv` 中完成可编辑安装。
- 建立最小 PySide6 窗口，可加载品牌 Logo、启动 Qt 事件循环并正常退出；未实现正式首页或业务页面。
- 将指定品牌源图复制为 `resources/branding/qingzhou_logo.png`；源图与副本 SHA-256 均为 `DB557A6374A928B46BD3AB499C0A295EF147E87D79A273D1FDE1F2D61F8BC24D`，尺寸 3060×759。
- 建立 JSON Lines 结构化日志基础，仅允许受控的事件、组件、结果和错误类型 token，过滤活动数据、企业信息和许可证字段，并在应用退出时释放文件句柄。
- 建立 G00 自动化测试：窗口资源加载与退出、日志敏感字段过滤、目录骨架和核心包无 UI/数据库依赖检查。
- 本轮没有实现 G01 的 `DecimalPolicy`、`UnitService`、领域模型或 Repository 契约，也没有实现数据库、标准规则、正式首页和计算功能。

## 未完成

- 无（G00 MUST 范围内）。
- G01～G08 属于后续阶段，按要求未启动。

## 与 HANDOFF 的偏差

- 无。

## 修改文件

- `.gitignore`
- `pyproject.toml`
- `README.md`
- `TASK_STATE.md`
- `IMPLEMENTATION_REPORT.md`
- `apps/` 下的最小桌面入口、配置和结构化日志模块
- `packages/` 下的共享分层占位包
- `resources/branding/qingzhou_logo.png` 与资源包标记
- `specs/`、`data-source/`、`migrations/`、`scripts/`、`build/`、`docs/`、`tests/` 骨架
- 未修改：`计算表/` 及其 7 个用户参考文件、外部 Logo 源文件、`tmp/`

## 数据与算法说明

- G00 没有数据库业务表、标准参数、排放因子、GWP、计算公式或业务输入。
- Logo 只做二进制副本，不修改外部源文件；项目副本保持原始 4.03:1 比例。
- 日志默认写入 Windows 用户本地应用数据目录的 `logs/application.jsonl`；格式为结构化 JSON Lines，未提供自由文本日志接口。
- 应用配置只包含产品名称、应用版本、日志目录和资源路径；没有项目保存、草稿或用户活动数据存储。

## 测试

### L1

命令：

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

结果：4 个通过，0 个失败，0 个错误，0 个跳过。覆盖最小窗口 Logo 加载/事件循环退出、结构化日志敏感字段过滤、G00 目录骨架和核心包依赖约束。首次运行曾出现 1 个 Windows 临时文件锁错误，加入 `StructuredLogger.close()` 并在应用退出/测试清理时调用后重跑通过。

### L2

命令：

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import sys, PySide6; print(sys.version); print(PySide6.__version__)"
```

结果：`pip check` 无损坏依赖；实际环境为 Python 3.12.14 64 位，PySide6 6.11.2。

### L3

命令：使用 Python 3.12 x64 的 `.venv`，设置 `QT_QPA_PLATFORM=offscreen`，独立创建 `QApplication`、显示 G00 窗口、进入 Qt 事件循环并用一次性定时器退出。

结果：启动、Logo 加载、事件循环和正常退出完成，返回码 0。

## Git

- 分支：`main`
- commit：`7881697 chore: establish G00 desktop skeleton`。
- git status：收口提交后复核为 clean；`计算表/`、`tmp/` 和 `.venv/` 被忽略。

## 已知问题

- 当前窗口是 G00 占位骨架，不代表正式首页；这是 HANDOFF 明确要求的范围。
- 尚未构建安装程序；安装打包属于 G00 OUT OF SCOPE。
- 尚未执行 Windows 10/11 多分辨率/DPI 矩阵和业务回归；分别属于后续桌面外壳或集成阶段。

## 建议 Sol 重点复核

- G00 是否满足“仅建立可启动骨架、不得提前进入 G01”的阶段边界。
- `pyproject.toml` 的 Python 3.12 x64 约束、PySide6 依赖和可编辑安装路径。
- Logo 源图未修改且副本哈希一致；`计算表/` 7 个用户文件未修改、未纳入 Git。
- 结构化日志的 allow-list 是否满足不记录活动数据、企业信息和许可证明文的要求。
