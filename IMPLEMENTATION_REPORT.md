# GHG-UI-P3-DF 实施报告

日期：2026-10-10。范围：参数与因子库（D）及新建核算视觉收敛（F）。交付单一独立 PR，等待验收，不自行合并或开始 C/E。

## 基线与平台 / Contract 预检查

PR37（UAT03 V2）与 PR38（AB）已通过 GitHub API 核实合并。从执行时最新 origin/main `a51afbcf684e3845369977e42adc938866726d0b` 创建 `codex/ghg-ui-p3-df`。产品源码修正提交 `a267881b9de2d965d44152b9a62c13cd4e38fb9d`；最终 PR head 以 PR 正文和最终 head 的 CI checks 为准，后续文档/截图提交不改变产品源码。

Locked central `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变。本任务不涉及中央公共 Contract。Architecture V2.1 的分层要求保持，Qt 状态仅在 Presentation；不增加公共包或跨仓运行时依赖。中央正式合并 `854b544563260f9e79c73e714c85f6589e0f19b3` 的 UI v0.2、家族规格、验收清单及 Phase2 三份规范作为 ACTIVE / EVOLVING 指南使用，不构成 Frozen adoption。无 Contract 冲突，无需中央变更。

Standard Issue 台账现有 8 项均 RESOLVED；本包不改变标准解释、标准支持状态或正式业务规则，未发现需要新裁定的标准问题。

## 实际修改

- D：`packages/ui/catalog_pages.py` 仅 `ParameterFactorLibraryPage` 和必要 import。紧凑查看方式/筛选；搜索突出参数名称、值、单位、来源与条件；详情独立滚动，追溯渐进展开；来源期间、年度、类型、原始值与定位可查；可调列宽、换行、工具提示、键盘操作与只读保留。查询仍调用现有服务，显示映射每次刷新读取一次。
- F：`packages/ui/carbon_material_page.py` 仅 `_build_page`、新增页面局部样式及 import。企业与周期对齐，长标准换行，活动区控件/按钮/八类启用状态统一；检查计算区两行；结果总量和状态在计算依据前。未改任何其他既有方法。
- 测试：新增 `tests/test_p3_df_factors.py`、`tests/test_p3_df_accounting.py`；新增隔离离屏证据脚本 `scripts/p3_df_ui_acceptance.py`。
- 治理与证据：更新 HANDOFF、TASK_STATE、REFERENCE_STANDARD_ROADMAP、当前实施报告，新增 `docs/ui/p3-df/ACCEPTANCE.md` 及本包证据。

保护审查确认 StandardLibraryPage 和 7 个共用 helper 源码与 base 一致；F 其他 183 个既有方法与 base 一致；报告/按钮相关 37 条初始化语句一致。Application、Domain/Core、Persistence、标准/参考数据、Resolver、Numeric、Calculator、Canonical、Project/Record、Shell、首页、记录、导入、报告导出和 platform-lock 均不修改。

## 验证记录

详细命令、数量、截图与未执行项见 `docs/ui/p3-df/ACCEPTANCE.md`。先 D 专项 17/17 通过后进入 F；F 新增布局 3/3 通过。F既有定向102/102通过。本地隔离全量410项：409通过、1项独立地区标签兼容失败；已恢复原展示字段，修复后专项结果见验收记录。独立程序构建/审计/两次启动通过，构建来源为修正前b8fc4bc；最终head的完整回归与独立构建以PR的Windows CI为准，不能将本地首次全量称为全部通过。

截图全部为本次 Windows PySide6 离屏自动化，使用临时 Catalog/Project 和内存 Record。正式结果截图由明确夹具调用现有 Calculator/Application 路径生成，非预制结果、非用户数据。离屏字体补注册 Segoe UI 解决 CO₂ 下标缺字，不改单位文字。

## 并行兼容与未解决项

EXB01 `codex/exb01-appendix-b-ingress` 和 RPT02 `codex/ghg-rpt02` 均未合并。只核对状态与路径，不取未合并实现；其 UI 改动分别涉及 pages.py、record_experience.py，DF不改这两文件。F避开报告相关组件与按钮。四份共享治理文档存在后续合并冲突，应按交付时事实整合。

原生 Windows 两种分辨率、系统 100%/125%/150% DPI 的鼠标、键盘和滚动验收 **OPEN**：正式 Computer Use 入口初始化失败，错误为 `windows sandbox failed: helper_unknown_error: setup refresh had errors`。离屏自动化不代替实机验收，不声称全部 UI 验收通过。窄屏八类选择条和长表格保留横向滚动，详情保留独立纵向滚动。

本次未扩展业务修复。待独立验收后再决定后续任务；不自行合并，不开始 C/E，不修改中央 UI 规范。
交付同步：PR创建后主线合入RPT02 #39；接收已合并main@029ebe6fa6081e3d742ba3900e641e4c4f6aecf0，只整合四份共享治理文档。RPT02业务保持主线原样，证据见docs/rpt02/ACCEPTANCE.md。初始DF base不变，最终head与merge-ref CI以PR41为准。本地同名用户Excel原始文件先保护到忽略目录，合并提交后恢复原路径，不作为DF改动提交。
