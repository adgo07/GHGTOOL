> 历史开工检查（2026-10-15原A基线）。保留当时检查与证据，不作当前政策；PR48合并后的本轮Contract/Mapping预检查见现有IMPLEMENTATION_REPORT。原中央锁定未升级。

# 规则统一A包开工与Contract预检查

日期：2026-10-15；仓库身份实核adgo07/GHGTOOL，默认分支main。成功fetch后main为204dded5d03853617f79a1f05693e89b619df9d1。独立工作树由该main创建，分支codex/ghg-business-rules-a。原主checkout为用户工作分支且有Excel及未跟踪资料，未切换、清理或覆盖。首轮非提权fetch因.git只读权限未写FETCH_HEAD，按允许范围重试后成功；这是执行权限问题，不是origin冲突。

PR46经GitHub实时读取：open、未合并，head77d36a155323bc82199cb516c4ac58a2e1c60309。A不并入PR46的生产改动；其字段政策/输入/报告成果是明确后续依赖，只作分层盘点。不把PR46的2.2.0模板/3.0.1布局误写为main当前资源。

已读取AGENTS、唯一路线、TASK_STATE、HANDOFF、标准问题台账、当前行业Mapping、报告架构/Schema、标准能力架构，以及完整批准V1.2（SHA98ABF84EA7F7AF3887D60C3C1E128C272D73CCBF73892D76581AD1771BFAD876）。批准全文已原字节收录；历史§1/§17不是本次检查结论。

中央仓origin已验证adgo07/Qingzhou-contracts，不动其用户修改。按本仓lock ee5feb0cc34dbd99790500fadd0c4c932e202a20读取Architecture V2.1、Numeric v1及Profiles v1；当前已合并ACTIVE读取GUIDE_INDEX、UI指南v0.2、家族规格/验收清单v0.1。v0.1旧UI正文仅历史，不并行当当前依据。没有自动升级lock。

适用MUST：分层与Domain平台独立、现有共享Calculator/Resolver、显式采用固定修订、业务decimal lossless解析、declared-profile consistency/ambient independence、full-value exact比较、项目与冻结Record分离、历史来源和结果不漂移。MUST NOT：binary float权威值、隐式修约/全局epsilon、显示回流、第二套算法、生产空定义降级、标准全文/用户数据打包。Carbon p40/HALF_UP是ALLOWED PROJECT DIFFERENCE而非平台统一默认。

A只增加本模块候选源、加载与审阅工具，不涉及中央公共Contract修改、不实施新Workspace/Record公共格式、不修改DB/公式/Runtime资源或正式产品支持范围。未发现与locked Frozen冲突；无需中央Contract升级。新014为本行业专业适用关系OPEN，仅停受影响企业电力路径资格落地，不阻断A及已核验路径。C01/C02按012/013登记为已批准决定。

A出口：完整消费者与旧路径盘点、字段/条件/操作审阅、候选严格加载与负例证据，提交独立验收后停止。B先燃料完整链、N专项均未开始；不自行合并任何PR。

## 当前候选审阅复现（R11，开发流程）

本节只描述当前 R11 候选的可复现命令；上方 2026-10-15 开工检查及既有证据作为历史保留。命令从仓库根目录的 Windows PowerShell 运行，生成物均写入被 Git 忽略的 `build/business-rules-authoring/`。

先用固定的三份候选定义导出紧凑审阅投影、同源技术详情和独立目录快照。`catalog-snapshot` 是开发审阅用的只读核对结果：验证器按字段的精确绑定从 Canonical `catalog.json` 查询，builder 再消费该快照，并把目录版本、来源哈希、绑定和数值写入 `review-view-manifest.json`；快照不复制到正式资产或生产数据库。

