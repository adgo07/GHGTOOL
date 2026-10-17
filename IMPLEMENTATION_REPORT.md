# B-MATERIAL 本地实施送验报告

2026-10-18更新。状态：PR49六项验收意见修订 / 新head待独立验收与CI。原d5205f5已技术+CI验收通过，cad63f19及本轮提交需单独验证。本包完成后停止，不自动转下一包，不宣布正式标准 SUPPORTED 或商业发行就绪。唯一产品路线仍为 REFERENCE_STANDARD_ROADMAP.md。PR46 已合并、PR45 已关闭；固定历史退修/验收报告保持原样。

## 平台 / Contract 预检查

实际核验 origin 为 adgo07/GHGTOOL，fetch 后从 main `dada7a188db55a2384ea3aad48038aa4472158b2` 创建隔离分支 codex/b-material-integration。执行不使用原 checkout 的用户工作簿。

中央锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，按该 SHA 读取 Architecture V2.1、Numeric Contract v1、Numeric Profiles v1。适用 MUST：分层、共享 Canonical/Application/Calculator、declared-profile consistency、ambient independence、正式完整值比较、不可变 Record 与历史快照不漂移。MUST NOT：未声明 float、隐式中间修约、业务 epsilon、显示回流、自动升级 Frozen。项目 p40/ROUND_HALF_UP 为 ALLOWED PROJECT DIFFERENCE；版本守卫缺陷属 LOCAL DEFECT。无 CENTRAL CONTRACT GAP，无中央 Contract 修改。Workspace 等 DRAFT 不称 Frozen。

当前 ACTIVE UI v0.2 及家族清单已读取，不据此升级 Frozen。相关 Standard Issue：004、016、018；本包落实已有效的软件决定，不新增标准原文解释。干基到收到基方法由 Owner 在材料会话明确授权；原文事实、技术判断和软件决定分开，未将该实现写成标准明文。无新官方因子。无长期知识条目新增。

## 实际交付范围

- material.json 为 R11 中固定碳/挥发分两字段的独立机械投影；原燃料/电力五字段资源、SHA、采用身份保留。共享 evaluator 保持唯一求值入口，材料薄 Adapter 不建立第二套算法。
- MaterialInputLine 增加兼容尾字段。质量基准、含量基准分别归一且各执行一次；干基方法要求明确收到基水分及方法，0 水分合法，缺方法/必要值阻断。百分数/ratio 严格解析，不猜测空气干燥基/干燥无灰基，不虚构附件门槛。
- MATERIAL_V2 按煅后料、欠烧回收料、粉尘各自碳量扣减，不跨角色共享平均含量；公式系数与既有执行次序保持。原始行和收到基采用行分别进入冻结 trace。旧 MATERIAL_V1 仅显式兼容原收到基实测组合，未知执行版本可读、不能正式核算。
- GUI 保留 instance/line/role 身份、分来源草稿，覆盖改名、中间删行、保存重开。升级须明确确认；取消不写回。Canonical 项目升级另存新项目/持久化单元身份，保留原项目和原始输入，不复用全局唯一 unit_id。
- codec2 兼容 codec1，旧缺字段按真实旧语义恢复；不迁移数据库，不改历史 Record。预览不写 Record；保存 Canonical 项目后正式 Application 核算成功新增不可变 Record，失败零新增。
- v6 / 2.4.0 在 B.3—B.5各增加 I—M 共5辅助列和1说明行，九工作表结构保留，无数值默认；Excel 与 GUI 共用归一化/核算链。v2—v5 原字节与基线逐一核对不变。
- 新 v6 在入口实际识别并验证后冻结独立 template_master_sha256；填写工作簿 sha256 保持独立。项目 SQLite 重开、Record、Word 原样消费同一证据；旧 v5/历史无母版证据不补，异常结构直接拒绝。Word 从所选 Record trace 读取采用值与方法，不再次 resolve 或归一。
- 真实包内检查发现 Numeric guard 把当前 Calculator 身份重标为旧 N01C；已移除该版本覆盖，保留 guard/上下文/历史常量与历史向量。当前输入/结果/Record 的真实算法版本一致。

