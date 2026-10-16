# PR47 合并前有限小修实施报告

更新时间：2026-10-17。当前工作包是原 PR47 的有限收尾，不另开规范或 PR，不接生产、不启动 PR46 / B / N。历史 R9/R10 过程由 Git history 恢复，本报告只表达当前有效交付。

## 平台 / Contract 预检查

- 实际 origin：`https://github.com/adgo07/GHGTOOL.git`；分支 `codex/ghg-business-rules-a`；开工修复基线 `4e7306992335e213fc0c3baf897022dd174e3acf`；已 fetch 的 main 为 `b0c1aa723391772f9aef026b4c0a8619eb61a65b`。最终受验 head 及对应 CI 由本 PR 最终送验评论定位，旧 CI 237 不为新 head 背书。
- 中央 locked SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 未修改。本任务不涉及中央公共 Contract；既有 Frozen 分层、声明 Numeric Profile、ambient independence、exact comparison、显示修约不回流、可变 Project 与不可变 Record 分离及历史不漂移约束继续适用，无新中央冲突或 adoption。
- Standard Issue：没有新建、关闭或重释条目。本次不修改 Mapping、标准事实或正式软件解释。014/018/019/020 的已批准决定继续有效；019 的软件决定不表述为官方勘误。

## 本次修改及范围

1. **基线和候选身份。** 两份 JSON 共修改 2 个 `base`、11 个字段 `basis` 人读说明。递归比较已确认没有其他 JSON 叶值变化；R8 是已合并历史基线，当前 R11 含有效批准的软件决定；CANDIDATE 仅表示执行接入尚未完成。未改允许来源、条件、绑定、锁定、公式或适用范围。
2. **审阅范围。** 在现有 `STANDARD_SEMANTICS_POLICY.md` 第7节登记 Owner 简化决定取代原 V1.2 第11节的全字段可见性盘点，原批准文件字节不变。纯导航、折叠和 advanced 展示不作为业务来源规则；业务适用条件仍由 Mapping / 策略约束。现有 HTML 范围说明引用该段，不恢复 GUI 镜像。
3. **当前状态。** 重写 `TASK_STATE.md` 和 `HANDOFF.md`，删除层叠旧覆盖段，保留当前有效产品、PF01、Project / Record、EXB01 等边界。原审阅表 Office 检查延期与 EXB01 原生保存回导未验证是两件事，不互相豁免。最终检查又校正 HANDOFF §3.7 的旧蒸汽表措辞，定向引用 Mapping §9.7 / 017：后续新自动焓采用 iapws.IAPWS97，C.4/C.5仅历史且不回退，生产接入待PR46，合法独立已知焓保留；不改变该专业决定或生产。
4. **检查复现。** 将被忽略目录里的必要审阅检查收拢为 `scripts/business_rules_review_checks.py`，复用现有 Python/openpyxl 读取与定义哈希检查，提供 root/stage/input/output/previous 参数，不新增生产依赖、检查框架或 CI Node 安装。`PREFLIGHT.md` 给出从干净 checkout 生成投影、工作簿、夹具和 checks 的命令。
5. **原有接口。** `review_mode=compact_business_v2` 与 `manifest.view_revision=compact-business-v2` 保留为既有序列化命名别名；详情定位仍是文本路径与锚点。程序统计实际意见行数，不把0写死；意见内容、身份、条件与跨版本复核由既有25场景 JavaScript 夹具验证。

检查工具验证实际投影、技术输入、HTML详情、工作簿、manifest、目录快照和夹具绑定。独立复核发现初稿缺少对混源 HTML 的拒绝，已完成修正，并以错误 HTML 投影、详情摘要及意见范围的负向测试验证拒绝；不使用修正前结果作为最终完整绑定证据。

正式四件套在忽略目录临时生成；正式原表已独占核验、原样备份，确认已保存意见为0，再更新原交付位置。不修改用户附件、原 V1.2 批准全文或固定历史 `electricity-paths.json`。61行仍为29/21/11，649技术组合仍为281 READY / 368 BLOCKED，442个条件意见作用域保留；当前检查与候选不成为第二套业务真值源。

