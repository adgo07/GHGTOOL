# GHG-RS01-B2 — Multi-entry Business Input Closure

日期：2026-10-03

状态：RS01-B2实现与本地验证完成；PR #24 保持 open，等待独立重新验收。latest-head Windows CI以PR当前checks为准；本报告不把PR head或工作流结果写入同一个会触发CI的提交。

范围：同一核算单元下多过程/多能源来源逐项输入、逐项计算和标准汇总；RS02/RS03/Golden Freeze/第二标准不在本工作包内。

## 1. 基线与治理预检查

- 仓库：`https://github.com/adgo07/GHGTOOL.git`；origin已核验。
- Base / `origin/main`：`24537ba766579db17ef5012151b5cd788724afe9`，已包含PR #23合并结果。
- 分支：`codex/ghg-rs01-b2-multi-entry-closure`，从已同步的最新`origin/main`创建。
- PR：[#24 — GHG-RS01-B2: Multi-entry Business Input Closure](https://github.com/adgo07/GHGTOOL/pull/24)，base `main`，从本包实现提交 `3c826c48870771b222e80245e964d7e77e55784c` 创建；PR当前head及最终exact-head CI以交付回执为准。报告不复制包含本报告的提交SHA，避免自引用。
- `platform-lock.json` SHA-256：`4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D`；locked Central SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`未变。
- 按locked SHA读取Architecture V2.1 FROZEN、Numeric Contract v1 FROZEN和Numeric Profiles v1 FROZEN；读取当前ACTIVE/Evolving UI Guidelines。保持Domain不依赖UI/数据库、既有Decimal Profile/输入快照规则、中文用户提示和内部细节渐进展示。
- 本任务沿用本仓既有Project/Workspace及不可变Record语义；中央Workspace相关DRAFT未作为Frozen Contract采用。本任务不涉及中央公共Contract，不改`platform-lock.json`、`PLATFORM_BASELINE.md`或中央内容。
- `STANDARD_ISSUES_REGISTER.md`已有4条历史RESOLVED问题；未改变既有执行解释，未新增标准问题。

## 2. 实际变更

- `packages/standards/carbon_material.py`：给五类过程实例及脱硫设施保留稳定身份；`CarbonMaterialInput`接受多实例tuple并兼容既有单例构造入口；Calculator逐实例验证/计算并汇总，错误定位到实例，任一致命错误不写成功Record。热力参数依购入/输出方向独立解析。
- `packages/ui/carbon_material_page.py`：新增/删除煅烧、焙烧、石墨化、烟气焚烧和脱硫设施实例；脱硫设施内可逐项添加碳酸盐组分；购入/输出热力与输出电力可逐来源输入和保留适用因子、实测值、来源及结果。输入身份写入既有form state，不更改SQLite schema或Project迁移。
- 多过程和能源行删除、表单恢复及Project保存/重开均保留稳定身份；fingerprint对身份顺序规范化，行排序不造成业务结果变化。旧单例Project及legacy v1 fingerprint可兼容读取；不重算或改写历史正式Record。
- 错误提示保留普通中文并标明对应过程序号和需补字段。首条过程ID与旧单例稳定ID契约一致，新增行使用不复用的序列ID；行ID不出现在普通用户标签。
- 回归变更：`tests/test_g06_carbon_material.py`、`tests/test_g06_page.py`、`tests/test_accounting_projects_ui.py`、`tests/test_uir01_field_semantics.py`。未修改Canonical参考数据或公式。

## 3. 计算与兼容边界

- 复用已有Domain/Calculator公式，不合并不同过程，不将来源平均；每个煅烧、焙烧、石墨化、烟气焚烧、脱硫设施/组分和能源行分别算出结果，再按标准汇总。
- 多输出电力逐行使用自己的适用因子，形成逐行结果与总抵扣值。购入/输出热力分开取值；实测因子优先，无实测值时才采用适用的0.11缺省。热力焓继续使用版本化C.4/C.5 Calculator及既有R6批准的压力键解释。
- 不重写公式、Canonical schema、reference-table架构、GUI整体设计或fingerprint多行模型；不启动Excel、RS02/RS03、Golden Freeze或第二标准。
- Project仅扩展既有form state承载实例/行身份；无破坏性数据库迁移。历史Record的输入、参数和结果仍只读快照，按`test_historical_snapshot_stays_stable_after_catalog_parameter_change`验证不漂移。

## 4. 缺口与Matrix

- B2关闭：GAP-001（购入/输出多热源与逐行因子）、GAP-004（多过程和多来源输入/逐项求和）、GAP-008（剩余B2测试覆盖）、GAP-011（多输出电力来源及逐行因子/结果/汇总）。
- B1已关闭：GAP-002/003/005/006/007/010。共11条登记Gap；10条关闭，唯一开放项GAP-009为非阻塞历史附件provenance debt。类型总量：IMPLEMENTATION_GAP 8、TEST_GAP 1、EVIDENCE_GAP 2、STANDARD_ISSUE 0、CENTRAL_CONTRACT_GAP 0。
- `CORE_CHECK.md`的Standard Completeness Matrix共26行：主状态OK 21、GAP 0、later-stage 5（RS02 3、RS03 1、RS04 1）、独立N/A状态0。closed Gap保留为完成证据；未将报告/Excel/Golden/正式支持等later-stage能力计作当前完成。
- `REFERENCE_STANDARD_ROADMAP.md`、`HANDOFF.md`、`TASK_STATE.md`、`IMPLEMENTATION_REPORT.md`、CORE_CHECK和GAPS已同步B2实施状态。整体参考标准仍为PARTIAL，不宣称正式SUPPORTED。

## 5. 测试与验收

- 定向核心/UI/Workspace/Record测试：80/80通过。
- 全量命令：`python -m unittest discover -s tests -t . -v`；234/234通过，0失败、0错误、0跳过。较B1基线223项增加11项回归。
- Canonical：`python scripts/validate_canonical.py`通过，9 standards、12 sources、98 parameters、98 factors。
- 编译：`python -m compileall -q apps packages scripts tests`通过。
- 依赖：`python -m pip check`通过，No broken requirements found。
- 多行Domain独立计算/求和、UI全部过程来源组装、脱硫多设施/组分、不同热力/电力因子、删除中间行后身份恢复、Project保存重开和旧单例Project/v1 fingerprint兼容均有专门测试。
- 历史Record测试保持通过；四数据库隔离构建与Canonical重建测试在全量回归内通过；UI缩放/无横向滚动验收测试在全量回归内通过。
- `git diff --check`通过；Matrix逐行复核结果为26行、OK 21、GAP 0、later-stage 5、N/A独立状态0。
- GitHub Actions历史核验：初始head `3c826c48870771b222e80245e964d7e77e55784c` 的run #130（ID `37090829842`）Merge-ref Full Tests通过；后续head `be48dc9be90ba7f811e239a44e5ac1ed42060915` 的run #131（ID `37091010125`）两项Windows作业均success。每次新提交都会触发新检查；PR #24当前head的exact-head结果以GitHub PR checks及交付回执为准。

## 6. 后续状态

RS01-B2实现及本地验证已完成；PR #24保持open，等待独立重新验收。提交后须确认PR当前head的两项Windows作业均success；检查结果由PR checks提供，不为记录检查SHA而追加提交。独立验收前不合并PR、不启动RS02/RS03、不冻结Golden、不扩展第二标准。
