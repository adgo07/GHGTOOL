# QZC-N01-C-R1 — Declared Numeric Profile Propagation Fix Execution Report

> 状态：**HISTORICAL-SUPERSEDED**
>
> 用途：N01-C Independent Acceptance FAIL 后定点整改的历史 Execution 证据（历史审计证据）
>
> 注意：不得作为当前正式规则依据。本报告中的中央锁定 SHA（`0cd74d78…`）与“Numeric Contract 仍为 DRAFT”等表述属于该任务历史口径；Independent Re-Acceptance 其后已 PASS，Numeric Contract v1 已由独立 adoption 任务采用为 FROZEN。
>
> 当前权威：根目录 `platform-lock.json`、`PLATFORM_BASELINE.md`、`docs/governance/NUMERIC_CONTRACT_V1_ADOPTION_REPORT.md`

状态：**REMEDIATION EXECUTION COMPLETE / INDEPENDENT ACCEPTANCE NOT STARTED**  
代表标准：**GB/T 32151.34—2024**  
Module ID：`qz.carbon_accounting`  
PR：`#16 QZC-N01-C: Numeric/Unit boundary pilot execution`  
整改分支：`qzc-n01-c/numeric-boundary-pilot`

> 本报告是 N01-C Independent Acceptance FAIL 后的定点整改证据。它不替代 Independent Acceptance，不宣布 Gate 3 PASS，不冻结 Numeric Contract、Unit Contract、D-004、D-011 或 D-012。
>
> 原 `QZC_N01_C_EXECUTION_REPORT.md` 中关于 ambient-context defect 的结论仍有效；其中把 p28/p34/p40/p50 helper sensitivity 作为“完整 declared-profile propagation 证据”的部分已被本 R1 报告取代。R1 使用真正端到端 declared profile 重新执行 precision sensitivity。

---

# 1. Remediation baseline

## 1.1 Acceptance finding

整改开始时 PR #16 最新 head：

`b4b577522b6b7218e3c14fa9ebb2608ce0efdf4c`

Independent Acceptance blocking finding：

```text
CarbonMaterialCalculator(policy=...) 声明的 Numeric Profile
没有被所有 authoritative operation 一致消费。

代表问题：
_mul(...)
    -> DecimalPolicy()

requested p28/p34/p50
+ helper default p40/HALF_UP
= mixed-profile authoritative execution
```

本次整改不把 ambient independence 与 declared-profile propagation 混为同一问题。

## 1.2 Branch / lock / baseline regression

- PR：#16，继续原 PR，未创建新 PR。
- branch：`qzc-n01-c/numeric-boundary-pilot`。
- R1 开始 head：`b4b577522b6b7218e3c14fa9ebb2608ce0efdf4c`。
- R1 code+test implementation head：`f337e9b0002020198ad9b63bc99179f1297b49a4`。
- R1 implementation Windows CI run：`36691022248`。
- merge-ref：`0c08455d1dcb48ba98f75eb7edb2e5598ae33fa9`。
- R1 前 full test baseline：head `b4b577...` 的 Windows CI run `36498923892` 已成功。
- `platform-lock.json` 未修改，仍锁定中央 Foundation SHA：`0cd74d783fa23add6dc881b408a8c8ba8503f8e8`。
- 中央仓未修改、未自动升级。

本次继续遵守中央 N01-C Distribution：业务仓只提供 Numeric/Unit/Quantity candidate evidence，不自行冻结公共 Contract。

---

# 2. Full Numeric Authority Audit

R1 不只检查 `_mul()`。对 GB/T 32151.34 代表 Calculator authoritative path 的 parse、policy、local context、直接 Decimal 运算、helpers、interpolation、44/12、44/16、UnitService 与 totals 进行了逐项审计。

