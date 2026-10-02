# QZC-N01-C — GHGTOOL Quantity / Unit / Numeric Boundary Pilot Execution Report

> 状态：**HISTORICAL-SUPERSEDED**
>
> 用途：QZC-N01-C Numeric / Unit / Quantity 边界试点的历史 Execution 证据（历史审计证据）
>
> 注意：不得作为当前正式规则依据。本报告中的中央锁定 SHA（`0cd74d78…`）与“Numeric Contract 仍为 DRAFT”等表述属于该任务历史口径；p28/p34/p40/p50 helper sensitivity 结论已被 `docs/governance/QZC_N01_C_R1_EXECUTION_REPORT.md` 取代，Numeric Contract v1 其后已由独立 adoption 任务采用为 FROZEN。
>
> 当前权威：根目录 `platform-lock.json`、`PLATFORM_BASELINE.md`、`docs/governance/NUMERIC_CONTRACT_V1_ADOPTION_REPORT.md`

状态：**EXECUTION COMPLETE / INDEPENDENT ACCEPTANCE NOT STARTED**  
代表标准：**GB/T 32151.34—2024**  
Module ID：`qz.carbon_accounting`  
Execution branch：`qzc-n01-c/numeric-boundary-pilot`  
PR：`#16 QZC-N01-C: Numeric/Unit boundary pilot execution`

> 本报告只记录业务仓 Execution 证据。它不替代 Independent Acceptance，不宣布 Gate 3 PASS，不冻结 Numeric Contract、Unit Contract、D-004、D-011 或 D-012。

---

## 1. Baseline and scope

### 1.1 Design / execution baseline

- GHGTOOL default branch：`main`
- Execution 开始时真实 `main` HEAD：`84e07bb74dbee8db0fd716e3ed8261cfaf9e3415`
- N01-C Distribution 冻结的 GHGTOOL head：同上
- 已真实执行 Numeric/Conformance 的 code + test head：`b92f5088f12c6d3da5a50e8b04305d10282be42b`
- Windows CI run：`36498353864`
- merge-ref：`0781e9beeb3290bf0f5483641a29894a37e4b8da`

### 1.2 Contract baseline

GHGTOOL `platform-lock.json` 本轮未修改，仍为：

- Contract repository：`adgo07/Qingzhou-contracts`
- baseline SHA：`0cd74d783fa23add6dc881b408a8c8ba8503f8e8`
- `contracts_release = null`
- `release_tag = null`
- `auto_upgrade = false`

中央仓在执行时的 `main` 为 `47a268dcebdc43c582f451b2004c9e63b46502a3`，本轮读取了其中 N01-C Distribution、Numeric Draft、Unit Draft、D-004、D-011、D-012，但**没有自动升级 GHGTOOL 的 platform lock**。

### 1.3 本轮生产代码改动边界

正式业务算法没有重写。生产代码只有一个 Numeric authority boundary：

- `packages/standards/_numeric_authority.py`：新增 declared Decimal context guard；
- `packages/standards/__init__.py`：幂等安装该 guard；
- 原 `packages/standards/carbon_material.py` 公式主体未改；
- `packages/core/units.py` 未改；
- `packages/core/decimal_policy.py` 未改；
- `platform-lock.json` 未改；
- SQLite migration 未改；
- UI 未改。

另外新增：

- `conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json`
- `tests/test_qzc_n01_c_numeric_unit_pilot.py`

---

# 2. Numeric correctness

## 2.1 Current declared Numeric Policy

当前项目已有 `DecimalPolicy`：

```text
precision      = 40
display_places = 2
rounding       = ROUND_HALF_UP
minimum precision accepted by policy = 28
```

`DecimalPolicy.parse()` 拒绝 binary float、bool、NaN、Infinity；policy 自身的 add/subtract/multiply/divide 使用 `localcontext()`。

但 Execution 前的 GB/T 32151.34 Calculator 同时存在：

1. 经过 `DecimalPolicy` 的运算；
2. 直接 Python `Decimal` 的 `+ - * /`；
3. 在调用 `_mul()` 之前已经求值的 `Decimal(44) / Decimal(12)` 等表达式。

