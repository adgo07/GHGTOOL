# 原PR46基线整合实施报告

状态：执行中；更新：2026-10-17。仅本轮依赖整合、五表接线对账及后续共享边界，不是完整B或N。完成后由源会话验收，执行代理不合并PR46、不关闭PR45。

## 平台 / Contract预检查

实际origin为https://github.com/adgo07/GHGTOOL.git，原分支codex/ghg-standard-input-unification，开工head77d36a155323bc82199cb516c4ac58a2e1c60309，已fetch最新main d0c26351200099a8e62c8adabadac266c77f7c8c。工作树开工clean；根工作区用户修改保留。

中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20未变；按locked Architecture V2.1、Numeric v1/Profiles读取适用约束：分层、离线正式能力、声明Profile/ambient independence、Decimal权威入口、exact业务比较、显示修约不回流、Record不漂移。允许本项目p40/HALF_UP差异；禁止新增第二算法、global epsilon、自动升级Frozen或混同可变Project/不可变Record。当前ACTIVE UI指南按中央已合并索引为v0.2，不以中央脏工作文件作权威。无公共Contract变更、无冲突升级。

Standard Issue：涉及010既有五表接线批准及014/016/017/018/019/020现行边界。本轮不新增/重释专业决定；Python现状不是批准权威。两份用户方案已读；旧文尚未授权表述由本次Owner明确开始覆盖。

## 冲突处置与能力保留

实际merge --no-commit origin/main产生4治理冲突：HANDOFF/IMPLEMENTATION_REPORT/TASK_STATE按当前事实重写，保留双方有效能力/来源与停止边界；STANDARD_ISSUES_REGISTER逐项融合001～020，010不重复，009/011保留真实正文，后续决定与历史限制分开。没有生产代码冲突。AGENTS/Roadmap当前入口随本次授权同步，保留原PR46当前ACTIVE UI v0.2引用。

原PR46现有标准分派、来源草稿、五表Resolver/三级查询、GUI/附录B、模板v4及v2/v3兼容、Canonical项目、冻结Record/Word与导航优化保留；原PR47候选加载、审阅检查、R11 Mapping/台账和原批准V1.2保持有效。Catalog不变，不录第二套因子，不重写历史Record。

## 五表对账与未接入边界

Issue010批准全国表1/4/5、区域表2、省级表3，并要求特殊全国表不自动补位、失效选择重选；014OTHER与官方五表及非化石独立零因子分开。两条G05候选规则尚保留204dded5两类范围，生产PR46已为五类。定向初跑1个test出现2个subtest failure，均为GEN-RULE-ELECTRICITY-001/CAR-RULE-POWER-HEAT-001 parameter_ids差异，其余RuleDefinition一致；不删断言掩盖差异。

仅按010既有批准对齐两个候选范围、统一修订/依赖并同源重生派生资产；PR47历史证据以固定受验head19a9c2b794433184886dbad7482d7f11b6803486和其原工作树保留，不把新表伪称旧原件。真正Canonical共享生产提供者接管留B；燃料LHV/FCh、DIRECT、材料、OTHER、IAPWS及分段监测等差异按现行Mapping逐段迁移，本整合不改变这些生产结果或宣称完整R11已生产同源。

## 当前实际验证

- 既有电力9模块标准库unittest：117/117，0failure/0error，136.975秒；首次pytest启动因环境无pytest失败，未安装新依赖。命令与最终全量/CI待本轮收口记录。
- 快照定向一致性测试初跑：1个test、2个失败subtest、0error，0.460秒；对应范围差异如上，最终修正后结果待补。
- 原PR46旧602/602、原PR47旧CI240仅为历史，不替整合后新head背书。

## 保留缺项与停止

规则审阅表Office为NOT_RUN/DEFERRED至下阶段首次正式使用前，CU Esc有效；本轮不启动CU。现有输入模板v4旧head原生WPS17/17证据保留，非本轮重跑；若未来资源更改须重新验证，不借旧证据。真实鼠标/中文输入/人工系统DPI与企业样例仍缺项。

后续燃料/电力并行的共享文件所有权与最小接口写在HANDOFF第4节，不另建规范或第二产品路线。完成后停止，由源会话验收并安排后续。
