> 历史开工检查（2026-10-15原A基线）。保留当时检查与证据，不作当前政策；PR48合并后的本轮Contract/Mapping预检查见现有IMPLEMENTATION_REPORT。原中央锁定未升级。

# 规则统一A包开工与Contract预检查

日期：2026-10-15；仓库身份实核adgo07/GHGTOOL，默认分支main。成功fetch后main为204dded5d03853617f79a1f05693e89b619df9d1。独立工作树由该main创建，分支codex/ghg-business-rules-a。原主checkout为用户工作分支且有Excel及未跟踪资料，未切换、清理或覆盖。首轮非提权fetch因.git只读权限未写FETCH_HEAD，按允许范围重试后成功；这是执行权限问题，不是origin冲突。

PR46经GitHub实时读取：open、未合并，head77d36a155323bc82199cb516c4ac58a2e1c60309。A不并入PR46的生产改动；其字段政策/输入/报告成果是明确后续依赖，只作分层盘点。不把PR46的2.2.0模板/3.0.1布局误写为main当前资源。

已读取AGENTS、唯一路线、TASK_STATE、HANDOFF、标准问题台账、当前行业Mapping、报告架构/Schema、标准能力架构，以及完整批准V1.2（SHA98ABF84EA7F7AF3887D60C3C1E128C272D73CCBF73892D76581AD1771BFAD876）。批准全文已原字节收录；历史§1/§17不是本次检查结论。

中央仓origin已验证adgo07/Qingzhou-contracts，不动其用户修改。按本仓lock ee5feb0cc34dbd99790500fadd0c4c932e202a20读取Architecture V2.1、Numeric v1及Profiles v1；当前已合并ACTIVE读取GUIDE_INDEX、UI指南v0.2、家族规格/验收清单v0.1。v0.1旧UI正文仅历史，不并行当当前依据。没有自动升级lock。

适用MUST：分层与Domain平台独立、现有共享Calculator/Resolver、显式采用固定修订、业务decimal lossless解析、declared-profile consistency/ambient independence、full-value exact比较、项目与冻结Record分离、历史来源和结果不漂移。MUST NOT：binary float权威值、隐式修约/全局epsilon、显示回流、第二套算法、生产空定义降级、标准全文/用户数据打包。Carbon p40/HALF_UP是ALLOWED PROJECT DIFFERENCE而非平台统一默认。

A只增加本模块候选源、加载与审阅工具，不涉及中央公共Contract修改、不实施新Workspace/Record公共格式、不修改DB/公式/Runtime资源或正式产品支持范围。未发现与locked Frozen冲突；无需中央Contract升级。新014为本行业专业适用关系OPEN，仅停受影响企业电力路径资格落地，不阻断A及已核验路径。C01/C02按012/013登记为已批准决定。

A出口：完整消费者与旧路径盘点、字段/条件/操作审阅、候选严格加载与负例证据，提交独立验收后停止。B先燃料完整链、N专项均未开始；不自行合并任何PR。

## 当前候选审阅复现（开发流程）

以下步骤从当前三份候选定义生成投影、生成审阅工作簿和同源详情，并运行基于正式投影的意见往返夹具。命令面向仓库根目录的 Windows PowerShell。生成输出写入忽略目录 `build/`。

`@oai/artifact-tool` 是 JavaScript 审阅工作簿生成与往返夹具使用的开发依赖，来自 Codex 工作区开发 bundle；不是产品运行依赖，不要安装进程序环境或加入 `pyproject.toml`。当前工作区可通过 Codex Desktop 的 `load_workspace_dependencies` 查询 Node.js executable 与 Node.js packages 路径；本次读取到该 bundle 的 package metadata 版本为 `2.8.94`。把返回的本机路径粘贴到变量中，并将 packages 根目录显式传给夹具：

```powershell
$node = Read-Host "粘贴 load_workspace_dependencies 返回的 Node.js executable 路径"
$nodeModules = Read-Host "粘贴 load_workspace_dependencies 返回的 Node.js packages 路径"

python scripts/validate_business_rules_candidate.py --review-json build/review-current.json --technical-review-json build/technical-current.json data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json data-source/carbon_accounting/business-rules/software_policy.json

& $node @(
  "scripts/build_business_rules_review.mjs",
  "--input", "build/review-current.json",
  "--details", "build/technical-current.json",
  "--output", "build/业务规则审阅表.xlsx",
  "--node-modules", $nodeModules,
  "--definition-root", "."
)
if ($LASTEXITCODE -ne 0) { throw "审阅工作簿生成失败：$LASTEXITCODE" }

python scripts/business_rules_review_hashes.py --root . --checks build/review-view-manifest.json
python scripts/business_rules_review_hashes.py --root . --checks docs/architecture/business-rules/evidence/review-artifact-checks.json

& $node @(
  "scripts/test_business_rules_review.mjs",
  "--builder", "scripts/build_business_rules_review.mjs",
  "--input", "build/review-current.json",
  "--technical-input", "build/technical-current.json",
  "--node-modules", $nodeModules,
  "--output", "build/review-feedback-fixture-current.json"
)
if ($LASTEXITCODE -ne 0) { throw "正式投影意见往返夹具失败：$LASTEXITCODE" }

python -m unittest tests.test_business_rules_candidate_assets -v
```

夹具显式读取当前正式投影及同源技术详情，期望正式输入模式产生 **20 个场景**。省略 `--input` 时运行的是 **16 个 synthetic smoke 场景**，不能替代正式投影夹具。缺少 `@oai/artifact-tool` 时，应按脚本提示显式提供该开发 bundle 的 `node_modules` 根目录；不要通过查看 package 内部实现或把它安装为产品依赖来排障。

GitHub Actions 的 Windows / Python 3.12 全量单元测试步骤会运行 `tests.test_business_rules_candidate_assets`。该模块已有审阅表三页结构、表范围和投影内容哈希检查；本次增加的定义资产清单及原始 XLSX 字节哈希断言也随该测试模块进入全量套件。此处没有声称这些新增断言已在当前 head 的 GitHub Actions 上执行。JavaScript 往返夹具使用 Codex 开发 bundle，不是当前 Windows CI 步骤；Python 资产哈希和 XLSX 结构检查仍可由 CI 验证。上述 `review-view-manifest.json` 与正式 checks 对 UTF-8 文本资产仅把 CRLF 换成 LF 后计算 SHA-256，不排序或重排 JSON；XLSX 工作簿 SHA-256 按原始二进制字节计算。
