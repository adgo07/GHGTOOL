# PR47收敛第一步实施报告

本轮完成候选业务规则和审阅准备的精简，并修复77b0b77独立验收指出的条件表达缺陷，保持正式软件执行路径不变。未实施B/N，不合并PR，不宣布Mapping最终对齐或新head正式验收PASS。

## 平台 / Contract预检查

实际仓库origin为https://github.com/adgo07/GHGTOOL.git，分支codex/ghg-business-rules-a；fetch成功后的base/main为204dded5d03853617f79a1f05693e89b619df9d1。本轮增量比较对象为历史A head 0f8d514779ef21e42f01af1d1eb8a4579a4cfcd3。最终受验head由本报告提交及PR47评论定位，避免回写SHA产生循环提交。

中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。既有Architecture V2.1、Numeric v1及Profiles v1约束继续适用：分层、共享Calculator/Resolver、lossless Decimal、declared-profile consistency/ambient independence、exact比较、项目与不可变Record分离、历史不漂移；禁止第二算法、显示修约回流、epsilon判定、自动升级Frozen。本任务不涉及中央公共Contract修改，不新增依赖、DB字段或计算语义。原批准V1.2文件保持原字节，SHA256 98abf84ea7f7af3887d60c3c1e128c272d73ccbf73892d76581ad1771bfad876。

Standard Issue：012/C01与013/C02原决定保留；014已获最新Owner软件决定，见HANDOFF，不再列为待Owner选择。该决定尚待并行Mapping任务落地，本步不改变运行解释、不改Mapping或问题台账。来源登记VERIFIED仍不等同软件适用资格。

## 实际删除、保留与新增

| 项目 | 本轮前 | 本轮后 |
|---|---:|---:|
| Industry字段定义 | 120 | 11 |
| Software内部字段镜像 | 333 | 0 |
| 默认字段审阅行 | 1090个条件行 | 11个业务摘要 |
| 操作条目 | 18 | 17 |
| 本次变化条目 | 12 | 8 |
| 两份变化JSON总字节 | 2401303 | 1286750 |
| 两份变化JSON总行 | 57313 | 34170 |
| 审阅工作簿字节 | 397971 | 21134 |

删除442个镜像，JSON减少1114553字节和23143行；不是缩减标准业务覆盖范围。保留11个来源/默认/锁定政策目标、全部41个策略、10条行业规则及adopts；与0f逐对象比较一致，Common包未改。主要体积仍来自严格条件组合，本步不进一步重写规则引擎。

默认review_rows按业务终态展示，不展开每个参数绑定、条件笛卡尔积或内部属性。technical_review_rows保留完整技术矩阵；不同允许来源集合分别分组，精确登记组合只折叠显示数量，不转为宽泛匹配。测试证明默认摘要不调用完整矩阵。新增可选mapping_refs仅作追溯引用，26个引用均存在于当前Mapping，不参与求值；不强制普通内部属性或序列化字段进入业务规则JSON。

工作簿保留三页、筛选、D6冻结、稳定审阅键、意见/状态/编号。意见恢复兼容旧页名；删除定义的意见转入变化页。用户关闭后先备份旧表，旧表哈希5bd80a288f6373b88746dc9995caf1d38e28c286db0a471b8c2bb53d6e3f5cc5、实际已保存意见0条，未丢弃用户意见。验证时的6条QA意见仅用于临时副本，未写入交付表。

最终LF审阅投影SHA256 e346d967f661c9bbf72acb78844d8a6ae15fe76458f8502e2393b5e3b2a9a221；工作簿SHA256 dd8e109120e2f509ae8d1532f85ce48d2b8c81fcc15b3252619de932bf29125c。完整证据见既有evidence/review-artifact-checks.json。

PR45/46盘点只读，按燃料、工艺、烟气焚烧、脱硫、电力、热力、输入/报告等概念列未来唯一执行点和替换对象；50/50改动路径包含关系不等于内容全等，已核对的blob和功能点、未执行的视觉验证均明确标注。没有修改其工作区或PR。

## 实际命令与结果

正式专项使用现有Python3.12环境；Node/Artifact Tool仅开发期产物工具，没有加入运行依赖。

