# 当前任务状态 — B-MATERIAL

更新：2026-10-17。状态：IMPLEMENTING。PR46已合并、PR45已关闭；原五字段及退修四项作为保护基线，固定历史报告不改写。

本包只落实已批准材料固定碳/挥发分、收到基换算及Issue018三工序整链，通过GUI/Excel/Canonical/SQLite重开/正式Record/冻结Word交付。V2是实施输入，唯一产品路线仍为REFERENCE_STANDARD_ROADMAP.md；不自动转下一包。

## 所有权与最小接口

| 所有者 | 独占写入范围 | 接口 |
|---|---|---|
| C共享集成 | 公共policy/Resolver、混合Calculator、Application/codec/Project、UI、Excel/模板、报告、运行资源、构建、治理及整链测试 | 沿用Canonical/Application，版本与采用事实分别冻结 |
| M材料 | carbon_material_normalization.py、新test_b_material_normalization.py | MaterialInputLine兼容尾字段；原始行/收到基采用行分开；018逐角色碳量 |
| F烟气准备 | 新carbon_material_fume_segments.py、新test_b_fume_segments.py | 实例/边界/段身份，半开区间逐段核算与独立覆盖，不进入材料包 |
| N只读测量 | 新benchmark_b_material_navigation.py、独立本地输出 | 固定head、正式采样避让重测试/构建，离屏不冒充原生首绘 |

instance_id、line_id与role共同定位，不以名称/行号代替；切源/改名/增删/恢复保留对应草稿及身份。非法输入可存待完善项目，正式失败零Record。打开仅恢复，不补默认，不静默升级；确认升级保留原输入，取消不写回。模板/codec/Calculator/采用组合按实际变化分别演进。必要换算值和方法致命校验，证明附件缺失只提醒。

## 平台 / Contract 预检查及执行边界

- 实际origin已核实adgo07/GHGTOOL；fetch后从origin/main dada7a188db55a2384ea3aad48038aa4472158b2创建干净隔离分支codex/b-material-integration。
- locked central SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；Architecture V2.1、Numeric v1/Profiles按锁定读取。当前ACTIVE UI路由v0.2及家族规格/清单，不升级Frozen。
- MUST：分层、同一内核、declared-profile consistency、ambient independence、full-value比较、历史不漂移。MUST NOT：未声明float、隐式修约/epsilon、复制算法、自动升级Frozen。p40/HALF_UP属ALLOWED PROJECT DIFFERENCE；本包无需改中央Contract。
- 相关Standard Issue：004/016/018；落实有效软件决定，不改标准原文或既有解释。
- 仅本地实现/本地提交；公开披露待确认，不push、不公开PR、不上传日志/制品，公开CI暂不触发。
- 不控制桌面、不改用户参考资料、不安装iapws/不改017、不采购/正式申请、不合并、不删除分支/工作树。
- 商业依赖/包体预检查并行，不作为法律放行。
- 当前新测试尚未执行；历史781/781和CI不当当前证据。v5原生Excel/WPS、真实鼠标/中文输入/人工DPI/企业样例仍OPEN，最终模板变化另验。

完成本业务包后重写IMPLEMENTATION_REPORT，交源会话独立验收并停止，不自动实施下一包或RS04/RS05，不宣布SUPPORTED。

## 材料整合稳定断点

- 已接入M专属提交ffd27e9（本分支91312cf）；独立material.json采用身份，原燃料/电力resource/SHA/identity不变。新MATERIAL_V2逐角色碳量；MATERIAL_V1仅明确收到基实测旧组合保留，未知版本可读不可正式执行。
- codec2兼容codec1真实默认；每物料原值、方法/水分/基准和采用值分别冻结。GUI分来源草稿、确认升级/取消及原输入副本；Canonical升级另存项目/单元身份，不改原项目。v6/2.4.0辅助列已登记，SHA ca61cf3133c2663c78ca7409d23f7dd20726e43a8c79adca2aa78faecb3c031a；v2—v5原字节保留。
- 本地材料4文件35项：首轮34PASS/1ERROR（升级副本复用unit_id唯一键），修复后35/35，10.049s。真实GUI/Excel/SQLite/正式Record/冻结Word链通过。
- 本地保护8文件74项首轮68PASS/4FAIL/2ERROR，涉及旧来源/版本断言、v6元数据及打包夹具未纳入新增资源；修复后4文件36/36，10.054s。失败历史保留，尚未冒称全量通过。
- M最终本人Python3.12.14材料27+政策3共30/30；F专属准备557f2c6未接入本包；N基线5/5进程、360计时操作已完成且停止，不是360测试。N/F结果保留其独立工作树，未公开上传。
- 正在运行本分支全量及随后本地构建/包体许可核对；公开CI不触发。原生/人工/企业缺项仍OPEN。
