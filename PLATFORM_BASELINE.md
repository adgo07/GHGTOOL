# PLATFORM_BASELINE

本项目当前锁定的 Qingzhou Contracts 上位治理基线。

## 上位仓库

```text
repository: https://github.com/adgo07/Qingzhou-contracts.git
contracts_release/tag: not adopted by this lock
baseline_status: numeric-v1-frozen-baseline
commit_sha: ee5feb0cc34dbd99790500fadd0c4c932e202a20
locked_from: explicit Numeric Contract v1 adoption baseline；不得实时跟随 main
```

本次升级只采用中央 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 已冻结的 Numeric Contract v1。`platform-lock.json` 仍不填写 `contracts_release` / `release_tag`，因为本任务按用户指定的精确中央 SHA 做兼容性采用，不将其他 Contract 或发布物一起升级。

## Architecture 与 Contract 状态

| 项目 | 版本/状态 | 权威文件 |
|---|---|---|
| Architecture | V2.1 — **FROZEN** | `docs/architecture/ARCHITECTURE_V2.1_FROZEN.md` |
| Numeric Contract | v1 — **FROZEN / ADOPTED** | `contracts/numeric/NUMERIC_CONTRACT_V1_FROZEN.md` |
| Numeric Profiles mechanism | v1 — **FROZEN / ADOPTED** | `contracts/numeric/NUMERIC_PROFILES_V1_FROZEN.md` |
| Unit Contract | v1 — **DRAFT / NOT ADOPTED AS FROZEN** | `contracts/units/UNIT_CONTRACT_V1_DRAFT.md` |
| Quantity public schema | — **NOT FROZEN** | Numeric v1 only freezes conceptual classification boundary |
| Module / Capability Contract | v1 — **DRAFT / NOT ADOPTED AS FROZEN** | `contracts/module/MODULE_CAPABILITY_CONTRACT_V1_DRAFT.md` |
| Workspace / Attempt / Record / Result Contract | v1 — **DRAFT / NOT ADOPTED AS FROZEN** | `contracts/records/WORKSPACE_ATTEMPT_RECORD_RESULT_CONTRACT_V1_DRAFT.md` |
| qzpack / Canonical Package Contract | v1 — **DRAFT / NOT ADOPTED AS FROZEN** | `contracts/package/QZPACK_CONTRACT_V1_DRAFT.md` |

永久 Module ID 继续为：

```text
qz.carbon_accounting
```

## Carbon Numeric Profile

GHGTOOL 当前正式 Carbon Profile 继续采用 N01-C-R1 已验证配置：

```text
numeric_profile_id       = GHGTOOL_CARBON_DECIMAL40_CURRENT
numeric_contract_version = v1
representation           = Decimal / DecimalPolicy
working_precision        = 40
rounding_mode             = ROUND_HALF_UP
comparison_policy         = full-value exact comparison
explicit_rounding_policy  = governing source/Rule only; display rounding does not become business rounding
transcendental_policy     = no Pump-style nonlinear procedure; current evidence is arithmetic/interpolation
business tolerance        = no global business epsilon
test/numerical tolerance  = purpose-specific; isolated from formal business result
display_policy            = 2-place presentation only
```

`p40 / ROUND_HALF_UP` 是 **GHGTOOL Carbon Profile**，不是 Qingzhou 平台默认。Numeric Contract v1 明确禁止把 p40、p50、HALF_UP 或 HALF_EVEN 中任一配置解释为平台统一默认。

N01-C-R1 已证明：

- authoritative Calculator scope 消费 declared Profile；
- helper/service 不允许 silent fallback；
- caller ambient Decimal context 不改变同一 declared Profile 的正式结果；
- requested/effective Profile 可被 Conformance 验证；
- 正式业务比较使用 full-value exact comparison；
- display value 不回流 calculation/comparison；
- `is_close()` / numerical tolerance 不控制正式业务结论。

本次 adoption 不修改 Carbon Calculator；上述行为继续由现有 N01-C/R1 测试与 Conformance 保护。

## Unit / Quantity 边界

本次只采用 Numeric Contract v1 已冻结的概念区分：

```text
ordinary unit conversion
quantity transformation
stoichiometric / standard-formula coefficient
characterization / equivalence factor
```

因此：

- kg↔t、kWh/MWh↔GJ 等继续属于 ordinary unit conversion；
- C mass → CO₂ mass 的 `44/12` 属于 quantity transformation + stoichiometric/formula coefficient；
- 相关公式中的 `44/16` 属于 quantity transformation + stoichiometric/formula coefficient；
- GWP 属于 characterization/equivalence factor。

本次不删除 legacy `tC ↔ tCO₂` UnitService bridge，不冻结 Quantity Schema、coefficient schema 或 CO₂e model，也不把 44/12、44/16、GWP 重新描述成普通 Unit multiplier。

## 本次升级记录

```text
project_base_head: 7b560299311b56f5e82b865ab8db7f7f879697ba
baseline_adopted_at: 2026-10-01
baseline_branch: chore/numeric-contract-v1-adoption
central_frozen_sha: ee5feb0cc34dbd99790500fadd0c4c932e202a20
```

N01-C/R1 已合并进入 `main@7b560299311b56f5e82b865ab8db7f7f879697ba`，本次是在该验证结果之上执行正式 Numeric v1 compatibility/adoption，不重新开启 N01-C 研究。

## Upgrade Rule

- 本项目只受本文件与 `platform-lock.json` 锁定的中央基线约束，不实时跟随 `Qingzhou-contracts/main`；
- 后续中央变更必须再次显式升级 baseline、核对兼容性并运行适用 Conformance 与完整回归；
- Numeric Contract v1 现可在本项目描述为 FROZEN；Unit、Module/Capability、Workspace/Attempt/Record/Result、qzpack 仍必须保持 DRAFT 表述；Quantity public schema 仍不得描述为 frozen；
- 公共 Contract 不覆盖更具体的标准原文、已批准标准映射和本模块合法自治范围；
- 历史正式 Record 不因本次 Numeric Contract adoption 自动重算或漂移；
- 公共语义后续缺口继续进入中央 RFC/ADR 流程，不在 GHGTOOL 私自冻结。
