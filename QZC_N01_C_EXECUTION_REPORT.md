# QZC-N01-C — GHGTOOL Quantity / Unit / Numeric Boundary Pilot Execution Report

> 状态：**EXECUTION COMPLETE / READY FOR INDEPENDENT ACCEPTANCE**  
> Pilot：`QZC-N01-C`  
> Representative standard：**GB/T 32151.34—2024**  
> Module ID：`qz.carbon_accounting`  
> 本报告不构成 Gate 3 独立验收，不冻结任何中央 Numeric / Unit / Conformance Decision。

---

## 1. Repository / baseline

- Repository：`adgo07/GHGTOOL`
- Default branch：`main`
- Design / Execution start baseline：`84e07bb74dbee8db0fd716e3ed8261cfaf9e3415`
- Pilot branch：`qzc-n01-c/numeric-unit-pilot`
- Draft PR：`#15`
- Fully tested implementation head：`e3c8ec88b1fa2e07f6b4788654e0474e2df6206c`
- Windows CI run：`36463903766` / run #91
- Contract baseline in `platform-lock.json` remains：`0cd74d783fa23add6dc881b408a8c8ba8503f8e8`
- `platform-lock.json` changed by this Pilot：**NO**

Central distribution evidence used:

- Contract baseline tag：`contracts-v0.1.0`
- Foundation baseline SHA：`0cd74d783fa23add6dc881b408a8c8ba8503f8e8`
- N01-C distribution baseline GHGTOOL head：`84e07bb74dbee8db0fd716e3ed8261cfaf9e3415`
- Numeric Contract v1：DRAFT
- Unit Contract v1：DRAFT
- D-011：OPEN
- D-012：OPEN
- D-004：OPEN

The previous local design `QZC_N01_C_LOCAL_DESIGN.md` was read as the Design input. It was not present in the repository at the execution baseline and this execution did not pretend that it was.

---

# 2. Scope executed

This execution performed two deliberately different kinds of work:

1. **Numeric correctness** — a real production Numeric Policy coverage defect was characterized, then the authoritative GB/T 32151.34 numeric path was fixed.
2. **Quantity / Unit semantics** — pilot-only candidate models, traces and conformance vectors were implemented without freezing a public replacement API or removing the legacy C↔CO₂ bridge.

No UI redesign, database migration, common platform package, qzpack work, or public Unit Contract rewrite was performed.

---

# 3. Numeric — before-fix finding

## 3.1 Declared project policy

Existing `DecimalPolicy` declared:

```text
precision      = 40
display_places = 2
rounding       = ROUND_HALF_UP
minimum precision = 28
```

It already rejected binary float / bool / NaN / Infinity as authoritative decimal inputs.

## 3.2 Coverage defect

The GB/T 32151.34 Calculator mixed two numeric styles:

- operations routed through `DecimalPolicy.multiply/divide()`;
- direct Python `Decimal` operators such as `+ - * /` outside an explicit local context.

A particularly important example was:

```text
Decimal(44) / Decimal(12)
```

being evaluated before it entered `_mul()`. Direct process formulas and steam interpolation likewise used bare Decimal operations, and Calculator accumulators used direct addition/subtraction.

Therefore the existence of `DecimalPolicy(precision=40, ROUND_HALF_UP)` did **not** mean the whole authoritative calculation chain was actually under that policy.

## 3.3 Before-fix characterization

The Pilot created a characterization test before the fix and demonstrated real drift under external Decimal contexts.

Representative examples:

| Formula/value | ambient p28 / HALF_EVEN | p40 / HALF_UP | adversarial p16 / DOWN |
|---|---|---|---|
| 44/12 | `3.666666666666666666666666667` | `3.666666666666666666666666666666666666667` | `3.666666666666666` |
| fuel representative | `0.10780000000000000000000000000980` | `0.1078000000000000000000000000000000000000` | `0.10779999999999998040` |
| baking | `3.364166666666666666666666667` | `3.364166666666666666666666666666666666667` | `3.364166666666666` |
| graphitization | `1.439166666666666666666666667` | `1.439166666666666666666666666666666666667` | `1.439166666666666` |
| fume | `0.0005174400000000000000000000000470400000` | `0.0005174400000000000000000000000000000000000` | `0.0005174399999999999059200000` |

This is a **Numeric Policy coverage defect**, not a historical behavior to preserve.

