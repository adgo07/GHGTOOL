# PR50 B-FGD定向退修实施报告

更新：2026-10-18。F01—F03退修本地实现与验证完成，送固定提交CI/实包及源独立复验；尚未签发本轮最终验收结论，不合并。原a683技术PASS仅限原已检覆盖；旧B.7版本修复及其CI262/实包事实保留，不为旧7b重建。完整历史实现/失败过程可由Git与PR50恢复。

## 平台 / Contract 预检查

实际工作树origin为adgo07/GHGTOOL，fetch后main仍1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e，本轮开工head为a6830e98f3e41f8748dfd86bfcefa58603fab150。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；沿用已读Architecture V2.1、Numeric v1/Profiles v1及当前ACTIVE UI v0.2。MUST：分层/共享内核、declared-profile consistency、ambient independence、full-value exact、历史不漂移。MUST NOT：业务epsilon、显示回流、复制算法、自动升级Frozen、Qt状态充当公共Workspace。p40/HALF_UP为ALLOWED PROJECT DIFFERENCE。

本轮仅修UI/Excel消费者的输入保留与Presentation恢复，无中央Contract冲突/变更，不改公式/来源集合/Calculator/codec/DB/模板/规则资源，不新增设施数据库。相关Standard Issue016；未产生新的标准歧义或软件解释。根用户文件、M/F工作树未改，未CU/不扩其他包。

## 真实复现与修复

已完整读取外部`PR50_独立验收报告_7b43c23.md`，在a683真实offscreen Qt、ExcelAdapter、Application及SQLite重新验证，不把其原隔离探针冒充整链。仓内原始结果见[PR50_FGD_A683_REPRO.json](docs/ci/PR50_FGD_A683_REPRO.json)。

| 问题 | a683实际结果 | 定向修复 |
|---|---|---|
| F01 | 界面2批→Canonical1批，实际正式1Record，GUI显示完成 | 完全未触占位可忽略；批次名称/用量或组分已有业务输入必须保留，空组分批次交Domain致命校验，零Record；名称/数量原输入保留 |
| F02 | 真实v8改C4/I4但无参数仍预览可算，Canonical1组分，正式1Record | 与受控母版完整C/I静态单元格比较（含第二空组的默认类型），编辑身份计业务行；静态占位不计，0/只选来源/只填值仍计；共享Resolver/求值器重新判单/多组分资格 |
| F03 | 真实保存→关闭窗口→新窗口/新服务打开，ID保留但findData=-1、显示空、Canonical名称None | 既有form_state补存设施显示名，先恢复全部稳定ID/名称、去重候选，再按ID选择；未知旧保存关系保留并提示，不选首项。升级/共享设施/删除前批/草稿/取消均保护 |

F01补齐第二批后11.88，未完输入SQLite保存/新窗口重开仍阻断；命名0但无组分仍阻断，补齐合法0批后总3.96。F02未完Canonical即使直接传Application也失败、零Record，GUI等价行同样阻断；补齐混合组分后2.8174，零组分份额与转化率保留实测、结果1.76；两独立批次同设施各自90%不跨批加百分比，总11.88。F03同设施两批真实新窗恢复后总9.9，来源切换草稿75保留；删除非首前批后其后批仍保留原设施关系。原Record始终不回填/重算。

## 本地验证与失败边界

新增10个`tests/test_b_fgd_acceptance_fixes.py`方法，覆盖F01三项、F02三项、F03四项；重点为正式零Record后补齐合法总量及真正关闭/新建窗口和服务，而非同页restore。

- a683首次实际运行14项、87.790s、3FAIL：前三项真实缺陷；额外11项为误直接导入TestCase导致发现原整链类，已改模块别名，原3失败证据保留。
- 首轮三反例修后3/3、21.717s；随后补受控母版第二空组静态类型保护。
- 边界/旧B.7/原整链联合28/28、229.747s。
- 受影响联合126/126、355.499s，0FAIL/0ERROR；日志`tmp/fgd-final-evidence/retake-affected-joint.log`：

```text
python -B -m unittest tests.test_b_fgd_acceptance_fixes tests.test_b_fgd_legacy_templates tests.test_g06_fgd_ui tests.test_accounting_projects_ui tests.test_exb01_ingress tests.test_main_integration_excel tests.test_business_rules_candidate_assets tests.test_pr46_parameter_source_policy tests.test_exb01_rpt02_integration -v
```

最后只增强F02测试，向Application实际提交保留的不完整Canonical，针对性1/1、8.586s：formal_success=False、零Record；补齐2.8174成功。生产代码与126组完全一致，不把重叠测试相加。固定受验CI/实际包身份与结果见[仓内摘要](docs/ci/PR50_FGD_RETAKE_SUMMARY.json)及[PR50](https://github.com/adgo07/GHGTOOL/pull/50)；摘要引用固定受验提交，不引用其自身head来制造循环。

## 文档与历史证据

CI252无运行时消费者、旧路径引用或目录扫描依赖，已100%原字节迁至[docs/ci/CI252_SUMMARY.json](docs/ci/CI252_SUMMARY.json)，SHA256保持92d63cff11f5ecbf9ec002f0a5fad7646197c9d72b7fe267794a338630858f17；只背书原PR49阶段d5205f5，不改历史身份/数字，不作为本轮PR50结果。HANDOFF/DELIVERY引用均已更新，仓内保留a683/CI262固定原覆盖摘要。

HANDOFF/DELIVERY明确：旧FGD_V1仍可打开/保存未完成项目，同组归一CAL不同现正式拒绝（10t/20t零新增Record）；10t/10000kg与资料引用差异不误判，同组/独立分组分开，软件不猜统一/拆批；历史Record/Word只读冻结信息，不回填、不重算。原公式/Numeric/来源集合不变。

## 停止边界

固定提交的新CI/下载实包及源复验完成后停止；不合并、不CU、不扩下一包、不删除旧工作树或商业发布。原生Office、真实鼠标/中文IME/人工DPI、企业样例、干净目标机与商业履约持续OPEN/NOT_RUN。本地offscreen与宿主包内代码核验不冒充原生人工验收。
