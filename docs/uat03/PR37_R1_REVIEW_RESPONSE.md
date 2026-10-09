# PR #37 — UAT03 V2 验收 BLOCKED 定点整改说明

状态：**执行方核查与回归补强；不是独立验收 PASS；PR 不合并。**  
原验收 head：fa04450c9e0836637e997987082207cb6d6a951d  
Base：ff15061d2d765dbff869a0b182af4432d09398bc  
中央 lock：Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20（Architecture V2.1 / Numeric v1 FROZEN；Unit / Record 等仍 DRAFT；不升级）。

## 1. 绿电证明门禁：按用户明确产品决定保留“无需上传”

登记依据：标准问题 GHG-STD-32151-34-007。**软件不强制上传或核验证明，不代表 GB/T 32151.34 附录 D 取消支撑资料要求。** 不应恢复旧 CAR-VAL-GREEN-ELECTRICITY-EVIDENCE 阻断码。

原 G05 的 GEN-VAL-NONFOSSIL-EVIDENCE 分支与 _has_nonfossil_proof 已从 parameter_resolution.py 同时删除。carbon_material.py 原 _map_electricity_resolution_problems 只是把该 G05 码映射成 G06 码，既然不再存在证明前置错误，删除映射是有意行为，不是“改成通用 G05 错误”。

剩余严格规则：必须存在独立、适用、有正式目录来源的非化石电力零因子；缺少因子则仍 ERROR，不得回退全国/省级普通电力因子。既有 proof_type/proof_status 字段保留，避免破坏历史项目兼容。

已有 tests/test_uat03_rules.py 测试“有绿证类型但未提供证明”，本轮新增“proof_type=NONE、proof_status=NOT_PROVIDED”的 Resolver→正式 Calculator 直接回归，验证零因子快照、零排放、无旧证明阻断错误码，以及当前 G06.2 版本。

## 2. G06.1 → G06.2 算法版本确有业务理由

GB/T 公式和 Numeric Conformance 期望值没有变化，但本轮正式业务规则改变：绿电取消证明前置门禁；增加按地区准确匹配省级电力因子；增加普通购入电力用户手填因子与来源快照。这些会影响能否计算、参数选择、结果或 warning，因此 G06.2 是**计算规则/决议口径版本**，不是声称 Decimal 算法变更。

新正式 Record 带 CAR-SM01-2026-10-09-G06.2-N01C-R1.1；旧 Record 原有版本与快照绝不可重写。carbon_material.py、_numeric_authority.py 与 N01-C vector 中同步的版本字段必须一致；Numeric p40/HALF_UP 和公式向量期望值不变。

## 3. parameter_resolution.py 被删除的 35 行是什么

根据 PR #37 实际 diff 分类：

- 原 Factor 类型/快照字段赋值改为适配 USER_PROVIDED 的条件赋值；普通目录因子保留原有身份与来源。
- 全国电力参数无条件返回变为“选地区走省级、未选地区走全国”，对应 GHG-STD-32151-34-008。
- 删除 _has_nonfossil_proof 与证明资料 ERROR 分支，对应 Issue -007。
- 非化石零因子错误文案、软件决定标注与规则说明同步调整。
- GEN-RULE-ELECTRICITY-001 增加省级参数 ID；**没有删除通用 Resolver 的 rule/priority 排序实现**。

相应新增分支必须保持：FactorApplicability 精确地区绑定，地区无候选不能静默回退；用户手填必须经过 Decimal、单位及非负检查，标为 MANUAL_OVERRIDE 且 factor_id/source_id 不伪造为目录来源。catalog/manual 两条路径互斥。回归入口：tests/test_uat03_rules.py、tests/test_uat03_formal_workflow.py、tests/test_g05_rules.py、tests/test_g05_multi_electricity.py。

## 4. 其余四处高风险链路核实

| 代码 | 当前增量性质 | 复验重点 |
|---|---|---|
| project_workspaces.py + projects_repository.py | 仅新增可选“已保存项目更新时间”查询；读取已有 updated_at，不加 migration，不修改 save/Record 关联 | 老项目读取、旧仓储 test double、失败恢复，test_project_workspaces / test_accounting_projects_ui |
| canonical_input_codec.py | 新字段 region、selected_factor_id、factor_selection_reason、factor_override 对旧 JSON 缺失时补 None；未知字段继续拒绝 | test_pre_region_saved_inputs_decode_with_region_unset；原项目可恢复 |
| carbon_material_page.py + responsive_fields.py | 页面正式核算调用 self.calculation_use_case.calculate(self._input())；响应式模块只使用 Qt layout 重排字段 | 不允许 UI 第二套计算；UAT03 formal/page/responsive、UIR 回归和真实 Windows 交互 |
| carbon_accounting.py | CarbonAccountingUseCase 继续使用一个 Calculator；成功才 create_with_details 追加 Record | 致命失败不写记录；历史 Record 不漂移 |

其他增量：enterprise_history.py 仅读企业名历史；uat03_parameter_queries.py 按已核验目录绑定并委托现有 Resolver；Word report_export.py 仅消费已保存 Record，输入发生变化后必须禁用过期导出。检查 tests/test_uat03_report.py、test_uat03_formal_workflow.py。

## 5. PR #37 的多主题归属（45 个文件）

- 页面布局/操作：carbon_material_page.py、responsive_fields.py、test_g06_page、test_uat03_page、test_uat02_*、test_uir0*、scripts/uir04_*。
- 参数规则/来源：parameter_resolution.py、carbon_accounting.py、uat03_parameter_queries.py、carbon_material.py、test_g05_*、test_g06_carbon_material、test_uat03_rules。
- 旧项目/Record：canonical_input_codec.py、project_workspaces.py、projects_repository.py、test_project_workspaces、test_accounting_projects_ui、test_rs03_excel_entrypoints。
- Word/历史：report_export.py、pages.py、enterprise_history.py、test_uat03_report、test_uat03_formal_workflow、test_main_integration_ui。
- 版本与治理：_numeric_authority.py、N01-C vector、HANDOFF、TASK_STATE、IMPLEMENTATION_REPORT、Roadmap、STANDARD_ISSUES_REGISTER、报告架构和 Schema、UAT03 方案与验收清单。

该分类用于帮助独立验收，不建议破坏性拆分已形成的相关工作包。今后继续小 PR。

## 6. 执行证据与待独立复验

用户提供的原 final-head CI：run 37891240721，成功；此前第三方本机只覆盖 4 个 UAT03 模块 36/36，其余文件未完成实质审查，BLOCKED 是**验收未完成**而非已证明生产缺陷。

本次通过 GitHub connector 在同一 PR 新增定点绿电回归和本说明，**没有修改正式 Calculator、Numeric Contract 或冻结 Mapping**。本环境无法联网 git clone，远程 Desktop Commander 离线；本次**未执行本地 Python/Qt 测试**，不能写成本地 PASS。新增提交后的 GitHub Actions 要另行检查。

独立验收仍需补齐原 skipped 文件审查、旧项目/正式记录兼容、Resolver 行为、绿色电力无证明但有合法零因子、项目/Word 数据闭环、Windows GUI 实际操作，最终以新 head 和真实 CI 判 PASS/FAIL/BLOCKED。**禁止自行合并。**
