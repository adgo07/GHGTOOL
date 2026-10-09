# 青舟温室气体排放核算软件

面向 Windows x64 的离线桌面应用，采用 Python 3.12、PySide6/Qt Widgets 与 SQLite。

| 项目 | 当前状态 |
|---|---|
| 当前 Reference Standard | `GB/T 32151.34—2024`（炭素材料生产企业），通用规则层 `GB/T 32150—2025` |
| 当前主要实现标准 | 仅 `GB/T 32151.34—2024` 完整可计算；其余计划标准只有目录与状态信息 |
| 正式支持状态 | **尚未达到正式支持（`SUPPORTED`）状态**；当前处于参考标准产品成熟路线中，路线见 `REFERENCE_STANDARD_ROADMAP.md` |
| Windows 交付 | 已具备 PyInstaller onedir 便携式交付基线与发布审计（尚无 MSI / 安装向导 / 代码签名 / 自动升级） |
| Excel | 附录B九表输入模板、整工作簿预览、Canonical项目保存/恢复及明确正式核算；预览和项目保存不生成Record，核算结果Excel导出已取消 |
| 当前工作包 | `GHG-RS03 — Excel输入项目与正式核算，输出仅保留Word报告`（PR35收口与PR36整合验收） |

## 环境要求

- Windows x64
- Python 3.12 x64
- PySide6（由 `pyproject.toml` 管理）

## 源码安装与启动

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m apps.carbon_accounting_desktop
```

如果系统中存在多个 Python，请确认创建虚拟环境的解释器为 Python 3.12 x64。源码模式下 Catalog 由 `build\databases\catalog.sqlite` 提供；用户记录与日志写入 `%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting`。

## Windows 便携式交付

构建依赖、启动、数据目录、卸载保留、限制与排障说明见 [docs/DELIVERY.md](docs/DELIVERY.md)。

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build]"
.\.venv\Scripts\python.exe scripts\build_standalone.py --clean
.\.venv\Scripts\python.exe scripts\inspect_release.py dist\QingzhouCarbonAccounting
```

发布包不得包含标准全文、`计算表/`、测试数据库、开发文件或密钥。

## 测试与校验

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
.\.venv\Scripts\python.exe -m compileall apps packages scripts tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\validate_canonical.py
```

Windows CI 会安装构建依赖、执行全量测试、校验 Canonical、构建便携式目录并执行发布审计。正式验证证据可来自本地或 GitHub Actions（Windows / Python 3.12）；报告须如实区分来源。

## 范围边界

- 项目保存与 `.qzproj` 是两个不同概念：当前仍不提供 `.qzproj` 可移植项目文件；已支持基于独立 `projects.sqlite` 的本地项目保存、打开和未完成输入恢复。项目/工作区可变状态不写入记录库。
- Excel采用经批准的附录B九表输入模板，下载保留受控模板字节；一份工作簿预览整个核算。显式保存Canonical项目并正式核算成功后追加不可变记录，Word报告读取该记录的冻结快照。旧R2项目及记录证据保持可读；Excel结果导出已取消，Word排版完善延期。审批、云端服务不在当前范围。
- 遇到其他行业活动或上下游运输时只提示需要其他标准，不猜算、不套算、不并入当前结果。
- 不修改、删除或覆盖 `计算表/` 中的用户参考文件。

## 仓库治理

| 文件 | 作用 |
|---|---|
| [AGENTS.md](AGENTS.md) | 本仓长期硬规则与中央治理入口 |
| [REFERENCE_STANDARD_ROADMAP.md](REFERENCE_STANDARD_ROADMAP.md) | 唯一当前产品路线（`GHG-RS01`～`GHG-RS06+`） |
| [HANDOFF.md](HANDOFF.md) | 当前阶段实施交接 |
| [TASK_STATE.md](TASK_STATE.md) | 当前执行状态 |
| [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) | 当前/最近一个工作包的实施报告 |
| [STANDARD_ISSUES_REGISTER.md](STANDARD_ISSUES_REGISTER.md) | 标准问题与解释台账 |
| [PLATFORM_BASELINE.md](PLATFORM_BASELINE.md) / [platform-lock.json](platform-lock.json) | 锁定的中央 Frozen 基线 |
