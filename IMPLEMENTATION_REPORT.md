# GHG-UI-P3-DF 实施报告

日期：2026-10-10。范围：参数与因子库（D）及新建核算视觉收敛（F）。交付单一独立 PR #41；已通过独立验收，接收最新main后完成最终CI再合并，不在本包开始 C/E。

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

EXB01 `codex/exb01-appendix-b-ingress` 和 RPT02 `codex/ghg-rpt02` 开工时均未合并；交付时RPT02已通过PR39合并并接收已合并main。只核对未合并分支状态与路径，不取未合并实现；其 UI 改动分别涉及 pages.py、record_experience.py，DF不改这两文件。F避开报告相关组件与按钮。四份共享治理文档存在后续合并冲突，应按交付时事实整合。

原生 Windows 两种分辨率、系统 100%/125%/150% DPI 的鼠标、键盘和滚动验收 **OPEN**：正式 Computer Use 入口初始化失败，错误为 `windows sandbox failed: helper_unknown_error: setup refresh had errors`。离屏自动化不代替实机验收，不声称全部 UI 验收通过。窄屏八类选择条和长表格保留横向滚动，详情保留独立纵向滚动。

本次未扩展业务修复。待独立验收后再决定后续任务；不自行合并，不开始 C/E，不修改中央 UI 规范。
交付同步：PR创建后主线合入RPT02 #39；接收已合并main@029ebe6fa6081e3d742ba3900e641e4c4f6aecf0，只整合四份共享治理文档。RPT02业务保持主线原样，证据见docs/rpt02/ACCEPTANCE.md。初始DF base不变，最终head与merge-ref CI以PR41为准。本地同名用户Excel原始文件先保护到忽略目录，合并提交后恢复原路径，不作为DF改动提交。

合并后专项：在工作树直接运行21项时，RPT02模板哈希一项因用户原Excel与主线批准副本不同而失败（20通过/1失败，16.227秒），没有修改原文件或弱化断言。随后git archive 3207998隔离运行相同命令：python -m unittest tests.test_electricity_2023_catalog tests.test_p3_df_factors tests.test_p3_df_accounting tests.test_rpt02_appendix_b -v：21项、12.942秒、OK。合并后六组Qt检查再次390/390通过，48图及6份JSON已更新并核对源码hash。完整CI需验证最终head的421项与独立构建。


## PR #40 EXB01 合并后的本次最终整合

已验收并合并的EXB01（PR #40）在 `main@242b535178dcf98ad69b025f14c9f5ed5bd03557`；此前RPT02（PR #39）已合并。PR #40已完成其附录B整工作簿输入与RPT02 Word报告联合回归（Windows CI 442/442、standalone审计PASS），历史原生Excel/WPS保存后回导仍明确OPEN。EXB01完整合并报告可由Git历史 `242b535178dcf98ad69b025f14c9f5ed5bd03557` 的 `IMPLEMENTATION_REPORT.md` 及原PR #40查看，本报告不覆盖其证据真值。

本DF PR #41原head `942f16e682c03d6f9b1e05bf4ecba8fef1b42bbd` 的新建核算与因子库生产源码并未与EXB01文件交叠；本次只保留两包已验收的各自变更，整合四份当前治理文档，未重构RPT02/EXB01业务。后续两项Windows CI应绑定新增的PR #41最终head，准确记录全量测试与独立安装包审计结果；旧head的421项CI成功只作历史证据。原生Windows人工输入和缩放仍OPEN，不用Qt离屏模拟冒充。
