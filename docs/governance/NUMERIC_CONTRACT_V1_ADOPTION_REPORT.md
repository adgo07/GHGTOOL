# Numeric Contract v1 Adoption Report

状态：**ADOPTION IMPLEMENTED / INITIAL FULL CI PASS / FINAL REPORT HEAD SUBJECT TO CI**  
项目：`adgo07/GHGTOOL`  
Module ID：`qz.carbon_accounting`  
Adoption branch：`chore/numeric-contract-v1-adoption`  
PR：`#17 Adopt frozen Numeric Contract v1`  
Project base：`main@7b560299311b56f5e82b865ab8db7f7f879697ba`  
Central frozen baseline：`Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`

> 本任务是 Numeric Contract v1 的正式 compatibility/adoption，不是新的 N01-C，不重新设计 Unit / Quantity Contract，也不重新开展 p40/p50 研究。

## 1. Adoption baseline

开始前确认：

- GHGTOOL `main` head：`7b560299311b56f5e82b865ab8db7f7f879697ba`；
- 该 head 是 PR #16（N01-C + R1）合并 commit；
- N01-C-R1 已保留 declared-profile propagation、ambient independence、precision sensitivity、rounding 与 Unit/Quantity candidate 证据；
- 原 `platform-lock.json` 仍锁定 `0cd74d783fa23add6dc881b408a8c8ba8503f8e8`，Numeric Contract 状态仍为 DRAFT；
- 中央 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 是 Numeric Contract v1 freeze 后的指定冻结基线。

中央冻结权威文件：

- `contracts/numeric/NUMERIC_CONTRACT_V1_FROZEN.md`；
- `contracts/numeric/NUMERIC_PROFILES_V1_FROZEN.md`；
- `decisions/ADR-NUMERIC-V1.md`；
- `conformance/common/numeric/CONFORMANCE_VECTOR_V1_FROZEN.md`；
- `conformance/common/numeric/conformance_vector_v1.schema.json`。

中央 Frozen Profile 文件明确保留 GHGTOOL Carbon evidence/business profile：

`GHGTOOL_CARBON_DECIMAL40_CURRENT`

## 2. platform-lock adoption

本次 `platform-lock.json` 只做显式基线升级：

```text
old central SHA = 0cd74d783fa23add6dc881b408a8c8ba8503f8e8
new central SHA = ee5feb0cc34dbd99790500fadd0c4c932e202a20
```

Numeric：

```text
version  = v1
status   = FROZEN
document = contracts/numeric/NUMERIC_CONTRACT_V1_FROZEN.md
```

继续保持：

```text
Architecture             = V2.1 FROZEN
Unit                     = v1 DRAFT
Quantity public schema   = NOT FROZEN
Module / Capability      = v1 DRAFT
Record                    = v1 DRAFT
Package / qzpack          = v1 DRAFT
```

`contracts_release`、`release_tag` 不借本任务推断或升级；`auto_upgrade=false` 保持不变。

## 3. Carbon Numeric Profile alignment

Frozen `NUMERIC_PROFILES_V1_FROZEN.md` 的 GHGTOOL Carbon Profile 与现有 N01-C-R1 实现一致：

| Frozen profile requirement | GHGTOOL current behavior | Adoption result |
|---|---|---|
| `numeric_profile_id` | `GHGTOOL_CARBON_DECIMAL40_CURRENT` | aligned |
| `numeric_contract_version` | `v1` | aligned |
| representation | Decimal / DecimalPolicy | aligned |
| working precision | 40 | aligned |
| working rounding | `ROUND_HALF_UP` | aligned |
| comparison | exact/full-value | aligned |
| explicit rounding | 不从 display 推断，须有 source/Rule | aligned |
| business tolerance | 无 global business epsilon | aligned |
| test/numerical tolerance | purpose-specific，与业务判断隔离 | aligned |
| display | 2 位展示，不回流 authoritative value | aligned |
| profile propagation | Calculator scope → helpers/services/aggregation 同一 declared Profile | aligned |
| ambient independence | caller Decimal context 不改变同一 declared Profile 结果 | aligned |

明确：

> `p40 / ROUND_HALF_UP` 是当前 **Carbon Profile**，不是 Numeric Contract v1 的平台默认。

中央 Contract 不建立 p40、p50、HALF_UP 或 HALF_EVEN 的平台统一默认。

## 4. Authoritative Profile consistency

N01-C 首次 Independent Acceptance 的负面证据：

```text
requested p50
→ outer p50
→ _mul() historical default p40/HALF_UP
→ mixed-profile execution
```

R1 已修复为：