| Operation / helper | Requested profile | R1 effective profile | Consistent? |
|---|---|---|---|
| `CarbonMaterialCalculator.calculate()` authority scope | `self.policy` | ContextVar + local Decimal context = `self.policy` | YES |
| `InputValue` / `ParameterValue` lexical parse | N/A | `DecimalPolicy().parse()`，只做精确有限十进制解析，不执行 precision-bearing arithmetic | N/A / no arithmetic drift |
| runtime `_d()` | calculator `self.policy` | active declared policy 的 `parse()` | YES |
| runtime `_mul()` | calculator `self.policy` | active declared policy 的 `multiply()` for every factor | YES |
| fuel `44/12` | `self.policy` | direct Decimal division inside declared local context | YES |
| fuel multiplication | `self.policy` | profile-aware `_mul()` | YES |
| calcination `+ - * /`, `44/12`, `44/16` | `self.policy` | direct Decimal arithmetic inside declared local context | YES |
| baking `+ - * /`, `44/12`, `44/16` | `self.policy` | direct Decimal arithmetic inside declared local context | YES |
| graphitization `+ - * /`, `44/12`, `44/16` | `self.policy` | direct Decimal arithmetic inside declared local context | YES |
| fume/incineration `44/12` | `self.policy` | direct division in declared context | YES |
| fume/incineration multiplication | `self.policy` | profile-aware `_mul()` | YES |
| FGD component multiplication | `self.policy` | common profile-aware `_mul()` | YES |
| FGD `total +=` | `self.policy` | direct Decimal addition in declared context | YES |
| purchased electricity multiplication | `self.policy` | common profile-aware `_mul()` | YES |
| purchased/exported heat multiplication | `self.policy` | common profile-aware `_mul()` | YES |
| UnitService conversion | `self.policy` | normal constructor uses `UnitService(self.policy)`; injected mismatched policy now FAILS | YES |
| saturated/superheated table exact lookup | `self.policy` | exact Decimal comparisons in declared context | YES |
| steam linear interpolation | `self.policy` | direct `+ - * /` in declared context | YES |
| direct / indirect / total aggregation | `self.policy` | direct Decimal `+/-` in declared context | YES |
| Decimal constants (`44`, `12`, `16`, `1e-6`, `1e-9`, table values) | exact literals | exact `Decimal` construction; arithmetic occurs only in declared context/profile | YES |

### Important boundary

Module-level formula helpers remain callable by engineering tests outside a Calculator invocation. Outside an authoritative scope they retain the historical default profile for backward-compatible standalone use. R1 does **not** treat those naked helper calls as an independent authoritative Calculator invocation. Whenever R1 sensitivity tests call those helpers directly, they explicitly enter `declared_numeric_profile(policy)` first.

If a standalone helper is ever promoted to a separate authoritative public calculation entry point, it must declare its own Numeric Profile rather than relying on that compatibility default.

---

# 3. Before R1

N01-C first fix established only the outer Decimal context:

```text
Calculator requested p50
  -> calculate() outer localcontext p50
  -> direct Decimal 44/12 p50
  -> _mul()
       -> DecimalPolicy() default p40/HALF_UP
       -> multiplication p40
```

Therefore the prior implementation could be ambient-context independent while still being internally mixed-profile.

Representative requested p50 fuel path before R1 could collapse back to p40 at `_mul()` and produce the p40-length value:

`3.666666666666666666666666666666666666667`

That is why the original “p40 versus p50” evidence was incomplete: it did not prove that the full p50 authoritative chain was actually p50.

---

# 4. R1 Fix

R1 keeps the existing narrow Numeric authority module and does not rewrite the GB/T formula bodies.

`packages/standards/_numeric_authority.py` now provides one calculator authority scope using a `ContextVar` plus `localcontext()`:

```text
one CarbonMaterialCalculator invocation
    -> self.policy declared once
    -> active policy ContextVar = self.policy
    -> Decimal context precision/rounding = self.policy
    -> direct Decimal operations consume that context
    -> runtime _d/_mul consume that same active policy
    -> UnitService must carry an equal policy
    -> authoritative result
```

### `_mul()` blocker

At package initialization, formula functions resolve `_mul` to the R1 profile-aware helper. Inside a Calculator invocation it obtains the active Calculator policy instead of constructing a hidden p40 policy.

Thus:

```text
requested p50
-> _mul effective p50
```

not:

```text
requested p50
-> _mul default p40
```

### UnitService injected-profile guard

The ordinary constructor already creates:

```text
UnitService(self.policy)
```

R1 additionally blocks dependency injection that would reintroduce a second profile:

```text
Calculator p50 + injected UnitService p40
-> DomainValidationError: numeric profile mismatch
```

This mismatch case has an executable conformance/test vector.

### Algorithm version

Because declared-profile behavior changed for non-default profiles, R1 uses:

`CAR-SM01-2026-09-30-N01C-R1.1`

GB/T formula mapping itself did not change.

---

# 5. After R1 — Declared Profile Consistency

R1 adds runtime instrumentation around representative authoritative helpers and observes both:

- active declared policy；
- Python Decimal current context。

For each Calculator profile below, every observed authoritative helper matched the request:

```text
requested p28 -> active p28 / context p28
requested p34 -> active p34 / context p34
requested p40 -> active p40 / context p40
requested p50 -> active p50 / context p50
```

Observed helpers included：

- `_mul`
- `fuel_mass_emission`
- `calcination_emission`
- `baking_emission`
- `graphitization_emission`
- `fume_incineration_emission`
- `superheated_steam_enthalpy`
- `purchased_heat_emission`
- `direct_emission`
- `indirect_emission`
- `total_emission`

