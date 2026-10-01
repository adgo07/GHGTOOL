# GHGTOOL 参考标准开发路线

状态：**CURRENT INVENTORY / GOVERNANCE ROADMAP**
盘点日期：2026-10-01
盘点基线：`main@f2f9c4f581fb4f39382b4b3f7db873bfddfaee4f`
参考标准：`GB/T 32151.34—2024`（本仓当前称“炭素材料生产企业核算模块”，准确标准元数据以正式标准目录为准）

> 本文件只盘点当前真实产品能力并调整后续交付优先级，不修改 Calculator、排放公式、Numeric Profile、数据库、Excel 功能、GUI 或 Frozen Contract。

## 1. 平台 / Contract 预检查

| 项目 | 结果 |
|---|---|
| 当前业务仓 SHA | `f2f9c4f581fb4f39382b4b3f7db873bfddfaee4f` |
| `platform-lock.json` | 锁定中央 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` |
| 中央 Contract | Architecture V2.1 FROZEN；Numeric Contract v1 FROZEN；Unit/Module/Workspace-Record/qzpack DRAFT；Quantity public schema NOT FROZEN |
| 当前 Carbon Numeric Profile | `GHGTOOL_CARBON_DECIMAL40_CURRENT`，项目专属，不是平台默认 |
| 适用 MUST | declared Profile consistency、ambient independence、full-value exact formal comparison、Windows-first、Excel 后续共用同一 Calculator |
| 适用 MUST NOT | 不自动跟随 central `main`；不把 44/12/44/16 当 ordinary unit conversion；不在本任务启用 Excel 或新增行业 Calculator |
| 是否发现中央 Contract 冲突 | 否 |
| 是否需要修改中央 Contract | 否 |

中央产品交付治理文件：`Qingzhou-contracts/docs/governance/PRODUCT_DELIVERY_POLICY_V1.md`。该 Policy 属产品交付治理，不改变本仓 Frozen Contract lock。

## 2. 当前批准产品范围

当前 Windows V1 已批准的第一条正式计算链为：

```text
GB/T 32150—2025 通用规则
+
GB/T 32151.34—2024 炭素材料生产企业核算模块
```

其余计划标准当前只允许标准目录/状态信息，不应因为本路线图自动进入 Calculator 开发。

当前产品已有：

- Windows x64 Python/PySide6/SQLite 产品；
- 标准库、参数库、手工核算；
- GB/T 32151.34 Calculator；
- validation + calculation；
- 成功核算立即生成不可编辑正式记录；
- `records.sqlite` 历史记录、快照、审计/删除治理；
- Windows 打包/交付基线；
- Numeric v1 Conformance/adoption。

当前明确未实现：

- 正式 Excel 导入闭环（现有入口为禁用占位）；
- 报告/导出完整能力；
- 其他行业标准 Calculator。

## 3. 状态定义

| 状态 | 中文解释 |
|---|---|
| `DONE` | 已完成，并有正式实现/测试/验收证据 |
| `PARTIAL` | 部分完成；核心能力存在但仍有产品闭环缺口 |
| `NOT STARTED` | 尚未进入正式实现 |
| `BLOCKED` | 被明确依赖或治理条件阻塞 |

## 4. 参考标准现状盘点

| 项目 | 状态 | 证据与说明 |
|---|---|---|
| 标准库 | `DONE` | 当前产品已具备标准目录、标准详情、官方来源/适用范围治理；GB/T 32151.34 是唯一当前完整可计算行业标准，其余标准保持 catalog-only。 |
| 企业信息 | `PARTIAL` | 新建核算流程已有满足当前计算所需的企业/基础信息输入；但历史 V1 治理明确“企业档案完善/企业层级”尚未实施，因此只能认为当前核算所需基础字段可用，不能声称企业主数据能力完整。该缺口不阻断 GB/T 32151.34 单次正式核算。 |
| 核算周期 | `DONE` | 当前新建核算页面和业务模型已经包含核算期间/周期语义，并纳入正式记录快照。 |
| 核算边界 | `DONE` | GB/T 32151.34 计算链已按本行业核算边界运行；遇到其他行业活动/上下游运输只提示需要其他标准，不猜算或并入当前结果。 |
| 排放源 | `DONE` | 已完成 UIR 重构后的排放源卡片/启用输入模式，并保持正式业务校验和数据 retention；代表标准排放源进入同一 Calculator。 |
| 活动数据 | `DONE` | 手工活动数据输入已形成正式主路径；输入经 Application/Domain 校验后进入权威计算，不依赖 Excel。 |
| 参数和因子 | `DONE` | `catalog.sqlite`/Canonical 参数与因子来源、版本、trace 已进入正式计算链；Numeric v1 adoption 保持参数/因子高精度权威语义。 |
| 校验 | `DONE` | 点击计算前执行业务/致命校验；致命错误不生成 Record，成功或带 warning 形成正式结果。N01-C 及全量测试继续覆盖 Profile propagation、mismatch、Unit/quantity/coefficient 边界。 |
| Calculator | `DONE` | GB/T 32151.34 是当前唯一完整行业 Calculator；N01-C R1 已真实修复并验证 declared-profile propagation、ambient independence、p28–p60 sensitivity 和 UnitService profile mismatch rejection。 |
| 分项排放 | `DONE` | 当前正式核算结果包含各排放源/分项计算和 trace；成功核算进入结果/记录快照。 |
| 总排放 | `DONE` | 当前 Calculator 正式聚合总排放；成功结果进入不可编辑正式记录。 |
| 结果解释 | `PARTIAL` | 当前 UI/记录能够展示结果、输入/规则/参数快照和追踪信息；但按新 Policy，仍需要把“计算依据 + 标准依据/来源 + 面向用户解释”作为 Reference Standard 产品级独立验收项集中确认，因此保守标 PARTIAL。 |
| 正式记录 | `DONE` | G07 已完成 `records.sqlite` 正式记录语义：成功计算自动新增不可编辑记录，标准版本/规则/输入/参数/结果快照真实落库；致命失败不生成记录。 |
| 历史记录 | `DONE` | G07 已通过历史记录列表/详情/只读快照、审计与删除治理；正式记录可重新打开查看，不依赖当前输入页面状态。 |
| Windows | `DONE` | G08 已完成 Windows 交付基线；当前批准范围是离线 Windows x64，具备 PySide6/SQLite、打包和启动 smoke 证据。后续仍需按 Reference Standard 新 Policy 在最终 Gate 中复核 Win10/11、中文路径、高 DPI 等，但现有 Windows V1 不是“尚未开始”。 |
| Excel | `NOT STARTED` | 当前 `AGENTS.md`/HANDOFF 明确 Excel 导入只保留禁用占位，正式实现未开始。按照新 Policy，核心业务闭环后 Excel 变为后续必备交付能力，但本任务不得启用或实现它。后续必须证明 GUI 与 Excel 走同一 Application/Domain/Calculator，并处理 Numeric v1 的 Excel 数值入口。 |
| Conformance | `DONE` | N01-C 最终 Independent Re-Acceptance PASS；R1 Profile propagation/ambient independence/unit/quantity/coefficient vectors 与 Numeric v1 compatibility/adoption 均有执行证据。 |
| 下一标准准备状态 | `NOT STARTED` | 七个计划标准当前保持 catalog-only。依据新治理，GB/T 32151.34 核心产品闭环之后应先补 Excel/必要导出，再选择第二标准验证扩展架构；不得直接开始第二行业 Calculator。 |

## 5. 当前结论

GHGTOOL 是三个软件中当前 **Reference Standard 软件核心纵向闭环最接近完整** 的项目：

```text
标准库
→ 新建核算
→ 手工输入
→ 校验
→ GB/T 32151.34 正式计算
→ 分项/总排放
→ 自动正式记录
→ 历史记录/快照
→ Windows 离线交付
```

当前主要缺口：

```text
结果解释的 Reference Standard 集中产品验收
+ 正式 Excel 导入/处理/必要导出闭环
```

因此当前 Reference Standard 总体状态：

`PARTIAL`

其中 Excel 是后续必备能力，但当前没有中央 Contract blocker；应作为独立产品任务实现和验收，而不是本治理盘点顺手开发。

## 6. 后续任务顺序

1. 对 GB/T 32151.34 现有软件核心纵向闭环做 Reference Standard 最终产品验收，重点补确认结果解释/标准依据/来源；
2. 单独设计并实现 Excel Import/Export Adapter，保持同一 Canonical input / Application / Domain / Calculator / result model；
3. 增加 GUI↔Excel 同输入同核心业务结果的 Conformance/Golden 类产品验证；
4. 完成 Excel 数值入口策略，未解决的公共 lossless ingress 继续明确 OPEN/PARTIAL；
5. Reference Standard + Excel Gate PASS 后，再选择第二个行业标准验证扩展架构。

本任务完成后停止，不进入上述实现。
