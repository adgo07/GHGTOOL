# B-EXTERNAL 实施报告（作者执行）

状态：本地实施及验证完成，Windows CI与exact-head制品待核验，之后停止等待源独立验收。唯一共享所有者C；原用户下载任务书不改，细化决定写入HANDOFF，不建立第二路线。当前产品提交85569337d181595ad3cce7a77859003b59958bcf，基线main@0f50642544b110ee461f1b32ef8a01091d0f44d0（PR52已合并）；原根用户修改及旧热力树文档保持。

## 平台 / Contract 预检查

业务仓origin实际核为adgo07/GHGTOOL，已fetch/default main。锁定中央ee5feb0cc34dbd99790500fadd0c4c932e202a20，Architecture V2.1/Numeric v1/Profiles v1 Frozen。MUST：分层、同Canonical/Application、声明Profile一致、ambient独立、full-value exact、Record不可变、消费者只读冻结值。MUST NOT：显示值回流、业务epsilon、改ES/EI/ET或造标准行、回填/重算旧Record或自动升级Frozen。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE，非平台默认；旧声明阻断为LOCAL DEFECT，不需改中央Contract。相关Standard Issue是016，Mapping11.1已批准，本包不改变既有专业解释；不做数据库迁移。当前ACTIVE UI v0.2不是Frozen，Unit/Workspace等DRAFT不冒称Frozen。

## 最终实施范围

软件补充独立Domain求值，版本CAR-EXTERNAL-CO2-016.1，共享Calculator新记录身份EXTERNAL.1。原标准ES/EI/ET和CalculationLine不改；采用完整ET与外部量按同声明Profile只求和一次，独立software_supplement节点冻结。勾选为用户声明同边界/同期/原结果未计入，不宣称自动核验；明确反证阻断。未纳入、纳入待补、真实0、合法正值、历史缺失分别保留；原烟气覆盖缺口与补充缺失独立。

GUI三项输入及原其他活动/运输声明可访问，禁用非法草稿保存/恢复，确认提示不清除声明。行业payload6兼容1—5缺失为None，通用封套仍2且拒绝内外版本错配。Excel v11/2.9.0在原九表后新增软件补充页，旧v2—v10字节不改且保留构建资源。原九表XML逐字节相同；当前母版SHA256 b1e843a1eb8980c5a9bf4ee11d5b2369abcb89ebf4ca5b8659d8cccaefd166c4。新增页仍按既有Excel Numeric词法/15位策略读取，未纳入草稿不做数值采用。

共享ReportModel/记录页/Word只读同Record冻结节点，不在消费者求和；新Schema3.1.0/布局3.0.6，原无节点的历史报告保持3.0.0与原正文。软件节非B.10、不替换B.1、不承诺完整企业核验。消费者增量记录本包直接冲突清理，未启动N抽查/RS04/RS05或跨阶段重构。

Mapping仅同步实际接管状态，R11候选与3份Canonical原字节不改；审阅四件套按PREFLIGHT机械重生并保留意见，61行/450scope/25场景/每表8隐藏技术列不变，最高行344pt。报告Schema/架构及构建精确白名单同步，未新增主要依赖。

## 本地执行证据

|命令/检查|真实结果|
|---|---|
|python -B -m unittest discover -s tests -t . -v（干净8556933）|1029通过/0失败/0错误/0跳过，1313.979s；tmp/b-external/frozen-head-full.log|
|修正后相关9组模块/指定方法复验（完整命令见日志/状态历史）|64通过，54.880s；tmp/b-external/regression-fix.log|
|python -B -m unittest tests.test_business_rules_candidate_assets -v|20通过，10.378s；本地JS意见往返25场景通过，非Actions|
|validate_canonical / pip check / compileall / 受控资源与v11投影|9标准/12来源/102参数/138因子；无依赖冲突；其余通过|
|UIR04脚本 / scale 1.25与1.5|5场景及两缩放探针通过；程序化离屏，非原生CU|
|build_standalone / B_EXTERNAL_PACKAGE_VERIFIER / smoke_standalone|8556933真实EXE/PYZ与包内原生CoolProp/NumPy/Qt，无业务源码回退；v11材料换算、外部状态/单位、partial烟气、GUI/Excel/SQLite/冻结Word及历史保护通过；2次隔离启动通过|
|verify_release_archive|313个manifest列项+manifest自身314可见文件，使用后ZIP往返通过|

