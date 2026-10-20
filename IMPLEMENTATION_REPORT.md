# B-EXTERNAL 实施报告（作者执行，S4进行中）

本包按Owner授权审查并细化既有任务书后实施，唯一共享执行者C，独立树codex/b-external-integration从main@0f50642544b110ee461f1b32ef8a01091d0f44d0开始；原根用户修改与旧热力树未提交文档未动。PR52已合并，旧CI仅为历史保护输入，不背书本包。

## 平台 / Contract 预检查

业务仓origin已核为adgo07/GHGTOOL，已fetch/default main。锁定中央ee5feb0cc34dbd99790500fadd0c4c932e202a20，Architecture V2.1/Numeric v1/Profiles v1为Frozen；声明Profile一致、ambient独立、full-value exact、分层及不可变Record为MUST。禁止显示修约回流、业务epsilon、消费者重算/查目录、旧Record回填或自动升级Frozen。Carbon p40/HALF_UP是ALLOWED PROJECT DIFFERENCE，非平台默认。Issue016与Mapping11.1已有批准，本包不新增专业解释；旧声明即ERROR为LOCAL DEFECT，不需改中央Contract或数据库迁移。读取当前ACTIVE UI v0.2，不冒称Frozen。

## 最终实施范围

软件补充独立Domain求值，版本CAR-EXTERNAL-CO2-016.1，共享Calculator新记录身份EXTERNAL.1。原标准ES/EI/ET和CalculationLine不改；采用完整ET与外部量按同声明Profile只求和一次，独立software_supplement节点冻结。勾选为用户声明同边界/同期/原结果未计入，不宣称自动核验；明确反证阻断。未纳入、纳入待补、真实0、合法正值、历史缺失分别保留；原烟气覆盖缺口与补充缺失独立。

GUI三项输入及原其他活动/运输声明可访问，禁用非法草稿保存/恢复，确认提示不清除声明。行业payload6兼容1—5缺失为None，通用封套仍2且拒绝内外版本错配。Excel v11/2.9.0在原九表后新增软件补充页，旧v2—v10字节不改且保留构建资源。原九表XML逐字节相同；当前母版SHA256 b1e843a1eb8980c5a9bf4ee11d5b2369abcb89ebf4ca5b8659d8cccaefd166c4。新增页仍按既有Excel Numeric词法/15位策略读取，未纳入草稿不做数值采用。

共享ReportModel/记录页/Word只读同Record冻结节点，不在消费者求和；新Schema3.1.0/布局3.0.6，原无节点的历史报告保持3.0.0与原正文。软件节非B.10、不替换B.1、不承诺完整企业核验。消费者增量记录本包直接冲突清理，未启动N抽查/RS04/RS05或跨阶段重构。

Mapping仅同步实际接管状态，R11候选与3份Canonical原字节不改；审阅四件套按PREFLIGHT机械重生并保留意见，61行/450scope/25场景/每表8隐藏技术列不变，最高行344pt。报告Schema/架构及构建精确白名单同步，未新增主要依赖。

## 本地执行证据

- python -B -m unittest tests.test_b_external_runtime tests.test_b_external_chain tests.test_b_external_excel tests.test_g08_delivery -v：32通过/0失败/0错误，37.909s；日志tmp/b-external/adapter-final.log。含真实GUI两次成功新增两条、失败零新增；Excel预览零Record、Canonical/SQLite恢复、禁用NaN草稿、空/0/正值、词法/精度/公式、冻结Word及旧九表保护。
- python -B -m unittest tests.test_business_rules_candidate_assets -v：20通过/0失败/0错误，10.378s；25场景JavaScript往返为本地ArtifactTool执行，非Actions。证据docs/ci/B_EXTERNAL_REVIEW_ASSET_PROOF.json。
- 实际旧CI273合成记录2/2的数据库、ReportModel和Word正文不变；固定原导出日期避免当天日期造成非业务差异。证据docs/ci/B_EXTERNAL_HISTORY_PROOF.json。
- validate_canonical：9标准/12来源/102参数/138因子；pip check无依赖冲突；compileall、v11机械投影与构建资源预检查通过。新增卡片及最终模板完成程序化离屏/ArtifactTool视觉核验，不是原生CU。

完整本地unittest仍在执行，Windows Actions与exact-head新制品待S4完成；未执行项不写PASS。

## 失败与修正记录

首批7项曾1FAIL：测试忽略原燃料p40尾数，改用独立公式预期，未修约产品。新增37项批次曾1FAIL/1ERROR：烟气p40尾数预期及测试控件名错误；85项批次剩1FAIL为既有GUI显示0.308的测试假设，均已修正并由最新32项复验。最初v11虽可被openpyxl读取但ArtifactTool最终读取拒绝OPC前缀序列化，修正为保留原内容类型/关系命名并成功重读渲染。首轮完整探测为修模板主动中止，无完整通过计数。审阅builder首调previous路径缺evidence导致ENOENT，未覆盖旧资产；改实际路径后完整生成/核验通过。

## 交付边界

代码待稳定测试后送独立PR，后续报告将区分产品head、文档head、CI merge-ref及实际制品head。无自动合并、无商业交付、无标准SUPPORTED声明；原生Excel/WPS/桌面CU及企业真实样例仍按后续正式验收安排。仓库public经Owner授权，$0预算不变，未公开用户文件或标准全文。完成S4后停止等待源独立验收。


S4复核增量：代码审查重现损坏payload fields=None抛TypeError、合法1e100冻结值显示历史未记录，已修为统一codec错误及科学计数展示；不改计算结果。最新python -B -m unittest tests.test_b_external_runtime tests.test_b_external_chain tests.test_b_external_excel tests.test_g08_delivery -v为33/33通过（15补充+18G08），37.984s，tmp/b-external/edge-final.log。新增极小非零显示亦保持非零。UIR04五场景及125%/150%离屏探针通过，非原生CU。首个本地独立包695af96已构建成功；最终修正后的包继续验证，均非Actions证据。


S4首轮完整回归：python -B -m unittest discover -s tests -t . -v实际1028项、1323.438s、4FAIL/1ERROR（1023通过），不能写全量PASS。发现v11材料独立parser遗漏2.9、通用封套误假设所有行业payload都有version字段；已补v11版本并由codec显式声明其内部版本字段，保留非炭素分派，不新增标准算法。两项旧断言分别仍要求声明阻断、当前模板仅九表，按批准行为同步。命令python -B -m unittest tests.test_b_external_runtime tests.test_b_external_chain tests.test_b_external_excel tests.test_g08_delivery tests.test_standard_dispatch tests.test_b_material_gui_excel tests.test_b_material_source_review tests.test_g06_page.G06PageTests.test_page_preserves_other_activity_and_transport_as_warnings tests.test_rpt02_appendix_b -v：64/64通过、54.880s（tmp/b-external/regression-fix.log）。将再次执行冻结head本地全量；尚未push/触发本包CI。实际包验收器增加v11材料换算路径；其扩展时一次SOURCE_FUME漏导入属开发验证脚本失败，已修正并保留失败日志，不算产品通过。