因此旧实现并非“所有 authoritative operations 都受 precision=40/HALF_UP 控制”。

---

## 2.2 Ambient Decimal context defect — BEFORE FIX

建立 characterization test 后，使用同一个正式燃料路径输入：

```text
1 × 1 × 1 × 44/12
```

直接调用修复前保存的原始 Calculator `calculate()`，仅改变外部 ambient Decimal context。

真实结果：

| Ambient context | Result |
|---|---|
| precision 28 / ROUND_HALF_EVEN | `3.666666666666666666666666667` |
| precision 40 / ROUND_HALF_UP | `3.666666666666666666666666666666666666667` |
| precision 50 / ROUND_HALF_EVEN | `3.666666666666666666666666666666666666667` |

因此结论明确：

> **authoritative Calculator 的正式结果曾经会因 caller/global ambient Decimal context 改变。**

按本 Pilot 判断标准，这是 **Numeric Policy coverage defect**，不是需要维持的历史行为。

---

## 2.3 Fix

未机械改写全部公式，也未把每个运算替换为 wrapper。

新增的 authority guard 在正式 `CarbonMaterialCalculator.calculate()` 入口建立：

```text
parse / existing typed input
→ enter calculator.policy declared Decimal context
→ execute existing formula operation sequence
→ authoritative result
```

运行时设置：

```text
context.prec     = self.policy.precision
context.rounding = self.policy.rounding
```

这样现有直接 Decimal：

- `44/12`
- `44/16`
- multiplication
- division
- addition/subtraction
- steam interpolation
- totals

只要位于正式 Calculator 业务链内，就在同一 declared context 下执行。

为避免把 correctness change 与旧算法版本混为一谈，新正式 Calculator 运行时算法版本更新为：

`CAR-SM01-2026-09-29-N01C.1`

注意：本轮没有修改 GB/T 32151.34 的公式映射内容；版本变化记录的是 Numeric authority 行为变化。

---

## 2.4 Ambient context — AFTER FIX

默认 Calculator 使用项目当前 p40/HALF_UP policy，在以下外部 ambient contexts 下真实执行：

- p28 / HALF_EVEN
- p34 / HALF_EVEN
- p40 / HALF_UP
- p50 / HALF_EVEN

四次结果完全一致：

`3.666666666666666666666666666666666666667`

因此：

> **正式 `CarbonMaterialCalculator.calculate()` 链现在不再受 caller ambient Decimal context 影响。**

边界说明：本结论针对正式 authoritative Calculator 入口。模块内可直接调用的低层 formula helper 仍是 Python Decimal 函数；Pilot sensitivity test 对它们显式建立 context。它们不应被误写成“任意裸调用都自动拥有全局 Contract context”。

---

# 3. Precision sensitivity — 28 / 34 / 40 / 50

真实运行代表公式，均使用显式 HALF_UP context：

| Formula | p28 | p34 | p40 | p50 |
|---|---|---|---|---|
| fuel | `0.10780000000000000000000000000980` | `0.10780000000000000000000000000000000980` | `0.1078000000000000000000000000000000000000` | `0.1078000000000000000000000000000000000000` |
| calcination | `10.6535` | `10.6535` | `10.6535` | `10.6535` |
| baking | `3.364166666666666666666666667` | `3.364166666666666666666666666666667` | `3.364166666666666666666666666666666666667` | `3.3641666666666666666666666666666666666666666666667` |
| graphitization | `1.439166666666666666666666667` | `1.439166666666666666666666666666667` | `1.439166666666666666666666666666666666667` | `1.4391666666666666666666666666666666666666666666667` |
| fume | `0.0005174400000000000000000000000470400000` | `0.0005174400000000000000000000000000000470400` | `0.0005174400000000000000000000000000000000000` | `0.0005174400000000000000000000000000000000000` |
| steam interpolation | `3092.1125` | `3092.1125` | `3092.1125` | `3092.1125` |
| representative total | `4.803333333333333333333333334` | `4.803333333333333333333333333333334` | `4.803333333333333333333333333333333333334` | `4.8033333333333333333333333333333333333333333333334` |