```text
one CarbonMaterialCalculator.calculate()
→ self.policy declared once
→ ContextVar active policy = self.policy
→ Decimal localcontext = same precision/rounding
→ _d / _mul consume same policy
→ UnitService must match same policy
→ aggregation consumes same context
```

本 Adoption 不修改该实现，只增加 Frozen Contract 锁定、adoption conformance 元数据与兼容性测试。

Compatibility 继续验证：

- authoritative scope 使用 declared Profile；
- helper/service 不 silent fallback；
- caller ambient Decimal context 不影响正式结果；
- requested/effective Profile 一致；
- mismatched UnitService profile FAIL；
- business comparison exact；
- display 不回流 decision；
- `is_close()` 不控制 Carbon Calculator 正式业务结论。

## 5. Numeric traceability

Numeric v1 要求正式结果能够识别至少：

```text
numeric_contract_version
numeric_profile_id
calculator_version and/or rule_version
```

本任务不冻结新的 Result/Record 字段，因为中央 ADR 明确 `numeric_behavior_version` 等字段的最终放置仍属于 Result/Record Contract 后续问题。

GHGTOOL 当前采用已有的 `algorithm_version` 作为 immutable lookup key：

```text
CalculationResult.algorithm_version
AccountingRecord.algorithm_version
        ↓
conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json
        ↓
calculator_version = CAR-SM01-2026-09-30-N01C-R1.1
numeric_contract_version = v1
numeric_profile_id = GHGTOOL_CARBON_DECIMAL40_CURRENT
```

新增 adoption test 真实生成成功 Result 与 Record，并验证：

```text
outcome.algorithm_version
= CalculationResult.algorithm_version
= AccountingRecord.algorithm_version
= numeric_profile.calculator_version
```

因此在不修改 Record schema 的前提下，当前正式结果可通过版本化 lookup/reference 结构识别 adopted Numeric Contract/Profile；本任务没有擅自冻结新的公共 Result 字段。

## 6. Local N01-C conformance metadata

现有：

`conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json`

继续保留原 N01-C/R1 vectors，不重做 Pilot；只补充 adoption metadata：

```text
numeric_contract.version                 = v1
numeric_contract.status                  = FROZEN
numeric_contract.central_baseline_sha    = ee5feb0...
numeric_profile.numeric_profile_id       = GHGTOOL_CARBON_DECIMAL40_CURRENT
numeric_profile.numeric_contract_version = v1
numeric_profile.calculator_version       = CAR-SM01-2026-09-30-N01C-R1.1
```

原 quantity / GWP candidate 内容继续保持 candidate/open 语义，不因为 Numeric v1 adoption 被升级为 Frozen Quantity Schema。

## 7. Unit / Quantity boundary

本次采用 Numeric v1 已冻结的概念分类：

```text
ordinary unit conversion
quantity transformation
stoichiometric / standard-formula coefficient
characterization / equivalence factor
```

因此继续明确：

- kg↔t、kWh/MWh↔GJ 是 ordinary unit conversion；
- `44/12`、`44/16` 是 quantity transformation 所使用的 stoichiometric/standard-formula coefficient；
- GWP 是 characterization/equivalence factor；
- `44/12`、`44/16`、GWP 不得重新描述为普通 Unit multiplier。

本任务没有：

- 删除 legacy `tC ↔ tCO₂` bridge；
- 冻结 Quantity Schema；
- 冻结 coefficient schema；
- 重写 CO₂e model；
- 重写 UnitService。

## 8. Production code impact

正式 Carbon Calculator：**未修改**。

未修改：

- `packages/standards/carbon_material.py`；
- `packages/standards/_numeric_authority.py`；
- `packages/core/decimal_policy.py`；
- `packages/core/units.py`；
- Canonical source；
- SQLite schema/migrations；
- UI。

本次改动限定为：

- `platform-lock.json`；
- `AGENTS.md` / `PLATFORM_BASELINE.md` 当前治理状态；
- N01-C conformance adoption/traceability metadata；
- Numeric v1 adoption compatibility tests；
- 本 Adoption Report。

## 9. Adoption-specific tests

新增 `tests/test_numeric_contract_v1_adoption.py`，直接检查：

1. 锁定中央 SHA 精确为 `ee5feb0...`；
2. Numeric v1 = FROZEN 且 Frozen 文档路径正确；
3. Unit / Module / Record / Package 继续 DRAFT，Quantity 未被新增为 Frozen Contract；
4. Carbon Profile ID / v1 / Calculator version / Decimal / p40 / HALF_UP / exact comparison / tolerance/display policy 与 Frozen Profile 对齐；
5. 正式 Result / Record 的 algorithm version 能映射到 adopted Contract/Profile；
6. declared p40 在 caller ambient p28/p34/p40/p50 下结果完全一致；
7. Calculator p50 + UnitService p40 继续明确 FAIL；
8. exact comparison 与 display separation 继续成立；
9. Carbon Calculator 源码不使用 `is_close()` 进行正式业务判断；
10. N01-C p28/p34/p40/p50/p60 propagation vectors 的 requested/effective Profile 继续一致。

