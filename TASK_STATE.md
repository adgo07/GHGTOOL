# 当前任务状态

状态：GHGTOOL标准分派与输入/输出一致性改造 — 第1包完成，第2包实施中；整阶段完成后提交独立PR等待验收，不自行合并。
最后更新：2026-10-13。

- 开工main：204dded5d03853617f79a1f05693e89b619df9d1；origin已核实为adgo07/GHGTOOL。独立分支codex/ghg-standard-input-unification；主目录旧分支及用户修改原样保留。
- PR45仍OPEN、未合并，head 9cdbcaa6e7e88914036535a65f80b11d26d8839e；在本分支以5d09ae6明确整合其视觉实现，不合并/关闭原PR。
- 同一阶段连续六包：①共同输入政策/模板保护/B.6/热力限制；②静态标准注册与分派；③共享燃料规则与双入口；④工序/脱硫/电力/热力/项目兼容；⑤冻结Record业务表与Word/Excel表式；⑥视觉清理及整体验证。内部断点不逐包重新请求批准。
- 已登记软件决定GHG-STD-32151-34-009：自定义燃料/碳酸盐参数可填，不套目录缺省，不自动标为实测或化学计算；FCh与FCm/FCV分离。既有001—008决定保留。
- Contract预检查：中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20；Architecture V2.1/Numeric v1保持不变。遵循p40/HALF_UP、完整精度正式计算、来源冻结及历史Record不漂移；本次内部标准注册不定义中央公共Contract，不上线其他行业公式。当前UI指南v0.2为ACTIVE，不升级Frozen。
- 第1包：已实现共同输入政策、显式自定义燃料/碳酸盐身份与真实来源、正式Calculator缺省防绕过、B.6全活动行、表后活动定位拒绝、.34蒸汽类别限制；保留旧模板1.0结构识别及旧项目codec。Calculator公式未改，验证版本更新为CAR-SM01-2026-10-13-G06.3。
- 候选Excel模板2.0受控资源：当前SHA256=223156ce3246f7b769bafdf76b50bdd334e07201e6318d409347361d167d043e。活动格解锁，目录采用格/结果格锁定，自定义参数独立填写格，B.6多行和B.7两组。下载逐字节复制；旧母版保留为兼容夹具，用户docs模板未改。后续包继续完善B.2单位子列和B.3—B.5身份字段，本阶段尚未交付验收。
- 本地Python 3.12第1包联合命令：python -m unittest tests.test_standard_input_policy tests.test_exb01_template_acceptance tests.test_exb01_ingress tests.test_uat03_page tests.test_g06_page tests.test_canonical_project_inputs tests.test_g08_delivery -q：108/108通过，151.562秒。前次62项定向为59通过/2失败/1错误，修正后3项复测通过并纳入本次108项。
- 九表已用Artifact Tool离屏渲染检查；其保护接口不支持所需操作，模板保护修订使用bundled openpyxl，运行时下载仍只复制字节。原生Excel/WPS保存回导及Windows人工DPI仍未执行；不冒充实机验收。
- 下一包：静态标准注册/分派及按需服务和页面构造；不开发第二行业公式。整阶段最终全量回归/Windows构建/CI/独立PR尚未执行。历史PR45 CI仅作基线证据。
