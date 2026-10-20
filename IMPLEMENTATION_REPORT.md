# B-EXTERNAL 实施报告（作者执行）

状态：首轮CI286及实际制品已验证；源独立接验发现的状态文案补丁d645c8b已由源2项复验关闭，当前无新增退修项。按源安排将补丁、包内新文案/母版复制断言及CI286回执集中推送一次，最终head的新显示代码CI/制品证据后置记录在PR53说明及当前checks，不为了纯文档再反复触发CI。未合并，整阶段独立验收待最终head证据。

唯一共享所有者C；基线main@0f50642544b110ee461f1b32ef8a01091d0f44d0（PR52已合并）。原用户任务书、根工作区修改及旧热力树文档保持。核心本地全量/包对象为85569337d181595ad3cce7a77859003b59958bcf；首轮PR/制品对象为a2429621e204dc22cb1cd157bedff9c2f794a982；d645为状态文字修正，不改变求值、冻结数值、无节点行为或算法/Schema身份。

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

## Windows CI286与真实制品证据

[CI286](https://github.com/adgo07/GHGTOOL/actions/runs/39405735408)两个作业success：merge-ref 4513b08315c3ad6003ea17078b3c7e180f6a079e全量1029/1029，1568.889s；PR-head a242962 G08 18/18，12.375s。Canonical/编译/pip check/隔离DB/两作业GUI及缩放/构建/审计/manifest ZIP往返/provenance/2次启动/上传均通过，GitHub执行不写成本地执行。

实际下载artifact12259330066，75,749,566字节，ZIP SHA256 8d7bc3f0378aeb5dee15f351aea995de1533f9d0d39bb3243daab37045b0f83c；322个manifest列项+manifest自身323可见文件。manifest source_commit/pr_head均a242962，tested_merge为上述4513；严格审计、旧head验收器实际EXE/PYZ/包内原生依赖整链、旧CI273保护及再次2隔离启动均通过，无业务源码回退。回执见B_EXTERNAL_CI286_RECEIPT_PROOF.json与B_EXTERNAL_CI286_PACKAGE_PROOF.json；完整解码日志仅保留tmp并以SHA256定位。

CI286制品明确不含d645状态文案修复，不能为新显示代码背书。最终一次集中推送后必须取得含新显示代码的制品，包内将断言5种冻结status的notes/PENDING标签与母版copy_to原字节一致性；最终head/SHA/制品哈希及复验结果以[PR53](https://github.com/adgo07/GHGTOOL/pull/53)说明、当前checks和最终本地制品回执为准，不再为补写纯文档启动第三轮CI。

## 源独立接验与交付边界

源回报已独立执行runtime/chain/excel 15项/35.383s/OK；源核对d645完整生产diff并独立执行状态文案2/2，已关闭此问题，当前无新增退修项。这些是源自行执行并回报的范围，不冒称作者执行或整阶段独立PASS。作者局部2/2及旧CI273 DB/模型/Word2/2保护亦通过。

不自动合并，不启动新N抽查/RS04/RS05，不声明SUPPORTED或商业交付。原生Excel/WPS/桌面CU及企业真实样例仍NOT_RUN/DEFERRED；既有全量中的历史N01测试不等于新N抽查。仓库public由Owner直接授权，$0预算不变，未付费绕过或弱化required checks；用户文件和标准全文未带入本包。