现有 `tests/test_qzc_n01_c_numeric_unit_pilot.py` 继续负责完整的 R1 runtime instrumentation、multi-precision、rounding、Unit/Quantity candidate 与 tolerance audit。

## 10. First complete CI evidence

PR #17 初始完整 adoption checkpoint：

```text
head      = 8a367ed829244490ef71fbaad120e4e6d8026033
merge-ref = 34a61a2e24a25b233dd85adb580041d48969ede8
CI run    = 36810851047
runner    = Windows Server 2025 / CPython 3.12.10
```

### Merge-ref Full Tests — PASS

真实执行：

```text
python scripts/validate_canonical.py
→ valid: 9 standards, 12 sources, 7 parameters, 7 factors

python -m compileall -q apps packages resources scripts tests
→ PASS

python -m pip check
→ No broken requirements found.

python scripts/initialize_databases.py --output-dir build/databases/uir04-ci-check
→ catalog/user/records/projects 四库重建 PASS

python scripts/uir04_manual_gui_acceptance.py
→ 场景 A–E PASS

python scripts/uir04_scale_acceptance.py --scale 1.25
python scripts/uir04_scale_acceptance.py --scale 1.5
→ PASS

python -m unittest discover -s tests -t . -v
→ Ran 213 tests
→ OK
```

全量日志实际包含并通过：

- G01 Decimal/Unit tests；
- G05 rules / multi-electricity；
- G06 Calculator / formula / page；
- G07 records / UI；
- N01-C / R1 profile propagation；
- p28/p34/p40/p50/p60 precision/conformance；
- Unit/Quantity candidate boundary；
- Numeric v1 adoption tests。

N01-C-R1 runtime instrumentation 继续显示 requested/effective profile 以及 active Decimal context 在 p28/p34/p40/p50 下逐 helper 一致。

### PR-head Standalone Audit — PASS

同一 run 的 exact-head job 真实完成并 PASS：

- exact-head checkout；
- Canonical validation；
- compileall；
- pip check；
- isolated DB rebuild；
- GUI acceptance；
- scale acceptance；
- G08 delivery tests；
- standalone directory build；
- standalone audit；
- archive manifest verification；
- release provenance verification；
- startup smoke；
- artifact upload。

因此本 Adoption 的首个完整 checkpoint 已真实通过项目完整 Windows CI，而不是只做静态审计。

## 11. Post-CI traceability tightening

首个完整 CI PASS 后，仅对 adoption traceability metadata/tests 做进一步收口：

- 在 Numeric Profile metadata 增加 `calculator_version = CAR-SM01-2026-09-30-N01C-R1.1`；
- 新增 Result/Record algorithm-version → Numeric v1/Profile mapping 的执行测试；
- 未修改任何生产 Calculator / Numeric helper / UnitService。

本报告提交前最新 implementation head：

`e70a16c4e8476b49e496b3bc3609ef9a018aa68e`

这些收口以及本报告提交后的最终 PR head 必须继续通过 PR Windows CI；本报告本身不把尚未结束的最终-head CI 写成已通过。

## 12. Historical Records

Numeric Contract v1 adoption 不触发历史正式 Record 自动重算。

N01-C-R1 已用独立 `algorithm_version` 标识 Numeric authority 行为。Adoption 不修改 Carbon 数值算法、正式公式或 working Profile，因此不人为制造新的 Calculator algorithm version；采用版本化 lookup/reference 将既有 R1 algorithm version 对应到已冻结的 Numeric v1 Carbon Profile。

## 13. Adoption conclusion

Compatibility audit 未发现需要修改正式 Carbon Calculator 的 Numeric v1 冲突。

当前结论：

- central frozen SHA 已显式锁定；
- Numeric Contract v1 已标记 FROZEN / adopted；
- Carbon p40/HALF_UP Profile 与 Frozen Profile 一致；
- p40/HALF_UP 未被提升为平台默认；
- R1 declared-profile propagation / ambient independence 继续受测试保护；
- exact/full-value comparison、display separation、tolerance separation 继续成立；
- Unit / Quantity 未越界升级；
- 正式 Calculator 未修改；
- 首个完整 Windows CI checkpoint 已 PASS；
- PR #17 保持 open / unmerged，最终报告 head 仍须通过 CI 后交付审查。

本任务不自行合并，不自行替代后续独立验收/合并决定。
