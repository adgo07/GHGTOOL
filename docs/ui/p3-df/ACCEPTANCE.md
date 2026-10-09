# GHG-UI-P3-DF 验收记录

本包仅参数与因子库（D）和新建核算视觉收敛（F），不是新的产品路线。按 D实现→D专项测试→F实现→F专项/联合回归顺序交付一个PR，不自行合并、不启动C/E。

## 前置与平台 / Contract 预检查

- 仓库origin核实为 https://github.com/adgo07/GHGTOOL.git，默认分支main；执行时fetch后base为 `a51afbcf684e3845369977e42adc938866726d0b`，独立分支 `codex/ghg-ui-p3-df`。
- GitHub认证API确认PR37 merged=true（2026-10-09T06:56:57Z），PR38 merged=true（2026-10-09T14:17:01Z）；PR38 merge commit就是本包base。未复用AB分支，不重复AB改造。
- 开工tracked工作树干净；既存未跟踪Office参考文件、其他工作树、.codex-run和旧临时参考目录保护，不提交、不清理。
- Locked central `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变。本任务不涉及中央公共 Contract，不修改Frozen、platform-lock、PLATFORM_BASELINE。相关Architecture V2.1 Frozen要求Presentation/Application/Domain/Infrastructure分层，Qt状态留在Presentation，不增加公共PySide6包或跨仓运行时依赖。
- MUST：来源浏览/全库搜索/只读详情保留；值、单位、条件、来源期间、数据类型和来源定位仍可查；UAT03 V2作为业务基线，八类开关、动态明细、输入精度、来源、参数门禁、计算、项目/单元/历史Record行为不变。
- MUST NOT：修改Application、Domain、Repository、Schema、Migration、Canonical、Catalog、Reference Data、Resolver、计算候选、公式、Numeric、Calculator、Project保存恢复、Record生命周期、报告生成或导出业务；不改AB、C/E和未合并EXB01/RPT02实现。
- Standard Issue：当前台账8项均RESOLVED；本包不改变标准事实或既有软件解释，不增加正式标准支持范围。无新标准疑义；若发现真实业务问题只单独记录。

## 中央指南与并行任务

已核实中央origin并fetch，只读取正式合并 `854b544563260f9e79c73e714c85f6589e0f19b3` 的UI v0.2、家族规格、验收清单、Phase2 INTERACTION_SPEC / VISUAL_SPEC / PYSIDE6_REFERENCE。ACTIVE / EVOLVING不作为Frozen adoption；旧原型截图/HTML及其历史产品基线不替代当前源码。

EXB01已在独立 `codex/exb01-appendix-b-ingress` 工作树实施（相对当前main有33个变更路径，未合并），RPT02独立 `codex/ghg-rpt02` 有37个变更路径，未合并。只核对状态和路径，不取未合并实现。前者UI交集候选为pages.py，后者为record_experience.py，本DF均不修改；catalog_pages.py/carbon_material_page.py未见其改动，但F仍避开报告按钮及组件。四份共享治理文件需后续按真实工作包状态整合，不覆盖其他工作树的修改。

本仓HANDOFF/路线仍称AB当前，是已合并阶段的文档滞后；用户已明确授权DF，属于本地阶段记录更新，不是Frozen冲突。无实质Contract冲突，无需中央变更；不升级正式支持状态或启动RS04/05。

## 自动化、离屏与原生证据边界

本地测试、GitHub Actions、Qt离屏截图、原生窗口操作分别记录。截图使用隔离临时Catalog和测试项目/Record，正式计算截图仅由明确测试输入调用现有计算路径生成，不读取用户数据、不伪造结果。

原生Windows检查 **OPEN**：2026-10-10通过Computer Use正式入口初始化，node_repl返回 `windows sandbox failed: helper_unknown_error: setup refresh had errors`，未能操作真实窗口。不能把离屏或Qt scale模拟称为100%/125%/150%系统DPI实机通过。独立验收须补两种分辨率的原生鼠标、键盘、滚动和缩放检查。

## 当前实施与验证

D与F尚在执行，最终命令、实际数量、截图及CI结果在交付前补齐。不沿用AB旧截图或旧测试结果冒充本包证据。
