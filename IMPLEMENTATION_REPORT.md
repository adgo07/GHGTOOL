# GHGTOOL HTML V4 — PR2 实施报告

日期：2026-10-12。状态：实现与定向验收完成，等待 PR Windows CI 和 Owner 最终视觉确认；不自动合并。

## 基线与平台 / Contract 预检查

仓库：`https://github.com/adgo07/GHGTOOL.git`。PR1 #44 已合并。PR2 独立分支 `codex/ghg-html-v4-pr2` 从最新 `origin/main@204dded5d03853617f79a1f05693e89b619df9d1` 开始；GitHub `main` 分支 API 回读 SHA 与本地基线一致。工作树 `git fetch origin` 因共享 worktree 的 `.git/worktrees/.../FETCH_HEAD` 权限失败，未修改原始 checkout 或其未提交文件。

`platform-lock.json` 中央 Frozen baseline 为 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。本任务遵循中央当前适用 UI 指南；不涉及中央公共 Contract，不修改 lock、Frozen Contract 或数据库 Schema。`STANDARD_ISSUES_REGISTER.md` 无新增问题，本任务不改变软件标准解释。

## 实施内容

- 按 Owner 的首页意见移除标准库卡片前的小字；首页保持无侧栏、真实青舟 Logo、标准库重点卡、五张入口卡和真实“继续工作 / 最近核算”内容。没有项目或记录时显示真实空状态。
- 统一公共页面的 V4 色彩、字体、间距、卡片、输入、表格、选项卡、焦点/悬停样式；新增一个 SVG 下拉箭头并加入既有发布资源白名单。
- 标准库和参数库采用标准中性文案。分发逻辑只把 `STANDARD_ID` 路由到炭素材料专属核算页；未开放标准不会进入该页。没有建立多标准插件或通用计算表单。
- 炭素材料页面的八类排放源入口改为 V4 四列网格，只调整布局，不改变输入、Calculator 或计算语义。
- 核算记录列表改为七列完整可访问表格，保留真实搜索、状态筛选、行内打开、键盘 Enter、删除确认与审计留存。详情是独立视图，保留两个页签及冻结输入/计算依据；首个页签仅排版已有冻结摘要，完整显示 ET、ES、净间接排放量和全部提醒。
- 保留现有正式 Word 导出入口和语义；没有修改 Record、Calculator、Canonical、Excel 导入、报告模型、模板、渲染器或历史快照。
- HTML→Qt 视觉映射和真实 Windows 截图见 `docs/ui/HTML_V4_QT_MAPPING.md` 与 `docs/ui/v4-evidence/`。

## 验证

- 定向命令 `python -B -m unittest tests.test_g03_shell tests.test_g04_catalog tests.test_g07_records.G07UiTests tests.test_g08_delivery tests.test_main_integration_ui tests.test_p3_c_records_ui tests.test_uat03_page tests.test_uat02_geometry`：84 项通过，0 失败，耗时 432.237 秒。
- 相关复测命令覆盖首页空/有数据、标准搜索与白名单分发、发布资源白名单：6 项通过，0 失败，耗时 10.386 秒。
- 14 个改动 Python 文件用内存 `compile()` 完成语法检查；`git diff --check` 通过。首次 `compileall` 在本机因沙箱不允许写入 worktree 的 `__pycache__` 失败，故改用不写缓存的内存语法检查；Windows CI 仍会按现有 workflow 执行 compileall。
- Windows 原生 Qt 进程生成并目视检查了 1600×900 主要页面、1366×768 和 1920×1080 首页截图；Qt 报告 DPR 1.0 / 96 logical DPI。125% Windows 系统显示缩放未在本机切换，也未声称实测。截图夹具使用隔离临时 Catalog/Project 和合成冻结 Record。
- PR 全量 Windows Python 3.12 测试、1.25/1.5 UI scale 检查及精确 head standalone build 尚未执行；创建 PR 后以 GitHub Actions 结果为准。

## 等待事项

PR 需等待完整 Windows CI、Owner 最终视觉确认和独立验收。PR2 不自动合并。PR1 既有 C.4 饱和温度来源 OPEN 项未在本轮处理。
