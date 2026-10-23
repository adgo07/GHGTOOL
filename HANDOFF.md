# UI 中文化 PR-A（本地自检通过，待 CI 和独立验收，2026-10-23）

PR57 已完成 CI299 新包核验并合并，merge `8f9fa119a0982d77dccc9a4ee982997004657949`。CI299 精确 head 为 `f4c33c277273389c7758c0ea5289cc4e290eec9e`；实际下载 ZIP、319 文件集合、318 项大小/hash、工具链身份及 Qt DLL 版本核验通过，见 `docs/ci/CI299_SUMMARY.json`。本地独立脚本审计 PASS；PNG/SVG 与两次隔离启动证据来自 CI，未在本地运行该 EXE。CI298 失败为历史已修缺陷，不能作为通过证据。

当前按 Owner 的 UI V1 与 V1.1 轻量修订实施 PR-A：可信 Qt 中文资源、一次初始化与安全降级、中文消息/输入弹窗、局部按钮样式、退出保存/取消保护，以及精确包资源与中文探针。首页布局、业务页布局、计算、Canonical、数据库、模板、Word 和原性能证据不变。PR-B 尚未开始。

## 平台 / Contract 预检查

实际 origin 为 adgo07/GHGTOOL；从合并后的 main 建立隔离工作树，保护根工作树用户修改。Frozen baseline `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变；已读实际 AGENTS、唯一路线、状态、交接、台账，UI 使用中央当前 ACTIVE V0.2。**本任务不涉及中央公共 Contract。** 不改变标准解释、适用范围、Numeric Profile、Record 或 schema，无新增 Standard Issue。

## 验证与待办

本地验证（Qt 均为 offscreen，Python 3.12.14 / Qt 6.11.2）：

- `python -B -m unittest tests.test_ui_chinese tests.test_g08_delivery -v` 首轮 28 项中 27 通过、1 项旧 QApplication 替身不兼容；改为真实 QApplication 后，6 项中文测试及启动错误测试 7/7 通过（1.106s）。
- `python -B -m unittest tests.test_ui_chinese tests.test_accounting_projects_ui tests.test_export_directory_ui tests.test_export_location tests.test_build_environment -q`：44/44，148.411s；含新增资源裁剪/审计负例和失败初始化不重试。
- `python -B -m unittest tests.test_b_external_review tests.test_b_fgd_acceptance_fixes tests.test_b_fgd_chain tests.test_b_fume_chain tests.test_b_material_draft_scope tests.test_b_material_gui_excel -q`：49/49，313.874s。
- 最小截图 `python scripts/capture_ui_review.py <新目录>`，见 `docs/ui/chinese-dialogs/summary.json` 与三张截图；DPR=1 离屏，callback_errors 为空。输入框按中文名称最小宽度调整；消息框按钮实际高36逻辑像素。首页仅静态核对布局实现未改，不冒称原生像素一致。

测试集合有重叠，不把以上数量相加宣称独立总数。完整套件和精确包交由本 PR 的 Windows CI；当前尚无本 UI 提交的远端结论。

开发捕获脚本使用实际主窗口入口、隔离临时数据库、系统已安装中文字体；不打包字体。首轮无字体截图已识别无效，补系统字体后核对退出/启动错误/输入框，最终截图与摘要已保留。当前尚未有本 UI head 的 CI 或实包，不用 CI299 背书 UI 改动。

PR-A 稳定后提交一个 PR，继承 required checks、全量测试和精确 head 包门禁，等待验收，不自动合并。A 验收合并后才开始 PR-B；B 先做真实 Qt 样板并请 Owner 确认视觉方向，再推广约定区域。

原生 Office、真实鼠标/中文 IME/人工系统 DPI、企业样例、干净机、完整许可履约、Release、RS04–05 继续 OPEN，本轮未获桌面操作授权，不宣称正式交付或完整标准支持。