原业务链断点为`5859ba7e71a5e4add659efeb4a8392adb3896d86`，仅代表当时的材料整链与本地包证据。随后e04d1fc修测试、d5205f5新增Qt6.12精确构建路径加固；`cad63f19cf5a25cc5e25fc2d1b8bdceaefb6b389`又新增材料重复line_id业务身份校验及6项测试，故最终业务实现不能再称冻结于5859。当前本轮基点为cad63f19，本轮只修文档/审阅生成器及产物；最终送验提交以PR49 head与对应CI为准。算法 `CAR-SM01-2026-10-17-MATERIAL.1`；归一化 `CAR-MATERIAL-NORMALIZATION-V2`；材料采用 `GHGTOOL_MATERIAL_R11_V1`。

|资产|SHA256|
|---|---|
|material.json|1737efec0f3b27bc14b373d4e70f8870f162a3bef6a702931207f4dc6cd93c02|
|v6 母版|ca61cf3133c2663c78ca7409d23f7dd20726e43a8c79adca2aa78faecb3c031a|
|5859原断点本地 EXE（非最终PR制品）|2755698bce622a67ce4afd2d63591370d7625a78e5ab5c68f9cd1c9f6a8f2da3|

## 本地验证与失败历史

环境：Python 3.12.14、PySide6/Qt 6.11.2、PyInstaller 6.22.3。以下均为本地执行，非 GitHub Actions；各测试组有重叠，不累加。临时工作簿/Repository 使用测试临时路径；最终命令另设 LOCALAPPDATA/TEMP/TMP 到隔离输出。用户数据库元数据时间仅辅助观察，不作为隔离证明。

命令中的 python 为上述真实 3.12 解释器，PYTHONPATH 指向已有依赖目录；Qt 使用 offscreen。

|命令/范围|实际结果与处置|
|---|---|
|python -B -m unittest tests.test_b_material_normalization tests.test_b_material_policy -v（M）|30/30，0.226s；此前 SQLite 夹具冲突 28 PASS/1 ERROR 已修正|
|python -B -m unittest tests.test_b_material_policy tests.test_b_material_normalization tests.test_b_material_chain tests.test_b_material_gui_excel -v|首轮35项34 PASS/1 ERROR（升级副本 unit_id）；修复后35/35，10.049s|
|原五字段/渠道/模板/交付保护8文件|首轮74项68 PASS/4 FAIL/2 ERROR；修复夹具与版本预期后受影响4文件36/36，10.054s|
|python -B -m unittest discover -s tests -v，提交2368380|816项，1122.271s，812 PASS/4 FAIL/0 ERROR；四失败均为 v5/下载测试仍引用当前默认 v6 或写死2.3文件名。完整日志 tmp/material-full-final.log|
|python -B -m unittest tests.test_fuel_power_template_v5 tests.test_p3_e_excel_import -v|原 v5 测试绑定保留 v5 资源，当前下载核实际登记版本；13/13，1.777s。没有删去旧 OOXML/字节/版本断言|
|python -B -m unittest tests.test_numeric_contract_v1_adoption tests.test_qzc_n01_c_numeric_unit_pilot tests.test_b_material_policy tests.test_b_material_normalization tests.test_b_material_chain tests.test_b_material_gui_excel -v|版本修复首轮63项62 PASS/1 FAIL（历史向量身份预期）；修正后64/64，11.033s，保留历史向量版本|
|python -B -m unittest tests.test_g08_delivery -v|16/16，6.406s，含精确包体排除/拒绝混入测试|
|python -B -m unittest tests.test_b_material_gui_excel tests.test_pr46_report_template_identity tests.test_rs03_record_ingress_evidence tests.test_rs03_excel_project_workflow -v|最终15/15，25.865s；SQLite重开/不同母版和填写SHA/旧v5不补证据/异常表头拒绝/历史报告保护。补充首轮15项1 ERROR为测试错期望返回对象，实际入口抛 WorkbookFatalError；已按拒绝行为修正。一次误写两个模块名导致3 ERROR属命令错误，已纠正|

首次全量运行曾在发现历史来源夹具失败后中断，不当完整证据。完整816项运行的四失败由上述13项定向闭环；后续 Numeric/包体/母版改动各有定向覆盖。按源会话决定不重复无关全量，故**没有“最新 head 全量 PASS”的证据**。

