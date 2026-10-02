# GHG-RS01-B1 — Calculation Safety & Reference Data Closure

日期：2026-10-02
状态：实现与本地验证完成；等待新PR latest-head GitHub Actions和独立重新验收。
范围：仅单条业务输入下的计算安全、参考数据、参数接通和目录真实性；不实施RS01-B2。

## 1. Base / Head / PR

- Base：origin/main 1bad93c66bb98fb5a6d23c29b3d7b135258ebe9d（PR #22的合并结果已包含）。
- 分支：codex/ghg-rs01-b1-calculation-safety，从该最新main创建。
- B1实现head：当前分支提交；最终SHA随完成回执和新B1 PR latest head报告，避免将包含自身的SHA写回本报告。
- PR：新建目标main的B1 PR；PR链接及最终latest head随交付回执给出。
- platform-lock.json SHA-256：4D5741A1127F3A957A0DAA5C36ED38C66622CBF089DA554A5E9AC80D3CD5E23D；锁定Qingzhou-contracts SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20未变。

## 2. B1实际变更

- Canonical新增附录C.1具体燃料默认参数、C.2全表因子、K1/K2/K3与FGD正式缺省；扩大Catalog查询/构建/验证及对应回归。
- Domain增加集中ParameterValue语义门禁；燃料质量、体积与热量单条路径改为消费可追溯Canonical参数；脱硫未知种类不再使用0.44；Catalog状态/引用修复；边界Rule来源定位修正。
- UI补具体燃料、C.2碳酸盐选择、来源编号和热值输入的FieldSpec及标准默认值接通；旧Project兼容测试覆盖缺种类重算阻断。
- 更新CORE_CHECK、GAPS、REFERENCE_STANDARD_ROADMAP、HANDOFF、TASK_STATE及本报告。
- 未改SQLite schema/迁移、platform-lock、中央Frozen Contract或已批准标准解释；未开始B2。

## 3. Canonical正式参考数据

- 总量：98 parameters / 98 factors；行业标准parameter_refs 95；10项排放源引用与实际业务源一致。
- C.1：26种标准燃料×3项（LHV、单位热值含碳量、碳氧化率）。原有天然气3项保留，新增25种燃料共75组参数/因子。
- C.2：11项碳酸盐因子，含CaCO3 0.440、MgCO3 0.522、Na2CO3 0.415及其余8项；每项source、2024版本/因子年、tCO2/t单位和标准表定位均可追溯。
- 另新增K1/K2/K3=0.35、脱硫剂碳酸盐含量=0.90、转化率=1.00，各有正式标准来源；90%/100%不与0.44混用。
- 标准文件：GB/T 32151.34—2024；外置PDF文件名为“34.GB_T 32151.34-2024 温室气体排放核算与报告要求 第34部分：炭素材料生产企业.pdf”，43页；SHA-256 60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738。PDF未入仓。
- 冻结Mapping：SM01-2026-09-13-R6，FROZEN；源文件名“GB T 32151.34—2024 炭素材料生产企业映射方案.md”；源文件SHA-256 01FB34E391A49D8EFAA2E465B38EA6BDFE2183CD00A414B3AB4A331EE36A080B；仓库路径specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md。

## 4. C.4/C.5策略与参数门禁

- 采用方案B：完整C.4/C.5表和查表/插值继续在版本化Domain Calculator；没有新增reference-table schema、DSL或repository。
- Canonical标准来源元数据记录C.4/C.5 PDF/印刷页、SM01-R6版本、原文异常和获批键修正、代表性验证锚点。
- 1.40 MPa/195.04 ℃、1.40 MPa/204.3 ℃及1.50 MPa/207.1 ℃原始证据保留；后两项按项目冻结口径采用1.70/1.80 MPa解释，不称官方勘误。
- Calculator内统一Domain门禁覆盖正式ParameterValue来源：明确非负量要求值≥0，比例为0至1，有标准明文范围时按标准处理；合法0可以继续。未加经验范围或未证实的物理关系判断。致命错误不生成成功Record。
- Catalog calculation_status仍使用已有本地枚举IMPLEMENTED，只代表GHGTOOL本地Catalog中的Calculator当前可用；不代表中央五态、SUPPORTED或RS01/RS02/RS05验收通过。