The test asserts both active policy and Decimal context for every captured call. Therefore a future `Calculator p50 -> helper p40` regression fails even if the displayed value appears close.

---

# 6. Ambient Context Independence — separate proof

R1 separately tests caller ambient context and declared Calculator profile.

For each declared Calculator precision p28 / p34 / p40 / p50, the same calculation is run under caller ambient contexts：

- p28 / HALF_EVEN
- p34 / HALF_EVEN
- p40 / HALF_UP
- p50 / HALF_EVEN

Results for each declared profile are invariant across all four ambient contexts.

Example declared p50 result under all four caller contexts：

`3.6666666666666666666666666666666666666666666666667`

Therefore：

> caller ambient context independence = PASS

and independently：

> declared profile propagation = PASS

One is not used as evidence for the other.

---

# 7. True Precision Sensitivity — full Calculator

R1 reran the full representative Calculator with genuine end-to-end profiles p28 / p34 / p40 / p50 / p60.

The fixture exercises fuel, calcination, baking, graphitization, fume incineration, superheated-steam interpolation, purchased heat and final aggregation.

| Item | p28 | p34 | p40 | p50 | p60 |
|---|---|---|---|---|---|
| 44/12 | `3.666666666666666666666666667` | `3.666666666666666666666666666666667` | `3.666666666666666666666666666666666666667` | `3.6666666666666666666666666666666666666666666666667` | `3.66666666666666666666666666666666666666666666666666666666667` |
| fuel | same precision form as 44/12 | same | same | same | same |
| calcination | `10.6535` | `10.6535` | `10.6535` | `10.6535` | `10.6535` |
| baking | `3.364166666666666666666666667` | `3.364166666666666666666666666666667` | `3.364166666666666666666666666666666666667` | `3.3641666666666666666666666666666666666666666666667` | `3.36416666666666666666666666666666666666666666666666666666667` |
| graphitization | `1.439166666666666666666666667` | `1.439166666666666666666666666666667` | `1.439166666666666666666666666666666666667` | `1.4391666666666666666666666666666666666666666666667` | `1.43916666666666666666666666666666666666666666666666666666667` |
| fume | `0.0005174400000000000000000000000` | `0.0005174400000000000000000000000000000` | `0.0005174400000000000000000000000000000000000` | `0.00051744000000000000000000000000000000000000000000000` | `0.000517440000000000000000000000000000000000000000000000000000000` |
| steam interpolation | `3092.1125` | `3092.1125` | `3092.1125` | `3092.1125` | `3092.1125` |
| full Calculator total | `19.46414981500000000000000001` | `19.46414981500000000000000000000001` | `19.46414981500000000000000000000000000001` | `19.464149815000000000000000000000000000000000000001` | `19.4641498150000000000000000000000000000000000000000000000001` |

Executable assertions：

```text
for every representative item:
abs(p40 - p50) <= 1E-38
abs(p50 - p60) <= 1E-48
```

All passed.

The direct formula-helper sensitivity was also rerun under explicit `declared_numeric_profile` for p28/p34/p40/p50/p60 and passed the same convergence checks.

---

# 8. Production Profile Decision

R1 re-evaluated p40 only after genuine p50 and p60 chains were available.

Evidence：

1. repeating-rational paths show the expected extra trailing digits as precision increases；
2. p40 vs true p50 is at or below `1E-38` for every representative item；
3. true p50 vs p60 is at or below `1E-48`；
4. current GB/T 32151.34 Calculator produces emission amounts, not a threshold/grade classification where these trailing digits cross a business boundary；
5. display remains 2 decimal places and is separate from authoritative full value；
6. p40 is now explicitly and consistently applied rather than accidentally mixed with another profile。

R1 therefore retains the current GHGTOOL production profile：

```text
precision = 40
rounding  = ROUND_HALF_UP
```

This is a **GHGTOOL / GB/T 32151.34 project decision supported by current representative evidence**. It does not freeze a platform-wide precision or rounding mode.

Changing to p50 would alter additional trailing authoritative digits and record values, but R1 found no current business-boundary consequence that justifies changing the existing p40 production profile.

---

# 9. Rounding — actual authoritative evidence

R1 distinguishes two facts.

## 9.1 Representative p40 formulas

For 44/12, fuel, calcination, baking, graphitization, fume, steam and representative total, p40 HALF_UP and p40 HALF_EVEN happen to produce identical values for the selected inputs.

This does not mean rounding mode is inactive.

## 9.2 Authoritative `_mul()` tie case

A fuel activity value was selected so the first authoritative multiplication hits an exact p28 halfway case：

`1.0000000000000000000000000005`

Full Calculator result：

- p28 / ROUND_HALF_UP → `3.666666666666666666666666671`
- p28 / ROUND_HALF_EVEN → `3.666666666666666666666666667`