离屏1366×900使用现有Windows字体检查材料行和窗口，中文可读、未见裁切，截图 tmp/material-visual/material-row-font.png；不代表真实鼠标/IME/人工DPI验收。

## 最终包体及商业依赖预检查

本地命令：`python -B -m scripts.build_standalone --output-root tmp/material-build-evidence-final`，成功，内置交付/归档审计通过。manifest source_commit 为5859ba7完整SHA；265文件含manifest，12个Qt DLL、21插件。

`python -B -m scripts.smoke_standalone tmp/material-build-evidence-final/QingzhouCarbonAccounting --starts 2`：两次独立临时用户目录离屏启动 PASS。

`python -B tmp/material_packaged_code_proof.py tmp/material-build-evidence-final/QingzhouCarbonAccounting tmp/material-packaged-proof-evidence-final`：从交付EXE实际PYZ加载业务代码及包内资源，禁止业务模块回退源码；逐角色结果226.8291666666666666666666666666666666667、干基案例158.9041666666666666666666666666666666667；非法方法零新增，两个成功Record，冻结Word42421字节。当前算法身份一致。该证据明确为 EXE_PYZ_CODE_WITH_PACKAGED_RESOURCES_NOT_NATIVE_UI，不冒充原生EXE业务点击。

实包先前自动收集未使用的 Qt Virtual Keyboard（官方Qt6.11许可列表为GPL-only）。仅在路径/符号链接边界检查后精确排除 Qt6VirtualKeyboard.dll 和 qtvirtualkeyboardplugin.dll，保留其他插件正常收集；不改安装环境。最终实际路径与PE正常/延迟imports检查均无该组件或引用，也无iapws。许可文件名路径枚举为空只说明当前文件枚举结果，不证明上游无许可或分发义务已满足。

直接依赖/构建工具实际版本已记 docs/DELIVERY.md 与 requirements-build.txt。Qt/PySide LGPL履约、第三方通知、源码/重新链接安排、其他DLL分发权利与正式发行材料仍待完成；不作法律或商业放行。官方依据见 docs/DELIVERY.md，未采购许可、未提交知识产权申请。

本地可检查证据：tmp/material-build-evidence-final.log、tmp/material-smoke-evidence-final.log、tmp/material-packaged-proof-evidence-final/proof.json、tmp/material-package-license-inventory-evidence-final.json、tmp/material-master-negatives-final.log。输出保留本地忽略目录，未上传。

## 有限并行交接

M 原提交 ffd27e9 已以91312cf集成；F 准备557f2c6独立烟气段模块及测试33/33、Numeric28/28，未 cherry-pick 到本包，无生产消费者。N 最终0805b10为独立测量脚本，未集成本包；固定产品dada7a18，5/5独立进程、360计时操作（不是测试），20:37:03—20:43:51本地正式采样。

N 中位数 handler/eventpump：首次新建4571/4801ms，首次记录630/671，首次因子224/243，热标准998/1042，热记录1016/1063，草稿恢复2350/2648，20行恢复3278/3764，记录详情355/395；构造2719ms。观察到200次get嵌套list_all，仅作基线，不宣称根因或完成优化。原始数据留N本地 .n-benchmark-local/formal，格式化脚本AST一致。F/N均已停止，不转下一包。

## NOT_RUN 与停止边界

- 原本地送验时未push/CI的历史限制已被Owner私有化/push/私有PR/CI授权取代；已执行私有CI，未公开上传、merge或删除分支/工作树。
- 原生EXE完整业务点击、Excel/WPS v6原生填写保存再导入、真实鼠标/中文IME/人工DPI、企业真实案例、干净机器发行验收未执行。历史v5原生Office缺项不因本包自动关闭。
- RS04/RS05、第二标准、烟气生产接入、蒸汽/iapws、性能优化、Word排版延期项、商业法律/IP正式程序未实施。
- 不修改计算表用户参考文件；中央锁/PLATFORM_BASELINE/历史Numeric conformance未改。

