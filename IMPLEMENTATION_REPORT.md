# GHG-RS01-A-R1 实施报告

状态：**GHG-RS01-A-R1 completed，等待独立重新验收**；日期2026-10-02。只做Evidence Closure & Audit Correction，未重新执行完整RS01-A。

## 1. 起点、交付对象与范围

- 仓库origin实际确认：https://github.com/adgo07/GHGTOOL.git。
- Base：`c8f7a8ce2139e21b239ce54fac6cbbb9c25aae72`；PR #22实际base及origin/main一致。
- R1起始head：`eb01a35bf085e51a2248dde2920f609ddf203901`；本地与PR远端一致，没有未知跟踪修改。
- 继续分支 `codex/ghg-rs01-a-core-check`，继续[PR #22](https://github.com/adgo07/GHGTOOL/pull/22)，保持open、不合并。
- R1新head为本报告所在交付提交；确切SHA与latest-head CI结果写入PR说明及最终交付回执（以PR实际head为准），避免为自引用SHA/CI反复制造提交。
- 仅修改用户允许的7份Markdown：Mapping、CORE_CHECK、GAPS、STANDARD_ISSUES_REGISTER、REFERENCE_STANDARD_ROADMAP、TASK_STATE、本报告。
- 未修改apps/packages/tests/data-source/migrations/conformance/platform-lock.json；未改业务、算法、参数数据、架构或既有标准执行解释；未启动Excel、RS02/RS03或RS01-B。
- 用户既有未跟踪docs/handoffs/及工业能源架构文档保留、不提交；计算表/未处理。用户R1范围覆盖HANDOFF旧治理任务范围，本轮不扩大修改HANDOFF。

## 2. 专业证据入仓

| 项目 | 实际结果 |
|---|---|
| Mapping源文件 | `GB T 32151.34—2024 炭素材料生产企业映射方案.md`；本次环境来源D:/MD仓库/杂/碳排放计算软件/，只是执行环境 |
| 正式版本/状态 | SM01-2026-09-13-R6 / FROZEN，实际核对正文§1及§17.1 |
| source SHA256 | `01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B`，复制前实际Get-FileHash确认 |
| repo路径 | `specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md` |
| 复制件 | 原样复制，实际SHA256与source相同；未美化/重写冻结内容，R4/R5未替代 |
| 标准PDF | `34.GB_T 32151.34-2024 温室气体排放核算与报告要求 第34部分：炭素材料生产企业.pdf`，43页；仍外置不入Git |
| PDF SHA256 | RS01-A既有核验证据 `60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738`，文件名及PDF/印刷页定位保留CORE_CHECK |

GAP-009中“Mapping不可复核”部分关闭；独立历史批准原件仍缺失，冻结R6、G06 Git最终PASS历史及正式验收记录证明既有口径曾被采用。剩余为provenance debt、业务影响NO，无B阶段业务修改动作，不阻止B，不再次请求确认既有R6口径。未来改变历史解释前才需加强证据或重新获得项目所有者确认。

## 3. 审计修订与治理收口

- CORE_CHECK增加精简Standard Completeness Matrix：25行，OK4 / GAP17 / N/A独立行0 / later-stage4（RS02两行、RS03一行、RS04一行）；列内N/A均有理由。它与原16项核心核对分别计数。
- 16项核心核对修正：OK4 / GAP12 / NEEDS_CONFIRMATION0 / N/A0，输出电力改为GAP。
- 新增GAP-011：表B.8、Mapping §13/TV-CAR-REPORT-003、多行exported_electricity tuple及Calculator逐行能力，与UI _exported_electricity只构造一行的证据对应。只给复用多行能力/逐行适用因子原则，不设计GUI、不重写公式。
- Gap总数11：IMPLEMENTATION8 / TEST1 / EVIDENCE2 / 未解决STANDARD_ISSUE Gap0 / CENTRAL_CONTRACT0。
- 业务影响YES5（001～004、011）、NO6（005～010）、UNKNOWN0；009按用户要求由UNKNOWN改NO，故旧NO5/UNKNOWN1合计不再适用。
- 历史4条Standard Issues正式登记001～004，类型CONFLICT/TYPO/CONFLICT/AMBIGUITY，均RESOLVED，分别区分标准事实、技术判断和项目软件决定；确认程度均非官方勘误/官方解释。它们不计作新增未解决Standard Issue Gap。
- Roadmap记录RS01内部A/B工作包；排放源、活动数据、参数/因子、校验、目录及总量覆盖由无条件DONE改为已有实现+待修Gap；Calculator保留“核心单组公式已实现”，不宣称完整标准支持。
- GAP-008及Minimum Validation补001～004/011、Domain不成记录、UI→Domain一致性及回归最低要求；未新建Test Plan。Golden仅列RS04 CANDIDATE，未冻结。

## 4. 平台 / Contract 预检查

本任务不涉及中央公共Contract。不新增/改变公共语义，不升级baseline；实际platform-lock仍锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。沿用RS01-A已经读取的Architecture V2.1、Numeric v1及Profile v1 Frozen；保持Decimal权威计算、显示修约不回流、历史Record不漂移。4条Standard Issue只登记历史执行决定，没有新增解释选择。CENTRAL_CONTRACT_GAP为0。

## 5. Local验证（本轮实际执行）

| 命令 | 结果 |
|---|---|
| `git diff --check`（工作区及最终暂存差异） | exit0；只允许Markdown文件 |
| `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v` | 214/214，21.451秒，0失败/错误/跳过，exit0；实际等待进程结束 |
| `.venv/Scripts/python.exe scripts/validate_canonical.py` | exit0；9 standards / 12 sources / 7 parameters / 7 factors |
| `Get-FileHash <Mapping源/复制件> -Algorithm SHA256` | 两者完全一致，见§2 |

Qt offscreen、PYTHONDONTWRITEBYTECODE=1，日志忽略目录tmp/rs01-a/r1-full-tests.log。未重跑完整RS01-A专业审计、Domain/GUI探查、独立核心88项、compileall/pip check/四库重建或本地standalone：纯Markdown收口不需要重复上一轮全部工作；CI会执行其规定检查。未添加/修改正式测试，回归通过不表示业务Gap已修复。

## 6. GitHub Actions与停止点

Local与CI严格分开。latest-head CI结果的正式回执在[PR #22检查页](https://github.com/adgo07/GHGTOOL/pull/22/checks)及PR说明，绑定R1实际新head。推送后必须实际等待Merge-ref Full Tests与PR-head Standalone Audit均success再交付；不冒用eb01a35旧run，不把启动当完成。确切head/run和最终结果以最终回执为准，不为把run SHA写回本Markdown新增自引用提交。

**GHG-RS01-B NOT STARTED**。交付后停止等待独立重新验收，不合并PR #22。
