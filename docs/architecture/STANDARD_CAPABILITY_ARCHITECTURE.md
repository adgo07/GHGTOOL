# 多标准能力渐进复用架构

状态：原则性设计说明；当前仅实现 GB/T 32150—2025 通用规则与 GB/T 32151.34—2024 炭素材料业务。

增加第二项行业标准时，先以该标准正文、已批准 Mapping 和业务测试逐项对照：

- Fuel；
- Electricity；
- Heat / Steam；
- Parameter Resolution；
- Record / Trace；
- Report section。

两个标准的概念、单位、数据来源、校验和结果语义确实一致时，再抽取共享能力。存在可描述差异时，由标准适配器 specialize / override 并保留各自来源与测试；语义明显不同则保留标准专用实现。

当前不得为未来标准提前建立或冻结公共 Fuel、Electricity、Heat、Parameter Resolution、Report 或 Trace Contract；不得因新增第二标准直接复用未经比较的规则。中央公共语义仍受本仓 `platform-lock.json` 和对应 Frozen Contract 约束，当前 Contract 不满足时按仓库治理流程提出证据，不在 GHGTOOL 定义同名公共规则。

本架构原则不授权实现第二标准。第二标准开发仍须遵守 `REFERENCE_STANDARD_ROADMAP.md` 的 RS05 / RS06+ 顺序与中央 Standard Development Guide。