本地送源会话独立验收后停止。验收可按以上完整失败历史、定向闭环、生产冻结提交及实际包体证据复核，不将本报告当独立验收结论。

## 私有仓推送与 CI250 退修断点（2026-10-17）

Owner 后续明确授权仓库转私有后推送及CI。源会话已执行私有化，本会话GET复核visibility=private，origin/main仍dada7a18；推送受验4b656911并创建私有PR49。此前“未push/未PR/未CI”是当时记录，不是当前状态；未授权merge、销售或下一包。

GitHub Actions Windows CI #250，run39038977148，PR head4b656911，实际checkout merge-ref af0edeba37fa49b755f752db97a7db805e3aa14d。Canonical/编译/pip check/数据库/GUI/缩放均成功；全量819项1189.610s，817PASS/2FAIL/0ERROR，exact-head standalone因needs跳过，不能称CI通过。

失败定位：新v6冻结母版后，EXB01整链测试仍断言母版空；当前真实算法身份修复后，UAT03仍断言旧G06.2字符串。仅更新这两处测试：核同Record冻结母版=当前受控母版且与填写SHA不同；核outcome/result精确等于声明ALGORITHM_VERSION。已有Numeric正式Record版本一致及PR46旧无母版仍空保护保留并同组执行，未放宽为任意非空。

本地命令：python -B -m unittest tests.test_exb01_rpt02_integration tests.test_uat03_rules tests.test_pr46_report_template_identity tests.test_numeric_contract_v1_adoption tests.test_qzc_n01_c_numeric_unit_pilot -v；49/49，8.650s，日志tmp/material-ci250-fixture-closure.log。无生产/资源/依赖策略修改。新提交须源会话复核及重新CI/此前跳过的exact-head构建审计。

CI实装CPython3.12.10、PySide6/Essentials/Addons/shiboken6 6.12.0及新增拆分包PySide6-WebEngine/Pdf；本地旧包为Python3.12.14/Qt6.11.2。该环境差异如实保留，不能把未生成CI包当作本地包相同；不自行改依赖策略或付费设置。

## CI251 构建布局退修（2026-10-17）

e04d1fc的GitHub Actions CI251/run39040774659：merge-ref04b182bfa63e20291310586e2d661085f2ee0939全量819/819，1178.754s通过；exact-head G08 16/16，5.777s通过，但实际构建审计拒绝PySide6/Qt6VirtualKeyboard.dll，整体CI失败，未上传成功制品。Qt6.12改变DLL收集目录，旧root精确路径未覆盖。

仅在构建已有列表增加已实证PySide6/Qt6VirtualKeyboard.dll，保留旧root DLL/插件路径、symlink/resolve根边界与包体拒绝门禁；不通配排除其他Qt、不改安装环境或依赖策略。G08补两种布局、其他组件保留、symlink/越界拒绝（注入文件系统分类，不声称创建真实Windows外链）。本地python -B -m unittest tests.test_g08_delivery -v：17/17，6.932s，tmp/material-ci251-build-closure.log。新head需复核和新CI实际构建/剩余DLL正常与延迟imports核验；此前本地6.11清单不能替代6.12包体。原生IME仍NOT_RUN。

## PR49 六项验收意见修订（2026-10-18）

开工实际核实origin正确，工作树干净，从d5205f5 fast-forward到远端cad63f19cf5a25cc5e25fc2d1b8bdceaefb6b389，保留重复材料line_id碰撞阻断（2文件140行）。该补丁是5859之后的业务身份校验，不是仅文档变化；源会话在cad63独立执行test_b_material_identity 6/6，0.915s，本会话未重复该组。业务仓本轮起点cad63，locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；本轮只修说明及审阅开发产物，不涉及中央公共Contract变更、专业公式、标准范围或历史Record解释。004/016/018关联不变，无新增Standard Issue。

