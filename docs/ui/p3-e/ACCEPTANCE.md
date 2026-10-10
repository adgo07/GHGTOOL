# GHG-UI-P3-E 验收记录

状态：PR #43 已创建，等待独立验收。不得自动合并。链接：[GHG-UI-P3-E #43](https://github.com/adgo07/GHGTOOL/pull/43)。

## 基线与平台 / Contract 预检查

- Canonical origin：`https://github.com/adgo07/GHGTOOL.git`。
- 任务分支：`codex/ghg-ui-p3-e-table-import`，从最新 `origin/main` 创建；基线 `4792d30bf0f31a7bb55d5cb5c13e0cae86bd7813`（P3-DF PR #41）。
- 页面及测试实现提交：`15b5cfb284ad85461490e7da78b99b9bf571a2c3`。最终PR head包含后续验收/治理文档提交，以GitHub PR所示head为准。
- P3-AB PR #38、RPT02 PR #39、EXB01 PR #40、P3-DF PR #41均已在基线中。EXB01是表格能力唯一业务基准。
- `platform-lock.json`锁定中央 `Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`。Architecture V2.1及Numeric v1保持原锁定；本任务不涉及中央公共Contract，不升级baseline。
- `STANDARD_ISSUES_REGISTER.md`共有8项且全部RESOLVED；本任务不改变标准解释或软件计算决定，不新增Issue。

## 实际修改

- `packages/ui/pages.py`：把导入页面整理为四个紧凑区域；先选择工作簿，再单独检查预览；明确展示所选文件、企业与期间、边界信息、核算单元状态、提醒及单元格位置；有效单元保存为项目后，再主动正式核算。打开已保存项目时继续使用项目数据。
- `packages/ui/excel_import_components.py`：新增页面专属区域与预览组件，提供只读核算单元表和当前单元错误/提醒详情。
- 新增P3-E专项测试；更新受操作步骤影响的Shell/Excel集成回归用例。
- 基线到实现提交的差异只有TASK_STATE、页面与专属组件、测试及四张UI证据截图。差异检查确认 `packages/excel/`、`packages/application/`、`packages/core/`、`packages/standards/`、`packages/persistence/` 与 `resources/databases/` 均无改动。没有改Excel模板、Importer/Adapter、Decimal、Canonical、Calculator、项目或Record语义、数据库结构、Word模型/renderer或结果Excel导出。

## 业务保护与验收证据

- 四个区域分别为“获取模板”“选择文件与核算信息”“数据检查与预览”“保存项目、正式核算与结果”。仅允许现有正式格式 `.xlsx`；选择文件不会自动运行导入，必须点击“检查并预览”。
- 预览使用现有EXB01完整工作簿Importer和共享Preview/Application路径，不写正式Record。表格可同时显示多个核算单元；逐行详情说明有效/需修正状态、错误和提醒位置。混合有效/无效预览的保存测试确认只保存有效单元。
- 模板下载测试比较目标文件与 `ExcelTemplateService` 批准模板的原始字节，未重新保存工作簿。
- `tests.test_main_integration_ui.test_gui_and_excel_have_exact_results_and_preview_does_not_save` 比较GUI和附录B输入的正式 `Decimal` 总量及每个分项数值/单位，使用完整精度相等断言；显示用两位小数的预览文本不参与该比较。该测试也确认预览不新增Record。
- `tests.test_exb01_rpt02_integration.test_approved_workbook_preview_project_record_and_frozen_word_report`覆盖真实附录B导入、Canonical项目保存、正式Record追加及项目Record关联；项目及记录恢复由既有SQLite项目回归覆盖，包括 `tests.test_canonical_project_inputs` 与 `tests.test_accounting_projects_ui`。这些正式数据语义未改动。
- 全量测试包含失败输入不覆盖历史Record、重复成功计算追加新Record、报告继续消费冻结Record等现有断言。

## 本地验证

所有下列证据均为本机Windows/Python 3.12执行，不是GitHub Actions结果。

| 检查 | 命令/证据 | 结果 |
|---|---|---|
| P3-E专属 | `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m unittest tests.test_p3_e_excel_import -v` | 5/5通过 |
| 定向回归 | `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m unittest tests.test_p3_e_excel_import tests.test_g03_shell tests.test_exb01_rpt02_integration tests.test_main_integration_ui tests.test_rs03_excel_entrypoints -q` | 34/34通过，64.125秒 |
| 完整回归 | `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m unittest discover -s tests -q` | 453/453通过，1207.469秒 |
| 标准目录 | `.\.venv\Scripts\python.exe scripts\validate_canonical.py` | 9 standards、12 sources、102 parameters、138 factors；PASS |
| 编译 | `.\.venv\Scripts\python.exe -m compileall -q apps packages resources scripts tests` | PASS |
| 依赖一致性 | `uv pip check --python .\.venv\Scripts\python.exe` | 19 packages兼容；PASS |
| Windows独立版构建 | `.\.venv\Scripts\python.exe scripts\build_standalone.py --output-root build\p3e-standalone --clean` | PASS；manifest的source_commit=`15b5cfb284ad85461490e7da78b99b9bf571a2c3`；267个文件 |
| 发布目录审计 | `.\.venv\Scripts\python.exe scripts\inspect_release.py build\p3e-standalone\QingzhouCarbonAccounting` | PASS；267 files |
| 上传式归档往返 | `.\.venv\Scripts\python.exe scripts\verify_release_archive.py build\p3e-standalone\QingzhouCarbonAccounting` | PASS；268 visible files，manifest经ZIP往返仍可验证 |
| Windows启动 | `.\.venv\Scripts\python.exe scripts\smoke_standalone.py build\p3e-standalone\QingzhouCarbonAccounting --starts 2` | 两次隔离启动均PASS |

PR #43已创建；GitHub Windows CI需绑定推送后的最新head复核。该检查结果以GitHub Actions实际状态为准。

## Windows截图

以下截图由Windows PySide6 Qt离屏环境生成并人工查看；不是原生桌面鼠标/键盘或系统DPI截图。尺寸均为1560×1050。原生交互与系统100%/125%/150%缩放验收仍OPEN；离屏证据不替代该项。

| 截图 | 内容 | SHA256 |
|---|---|---|
| [01-import-ready-1560x1050.png](evidence/01-import-ready-1560x1050.png) | 初始页面与四个区域 | `96a2e40106439235f59a2536d5428679cbdb5b7dc2f1c726caf0948b119a4197` |
| [02-import-preview-1560x1050.png](evidence/02-import-preview-1560x1050.png) | 导入预览与核算单元状态 | `1c6a904ce0a39d174729445d1d198a656c423dd7c6da988d734f8034138b2d7c` |
| [03-import-cell-error-1560x1050.png](evidence/03-import-cell-error-1560x1050.png) | 单元格错误位置和详情 | `5e4048101f01ca305a1c3bc90b3f07edecf82dcdefb0429cda6b4c95346464ab` |
| [04-project-record-1560x1050.png](evidence/04-project-record-1560x1050.png) | 保存项目、正式核算与关联Record | `3a507fc7f780ecff1716fbde976ca73faab1d559e8253c88640a69fb929da80a` |

## 待独立验收项

- GitHub Actions的最终PR-head Windows全量回归/Standalone CI尚待执行或完成。
- 原生Windows人工点击、键盘、滚动及不同系统DPI操作未验证。
- EXB01原有的原生Excel/WPS保存后再导入验收仍按#40记录保持OPEN；P3-E不扩大该工作包范围。
- 用户明确要求不自行合并；完成PR并等待独立验收。