Thus R1 proves with the authoritative fuel path that rounding mode is consumed by working arithmetic and can change the formal result when a tie occurs.

---

# 10. Profile Propagation Conformance

The existing N01-C conformance file now includes executable R1 categories：

```text
kind = profile_propagation
requested_numeric_profile
effective_numeric_profile
authority_scope
expected_total
```

Cases：

- `N01C-P28`
- `N01C-P34`
- `N01C-P40`
- `N01C-P50`
- `N01C-P60`

Each runs a real `CarbonMaterialCalculator(policy=...)` and exact-compares the authoritative result against the profile-specific expected value.

A separate mismatch vector：

`N01C-PX01`

verifies：

```text
Calculator p50 + UnitService p40 -> FAIL
```

This means profile consistency is itself guarded, not inferred only from “close enough” numeric output.

---

# 11. Unit / Quantity scope remains unchanged

R1 did not expand the N01-C Unit/Quantity scope：

- legacy `tC <-> tCO2` UnitService bridge：retained；
- 44/12 and 44/16 structured stoichiometric candidate evidence：retained；
- GWP candidate：retained and still candidate-only；
- C / CO2 / CH4 / CO2e quantity candidate：retained；
- exact business comparison：retained；
- display separation：retained；
- test-only tolerance：retained；
- invalid quantity/unit rejection：retained；
- D-011：OPEN；
- D-012：OPEN；
- D-004：OPEN。

No public Quantity/Unit/coefficient schema was frozen.

---

# 12. Regression evidence

Implementation head：

`f337e9b0002020198ad9b63bc99179f1297b49a4`

Windows CI run：

`36691022248`

## 12.1 Merge-ref Full Tests — PASS

Real execution completed：

- Canonical validation：PASS — `9 standards, 12 sources, 7 parameters, 7 factors`
- `compileall`：PASS
- `pip check`：PASS — `No broken requirements found.`
- isolated DB rebuild：PASS
- UIR04 manual GUI A–E：PASS
- Windows scale 1.25 / 1.5：PASS
- full unittest：**206 tests / OK**
- N01-C Pilot tests：PASS
- R1 profile propagation tests：PASS
- G01：PASS
- G05：PASS
- G06：PASS
- G07：PASS
- existing Unit/Quantity/Coefficient/GWP vectors：PASS
- new profile propagation/mismatch vectors：PASS

## 12.2 PR-head Standalone Audit — PASS

Exact implementation head also completed：

- exact-head canonical validation：PASS
- exact-head compile / pip check：PASS
- DB rebuild：PASS
- GUI / scale acceptance：PASS
- G08 delivery tests：PASS
- standalone build：PASS
- standalone audit：PASS
- archive manifest：PASS
- release provenance：PASS
- startup smoke：PASS
- standalone artifact upload：PASS

Therefore R1 evidence is not only static code inspection; declared profile propagation and true precision sensitivity were actually executed in Windows CI.

---

# 13. Observable / breaking behavior

## Default production p40

For default p40/HALF_UP, the R1 profile propagation fix does not intentionally change the GB/T formula or the normal p40 arithmetic result. It changes the authority mechanism so p40 is now consistently declared and consumed.

## Explicit custom profiles

These are corrected behavior changes. For example requested p50 fuel：

Before R1 mixed-profile path could collapse at `_mul()` to：

`3.666666666666666666666666666666666666667`

After R1 true p50：

`3.6666666666666666666666666666666666666666666666667`

This difference is the intended correctness fix.

Historical records were not mass-recomputed or mutated.

---

# 14. Completion checklist

- `_mul()` authoritative execution no longer silently falls back to p40：**YES**
- other representative authoritative helpers audited for profile source：**YES**
- Calculator/UnitService profile mismatch blocked：**YES**
- ambient independence independently tested：**PASS**
- declared profile p28/p34/p40/p50 consistency independently tested：**PASS**
- p60 reference also executed：**YES**
- true full-Calculator precision sensitivity executed：**YES**
- authoritative rounding-mode effect numerically demonstrated：**YES**
- profile propagation conformance vectors actually executed：**YES**
- existing Unit/Quantity conformance retained：**YES**
- full regression / compile / pip / Canonical / DB / CI executed：**PASS**
- `platform-lock.json` modified：**NO**
- central repository modified：**NO**
- legacy C<->CO2 bridge removed：**NO**
- Quantity schema frozen：**NO**
- D-004 frozen：**NO**
- D-011 frozen：**NO**
- D-012 frozen：**NO**
- PR merged：**NO**
- Independent Acceptance performed by this task：**NO**
- Gate 3 declared PASS by this task：**NO**

**QZC-N01-C-R1 remediation execution is complete. Stop here and return PR #16 to Independent Acceptance.**
