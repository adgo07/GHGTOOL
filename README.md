# 青舟温室气体排放核算软件

这是 Windows V1 的 G00 工程骨架。当前只提供可启动的空窗口、基础配置、结构化日志和测试；业务页面、数据库和核算规则按 `HANDOFF.md` 的后续阶段实施。

## 环境要求

- Windows x64
- Python 3.12 x64
- PySide6（由 `pyproject.toml` 管理）

## 安装

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

如果系统中存在多个 Python，请确认创建虚拟环境的解释器为 Python 3.12 x64。

## 启动

```powershell
.\.venv\Scripts\python.exe -m apps.carbon_accounting_desktop
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

测试覆盖最小窗口启动/退出、Logo资源加载、结构化日志的敏感字段过滤和 G00 目录层级约束。