Pilot assertion 要求所有代表公式：

```text
abs(p40 - p50) <= 1E-38
```

真实通过。

### Execution conclusion on precision=40

对于本 Pilot 已覆盖的 **GB/T 32151.34 当前代表公式和结果链**：

- p28 / p34 对 repeating-decimal 尾数明显较短；
- p40 与 p50 在前约 38 个小数数量级内一致；
- 当前显示 2 位不会暴露这些尾数差异；
- 当前正式业务边界使用 exact comparison，因此仍应以 declared full value 为真值，而不能靠显示修约消除差异。

因此可以提出业务项目 candidate：

> **precision=40 对当前 GB/T 32151.34 Calculator 是足够且合理的 working precision。**

但本证据**不足以冻结“全平台统一 precision=40”**。中央 Numeric Draft 已明确全局精度仍不应机械统一。

---

# 4. ROUND_HALF_UP sensitivity

## 4.1 Rounding mode is real, not decorative

单独构造 p28 的 exact-halfway addition：

```text
1.000000000000000000000000000
+ 0.0000000000000000000000000005
```

真实结果：

- HALF_UP → `1.000000000000000000000000001`
- HALF_EVEN → `1.000000000000000000000000000`

所以 `ROUND_HALF_UP` 在 working arithmetic 中**确实能够改变结果**，并非只用于 UI display。

## 4.2 Current representative formulas at p40

对 fuel、calcination、baking、graphitization、fume、steam、total 在 p40 下分别使用：

- ROUND_HALF_UP
- ROUND_HALF_EVEN

本轮代表输入全部得到相同值。

结论：

> HALF_UP 是一个真实生效的 working policy；但本次代表 GB/T 32151.34 vectors 在 p40 下没有命中能区分 HALF_UP/HALF_EVEN 的 tie。不能据此证明 rounding mode 无关，也不能据此冻结全平台 HALF_UP。

Display 的 2 位格式化仍明确使用 HALF_UP，并已验证不会反向改变 comparison value。

---

# 5. Unit Conversion vs Quantity Transformation

## 5.1 Pure unit conversion — 已真实执行

Conformance 中实际执行：

- `1000 kg → 1 t`
- `1 MWh → 3.6 GJ`
- `1 × 10⁴Nm³ → 10000 Nm³`
- `12.5 % → 0.125 ratio`

这些转换只改变表示尺度/单位，不改变 quantity semantics。

同类可包括现有 UnitService 中：

- kg ↔ t
- kJ / GJ / kWh / MWh
- Nm³ ↔ 10⁴Nm³
- percent ↔ ratio

---

## 5.2 Quantity transformation

本 Pilot 将以下对象与 ordinary unit conversion 分开：

### C → CO₂ via 44/12

它改变 `substance_id`：

```text
C mass → CO2 mass
```

因此不是 kg↔t 一类 unit scaling。

### methane-related → CO₂ via 44/16

同样属于公式/化学计量 transformation，不是普通 unit multiplier。

### gas mass → CO₂e via GWP

GWP 需要：

- greenhouse gas / substance；
- mass；
- GWP value；
- time horizon；
- assessment/version；
- source/provenance。

它是 characterization/equivalence transformation，而非 SI unit conversion。

---

# 6. Legacy `UnitService.convert(tC, tCO2)`

当前 legacy 实现仍真实存在：

- `tC` dimension = `mass_carbon`
- `tCO2` dimension = `mass_co2`
- `UnitService.is_compatible()` 对这两个 dimension 开特殊 bridge；
- `UnitService.convert()` 用 `44/12` / `12/44` 实现跨 bridge。

本 Pilot 对该行为做了 characterization，并验证：

```text
1 tC → 44/12 tCO2
```

### 本轮处理

**没有删除、没有大规模重构、没有把它宣布为未来公共模型。**

原因不是认为旧语义正确，而是：

> 公共 replacement quantity model 仍属于 D-011，尚未冻结。

建议中央后续把 legacy bridge 标为 migration/deprecation candidate，在 quantity model 冻结后再迁移，而不是继续把 44/12 定义成 ordinary `unit_convert()`。

