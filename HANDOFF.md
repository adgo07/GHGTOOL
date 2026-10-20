# B总体收口盘点＋N性能基线测量 — 当前实施交接

2026-10-20，IMPLEMENTED / 待源独立验收；唯一产品路线仍为 `REFERENCE_STANDARD_ROADMAP.md`。用户经源会话授权这两项并行；本包为治理盘点与测量，不是业务实现、优化、Golden或Release阶段。

## 平台 / Contract 预检查

生产基线 `348077cd972a27b6eeb80b77b712e7cb35375988`、canonical origin adgo07/GHGTOOL、默认main及fetch已核；中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。Architecture2.1/Numeric1/Profiles1 Frozen按锁读取，当前ACTIVE UI v0.2另读，不构成Frozen adoption。分层/同业务真值、Profile传播与ambient独立、Record只读历史必须保留；不改计算解释、公式、数据库/Codec/模板/算法身份、Frozen或标准范围。遥测时长不是业务Numeric，不回流正式值。相关016/017/018/020沿用，本包无新增标准决定或中央Contract修改。

## 当前范围和文件所有权

B由集成负责人执行，独占本文件、路线、状态、实施报告、消费者清单及必要的陈旧治理措辞。逐项只读核燃料、电力、材料、工艺、脱硫、烟气、热力蒸汽、外部CO₂在7个渠道的共同链；输出旧定义退出/兼容与交付缺项。现有消费者文档保持当前表和明确历史区分，不建立第二总路线，不顺手重构。

N由唯一gpt-6.1-sol/medium执行者负责 `scripts/measure_n_baseline.py` 与 `docs/performance/n-baseline/`，使用冻结生产基线；既有 `tests/benchmark_navigation.py` 作为复用入口。启动、页面切换、项目打开、Excel导入、Application正式计算、冻结Word各有计时边界、规模、重复原值和统计；串行测量，B不同时跑测试/build。临时合成DB/Excel/Word仅放忽略目录，不读取真实企业/用户数据库。

## 证据与停止条件

本轮不改生产，原始样本、命令、环境、失败与统计必须可复核。进程fresh不等于磁盘冷cache；Qt offscreen不等于人工鼠标/DPI；单代表业务单元不等于全场景负载或SLA。新业务Bug单列证据，不混入N优化；需专业选择只停相关项。旧CI/制品保留真实head，不改标当前merge。

完成后源独立验收，再等明确后续授权；不自动合并、不CU或变通桌面控制、不跑无必要昂贵完整CI、不进入RS04/RS05/第二标准、不商业交付。原生Office/中文IME/人工DPI/企业实样/干净机/许可门禁继续OPEN。原B2 CORE_CHECK/GAPS和PR53过程从Git历史读取，不复制成新路线。

## 当前交付断点

B当前8组矩阵与11字段接管范围已核，治理时态已同步；N于本地Asia/Shanghai 2026-10-20 23:00:32—23:02:35串行完成14指标×5样本，0计时失败。源码事件循环就绪median819.640ms、Excel502.906ms、Canonical项目54.643ms、正式Application65.610ms、Word644.119ms。首次fresh全程17.762s和新建页首次14.543s作为暖身原值保留，不隐藏首次成本、不称冷cache或SLA。

原始/脚本哈希、完整环境、边界和统计在N目录；按.gitattributes原字节保存。集成证据复算8项通过，生产与data-source/tests不变；不会为纯文档建立PR触发昂贵全量CI。当前先本地小提交送源验收，未推送/建PR/合并；若后续要求远端PR，须遵守当时required checks，不能拿本包文字绕过。
