# TASK_STATE

状态：CURRENT STATE；更新2026-10-03。

## 当前工作包与基线

- 仓库：adgo07/GHGTOOL；origin已核对为 https://github.com/adgo07/GHGTOOL.git；本地工作树按用户指定地址执行。
- 工作包：GHG-RS01-B2 — Multi-entry Business Input Closure。
- Base / origin/main：24537ba766579db17ef5012151b5cd788724afe9；该提交包含PR #23合并结果。分支 `codex/ghg-rs01-b2-multi-entry-closure` 从已同步的最新origin/main创建。
- `platform-lock.json` SHA-256：4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D；中央Frozen锁定SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20未变。
- Contract预检查：按locked SHA读取Architecture V2.1 FROZEN、Numeric Contract v1 FROZEN、Numeric Profiles v1 FROZEN；另读取当前ACTIVE/Evolving UI Guidelines。沿用既有本地Project/Workspace与不可变Record规则；不采纳DRAFT Workspace文本为Frozen、不修改中央公共Contract或baseline。本任务不涉及中央公共Contract。
- 相关标准问题：台账已有4条历史RESOLVED解释；本任务未改变其执行口径，也未新增标准问题。
- 预计仅更新业务实现、回归测试和B2要求的治理文档；不改SQLite schema/迁移、platform-lock或PLATFORM_BASELINE；不启动RS02/RS03、Golden Freeze或第二标准。

**B2实现和本地验证完成；PR #24 已创建。初始实现head的Merge-ref Full Tests已通过，PR-head Standalone Audit正在运行；当前治理文档同步后将验证最终latest-head GitHub Actions，再等待独立重新验收。RS01-B2不代表正式SUPPORTED。**

## 已交付范围

- Domain接通同一核算单元多煅烧、焙烧、石墨化、烟气焚烧、脱硫设施/碳酸盐组分以及电热来源；按现有单条公式逐项计算，再按标准汇总，不自动合并、不平均。
- UI/Application提供相应逐项添加/删除、每行适用因子与来源；输入错误定位到过程实例并以中文业务提示显示。购入/输出热力分开按方向解析因子；输出电力逐行保留不同排放因子及抵扣结果。
- Workspace form state保存过程/组分/能源行身份；middle deletion、保存重开及表单恢复不重用或漂移行ID。单条旧Project与legacy v1 fingerprint继续兼容；旧Record不重算、不迁移、不改写。
- 过程实例ID沿用可读稳定序列并保留旧单例Domain aliases；业务fingerprint按身份规范排序，使行重排不导致结果变化或误标旧结果过期。
- Matrix共26行：核心OK 21、GAP 0、later-stage 5（RS02 3、RS03 1、RS04 1）、独立N/A状态0。
- GAPS共11条：001/002/003/004/005/006/007/008/010/011关闭；009仍为非阻塞EVIDENCE_GAP。历史登记类型总量：IMPLEMENTATION_GAP 8、TEST_GAP 1、EVIDENCE_GAP 2、STANDARD_ISSUE 0、CENTRAL_CONTRACT_GAP 0。
- Roadmap/HANDOFF/TASK_STATE/IMPLEMENTATION_REPORT及CORE_CHECK/GAPS已同步当前RS01-B2状态。RS02、RS03、RS04/RS05工作尚未启动。

## 本地验证

- 定向核心/UI/Workspace/Record回归：80/80通过。
- 全量：`python -m unittest discover -s tests -t . -v`；234/234通过，0失败、0错误、0跳过。
- Canonical：`python scripts/validate_canonical.py`通过，9 standards、12 sources、98 parameters、98 factors。
- Compile：`python -m compileall -q apps packages scripts tests`通过。
- Dependencies：`python -m pip check`通过，No broken requirements found。
- `test_historical_snapshot_stays_stable_after_catalog_parameter_change`、旧Project单例/v1 fingerprint、以及多过程/能源来源保存重开专项回归已通过。
- `git diff --check`通过；Matrix逐行主状态计数为26行：OK 21、GAP 0、later-stage 5（RS02 3、RS03 1、RS04 1）、独立N/A 0。
- GitHub Actions：PR #24 初始实现head `3c826c48870771b222e80245e964d7e77e55784c` 对应run #130（run ID `37090829842`）；Merge-ref Full Tests已success，PR-head Standalone Audit仍queued。该head不是最终验证目标，因为本次治理文档同步会更新PR head；最终只以更新后PR最新head SHA对应的两项Windows作业为证。

下一步：提交并推送本次PR跟踪文档更新；等待更新后最新PR head的两项Windows CI成功，再等待独立重新验收。不要合并，不要启动RS02/RS03。
