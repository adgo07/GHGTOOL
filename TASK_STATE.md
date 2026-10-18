# 当前任务状态 — B-FUME

更新：2026-10-18。状态：PR51_F01_HOUR_FIX / LOCAL_PASS / WAIT_NEW_CI_PACKAGE。PR50已合并（8d054d2480d744882f4f11f56b59e68df91dc50f），F01—F03源独立技术复验PASS；固定b4/CI263证据按docs/ci/PR50_FGD_RETAKE_SUMMARY.json追溯，文档head不冒充制品head。本包唯一正式出口为P04A烟气监测分段完整链，完成送源独立验收后停止。

## 执行与接口

实际origin adgo07/GHGTOOL与main已fetch核验，独立codex/b-fume-integration基于PR50合并main，工作树创建时干净；根用户修改及旧工作树未动。C独占共享消费者、采用资源/版本、GUI/B.6、冻结报告、构建治理与整链测试。F独占carbon_material_fume_segments.py/test_b_fume_segments.py，ca8aa1f两文件单次取用，F声明33+8本地通过仅专属准备证据，不替代C整链。

| 项 | 本包接口 |
|---|---|
| 身份 | FumeMonitoringSegment：真实source_instance_id、metering_boundary_id、segment_id；不由显示名或行号替代 |
| 测量 | 既有FumeIncinerationInput配对Q/QVar/段时长与参数；FCh由正式门禁同次核验/采用/快照 |
| 时间 | 无时区半开区间，正式起止整小时；h与整数小时全值相等，d与Profile下hours/24规范化值全值相等；两路采用同一日值；旧细时间可读保存 |
| 完整性 | 有效段完整覆盖可称完整期间；缺口仅已覆盖合计+WARNING；重叠/倒置/坏段/INVOLVED无段整体拒绝零Record |
| 版本 | Carbon Canonical codec4兼容1/2/3；尾字段FUME_V2分段。旧FUME_V1可开存/按旧组合资格计算且明确未证明覆盖，不补造区间；显式升级保留原项目副本/旧Record |
| 退出 | 分段版正式入口退出旧逐行时长判断；旧路径仅显式旧组合保留，不作失败回退 |
| 冻结 | 新Record冻结段输入、实际采用值、逐段结果、覆盖/缺口、方法版本；Word只消费冻结值，历史不补算 |

## 平台 / Contract 预检查

业务base8d054d2480d744882f4f11f56b59e68df91dc50f；locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20保持。中央origin已实际核验，按锁定读取Architecture2.1/Numericv1/Profilesv1；ACTIVE UIv0.2按当前合并入口读取。MUST：分层/共享内核、declared-profile consistency、ambient independence、full-value exact、历史不漂移；MUST NOT：隐式float/业务epsilon/display回流/复制算法/Qt状态成为公共Workspace/自动Frozen升级。p40/HALF_UP属ALLOWED PROJECT DIFFERENCE，无中央缺口/修改。Issue020已RESOLVED Owner软件决定，落实Mapping§7.2/§8/§12与V2§9，不改标准式(9)或既有解释。

## PR51-F01 当前退修

Owner于2026-10-18决定烟气时间精确到小时；此为产品输入精度决定，不称标准要求。共享正式校验拒绝分钟/秒/微秒非零端点，不截断、不改写旧值；原输入与采用日值分别冻结。算法CAR-SM01-2026-10-18-FUME.2，方法CAR-FUME-SEGMENTS-020.2。GUI/B.6推荐小时；v9仍2.7.0，仅sheet6小时提示机械变化，hash 0fa20cbc126fadd2807fe02bea9b26b4a8855285e6b90fc171985557a895fae9。旧v2-v8不变。

本地小时/正式链/G08 66/66、64.768s；后续相关联合135/135、62.699s，包含最终实际wheel/sdist验证器。8份模板在真实wheel/sdist与安装后逐字节一致，未包含用户数据库/计算表。两次验证接线失败及修复原因保留于摘要，不改Numeric守卫。编译/依赖/Canonical/投影PASS。

实际旧CI268包生成当时合法3分钟Record，由当前代码读取模型/Word XML保持；原细时间Canonical/SQLite可开存，新正式核算明确拒绝且零Record。实际旧b4烟气与两份脱硫Word也由仓内可复现只读脚本验证不变。CI252仅docs/ci一处，PR50已迁移，无需重复处理。

当前新源码CI与精确head实际包尚待完成；CI268/b0只为前轮历史证据，不能背书本修复。完整命令/失败/来源/hash见docs/ci/B_FUME_SUMMARY.json。保留原生Office/鼠标/中文IME/人工DPI/企业样例/干净目标机/商业履约OPEN。完成送源验收，合并由源会话执行；C不合并、不CU、不扩下一包、不动根用户修改或旧树。
