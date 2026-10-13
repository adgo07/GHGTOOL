# GHGTOOL HTML V4 — PR2 实施报告

日期：2026-10-13。PR #45 仍开放且未合并；代码 head `3545030a97bcaaa36744fbb37e55fa2b34bc75c7` 的 Windows CI #216 全部通过。既有代码 head `bbecb302f5611db40b1e30aed62d3221e107176f` 的 CI #211 通过记录见下文历史验证。

## Owner 页面反馈跟进（2026-10-13）

- 已读取正式 V4 交接包中的 HTML、定稿说明，以及首页、焙烧物料和热力三张配套截图，并按该包核对下拉样式。V4 页面使用原生选择框箭头和自定义搜索框箭头；因此保留箭头，同时增加点击输入区展开候选并保留键盘选择。
- 按 Owner 页面反馈，收口首页最近核算列宽和“打开”垂直位置；标准目录的支持列/名称列比例、字号、标准编号/名称的可点击悬停提示、状态标签；统一快速定位与八张排放源卡的 Mapping 名称和分组；加入启用源深蓝标题条、燃料标签简化、煅烧/焙烧/石墨化分别 4/6/8 个 V4 默认类别行。因子库使用真实 Catalog，保留全库搜索和来源浏览两个模式，并按 V4 呈现查询方式和来源浏览说明。
- 空白默认物料行可删除，不会生成 Canonical 物料项；保存项目会保留实际页面行及 ID。修复燃料行删除后 Qt 尺寸提示未刷新的滚动高度问题。输入文字不会重排活动卡片。
- 本机 17 项唯一 UI/项目定向用例通过；事件过滤收窄后另复跑 4 项相关用例通过；UIR04 人工 GUI 脚本 A–E 通过。
- Windows CI #214 在 470 项全量测试中有 3 failures / 10 errors。旧夹具/断言和动态燃料行移除后页面未收缩问题已修复。PR head `6403371` 的 Windows CI #215 前置、UIR04 A–E 和缩放检查通过，但 full-test 步骤在 40 分钟 job 时限处取消，无全量统计，standalone audit 跳过。为减少全局事件开销，将点击事件过滤收窄到标记过的可搜索输入框；相关下拉、滚动、打字稳定测试和 UIR04 A–E 本机复跑通过。
- exact-head Windows CI #216（PR head `3545030`）：merge-ref 全量 470 项通过，0 failures / 0 errors / 0 skipped，耗时 1292.646 秒；前置规范、编译、依赖、数据库、UIR04 A–E 和 Windows 1.25/1.5 缩放检查通过。PR-head standalone audit 的 14 项 G08 交付测试通过，独立目录构建成功；270 个可见文件通过 release audit，271 个文件的归档 manifest 往返、provenance 和双次独立启动 smoke test 均通过，候选归档已上传。
- 当前 PR head `3545030` 的说明与截图链接已更新。125% Windows 桌面实机视觉检查和 Owner 最终视觉确认仍待完成；本任务不自动合并。
- 后续 Owner 反馈在 `3545030` 之后追加：焙烧/炭化与石墨化默认类别扩展至 V4 的六行/八行；因子库搜索列序调整为“参数名称、数值、单位、类别”，来源浏览保留真实 Catalog 原表列。为保持旧项目 `form_state` 的语义，旧的前四个类别下拉索引未移动；新增默认子类别只映射到既有 Domain 角色，不改变计算字段。
- 最新定向回归（本机 Windows；运行时使用 `QT_QPA_PLATFORM=offscreen`）：`python -B -m unittest tests.test_g06_page.G06PageTests.test_quick_jump_matches_eight_source_groups_and_material_roles_are_preopened tests.test_g04_catalog.G04CatalogTests.test_parameter_factor_page_browses_sources_and_aggregates_shared_assets tests.test_g04_catalog.G04CatalogTests.test_missing_optional_source_url_disables_external_link_safely tests.test_p3_df_factors tests.test_accounting_projects_ui.AccountingProjectUiTests.test_material_rows_keep_values_after_project_reopen`，7 项通过、0 失败/错误。运行期间产生 1 条现存 SQLite `ResourceWarning`，不影响测试结果；完整 Windows CI 将在新 Head 推送后复验。
- 因子库及焙烧/石墨化截图由本机 Windows PySide6 真实窗口生成，尺寸 1600×900、DPI 96、DPR 1.0，数据库位于隔离临时目录；125% Windows 系统缩放仍未实测。

## 基线与平台 / Contract 预检查