The very first characterization CI commit intentionally recorded the defect; one exploratory assertion about the chosen steam vector was too strong and that exploratory run failed. The later fixed execution does not rely on that failed assertion as evidence. The actual defect was independently reproduced across the repeating-coefficient paths and representative totals and was then covered by the final passing conformance suite.

---

# 4. Numeric fix

## 4.1 Rule now implemented

The authoritative path is now:

```text
parse
→ declared DecimalPolicy calculation context
→ formula operation sequence
→ authoritative result
```

## 4.2 Minimal implementation

`DecimalPolicy` gained one explicit `calculation_context()` helper that sets its declared precision and rounding inside `localcontext()`.

A small standard-specific authority layer was added:

```text
packages/standards/carbon_numeric_authority.py
```

It does **not** rewrite the GB/T 32151.34 formula architecture. It:

- installs one declared context around standalone authoritative formula sequences;
- makes `_d` / `_mul` use the active declared policy;
- wraps direct add/subtract/multiply/divide and interpolation sequences in that context;
- wraps `CarbonMaterialCalculator.calculate()` so accumulators and all nested formula work use `self.policy`;
- allows explicit `policy=` only for numeric sensitivity/conformance characterization;
- uses `ContextVar` so the active Calculator policy is local to the execution context rather than a mutable global numeric setting.

## 4.3 Algorithm version

Newly calculated records now use:

```text
CAR-SM01-2026-09-29-N01C.1
```

Reason: the standard formula mapping did not change, but the authoritative numeric execution semantics did. Historical records are not rewritten.

---

# 5. After-fix ambient-context proof

The final Windows CI actually executed the same representative formulas under three external ambient contexts:

```text
28 / ROUND_HALF_EVEN
40 / ROUND_HALF_UP
16 / ROUND_DOWN
```

All three produced the **same authoritative default-policy results** after the fix:

```text
baking              3.364166666666666666666666666666666666667
calcination         10.6535
fuel                0.1078000000000000000000000000000000000000
fume                0.0005174400000000000000000000000000000000000
graphitization      1.439166666666666666666666666666666666667
representative total 15.56515077333333333333333333333333333334
saturated steam     2794.45
superheated steam   3116.717077732360082870
```

**Conclusion:** external Python Decimal context no longer changes the tested authoritative GB/T 32151.34 results.

---

# 6. Precision sensitivity — 28 / 34 / 40 / 50

The Pilot explicitly executed the representative formula set at 28, 34, 40 and 50 digits with the same declared rounding mode.

Representative total:

```text
p28 = 15.56515077333333333333333334
p34 = 15.56515077333333333333333333333334
p40 = 15.56515077333333333333333333333333333334
p50 = 15.565150773333333333333333333333333333333333333334
```

Graphitization:

```text
p28 = 1.439166666666666666666666667
p34 = 1.439166666666666666666666666666667
p40 = 1.439166666666666666666666666666666666667
p50 = 1.4391666666666666666666666666666666666666666666667
```

Fuel/fume show the same expected deep-tail extension. Saturated and the tested superheated interpolation vector were identical across these precisions at the represented digits.

The final conformance test requires every p40 result to differ from the p50 reference by less than `1e-37`; it passed. All tested 28/34/40/50 values also produced the same current 2-place display output.

## 6.1 Is 40 sufficient and reasonable?

For the **current representative GB/T 32151.34 formula set tested here**, yes as a GHGTOOL project profile candidate:

- it supplies 12 guard digits above the previous minimum 28;
- p40 vs p50 differences are below `1e-37` on the executed vector set;
- 2-place display is stable across all four tested precisions;
- no business-boundary result was changed by precision in the tested paths.

This does **not** freeze precision=40 as the Qingzhou platform-wide Numeric Contract.

## 6.2 What does HALF_UP actually do?

A synthetic precision-boundary tie proved the working rounding mode is real:

- 28 / HALF_UP and 28 / HALF_EVEN give different results on an intentionally constructed tie.

However, the representative GB/T 32151.34 formulas did not hit a HALF_UP/HALF_EVEN tie at precision 40, so changing only those two rounding modes did not alter the tested representative formula outputs.

HALF_UP also continues to control explicit display rounding, e.g. `1.235 → 1.24` at two places.

Therefore:

> HALF_UP is technically operative and explicitly declared, but it is not outcome-determining for the representative GB/T 32151.34 formula vectors executed in this Pilot.

---

# 7. Breaking / numerical changes

The formula interpretation did not change. Deep repeating-decimal tails can change because calculations that previously inherited Python ambient/default precision now use the declared 40-digit policy.

Example:

