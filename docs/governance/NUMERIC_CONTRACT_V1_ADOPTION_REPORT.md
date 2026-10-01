# Numeric Contract v1 Adoption Report

状态：**ADOPTION IMPLEMENTED / CI VERIFICATION PENDING**  
项目：`adgo07/GHGTOOL`  
Module ID：`qz.carbon_accounting`  
Adoption branch：`chore/numeric-contract-v1-adoption`  
Project base：`main@7b560299311b56f5e82b865ab8db7f7f879697ba`  
Central frozen baseline：`Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`

> 本任务是 Numeric Contract v1 的正式 compatibility/adoption，不是新的 N01-C，不重新设计 Unit / Quantity Contract，也不重新开展 p40/p50 研究。

## 1. Adoption baseline

开始前确认：

- GHGTOOL 当前 `main` head：`7b560299311b56f5e82b865ab8db7f7f879697ba`；
- 该 head 是 PR #16（N01-C + R1）合并 commit；
- N01-C-R1 已保留 declared-profile propagation、ambient independence、precision sensitivity、rounding 与 Unit/Quantity candidate 证据；
- 原 `platform-lock.json` 仍锁定 `0cd74d783fa23add6dc881b408a8c8ba8503f8e8`，Numeric Contract 状态仍为 DRAFT；
- 中央 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 是 `QZC-N01-E: freeze Numeric Contract v1` 的已合并 freeze commit。

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

`contracts_release`、`release_tag` 继续不借本任务推断或升级；`auto_upgrade=false` 保持不变。

## 3. Carbon Numeric Profile alignment

Frozen `NUMERIC_PROFILES_V1_FROZEN.md` 的 GHGTOOL Carbon Profile 与现有 N01-C-R1 实现一致：

| Frozen profile requirement | GHGTOOL current behavior | Adoption result |
|---|---|---|
| `numeric_profile_id` | `GHGTOOL_CARBON_DECIMAL40_CURRENT` | aligned |
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

中央 Contract 明确不建立 p40、p50、HALF_UP 或 HALF_EVEN 的平台统一默认。

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

本 Adoption 不修改该实现，只增加 Frozen Contract 锁定与 adoption conformance 元数据/测试。

Compatibility 要继续证明：

- authoritative scope 使用 declared Profile；
- helper/service 不 silent fallback；
- caller ambient Decimal context 不影响正式结果；
- requested/effective Profile 一致；
- mismatched UnitService profile FAIL；
- business comparison exact；
- display 不回流 decision；
- `is_close()` 不控制 Carbon Calculator 正式业务结论。

## 5. Local N01-C conformance metadata

现有：

`conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json`

继续保留原 N01-C/R1 vectors，不重做 Pilot；仅补充 adoption metadata：

```text
numeric_contract.version              = v1
numeric_contract.status               = FROZEN
numeric_contract.central_baseline_sha = ee5feb0...
numeric_profile.numeric_profile_id    = GHGTOOL_CARBON_DECIMAL40_CURRENT
numeric_profile.numeric_contract_version = v1
```

原 quantity / GWP candidate 内容仍保持 candidate/open 语义，不因为 Numeric v1 adoption 被升级为 Frozen Quantity Schema。

## 6. Unit / Quantity boundary

本次采用 Numeric v1 已冻结的概念分类：

```text
ordinary unit conversion
quantity transformation
stoichiometric / standard-formula coefficient
characterization / equivalence factor
```

因此继续明确：

- kg↔t、kWh/MWh↔GJ 是普通单位换算；
- `44/12`、`44/16` 是 quantity transformation 所使用的 stoichiometric/standard-formula coefficient；
- GWP 是 characterization/equivalence factor；
- `44/12`、`44/16`、GWP 不得提升为公共 ordinary Unit multiplier。

本任务没有：

- 删除 legacy `tC ↔ tCO₂` bridge；
- 冻结 Quantity Schema；
- 冻结 coefficient schema；
- 重写 CO₂e model；
- 重写 UnitService。

## 7. Production code impact

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
- Platform baseline / governance 文档；
- N01-C conformance adoption metadata；
- Numeric v1 adoption compatibility tests；
- Adoption Report / task state / implementation evidence。

## 8. Adoption-specific tests

新增 `tests/test_numeric_contract_v1_adoption.py`，直接检查：

1. 锁定中央 SHA 精确为 `ee5feb0...`；
2. Numeric v1 = FROZEN 且 Frozen 文档路径正确；
3. Unit / Module / Record / Package 继续 DRAFT，Quantity 未被新增为 Frozen Contract；
4. Carbon Profile ID / v1 / Decimal / p40 / HALF_UP / exact comparison / tolerance/display policy 与 Frozen Profile 对齐；
5. declared p40 在 caller ambient p28/p34/p40/p50 下结果完全一致；
6. Calculator p50 + UnitService p40 继续明确 FAIL；
7. exact comparison 与 display separation 继续成立；
8. Carbon Calculator 源码不使用 `is_close()` 进行正式业务判断；
9. N01-C p28/p34/p40/p50/p60 propagation vectors 的 requested/effective Profile 继续一致。

现有 `tests/test_qzc_n01_c_numeric_unit_pilot.py` 继续负责更完整的 R1 instrumentation、multi-precision、rounding、Unit/Quantity candidate 与 tolerance audit。

## 9. Required regression plan

必须在本 Adoption PR 上真实执行：

```text
N01-C / R1 tests
Numeric v1 adoption tests
profile propagation / multi-precision / conformance
G01
G05
G06
G07
full unittest
compileall
pip check
Canonical validation / DB rebuild / existing Windows CI
```

GitHub Actions 的 full unittest 会实际枚举并执行上述 test modules；CI 日志必须用于最终报告，而不能只写静态审计。

## 10. Historical Records

Numeric Contract v1 adoption 不触发历史正式 Record 自动重算。

N01-C-R1 已用独立 algorithm version 标识 Numeric authority 行为变化；本次 Adoption 不修改 Carbon 算法或正式结果，因此不再人为制造新的 Calculator algorithm version。

## 11. Adoption decision

当前实现与中央 Frozen Numeric v1 在 Carbon Numeric Profile 上没有发现需要修改正式 Calculator 的直接兼容冲突。

Adoption 代码/治理修改已完成；最终状态仍等待当前 Adoption PR 的真实 Windows CI。CI 通过后，本报告应补充 exact head、run ID、测试数量和命令证据，然后停止等待独立验收/合并决定。
