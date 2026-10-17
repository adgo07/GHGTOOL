# 当前任务状态 — B-MATERIAL

更新：2026-10-17。状态：LOCAL_IMPLEMENTED / 待独立验收。PR46已合并、PR45已关闭；原五字段及退修四项作为保护基线，固定历史报告不改写。

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
- 本包真实本地测试见末尾送验断点及IMPLEMENTATION_REPORT；历史781/781和CI不当当前证据。v5原生Excel/WPS、真实鼠标/中文输入/人工DPI/企业样例仍OPEN，最终模板变化另验。

完成本业务包后重写IMPLEMENTATION_REPORT，交源会话独立验收并停止，不自动实施下一包或RS04/RS05，不宣布SUPPORTED。

## 材料整合稳定断点

- 已接入M专属提交ffd27e9（本分支91312cf）；独立material.json采用身份，原燃料/电力resource/SHA/identity不变。新MATERIAL_V2逐角色碳量；MATERIAL_V1仅明确收到基实测旧组合保留，未知版本可读不可正式执行。
- codec2兼容codec1真实默认；每物料原值、方法/水分/基准和采用值分别冻结。GUI分来源草稿、确认升级/取消及原输入副本；Canonical升级另存项目/单元身份，不改原项目。v6/2.4.0辅助列已登记，SHA ca61cf3133c2663c78ca7409d23f7dd20726e43a8c79adca2aa78faecb3c031a；v2—v5原字节保留。
- 本地材料4文件35项：首轮34PASS/1ERROR（升级副本复用unit_id唯一键），修复后35/35，10.049s。真实GUI/Excel/SQLite/正式Record/冻结Word链通过。
- 本地保护8文件74项首轮68PASS/4FAIL/2ERROR，涉及旧来源/版本断言、v6元数据及打包夹具未纳入新增资源；修复后4文件36/36，10.054s。失败历史保留，尚未冒称全量通过。
- M最终本人Python3.12.14材料27+政策3共30/30；F专属准备557f2c6未接入本包；N基线5/5进程、360计时操作已完成且停止，不是360测试。N/F结果保留其独立工作树，未公开上传。
- 正在运行本分支全量及随后本地构建/包体许可核对；公开CI不触发。原生/人工/企业缺项仍OPEN。
- 6954292全量早期发现旧历史干基夹具依赖“切源保留原值/仅实测”旧假设；已核实并只停止本会话测试进程，运行未完成，不计全量PASS。同时静态发现Canonical升级后单元选择未刷新，已修为打开已保存升级副本。历史夹具按恢复状态构造原值而非普通切源；缺计算定义仍零Record，测量/恢复断言保留。修复后GUI整链+该历史用例+模板验收7/7，14.226s。
- 2368380原始本地Windows构建/267文件包审计/归档及2次隔离离屏启动通过；它只是内部预检查包。实际盘点发现自动收集的Qt6VirtualKeyboard.dll与唯一引用它的qtvirtualkeyboardplugin.dll（官方Qt6.11列GPL模块），应用无消费者。已精确排除这两项并加入包审计拒绝，G08定向16/16，6.406s；不关闭整个插件收集、不修改用户安装环境。正在重建修订包。原始包枚举未发现LICENSE/COPYING/NOTICE文件，不等于上游无许可；发布通知/源码提供/替换条件仍待补齐，不宣布销售放行。
- 本轮业务全量固定2368380继续执行；后续打包差异只在scripts/build_standalone.py、scripts/inspect_release.py及G08测试，无业务/Numeric变化。按源会话要求单列打包head及定向验证，不重复无关业务全量。
- 包内PYZ代码/实际资源验证（禁止业务源码回退）通过角色结果226.829166…、干基158.904166…、非法定义不新增Record及Word生成，但发现既有_numeric_authority安装器覆盖实际算法版本。已仅去掉旧版本赋值，ContextVar/运算/Profile/Frozen向量不变；新Outcome/Result/正式Record采用CAR-SM01-2026-10-17-MATERIAL.1，旧Record与原N01C向量身份保留。首轮63项62PASS/1FAIL为另一个历史向量被误当当前版本的旧断言；对齐后Numeric+材料64/64，11.033s（含历史Record不重标）。
- 2368380全量在途发现4个旧模板夹具失败：v5专属测试误用了已升级v6的当前默认资源，及下载文件名硬编码2.3.0。已让v5测试精确绑定保留v5原资源，XML/字节/旧身份断言不删；当前下载按正式登记版本验证。定向两文件13/13，1.777s。完整在途结果如实保留，不冒称最终head已完整全量通过。
- 2368380全量套件已完成：816项，812PASS/4FAIL/0ERROR，1122.271s；4失败准确对应v5历史资源/当前下载版本旧夹具，已在13/13定向修复中关闭。不得写成最终head全量PASS；后续包体排除、算法版本标记及新母版证据按各自定向回归独立证明。
- 新v6导入在预览时冻结已验证母版SHA到WorkbookProvenance，再原样进入项目/Record/Word；填写工作簿SHA独立，旧版本/历史无证据不补。GUI身份/来源草稿及母版追溯、PR46历史模板身份、RS03来源/项目链15/15，25.831s。只增加可选内部证据字段，无DB迁移。

## 最终本地送验断点（2026-10-17）

状态：LOCAL_IMPLEMENTED / 待源会话独立验收。生产代码冻结5859ba7e71a5e4add659efeb4a8392adb3896d86；其后只补测试/文档。最终15项母版/历史报告/项目链25.865s全过；最终包构建审计成功、两次隔离启动PASS、实际EXE PYZ代码与包内资源核算/Record/Word证明PASS。最终包265文件，无VirtualKeyboard/iapws路径及VirtualKeyboard PE引用。

全量证据仍为2368380的816项812PASS/4FAIL/0ERROR；四失败对应旧模板夹具已13/13定向闭环，后续Numeric/材料64项及交付16项通过，不宣称最新head全量PASS。完整命令、失败历史、SHA、商业待办及NOT_RUN见IMPLEMENTATION_REPORT.md。

C/M/F/N本包工作完成并停止，F/N未生产集成。不push/公开PR/上传/合并/删除，不自动进入下一包；原生Office/鼠标/IME/DPI/企业案例/干净机器/正式商业与IP仍未完成。

## 私有 CI250 断点

用户已授权私有化后push/PR/CI；已实际GET复核private，推送4b656911并创建PR49。旧“仅本地/不push/未CI”是历史停止点，已由新授权解除，其他范围不扩大。

CI250/run39038977148实际819项817PASS/2FAIL/0ERROR（1189.610s），exact-head构建跳过。只修EXB01新v6母版空断言与UAT03旧算法字符串断言，精确核冻结母版/填写SHA分离和声明版本；PR46历史空证据/Numeric正式Record一致保护保留。受影响5模块本地49/49，8.650s。生产树不变；新head送源会话复核并重跑CI及实包审计，不merge/不启动下包。详情见IMPLEMENTATION_REPORT末尾。
