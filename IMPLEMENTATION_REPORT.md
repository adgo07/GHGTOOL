# B-MATERIAL 本地实施送验报告

2026-10-17。状态：LOCAL_IMPLEMENTED / 待源会话独立验收。本包完成后停止，不自动转下一包，不宣布正式标准 SUPPORTED 或商业发行就绪。唯一产品路线仍为 REFERENCE_STANDARD_ROADMAP.md。PR46 已合并、PR45 已关闭；固定历史退修/验收报告保持原样。

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
- v6 / 2.4.0 只在 B.3—B.5 增加 I—M 辅助列，九工作表结构保留，无数值默认；Excel 与 GUI 共用归一化/核算链。v2—v5 原字节与基线逐一核对不变。
- 新 v6 在入口实际识别并验证后冻结独立 template_master_sha256；填写工作簿 sha256 保持独立。项目 SQLite 重开、Record、Word 原样消费同一证据；旧 v5/历史无母版证据不补，异常结构直接拒绝。Word 从所选 Record trace 读取采用值与方法，不再次 resolve 或归一。
- 真实包内检查发现 Numeric guard 把当前 Calculator 身份重标为旧 N01C；已移除该版本覆盖，保留 guard/上下文/历史常量与历史向量。当前输入/结果/Record 的真实算法版本一致。

当前生产代码冻结提交：`5859ba7e71a5e4add659efeb4a8392adb3896d86`。其后只补反向测试与本文等文档，不修改生产树。算法 `CAR-SM01-2026-10-17-MATERIAL.1`；归一化 `CAR-MATERIAL-NORMALIZATION-V2`；材料采用 `GHGTOOL_MATERIAL_R11_V1`。

|资产|SHA256|
|---|---|
|material.json|1737efec0f3b27bc14b373d4e70f8870f162a3bef6a702931207f4dc6cd93c02|
|v6 母版|ca61cf3133c2663c78ca7409d23f7dd20726e43a8c79adca2aa78faecb3c031a|
|最终本地 EXE|2755698bce622a67ce4afd2d63591370d7625a78e5ab5c68f9cd1c9f6a8f2da3|

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

- 公开CI未触发（披露暂停）；无push、公开PR、日志/制品上传、merge或分支/工作树删除。
- 原生EXE完整业务点击、Excel/WPS v6原生填写保存再导入、真实鼠标/中文IME/人工DPI、企业真实案例、干净机器发行验收未执行。历史v5原生Office缺项不因本包自动关闭。
- RS04/RS05、第二标准、烟气生产接入、蒸汽/iapws、性能优化、Word排版延期项、商业法律/IP正式程序未实施。
- 不修改计算表用户参考文件；中央锁/PLATFORM_BASELINE/历史Numeric conformance未改。

本地送源会话独立验收后停止。验收可按以上完整失败历史、定向闭环、生产冻结提交及实际包体证据复核，不将本报告当独立验收结论。
