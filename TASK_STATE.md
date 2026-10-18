# 当前任务状态 — B-FGD

更新：2026-10-18。状态：生产实现收口／最终统一head验证与送验。当前最终测试、CI和实包身份以当前私有PR及tmp/fgd-final-evidence/summary.json实际记录为准；未取得证据前不称PASS。

PR49已按Owner授权合并；main/本包起点为1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e。材料受验head40778c7及CI256（832项全量、17项exact-head G08、实际包审计/归档/两次启动）证据保留于PR49收口记录，不能当本包测试。F01/F02/F03、v7/2.5.0及旧模板字节为保护基线。旧材料工作树和根用户修改保留。

## 本包范围与所有权

仅接管fgd.ratio、fgd.factor、fgd.conversion及脱硫GUI/B.7/Canonical/项目保存重开/正式Record/冻结Word完整链。依据Mapping §9.1/§9.3、Issue016与批准V2第8节；不新解释原公式、Numeric、来源资格，不夹带烟气/热力/外部CO₂。

| 所有者 | 独占写入范围 | 当前接口 |
|---|---|---|
| C共享集成 | policy/Resolver/混合Calculator/UI/Excel/codec/Project/报告/资源/构建/治理、整链测试 | 原Canonical/Application；生产接口经本包小提交发布给M |
| M脱硫核对 | 新tests/test_b_fgd_specialist.py | 先只读真实C.2和通用I/TR绑定、独立预期；待C确定API后补专属测试 |
| F烟气准备 | 原carbon_material_fume_segments.py/test_b_fume_segments.py | 557f2c6准备补丁保留，最新main静态兼容核对完成并停止，不接本包 |

I单批单有效组分且通用绑定适用才新建初始化90%；多组分不复制90%，空行不计有效组分，已填未完行不忽略。TR通用100%绑定独立C.2。EF真实精确C.2绑定锁定，否则批准实测，不猜物种。实测空白不回缺省，单多单保留草稿且不重标旧缺省。同批整剂分母校验，不跨批合并、不归一、不重复乘用量；设施/批次/组分用稳定身份。

## 平台 / Contract 预检查

origin已实际核实adgo07/GHGTOOL，fetch后从最新origin/main建立干净隔离codex/b-fgd-integration，默认main。locked central SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；Architecture V2.1、Numeric v1及Profiles v1按该SHA读取，UI v0.2按当前ACTIVE读取。MUST：分层、共享内核、declared-profile consistency、ambient independence、full-value exact、历史不漂移。MUST NOT：未声明float、隐式修约/业务epsilon、算法复制、自动升级Frozen、Qt状态充当公共Workspace。p40/HALF_UP属ALLOWED PROJECT DIFFERENCE；无中央Contract冲突，无需修改中央Contract。相关Standard Issue016，落实已有软件决定，不改变既有解释。

## 授权与验收边界

Owner已授权下一包及既有M/F/源协调、私有push/PR/CI。完成单一脱硫PR与最终head CI/实际包后送源独立验收，停止；不合并、不CU、不删除旧工作树、不公开上传、不商业发布。必要模板演进机械生成并保留旧字节，能复用v7则复用。原生Office/鼠标/中文IME/人工DPI/企业样例/干净目标机/商业履约仍OPEN。本包尚未运行测试，不宣称PASS或SUPPORTED。

## 当前实施断点

Owner在本会话明确批准脱硫稳定身份尾字段、codec3兼容1/2及Calculator同次Resolver接管/按批校验；原公式/Numeric/历史Record不变，无数据库迁移。e09cf83状态同步、f2e2f5b解析API、37807b1专属测试已提交。M只写专属测试，真实13绑定及错asset/unit/year/period反例15/15（作者1.206s）。C首次联合22项4失败记录、GUI第二轮7项3ERROR（夹具变量初始化）及48项1FAIL/1ERROR（来源状态改为隔离后旧夹具）均保留失败历史。修后四模块联合65/65，61.022s；当时测试源码版本与后续小修须按最终head另验，不能当最终整链通过。

v7无法表达I/TR已选实测空白，必要v8/2.6.0仅机械改B.7增加K/L来源与M企业设施编号，旧v2—v7原字节保留。v8 SHA a8ee7272ee4ac3665997f7ce93f78e8fd78c58cb4215ee477c01b76b6f87dff4。新输入FGD_V2和codec3；旧FGD_V1读取不补键，确认升级另存副本/留原输入，组分旧用量不同不猜统一。模型/GUI/导入/Word及包体保护仍在联合闭环，不称本包已完成。C新整链首轮3项2通过1ERROR（夹具WorkbookProvenance属性名错误），正修复，未生成发布/正式验收结论。


生产链已提交5af702d；其后针对真实未完成行、旧歧义投影及升级用量语义补强。旧组分用量以显式Decimal/UnitService归一量比较，不以资料引用等对象元数据判异；Canonical旧项目另存新project/unit键，原项目输入不回写。新增实际Qt/SQLite/Word组最终9/9，58.304s（tmp/fgd-legacy-final.log）；之前6/6 37.556s、7/7 40.557s是各自断点，不累加。M Domain/API30/30已由73a7bc5单次集成。44项正式链/政策/M联合32.185s通过；四模块65/65 61.022s为更早断点。

全表输入+整链51项77.835s有1FAIL：重复入站随机ID导致Canonical比较不一致；已改为整工作簿身份命名空间下的冻结不透明键，针对性ambient+模板6/6 1.767s。初次新链17项4FAIL为v8材料路由与夹具证据/文字；28项1FAIL/14ERROR为退出私有helper后的旧测试调用及来源字段断言；现已改为真实API且44联合通过。旧Word短来源可能只显示B.7定位，新FGD_V2已独立显示冻结实测/缺省标签，完整定位留审计，历史V1显示不重解释。

曾拟移除asset_id一致性校验的提交被自动审批拒绝，该整条编辑未执行；安全替代保留原门禁，不降低错资产测试要求。当前无未决审批。审阅同版本四件套机械重生25/25场景、意见0→0、29/21/11行、652组合/450条件，未扩大审阅范围。最终统一head联合、私有PR/CI及实包仍待完成，不合并/不进入下包。
