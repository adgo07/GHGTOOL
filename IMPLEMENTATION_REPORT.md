# GHG-UAT03 V2实施报告

日期：2026-10-09。状态：IN PROGRESS。

## 平台 / Contract 预检查

实际业务起点main ff15061d2d765dbff869a0b182af4432d09398bc，origin/default branch/工作区已核验；独立codex/uat03-new-accounting-v2不覆盖用户实测文件。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；已读取locked Architecture V2.1、Numeric v1、Profiles v1及当前ACTIVE Policy/标准开发指南/UI v0.2/家族规格/验收清单。

MUST：UI/Application/Domain/Infrastructure分层；库与Resolver唯一默认参数链；共享Calculator；Decimal40/HALF_UP与ambient independence、full-value exact比较；输入保存保留完整decimal，展示修约不回流；成功新增不可变Record、致命失败不新增；Word只读正式快照；旧项目/历史Record保留。

MUST NOT：UI硬编码重复因子清单、UI另写正式公式、当前Catalog重算历史、Qt状态冒充公共Workspace、升级Frozen/增加标准范围/复制标准全文。本轮内部可选地区字段及UI适配不新增公共Contract；ALLOWED PROJECT DIFFERENCE继续为项目Numeric Profile。无需中央Contract修改。

Standard Issue：用户V2明确批准取消非化石电力自动证明前置；新问题/Software Decision须先登记再实现，冻结Mapping保留。地区因子的适用性与实际来源需保持。既有001～006与44/12、蒸汽查表、过程K参数计算不变。

## 授权、范围与当前验证

正式需求见docs/uat03/NEW_ACCOUNTING_V2_REQUIREMENTS.md及用户三图；这是本次需求副本，不是第二条产品路线。UAT03属于既有参考标准路线内新建页与记录业务链工作包。输入模板/Word排版与其他页面重设计仍不在本包；新建页仅复用已有Word输出流程。

当前处于实现，不宣称测试/原生视觉/构建通过。三个Luna/max子agent分工，主agent负责接口、标准决定与版本复核、完整回归与独立验收。需要computer use时使用Astra/low子agent；无法取得原生证据必须明确未执行，不以离屏冒充。

治理文档与中央当前事实中的Excel只读旧描述已落后于已明确授权合并PR35的独立正式计算链；本轮不修改或退回Excel，按用户既有授权保留，避免把展示任务扩成能力回退或治理改版。
## 原生界面验证状态

2026-10-09 Astra/low子agent按computer-use技能尝试初始化原生Windows接口，两次均失败：`node_repl kernel exited unexpectedly` / `windows sandbox failed: helper_unknown_error: setup refresh had errors`。没有启动用户现有应用、操作已有窗口或取得原生截图；工具限制不得通过自建UIA/helper绕过。

1366×768和1920×1080下的原生排版、滚轮、可搜索下拉、增删行、启停恢复、错误定位和Word按钮业务操作均未执行。后续Qt离屏尺寸/逻辑测试仅提供技术证据，不作为原生验收通过；最终需用户实际操作验收。
