# 当前任务状态

状态：GHGTOOL标准分派与输入/输出一致性改造 — 第1包实施中；整阶段完成后提交独立PR等待验收，不自行合并。
最后更新：2026-10-13。

- 开工main：204dded5d03853617f79a1f05693e89b619df9d1；origin已核实为adgo07/GHGTOOL。独立分支codex/ghg-standard-input-unification；主目录旧分支及用户修改原样保留。
- PR45仍OPEN、未合并，head 9cdbcaa6e7e88914036535a65f80b11d26d8839e；在本分支以5d09ae6明确整合其视觉实现，不合并/关闭原PR。
- 同一阶段连续六包：①共同输入政策/模板保护/B.6/热力限制；②静态标准注册与分派；③共享燃料规则与双入口；④工序/脱硫/电力/热力/项目兼容；⑤冻结Record业务表与Word/Excel表式；⑥视觉清理及整体验证。内部断点不逐包重新请求批准。
- 已登记软件决定GHG-STD-32151-34-009：自定义燃料/碳酸盐参数可填，不套目录缺省，不自动标为实测或化学计算；FCh与FCm/FCV分离。既有001—008决定保留。
- Contract预检查：中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20；Architecture V2.1/Numeric v1保持不变。遵循p40/HALF_UP、完整精度正式计算、来源冻结及历史Record不漂移；本次内部标准注册不定义中央公共Contract，不上线其他行业公式。当前UI指南v0.2为ACTIVE，不升级Frozen。
- 已建立Python 3.12隔离环境；尚未执行本次改造后的测试。历史PR45 CI结果只作基线证据。