`@oai/artifact-tool` 是 JavaScript 审阅工作簿生成与往返夹具使用的开发依赖，来自 Codex 工作区开发 bundle，不是产品运行依赖。通过 `load_workspace_dependencies` 获取 Node.js executable、Node.js packages 根目录和 Python executable。builder 的 `--python` 只调用现有 Python 运行时的标准库，用于折叠审阅技术列；`audit-r11.py` 读回工作簿时使用工作区 Python bundle 已有的 `openpyxl`。不安装产品依赖。

```powershell
$work = "build/business-rules-authoring"
$stage = "$work/r11-review"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$node = Read-Host "粘贴 load_workspace_dependencies 返回的 Node.js executable 路径"
$nodeModules = Read-Host "粘贴 load_workspace_dependencies 返回的 Node.js packages 路径"
$python = Read-Host "粘贴 load_workspace_dependencies 返回的 Python executable 路径"

& $python scripts/validate_business_rules_candidate.py `
  --review-json "$work/review-r11.json" `
  --technical-review-json "$work/technical-r11.json" `
  --catalog-snapshot "$work/catalog-r11.json" `
  --catalog-source data-source/carbon_accounting/catalog.json `
  data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json `
  data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json `
  data-source/carbon_accounting/business-rules/software_policy.json
if ($LASTEXITCODE -ne 0) { throw "候选验证或目录快照导出失败：$LASTEXITCODE" }

& $node @(
  "scripts/build_business_rules_review.mjs",
  "--input", "$work/review-r11.json",
  "--details", "$work/technical-r11.json",
  "--catalog-snapshot", "$work/catalog-r11.json",
  "--output", "$stage/业务规则审阅表.xlsx",
  "--node-modules", $nodeModules,
  "--definition-root", ".",
  "--python", $python
)
if ($LASTEXITCODE -ne 0) { throw "R11 审阅工作簿生成失败：$LASTEXITCODE" }

& $python scripts/business_rules_review_hashes.py --root . --checks "$stage/review-view-manifest.json"
if ($LASTEXITCODE -ne 0) { throw "R11 投影/资产哈希检查失败：$LASTEXITCODE" }

& $node @(
  "scripts/test_business_rules_review.mjs",
  "--builder", "scripts/build_business_rules_review.mjs",
  "--input", "$work/review-r11.json",
  "--technical-input", "$work/technical-r11.json",
  "--node-modules", $nodeModules,
  "--output", "$stage/review-feedback-fixture.json"
)
if ($LASTEXITCODE -ne 0) { throw "R11 正式投影意见往返夹具失败：$LASTEXITCODE" }

& $python build/business-rules-authoring/audit-r11.py "$stage/review-feedback-fixture.json"
if ($LASTEXITCODE -ne 0) { throw "R11 工作簿结构与证据摘要检查失败：$LASTEXITCODE" }

& $python -m unittest tests.test_business_rules_candidate_assets -v
```

已核实的正式投影夹具报告为 `status=PASS`、`actual_scenario_count=25`，其中主场景 23 项、方向隔离 2 项；本轮新增 5 项可见条件/操作克隆场景，原有 20 项保留。场景数应以运行报告的 `actual_scenario_count` 为准。无正式输入的 synthetic smoke 仅作补充，不能替代此正式投影夹具；本节不固定其场景数。

`audit-r11.py` 位于忽略的 `build/` 目录，只写入该目录下的临时审计摘要。它核对 R11 `manifest.catalog_snapshot` 的三项值、649 个技术组合（281 READY、368 BLOCKED）、442 个唯一条件作用域，以及技术列隐藏/可展开和各对象属性下拉验证。该摘要不覆盖正式审阅资产、状态报告或用户工作簿。

GitHub Actions 的 Windows / Python 3.12 全量单元测试步骤会运行 `tests.test_business_rules_candidate_assets`；本地审阅工作簿生成与 JavaScript 往返夹具使用 Codex 工作区开发 bundle，不声称由当前 CI 执行。`review-view-manifest.json` 对 UTF-8 文本资产仅把 CRLF 归一为 LF 后计算 SHA-256，不重排 JSON；工作簿 SHA-256 按原始二进制字节计算。
