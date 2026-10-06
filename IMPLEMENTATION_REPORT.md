# GHG-RPT01 — 统一报告模型 + Word 核算报告 + Excel R2 正式导入模板

状态：`IMPLEMENTED / AWAITING ACCEPTANCE`。最终独立 PR 最新提交的 GitHub Actions 与独立验收是交付门槛；本报告不写入会触发新提交的自身 head 或 CI run SHA，精确提交与 CI 证据见最终交付回复及 PR Checks。

## 1. 基线与平台 / Contract 预检查

- 仓库：`adgo07/GHGTOOL`；origin：`https://github.com/adgo07/GHGTOOL.git`。
- 开工时最新 `origin/main` Base：`c61b29baa2f5d75deae5fc243874d2b1d947bf4a`。
- 独立分支：`codex/ghg-rpt01-report-excel-r2`；未从 PR #27、PF01 或 UAT02 分支派生。
- `platform-lock.json` SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；锁定中央 SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`。未修改或升级锁定基线。
- 按锁定 SHA 核对 Architecture V2.1、Numeric Contract v1 与 Numeric Profiles v1。适用要求是保持分层边界和已采用的数值语义；本任务的 ReportModel 留在 Application，Word / Excel 为外层适配器，Decimal OOXML 读取是本仓 Excel 适配语义。
- 本任务不涉及中央公共 Contract，没有 Contract 冲突；未修改 Calculator、标准公式、标准解释、Canonical 标准数据、标准适用范围或 Frozen Contract。
- Standard Issue：没有新增问题或改变既有解释。PR #27 保持 `OPEN / UNMERGED` 且未修改，仅作只读背景参考。

## 2. 实际交付

### 统一报告模型与 Word 报告

- Application `ReportModel` 从一条已保存 AccountingRecord 的输入、结果、参数、Trace、Provenance、Reporting 和资格快照生成 B.1–B.9 结构化报告；不调用 Calculator、不查当前 Catalog、不补算旧快照中没有的值。
- Infrastructure Word renderer 生成中文 DOCX 报告，包含报告所需业务输入、来源、结果、汇总及可追溯说明。显示修约只用于输出展示。补充信息优先取 Record 的 Reporting 快照，再取同一 Record 既有导出历史，最后使用空白表单。
- 新增 `records.sqlite` 迁移 004 `report_export_history`，追加保存导出格式、模板版本、文件名、文件 SHA-256 与补充信息，并写入审计事件。表有禁止 UPDATE / DELETE 的触发器。既有正式 Record 不变、不可编辑，报告导出不重算或改写历史记录。
- Word 页面采用 A4，宽表切换横向、表头跨页重复、缺失快照明确显示缺项。以非敏感示例生成的简单报告与含长表、多实例的报告在 WPS 打开并渲染检查；页数分别为 4 页与 7 页，检查了中文、分页、表格和重复表头。

### Excel R2 输入模板与预览

- `packages/excel/r2.py` 提供 10 张中文可见工作表及 1 张隐藏模板元数据页，覆盖基本信息、B.2–B.9 输入；动态明细行、下拉项、必要数据提示和 Excel 单元格数据校验均在模板中提供。
- 导入器读取 OOXML 原始数字词法并保留 Decimal；拒绝公式、文本数字、日期、布尔值、非有限值及超过 15 位有效数字的输入。空白和显式数值 0 保持不同含义。
- 每个核算单元独立解析、验证并复用现有 Application / Domain / Calculator 生成只读预览，失败单元与其他单元隔离；预览会说明模板版本、来源文件哈希和行列位置。不保存 Project、Workspace 或 Record，不提供核算结果写回/结果导出。
- Excel 禁止半角斜线作为页签名，模板的 B.4 使用标准的全角斜线。真实 WPS 另存会将它规范化成 `B.4 焙烧_炭化`；导入器接受该已验证别名但仅在内存归一化，规范页名与别名同时出现时因歧义阻断，不改写用户源文件。实际 WPS 另存文件的导入检查成功识别 2 个核算单元。
- Excel 仍只提供导入预览；正式写入 Project / Record 及 Excel 结果导出留在 GHG-RS03。

### UI、架构与 PR #27 参考资产

- UI 增加已保存 Record 的 Word 报告导出、R2 模板下载及只读导入预览，不增加第二套计算路径；普通提示为中文。
- 新增报告输出架构说明、标准能力渐进架构说明、GB/T 32151.34—2024 报告 Schema，以及交付 / 路线 / 交接状态更新。
- PR #27 资产处置：复用已在 Base 中的共享物料标准化 Domain 能力；将现有输入语义适配到 R2 工作簿并增加 Decimal OOXML 入口。没有依赖或复制 PR #27 未合并分支中的旧 Excel 计算器，也没有修改 PR #27。
- 对用户现有 `计算表/` 文件只进行结构性只读检查：5 个 `.xlsx` 与 2 个 `.xls`；没有改动源文件或将其中企业数据写入仓库。历史表格主要是多页、公式驱动的月度台账；R2 将标准业务入口分为 B.2–B.9，并让软件负责计算与预览。

## 3. 测试预期变更

- 数据 / 持久化契约变化：新增 Records 数据库迁移 004 后，`test_g08_delivery` 中“记录库迁移版本数为 3”的旧断言改为 4，以匹配实际新增迁移。Canonical 数据集没有变化，标准、来源、参数和因子计数未因本包改变。
- 新增行为验证：报告使用不可变 Record 快照；导出历史追加且不能更新或删除；R2 按单元隔离；输入数字按 OOXML Decimal 规则检查；空白与零区分；WPS B.4 已知页签别名成功归一，双重页签则阻断。
- 这次工作没有通过放松既有业务校验或修改正式公式来让测试通过，也未改历史 Record 行为。

## 4. 本地验证

验证均在 Windows / Python 3.12.14 本地执行；完整测试通过，不把本地结果冒充 GitHub Actions。

- 定向：`python -m unittest tests.test_rpt01_report_excel -v`：8/8 通过。
- 交付回归：`python -m unittest tests.test_g08_delivery -v`：10/10 通过。
- 全量：`python -m unittest discover -s tests -t . -v`：268/268 通过。
- Canonical：`python scripts/validate_canonical.py`：通过，9 standards、12 sources、98 parameters、98 factors。
- 编译：`python -m compileall -q apps packages scripts tests`：通过。
- 依赖：`python -m pip check`：通过，无损坏依赖。
- 数据库：`python scripts/initialize_databases.py --output-dir <隔离临时目录>`：通过，隔离创建 catalog、user、records、projects 四库。
- Windows 便携版：用 Python 3.12.14 与 RPT01 声明的 DOCX / Excel 依赖从干净临时目录重建 onedir；`scripts/build_standalone.py` 通过文件范围审计和归档校验；`scripts/smoke_standalone.py` 隔离启动 2/2 通过。最初直接使用未安装新增 `python-docx` 的既有本地 `.venv` 构建时，smoke 检出缺失 `docx` 模块；随后在依赖完整的 Python 3.12 构建环境重建，并以最终产物完成启动验证。
- WPS：验证 Word DOCX 的实际打开 / 渲染与 R2 模板、填写样例的打开、另存和重新导入；工作表数量为 10 张可见 + 1 张隐藏元数据页。
- `git diff --check`：提交前执行并要求 exit 0；GitHub Actions 的两项 Windows 检查在独立 PR 最新提交完成后确认。

## 5. 差异与治理状态

本包差异仅包括：统一报告模型与 Word renderer、报告导出审计迁移、Excel R2 模板与只读预览、对应 UI 和测试、交付构建/审计支持、报告架构及路线/交接文档。精确文件数、行数、提交数和 Final Head 由最终 Base→Head Git 差异与 PR 给出。

最终状态：

- GHG-RPT01：`IMPLEMENTED / AWAITING ACCEPTANCE`。
- RS03-A USER UAT：`PENDING`。
- PR #27：`OPEN / UNMERGED`，保持未修改。
- RS03-B：`NOT STARTED`。
- Excel 结果导出：`NOT STARTED`。
- `GB/T 32151.34—2024`：`NOT SUPPORTED`。

最终 PR Head 的精确 SHA、两项 Windows CI run 及其 head SHA 在最终交付回复中报告；文档不会写入自身提交后的 CI run 元数据以避免循环提交。