仓库：`https://github.com/adgo07/GHGTOOL.git`。PR1 #44 已合并。PR2 独立分支 `codex/ghg-html-v4-pr2` 从最新 `origin/main@204dded5d03853617f79a1f05693e89b619df9d1` 开始；GitHub `main` 分支 API 回读 SHA 与本地基线一致。工作树 `git fetch origin` 因共享 worktree 的 `.git/worktrees/.../FETCH_HEAD` 权限失败，未修改原始 checkout 或其未提交文件。

`platform-lock.json` 中央 Frozen baseline 为 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。本任务遵循中央当前适用 UI 指南；不涉及中央公共 Contract，不修改 lock、Frozen Contract 或数据库 Schema。`STANDARD_ISSUES_REGISTER.md` 无新增问题，本任务不改变软件标准解释。

## 实施内容

- 按 Owner 的首页意见移除入口卡片前的演示提示标签，保留 V4 主标题副文案；首页保持无侧栏、真实青舟 Logo、标准库重点卡、五张入口卡和真实“继续工作 / 最近核算”内容。没有项目或记录时显示真实空状态。
- 统一公共页面的 V4 色彩、字体、间距、卡片、输入、表格、选项卡、焦点/悬停样式；新增一个 SVG 下拉箭头并加入既有发布资源白名单。
- 标准库和参数库采用标准中性文案。分发逻辑只把 `STANDARD_ID` 路由到炭素材料专属核算页；未开放标准不会进入该页。没有建立多标准插件或通用计算表单。
- 炭素材料页面的八类排放源入口改为 V4 四列网格，只调整布局，不改变输入、Calculator 或计算语义。
- 核算记录列表改为七列完整可访问表格，保留真实搜索、状态筛选、行内打开、键盘 Enter、删除确认与审计留存。详情是独立视图，保留两个页签及冻结输入/计算依据；首个页签仅排版已有冻结摘要，完整显示 ET、ES、净间接排放量和全部提醒。
- 保留现有正式 Word 导出入口和语义；没有修改 Record、Calculator、Canonical、Excel 导入、报告模型、模板、渲染器或历史快照。
- HTML→Qt 视觉映射和真实 Windows 截图见 `docs/ui/HTML_V4_QT_MAPPING.md` 与 `docs/ui/v4-evidence/`。

## 验证

- 定向命令 `python -B -m unittest tests.test_g03_shell tests.test_g04_catalog tests.test_g07_records.G07UiTests tests.test_g08_delivery tests.test_main_integration_ui tests.test_p3_c_records_ui tests.test_uat03_page tests.test_uat02_geometry`：84 项通过，0 失败，耗时 432.237 秒。
- 按首页反馈移除页头副文案后复测 `test_home_is_a_safe_empty_workbench` 与 `test_home_recent_work_shows_saved_project_and_immutable_record`：2 项通过，0 失败，3.285 秒。
- 相关复测命令覆盖首页空/有数据、标准搜索与白名单分发、发布资源白名单：6 项通过，0 失败，耗时 10.386 秒。
- 14 个改动 Python 文件用内存 `compile()` 完成语法检查；`git diff --check` 通过。首次 `compileall` 在本机因沙箱不允许写入 worktree 的 `__pycache__` 失败，故改用不写缓存的内存语法检查；Windows CI 仍会按现有 workflow 执行 compileall。
- Windows 原生 Qt 进程生成并目视检查了 1600×900 主要页面、1366×768 和 1920×1080 首页截图；Qt 报告 DPR 1.0 / 96 logical DPI。125% Windows 系统显示缩放未在本机切换，也未声称实测。截图夹具使用隔离临时 Catalog/Project 和合成冻结 Record。
- 本机 Python 3.13 的一次全量测试试跑在 125 项通过后由执行者手动中止，没有完整汇总，不计为全量通过；正式 Windows Python 3.12 CI 为验收依据。
- GitHub Actions run [#211](https://github.com/adgo07/GHGTOOL/actions/runs/38254589528)，PR 代码 head `bbecb302f5611db40b1e30aed62d3221e107176f`：Windows/Python 3.12 全量测试 466 项通过，失败 0、错误 0、跳过 0，耗时 1762.270 秒，汇总 `OK`。规范校验、编译、依赖、数据库重建、UIR04 GUI 与 1.25/1.5 缩放步骤均成功。
- 同一 run 的 exact-head standalone audit 成功：独立目录构建、发行目录和归档清单检查、provenance、启动 smoke test、上传均通过。
- run #209 两次旧 30 分钟 job 尝试在时间上限处取消，日志中没有断言失败；仅将现有全量测试 job 的时间上限调整至 40 分钟，未另建 CI。

## 等待事项

PR 需等待 Owner 最终视觉确认和独立验收；PR2 不自动合并。PR1 既有 C.4 饱和温度来源 OPEN 项未在本轮处理。
