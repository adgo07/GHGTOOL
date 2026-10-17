# 原PR46基线整合实施报告

状态：本地整合与完整回归完成，待最终head Windows CI；更新：2026-10-17。仅本轮依赖整合、五表接线对账及后续共享边界，不是完整B或N。完成后由源会话验收，执行代理不合并PR46、不关闭PR45。

## 平台 / Contract预检查

实际origin为https://github.com/adgo07/GHGTOOL.git，原分支codex/ghg-standard-input-unification，开工head77d36a155323bc82199cb516c4ac58a2e1c60309，已fetch最新main d0c26351200099a8e62c8adabadac266c77f7c8c。工作树开工clean；根工作区用户修改保留。

中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20未变；按locked Architecture V2.1、Numeric v1/Profiles读取适用约束：分层、离线正式能力、声明Profile/ambient independence、Decimal权威入口、exact业务比较、显示修约不回流、Record不漂移。允许本项目p40/HALF_UP差异；禁止新增第二算法、global epsilon、自动升级Frozen或混同可变Project/不可变Record。当前ACTIVE UI指南按中央已合并索引为v0.2，不以中央脏工作文件作权威。无公共Contract变更、无冲突升级。

Standard Issue：涉及010既有五表接线批准及014/016/017/018/019/020现行边界。本轮不新增/重释专业决定；Python现状不是批准权威。两份用户方案已读；旧文尚未授权表述由本次Owner明确开始覆盖。

## 冲突处置与能力保留

实际merge --no-commit origin/main产生4治理冲突：HANDOFF/IMPLEMENTATION_REPORT/TASK_STATE按当前事实重写，保留双方有效能力/来源与停止边界；STANDARD_ISSUES_REGISTER逐项融合001～020，010不重复，009/011保留真实正文，后续决定与历史限制分开。没有生产代码冲突。AGENTS/Roadmap当前入口随本次授权同步，保留原PR46当前ACTIVE UI v0.2引用。

原PR46现有标准分派、来源草稿、五表Resolver/三级查询、GUI/附录B、模板v4及v2/v3兼容、Canonical项目、冻结Record/Word与导航优化保留；原PR47候选加载、审阅检查、R11 Mapping/台账和原批准V1.2保持有效。Catalog不变，不录第二套因子，不重写历史Record。

## 五表对账与未接入边界

Issue010批准全国表1/4/5、区域表2、省级表3，并要求特殊全国表不自动补位、失效选择重选；014OTHER与官方五表及非化石独立零因子分开。两条G05候选规则尚保留204dded5两类范围，生产PR46已为五类。定向初跑1个test出现2个subtest failure，均为GEN-RULE-ELECTRICITY-001/CAR-RULE-POWER-HEAT-001 parameter_ids差异，其余RuleDefinition一致；不删断言掩盖差异。

已仅按010既有批准对齐两个候选范围、统一修订/依赖并同源重生派生资产；PR47历史证据以固定受验head19a9c2b794433184886dbad7482d7f11b6803486和其原工作树保留，不把新表伪称旧原件。真正Canonical共享生产提供者接管留B；燃料LHV/FCh、DIRECT、材料、OTHER、IAPWS及分段监测等差异按现行Mapping逐段迁移，本整合不改变这些生产结果或宣称完整R11已生产同源。

## 实际实现与测试迁移

本轮merge提交保留双方基线，实际生产树相对原PR46不变（apps/core/standards/excel/ui/reporting/persistence/迁移/资源/pyproject/正式入口均无diff）；仅新增main的开发候选加载器。后续提交有限修改两条候选的applies_to_parameter_ids，主体G05规则、R11字段/条件/操作与来源资格不变；固定common修订pr46-integration-2026-10-17-g05及industry/software修订candidate-2026-10-17-r11-integration1，明确未接管生产提供者。

Mapping §9.4只补Issue010已有五表分组/采用说明，不复制值、不把公告表号称为GB逐表规定；014 OTHER独立、017/018/019/020不变。台账保留20唯一编号、009/010/011批准与旧实施事实，后续决定与历史限制分开。两份用户方案、当前AGENTS/路线/台账/政策与相关Contract预检均已读。

3处测试兼容迁移保留原断言职责：候选版本固定预期改integration1；模板百分数表头从当前ExcelTemplateService批准字节读取；OOXML结果缓存夹具从唯一排放量表头定位（当前K4），不再误写新模板的J4来源列。没有修改正式模板、删除词法/公式缓存/来源资格/历史兼容断言，也未新增固定列号的长期门禁。

新增test_pr46_baseline_integration仅3方法，独立固定100MWh预期53.06/60.96/82.73/55.43/61.87；购入/输出各自分项与抵扣、preview/失败零Record、每次成功追加、10条旧Record逐条稳定。Catalog binding/table的当前对账与Record实际冻结字段分开：现模型无独立binding_id，不以回查Catalog冒充冻结证据。

## 本地实际验证（非GitHub Actions）