```text
before (typical ambient p28 graphitization)
1.439166666666666666666666667

after (declared p40)
1.439166666666666666666666666666666666667
```

The existing R6 regression test originally froze the p28 serialization exactly. It was changed to the existing G06 **test-only** `1e-24` assertion style because that test checks the approved R6 formula choice, not the Python ambient precision tail. No business tolerance was added.

The GUI regression still reports the representative visible result `11.17 tCO₂` for the existing UIR04 acceptance scenario.

---

# 8. Pure Unit Conversion vs Quantity Transformation

## 8.1 Pure unit conversion confirmed

These remain ordinary unit semantics and were executed as conformance cases:

- `kg ↔ t`
- energy conversion including `MWh ↔ GJ` and the existing kWh/MWh/kJ/GJ family
- `Nm³ ↔ 10⁴Nm³`
- `percent ↔ ratio`

The physical/business quantity identity is unchanged by these transformations.

## 8.2 Quantity transformation confirmed as a separate semantic class

These are **not** ordinary unit multipliers:

- carbon-related quantity → CO₂ via `44/12`;
- methane-related standard formula term → CO₂ via `44/16`;
- greenhouse-gas mass → CO₂e via a GWP characterization factor.

The Pilot vectors and candidate traces structurally separate these from pure Unit conversions.

---

# 9. Legacy `UnitService.convert(tC, tCO2)`

The existing bridge remains in production during this Pilot.

It was characterized and compared numerically with the candidate stoichiometric transformation. The numbers agree, but their semantics are deliberately classified differently:

```text
legacy API shape: UnitService.convert("1", "tC", "tCO2")
candidate meaning: substance-mass(C, t) × stoichiometric 44/12 → substance-mass(CO2, t)
```

The Pilot does **not** promote the legacy bridge into the public Unit Contract and does not remove it before D-011 freezes a replacement model.

Candidate deprecation proposal for central review:

> once a public Quantity/Transformation Contract exists, retain legacy `tC/tCO₂` aliases only through an adapter/migration boundary and stop describing C↔CO₂ as ordinary Unit compatibility.

This proposal is not executed here.

---

# 10. Candidate Quantity model

Pilot-only code lives under `tests/pilot_support/`; it is intentionally not a public GHGTOOL runtime Contract.

## 10.1 Minimal candidate

```text
value
quantity_type
unit_id
```

This can distinguish `mass_carbon`, `mass_co2`, `mass_co2e` from their unit scale.

## 10.2 Extended candidate

The Pilot also executed:

```text
value
quantity_type = substance_mass | co2e_mass
unit_id       = kg | t
substance_id  = C | CO2 | CH4
equivalence_basis
```

For the tested C / CO₂ / CH₄ / CO₂e cases, the extended model is clearer and more scalable because it avoids creating a new quantity_type for every chemical species.

Candidate interpretation:

```text
C   = substance_mass + substance_id=C
CO2 = substance_mass + substance_id=CO2
CH4 = substance_mass + substance_id=CH4
CO2e = co2e_mass + equivalence_basis
```

`value + quantity_type + unit_id` is sufficient to demonstrate separation, but `substance_id + equivalence_basis` is the stronger candidate for central review.

No public schema is frozen by this finding.

---

# 11. 44/12 and 44/16 coefficient trace

Both are represented by structured rational candidates with:

```text
coefficient_id
coefficient_type
rational_expression
numerator
denominator
formula_id
source_id
source_location
input quantity semantics
output quantity semantics
numeric profile
operation
```

The vectors retain:

```text
44/12
numerator = 44
denominator = 12
```

and:

```text
44/16
numerator = 44
denominator = 16
```

rather than storing only `3.666...` or `2.75`.

Their candidate type is `STOICHIOMETRIC` / standard-formula semantics — never `UNIT_CONVERSION`.

---

# 12. GWP candidate

The repository already contains the CO₂ GWP100 reference factor with provenance:

```text
factor_id      = gwp_co2_ar6_100
value          = 1
time horizon   = 100 years
assessment     = IPCC AR6 WGI
source_id      = SRC-IPCC-AR6-WGI
source_location = Chapter 7 Table 7.15 / Supplementary Table 7.SM.7
factor_year    = 2021
```

N01-C executed a **candidate-only** vector:

```text
1 t substance_mass(CO2)
× GWP100(CO2)=1
→ 1 t co2e_mass
```

The candidate trace classifies the GWP as `CHARACTERIZATION_FACTOR` and preserves time horizon / assessment / source.