---

# 7. Candidate Quantity Model — 实际 fixture / validation

本 Pilot 实际验证了扩展模型：

## 7.1 Substance mass

```json
{
  "value": "1",
  "quantity_type": "substance_mass",
  "unit_id": "t",
  "substance_id": "C"
}
```

同一结构已验证：

- C
- CO₂
- CH₄

这比 `mass_carbon / mass_co2 / mass_ch4` 无限扩展 quantity_type 更清晰。

## 7.2 CO₂e

```json
{
  "value": "1",
  "quantity_type": "co2e_mass",
  "unit_id": "t",
  "equivalence_basis": {
    "method": "GWP",
    "time_horizon_years": 100,
    "assessment": "IPCC_AR6"
  }
}
```

该结构通过 JSON round-trip 与 candidate validator。

### Candidate conclusion

`value + quantity_type + unit_id` 是必要基础，但对碳领域而言，Pilot 证据支持至少再考虑：

```text
substance_id
```

以及 CO₂e 的：

```text
equivalence_basis
```

这仍是 **candidate**，不得由 GHGTOOL 单方面冻结为公共 Contract。

---

# 8. 44/12 and 44/16 structured trace candidate

Conformance vector 不只存最终十进制值，而是结构化保存：

```text
coefficient_id
coefficient_type = STOICHIOMETRIC
rational_expression
numerator
denominator
standard_id
formula_id
mapping_version
input quantity semantics
output quantity semantics
```

### 44/12

```text
rational_expression = 44/12
numerator           = 44
denominator         = 12
input               = C substance_mass
output              = CO2 substance_mass
```

p40 Decimal evaluation：

`3.666666666666666666666666666666666666667`

### 44/16

```text
rational_expression = 44/16
numerator           = 44
denominator         = 16
input               = CH4-related substance_mass
output              = CO2 substance_mass
```

精确值：`2.75`

结论：

> 44/12 与 44/16 不应作为 ordinary Unit Contract multiplier 的公共候选。

---

# 9. GWP candidate

已建立并执行 candidate-only vector：

```text
gas                = CO2
mass               = 1 t CO2
GWP                 = 1
time horizon        = 100 years
assessment          = IPCC AR6
source_id           = SRC-IPCC-AR6-WGI
factor_year         = 2021
source_location     = Chapter 7 Table 7.15 / Supplementary Table 7.SM.7
result semantics    = 1 t CO2e
```

**明确边界：当前 GB/T 32151.34 Calculator 仍输出 `tCO2`，没有执行 GWP→tCO₂e 业务链。**

所以该 vector 只验证中央未来需要的 Quantity/Trace/Provenance 结构，不能写成“当前 Calculator 已支持 tCO₂e”。

---

# 10. Tolerance audit

对仓库 Python 源进行了 `is_close / tolerance / abs / approximate / interpolation` 扫描，并结合真实调用检查分类。

## 10.1 business-boundary tolerance

当前代表 Calculator：**未发现**。

已确认正式业务判断包括：

- `amount < 0`
- fractions `> 1`
- `0 <= ratio <= 1`
- steam table key `==`
- steam bracket `< / <=`

均是 exact Decimal comparison。

## 10.2 standard-explicit tolerance

本代表标准当前已检查业务路径：**未发现通过 tolerance 改变正式判定的标准明文容差实现**。

## 10.3 lookup / interpolation tolerance

当前 steam lookup：

- exact key 使用 `==`；
- bracket 使用 `< / <=`；
- 非 exact 状态执行线性插值。

没有 epsilon-based lookup tolerance。

## 10.4 algorithmic tolerance

当前 GB/T 32151.34 代表计算链没有 iterative convergence / nonlinear solver tolerance。

## 10.5 test assertion tolerance

确认存在：

- `DecimalPolicy.is_close(..., tolerance="1E-38")`：G01 tC↔tCO₂ repeating decimal 测试；
- `abs(actual - expected) < Decimal("1e-24")`：G06 formula regression；
- N01-C 自身 precision sensitivity assertion。

这些属于 test assertion，不进入业务结果。

