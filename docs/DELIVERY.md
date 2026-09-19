# G08 Windows 交付说明

本文档描述青舟温室气体排放核算软件 Windows V1 的 G08 交付候选包。它是便携式 `onedir` 目录，不是安装程序；G09 未实施。

## 版本与数据矩阵

| 项目 | 值 |
| --- | --- |
| 应用版本 | `1.0.0` |
| Canonical schema 版本 | `1.0.0`（G08 未修改 schema，未新增迁移） |
| Catalog data 版本 | `2026.09.20-g08.1` |
| Catalog 数据库迁移 | `001` |
| User 数据库迁移 | `001` |
| Records 数据库迁移 | `002` |

构建脚本会从 `data-source/carbon_accounting/catalog.json` 重新生成只读 `databases/catalog.sqlite`，并写入 `build-manifest.json`。发布前必须通过 `scripts/inspect_release.py` 的文件范围、哈希、数据库元数据和敏感文件检查。

## 构建

环境要求：Windows x64、Python 3.12 x64。开发环境中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[build]"
.\.venv\Scripts\python.exe scripts\build_standalone.py --clean
```

输出目录为：

```text
dist\QingzhouCarbonAccounting\QingzhouCarbonAccounting.exe
dist\QingzhouCarbonAccounting\databases\catalog.sqlite
dist\QingzhouCarbonAccounting\build-manifest.json
```

将整个 `dist\QingzhouCarbonAccounting` 目录复制到目标 Windows 机器即可启动。当前没有 MSI、安装向导、代码签名或自动升级服务；这是 G08 的明确限制。

## 启动与数据目录

双击 `QingzhouCarbonAccounting.exe`，或在该目录执行：

```powershell
.\QingzhouCarbonAccounting.exe
```

应用只读 Catalog 位于发布目录 `databases\catalog.sqlite`。用户数据与日志不写入程序目录：

- 核算记录：`%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting\data\records.sqlite`
- 结构化日志：`%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting\logs\application.jsonl`

首次使用时，records 数据库会自动创建并执行已知迁移。数据库迁移只允许向前应用；未知的未来迁移版本会安全失败，不会自动删除或覆盖文件。

## 卸载与数据保留

便携式交付没有注册表安装项。删除发布目录不会删除 `%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting\data` 或 `logs`，因此历史记录和日志默认保留。若确需清理，请先备份 `records.sqlite`，再由用户手动删除上述数据目录；软件不会在卸载或启动失败时自动清理用户数据。

发布包不得包含标准全文、`计算表`、测试数据库、开发目录、环境文件或开发密钥。`build-manifest.json` 记录每个发布文件的 SHA-256 和大小，供验收与追溯使用。

## 当前能力边界

- 计算链只覆盖 GB/T 32150—2025 通用规则和 GB/T 32151.34—2024 炭素材料生产企业模块。
- 其余计划标准只有目录与状态信息，不实现计算规则。
- Excel 导入、报告/导出、企业档案完善、企业层级、审批、`.qzproj` 项目文件和云端服务不在 V1。
- 遇到其他行业活动或上下游运输时只提示需要其他标准，不猜算、不套算、不并入当前结果。
- G08 在 Windows 11 CI 上验证；若本地没有 Windows 10 环境，Windows 10 实机验证不宣称已完成。

## 故障排查

1. **启动提示找不到 Catalog**：确认 `databases\catalog.sqlite` 与 exe 同在发布目录，重新运行构建脚本；不要把标准 PDF 复制进发布包。
2. **数据库迁移错误**：先关闭应用并备份 `%LOCALAPPDATA%` 下的 `records.sqlite`，保存 `application.jsonl` 后再提交问题；不要直接删除或手工修改迁移历史。
3. **无写入权限**：确认用户对 `%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting` 有写权限，程序目录只需可读。
4. **查看日志**：日志是 JSON Lines，默认脱敏敏感字段；只收集与问题相关的时间段，避免上传用户数据。
5. **自动化测试环境**：`QT_QPA_PLATFORM=offscreen` 仅用于无显示器测试，不是生产启动参数。

## 构建后检查

```powershell
.\.venv\Scripts\python.exe scripts\inspect_release.py dist\QingzhouCarbonAccounting
.\.venv\Scripts\python.exe scripts\smoke_standalone.py dist\QingzhouCarbonAccounting
```
