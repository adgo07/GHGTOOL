# PR46 第二轮来源与导航修订实施报告（执行中）

2026-10-14。继续原 PR46，不合并。最新 Owner 决定：目录燃料 FCh 默认采用缺省值，但允许按真实填写来源修改；自定义燃料的参数全部由使用者填写。此前“目录 FCh 只能采用缺省”的交接限制已被该直接答复覆盖。

## 平台 / Contract 预检查

实际 origin 为 adgo07/GHGTOOL，分支 codex/ghg-standard-input-unification。重新 fetch 后 origin/main 为 `204dded5d03853617f79a1f05693e89b619df9d1`；本轮起始 head 为 `d36e50c89b87542ab83f63586dd5f6bad243134b`，当前生产修订尚未提交。中央锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，Architecture V2.1 / Numeric v1，当前 ACTIVE UI 指南 v0.2。

适用 MUST：分层、同一正式 Calculator、Decimal40/HALF_UP declared Profile、ambient independence、显示修约不回流、冻结 Record 与来源证据不漂移。MUST NOT：第二套算法、改写历史 Record、修改 Frozen/Profile/数据库结构、来源静默重标。Issue011先登记后实现；本轮为本模块输入来源政策和普通产品缺陷修复，无中央 Contract 冲突或升级，不扩大标准范围。

## 当前实现

逐字段来源政策由 `carbon_material_input_policy.py` 统一提供，GUI、Excel 与 Domain 消费该政策；模板与解析器仍在收口。数值缺省必须来自实际适用的 Catalog / Resolver 绑定，不能由控件或模板硬编码补值。

| 字段 | 当前来源政策 |
| --- | --- |
| 直接单位含碳量 | 实测；计算含碳量仍沿既有热值路径派生 |
| 目录燃料 LHV / FCh | 适用缺省、计算、实测；缺省状态锁定，明确改源后手填 |
| 自定义燃料 LHV / FCh | 使用者按计算或实测来源填写，不套目录缺省 |
| 碳氧化率 | 目录项缺省或实测；自定义仅实测，数值手填 |
| 物料固定碳 / 挥发分 | 实测；基准换算证据仍独立保留 |
| 碳酸盐含量 I | 单组分可用通用缺省90%或实测；多组分仅实测 |
| 碳酸盐因子 EF1 | 精确 C.2 绑定采用目录因子并锁定；未匹配采用手填实测 |
| 转化率 TR | 各组分可用通用缺省100%或实测，与 C.2 物种匹配分开 |

来源切换不把缺省数值直接贴成实测/计算。燃料按字段与来源分别保存草稿，非当前来源草稿也随既有 form_state JSON 保存恢复；不扩展 Canonical 或数据库模型。新增第二组分保留首行原90%草稿并提示确认实测，删除回单不覆盖已确认实测值。旧 STD/CALC/CATALOG/USER_DEFINED 保留原机器码、数值和展示证据，不静默重标；不适用来源在重新正式核算前须确认。

正式校验核对当前 Resolver 的参数身份、单位、完整值及来源元数据，问题定位绑定实际燃料/组分字段。C.2 的显式11项映射只描述标准专属身份，不复制因子数值；CUSTOM/legacy 不因名称看似化学式就自动升级目录身份。Calculator 验证版本已更新，公式、系数和 Numeric Profile 未变。百分比双向转换改为精确移动 Decimal 指数，修复默认 p28 context 截断输入的问题。

来源简写采用共享 formatter，优先已有条款/表号，无定位时显示来源名称；只在展示层去物理/印刷页码，完整 Canonical/Record/tooltip/source_detail 保留。电力短标签去前置表号和冗余尾年，同口径跨年仍明确区分。分段控件首/尾圆角、中缝直边，有焦点与选中对比；唯一合法来源显示只读标签，旧来源保留明确确认入口。

导航采用只读 RecordSummary 与可选摘要查询，不改 Record schema/写入。首页最多3条，记录列表完整可达，详情按需 get；筛选复用摘要，实际变更才刷新，项目关联单独失效，保留选择/搜索/滚动。跨启动、另一 repository 写入、不同时区与同秒微秒排序均有专项检查。

## 当前验证证据

以下为实际已执行的定向检查，不能替代待执行的最终完整回归、构建和 CI。

- `python -m unittest tests.test_pr46_percentage_precision tests.test_pr46_fuel_confirmation tests.test_g06_fgd_ui -q`：23/23，46.617s；后续元数据收口仍需最终回归。
- `python -m unittest tests.test_g06_page tests.test_uat03_formal_workflow -q`：34/34，161.052s。此前同命令30pass/1fail/3error定位到新FGD门禁未定义变量，已修复后复验通过。
- 后端来源/规则/冻结证据初轮组合69项通过；材料/Numeric/canonical项目关联45项通过；严格来源元数据与具体行定位组合当前66项通过，RS02补验进行中。
- 摘要与记录UI组合27项通过；后续摘要排序补验6项通过。来源 formatter / 控件 / Word表式25项通过；目录定向2项通过。
- `validate_canonical.py`：9 standards / 12 sources / 102 parameters / 138 factors；`pip check`：无破损依赖。
- Windows Qt实际windows平台程序驱动100%/125%/150%各12项检查、7张截图；共21张截图。证据在 `docs/ui/standard-input-evidence/source-policy/`，是QTest与QWidget.grab，人工原生鼠标/中文输入验收仍 OPEN。

导航实测使用临时合成200条记录、20个项目，未读写用户数据库。最终after冷点击返回302.465ms、首次绘制317.29ms、缓存重访中位数93.682ms；构造结束仅加载1页。原d36留存摘要冷handler约1045.574ms、缓存重访约657.654ms；原始完整baseline JSON未能恢复，不补造。开发中1103/743ms慢中间版本不是原版基线。完整after JSON、命令及源码SHA在 `docs/ui/standard-input-evidence/navigation/`。

## 尚未闭合

1. Excel v2.2 / v4资源与逐字段导入校验、旧模板身份/证据兼容、精确打包白名单。
2. 新资源的WPS原生TEMP副本保存回导；不得用程序重存冒充。
3. 最终稳定源码的完整回归、Windows本地构建/审计/隔离启动，以及GitHub Actions最终head CI。
4. 最终实际diff/head的独立AI验收，更新原PR46并交用户实际操作验收；不自行合并。

上一轮 d36 CI222 / 561项通过只证明此前基线，不作为本轮通过证据。原主目录的用户修改、批准原始母版与历史受控模板文件不覆盖。
