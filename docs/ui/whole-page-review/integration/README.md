# 正式集成回归与燃料来源适配器补齐

**当前状态已由后续专项A更新：原始命令完整1074/1074通过，0失败/错误，2741.635秒；源码/测试/资源哈希无变化，未处理的已删除Qt对象异常0。** 当前结论、两个生命周期回归及新8源绑定图见`qt-lifecycle/README.md`、`qt-lifecycle/full/identity.json`和根IMPLEMENTATION_REPORT。下文1071/1072失败与HOLD是保留的历史诊断，不是最新结论；不覆盖旧证据。

本目录保全首轮失败、定向诊断和受影响燃料截图，不能用局部通过覆盖首轮失败。原`../final/`对应53a本地独立验收的历史证据，151项受验身份及最后8行定位差异仍按原报告理解；本次新增生产差异超出那8行。

本目录`.gitattributes`仅对证据log/json/txt禁用Git文本换行归一，并把原始CR视为行尾，以保留原始字节及记录的SHA256，不将原始日志CRLF误报为源码尾空格；不改变生产代码或仓库全局属性。受验源码哈希仍指实际Windows工作区字节，受验父HEAD与实际工作区差异分列。

## 平台 / Contract 预检查

起始业务仓提交53a3ae83256aeb6ee8b95f426fb6d7297493b65c；当轮实际fetch核到origin/main为092604639cd5b2b61fef1523f87fcd711d8aefea且为祖先，origin为adgo07/GHGTOOL，沿用既有codex/ui-business-layout。中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20，Architecture V2.1分层、展示不回流、Presentation State与正式Record隔离约束保持；当前UI指南v0.2为ACTIVE指南，不升级Frozen基线。无Contract冲突或中央改动。本任务不涉及中央公共 Contract。相关既有Standard Issue004/016/018、017、020；不改变既有软件解释，没有新增标准问题。

## 六项首轮问题

完整命令为`python -B -m unittest discover -s tests -t . -v`。`full-tests.log`实际1071项、3失败3错误、1065通过、2994.432秒；`initial-failures.txt`保留原始堆栈。

| 首轮问题 | 判断与处理 | 定向证据及边界 |
|---|---|---|
| P3DF查旧body_layout直属result索引 | V2公共区持有结果与依据。检查唯一公共区在正文、来源目录外、相同父容器、结果先于依据，保留标准标题换行断言 | `updated-layout-tests.log`，12/12，23.321秒；不合并为全量结果 |
| StandardInputPolicy固定3行 | V2响应重排的旧几何假设。保留原Canonical选项/名称/别名/来源资格，检查原对象与宽窄布局无缺项重复 | 同上 |
| UAT03旧独立pressure单位标签 | 单位已并入可见标题，验证完整“蒸汽压力（MPa，绝压）”；其他焓方式/适用/单位断言保留 | 同上 |
| UAT02删20动态行后立即比较高度 | 正常事件后确会收缩，改2秒真实截止、至少8轮观测且连续3轮稳定，不强制activate/产品refresh；严格保留高度/scroll max下降、剩余身份，并新增行/控件边界和Qt异常检查 | `geometry-current.json`/`geometry-main.json`及探针；`twenty-rows-updated.log`保留新增边界发现的真实缺陷，不伪作通过 |
| ChineseUi modal子进程45秒超时 | 未改对话框或阈值。原包装器隔离1/1通过3.805秒；最终候选按原child命令又保全stdout/stderr，12.485秒通过 | `modal-isolated.log`、`exact-children/`；只能称隔离未复现，不能断言原因或根治 |
| UIR04 scale子进程60秒超时 | 未改脚本、阈值或工作流。原包装器隔离1/1通过94.690秒；最终候选每子进程原60秒限制，1.0/1.25/1.5分别52.797/39.484/44.813秒通过 | `scale-test-isolated.log`、`exact-children/`；完整稳定套件结果须另列 |

同1280窗口、运行时、字体及数据的自然几何对照：当前目录占用后编辑器宽674，main编辑器宽862，不能称等编辑宽度性能对比。current grown12263/max11463→shrunk11736/max10936；main6837/max6037→6573/max5773。行在host内、满足minimumSizeHint且无重叠、身份不变、回调异常0。current原测试在收缩后第一轮正常事件已观测到正确外层尺寸。

## 真实展示缺陷与限定修复

增强控件边界断言发现`fuelLhvSource1`等原始combo被`_refresh_fuel_row`重新显示，其geometry超出SegmentedChoiceControl父容器。这四个原始combo仍是数据与信号对象，交互由可见单选按钮提供。

