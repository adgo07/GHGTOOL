# 当前交接：中央 UI 指南呈现收口

2026-11-10。最新候选为 `codex/ui-guideline-closeout`，基于已合并PR62 / `224442530fcc61d8224c45e486688b2c27ec9324`。状态、逐项范围、测试与原生OPEN见TASK_STATE和IMPLEMENTATION_REPORT；8张源码离屏图及源hash在docs/ui/guideline-closeout。父代理代码与范围内Qt回归独立检查通过，尚未push/PR/CI/打包，不冒称正式发布。无Goal。

保留既有核算/输入/项目/不可变Record/Word/官方母版和Frozen lock。本轮只有Presentation增量；PR63 `f4ed05d3195ba5d5edfe4172e00dffbd96a691cf` 仍未合并，carbon_material_page.py重叠为顶部按钮与两处hint共3项文案，不自动合并该分支。后续以实际Git核验，旧报告中的“未合并PR62”等是历史记录，不代表当前事实。

---

# 历史交接（PR60已合并，仅保留业务约束）

当前候选产品代码 `fb56ad737b6d0a676e5f594f689e08e88f14aaa3`；仓库以 `https://github.com/adgo07/GHGTOOL.git` 与实际origin识别，不把历史绝对路径当当前checkout。复用 `codex/ui-five-business-pages-v2`；接续前实际核对root/origin/fetch/branch/HEAD/status，不覆盖其他工作区用户修改。

产品及验证结论见IMPLEMENTATION_REPORT、TASK_STATE；字体QA增量仅class前置，原断言体不变，修后整组21/21（119.918s），本地原全量1项失败不改标。图集/源码与限定复核回执在docs/ui/business-pages-v2/refinements-r3。本地裸字体完整运行1121通过/1失败，5371.075s；astra限定视觉PASS。required CI、最新PR head、ZIP/manifest/原始job日志及实际包核验以PR60最终交付回执精确绑定，旧版本不冒用。源独立验收未完成，不自动合并或发布；本阶段交源验收后停止。

必须保持：冻结业务记录只读，每次正式成功新增；项目状态独立projects.sqlite；预览/项目保存/历史查看不生成Record；主查看本次/最新真实Record且历史查看独立；关联失败原恢复提示不吞掉；显示修约不回流计算。普通详情无技术审计入口但底层审计、原完整业务值、来源与旧记录回退保留。Word/冻结表头/母版字节、Calculator/Canonical/DB、首页壳新建核算及中央锁不变。启动日志不能写仍安全拒绝启动，真实用户路径原因未确定。未执行原生桌面/Office/IME/人工DPI/企业样例/干净机。

后续新建核算整页必须独立范围/分支，当前不实施。Owner明确决定：手动访问未启用8源卡启用并展示，已启用只浏览；程序/错误定位/恢复不启用。外部CO₂第九卡是软件补充，访问不自动同意范围声明；未来标准入口仅产品计划。含碳量改业务名称但路径与来源维度分开；电力因子值优先且保留五表/OTHER/零/冲突/无适用不回退。热力“常用入口简化，特殊情况可展开，旧值保留”已获Owner批准，非默认旧值可辨认，不将内部/输出强改外购，不改015防重复计碳和未知边界，不因折叠强写默认或改变dirty；需旧值/特殊/输出/重复计碳守卫，无需重问。不得自动扩标准、改正式结果或中央Frozen。
