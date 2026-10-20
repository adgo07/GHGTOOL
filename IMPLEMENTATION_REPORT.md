# B-EXTERNAL 实施报告（作者执行）

状态：此前最终head 73c47a9已完成CI287与实际制品验证；当前按源授权处理PR53复核退修，证据与原CI286历史分列于文末。未合并，待新head证据及源独立验收。

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


## PR53 复核退修（2026-10-20）

平台 / Contract 预检查：继续原 PR53 分支，开工核对 origin 为 adgo07/GHGTOOL、fetch 后 head 73c47a98044c00591d6717d1d47d3a05f5aecffe、工作区干净。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20 不变；Architecture V2.1 / Numeric v1 / Profiles v1 的分层、Profile 一致、ambient 独立及不可变 Record MUST 不变。不得更改公式、Numeric、旧 Record 或把 Presentation State 定义为公共 Workspace Contract；属于本地兼容缺陷与提示修复，无中央 Contract 修改。相关 Standard Issue 为016；本轮不改变既有软件解释。

此前最终显示补丁已有 [CI287](https://github.com/adgo07/GHGTOOL/actions/runs/39410582292) 与实际下载制品证据：head 73c47a9，merge ff2a373，GitHub 全量1031/1698.091s、G08 18/8.369s，0失败/错误/跳过。artifact12260549104，75,747,968字节，ZIP SHA256 df8e32283b05265c15ddab918816a21e2571a5c3fa0452df41784190837b37c9，manifest SHA256 2ac64788c0f1689679921ae8c99c64ab70de4ed430345ca1421c96dcedd87f4b，322列项+manifest自身323文件；实际EXE/PYZ、包内原生依赖、状态文案、母版复制、旧CI273记录保护及2启动通过。源另独立核验API与322文件哈希（源提供证据，非作者执行）。CI286继续保留为不含显示补丁的历史证据；CI287不能证明本轮新指纹修复。

F01修复前：实际PR52 merge 0f506425旧代码运行GUI计算/保存生成SQLite项目，当前代码动态关闭重开两次均误报stale并隐藏结果；历史calculation fingerprint a283337c88c506af90bf6c346710889924a3782ce6529b4ca69087d3f05f0844，新增空字段后变为2cc2d1c35c137ae97277503a9d543b1b5d2d41fa508a2e1ef262af68b399464f。仅根external_co2=None按缺省缺失处理，显式纳入/不纳入保留差异；合成旧SQLite/Word/生成脚本与proof纳入回归，非删除新字段手造旧指纹。F02只改GUI业务提醒。模板能力归并为有界已知版本表，未知未来版本拒绝，2.4专有别名和旧热力种子规则保留，母版/XML字节不动。投影片段README说明其构建用途。交付验证缺pip明确前置失败，不skip，原强制CI不变。

本地首轮新回归5项中3通过、2ERROR（测试引用错误的热力行键及Importer类名，业务恢复/Word断言已通过）；已修正测试接口。稳定产品断点1fb4cd50ca77b3c31bc3e63c44abe94cc0eaad49；`python -B -m unittest tests.test_b_external_review tests.test_b_external_excel tests.test_b_fgd_legacy_templates tests.test_b_material_source_review tests.test_fuel_power_template_v5 tests.test_b_heat_chain tests.test_g08_delivery -v`：本地56/56通过，218.023s，0失败/错误/跳过；日志SHA256 6774aad6a74e3d4b35a9973aea5a3523be09eb882d8fbbca8e41a95ada815b73。`python -B scripts/validate_canonical.py`：9 standards/12 sources/102 parameters/138 factors有效；`python -B -m compileall -q apps packages resources scripts tests docs/ci/B_EXTERNAL_PACKAGE_VERIFIER.py`通过。真实wheel/sdist安装资源验证已执行，缺pip测试验证明确失败且不构建。未追加本地全量，跨模块全量由必需Windows merge-ref CI执行，避免重复昂贵检查；原生CU与N抽查未执行，按任务边界延期。下一步一次稳定推送，取得新head CI/实际制品及源独立验收；最终回执落PR53当前checks/说明与本地proof，不为纯文档再触发CI，不合并。
