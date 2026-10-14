# 当前任务状态

状态：GHGTOOL标准分派与输入/输出一致性改造 — 第1—5包完成，第6包实施中；整阶段完成后提交独立PR等待验收，不自行合并。
最后更新：2026-10-14。

- 开工main：204dded5d03853617f79a1f05693e89b619df9d1；origin已核实为adgo07/GHGTOOL。独立分支codex/ghg-standard-input-unification；主目录旧分支及用户修改原样保留。
- PR45仍OPEN、未合并，head 9cdbcaa6e7e88914036535a65f80b11d26d8839e；在本分支以5d09ae6明确整合其视觉实现，不合并/关闭原PR。
- 同一阶段连续六包：①共同输入政策/模板保护/B.6/热力限制；②静态标准注册与分派；③共享燃料规则与双入口；④工序/脱硫/电力/热力/项目兼容；⑤冻结Record业务表与Word/Excel表式；⑥视觉清理及整体验证。内部断点不逐包重新请求批准。
- 已登记软件决定GHG-STD-32151-34-009：自定义燃料/碳酸盐参数可填，不套目录缺省，不自动标为实测或化学计算；FCh与FCm/FCV分离。既有001—008决定保留。
- Contract预检查：中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20；Architecture V2.1/Numeric v1保持不变。遵循p40/HALF_UP、完整精度正式计算、来源冻结及历史Record不漂移；本次内部标准注册不定义中央公共Contract，不上线其他行业公式。当前UI指南v0.2为ACTIVE，不升级Frozen。
- 第1包：已实现共同输入政策、显式自定义燃料/碳酸盐身份与真实来源、正式Calculator缺省防绕过、B.6全活动行、表后活动定位拒绝、.34蒸汽类别限制；保留旧模板1.0结构识别及旧项目codec。Calculator公式未改，验证版本更新为CAR-SM01-2026-10-13-G06.4（第5包增加冻结展示证据）。
- 候选Excel模板2.0受控资源：当前SHA256=58b38c15d487bdc173f573a50e5b8f3446b5bb4df4693dd696a83742da5235b4。活动格解锁，目录采用格/结果格锁定，自定义参数独立填写格，B.6多行和B.7两组。下载逐字节复制；旧母版保留为兼容夹具，用户docs模板未改。B.2数据/单位已分列，B.3—B.5已增加身份字段，本阶段尚未交付验收。
- 本地Python 3.12第1包联合命令：python -m unittest tests.test_standard_input_policy tests.test_exb01_template_acceptance tests.test_exb01_ingress tests.test_uat03_page tests.test_g06_page tests.test_canonical_project_inputs tests.test_g08_delivery -q：108/108通过，151.562秒。前次62项定向为59通过/2失败/1错误，修正后3项复测通过并纳入本次108项。
- 九表已用Artifact Tool离屏渲染检查；其保护接口不支持所需操作，模板保护修订使用bundled openpyxl，运行时下载仍只复制字节。原生Excel/WPS保存回导及Windows人工DPI仍未执行；不冒充实机验收。
- 第2包：小型静态StandardRegistry/StandardRuntime登记当前唯一实现；公共启动/壳/导入页不直接构造炭素Calculator或附录B Adapter。核算与Excel页面按需创建，标准间草稿分别缓存；标准详情、蒸汽参考表及冻结报告通过注册项分派，未知标准/版本明确拒绝。未新增正式标准、数据库或插件框架。
- 第2包本地联合命令：python -m unittest tests.test_standard_dispatch tests.test_g03_shell tests.test_exb01_ingress tests.test_exb01_rpt02_integration tests.test_canonical_project_inputs tests.test_g08_delivery -q：69/69通过，34.868秒；增补假标准Excel页和公共组合依赖断言后，test_standard_dispatch为8/8通过（0.143秒）。先前外壳抽取引用错误已修复，13/13复测通过。
- 第3包：燃料编辑组件独立，目录仅规范名称，别名仅用于匹配/补全；两行输入带、共同数量/单位/含碳量语义；B.2消耗量拆数据B列/单位C列，解析与保护同步，旧模板仍独立识别。自定义质量/体积×计算/实测四场景比对完整值、单位、来源和正式结果，预览零Record。正式Unit标识保留原值，上标仅显示；旧项目缺失origin等字段兼容读取。
- 第3包本地联合命令：python -m unittest tests.test_standard_input_policy tests.test_standard_dispatch tests.test_exb01_template_acceptance tests.test_exb01_ingress tests.test_main_integration_excel tests.test_main_integration_ui tests.test_exb01_rpt02_integration tests.test_rs03_excel_project_workflow tests.test_rs03_excel_entrypoints tests.test_rs03_pending_link_recovery tests.test_canonical_project_inputs -q：86/86通过，92.120秒。前次67项有2错误（外壳旧服务访问），已保留惰性兼容访问；前次单位显示串误用已恢复既有Unit标识并纳入本次回归。燃料GUI两模块53/53通过（97.548秒）。
- 第4包：B.3—B.5分组/类别/实际名称/工序名称/物料序号明确归属；多过程同名物料不混合，组分配对质量只计一次，换行不改类别。工序名称与ASCII内部标识分离并冻结，旧载荷新增字段缺省可读。GUI工序名称可保存恢复，脱硫剂就近新增、组分数据/来源分行；既有多剂多组分及旧分组用量读取保留。
- 项目内部标准/输入版本2封装及标准codec隔离已提交471c06b；无数据库迁移。新燃料草稿保存稳定path/basis值，优先于旧Qt下标；旧下标兼容集中在专属适配器，旧HEAT路径与真实来源保留。
- 电力五表区分全国/区域/省级及不同因子口径。共享查询以正式Resolver候选为准，补上注册展示绑定曾截断历史期间候选的缺陷；GUI/Excel共用候选，未开放口径仅查阅并标明原因，未添加因子/改变Resolver业务规则。全国表1/4/5可查阅，区域表2不自动加入正式路径，省级表3按已批准规则可选。
- 第4包联合命令：python -m unittest tests.test_uat03_rules tests.test_exb01_ingress tests.test_main_integration_ui tests.test_uat03_page tests.test_canonical_project_inputs tests.test_exb01_template_acceptance -q：86/86通过（52.569秒）。此前86项有1失败为旧夹具包含新版稳定字段，改为真实旧结构后通过；此前电力70项10失败/71项1失败分别定位为重复筛选与全国绑定地域表示，修复后纳入本次回归。B.3—B.5 Artifact Tool离屏渲染已查，原生Office验收仍待执行。
- 第5包：记录页与Word共用冻结业务表，移除UI重复B.1—B.9投影；B.2数据/单位11列、B.3—B.5类别/名称6列同步。短来源、完整表下证据及来源类型/选择动作/版本/年度分开；新派生FCm/FCV与实际因子类型随Record冻结，旧记录不补算，公式/操作顺序和Numeric Profile未改。报告模型3.0.0候选，来源母版与当前输入模板SHA分别追溯。
- 第5包联合命令：python -m unittest tests.test_frozen_business_tables tests.test_rpt01_report_excel tests.test_rpt02_appendix_b tests.test_rs02_record_evidence tests.test_p3_c_records_ui tests.test_exb01_rpt02_integration tests.test_uat03_report tests.test_standard_dispatch -q：56/56通过（7.409秒）。旧表式断言已迁移，来源错配、精度、原模板公式保护和历史汇总核对均保留；日志中的故意注入异常属于失败路径测试。
- 原生报告视觉证据：技能render_docx.py因本机缺LibreOffice失败；改用已核实注册为WPS 12的Word兼容COM引擎只读打开临时DOCX→原生PDF→bundled PDFium逐页PNG。11页全部检查，已修正Title蓝线、长来源、输出属性、内部编号和提醒分页；1个合成完整工作簿→1条Record→10张业务表，不称作真实企业数据或Microsoft Word验收。临时输出位于系统TEMP的ghg-standard-input-word-qa，非产品资源。
- 下一包：最后的首页/标准库/卡片/字号及二选控件收口、重复清理、原生Windows与缩放截图、原生WPS保存回导、完整回归/Windows构建/CI/独立PR。整阶段尚未完成，不自行合并。历史PR45 CI仅作基线证据。

- 第6包视觉实现：最近记录表状态列140、操作列固定并将余宽给企业列、表头居中；标准筛选一行/支持列104、名称列伸展且不升级SUPPORTED；来源卡名称单行/开关与状态下置/浅色标题，输入14px；燃料二选控件保持既有typed combo与旧HEAT读值、键盘可选。未开放标准信号入口拒绝进入而不向Qt抛异常。
- 第6包首轮完整回归482项，475通过/5失败/2错误（368.757秒）：定位为1个UI信号缺陷及旧常量导入/布局/模板版本/自定义来源断言；已修复并93项复测通过、29项政策/报告复测通过。最终完整回归、构建/CI尚待执行，不把定向结果写为全量通过。
- Windows原生Qt平台程序驱动：1366×768逻辑窗口、Qt缩放1.0/1.25各20项检查通过，截图与源文件哈希位于docs/ui/standard-input-evidence；仅合成数据，未改变Windows系统DPI，不称人工DPI验收。WPS原生工作簿保存回导独立复核中。
