# 当前任务状态 — B-HEAT

更新：2026-10-18。状态：LOCAL_CHAIN_PARTIAL / COMPATIBILITY_DECISION_PENDING。当前仅本地候选，不是正式验收PASS或交付。领域断点提交5870ecf871b50431668a9efaf1419ac21e61613b；后续UI/B.9/冻结报告候选与证据见本轮提交。

## 已核基线与范围

业务base为PR51 merge a1aeebc1b6809397e61a2ffa7a2333a3b440c756，origin adgo07/GHGTOOL、fetch、main和起步干净已实际核。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。Architecture V2.1、Numeric v1、Profiles v1按锁定读取；UI当前正式合并指南按中央origin/main读取。MUST：分层、共享内核、声明Profile一致、ambient独立、full-value exact、原/规范/显示值隔离、历史Record/Word冻结；MUST NOT：隐式float、业务epsilon、显示值回流、Qt状态当公共Workspace、自动Frozen升级。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE；本轮不改中央Contract。相关Standard Issue005/006/015/017/019；无新专业解释，C3候选漏项需按既有005/006补齐的确认尚待答复。

C唯一修改共享消费者/资源/GUI/B.9/项目/记录/Word/构建/治理。F的4bdef411只取heat helper/tests两文件。M外部CO₂准备1f73cc82保留独立分支，不在本包生产或送验。N不启动。原用户脏树、旧树、计算表不改。

## 当前实现

- HeatInput增加source_boundary/fuel_emissions_accounted尾字段；codec5读1—4保留值、旧边界UNCONFIRMED，项目可读保存但新正式核算不猜事实。
- 015先分类：内部同边界且供热燃料已计时不重复购热，不要求无关HM/因子，原燃料全值保持；未知/冲突阻断。外送按原公式独立抵扣一次。
- 独立已知焓只消费明确输入；kJ/kg/GJ/kg/GJ/t归一显式Profile，不访问旧表或自动P/T；有限零/负沿既有WARNING采用，不擅变ERROR。方法CAR-HEAT-KNOWN-017.1和Profile/采用值冻结trace。
- heat.factor真实Catalog关联核验、同次Resolver资格/采用值/快照；已选实测空/非法不回默认，合法0保留、证明缺失只提醒。C.3资格漏项尚未修复，不冒称所有历史期间默认已可用。
- 实际统一热力UI有中文边界/燃料声明，草稿保存恢复、源卡状态与内部已计分派一致；已知焓不消费超物性范围辅助状态。B.9 v10/2.8本地字段/识别已接、旧模板原字节保留；Word消费冻结值、内部流转不造购热0或误报缺明细。
- 全局ALGORITHM_VERSION仍FUME.2，包/报告布局元数据及跨阶段当前版本断言尚未同步：相关编辑被拒，未提交送验、未构建或发布。

## 实际验证

| 来源 | 命令/证据 | 结果 |
|---|---|---|
| C本地Python3.12.14 | `python -B -m unittest tests.test_b_heat_chain.HeatQtTests tests.test_b_heat_chain.HeatExcelTests -v` | 6/6，0失败/错误/跳过，41.731s；Qt/Excel/SQLite/Canonical/正式购入输出/冻结Word |
| C本地最后UI修正后 | `python -B -m unittest tests.test_b_heat_chain.HeatQtTests.test_internal_no_unrelated_values_and_boundary_conflict tests.test_b_heat_runtime tests.test_b_heat_specialist tests.test_numeric_contract_v1_adoption -v` | 37/37，0失败/错误/跳过，7.412s |
| C本地既有回归 | `python -B -m unittest tests.test_g06_carbon_material tests.test_uat01b_material_steam -v` | 32项、22FAIL含subtests、0ERROR，2.502s；未收口，不能称通过 |
| C本地实际历史包 | CI273源码bbb1d5b的EXE/PYZ生成两条旧热力Record/Word，再用当前代码调用`verify_frozen_record_word.verify` | 两条ReportModel哈希及Word document.xml字节一致，禁Calculator/Resolver；复制DB、原DB不改 |
| C本地受控母版 | `python -B -m scripts.project_appendix_b_v10 --write`及专属ZIP部件比较 | v10 SHA5dd12be5e78f13e1408e96f4698e725a4c5bf45071923b6c90d75a080437b5e9；仅sheet9变化，v9真实识别 |
| C本地渲染 | Artifact Tool只读导入/render B.9前后PNG并查看 | 新表头/提示可见；不是原生Excel/WPS回导 |

日志/历史生成器/真实包比对证据均在本树tmp/b-heat；未将tmp作为运行时真值源。上述本地结果不是GitHub Actions。本包尚未执行全量、构建、CI或新实际包验证。

## BLOCKED：共享版本和C.3资格兼容

问题：共享Calculator版本/打包/报告元数据同步待用户具体授权；候选heat.factor漏列原有C.3独立来源，旧正式兼容未收口。
证据：自动审批拒绝组合脚本后，又拒绝仅改ALGORITHM_VERSION一行，理由为会影响材料/脱硫/烟气的新Record版本及断言；两个脚本都未执行。现有Canonical资格只列binding-heat_default_2025；Catalog和既有Resolver另有binding-heat_default_gbt32151_34_c3、同资产但不同来源/适用条件，Mapping§9.4/Issue005/006保留C.3。源会话已核该事实并向用户提确认。
为什么不能按原方案继续：不能把C.3伪装成通则来源、按0.11数值相同放行，不能静默把原合法默认改成不可用，也不能用旧FUME.2标记作为新热力交付身份或只改测试掩盖失败。
可选方案A：用户授权共享HEAT.1/当前母版v10元数据/包核验与仅当前版本断言同步；授权补齐准确C.3资格，保留Resolver原来源选择/适用条件，完成早于/跨越/晚于实施日回归。
可选方案B：保留本地候选与证据，暂停正式版本送验，待决策后继续。
建议：A；不改原排放公式、Numeric、历史Record或数据库结构。
需要决策的具体问题：本会话已发版本兼容窄确认；C.3补齐确认由源提出。017自动物性更换实现仍独立待Owner，未加产品依赖、不换库或回旧表。不得重试被拒脚本或另设版本绕过。

## 执行边界

已从源工具读取直接用户原话“PR51自检通过并合并后，启动下一步工作”（turn01a14e3a/userMessage01a14e3a-3a98）及上一轮热力完整链计划；首个组合接线拒绝后，携原始证据的小职责补丁获正常审批。后续共享版本拒绝并未因阶段授权自动解除，明确待用户窄决定。

失败保留：领域夹具日期/全值/字段名、真实Catalog单位别名已修后7/7；Qt首轮试填字母被原NumericLineEdit清空，改成实际可保留999MPa后恢复验证通过；冻结报告测试漏report_qualification已补。默认沙箱向新树tmp重定向日志被拒一次，测试未启动；改用正常升级仅运行测试。原失败事实不删除、不把旧证据当当前整仓通过。

完成后需新私有PR/attach/精确head CI与实际包，再停源独立验收，不自行合并。原生Office、鼠标/IME/DPI、企业样例、干净目标机、商业分发继续OPEN；不CU、不商业发布、不升级SUPPORTED。知识无新增。
