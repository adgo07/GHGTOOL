# TASK_STATE

状态：CURRENT STATE；更新2026-10-02。

## 当前工作包与基线

- 仓库：adgo07/GHGTOOL；origin已核对为 https://github.com/adgo07/GHGTOOL.git。
- B1 base / origin/main：1bad93c66bb98fb5a6d23c29b3d7b135258ebe9d；PR #22合并提交已在该main历史中。
- 新分支：codex/ghg-rs01-b1-calculation-safety；从上述最新main创建，不基于RS01-A分支。
- platform-lock.json SHA-256：4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D；中央Frozen锁定SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20未变。
- B1包含单条输入的参数安全、标准参考数据、燃料参数接通、Catalog本地计算状态和边界Rule定位；未修改SQLite schema/迁移或中央baseline。
- 新B1 PR及最终HEAD在推送、创建PR后登记；当前待提交/发布。

**GHG-RS01-B1实现和本地验证完成；交付门槛还需新PR latest-head GitHub Actions成功及独立重新验收。**

## 已交付范围

- Canonical：总量98 parameters / 98 factors。新增91组参数和因子数据：C.1新增25种燃料×3=75；C.2完整11项；K1/K2/K3三项；脱硫含量与转化率两项。标准正式参数引用共95项；10个行业排放源引用完整。
- C.4/C.5完整表与查表/插值继续在版本化Domain Calculator；Canonical来源元数据记录标准页码、R6压力键项目解释及锚点，不建reference-table架构。
- Domain ParameterValue门禁覆盖正式来源类型：明确非负参数≥0、比例0至1，合法0允许；非法值为ERROR且不生成成功Record。
- GAP-002未知碳酸盐不再默认0.44；C.2因子逐项来源可追溯，旧Project无种类选择时可打开和保留原数据，重算阻断且不创建Record。
- GAP-005接通具体燃料单条质量/体积/热量参数路径；不为泛称煤猜值。
- GAP-007 Catalog calculation_status=IMPLEMENTED只表示GHGTOOL本地Catalog的Calculator可用，不表示中央标准状态、SUPPORTED或阶段验收。
- GAP-010已将边界Rule source_location改为GB/T 32151.34—2024第4.1条、PDF第10页、印刷页2；未改边界计算语义。
- 历史正式Record不按新Catalog/Calculator重算；历史输入、参数及结果快照稳定性回归通过。
- CORE_CHECK含25行Standard Completeness Matrix：GAP 14行、OK 7行、later-stage 4行、独立N/A状态0行。
- GAPS 11条：关闭6条（002/003/005/006/007/010），开放5条（001/004/008/009/011）。登记类型总量：IMPLEMENTATION_GAP 8、TEST_GAP 1、EVIDENCE_GAP 2、STANDARD_ISSUE 0、CENTRAL_CONTRACT_GAP 0。当前开放风险YES 3、NO 2、UNKNOWN 0；根台账4项历史Standard Issues仍为RESOLVED。
- Roadmap和HANDOFF已同步RS01-A/B及B1/B2边界；GAP-008仅剩B2测试覆盖；GAP-009仍是非阻塞provenance debt。
- RS01-B2 NOT STARTED；未实施多过程/多来源模型、Excel、RS02、Golden Freeze或第二标准。

## 测试预期变化记录

A. 数据/契约随正式标准参考数据扩大：
- Canonical及SQLite parameter/factor定义计数：7/7改为98/98；差额各+91。来源为标准C.1 25种新增燃料（75项）、C.2 11种碳酸盐、K1/K2/K3与脱硫90%/100%缺省（5项）。保留原有天然气三项。
- 行业标准直接parameter_refs及来源查询：4改为95；标准详情/适用参数显示随之扩展。9 standards、12 sources、13 conversion_rules不变。
- “天然气”搜索结果3改为6，因查询文本也匹配LNG三项；C1 LHV多版本结果3改为4，新增LNG标准值。不是人为固定旧计数。
- 每个C.1/C.2值都以GB/T 32151.34—2024附录C.1/C.2原表及页码核对，并在Canonical source/version/location测试中验证；PDF保持仓库外，SHA-256 60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738。

B. Gap修复导致的行为预期变化：
- 旧FGDInput(cal=10)隐式采用0.90/0.44/1并成功的测试预期已反转：未选碳酸盐种类/无可追溯因子现在ERROR且无Record。此举是纠正被旧测试固化的错误行为，不是为了让测试变绿。
- K1/K2/K3与FGD标准缺省来自Canonical并形成来源快照；Canonical缺值不再由Domain静默猜填。
- UI→Domain等价测试改用真实Canonical目录提供标准默认值；空Catalog缺少必需参数时仍阻断。

## 本地验证

- 定向核心/UI/项目/记录测试：111/111通过。
- 全量命令 python -m unittest discover -s tests -t . -v：223/223通过，0失败/错误/跳过。
- python scripts/validate_canonical.py：通过，9 standards、12 sources、98 parameters、98 factors。
- python -m compileall -q apps packages scripts tests：通过。
- python -m pip check：No broken requirements found。
- 隔离临时目录重建catalog.sqlite、user.sqlite、records.sqlite、projects.sqlite并查询：通过；Catalog读回98/98，行业状态IMPLEMENTED、10个排放源引用。
- UIR04 scale acceptance：1366×768、1.25与1.5缩放均通过，无横向滚动且计算按钮/状态栏可见。
- test_historical_snapshot_stays_stable_after_catalog_parameter_change验证旧Record快照稳定；旧项目兼容有专门UI回归。
- git diff --check：通过。
- GitHub Actions exact latest-head结果：PR创建后等待并记录；不得使用旧head CI代替。

下一步仅推送B1分支、创建新的main目标PR、等待最新head CI，然后停止等待独立验收。不要合并，也不要开始RS01-B2。