## 验证与证据来源

以下本地100/20/25与四件套检查对应047210f的代码和产物；后续只同步HANDOFF/TASK_STATE/本报告的017既有决定文案，未重复本地业务测试。该文档补丁运行git diff --check及独立只读复核；新 head 的 GitHub Actions 另在原 PR 最终送验评论记录，不将其写成本地执行。

- `python scripts/validate_business_rules_candidate.py --review-json ... --technical-review-json ... --catalog-snapshot ... --catalog-source data-source/carbon_accounting/catalog.json <三份候选JSON>`：成功生成当前同源投影、技术详情和目录快照，exit 0。
- `node scripts/build_business_rules_review.mjs --input ... --details ... --catalog-snapshot ... --output ... --previous <备份原表> --node-modules <bundled路径> --definition-root . --python <Python3.12>`：成功，3 Sheet / 61行 / retained_feedback 0；现有 ArtifactTool 渲染视检，布局未变。
- `node scripts/test_business_rules_review.mjs --builder scripts/build_business_rules_review.mjs --input ... --technical-input ... --node-modules <bundled路径> --output ...`：25/25 PASS（23主场景+2方向隔离），6次实际 HTML 条件输入；这是本地 bundled ArtifactTool 验证，不是 Windows CI 或原生 Office 验证。
- `python scripts/business_rules_review_checks.py --root . --stage ... --review-json ... --technical-json ... --fixture ... --output ... --previous <备份原表>`：PASS；61行、649组合、442唯一范围、意见0/0/0，同源绑定通过。
- `python scripts/business_rules_review_hashes.py --root . --checks <stage>/review-view-manifest.json`：4/4 定义资产 LF 哈希通过。
- `GHG_BUSINESS_RULES_REVIEW_ARTIFACT_DIR=<stage>; python -m unittest tests.test_business_rules_candidate tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_assets tests.test_business_rules_excel_evidence tests.test_business_rules_candidate_revisions tests.test_business_rules_r8_operations tests.test_pr48_mapping_arithmetic -v`：最终100/100通过，0 failure、0 error，20.402秒；新增 Python CLI 无 Node 测试覆盖嵌套临时输出、意见保留及混源拒绝。
- `python -m unittest tests.test_business_rules_candidate_assets -q`（正式交付路径）：最终20/20通过，0 failure、0 error，14.136秒。
- `git diff --check`：通过；仅 Git 的 CRLF 标准化提示。独立 Luna/max 依据实际 diff 和最终工具静态复核，确认混源 HTML 缺口关闭、无剩余阻断；独立代理没有另跑测试。

当前正式投影 LF SHA256：`df5a801fb23f504fe0b2c5cf84c579139f8a6c2f7b2624853e47a7b456880b37`。正式四件套 SHA256：XLSX `f85f2bd7e2351cf53af5f9af619054e803682e7f8a41ad7ebd76409ecf769e6a`；HTML `05c7f43545c50eb468b2bef477d23550148b9d9a991ab6e7aed2b7fb63400b1b`；checks `948f77f4d8605129a6f70752c1304a0377c4ae174ec735f1cf96da2b43e51d7e`；fixture `86119775c215eb6290b81b909aa68b0c710c25e1fefc3e52965aa4990ef2c313`。精确 head 与新 CI 由最终送验评论记录。

## 未执行与停止边界

- 审阅表原生 Excel / WPS 副本打开、填写意见、表头排序、保存重开及回收：**NOT_RUN / DEFERRED**。Owner 已允许延至下一阶段首次正式使用审阅表之前；不是 PASS 或豁免。CU Esc 仍有效，本次不启动电脑操作，不以程序重存冒充原生操作。
- EXB01 输入 Adapter 原生保存回导仍单独未验证；实际 DOCX 和生产消费者替换不在本包。
- 本地没有重跑全软件/完整独立构建；新 head 的 Windows CI 实际结果独立报告。未改 Calculator、Numeric、数据库/迁移、Catalog、正式输入模板、生产 GUI / Word、历史 Record 或中央锁定。
- 执行代理不合并 PR47。完成后交源会话最终独立验收及合并决定，停止本任务。
