# PLATFORM_BASELINE

本项目当前锁定的 Qingzhou Contracts 上位治理基线。

## 上位仓库

```text
repository: https://github.com/adgo07/Qingzhou-contracts.git
contracts_release/tag: none
baseline_status: pre-release / bootstrap baseline
commit_sha: 0cd74d783fa23add6dc881b408a8c8ba8503f8e8
locked_from: Qingzhou-contracts/main（仅用于本次 bootstrap 锁定；后续不得实时跟随 main）
```

截至 2026-09-28，`Qingzhou-contracts` 尚无正式 release，且没有可用的 `contracts-v0.x.x` tag。因此本项目不虚构版本号，按公共版本规则锁定已经合并批准的精确 `main` commit SHA，并明确标记为 pre-release / bootstrap baseline。

## Architecture 与 Contract 状态

| 项目 | 版本/状态 | 权威文件 |
|---|---|---|
| Architecture | V2.1 — **FROZEN** | `docs/architecture/ARCHITECTURE_V2.1_FROZEN.md` |
| Numeric Contract | v1 — **DRAFT / NOT YET RELEASED** | `contracts/numeric/NUMERIC_CONTRACT_V1_DRAFT.md` |
| Unit Contract | v1 — **DRAFT / NOT YET RELEASED** | `contracts/units/UNIT_CONTRACT_V1_DRAFT.md` |
| Module / Capability Contract | v1 — **DRAFT / NOT YET RELEASED** | `contracts/module/MODULE_CAPABILITY_CONTRACT_V1_DRAFT.md` |
| Workspace / Attempt / Record / Result Contract | v1 — **DRAFT / NOT YET RELEASED** | `contracts/records/WORKSPACE_ATTEMPT_RECORD_RESULT_CONTRACT_V1_DRAFT.md` |
| qzpack / Canonical Package Contract | v1 — **DRAFT / NOT YET RELEASED** | `contracts/package/QZPACK_CONTRACT_V1_DRAFT.md` |

永久 Module ID 已由 Architecture V2.1 FROZEN 冻结为：

```text
qz.carbon_accounting
```

本次接入只建立治理关系，不据此修改现有业务模型、数据库或计算代码。

## 最近升级

```text
baseline_adopted_at: 2026-09-28
baseline_branch: chore/qingzhou-contracts-adoption
```

## 已知公共 Contract 偏差

**存在。** 当前仓库对 Architecture V2.1 的总体方向兼容，但部分公共 Contract 尚未实施或仅部分满足，包括：

- `qz.carbon_accounting` 尚未进入当前业务对象/Result/Record 外围；
- 尚无正式 Capability Manifest；
- Numeric / Unit 已有成熟基础，但权威计算链仍存在待逐步收口项；
- 当前 `projects.sqlite` Workspace 主要保存 Windows runtime Presentation State，尚不是跨平台 Business Workspace Contract；
- 当前 Record/Result 快照较成熟，但尚未形成 V2.1 公共 Result Envelope；
- 尚无平台无关 Conformance Vectors；
- 尚未实施 qzpack。

详细证据、冲突与 RFC Candidate 见 `docs/governance/PLATFORM_ADOPTION_REPORT.md`。

## Upgrade Rule

- 本项目**只受本文件和 `platform-lock.json` 锁定的 Qingzhou-contracts 基线约束**；
- 本项目不得自动、实时跟随 `Qingzhou-contracts/main`；
- 中央仓后续新增或修改的 Architecture / Contract / Schema / Conformance，在本项目显式升级 baseline 前不自动生效；
- 升级必须显式修改本文件和 `platform-lock.json`，核对 breaking changes，并运行适用的公共 Conformance 与本项目完整回归；
- Qingzhou-contracts 中标记为 DRAFT 的内容不得在本项目描述为 FROZEN；
- 公共 Contract 不覆盖更具体的标准原文、已批准标准映射和本业务模块合法自治范围；
- 如发现跨三个产品或跨平台的长期公共语义缺口，应记录 RFC Candidate 并提交 Qingzhou-contracts 统一处理，不在本项目永久私自定义同名公共 Contract；
- 本次接入不要求重构现有业务代码。