## 10.6 display

UI `_display_amount()` 对最终展示使用 2 位、ROUND_HALF_UP；`abs()` 只用于把 Decimal negative zero 规范成显示用正零，不参与业务判定。

### Tolerance conclusion

> **正式业务边界继续 exact；测试 tolerance 可以保留；当前没有证据允许把 `is_close()` 默认 epsilon 升级为业务全局 epsilon。**

---

# 11. Conformance Vectors executed

文件：

`conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json`

已通过测试实际读取并执行，而不是只生成 JSON。

覆盖：

1. pure mass unit conversion；
2. energy conversion；
3. Nm³ / 10⁴Nm³；
4. percent / ratio；
5. C quantity candidate；
6. CO₂ quantity candidate；
7. CH₄ quantity candidate；
8. CO₂e candidate；
9. 44/12 structured coefficient；
10. 44/16 structured coefficient；
11. GWP provenance；
12. invalid quantity/unit combination；
13. full calculation value vs display value；
14. test-only tolerance metadata；
15. ambient Decimal context characterization；
16. p28/p34/p40/p50 sensitivity；
17. p40 HALF_UP/HALF_EVEN sensitivity；
18. representative fuel/calcination/baking/graphitization/fume/steam/total formulas。

---

# 12. Breaking / observable result changes

## 12.1 Formal numeric value

旧实现如果调用方 ambient context 为 p28/HALF_EVEN，可得到：

`3.666666666666666666666666667`

修复后默认 declared p40/HALF_UP authoritative value：

`3.666666666666666666666666666666666666667`

这是正式计算值尾数变化。

原因：

> 修复 ambient-context leakage，统一进入 declared Numeric Policy；不是公式变化、标准变化或人为 ROUND。

## 12.2 Business/UI regression

CI 的 UIR04 GUI 场景仍全部 PASS，其中典型总排放显示仍为：

`11.17 tCO₂`

因此现有已覆盖 UI 显示结果没有因尾数修复产生用户可见破坏。

## 12.3 Historical records

本任务没有批量重算或修改历史 Record。新执行使用新的算法版本标识，历史正式记录不应自动漂移。

---

# 13. Test / execution evidence

在 Windows Server 2025 / CPython 3.12.10 的 GitHub Actions 中，针对 code/test head `b92f5088f12c6d3da5a50e8b04305d10282be42b`：

## 13.1 Merge-ref Full Tests — PASS

Run：`36498353864`  
Job：`Windows / Python 3.12 / Merge-ref Full Tests`

真实完成：

- canonical validation：PASS — `9 standards, 12 sources, 7 parameters, 7 factors`
- `compileall`：PASS
- `pip check`：PASS — `No broken requirements found.`
- isolated databases rebuild：PASS
- UIR04 manual GUI scenarios A–E：PASS
- Windows scale 1.25：PASS
- Windows scale 1.5：PASS
- full unittest：**202 tests / OK**

N01-C 所有新增 characterization / conformance tests 均 PASS。

## 13.2 PR-head Standalone Audit — PASS

同一 Run 的 exact-head job：`Windows / Python 3.12 / PR-head Standalone Audit`

真实完成：

- exact-head checkout：PASS
- canonical validation：PASS
- compile：PASS
- dependency check：PASS
- DB rebuild：PASS
- UIR04 GUI：PASS
- scale acceptance：PASS
- G08 delivery tests：PASS
- standalone directory build：PASS
- standalone directory audit：PASS
- upload archive manifest verification：PASS
- release provenance verification：PASS
- standalone startup smoke：PASS
- standalone candidate upload：PASS

因此 Execution 不是静态审计：数值、边界、Conformance、全量回归和正式打包链均已真实运行。

---

# 14. Central feedback — D-011

## New evidence

