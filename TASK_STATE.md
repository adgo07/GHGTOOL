# 当前任务状态

状态：IN PROGRESS — GHG-UAT03 新建核算页面V2改造
最后更新：2026-10-09

用户明确授权以V2与三张参考图为正式需求基线，在02:43额度重置后继续。已实际核对origin为adgo07/GHGTOOL、默认main、fetch、HEAD与工作区；从已合并PR35/36的最新main ff15061d2d765dbff869a0b182af4432d09398bc创建codex/uat03-new-accounting-v2，独立工作树原始干净；原checkout用户Excel/Word/锁文件保留。

范围：8排放源卡片、企业搜索、自定义周期整行、重复明细首条保留与启停保留输入、燃料双路径/自定义、过程与烟气压缩、统一电力与热力、当前正式Record直接Word导出。取消非化石电力自动证明前置由用户明确批准，必须先登记软件决定与新旧版本追溯；地区因子仅从已批准Catalog/Resolver读取，不硬编码或跨有效期误用。不修改Excel模板、重录公告、新增标准/数据库/依赖或升级Frozen基线。

中央locked SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，已读locked Architecture/Numeric/Profiles；当前ACTIVE UI指南v0.2、产品家族规格与轻量验收清单按最新GUIDE_INDEX读取，旧v0.1仅历史。这里只采用当前newpage适用部分，不顺手重构首页/导航/记录页。最低读取已覆盖本仓路线、交接、台账及报告架构/schema。

Luna/max三个子agent分别实施页面、参数/规则和共享Word/企业候选。正式验证尚未开始，不沿用上轮344/344或CI176宣称本轮通过。新PR须完成独立验证并交用户实际操作验收，此任务没有预先合并授权。

稳定断点：共享Word导出与企业候选查询已实施；企业候选按Record创建时间/Project现有更新时间跨库排序，无数据库迁移。主agent独立运行 `python -m unittest tests.test_architecture_boundaries tests.test_numeric_contract_v1_adoption tests.test_canonical_project_inputs tests.test_electricity_2023_catalog tests.test_electricity_region_persistence -q`：30/30通过；`python -m unittest tests.test_rs03_excel_entrypoints tests.test_main_integration_ui -q`：15/15通过。`python scripts/validate_canonical.py`通过（9 standards / 12 sources / 102 parameters / 138 factors）；`python -m pip check`通过。均为本地执行、实现中的断点证据，非最终全量或CI验收。