## 5. GAP-002兼容及历史Record

- 未选碳酸盐种类且无显式可追溯因子：普通中文提示、Domain ERROR、没有成功Record；不会猜CaCO3或静默0.44。
- 旧Project仍可打开；原消耗量保留；未自动选择CaCO3；重新计算得到可操作提示且不创建Record。没有破坏性Project migration。
- 历史Record仍为不可变快照，只读查看原输入/参数/结果，不随新Catalog或Calculator重算、覆盖、迁移；test_historical_snapshot_stays_stable_after_catalog_parameter_change通过。

## 6. 测试预期变化

A. 数据/契约扩展（旧断言 → 新断言）：
- Canonical和隔离Catalog的parameters、factors：7/7 → 98/98；因为上述91项有标准来源的新增C.1/C.2/K/FGD数据。
- 标准参数refs/详情与SRC-32151-34-2024查询：4 → 95；9个标准、12个来源、13条换算规则维持原值。
- “天然气”因子搜索：3 → 6，新增LNG的3项会被同一中文查询匹配；多版本LHV搜索3 → 4，新增LNG标准值。
- 来源验证逐项检查C.1/C.2数值、单位、来源ID、来源版本/年份及条款页码；标准PDF哈希作为外置来源证据。
B. 行为预期修正：
- 旧FGDInput(cal=10)成功采用0.90/0.44/1的测试预期反转为未确认碳酸盐/因子ERROR且不生成Record。这是纠正错误旧行为，不是为使测试变绿。
- K1/K2/K3和FGD标准缺省由Canonical ParameterValue提供并留下来源快照；缺少Canonical值时阻断。
- UI→Domain等价测试改为用真实Canonical目录提供必需缺省；空Catalog缺参仍阻断。

## 7. Gap与文档状态

- 已关闭：GAP-003（集中参数门禁）、GAP-002（未知碳酸盐阻断/C.2全表）、GAP-005（C.1单条燃料路径）、GAP-006（正式参考数据与C.4/C.5 provenance）、GAP-007（本地状态/10来源引用）、GAP-010（Rule定位）。
- 仍开放：GAP-001、GAP-004、GAP-011归RS01-B2；GAP-008仅剩B2测试覆盖；GAP-009为非阻塞provenance debt。
- Gap总数11：IMPLEMENTATION_GAP 8、TEST_GAP 1、EVIDENCE_GAP 2、未解决STANDARD_ISSUE Gap 0、CENTRAL_CONTRACT_GAP 0；已关闭6、开放5。
- CORE_CHECK：25行Matrix，GAP 14、OK 7、N/A独立行0、later-stage 4。
- Roadmap/HANDOFF均记录RS01-A/B和B1/B2；Roadmap的过期无条件DONE已纠正。RS01-B2 NOT STARTED。

## 8. 本地验证与GitHub CI

- 定向核心、Catalog、边界Rule、UI、Project兼容、Result/Record回归：111/111通过。
- 全量：python -m unittest discover -s tests -t . -v，223/223通过，0失败/错误/跳过。
- Canonical：python scripts/validate_canonical.py通过，9 standards / 12 sources / 98 parameters / 98 factors。
- compileall：python -m compileall -q apps packages scripts tests通过。
- pip check：No broken requirements found。
- 隔离临时目录重建4个数据库并查询Catalog：通过；读回98/98，行业本地状态IMPLEMENTED，10个source refs。
- UIR04 Windows缩放验收：1366×768，1.25与1.5均通过；无横向滚动，计算按钮和状态栏可见。
- git diff --check通过。
- GitHub Actions：创建B1 PR后等待并核验Merge-ref Full Tests、PR-head Standalone Audit在latest head成功；最终状态以PR checks页和交付回执中的精确head为准。

## 9. 后续边界

本报告结束后仅等待最新B1 PR head CI及独立重新验收。不合并PR，不启动RS01-B2，不开展RS02/RS03。
