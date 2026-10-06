# TASK_STATE

状态：CURRENT STATE；更新：2026-10-07。

## 当前工作包与基线

- 仓库：`adgo07/GHGTOOL`；Canonical origin：`https://github.com/adgo07/GHGTOOL.git`。
- 工作包：GHG-RPT01 — 统一报告模型 + Word 核算报告 + Excel R2 正式导入模板。
- 基线：开工时最新 `origin/main` SHA `c61b29baa2f5d75deae5fc243874d2b1d947bf4a`；独立分支 `codex/ghg-rpt01-report-excel-r2`，未从 PR #27、PF01 或 UAT02 分支派生。
- 并行集成：执行期间 UAT02 经 PR #31 合并，最新 `origin/main` 为 `880d5515e8c48cc01294926f7727de4270f73a66`。确认远端本包分支仍为已推送 head 后，将该 main 合入本分支；4 份治理文档冲突已按 RPT01 当前状态和已合并 UAT02 事实解决，UI 页面自动合并。
- 当前阶段：`IMPLEMENTED / AWAITING ACCEPTANCE`。实现与本地验证完成；独立 PR、最新提交 CI 和验收的精确证据见最终交付回复及 PR Checks。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央锁定 SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`，未升级。
- 平台 / Contract 预检查：按锁定 SHA 检查 Architecture V2.1、Numeric Contract v1、Numeric Profiles v1。报告模型不依赖 UI、数据库或 renderer；Excel Decimal 入口是本仓适配器规则，不声明为中央冻结语义。本任务不涉及中央公共 Contract，未修改 Frozen baseline。
- Standard Issue：未新增或改变标准解释；本任务不改变计算公式、标准适用范围或 Canonical 标准数据。
- PR #27：只读参考，未修改、未合并或以其分支为 Base；当前仍保持 `OPEN / UNMERGED`。

## 实现状态

- Application ReportModel 从不可变 AccountingRecord 快照构建 B.1–B.9 报告内容，不调用 Calculator、不读取当前 Catalog、不重算旧记录。Word renderer 输出 DOCX，报告导出采用追加式历史记录和审计事件。
- 新增 `records.sqlite` 迁移 004：保存报告格式、模板版本、文件名、文件 SHA-256 与补充信息；导出历史禁止更新和删除。不修改正式 Record 表或既有记录。
- Excel R2 提供十张中文可见工作表与一张隐藏元数据页；支持动态行、空白与显式零区分、严格 OOXML Decimal 数值入口，以及逐核算单元复用现有 Domain / Calculator 的只读预览。不保存 Project / Workspace / Record，不提供结果导出。
- WPS 实际另存会把 B.4 页签的全角斜线规范化为下划线。导入器仅在内存中接受该已验证别名；若规范名和别名同时出现则阻断，原始工作簿不会被改写。
- UI 增加已保存记录 Word 导出、R2 模板下载和只读预览。报告与 Excel 适配器共用既有 Domain / Calculator。
- 未修改 `计算表/` 用户参考文件、正式公式、Canonical 标准参考数据、`platform-lock.json` 或标准解释；未启动 RS03-B、Golden、Release、Excel 结果导出或第二标准。

## 本地验证

- 定向测试：`python -m unittest tests.test_rpt01_report_excel -v`，8/8 通过；另 `tests.test_g08_delivery` 10/10 通过。覆盖 Word 快照和追加式导出历史、R2 模板、单元隔离、Decimal 入口、空白 / 零与 WPS 页签别名冲突。
- 全量回归：在集成 PR #31 最新 main 后，`QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -t . -v`，276/276 通过，0失败、0错误，Windows / Python 3.12.14。
- Canonical：`python scripts/validate_canonical.py` 通过，9 standards、12 sources、98 parameters、98 factors。
- 编译与依赖：集成后使用 Python 3.12.14 执行 `python -m compileall -q apps packages scripts tests` 通过；`python -m pip check` 输出 No broken requirements found。
- 隔离数据库重建：集成后使用 Python 3.12.14 执行 `python scripts/initialize_databases.py --output-dir <独立临时目录>`，成功创建 catalog、user、records、projects 四库。
- Windows onedir：用 Python 3.12.14 和 RPT01 声明的 DOCX/Excel 依赖重建成功；`build_standalone.py` 内含的发布范围审计与归档校验均通过，`smoke_standalone.py` 隔离启动 2/2 通过。先前直接使用未装新增 `python-docx` 的既有本地 `.venv` 时，首个临时构建缺少 `docx`；发现后改用已具备全部依赖的 3.12 运行环境重建并完成验收。
- WPS 检查：用生成的非敏感示例打开 R2 模板和填写样例，并另存、重新导入；确认识别 2 个核算单元。实际 Word 输出在 WPS 打开并渲染，检查 A4 页面、重复表头、跨页长表与中文内容。用户参考 Excel 文件仅作只读结构检查：5 个 `.xlsx`、2 个 `.xls`，没有将其中企业数据复制到仓库或报告。
- `git diff --check` 与文档状态在提交前复核；GitHub Actions 以独立 PR 最新提交为准，结果见最终交付回复。

- 并行工作包状态：UAT02经PR #31已合并进入最新main；PF01 PR #30仍为`OPEN / UNMERGED`且未并入本分支；PR #27未修改，仍为`OPEN / UNMERGED`。

## 治理状态与停止点

- GHG-RPT01：`IMPLEMENTED / AWAITING ACCEPTANCE`；PR 最终提交 Windows CI 与独立验收通过后停止，不合并。
- RS03-A USER UAT：`PENDING`；PR #27：`OPEN / UNMERGED`且未修改；RS03-B：`NOT STARTED`；Excel 结果导出：`NOT STARTED`。
- `GB/T 32151.34—2024` 仍为 `NOT SUPPORTED`；本任务不启动产品下一阶段。