**The current GB/T 32151.34 Calculator still outputs `tCO2`; this Pilot does not claim it now calculates or reports `tCO₂e`.**

---

# 13. Tolerance taxonomy

The repository was searched/tested for `is_close`, tolerance-style assertions and interpolation behavior.

| Category | N01-C finding |
|---|---|
| business-boundary | no use of `is_close`; representative business bounds remain exact |
| standard-explicit | none identified in the representative Numeric comparison path |
| lookup/interpolation | steam lookup uses exact bracket/equality and linear interpolation; no epsilon was introduced |
| algorithmic | no iterative/solver tolerance found in the representative Calculator path |
| test assertion | G01 `is_close(..., 1E-38)`; G06 `abs(diff) < 1e-24`; R6 regression now consistently uses test-only `1e-24` |
| display | 2-place HALF_UP formatting only; display does not feed comparison/calculation |

A dedicated Pilot test scans `packages/**/*.py` and confirms there is no business `.is_close(...)` call.

**Business-boundary default remains exact/full-value.** `DecimalPolicy.is_close()` therefore remains a utility/test capability and its default epsilon is not a business-wide epsilon.

---

# 14. Conformance Vectors

File:

```text
conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json
```

Schema status:

```text
n01c-candidate-1
```

Count actually executed: **21**

Executed categories:

- 5 pure Unit conversion cases;
- C / CO₂ / CH₄ Quantity candidates;
- structured 44/12 and 44/16 coefficients;
- GWP100 provenance / CO₂e candidate;
- fuel, graphitization, fume/incineration formulas;
- exact boundary case;
- display/calculation separation;
- ambient-context invariance;
- 28/34/40/50 precision sensitivity;
- invalid semantic combinations;
- Quantity serialization round-trip.

Windows CI printed `N01C_CONFORMANCE_EXECUTED` with all 21 case IDs and the full suite passed.

---

# 15. Actual tests / execution evidence

Final fully tested implementation head:

```text
e3c8ec88b1fa2e07f6b4788654e0474e2df6206c
```

Windows CI:

```text
run #91
run id 36463903766
conclusion SUCCESS
Windows Server 2025
Python 3.12.10
```

## 15.1 Merge-ref Full Tests — PASS

Actual workflow checks:

```text
python scripts/validate_canonical.py
python -m compileall -q apps packages resources scripts tests
python -m pip check
python scripts/initialize_databases.py --output-dir build/databases/uir04-ci-check
python scripts/uir04_manual_gui_acceptance.py
python scripts/uir04_scale_acceptance.py --scale 1.25
python scripts/uir04_scale_acceptance.py --scale 1.5
python -m unittest discover -s tests -t . -v
```

Observed:

- Canonical validation：PASS — `9 standards, 12 sources, 7 parameters, 7 factors`
- compileall：PASS
- pip check：PASS — `No broken requirements found.`
- isolated DB rebuild：PASS
- UIR04 GUI scenarios A–E：PASS
- Windows scale 1.25 / 1.5：PASS
- Full unittest：**199 tests / 199 PASS**
- G01 Decimal/Unit：PASS
- G05 rules / multi-electricity：PASS
- G06 formula / Calculator / page：PASS
- G07 records：PASS
- G08 delivery：PASS in full suite
- N01-C tests：PASS
- 21 Conformance Vectors：executed and PASS

## 15.2 Exact PR-head Standalone Audit — PASS

The second job on the same CI run also passed:

- exact-head canonical validation;
- exact-head compileall;
- exact-head dependency check;
- exact-head isolated databases;
- exact-head GUI acceptance;
- exact-head scale acceptance;
- G08 delivery tests;
- standalone directory build;
- standalone audit;
- archive manifest verification;
- release provenance verification;
- standalone startup smoke test;
- artifact upload step.

This is execution evidence, not independent acceptance.

---

# 16. Files changed by the Pilot implementation

Relative to execution baseline `84e07bb...`, the tested implementation changed only:

```text
conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json     added
packages/core/decimal_policy.py                                      modified
packages/standards/__init__.py                                       modified
packages/standards/carbon_numeric_authority.py                       added
scripts/qzc_n01_c_audit.py                                           added
tests/pilot_support/__init__.py                                      added
tests/pilot_support/n01_c_quantity.py                                added
tests/test_g06_carbon_material.py                                    modified (test assertion only)
tests/test_qzc_n01_c_numeric_unit_pilot.py                           added
```

Production-business impact is narrowly limited to the declared numeric execution authority. The legacy UnitService C↔CO₂ bridge was not rewritten and the production CalculationTrace schema was not migrated.