生产只增加`_set_fuel_source_visibility`及四处调用：确认父为SegmentedChoiceControl且父.combo是原对象时，保持内部combo隐藏；未包装combo仍遵循原visible逻辑。真实来源按钮、原combo身份/itemData/信号、policy资格、参数值、报告、来源草稿均保留。不改变算法、Canonical、数据库或Record。

- `fuel-adapter-fix-tests.log`：16/16，121.164秒，受影响测试；执行时为四个已包装combo直接hide的中间修复，之后改为所有权guard，不能称最终guard全覆盖。
- `fuel-proxy-policy-wide-narrow.log`：最终guard下1/1，32.511秒；四来源真实按钮、缺省/实测、仅DIRECT合法计算、禁用按钮不能选、原对象同步、精度草稿、输入与报告入口、宽窄往返、原未包装combo兼容、浏览保值与零Record。与16项有重复，不累加。
- `fuel-capture/`：从最终候选完整42张真实Qt图中归档5张受影响燃料图；`summary.json`记录整个捕获流程及7个UI源/脚本哈希，捕获父HEAD仍53a，实际工作区源码以哈希为准，不能把父HEAD写成无改动受验提交。完整42图暂存build诊断目录。失败0Record、后续成功恰好1Record、输入改后Word出口禁用、回调异常0。预期校验错误见capture日志。

## 最终稳定全套

astra受影响范围独立视觉复核PASS：逐张检查上述5张燃料图，7/7 UI源哈希与现场文件匹配，其中page为bb1208c2a829e3715423440d0bdfe0da7124fe3e4e9fbac37fb04ebad421612e。来源按钮与报告在宽窄布局可读完整，没有原combo残影或重叠；只证明这5图，不覆盖旧151或旧42图的源身份。DIRECT未参与热参数在5图中均为收起态，展开态另补，不能先宣称已视觉验过。

随后补`22-direct-expanded-1680.png`及`22-direct-expanded-1180.png`，astra实际查看两图也给出局部PASS，并现场核page哈希一致。LHV/FCh标签、单位、数值和灰化来源完整可读；展开区位于当前参数组/报告下、添加燃料上，宽窄无裁切或重叠。该结论补足展开内部，本轮视觉范围累计7张燃料图。`expanded-summary.json`的代理可见禁用、raw combo隐藏、可见控件父内边界、resize保值、零Record和异常零，是捕获脚本的自动守卫，不描述为astra亲自执行功能测试。

最终代码/测试冻结后实际执行一次完整discover：1072项，1070通过、1失败1错误，3021.448秒，未列跳过。`final-full-tests.log`与`final-discover-identity.json`完整保全，开始/结束文件哈希无变化；运行器3104.688秒含进程退出，不混同测试耗时。不能以旧151、12、16或单项通过代替完整结果。

新增失败为我方将main对照源码副本放在工作树build目录，Numeric原全仓rglob扫描把副本内的测试与decimal_policy计为生产命中。已核实源/目标实际路径均在获准workspace，将该副本完整移到工作树外临时落点，原ZIP与对照证据保留；不改Numeric测试或规则。原用例`test_tolerance_taxonomy_is_test_only_for_confirmed_is_close_call`重跑1/1通过4.157秒，见`numeric-scan-clean.log`。当前代码没有Numeric业务缺陷；此项属于诊断落点污染，原失败不删除。

仍OPEN：scale1.0子进程在最终完整套件再次超原60秒。`trace_scale.py`只添加每10秒faulthandler采样，60秒不变，诊断执行38.968秒退出0；10秒栈位于页面输入构建、20/30秒在动态物料layout.addWidget，未见模态等待。`scale-trace.*`是另一次诊断运行，不能冒称取得失败子进程栈，也不能确定两次完整超时根因或以隔离通过替代全量。原UIR04测试、脚本、超时和CI工作流均未修改，没有第三次机械完整重跑。

最终全套中的14项来源目录、严格20行增删、结果公共区、Canonical选项/别名、热力单位标题和45秒模态通过。最终compileall和diff --check退出0。发布状态HOLD：不push/PR/CI/当前head实包，等待门禁决定或明确的专项定位方案；完整BLOCKED说明见根IMPLEMENTATION_REPORT.md。

本地Python3.12.14、Qt6.11.2、offscreen、合成输入及隔离临时数据库；早期53a的canonical 9标准/12来源/102参数/138因子、编译、pip check、隔离数据库重建、5个UI场景、1.25/1.5离屏缩放均通过，日志本目录保留，不改标为当前head CI。脚本文件名包含manual不代表执行了原生人工测试。

未执行：GitHub Actions、当前head standalone实包、原生桌面/鼠标/IME/系统DPI、Office与企业真实样例。不改变标准支持状态，不自动合并。独立复核与CI结果须按实际身份单独记录。