统一使用指定工作树Python3.12；GUI相关命令设QT_QPA_PLATFORM=offscreen，无stage override的完整回归读正式四件套。

|阶段/命令|实际结果|
|---|---|
|python -m unittest tests.test_business_rules_candidate_assets.CandidateAssetCoverageTests.test_actual_g05_snapshots_and_existing_resolver_remain_identical -v（初跑）|1 test，2失败subtest，0error，0.460秒；唯一差异为两条电力范围；未隐藏失败|
|既有9模块unittest（uat03_rules/uat03_page/pr46_fuel_confirmation/exb01_ingress/exb01_gui_parity/uat03_formal_workflow/rs03_record_ingress_evidence/rs03_excel_project_workflow/exb01_rpt02_integration）|117/117，0failure/0error，136.975秒；pytest首次启动因未安装失败，未安装新依赖|
|python -m unittest -v tests.test_pr46_baseline_integration|3/3，0failure/0error，0.564秒；初版测试曾有7个subtest失败，为把全国Catalog地区误期望None（实际全国），已区分Canonical None并修正测试，非生产修正|
|快照一致性＋candidate_paths＋baseline定向|17/17，0failure/0error，1.731秒|
|候选六模块＋test_pr48_mapping_arithmetic＋baseline，stage override|初跑103项，3失败/1错误，15.329秒；旧模板路径/结果列/修订号不兼容；迁移后103/103，0failure/0error，15.319秒|
|python -m unittest tests.test_business_rules_candidate_revisions tests.test_business_rules_excel_evidence tests.test_business_rules_r8_operations -v|21/21，0failure/0error，3.103秒（103项内的定向子集）|
|QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 python -m unittest discover -s tests -t . -v|705/705，0failure/0error/0skip，687.989秒；含退出清理总703.811秒；正式产物路径、同一进程一次完整运行|
|现有validate_business_rules_candidate.py → build_business_rules_review.mjs → test_business_rules_review.mjs → business_rules_review_checks.py；参数见PREFLIGHT及本轮stage|同源生成/25场景意见往返/checks全部PASS；649组合281READY/368BLOCKED、442唯一意见范围、61行29/21/11、意见0→0；checks 1.108秒。Node夹具只记录25场景结果，不把40.565秒局部区间当完整进程耗时|
|python scripts/business_rules_review_hashes.py / git diff --check|4定义LF哈希通过；diff检查通过，仅Git CRLF提示|

全量UTF8日志位于忽略的build/business-rules-authoring/pr46-integration1/full-regression.log，SHA256 1194c17d1b55d52c2db026f956e685002704e8de238e67f8c9bc6384ee2c4fd2。故障注入日志栈对应test ok，不当作unittest error。原PR46旧602/CI223、原PR47旧CI240均不替本轮新head背书。本地完整回归执行时代码/资源与最终提交相同，随后只填治理结果；最新head CI/Windows构建及下载证据在原PR最终送验评论精确定位，不为回写CI再改变受验head。

## 资产、兼容与历史保护

正式模板v4/2.2.0 SHA256 e9b83462eabd97d5c7bd9aae1b4fa97a27d80006a205907c6671e626e8e57f6f保持原字节；v2/v3资源与注册兼容不变。Catalog、中央锁、原批准V1.2、固定electricity-paths.json与main一致，生产与发布白名单相对原PR46不变。

PR47原受验四件套固定于19a9c2b及原工作树；新派生资产有独立修订/投影，更新前独占哈希核对/备份，不覆盖原工作树和用户意见。正式四件套当前SHA256：
- XLSX：b571c1f5d0d7309d78d2580bf350c00aef215f17abc9108ef4de52b8f6a65c3c
- HTML：32d612104605bec390afcaa6a1393c9493e5a1cd57e978a12281f884d82e35a0
- checks：9231fa79f6f8b24a4b4f691427655c2fb8b4966b405fd39f8c69f3e7a58525b4
- fixture：8763d2379e33f3e4eace994f3310e272ea08a8d7c28e5aba0c5dcb351f2c25e3
- 正式投影LF：69f4bf5d6591030fe83fec06abb28bfad139911eab7bb867f76dfde2439a5d90

现有ArtifactTool对受影响版本标题/首屏渲染视检，布局未变；不是原生Office验证。未重跑导航基准，不将旧302/94ms记为本轮性能实测。未改数据库结构/历史Record、正式计算公式/Profile、产品标准范围或输入模板，不实现完整燃料/电力B。

## 保留缺项与停止

规则审阅表Office为NOT_RUN/DEFERRED至下阶段首次正式使用前，CU Esc有效；本轮不启动CU。现有输入模板v4旧head原生WPS17/17证据保留，非本轮重跑；若未来资源更改须重新验证，不借旧证据。真实鼠标/中文输入/人工系统DPI与企业样例仍缺项。

后续燃料/电力并行的共享文件所有权与最小接口写在HANDOFF第4节，不另建规范或第二产品路线。完成后停止，由源会话验收并安排后续。
