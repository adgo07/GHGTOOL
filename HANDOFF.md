# B-EXTERNAL 当前实施交接

2026-10-20：ACTIVE / S0→S4实施。用户源会话直接消息01a15876-e86c-7e01-b74f-6bfa0f3a2328授权审查、完善后实施，已实际读取；“先改公开”及源API/本会话API均已核实仓库public。用户未授权公开额外资料或标准全文，账户零付费边界不变。本文件细化现有路线，不新建第二路线；E下载原任务书保留原文，下面明确修订其执行歧义。

## 平台 / Contract 预检查

开工实际origin为adgo07/GHGTOOL，已fetch，默认main；本包从最新origin/main@0f50642544b110ee461f1b32ef8a01091d0f44d0独立分支codex/b-external-integration开始。PR52已合并，旧热力报告/原始证明保留，不在其分支继续产品。中央锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，相关Frozen为Architecture V2.1、Numeric v1及Profiles v1；正式当前ACTIVE UI v0.2指南及GUIDE_INDEX已读取。MUST：分层、同一Canonical/Application、声明Profile一致和ambient独立、full-value exact、ET语义/Record不可变、消费者只读冻结补充。MUST NOT：显示值回流、业务epsilon、把软件补充混入ES/EI/ET或伪造标准CalculationLine、消费者重算/回查目录/旧Record回填、升Frozen基线。Carbon Decimal40/HALF_UP为ALLOWED PROJECT DIFFERENCE，非平台默认。已批准Issue016及Mapping11.1为本包依据；声明即ERROR残留为LOCAL DEFECT，不新增专业解释或中央Contract，Unit/Record/Workspace等DRAFT不冒称Frozen。

## 方案修订与执行边界

1. GUI仅“纳入、外部tCO₂总量、可选短名称”；勾选旁明确同边界/同期/原结果未计入的用户声明，不自动核验真实性，不加附件审核或大量必填字段。仅在存在明确事实反证时阻断；三项轻量输入本身不能自动判定跨期。已知边界/期间/重复计入事实可由受控可选上下文传递，不作为新GUI必填项。
2. 新建默认明确不纳入；旧行业codec缺节点解为历史未记录None，不补0或伪造未纳入。区分禁用草稿（包括非法词法可保存）、启用空白待补、真实0、合法正值；仅纳入后校验数值/单位/已知反证。旧项目打开/保存不替用户确认或清除声明。
3. 只在声明的DecimalPolicy/Profile下由正式producer计算一次软件补充并冻结：ET不变，补充为原ET全精度+外部采用值；无伪造标准CalculationLine，不从显示值求和。报告/记录页/Word只读同Record冻结节点，不重算。烟气覆盖不完整与外部待补是两个维度；任何状态均不宣称软件已核实完整企业排放。
4. 仅行业payload v5→v6，兼容1—5；通用canonical_input_codec envelope仍v2，拒绝封套input_version与payload.version不匹配，不静默升级身份。新行业模型/版本登记按实际影响同步，非公共Workspace演进，无数据库迁移。
5. 旧v2—v10模板字节及原九表不改，新v11/2.9在九表后追加“软件补充”页，非B.10。GUI/Excel/项目都装配同一Canonical，预览不写Record，重复成功点击每次新增一条但每条补充只加一次。已纳入非法值/错误单位/明确反证为ERROR；预览失败零Record。所有消费者只读冻结补充，历史原DB与同次导出条件的Word保护。
6. 按实际变更同步payload/受控资源/模板hash/报告schema或布局登记、wheel及standalone检查；旧Record无冻结补充不造节点或0，必要版本分派保护旧模型/Word。不改标准原式、Numeric/物性Profile或Frozen基线。
7. B收口仅CONSUMER_INVENTORY当前消费者身份/本包旧声明阻断退出；跨段真实新缺陷单列，不顺手重构。本轮不启动N采样/优化或桌面CU；后续顺序N→RS04→RS05，SUPPORTED与商业发布仍未授权。

## 工作分组与所有权

C为唯一共享所有者，负责本树Domain/Application/codec、GUI、Excel与受控模板、SQLite项目恢复、共享ReportModel/Word、资源/构建/治理与独立预期测试。已有external-co2-prep纯helper和算例仅作待审实现输入，不把准备分支当生产已接入；不创建重复执行者、不并写共享文件。源只做独立验收，作者测试不冒作源测试。

S0：核基线/消费者/版本并写独立预期；S1：正式软件补充校验与冻结、旧声明ERROR退出；S2：GUI/表格/Canonical项目恢复；S3：Record/共享报告/Word及历史保护；S4：受控资源、必要回归、Windows全量CI、exact产品head实包与报告送验。小本地断点，完成稳定批次后才push一个独立PR并attach；先查同head CI，不无变化rerun、不弱化required checks，不擅删制品/证据，$0额度不足如实保留CI缺项、不付费绕过。

## 验收重点

独立预期ET100，禁用草稿20→原ET100/不参与；纳入空→待补非100非0；纳入0→补充100且显式0；纳入20→原ET100/补充120一次。负值/非有限/非法词法/单位及明确反证→零新增Record。声明单独为真仅提醒且不清除。覆盖GUI/Excel等价、非法禁用草稿/空/0/短名跨启动恢复、重复点击、旧codec与版本错配拒绝、partial烟气与missing补充共存、全精度/ambient独立、禁Calculator/Resolver/求值helper后的冻结报告/Word和历史原DB不变；实际包母版下载/导入/项目/正式记录/Word/两次启动。

原生Office回导、真实鼠标/IME/人工DPI、企业实样、干净目标机、原生正常退出及商业许可履约仍OPEN，不冒称本包已覆盖。新CI/制品按精确head记录；最终重写IMPLEMENTATION_REPORT并交源验收后停止，禁止自动合并或启动下一包。

Excel软件补充纳入值继续遵守既有Adapter数值单元格/最多15位有效数字/OOXML原始词法证据策略，GUI/Canonical仍允许声明Profile的完整精度；禁用非法文本草稿保留但不参与数值校验，实际公式单元格拒绝。不新增中央Numeric交换规则。
