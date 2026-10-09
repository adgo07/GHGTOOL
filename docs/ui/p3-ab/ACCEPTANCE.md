# GHG-UI-P3-AB 联合验收记录

本记录只覆盖 Shell、首页、导航与标准库；不是新的产品路线。最终 PR head 以 PR 元数据为准，完成后等待独立验收，不自行合并。

## 平台 / Contract 预检查

- 业务仓 origin：`https://github.com/adgo07/GHGTOOL.git`。
- Baseline：`708f78a455790946b4a728029bba768d8fb295fc`；分支：`codex/ghg-ui-p3-ab`，从最新 `origin/main` 创建。
- PR #37：GitHub API 核实 `merged=true`，合并时间 `2026-10-09T06:56:57Z`，merge commit 与本包 baseline 相同；未复用旧 feature branch。
- 开工时 tracked 文件干净；既存未跟踪的 docs Office 参考文件及 `tmp-rs03-review/` 原样保留。
- Locked central SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`。读取该版本 Architecture V2.1 Frozen 的分层边界：Qt 状态留在 Presentation，业务层不依赖 Qt，不新建公共 UI package 或跨仓运行时依赖。
- 本任务不涉及中央公共 Contract。Numeric、Unit、Workspace、Record、qzpack 的公共语义不变；不修改 `platform-lock.json`、Calculator、Canonical、Schema、迁移和历史记录。
- 中央 UI 依据：已验证 origin 的 `Qingzhou-contracts origin/main@854b544563260f9e79c73e714c85f6589e0f19b3`；读取 v0.2 指南、家族规格 v0.1、验收清单 v0.1、Phase 2 的 INTERACTION_SPEC / VISUAL_SPEC / PYSIDE6_REFERENCE。均为 ACTIVE / EVOLVING，不作为 Frozen adoption。
- 中央工作区有未提交原型证据；本包只读已合并 Git 对象，不使用其未提交内容。未移植原型 HTML/CSS/JavaScript 或演示数据。
- 冲突分类：无 Frozen Contract 冲突，无需中央 Contract 变更。产品现有显式 Excel 保存项目与预览分开，沿用主线真实能力。
- Standard Issue：现有 001～008 均已登记；本包不改变既有解释、不新增标准疑义或正式支持状态。

## 顺序与保护范围

先完成 A 并通过 A 定向测试，再实施 B；最后进行 AB 联合回归和 Windows CI。仅改 Presentation、界面资源、相关测试与治理记录。

`RecordLibraryPage`、`ExcelImportPage` 的业务结构、`ParameterFactorLibraryPage`、核算页、项目保存恢复、正式 Record 和关闭确认保持原有行为。标准库删除可见来源区域不删除底层来源或追溯。

## 中央 A 类规范对应

| 规范 | 本包对应与边界 |
|---|---|
| A-01～A-05 | 启动无侧栏首页；标准库优先；设置独立；业务页淡蓝侧栏、顶部真实 LOGO、底部设置，首页入口返回无侧栏首页 |
| A-06 / A-16 | 真实青舟 LOGO、统一 SVG、专业简洁风格；不引入公共 package |
| A-07 | 首页真实项目/记录或准确空态；软件支持与标准状态分开，未实现核算保持门禁 |
| A-08 / A-09 / A-17 | 关键词与状态两个查询控件、固定五列、编号/名称双入口；详情连续三分区，去除禁止可见区域，保留原文和核算门禁 |
| A-18 | 对用户显示“表格导入”，内部 `AppRoute.EXCEL_IMPORT` 和格式/API 不变 |
| A-10～A-15 | 记录、表格导入结构、因子库及新建业务页面的进一步改造不属于本包；保留当前真实功能，不提前实施 C/D/E/F |

## EXB01、RPT02 兼容性

开工检查：当前主线文本、远端分支命名及 PR 搜索未找到 EXB01 / RPT02 分支或 PR；认证 API 当前 open PR 集合为空。进一步检查 Codex 对话，发现“完善附录B Word报告”已接收 GHG-RPT02 任务，但因 helper_unknown_error 环境启动失败而 BLOCKED，明确尚未修改文件或创建分支。未找到 EXB01 已启动的可核验证据。不从任何未合并分支取代码。

潜在文件交集为 `product.py`、`shell.py` 与同一 `pages.py`；本包将修改限定为 Shell、HomePage 和必要的“表格导入”显示词汇。后续 Excel 或报告任务仍应重新检查上述文件合并冲突；ExcelImportPage / RecordLibraryPage 的业务结构和报告、解析实现不在本包变更范围。

交付前复查：RPT02 已恢复，并从同一 main 在独立工作树创建 `codex/ghg-rpt02`，当前处于实施中。只读取其文件名清单：reporting/model.py、word_renderer.py、ui/record_experience.py、pyproject.toml、scripts/build_standalone.py 与新增 appendix_b 布局文件/模板；本包不修改这些业务文件。当前明确交集为 TASK_STATE.md，后续若报告包同步 HANDOFF / IMPLEMENTATION_REPORT 也需手工整合当前状态。仅核对元数据和变更路径，不读取或合入未合并实现。EXB01 仍无可核验启动证据。

## 实机证据边界

自动测试、Windows PySide6 离屏截图、原生人工操作分别记录。截图脚本使用隔离临时 Catalog 与内存 Record，不读取用户项目或生成正式记录；逻辑窗口尺寸、截图像素尺寸和 Qt scale factor 均写入对应 JSON，不把 Qt 缩放模拟称为真实 Windows 显示设置变更。

原生操作：**OPEN**。Computer Use 的 node_repl 两次初始化失败，返回 `trusted Node process exited unexpectedly` / `windows sandbox failed: helper_unknown_error: setup refresh had errors`，未能控制真实窗口。需独立验收者在原生 Windows 程序中完成两种分辨率与 100% / 125% / 150% 系统 DPI 的鼠标、键盘及缩放核查。离屏通过不代替此项。

## 联合验收项

| 用户要求 | 自动证据 | 状态 / 限制 |
|---|---|---|
| 启动无侧栏、业务有侧栏、首页顺序与导航名 | G03 9/9；截图脚本六组检查 | PASS（自动），原生 OPEN |
| 页面切换、未完成输入与项目/单元状态保留 | 项目/记录/导入/UAT03 保护回归 68/68；截图脚本连续切页 | PASS（自动） |
| 关键词与状态、五列、两可点击入口正确 ID | G04 + P3AB 22/22；鼠标与 Enter 用例 | PASS（自动），原生键盘 OPEN |
| 独立单页三分区、无禁止可见内容 | P3AB 详情结构及连续切换清理用例；详情截图 | PASS（自动） |
| 原文 URL 与核算门禁 | 缺 URL、通则、未开放、非现行、允许标准测试 | PASS；没有扩大支持 |
| 因子库、记录与表格导入保护 | 68 项保护回归；类正文与 baseline 对比 | PASS（自动），联合全量见实施报告 |
| 长名称、空态、滚动恢复、窗口缩放 | in-memory 长名称 fixture、无结果截图、非零外层/水平滚动恢复、六组尺寸/Qt scale | PASS（自动）；真实系统 DPI OPEN |
| 标准要求可靠内容 | 无结构化可靠内容时准确占位，未编造条款/因子 | PASS（边界）；权威内容补充另包 |
| 全量、构建、Windows CI | 命令、数量、commit 与执行来源逐项列于 IMPLEMENTATION_REPORT | 完整结果以该报告及最终 PR checks 为准 |

A 先通过 G03 定向，再进入 B。B 最终文案后 22/22。AB 使用代码 commit `12bab994e0b8afcec1f73740c1db59ae729e25f3` 的干净 archive 做全量，后续仅补充既有测试夹具的 Windows 清理顺序及治理证据；业务代码不变。首次探索失败、修正和未执行尝试均在实施报告公开，不把重叠测试数相加。

## 可复现截图

以下均为本地 Windows Python 3.12 / PySide6 的 **offscreen 自动证据**。执行命令模板：

```text
python scripts/p3_ab_ui_acceptance.py --width 1366 --height 768 --scale 1.0 --output-dir tmp/p3-ab/capture-final
```

分别执行两组逻辑尺寸（1366×768、1920×1080）与三档 Qt scale（1.0、1.25、1.5），六组各 15/15，共 90/90 检查。每组包含首页、标准列表、详情与无结果四张图以及来源哈希/逻辑尺寸/物理像素/比例 JSON。使用 Windows 已安装微软雅黑注册到离屏字体系统；没有复制模拟业务数据进产品。

| 逻辑窗口 / Qt scale | 首页 | 标准列表 | 标准详情 | 空态 / 元数据 |
|---|---|---|---|---|
| 1366×768 / 1.0 | [首页](evidence/1366x768-100-home.png) | [列表](evidence/1366x768-100-standards.png) | [详情](evidence/1366x768-100-standard-detail.png) | [空态](evidence/1366x768-100-standards-empty.png) / [JSON](evidence/1366x768-100.json) |
| 1366×768 / 1.25 | [首页](evidence/1366x768-125-home.png) | [列表](evidence/1366x768-125-standards.png) | [详情](evidence/1366x768-125-standard-detail.png) | [空态](evidence/1366x768-125-standards-empty.png) / [JSON](evidence/1366x768-125.json) |
| 1366×768 / 1.5 | [首页](evidence/1366x768-150-home.png) | [列表](evidence/1366x768-150-standards.png) | [详情](evidence/1366x768-150-standard-detail.png) | [空态](evidence/1366x768-150-standards-empty.png) / [JSON](evidence/1366x768-150.json) |
| 1920×1080 / 1.0 | [首页](evidence/1920x1080-100-home.png) | [列表](evidence/1920x1080-100-standards.png) | [详情](evidence/1920x1080-100-standard-detail.png) | [空态](evidence/1920x1080-100-standards-empty.png) / [JSON](evidence/1920x1080-100.json) |
| 1920×1080 / 1.25 | [首页](evidence/1920x1080-125-home.png) | [列表](evidence/1920x1080-125-standards.png) | [详情](evidence/1920x1080-125-standard-detail.png) | [空态](evidence/1920x1080-125-standards-empty.png) / [JSON](evidence/1920x1080-125.json) |
| 1920×1080 / 1.5 | [首页](evidence/1920x1080-150-home.png) | [列表](evidence/1920x1080-150-standards.png) | [详情](evidence/1920x1080-150-standard-detail.png) | [空态](evidence/1920x1080-150-standards-empty.png) / [JSON](evidence/1920x1080-150.json) |

Qt scale 模拟增加截图物理像素，不等价于在对应物理分辨率的原生桌面上更改系统 DPI。此表不宣称原生六组合通过。

## 独立验收与暂停点

交付一份独立 PR，原生实机项目保持 OPEN，等待独立验收。不得自行合并；AB 完成并合并后 Phase 3 暂停，C/D/E/F 按后续任务和 EXB01、RPT02 实际状态独立开展。当前标准支持状态、RS04 / RS05 出口和 Frozen 基线均不因本包改变。


## 最终证据追溯修正（合并前）

GitHub Code Review 指出第一版六组离屏截图 JSON 记录的 `packages/ui/pages.py`、`packages/ui/catalog_pages.py` SHA256 与所审 PR head 不一致。该问题属于截图证据版本不一致，不能引用旧证据冒充最终代码。

已通过 GitHub-hosted Windows / Python 3.12 从最新实际 PR 源文件重新运行 `scripts/p3_ab_ui_acceptance.py` 六组（1366×768、1920×1080，各 100% / 125% / 150% Qt scale），更新 24 张 PNG 和六个 JSON；每组 15/15，总计 **90/90 PASS**。六份 JSON 的五个源码哈希完全一致，其中：
- `packages/ui/pages.py`: `0a453c571a04879a2a1c8067973fa848d9eea103fd4283afe47bceeb33b51a4f`
- `packages/ui/catalog_pages.py`: `e8c98cadb7477fe5ed481b620b56bae2b4cdac5bb7fb91e8ebcb3b22550689aa`

执行与校验时检查了 manifest 声明的源码与磁盘文件 SHA256 一致。修正未修改业务生产代码，不改变 UAT03、Catalog / Calculator / Record 语义。

**证据结论：** 新版离屏检查 PASS；不是原生 Windows 鼠标人工操作的替代证据。原生人工验证的证据出处应由独立验收结论提供，不能仅凭六组离屏截图宣布原生 DPI PASS。