| 命令或检查 | 真实结果 |
|---|---|
| `python -m unittest tests.test_business_rules_candidate tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_assets tests.test_business_rules_excel_evidence tests.test_business_rules_candidate_revisions -q` | 67/67，0失败/错误，5.402s |
| `python -m packages.application.business_rules_candidate --review-json build/business-rules-authoring/review.json <三份固定候选包>` | 成功；11字段/17操作/8变化 |
| `node build/business-rules-authoring/build_business_rules_review.mjs --input build/business-rules-authoring/review.json --output build/business-rules-authoring/compact-review/业务规则审阅表.xlsx --previous build/business-rules-authoring/review-before-shrink.xlsx` | 成功；三页36行，实际旧意见0条；三张渲染已查看 |
| `node build/business-rules-authoring/qa-feedback.mjs` 及同builder读取qa-review/qa-seeded副本 | 6条意见跨三页重排全部原样保留，删除定义1条意见迁入变化页 |
| `python build/business-rules-authoring/verify_review.py` | 0公式/0错误；最长单元格2315字符；意见6/6；当前表无QA意见 |
| Draft202012Validator检查Schema、三个真实JSON与mapping_refs负例 | 3包通过；空/非法/重复引用3负例均拒绝 |
| `python -m compileall -q`（本轮变更Python文件）；`node --check scripts/build_business_rules_review.mjs`；`git diff --check` | 全部成功 |
| Git对象对比及受保护文件检查 | 41策略、rules/adopts完全相同；Common、Mapping、台账、AGENTS、路线、锁文件未改 |
| 独立Luna只读diff审查 | 无所列范围阻断项；未运行测试，不代替最终head验收 |

一次开发命令误用不存在的tests.test_excel_ooxml_numeric：64项中63成功、1导入error；随后使用真实Excel证据模块得到67/67。首次普通fetch因FETCH_HEAD权限不足失败，随后提权成功。此前builder换行语法和摘要对象显示问题已修复，node语法检查及最终渲染通过。失败均不计为通过。

本轮未重跑本地全量回归、Windows构建/发布审计、GUI/DPI或原生Excel/WPS；不冒充原生验证。历史0f8d514的独立A PASS和CI仅作历史，可在PR47既有验收评论定位，不继承为本轮新head结论。新head GitHub Actions状态在PR评论单独记录。

## 治理处理与剩余依赖

自动审批拒绝了同时删除治理规范、改写AGENTS/路线/交接的广泛操作，原因是授权证据不足且可能丢失既有约束；该命令未执行。采用更保守且已成功执行的方案：原治理文件和硬约束保留，仅在现有HANDOFF、TASK_STATE及本报告记录本轮范围，不新增平行规范或路线。

并行Mapping批准是下一步前提：逐参数来源资格/默认/锁定ID尚缺，P04A烟气焚烧不在当前11个政策目标内，不能复用fuel规则；输出电力/热力目前只关联既有RESULT ID，不假称专属因子映射已建立。Issue014产品选择已批准，实施与Mapping对齐仍待后续工作包。当前摘要是现有业务政策的收敛准备，不是全标准来源政策完成声明。

更新原PR47并发送最新head、缩减量、Mapping依赖和实际测试证据到「方案设计」后停止；等待独立检查，不自行开始B/N或合并。

## 77b0b77独立验收退回项：审阅条件表达

根因在生成器：locking只取business_source而丢弃其他条件；数值default提前return而无条件；其他摘要超过6组仅显示计数。修复保持原11个业务目标和机器策略不变，对每种终态附上完整可读条件；若其余标签、范围与精确匹配约束均相同，才沿一个维度并列值，随后提取所有分支共有前提，等价保留原有析取，不把独立组合变成笛卡尔积。未新增规则求值或Markdown运行依赖。

实际G9/G12/G14明确区分已核验绑定与无绑定、实测来源及单/多组分；F列数值默认同样含适用条件。大组保留目录表1～5、供电单位/企业路径、购入/输出、绑定资格等决定条件，不再使用组数和测试替代业务判断。路径中文化；ratio单位列仅显示层改为「比值（0～1）；界面/Excel用百分数（%）」。不修改政策、计算单位、输入或业务口径。

新增2个实际工作簿测试（不是只搜生成器源码）：逐块检查相反结果各自有区分条件及单位；检查default条件和大于6组的电力路径不丢失。单独2/2，0失败/错误，0.296s；最终5模块联合67/67，0失败/错误，5.402s。重新运行生成、三页渲染查看、6/6意见保留、0公式/错误及语法/compile/diff检查成功。本轮原生Office未执行，不把离屏渲染充当原生验证。

独立验收方此前运行在tempfile权限上失败（实际Ran63/errors39，多数setUp）；该结果仅记录环境阻碍，不写成业务失败或对方全过。77b0b77的CI #227属于旧head，新head须另核实。此次修复仅生成器、产物断言、工作簿与证据、既有状态/报告；业务资产、Mapping/台账、生产代码未变。送验后停止，不B/N、不合并。
