# 当前任务状态 — B-FUME

更新：2026-10-18。状态：IMPLEMENTED / WAIT_CI_AND_SOURCE。PR50已合并（8d054d2480d744882f4f11f56b59e68df91dc50f），F01—F03源独立技术复验PASS；固定b4/CI263证据按docs/ci/PR50_FGD_RETAKE_SUMMARY.json追溯，文档head不冒充制品head。本包唯一正式出口为P04A烟气监测分段完整链，完成送源独立验收后停止。

## 执行与接口

实际origin adgo07/GHGTOOL与main已fetch核验，独立codex/b-fume-integration基于PR50合并main，工作树创建时干净；根用户修改及旧工作树未动。C独占共享消费者、采用资源/版本、GUI/B.6、冻结报告、构建治理与整链测试。F独占carbon_material_fume_segments.py/test_b_fume_segments.py，ca8aa1f两文件单次取用，F声明33+8本地通过仅专属准备证据，不替代C整链。

| 项 | 本包接口 |
|---|---|
| 身份 | FumeMonitoringSegment：真实source_instance_id、metering_boundary_id、segment_id；不由显示名或行号替代 |
| 测量 | 既有FumeIncinerationInput配对Q/QVar/段时长与参数；FCh由正式门禁同次核验/采用/快照 |
| 时间 | 无时区同一报告时钟半开区间；核算期独立，段时长显式输入精确配对；d/h只归一一次 |
| 完整性 | 有效段完整覆盖可称完整期间；缺口仅已覆盖合计+WARNING；重叠/倒置/坏段/INVOLVED无段整体拒绝零Record |
| 版本 | Carbon Canonical codec4兼容1/2/3；尾字段FUME_V2分段。旧FUME_V1可开存/按旧组合资格计算且明确未证明覆盖，不补造区间；显式升级保留原项目副本/旧Record |
| 退出 | 分段版正式入口退出旧逐行时长判断；旧路径仅显式旧组合保留，不作失败回退 |
| 冻结 | 新Record冻结段输入、实际采用值、逐段结果、覆盖/缺口、方法版本；Word只消费冻结值，历史不补算 |

## 平台 / Contract 预检查

业务base8d054d2480d744882f4f11f56b59e68df91dc50f；locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20保持。中央origin已实际核验，按锁定读取Architecture2.1/Numericv1/Profilesv1；ACTIVE UIv0.2按当前合并入口读取。MUST：分层/共享内核、declared-profile consistency、ambient independence、full-value exact、历史不漂移；MUST NOT：隐式float/业务epsilon/display回流/复制算法/Qt状态成为公共Workspace/自动Frozen升级。p40/HALF_UP属ALLOWED PROJECT DIFFERENCE，无中央缺口/修改。Issue020已RESOLVED Owner软件决定，落实Mapping§7.2/§8/§12与V2§9，不改标准式(9)或既有解释。

## 验证与边界

本地最终烟气/多实例GUI/Numeric/FGD专属/材料/codec联合82/82、69.983s；全源表格/烟气/G08联合76/76、121.482s。早期97项1失败为旧布局版本断言，82项1失败为旧结果ID断言，修正后最终82通过；原始失败日志和测试接线错误见IMPLEMENTATION_REPORT。Canonical/编译/pip check及v9机械投影通过。实际旧b4实包生成的烟气Record由新代码读取，原输入/模型/Word正文XML不变。当前新head CI与精确head包尚待执行，不将F专属测试或PR50旧CI写成本包通过。保留FGD10项退修、燃料/电力/材料、旧模板与历史Record保护。原生Office回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机及商业履约继续OPEN/NOT_RUN；不CU、不合并、不扩热力/外部CO₂/N、不删树、不商业发布。
