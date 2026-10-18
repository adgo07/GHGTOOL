# B-HEAT 实施报告（本地阶段候选）

更新：2026-10-18。当前结论PARTIAL，兼容决策待确认；无新PR/CI/实际新包，不作完整支持声明。

## 平台 / Contract 预检查

业务base为PR51 merge a1aeebc1b6809397e61a2ffa7a2333a3b440c756，origin adgo07/GHGTOOL、fetch、main和起步干净已实际核。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。Architecture V2.1、Numeric v1、Profiles v1按锁定读取；UI当前正式合并指南按中央origin/main读取。MUST：分层、共享内核、声明Profile一致、ambient独立、full-value exact、原/规范/显示值隔离、历史Record/Word冻结；MUST NOT：隐式float、业务epsilon、显示值回流、Qt状态当公共Workspace、自动Frozen升级。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE；本轮不改中央Contract。相关Standard Issue005/006/015/017/019；无新专业解释，C3候选漏项需按既有005/006补齐的确认尚待答复。

## 实现与可审查结果

具体实现、接口、当前版本和非目标范围见TASK_STATE。正式领域断点5870ecf已提交；本地候选补齐实际统一热力GUI、受控B.9 v10明确方式/来源/边界、codec/SQLite项目恢复、购入输出独立抵扣与冻结Word。没有第二套算法、数据库迁移或自动物性产品依赖。原燃料及历史记录不删除重算。

## 验证

| 来源 | 命令/证据 | 结果 |
|---|---|---|
| C本地Python3.12.14 | `python -B -m unittest tests.test_b_heat_chain.HeatQtTests tests.test_b_heat_chain.HeatExcelTests -v` | 6/6，0失败/错误/跳过，41.731s；Qt/Excel/SQLite/Canonical/正式购入输出/冻结Word |
| C本地最后UI修正后 | `python -B -m unittest tests.test_b_heat_chain.HeatQtTests.test_internal_no_unrelated_values_and_boundary_conflict tests.test_b_heat_runtime tests.test_b_heat_specialist tests.test_numeric_contract_v1_adoption -v` | 37/37，0失败/错误/跳过，7.412s |
| C本地既有回归 | `python -B -m unittest tests.test_g06_carbon_material tests.test_uat01b_material_steam -v` | 32项、22FAIL含subtests、0ERROR，2.502s；未收口，不能称通过 |
| C本地实际历史包 | CI273源码bbb1d5b的EXE/PYZ生成两条旧热力Record/Word，再用当前代码调用`verify_frozen_record_word.verify` | 两条ReportModel哈希及Word document.xml字节一致，禁Calculator/Resolver；复制DB、原DB不改 |
| C本地受控母版 | `python -B -m scripts.project_appendix_b_v10 --write`及专属ZIP部件比较 | v10 SHA5dd12be5e78f13e1408e96f4698e725a4c5bf45071923b6c90d75a080437b5e9；仅sheet9变化，v9真实识别 |
| C本地渲染 | Artifact Tool只读导入/render B.9前后PNG并查看 | 新表头/提示可见；不是原生Excel/WPS回导 |

日志/历史生成器/真实包比对证据均在本树tmp/b-heat；未将tmp作为运行时真值源。上述本地结果不是GitHub Actions。本包尚未执行全量、构建、CI或新实际包验证。

## 历史热力证据

从已核CI273实际EXE/PYZ业务代码及其包资源生成旧known-with-old-reference/old-auto-table合成记录，不冒称真实企业数据或原生EXE交互。旧known ReportModel SHA29a564bbbdc221c5a34c223c39e8001352d853f3f60d2a1d8fa65c675d7ddc2c、XML SHAe93c2ef859cc44a547a16b9a3e02a756426e1d09089126f13caf194bbb5955fe；旧auto model0578d13aead197d0b8f14f6c9a344be3946236e76fd4729b40a4d6d6802d6bb1、XML51735e78cf9571f0d074010ba26e4be6ee504b96ab0a1ab230de097e980d4df5。当前阅读器禁计算/Resolver后两者逐字节一致，原数据库SHA未变。最终受验head/实际包仍须重核。

## BLOCKED：共享版本和C.3资格兼容

问题：共享Calculator版本/打包/报告元数据同步待用户具体授权；候选heat.factor漏列原有C.3独立来源，旧正式兼容未收口。
证据：自动审批拒绝组合脚本后，又拒绝仅改ALGORITHM_VERSION一行，理由为会影响材料/脱硫/烟气的新Record版本及断言；两个脚本都未执行。现有Canonical资格只列binding-heat_default_2025；Catalog和既有Resolver另有binding-heat_default_gbt32151_34_c3、同资产但不同来源/适用条件，Mapping§9.4/Issue005/006保留C.3。源会话已核该事实并向用户提确认。
为什么不能按原方案继续：不能把C.3伪装成通则来源、按0.11数值相同放行，不能静默把原合法默认改成不可用，也不能用旧FUME.2标记作为新热力交付身份或只改测试掩盖失败。
可选方案A：用户授权共享HEAT.1/当前母版v10元数据/包核验与仅当前版本断言同步；授权补齐准确C.3资格，保留Resolver原来源选择/适用条件，完成早于/跨越/晚于实施日回归。
可选方案B：保留本地候选与证据，暂停正式版本送验，待决策后继续。
建议：A；不改原排放公式、Numeric、历史Record或数据库结构。
需要决策的具体问题：本会话已发版本兼容窄确认；C.3补齐确认由源提出。017自动物性更换实现仍独立待Owner，未加产品依赖、不换库或回旧表。不得重试被拒脚本或另设版本绕过。

## 未执行项

全量/构建/新CI/实际新包：待兼容决策并修完受影响回归。自动IF97正式接入：待Owner具体实现及分发选择。原生Office/实际鼠标/IME/DPI/企业样例/目标机/商业履约：仍OPEN，不以offscreen或包内PYZ证明替代。旧材料/脱硫/烟气包证据保持原身份，本包最终需保护回归。既有失败与已修夹具详见TASK_STATE，未删除失败统计。
