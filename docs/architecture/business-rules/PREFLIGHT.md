# 业务规则候选审阅工具复现

> 历史开工检查记录于2026-10-15的基线，只作为历史证据；本节给出当前 R11 候选在干净 checkout 中的复现步骤。中央 Frozen baseline 仍以本仓 `platform-lock.json` 锁定的 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 为准，本任务不升级 Contract。

## 当前候选审阅复现

当前PR46整合候选为`candidate-2026-10-17-r11-integration1`，通则固定依赖为`pr46-integration-2026-10-17-g05`。只按既有Issue010对齐两条电力范围，主体R11语义不变；这不是生产共享提供者接管。PR47原`19a9c2b`四件套仍以固定历史提交/原工作树保留，新生成表不能冒称原件。

从 GHGTOOL 仓库根目录打开 Windows PowerShell。候选验证器生成紧凑审阅投影、同源技术详情和只读目录快照；工作簿 builder 消费这些输入并生成审阅表、同源 HTML 详情与 `review-view-manifest.json`；往返夹具按正式投影生成反馈场景；仓内 Python checks 工具核对工作簿结构、意见保留、候选来源及生成器绑定，并检查 HTML 内嵌的投影 SHA、technical semantic SHA 和工作簿 scope 指纹是否与本轮输入一致。

`@oai/artifact-tool` 只用于本地开发工作簿和 JavaScript 往返夹具，不是产品依赖。先调用 `load_workspace_dependencies`，把返回的 Node.js executable、Node.js packages 根目录和 Python executable 粘贴到提示中。builder 的 `--python` 使用该 Python 的标准库折叠技术列；`scripts/business_rules_review_checks.py` 使用现有 `openpyxl` 读取工作簿，不调用 Node，也不新增产品依赖。

```powershell
$work = "build/business-rules-authoring"
$stage = "$work/r11-review"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$node = Read-Host "粘贴 load_workspace_dependencies 返回的 Node.js executable 路径"
$nodeModules = Read-Host "粘贴 load_workspace_dependencies 返回的 Node.js packages 路径"
$python = Read-Host "粘贴 load_workspace_dependencies 返回的 Python executable 路径"
$previous = Read-Host "如需保留上一版审阅意见，粘贴上一版工作簿路径；没有则留空"

& $python scripts/validate_business_rules_candidate.py `
  --review-json "$work/review-r11.json" `
  --technical-review-json "$work/technical-r11.json" `
  --catalog-snapshot "$work/catalog-r11.json" `
  --catalog-source data-source/carbon_accounting/catalog.json `
  data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json `
  data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json `
  data-source/carbon_accounting/business-rules/software_policy.json
if ($LASTEXITCODE -ne 0) { throw "候选验证或目录快照导出失败：$LASTEXITCODE" }

$builderArgs = @(
  "scripts/build_business_rules_review.mjs",
  "--input", "$work/review-r11.json",
  "--details", "$work/technical-r11.json",
  "--catalog-snapshot", "$work/catalog-r11.json",
  "--output", "$stage/业务规则审阅表.xlsx",
  "--node-modules", $nodeModules,
  "--definition-root", ".",
  "--python", $python
)
if ($previous) { $builderArgs += @("--previous", $previous) }
& $node @builderArgs
if ($LASTEXITCODE -ne 0) { throw "R11 审阅工作簿生成失败：$LASTEXITCODE" }

& $python scripts/business_rules_review_hashes.py `
  --root . `
  --checks "$stage/review-view-manifest.json"
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

$checksArgs = @(
  "scripts/business_rules_review_checks.py",
  "--root", ".",
  "--stage", $stage,
  "--review-json", "$work/review-r11.json",
  "--technical-json", "$work/technical-r11.json",
  "--fixture", "$stage/review-feedback-fixture.json",
  "--output", "$stage/review-artifact-checks.json"
)
if ($previous) { $checksArgs += @("--previous", $previous) }
& $python @checksArgs
if ($LASTEXITCODE -ne 0) { throw "R11 工作簿结构与证据摘要检查失败：$LASTEXITCODE" }

$reviewArtifactDirBefore = $env:GHG_BUSINESS_RULES_REVIEW_ARTIFACT_DIR
try {
  $env:GHG_BUSINESS_RULES_REVIEW_ARTIFACT_DIR = $stage
  & $python -m unittest tests.test_business_rules_candidate_assets -v
  if ($LASTEXITCODE -ne 0) { throw "业务规则候选资产 Python 测试失败：$LASTEXITCODE" }
} finally {
  if ($null -eq $reviewArtifactDirBefore) {
    Remove-Item Env:GHG_BUSINESS_RULES_REVIEW_ARTIFACT_DIR -ErrorAction SilentlyContinue
  } else {
    $env:GHG_BUSINESS_RULES_REVIEW_ARTIFACT_DIR = $reviewArtifactDirBefore
  }
}
```

所有默认生成物都位于被 Git 忽略的 `build/business-rules-authoring/`。Checks CLI 的 `--root`、`--stage`、`--review-json`、`--technical-json`、`--fixture` 和 `--output` 均可传入其他路径；输出目录不存在时会自动建立。若有上一版审阅表，builder 与 checks CLI 都传入同一个 `--previous`，checks 只比较上一版工作簿、生成 manifest 的 `retained_feedback` 与新工作簿实际非空意见行数；意见内容及跨版本关联由 JavaScript 往返夹具验证，不以行数冒充内容核验，也不清空或假设意见为空。复现测试把 `$stage` 设为 `GHG_BUSINESS_RULES_REVIEW_ARTIFACT_DIR`，确保测试读取本轮生成的资产。

`review-view-manifest.json` 的 `view_revision=compact-business-v2` 与 checks 文件的 `review_mode=compact_business_v2` 是各自既有接口中的序列化命名别名。生成器保留这两个字段及原值，不据此改变业务语义。Manifest 的工作簿行数、技术组合数量、目录快照值和意见数量均按本轮实际输入核验；文本资产哈希仅将 CRLF 归一为 LF，工作簿哈希按原始字节计算。

正式投影往返夹具会在报告中记录 `actual_scenario_count`；当前 R11 夹具为25个场景，实际结果以本轮生成的 fixture 报告为准。该 JavaScript 夹具与本地工作簿生成使用 Codex 工作区开发 bundle；GitHub Actions 的 Windows / Python 3.12 工作流运行 Python 测试，不应把它描述为执行了本地 JavaScript 夹具。

原生 Excel/WPS 副本验证目前为 `NOT_RUN` / `DEFERRED`。Owner 允许延至下阶段首次正式使用审阅表前完成；此状态不表示 `PASS` 或豁免，本次不启动 CU。
