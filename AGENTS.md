# AGENTS.md

## 项目名称与当前目标

本仓库当前只开发“青舟温室气体排放核算软件”Windows V1。

第一条完整业务链只实现：

- GB/T 32150—2025 通用规则；
- GB/T 32151.34—2024 炭素材料生产企业核算模块。

其余七项计划标准本阶段只允许建立标准目录和状态信息，不得实现、猜测或复用计算规则。

## 模型分工

本项目采用“Sol 决策与验收，Luna Max 实施”的分工。

Luna Max 必须以根目录 `HANDOFF.md` 为当前实施基线，按其中阶段顺序逐个 Goal 执行。一个阶段只能建立一个 Goal；当前阶段未完成、未提交实施报告或存在 BLOCKED 时，不得进入下一阶段。

## 开工与恢复检查

每个 Goal 开始前以及任何中断恢复后，必须依次检查：

1. `AGENTS.md`；
2. `HANDOFF.md`；
3. `TASK_STATE.md`；
4. `git status`；
5. `git diff`；
6. 最近 5 个 commit（仓库存在 Git 时）；
7. 当前阶段直接相关的源码、数据和测试；
8. 上一次测试是否真正执行完毕。

以磁盘、Git 和测试结果为准，不得以上一次对话的文字推断完成状态。

## 长期不可偏离规则

- Windows V1 使用 Python、PySide6/Qt Widgets、SQLite，目标为 Windows x64。
- 保持 Presentation、Application、Domain、Infrastructure 分层。
- Domain 不得依赖 PySide6、SQLite、Windows API、页面控件或桌面弹窗。
- UI、计算、校验、数据访问必须分离；数据访问通过 Repository 接口。
- 标准和参数的 Canonical Source 必须是可校验的 JSON/YAML；SQLite 只是 Windows 查询与部署格式。
- 官方标准与参数放入 `catalog.sqlite`，用户设置放入 `user.sqlite`，成功核算记录放入 `records.sqlite`。
- 碳核算 V1 不向用户提供 `.qzproj` 项目文件，不设置项目保存、草稿、审批状态或恢复未计算输入。
- 点击“计算排放量”并通过致命校验后，立即生成一条不可编辑的新核算记录；再次计算不得覆盖旧记录。
- 记录只允许 `COMPLETED` 或 `COMPLETED_WITH_WARNINGS`；致命错误不生成核算记录。
- 删除核算记录必须二次确认并留下审计日志；不得直接修改历史记录。
- Excel 导入只保留禁用入口和占位说明，内部默认不可点击、不可选择。
- 报告与导出、企业档案完善、企业层级、企业真实输入基准和黄金算例暂不实施。
- 标准全文不得复制或打包进软件；“打开标准原文”只能调用官方网址。
- GB/T 32151.34 遇到其他行业活动或上下游运输时只提示需要其他标准，不得猜算、套算或并入当前结果。
- 内部使用十进制高精度计算；中间结果默认不舍入；最终界面默认显示 2 位小数，标准明确要求除外。
- 官方参数、排放因子、标准状态和网址不得凭记忆或搜索摘要录入，必须能追溯到原始来源。
- 不得修改、删除或覆盖 `计算表/` 中的用户参考文件。

## Scope 规则

- MUST：`HANDOFF.md` 当前阶段明确要求的事项。
- MAY：默认不做，只有 `HANDOFF.md` 明确允许时才能实施。
- OUT OF SCOPE：不得实施，包括顺手重构、扩大标准范围、改变计算口径、增加云端服务或新的主要技术栈。

## 停止并上报条件

遇到下列情况，停止相关工作，不得自行作重大决定：

- 文档内部或文档与实际代码存在关键冲突；
- 需要改变数据模型、架构、计算公式、标准解释或阶段范围；
- 原始标准或官方来源无法支持准备录入的值；
- 需要新增一级模块或主要依赖；
- 发现公共接口修改会影响另外两套软件；
- 无法满足当前阶段验收条件；
- 测试证明批准方案存在逻辑错误。

上报格式：

```md
## BLOCKED

问题：
证据：
为什么不能按原方案继续：
可选方案 A：
可选方案 B：
建议：
需要 Sol 决策的具体问题：
```

## 实施纪律

- 小工作包、小测试、小提交。
- 不覆盖用户已有修改，不使用破坏性 Git 操作。
- 每个稳定断点更新 `TASK_STATE.md`。
- 每个阶段完成后生成或更新 `IMPLEMENTATION_REPORT.md`，然后停止并等待 Sol 验收。
- 不得仅写“测试通过”；必须记录命令、通过/失败数量、未执行项和原因。

# Qingzhou Contracts 上位治理

本项目是青舟工业能源软件体系三个业务产品之一，受公共规范权威仓库 `https://github.com/adgo07/Qingzhou-contracts.git` 的上位公共架构与 Contract 治理约束。

1. 当前批准的公共基线只以根目录 `PLATFORM_BASELINE.md` 和 `platform-lock.json` 锁定内容为准。
2. 不得实时采用或自动跟随 `Qingzhou-contracts/main`；中央仓后续变化在本项目显式升级 baseline 前不自动生效。
3. 只有经过显式 baseline 升级、版本/兼容性核对和本项目批准后，新的公共 Contract 才对本项目生效。
4. 普通产品 Bug、单标准公式/解释、业务 UI、产品特有数据库字段及本模块自治问题继续在本仓库解决。
5. 如果发现跨三个产品或跨平台的 Numeric、Unit、Module/Capability、Workspace/Attempt/Record/Result、qzpack、Conformance 等公共 Contract 缺口，不得在本项目永久私自定义同名公共规则。
6. 上述公共缺口应先记录为 RFC Candidate，并按 Qingzhou-contracts 变更流程提交中央仓统一处理；在公共语义未冻结前只允许明确、可逆且不冒充公共规范的本地试验。
7. Qingzhou-contracts 中状态为 `DRAFT / NOT YET RELEASED` 的内容不得在本项目描述成 `FROZEN` 或已发布正式 Contract。
8. 公共 Contract 不得覆盖更具体且有权威依据的标准原文、已批准标准映射、标准专属业务规则和当前业务模块合法自治范围；发生真实冲突时按本仓现有 BLOCKED 流程记录，不得偷偷改掉现有治理。
9. 当前 QZC-A01 接入只建立治理关系和版本锁，不要求重构业务代码、修改计算算法、迁移数据库、抽公共代码或重写 UI。
10. 已发现的本地历史治理文本陈旧或公共 Contract 差距统一记录于 `docs/governance/PLATFORM_ADOPTION_REPORT.md`；该报告本身不授权实施其中的后续迁移。

当前中央基线无正式 Contract release/tag，锁定的是 `Qingzhou-contracts@0cd74d783fa23add6dc881b408a8c8ba8503f8e8` 的 **pre-release / bootstrap baseline**。Architecture `V2.1` 为 **FROZEN**；Numeric、Unit、Module/Capability、Workspace/Attempt/Record/Result 与 qzpack v1 均仍为 **DRAFT**。
