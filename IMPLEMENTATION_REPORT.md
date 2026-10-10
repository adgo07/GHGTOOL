# GHG-UI-P3-C 核算记录与报告界面统一实施报告

日期：2026-10-10。当前状态：整合最新main后验证中；不自动合并、不实施P3-E。

## 平台 / Contract 预检查

仓库origin已确认是`https://github.com/adgo07/GHGTOOL.git`。任务启动时最新main为`029ebe6fa6081e3d742ba3900e641e4c4f6aecf0`；PR40/41在执行期间进入main，本分支已整合到最终验证基线`4792d30bf0f31a7bb55d5cb5c13e0cae86bd7813`。已合并P3-AB PR38、RPT02 PR39、EXB01 PR40、P3-DF PR41。

中央Frozen SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`保持不变；已读中央Phase 2 UI规范及当前ACTIVE UI指南。本任务不涉及中央公共Contract，不修改Frozen、Numeric或baseline。相关Standard Issue：无；本任务不改变既有软件解释或正式核算结果。

## 改动与边界

- `packages/ui/pages.py`：记录页拆分列表与独立详情；完整搜索/状态筛选/行操作；两个且仅两个指定页签；第二页签连续呈现报告汇总、活动/来源、参数来源、质量提示与可读计算依据；移除普通审计详情弹窗；导出/删除绑定已打开Record，避免隐藏列表选中项改变操作对象。
- `packages/ui/record_experience.py`：为连续计算依据提供面向人的说明；收紧第一屏结果摘要；明确ES/ET/EI语义。历史输入缺失或快照损坏按已保存证据展示，不从Catalog或Calculator补造。
- `tests/test_p3_c_records_ui.py`及相关记录/UAT测试：列表访问、搜索筛选、独立详情、审计入口、导出绑定、删除确认与历史快照回归。
- `scripts/p3_c_ui_acceptance.py`及`docs/ui/p3-c/evidence/`：Windows原生Qt自动场景、截图、正式Application演示Record Word和证据JSON。
- `HANDOFF.md`、路线、状态与本报告：更新当前包范围和验收状态。

未改Calculator、Canonical、Record模型/Schema、数据库、历史快照、Excel导入、新建核算、参数因子库、Shell或RPT02报告实现。RPT02一致性证据应以保护文件哈希和同Record公共Word导出对照为准。

## 本地验证结果

所有Python验证均使用项目Python 3.12.14环境；以下为本地执行结果，不是GitHub Actions结果。

| 验证 | 命令/证据 | 实际结果 |
|---|---|---|
| 定向回归 | python -m unittest tests.test_p3_c_records_ui tests.test_g07_records tests.test_g08_delivery tests.test_uat02_usability tests.test_main_integration_ui tests.test_rs03_excel_entrypoints tests.test_rpt02_appendix_b -v | 69项通过；0失败、0错误、0跳过；233.247秒。日志：tmp/p3c-final-focused-py312.log。 |
| 全量回归 | QT_QPA_PLATFORM=offscreen；python -m unittest discover -s tests -t . -v | 456项通过；0失败、0错误、0跳过；1572.595秒。日志：tmp/p3c-full-tests-py312.log；摘要Ran 456 tests ... OK。 |
| Windows原生Qt | python scripts/p3_c_ui_acceptance.py --platform windows；1366×768及1920×1080，Qt缩放100%、125%、150% | 六组均PASS，共115项检查（20+19×5）；Windows 10、PySide6 windows平台。自动脚本，不是人工操作系统DPI验收。 |
| 截图与样例 | docs/ui/p3-c/evidence/ | 30张最终PNG、6份配置JSON、1份范围/RPT02证明JSON、1份正式Application Record Word样例。公共导出与直接RPT02建模/渲染的Word body XML一致；导出前后Record快照相同且Record数量不增加。 |
| 范围证明 | evidence/scope-and-rpt02-proof.json | 基线4792d30bf0f31a7bb55d5cb5c13e0cae86bd7813；12项报告、Shell、计算、Schema/Frozen保护文件均未变；pages.py中RecordLibraryPage以外的4个页面AST均未变。 |
| 编译 | python -m compileall -q apps packages resources scripts tests | Python 3.12.14，退出码0。 |
| 依赖检查 | uv pip check --python（项目Python 3.12环境） | 17个已安装包兼容。 |
| Windows独立构建与GitHub CI | 以提交后的P3-C PR head运行 | 待提交后执行/等待最新PR head结果；最终证据在PR正文。 |

## 待完成验收项

本地定向/全量、六组Windows原生Qt截图和Word一致性已通过。剩余：提交后运行Windows standalone构建、smoke与GitHub当前PR head CI；更新PR最终base/head/diff/结果并等待独立验收。