实际旧CI273的2条合成记录，只复制DB验证，不重建历史算法；原DB、ReportModel及Word正文保持，固定原导出日期2026-10-18。docs/ci/B_EXTERNAL_HISTORY_PROOF.json及B_EXTERNAL_LOCAL_PACKAGE_PROOF.json分别记录历史与本地新包证据。旧CI273不是本包CI。审阅资产见B_EXTERNAL_REVIEW_ASSET_PROOF.json，源代码与资源自8556933无后续变动。

## 负向记录与修正

- 首轮完整回归1028项/1323.438s为4FAIL/1ERROR，不能写PASS：v11未进入独立材料parser版本集合（2失败），通用封套误假设所有注册codec payload都有version（1错误），两旧断言仍要求声明阻断/仅九表。修正后64项复验与冻结head1029项全量通过。通用封套现在按codec显式声明内部版本字段，保持非炭素分派，不新增标准。
- 早期7项批次曾1FAIL，燃料p40尾数测试预期不完整；37项批次曾1FAIL/1ERROR，为烟气p40预期及测试控件名；85项批次剩1FAIL为既有GUI小值显示0.308的预期。均修正独立预期/测试引用，不修约产品结果。
- 初版v11 OPC前缀虽被openpyxl接受但最终ArtifactTool读取拒绝；已保留原内容类型/关系命名序列化，重新读取/渲染通过。最初完整探测因此主动中止，无通过计数。
- 复核重现损坏payload fields=None抛TypeError、合法1e100被显示成历史缺失，已修为受控codec错误和科学计数显示，含极小非零保护，不改计算结果。
- 审阅builder首调previous路径缺evidence报ENOENT，未覆盖旧资产；实际包验收器扩展时漏导SOURCE_FUME报NameError，修正后在新临时DB完整复验。均保留日志，不把脚本失败写成产品通过。

## 后续S4门禁与交付边界

Windows Actions尚未触发，待本地证据稳定提交后执行既有必跑全量及PR-head独立包流程，核对最新PRhead/merge-ref/manifest/制品哈希，再实际下载核验。作者执行不冒作源独立验收；不自动合并，不启动新N抽查/RS04/RS05，不声明SUPPORTED或商业交付。原生Excel/WPS/桌面CU与企业真实样例仍NOT_RUN/DEFERRED；既有全量中的历史N01测试不等于启动新N抽查。

仓库public为Owner直接授权，$0预算不变，未采用付费绕过或弱化required checks。原用户文件和标准全文未带入本包。最终CI回执会单列产品、文档、实际制品head，避免旧CI为新代码背书。


源独立接验增量：源已独立运行补充runtime/chain/excel共15项，35.383s，OK（源自行提供，非作者执行）。源指出所有状态的声明纳入提示不准确，本地仅按冻结status修正notes及PENDING状态标签：COMPLETED_*才称已纳入，PENDING为声明已选择/数值待补，NOT_INCLUDED与历史不声称声明或纳入；未核验外部计算/完整性及partial覆盖提示保留。python -B -m unittest tests.test_b_external_status_copy -v：2/2通过；实际旧CI273 DB/模型/Word2/2保护仍通过。求值、冻结数值、无节点行为、算法/Schema身份均不变。按源协调要求本地保留补丁、暂不推送，CI286继续取得现远端a242962证据，不取消或重复触发昂贵CI；最终head待统一收口。
