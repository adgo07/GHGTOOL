# 当前任务状态

状态：GHGTOOL HTML V4 正式落地 — PR1 已合并（PR #44）；PR2 独立 PR #45 已追加 V4 页面反馈跟进提交 `3b60a9f7aed988b8c18fdc32d0ac47b3a5e5ae77`，当前待推送并执行新 Head Windows CI，之后等待 Owner 最终视觉确认和独立验收。

最后更新：2026-10-13。工作分支：`codex/ghg-html-v4-pr2`；基线为 `origin/main@204dded5d03853617f79a1f05693e89b619df9d1`。原 `codex/ghg-ui-p3-df` 脏工作区保持未动。

- Owner 已确认首页样板；按反馈移除入口卡片前的演示提示标签，保留 V4 主标题副文案，并用隔离 Project/Record 夹具确认“继续工作”和“最近核算”展示具体内容。
- 已更新 1600×900、1366×768、1920×1080 首页截图；保留 V4 主标题说明，且项目与最近记录均有实际展示内容。
- 公共页面沿用中性标准文案；标准分发仅允许 `STANDARD_ID` 进入炭素材料专属核算页。记录列表改为 V4 七列表，记录详情保持两个页签；八类源卡片为炭素材料模块专属四列布局。
- 全页 Windows Qt 截图和 HTML→Qt 映射说明位于 `docs/ui/v4-evidence/` 与 `docs/ui/HTML_V4_QT_MAPPING.md`。已检查 1600×900、1366×768、1920×1080；当前环境 DPR 1.0 / 96 logical DPI，125% Windows 设置未更改或伪称已验收。
- 定向回归 84 项通过、相关复测 6 项通过、首页反馈后复测 2 项通过；GitHub Actions run #211：Windows Python 3.12 全量测试 466 项通过，standalone audit/build 成功。
- 2026-10-13 收到的 V4 页面差异已纳入 PR #45：最近核算表列宽与“打开”对齐、标准目录列宽/字号/链接悬停/状态标签、排放源入口共用 Mapping 名称并与八张卡分组一致、深蓝标题条、燃料标签、煅烧/焙烧/石墨化分别 4/6/8 个默认物料行及真实 Catalog 因子库。工序默认空物料行不会写入 Canonical；项目保存/恢复保留各行身份及既有类别索引。
- 已核对正式 V4 交接包的 HTML、定稿说明和三张配套截图。V4 明确使用下拉箭头，因此保留箭头；同时支持点击输入区域展开候选，保留键盘选择。打字不触发布局重排，结构变化后刷新页面尺寸提示；下拉点击过滤仅处理标记过的可搜索输入框。
- 本机 17 项唯一界面/项目定向用例通过；事件过滤收窄后复跑 4 项相关测试通过，UIR04 GUI 验收脚本 A–E 通过；`git diff --check` 通过。
- Windows CI #214 全量 470 项发现 3 failures / 10 errors；相关过期夹具/断言和动态行尺寸缓存问题已修复。head `6403371` 的 #215 前置、UIR04 和缩放通过，但 full-test 达到 40 分钟 job 时限而取消，standalone audit 跳过。随后将点击事件处理收窄到可搜索输入框；head `3545030` 的 Windows CI #216 已全部通过：Windows/Python 3.12 全量 470 项、UIR04 A–E、1.25/1.5 缩放、standalone 14 项交付测试、目录/归档/provenance 审计和双次启动 smoke test。
- 后续 Owner 反馈收口后，现地 Windows 1600×900 截图已更新：因子库搜索表为“参数名称/数值/单位/类别”，来源浏览保留真实 Catalog 原始表列；新增焙烧六行、石墨化八行截图。当前改动定向回归命令共 7 项通过；提交 `3b60a9f` 的 Windows CI 尚待运行。
- 本任务未修改 Frozen Contract、计算语义、Excel 导入规则、数据库 Schema 或正式报告业务；PR2 独立提交，不自动合并。原 `codex/ghg-ui-p3-df` 脏工作区保持未动。

中央 Frozen baseline 继续锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。