1. legacy UnitService 确实把 `mass_carbon ↔ mass_co2` 当作特殊 compatible bridge；
2. 同一个 `44/12` 既存在于 UnitService bridge，也存在于标准 Calculator 公式语义中；
3. `44/16` 属于标准公式/化学计量 transformation；
4. C / CO₂ / CH₄ 用 `quantity_type=substance_mass + substance_id + pure mass unit` 的 candidate 能清楚表达；
5. CO₂e 还需要 `equivalence_basis`；
6. GWP 需要 horizon / assessment / source/version；
7. 当前 Calculator 不输出 tCO₂e；
8. legacy bridge 可以保留到 replacement model 冻结，但应视作 deprecation/migration candidate，而不是未来 ordinary unit-conversion precedent。

## Suggested status

`OPEN — N01-C execution evidence added`

## Freeze now?

**NO**。

仍需中央跨 Pilot / Contract 审查决定最终 Quantity/Unit schema 与 migration policy。

---

# 15. Central feedback — D-012

## New evidence

1. GHGTOOL 正式业务边界当前使用 exact Decimal comparison；
2. `is_close()` 没有进入代表 Calculator 的正式业务判断；
3. 已确认 `is_close(1E-38)` 与 `abs(diff)<1e-24` 为测试断言；
4. steam lookup/interpolation 没有 epsilon；
5. ambient Decimal context 是 precision/context defect，不应靠 tolerance 掩盖；
6. 修复后 formal result 对 caller ambient context 不敏感；
7. 没有证据支持公共 global epsilon。

## Suggested status

`OPEN — supports exact-default and purpose-specific tolerance taxonomy`

## Freeze now?

**NO**。

D-012 仍需 ECQuota exact boundary 与 EquipEffi nonlinear numeric 证据共同审查。

---

# 16. Central feedback — D-004

N01-C 表明 common Conformance Schema 候选至少需要能够表达：

```text
case_id
kind / purpose
numeric_profile
value
quantity_type
unit_id
substance_id (when applicable)
equivalence_basis (CO2e candidate)
coefficient_id
coefficient_type
rational_expression
numerator / denominator
standard_id / formula_id / mapping_version
source / provenance
tolerance purpose
tolerance business_effect
candidate_only
expected business comparison/result
```

特别是：

- coefficient 不能只存最终浮点/十进制值；
- tolerance 必须说明 purpose；
- Quantity semantics 与 Unit 必须可分开；
- candidate-only 行为必须能与正式 Calculator capability 区分。

## Suggested status

`OPEN — candidate fields supplied by N01-C`

## Freeze now?

**NO**。

三个 Pilot 共同完成后再做 Schema v1 冻结。

---

# 17. Matters deliberately left open

本业务仓未决定：

- 公共 Quantity Contract 最终字段；
- `substance_id` 是否 mandatory；
- CO₂e `equivalence_basis` 的最终 schema；
- tC/tCO₂ legacy alias 的长期命运；
- UnitService C↔CO₂ bridge 何时删除；
- coefficient_type 公共枚举；
- GWP 公共 coefficient/characterization 类型；
- 公共 tolerance schema；
- 全平台 precision；
- 全平台 rounding mode；
- D-004 / D-011 / D-012 最终状态。

---

# 18. Execution-stage final statement

- Static code audit completed：**YES**
- Numeric characterization actually executed：**YES**
- Ambient-context defect reproduced before fix：**YES**
- Numeric correctness fix implemented：**YES**
- Numerical results actually recomputed：**YES**
- Precision 28/34/40/50 sensitivity actually executed：**YES**
- HALF_UP/HALF_EVEN sensitivity actually executed：**YES**
- Boundary cases actually executed：**YES**
- Unit/Quantity candidate validation actually executed：**YES**
- Conformance vectors actually executed：**YES**
- Full regression actually executed：**YES**
- Exact-head standalone audit actually executed：**YES**
- `platform-lock.json` changed：**NO**
- UnitService C↔CO₂ bridge removed：**NO**
- Current GB/T 32151.34 Calculator claimed to output tCO₂e：**NO**
- This report freezes D-004：**NO**
- This report freezes D-011：**NO**
- This report freezes D-012：**NO**
- This report freezes a platform-wide Numeric/Unit rule：**NO**
- Independent Acceptance completed：**NO**
- Gate 3 declared PASS by this Execution：**NO**

**QZC-N01-C Execution 已完成；下一步只能进入独立验收。**
