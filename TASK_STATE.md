# 当前任务状态 — B-FUME

更新：2026-10-18。状态：PR51_F01_HOUR_FIX / CI_PACKAGE_PASS / WAIT_SOURCE_ACCEPTANCE_AND_MERGE。PR50已合并（8d054d2480d744882f4f11f56b59e68df91dc50f），F01—F03源独立技术复验PASS；固定b4/CI263证据按docs/ci/PR50_FGD_RETAKE_SUMMARY.json追溯，文档head不冒充制品head。本包唯一正式出口为P04A烟气监测分段完整链，完成送源独立验收后停止。

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

本地小时/正式链/G08 66/66、64.768s；后续相关联合135/135、62.699s，包含当时实际wheel/sdist验证器。8份模板在真实wheel/sdist与安装后逐字节一致，未包含用户数据库/计算表。两次验证接线失败及修复原因保留于摘要，不改Numeric守卫。编译/依赖/Canonical/投影PASS。

实际旧CI268包生成当时合法3分钟Record，由当前代码读取模型/Word XML保持；原细时间Canonical/SQLite可开存，新正式核算明确拒绝且零Record。实际旧b4烟气与两份脱硫Word也由仓内可复现只读脚本验证不变。CI252仅docs/ci一处，PR50已迁移，无需重复处理。

固定bbb1d5b的新CI273与精确head实际包已完成；CI268/b0只为前轮历史证据，不能背书本修复。完整命令/失败/来源/hash见docs/ci/B_FUME_SUMMARY.json。保留原生Office/鼠标/中文IME/人工DPI/企业样例/干净目标机/商业履约OPEN。完成送源验收，合并由源会话执行；C不合并、不CU、不扩下一包、不动根用户修改或旧树。

## CI271 验证器定向修复

CI271/run39113048982实际全量942项，941通过/1ERROR、1532.572s；唯一为新G08 installed-resources来源路径断言，standalone跳过，无新制品。原CI未打印路径，不能声称已实证8.3或editable具体成因。本地有效非规范临时目录别名复现同一断言：实际从wheel安装目录导入，但子路径resolve/父路径未resolve误判。验证器现统一resolve，并用-I/-S隔离安装探针，打印实际资源与安装根诊断；严格来源及8份模板字节断言保持。回归同时注入路径别名与sitecustomize预导入源码resources。

python -B -m unittest tests.test_g08_delivery tests.test_qzc_n01_c_numeric_unit_pilot -v：首次38项37通过/1ERROR、32.766s为回归覆盖既有PYTHONPATH致本机构建缺setuptools；保留原构建路径并额外注入后38/38、18.961s。实际wheel/sdist/安装资源证明再次PASS。原小时业务/模板未改；此前66/135属验证器修复前范围。原始失败/复现/最终日志保留，新head继续全量CI与精确包后送源，不借CI271失败或CI268旧证据放行。

## 小时边界词法必要补漏

c8实际入口补核发现datetime.fromisoformat将第7位非零小数秒静默截掉：2025-01-02 00:00:00.0000001变为整小时，GUI与B.6正式链合计生成2条隔离Record。before证据submicrosecond-before.log保留；源确认此为本次“不截断、明确拒绝非整小时”决定内普通Bug，立即补漏，不新增标准解释。

GUI/B.6共用parse_fume_timestamp，在datetime解析前检查所有点/逗号小数（含Python实际接受的小时/分钟后小数形态）；六位之后任何非零数字明确拒绝，超位全零才与可表达时间同一物理时刻。原可表达分钟/秒/微秒仍能构造/保存，正式整小时门禁不变；不改公式/Profile/算法版本/codec/模板。python -B -m unittest tests.test_b_fume_segments tests.test_b_fume_chain tests.test_g08_delivery -v：68/68、70.196s，包含真实渠道零Record与全零对照、旧细时间保留。diffcheck发现docstring空行空白已在提交前规范化；无功能改动。

CI272对应补漏前c8；即使其后通过，也不能背书本补丁。当前继续新head CI及精确包，完成送源验收合并，不启动下一包。

## 当前固定验收与合并交接

源码 bbb1d5bd953d463013f135c1047de33fc37fcc59；CI273/run39116916157 SUCCESS，merge c5f71d437a30f4b98803349054d4fbd27a6b754b：全量944/944、1573.998s；精确head G08 18/18、9.817s，2次隔离EXE启动PASS。artifact12133602018，ZIP 40cfd4632226474853e5ab320323edb2c734b9b974460002b9dd7b59133b6005；全部manifest/hash/PE审计与实际包小时/词法非零精度拒绝与全零对照/旧细时间恢复/历史分钟Word证明PASS，后置制品复审PASS。源3ee阶段小时66/66、97.937s；c8阶段装配1/1、15.882s；当前bbb词法2/2、8.858s通过，最终对应身份/包验收及合并由源执行。当前文档仅三证据文件补证，不自指制品head；合并确认前不启动下一包编码，已按授权只读准备现有热力/外部CO₂重叠所有者清单。