1. 版本证据改为5859原整链断点→d5205f5构建加固→cad63业务身份校验，撤销“最终业务冻结5859/之后只测试文档”的失实表述。旧包证据保留原身份，不替新head背书。
2. Mapping头补GHGTOOL_MATERIAL_R11_V1两材料字段已采用；明确脱硫/外部CO₂/烟气/蒸汽等未由本包接管。审阅A3/A4、同源HTML和checks compatibility区分视图自身与PR49的材料、v6、冻结报告变更；不修改Canonical规则定义/版本/运行资源。
3. ROADMAP、DELIVERY、HANDOFF、TASK_STATE现行授权统一为Owner已授权私有化、push、私有PR49及CI，明确取代旧本地限制；不扩大到公开上传、商业发布、合并或CU。历史执行记录仍保持当时结果。
4. 增加仅元数据/统计/制品hash的本地可读evidence/CI252_SUMMARY.json，不含token/源码/原始日志；CI252只背书d5205f5，cad63的CI253开工时in_progress。后续新head需各自CI；最终运行摘要另以实际完成结果交接，不能套旧PASS。
5. 实际只读对比v5/v6：B.3/B.4为13行8列→14行13列，B.5为12行8列→13行13列；各+5辅助列（I—M）及+1说明行（B3/B4 A14、B5 A13）。已补报告/DELIVERY/审阅兼容说明；模板字节及登记SHA不改。
6. 原生v6 Excel/WPS保存回导、真实鼠标/中文IME/人工DPI、企业样例仍OPEN，禁止用离屏或CI自动替代，也未启动CU。

机械重生按PREFLIGHT既有命令完成：validate_business_rules_candidate.py导出review/technical/catalog同版本输入；build_business_rules_review.mjs通过--previous保留意见；test_business_rules_review.mjs --builder/--input/--technical-input/--node-modules/--output执行25/25场景PASS；business_rules_review_checks.py --previous核三表29/21/11、652组合、450条件与意见0→0；business_rules_review_hashes.py验证4定义资产PASS。Mapping规范化SHA机械更新为01e5adff362b5e4f1d15ad6141c0d1359a4ef5a3a31bbcd30abf57f84d84b5c7；工作簿SHA a47855f781c0c52f80c083d600dd11e5a0983e31e79927dcede090fae6c8375f，未手盖清单。builder导出前执行一次recalculate，表内无公式，未改业务规则。

本地定向命令：python -B -m unittest tests.test_business_rules_candidate_assets tests.test_pr48_mapping_arithmetic tests.test_b_material_policy -v，30/30，12.698s；python -B -m scripts.project_material_rules机械投影PASS。只读对比同版本前后表数据仅三表A3/A4共6处改变，表范围/冻结窗格/其他值保留；ArtifactTool渲染三表开头可读，非原生Office验收。日志/预览位于tmp/review-rework-r11；固定四件套同源重生后入仓。

本轮未重复完整本地回归/旧包构建，等待新head CI；此前本地816失败历史、CI250/251失败及CI252成功各有独立身份，不互相替代。不合并、不启动下一包、不改专业口径或历史Record。

## F03 实例来源草稿隔离（2026-10-18，F02仍处理中）

完整读取Owner新增cad63独立验收报告，F01保留不重复修。实际Qt离屏反例（tmp/material-f02-f03-before.log）2项均FAIL：计算来源标签仍收到基换算；两个煅烧实例复用feed-local经SQLite重开后未各自恢复。该反例不冒充原生鼠标/IME。

F03修复：控件Presentation objectName纳入工序类型/实例，正式instance_id/line_id不改；material_source_drafts版本2按工序类型→实例→行→字段→来源隔离。旧仅line_id草稿及扁平控件名仅唯一对应时恢复；歧义不猜贴、不覆盖当前可辨识输入，原未采用草稿/扁平值随form_state保留，来源提示显示原草稿供核实，不新增DB/通用迁移框架。两实例同局部ID、同名不同ID、中间删行、来源往返、SQLite保存重开、旧唯一与歧义保留已覆盖。

本地命令：python -B -m unittest（F03三用例、test_b_material_gui_excel、test_accounting_projects_ui）-v：25项24PASS/1ERROR，126.263s；唯一错误为提示控件误用addItem（实际QTreeWidget），已改正确addTopLevelItem。修正后python -B -m unittest tests.test_b_material_draft_scope -v：3/3，26.210s（tmp/material-f03-final.log）。其余22项此前通过，不冒称25项已重跑全过。F02标签/实际模板/来源报告分离继续处理，后续最终head统一CI。
