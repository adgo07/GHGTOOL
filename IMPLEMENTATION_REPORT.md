# GHG-UI-P3-AB 实施报告

日期：2026-10-09。状态：本地联合回归完成，待最终 head Windows CI；原生实机验收 OPEN，不自行合并。

## 平台 / Contract 预检查

- origin 已核验为 `https://github.com/adgo07/GHGTOOL.git`；默认分支 main。PR #37 已合并，最新 baseline 为 `708f78a455790946b4a728029bba768d8fb295fc`，从其新建 `codex/ghg-ui-p3-ab`，没有复用旧分支。
- 开工 tracked 工作树干净；既存用户 Office 参考文件、`tmp-rs03-review/` 及后续出现的其他工作树目录不覆盖、不纳入本 PR。
- Locked central SHA 保持 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`；相关 Architecture V2.1 Frozen 要求分层、Qt 状态留在 Presentation、业务层不依赖界面。本任务不涉及中央公共 Contract，无 Frozen 冲突或 adoption，不修改 lock / baseline。
- UI 使用中央已合并 `854b544563260f9e79c73e714c85f6589e0f19b3` 的 v0.2 指南、家族规格、验收清单及 Phase 2 三份规格。ACTIVE / EVOLVING 与 Frozen 分开；只读取可信 origin 的已合并对象，不移植 HTML/CSS/JavaScript 或演示数据。
- MUST：七个路由稳定、页面实例和项目/单元输入保留、现有核算/原文门禁、真实数据与准确空态、来源追溯不删除。
- MUST NOT：修改 Application / Domain / Repository / 持久化接口、Calculator、Numeric、Canonical、标准解释/支持范围、Schema、迁移、历史 Record、Excel 解析/模板/保存逻辑、Word 生成。
- Standard Issue：001～008 现有登记不变；本包没有新增疑义，不改变既有软件解释。参考标准仍未获正式 SUPPORTED 状态。

## A：Shell、首页与导航

启动首页隐藏侧栏，五入口顺序为标准库、新建核算、表格导入、核算记录、参数与因子库；设置独立。使用既有真实青舟 LOGO 与 SVG，最近工作只读真实项目/记录或显示准确空态。首页项目名称只作真实记录展示，沿既有新建核算项目列表打开，避免新增项目恢复路径。

业务页淡蓝侧栏、顶部品牌、底部设置、当前页高亮；返回首页仅隐藏侧栏，原页面实例继续保留。七个 `AppRoute`、EXCEL_IMPORT/API/格式、输入及关闭确认均沿用。

## B：标准库

查询只保留关键词与状态，复用 `CatalogQueryService`。五列严格为标准编号、标准名称、标准状态、实施日期、软件支持；前两列下划线及键盘 Enter 均打开对应详情，返回保留查询、选中和可用滚动位置。长名称支持表格滚动与完整详情。

详情为同一路由独立完整视图，连续基本信息、适用范围、标准要求三分区，无页签、发布单位、软件支持范围、关系与来源区或参数堆砌。现有 Catalog 没有可靠结构化标准要求，因此显示准确占位，不从因子反推条款；适用范围仅消费已有核实说明。官方 URL 缺失时禁用并解释；新建核算沿原有当前标准门禁。软件支持明确“已实现核算（未正式支持）”，不升级标准能力状态。

## 修改范围与保护复核

| 文件 | 范围 |
|---|---|
| `apps/carbon_accounting_desktop/product.py` | 软件名称、首页描述及“表格导入”展示文案 |
| `packages/ui/shell.py` | 侧栏显隐、样式、首页品牌资源传递 |
| `packages/ui/view_models.py` | 导航显示名与七路由唯一性检查 |
| `packages/ui/pages.py` | HomePage；ExcelImportPage 仅标题改为“表格导入”；页面装配参数 |
| `packages/ui/catalog_pages.py` | StandardLibraryPage 与必要导入；共用 helper 和 ParameterFactorLibraryPage 不变 |
| `tests/test_g03_shell.py`、`tests/test_g04_catalog.py`、`tests/test_p3_ab_standards.py`、`tests/test_main_integration_ui.py` | A/B、状态保留、键盘、长名称、原文及能力门禁回归 |
| `scripts/p3_ab_ui_acceptance.py` | 隔离临时数据的 Windows Qt 离屏检查与截图 |
| 当前治理记录、`docs/ui/p3-ab/` | 验收对应、证据和阶段暂停边界 |

按 baseline 对类正文复核：RecordLibraryPage 完全不变；ExcelImportPage 仅显示标题变化；ParameterFactorLibraryPage 完全不变。Calculator、业务核算页、源数据、数据库、报告与解析文件不在 diff 中。两名实施子 agent 分别负责 A/B，独立 Luna max 复核发现的项目入口表述、支持状态限定和详情按钮重复问题均已修正。

## 本地执行证据

代码快照：`12bab994e0b8afcec1f73740c1db59ae729e25f3`；后续提交增加测试夹具清理修正并同步治理与截图，最终 head 以 PR 元数据为准。全量使用该 commit 的干净 Git archive，避免既存临时工作树和旧构建目录污染；没有删除用户文件来制造通过。

| 命令 / 范围 | 实际结果 |
|---|---|
| baseline `python -m unittest discover -s tests -t . -v` | 最新 main 干净快照 395/395，1051.994s；日志 `tmp/p3-ab/baseline-clean-tests.log` |
| A：`python -m unittest tests.test_g03_shell -v` | 9/9；A 通过后开始 B，日志 `tmp/p3-ab/a-targeted.log` |
| A 保护回归：`python -m unittest tests.test_main_integration_ui tests.test_accounting_projects_ui tests.test_rs03_excel_project_workflow tests.test_uat03_page tests.test_g07_records -v` | 68/68，510.796s；日志 `tmp/p3-ab/a-regression-68.log` |
| B：`python -m unittest tests.test_p3_ab_standards tests.test_g04_catalog -v` | 最终文案后 22/22，46.877s；日志 `tmp/p3-ab/b-final-targeted.log` |
| AB：`python -m unittest discover -s tests -t . -v` | 404 项：403通过、1清理错误，1401.112s；业务断言通过后 tearDown 删除 catalog.sqlite 遇 WinError32。日志 `tmp/p3-ab/ab-full-tests.log`，不声称本地全量通过 |
| `python scripts/uir04_manual_gui_acceptance.py` | 自动驱动 A～E 五场景 PASS；不是原生人工操作 |
| `python scripts/uir04_scale_acceptance.py --scale 1.0` / `1.25` / `1.5` | 三次 PASS，既有动态录入布局回归；不是系统 DPI 实测 |
| `python scripts/validate_canonical.py` | PASS：9 标准、12 来源、102 参数、138 因子 |
| `python -m compileall -q apps packages resources scripts tests` | PASS |
| `uv pip check --python .venv/Scripts/python.exe` | PASS：17 个依赖兼容；本机 venv 无 pip，不虚称执行 pip 模块 |
| `python scripts/initialize_databases.py --output-dir tmp/p3-ab/databases-check` | PASS：四个隔离数据库从零初始化 |
| `git diff --check` | PASS |
| `python -m unittest tests.test_main_integration_ui -v`，严格清理修正后 | 5/5，26.976s；日志 `tmp/p3-ab/integration-cleanup-targeted.log` |
| `python scripts/build_standalone.py --output-root tmp/p3-ab/standalone-check` | PASS：source_commit / pr_head_sha = 代码快照 12bab994；最终治理 head 的交付由 CI 另验 |
| `python scripts/inspect_release.py tmp/p3-ab/standalone-check/QingzhouCarbonAccounting` | PASS：264 files |
| `python scripts/verify_release_archive.py tmp/p3-ab/standalone-check/QingzhouCarbonAccounting` | PASS：265 visible files，ZIP round-trip 清单一致 |
| `python scripts/smoke_standalone.py tmp/p3-ab/standalone-check/QingzhouCarbonAccounting` | PASS：2 isolated starts |

前序失败与闭环：首次根目录探索性全量 395 项中 2 失败、1 错误，受旧临时副本扫描、既存构建目录权限及 A 进行中断言影响，不作为 baseline 或最终证据；随后使用干净 baseline 快照 395/395。A 首轮保护回归 67/68，恢复最近记录既有 bodyText 标识后 68/68。B 首轮 21/22，返回布局最大滚动值会收敛，改为验证非零中间位置及水平溢出恢复后 22/22，未删除生产状态保持要求。暂停前一次全量启动被自动审批用量限制拒绝，未执行；恢复后正常重试执行全量。全量唯一错误发生于既有 MainIntegrationUiTests 临时目录清理；补充 DeferredDelete 事件处理与 gc.collect 后严格清理（不忽略异常、不删断言），模块复测见下，最终全量由 Windows CI 验证。

## Windows 截图与原生验收

`scripts/p3_ab_ui_acceptance.py` 对逻辑窗口 1366×768 / 1920×1080、Qt scale 1.0 / 1.25 / 1.5 共六组，90/90 自动检查，24 PNG + 6 JSON。当前源文件哈希与 JSON 一致。证据在 `docs/ui/p3-ab/evidence/`，分别记录逻辑尺寸、物理像素和比例；不是六组原生显示设置实测。

原生人工验收 **OPEN**：Computer Use 两次初始化因 trusted Node / Windows sandbox helper 失败，未能操作真实程序。需独立验收原生鼠标、键盘、窗口缩放及上述系统 DPI；离屏图不能替代。标准要求无可靠内容为准确占位，后续有权威依据再独立补充，不修改 Catalog 以凑页面。

## CI、兼容性与交付边界

Windows CI 与本地证据分开：最终 PR 的 checks / body 记录最终 head 的 Merge-ref Full Tests 与 PR-head Standalone Audit 结果及运行链接。本报告提交时待 CI，不预先声称通过；创建后若失败必须修正并核对新的最终 head，不以旧 head 结果替代。

开工查询未发现 EXB01 远端分支/PR/启动证据；RPT02 对话“完善附录B Word报告”已接收任务，但当时因 helper 错误 BLOCKED，无分支或修改。交付前复查 RPT02 已恢复，在独立 `codex/ghg-rpt02` 工作树实施 reporting/model.py、word_renderer.py、ui/record_experience.py、pyproject.toml、build_standalone.py 及新增报告布局；本包与这些业务文件无交集。TASK_STATE.md 为明确治理交集，后续 HANDOFF / IMPLEMENTATION_REPORT 也可能冲突，须分别保留真实工作包状态。只读元数据和路径清单，不读取或合入未合并实现；本包不改 ExcelImportPage / RecordLibraryPage 业务或 Word 实现。EXB01 仍未找到启动证据。

中央 A 类对应和详细验收项见 `docs/ui/p3-ab/ACCEPTANCE.md`。交付单一独立 PR，不自行合并；AB 完成并合并后 Phase 3 暂停，C/D/E/F 按新任务及 EXB01、RPT02 的真实状态另行开展，RS04～RS06+ 和正式支持验收均未因此启动。
