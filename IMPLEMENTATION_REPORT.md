# B-HEAT 实施报告 — 送独立验收

更新：2026-10-18。状态：READY_FOR_INDEPENDENT_ACCEPTANCE。

受验代码及实际制品head：`fca06e14a8526a968c27e3859888205079729864`；CI280 merge：`d21e84149b2110051e3d6e2da46e52e7a2ac8a99`。本回执提交只同步文档/证明，最新文档head以PR52为准，不能把制品来源改标为文档head。私有[PR52](https://github.com/adgo07/GHGTOOL/pull/52)保持OPEN、未合并。

## 平台 / Contract 预检查

业务base `a1aeebc1b6809397e61a2ffa7a2333a3b440c756`，工作树origin实际核实为adgo07/GHGTOOL且已fetch；当前任务分支codex/b-heat-integration。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，相关Frozen为Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；ACTIVE UI指南按中央正式main适用版读取。MUST：分层、共享Application、declared-profile consistency、ambient independence、full-value exact、原输入/规范/物性工作/显示值分开、Record/Word冻结。MUST NOT：业务epsilon、显示修约回流、隐式物性回退、Qt状态充当公共Workspace、自动升级Frozen。Carbon Decimal40/ROUND_HALF_UP是ALLOWED PROJECT DIFFERENCE；binary64物性子Profile单独声明，不冒称p40物性精度。C3资格漏项、工作Pa/K门禁不足均LOCAL DEFECT，不需改中央Contract。相关Standard Issue005/006/015/017/019；本包执行已经批准的软件决定，没有新增标准解释、标准范围或Frozen变更。

## 最终实现

- HEAT.1及codec5兼容读取1—4，无数据库迁移。旧项目未知边界仍可恢复，重新正式计算需明确事实；旧Record不回填、不重算。
- 015先判边界；内部且供热燃料已计入时保留原燃料全值、不重复购热，也不要求无关焓/因子。未知/冲突阻断；输出热力按原公式独立扣一次。
- 已知焓独立采用明确值/单位，不查P/T、旧表或自动物性；有限零/负值沿既有WARNING冻结原值和采用值。其余GUI字段负值门禁不变。
- 自动路径固定CoolProp8.0.0、NumPy2.3.3、revision ae81610e7d23efc57f9d051c8e70a4d66e87537f，显式IF97Backend；方法CAR-HEAT-IF97-017.1，子Profile GHGTOOL_COOLPROP_IF97_PROPERTY_V1。原始/规范/工作Pa-K/Q/原库Jkg词法/采用焓/真实phase/实现身份冻结。原值与实际binary64工作状态都须在域；工作Pa严格低于临界压，过热工作K严格高于同压Tsat并通过真实气相门禁，无epsilon、夹值、抬温或其他后端/旧表回退。
- heat.factor由同一次真实Resolver核资格、采用值和快照；Canonical小增量准确补齐独立C3来源与期间条件，不凭0.11同值冒认。实测空/非法不回默认，合法零保留。
- GUI/B.9→Canonical项目→共享Application正式追加Record→冻结Word同链，Excel预览零Record，项目跨启动恢复。新自动Word B.9展示方法，旧正文保持。
- v10/2.8.0仅B.9改变，SHA705a9326f6910bceaad34ce955975a6150731fa8ed2b50ddfe8c2c5188deb729；旧v2—v9原字节不变。Word布局元数据3.0.5；热力资源SHA37844a5b09fce7350ebc172457b768b86b665a4be8398408c4e2727be1216ca3。
- 固定运行身份探针、CoolProp delvewheel hook、14份原始许可/来源哈希随包核验；原始通知空白按源字节保留。工程候选不等于商业许可履约完成。

## 实际验证

| 证据来源与命令 | 实际结果 |
|---|---|
| GitHub CI280 merge-ref `python -m unittest discover -s tests -t . -v`，job117698607286 | 1010/1010，1912.733s，0FAIL/ERROR，skipped=0 |
| GitHub CI280 exact-head `python -m unittest tests.test_g08_delivery -v`，job117706232197 | 18/18，11.422s；构建、审计、ZIP回读、provenance及2次隔离启动通过 |
| C本地最终热力联合 `python -B -m unittest tests.test_b_heat_if97 tests.test_b_heat_specialist tests.test_b_heat_runtime tests.test_b_heat_chain.HeatQtTests tests.test_b_heat_chain.HeatExcelTests tests.test_numeric_contract_v1_adoption tests.test_g08_delivery -v` | 89/89，96.081s，0失败/错误/跳过 |
| C本地报告/记录/Excel入口五模块 | 46/46，135.016s；字段/来源卡/项目/codec+Word有45秒单项堆栈界限组合49/49，187.332s |
| C本地同R11机械审阅资产重生及校验 | 23项Python资产/来源审阅18.334s；25场景实际ArtifactTool往返通过，未冒称CI/源执行JS |
| 源独立fca工作状态三项定向unittest | 3/3，0.215s；不是源全量验收 |
| C本地对下载的CI280真实EXE/PYZ+包内CoolProp/NumPy/Qt执行 `python -B docs/ci/B_HEAT_PACKAGE_VERIFIER.py <CI280包> <新输出> fca06e14a8526a968c27e3859888205079729864 <实际CI273旧数据>` | 完整proof生成，进程退出码0；业务源码回退被禁止，原生依赖路径均在包内 |

重叠套件不相加。CI不是本地执行；实际CI包下载后程序化离屏核验是C本地执行。实际CI280 artifact `12140751279`，ZIP SHA `98b9a87204b667431a4b32ce31553a43dbaa05cc346725ab811e6549ceddb3c0`，75707621字节；manifest列321文件，ZIP 322文件。制品manifest source_commit/pr_head均为fca，tested_merge为上述CI merge，原文件哈希与上传包清单一致。包内资源/通知/PE x64与固定CP/NP身份已核。精确数据见B_HEAT_CI280_RECEIPT_PROOF.json。

真实CI279旧包复现：raw22.06399999999999999999999999999999999999MPa→working22064000.0Pa，真实twophase，旧错误生成1Record；新CI280同反例拒绝且0新增Record，邻近合法Pa和真实气相K仍采用。新包同时证明ambient6/17/60相同结果、饱和Q1、known独立及非正WARNING、实测零不回默认/负值阻断、内部原燃料8.624000000000000000000000000000000000001完整保持、购热/输出一次抵扣0.154000000、C3期间来源、Qt/Excel项目重开/正式Record/冻结Word。

实际CI273旧EXE/PYZ生成两条合成热力Record，当前reader拦截Calculator/Resolver后重放：known模型29a564bbbdc221c5a34c223c39e8001352d853f3f60d2a1d8fa65c675d7ddc2c / XML e93c2ef859cc44a547a16b9a3e02a756426e1d09089126f13caf194bbb5955fe；old-auto模型0578d13aead197d0b8f14f6c9a344be3946236e76fd4729b40a4d6d6802d6bb1 / XML51735e78cf9571f0d074010ba26e4be6ee504b96ab0a1ab230de097e980d4df5。模型和Word正文完全一致，原DB不变；不是企业真实案例或新算法重算旧输入。

## 失败对账与定向修复

| 旧CI | head / merge | 实际结果及处置 |
|---|---|---|
|276 /39128755391| f85e058 / a4de96d507c4a9bdcd121a5835a58f4022ce705a |1006项，2027.458s，1FAIL+2ERROR；UIR04旧边界/文案、C3 raw字节投影、Mapping定义hash；standalone跳过|
|277 /39129892649| e931c21 /903a8d9fa8f936b87734f3fe79458ddb35621e9f |1006项，1925.620s，2ERROR；剩C3字节/Mapping hash；standalone跳过|
|278 /39130931396| a7d5d46 /78c547019f1c243058297577d5a2c1bc8b391eb5 |1007项，1900.408s，1ERROR；仅Mapping hash；standalone跳过|
|279 /39132032103|24901e1 /fc0cee485bab1e3148ac00c4f20036d7cd1a9979 |1007/1007，1860.444s；G08 18/18，11.038s；包审计321、ZIP322、2启动通过。但真实包仍有临界工作状态缺陷，被fca取代，不放行|

C3本地CRLF/Git LF真实干净blob复现后，按既有LF保存并机械投影；仅末项来源sha变化，fields/policies/前三来源完全相同。投影器明确拒CRLF，不读取时归一化hash。源SHA1dd97fd8c8eeac5f22dbe17779904d6bf20179f9eab3d3e0a19d22022aa8fd9c；原3Canonical不改。同R11按既有PREFLIGHT机械重生审阅四件套，新旧全部单元格值/Table名称/ref相同，仓内该previous意见0→0，不推断用户附件；3表61行、450原有scope（既有442+Issue010八项），每表8隐藏技术列，最高344pt≤409。源独立重算四件套/4定义hash 8/8。证明见CANONICAL_BYTE/REVIEW_ASSET JSON。

其他真实失败保留：旧广Qt组合5项旧断言失败后Word入口停顿被终止，无最终统计；修复后独立报告46及有界组合49均通过，停顿原因未确定。新known测试误用severity造成2subtestERROR，改真实level并保留原值/采用值断言。初包验证器宿主openpyxl/包内lxml冲突，改全包内加载后通过，未改产品。F低压.0001MPa/300K成功初报撤回，真实后端超域拒绝、无绕行。工作门禁修前2测试3FAIL；首轮89项1ERROR因错误假定Tsat首ULP为气相，实际库仍液相，改实际合法气相正例后3/3 .229s、89/89 96.081s，无生产门禁放宽。

## 未执行项与停止边界

等待源独立验收；不自行合并、不启动下一包、不纳入M外部CO₂、不改PR49/50/51。原生Office、鼠标/中文IME/人工DPI、企业真实样例、干净目标机和商业许可履约OPEN；程序化Qt离屏/ArtifactTool可读性不替代原生验收。不CU、不商业发布、不宣布SUPPORTED，不改Frozen/路线/用户原脏树/计算表。

完整原始证明见docs/ci/B_HEAT_*PROOF.json及B_HEAT_IF97_CANDIDATE*_RAW.json；本次CI实际日志和本地全部执行日志在tmp/b-heat保留，摘要不隐藏失败。nanobind退出诊断与退出码/条件的最小核查见B_HEAT_EXIT_DIAGNOSTIC_PROOF.json。

退出诊断：原完整宿主验证器exit0但模块关闭时报告nanobind对象未释放；相同脚本显式释放临时sat_state并回收后exit0无诊断。最终验证器仅在提取Tsat后立即del该对象，实际CI280包exit0且无nanobind/Traceback。包内PYZ app.main程序化Qt正常quit为0无诊断；首次Qt探针调用静态exec误传self的TypeError/exit1保留。原生EXE人工正常关闭未执行，不能用终止式smoke替代。下载包本地审计首轮因宿主PYTHONPATH漏当前仓库而ModuleNotFoundError/exit1，发生在审计前，修正审计路径后通过；实际包验证器仍去除仓库源码路径。完整日志/条件/退出码均入原始proof。

回执格式核验：原始proof按-text保留实际CRLF字节，首次默认git diff --cached --check把CR报为行尾空白，未提交；使用仅明确cr-at-eol并保留blank-at-eol/blank-at-eof/space-before-tab检查后通过，不改原始proof或许可证字节。