---

# 17. Central feedback — D-011

## New evidence

1. Existing `UnitService` genuinely models `mass_carbon ↔ mass_co2` as a special compatible bridge and applies `44/12` / `12/44` inside `convert()`.
2. The same `44/12` is a standard-formula / stoichiometric coefficient in the representative Calculator.
3. `44/16` likewise belongs to the standard/stoichiometric formula class, not ordinary Unit scaling.
4. A pilot model separating mass unit from `substance_id` cleanly represents C / CO₂ / CH₄.
5. CO₂e is better represented as an equivalence result carrying `equivalence_basis`, not as another ordinary mass unit alias.
6. GWP requires gas, horizon, assessment/version and provenance.
7. Current production `CalculationTrace` is insufficient to encode this distinction structurally without candidate extensions.

## Suggested status

```text
OPEN — evidence strengthened by executed N01-C vectors
```

## May D-011 be frozen by this Pilot?

**NO.** The replacement public Quantity/Transformation API and schema remain central decisions.

---

# 18. Central feedback — D-012

## New evidence

1. Representative formal business comparisons are exact/full-value.
2. No business `.is_close()` use was found in `packages`.
3. Existing `is_close(...,1E-38)` and `1e-24` comparisons are test assertions.
4. Steam lookup/interpolation uses exact bracket/equality and does not need a lookup epsilon in the current implementation.
5. Fixing Decimal context determinism did not require introducing any business tolerance.
6. A working rounding mode and a tolerance are different concepts and should remain separate in the Contract.

## Suggested status

```text
OPEN — supports exact-default and purpose-specific tolerance taxonomy
```

## May D-012 be frozen by this Pilot?

**NO.** ECQuota and EquipEffi evidence is still required, especially for nonlinear numerical behavior.

---

# 19. Central feedback — D-004 Conformance Schema

N01-C suggests the common Conformance schema needs to be able to express, without assuming these exact field names are final:

```text
semantic category: unit | quantity | coefficient | characterization | formula | boundary
numeric profile / declared context
quantity_type
unit_id
substance_id (when applicable)
equivalence_basis (when applicable)
coefficient_id
coefficient_type
rational_expression + numerator + denominator
formula/source provenance
tolerance purpose/category (only when present)
candidate_only / status for experimental semantics
```

The Pilot also demonstrates why `expected numerical value` alone is insufficient: legacy `UnitService.convert(tC,tCO2)` and the candidate stoichiometric transformation can produce the same number while representing different semantics.

Suggested D-004 status:

```text
OPEN — N01-C candidate evidence available for cross-pilot review
```

No common JSON Schema is frozen here.

---

# 20. Remaining central decisions

GHGTOOL does not decide in this execution:

1. final public Quantity schema;
2. whether public semantics use species-specific quantity types or `substance_id`;
3. public handling of `tC / tCO₂ / tCO₂e` aliases;
4. final coefficient type enumeration;
5. final GWP/CO₂e equivalence-basis schema;
6. when/how the legacy UnitService C↔CO₂ bridge is deprecated or removed;
7. public tolerance purpose enumeration;
8. common Conformance Vector schema;
9. whether 40/HALF_UP is ever shared beyond this GHGTOOL profile;
10. any platform-wide Numeric or Unit Contract freeze.

---

# 21. Explicit execution status

- Static implementation audit completed：**YES**
- Before-fix Numeric defect characterized：**YES**
- Production Numeric authority defect fixed：**YES**
- Numerical results actually executed：**YES**
- Ambient-context cases actually executed：**YES**
- 28/34/40/50 sensitivity actually executed：**YES**
- Business boundary case actually executed：**YES**
- Conformance vectors actually executed：**YES — 21/21**
- Existing regression suite actually executed：**YES — 199/199 PASS**
- Compileall / pip check / Canonical / DB / GUI checks actually executed：**YES**
- Exact-head standalone audit actually executed：**YES**
- `platform-lock.json` changed：**NO**
- Legacy C↔CO₂ bridge removed：**NO**
- Production CalculationTrace schema migrated：**NO**
- Current GB/T 32151.34 Calculator changed to output tCO₂e：**NO**
- D-004 / D-011 / D-012 frozen：**NO**
- Platform-wide Numeric/Unit rule frozen by this report：**NO**
- Independent Acceptance performed：**NO**

**Execution result: COMPLETE — stop here and hand off PR #15 to an independent QZC-N01-C acceptance task.**
