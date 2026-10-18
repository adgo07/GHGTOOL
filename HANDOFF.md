# HANDOFF — B-FGD完整链

更新：2026-10-18。PR49已合并，受验材料及CI256证据见PR49收口；新包从最新main 1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e独立启动，旧材料分支停止开发。当前分工、预检查、授权和实际测试状态见TASK_STATE.md；唯一产品路线仍为REFERENCE_STANDARD_ROADMAP.md。

本包按Mapping §9.1/9.3、Issue016及批准V2第8节落实脱硫三字段同源与批次完整链。C独占公共消费者和治理；M只写新test_b_fgd_specialist.py，F原烟气准备不集成。先发布最小接口，再独立测试及整链保护。历史Record、材料F01/F02/F03、v7/2.5.0、旧模板原字节和燃料电力采用身份保持可追溯。

沿用已明确私有push/PR/CI授权；交付一个脱硫PR、最终head真实CI和下载实包证据后交源独立验收并停止，不自行合并/进入烟气/热力/商业发布，不CU或删除工作树。原生与商业缺项仍OPEN，不宣称正式支持。

## 脱硫最小兼容输入方案（实施设计）

沿用现有FGDInput作为批次容器；instance_id继续唯一标识该输入批次及已有结果/Trace行，新增可选facility_id表达真实设施归属，batch_id明确批次身份，CarbonateComponent尾部新增component_id。新GUI/Excel产生稳定键，不以显示名或行号代替；同设施允许多个独立批次，I合计按每个批次校验。旧输入无新键时只读恢复原组合，不凭名称合并设施或虚构批次；确认升级另存副本时生成新键，旧Record永不回填/重算。项目仍使用现有projects.sqlite和codec，版本演进不改数据库公共Schema。来源草稿按设施/批次/组分/字段/来源隔离；冻结输入、参数快照及Word按相同身份对应。

先发布resolve_fgd_field最小API：返回context、实际factor和同次resolution；真实关联核验只补三字段采用范围，不取消其他unverified门禁。I/TR通用身份与C.2的11个物种身份分开。当前小探针只证明CaCO3/I/TR三项真实SQLite解析READY，不构成整链或全部13项验收。


Excel初次入站以整工作簿内容身份作为命名空间，为原始分组/组分生成不透明稳定键；原单元格仅作为入站定位，不是跨项目业务身份。保存后直接恢复Canonical键，不随显示名称/行号重新生成；变更工作簿视为新的导入。企业设施编号只用于显式归属和业务展示，内部facility_id/batch_id/component_id仍独立冻结。审阅范围/规则版本不扩张，四件套仅同步采用状态并机械重生。
