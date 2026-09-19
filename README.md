# 青舟温室气体排放核算软件

青舟温室气体排放核算软件是面向 Windows x64 的 V1 桌面应用，采用 Python、PySide6/Qt Widgets 和 SQLite。当前交付链覆盖 GB/T 32150—2025 通用规则及 GB/T 32151.34—2024 炭素材料生产企业模块；其他标准仅维护目录和状态信息。

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

如果系统中存在多个 Python，请确认创建虚拟环境的解释器为 Python 3.12 x64。源码模式下，Catalog 由 `build\databases\catalog.sqlite` 提供；用户记录和日志写入 `%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting`。

## Windows 便携式交付

G08 使用 PyInstaller `onedir` 构建便携式目录。构建依赖和启动、数据目录、卸载保留、限制及排障说明见 [docs/DELIVERY.md](docs/DELIVERY.md)。快速构建命令：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build]"
.\.venv\Scripts\python.exe scripts\build_standalone.py --clean
.\.venv\Scripts\python.exe scripts\inspect_release.py dist\QingzhouCarbonAccounting
```

当前没有 MSI、安装向导、代码签名或自动升级服务。发布包不得包含标准全文、`计算表`、测试数据库、开发文件或密钥。

## 测试与校验

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
.\.venv\Scripts\python.exe -m compileall apps packages scripts tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\validate_canonical.py
```

Windows CI 会安装构建依赖、执行全量测试、校验 Canonical、构建便携式目录并执行发布审计。G08 不实施 G09 的功能或页面。

## 范围边界

- 不向用户提供 `.qzproj` 项目文件、项目保存、草稿、审批状态或恢复未计算输入。
- Excel 导入只保留禁用入口和占位说明；报告/导出、企业档案完善和云端服务暂不实施。
- 遇到其他行业活动或上下游运输时只提示需要其他标准，不猜算、不套算、不并入当前结果。
- 不修改、删除或覆盖 `计算表/` 中的用户参考文件。

构建完成后，在目标 Windows 机器上可用以下命令验证发布目录：

```powershell
.\.venv\Scripts\python.exe scripts\inspect_release.py dist\QingzhouCarbonAccounting
.\.venv\Scripts\python.exe scripts\smoke_standalone.py dist\QingzhouCarbonAccounting
```
