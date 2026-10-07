# 报告输出架构

状态：RPT01 实施口径（等待独立验收）

## 数据流

```text
成功的不可变 AccountingRecord
  + 该记录保存的输入、结果、参数、Trace、Provenance、Reporting 与资格快照
       ↓
packages/application/reporting/ — 平台无关、只读 ReportModel
       ↓
packages/infrastructure/reporting/ — Word DOCX renderer
       ↓
未来 Excel 结果 renderer（尚未实现）
```

ReportModel 位于 Application 层，不依赖 Qt、SQLite、python-docx 或 openpyxl。它只消费选定记录的冻结快照；不得读取当前编辑页面、调用 Calculator、查询当前 Catalog 补历史参数，也不得按当前规则重算结果。旧记录的快照不足时，报告显示可取得的历史信息并提示限制。

Word 与未来 Excel 结果输出共享同一 ReportModel 和字段语义。两个 renderer 不得各自遍历 Record 或建立独立取数逻辑。模型以附录 B 的业务分节表达数据，在对应位置列出已保存的排放量、小计和合计；不增加“标准原字段 / 软件计算字段”等来源分类，也不声称是标准附录的逐像素复制件。

## 记录与补充信息

一份 Word 报告对应一条不可变正式 Record。报告补充信息（如联系人、地址、编制日期和说明）只用于该次报告，不回写 Record；每次成功导出追加一条 `records.sqlite` 的 `report_export_history` 事件，记录格式、报告模板版本、文件名、SHA-256 和补充信息。该表为追加式，不增加数据库、不修改 `accounting_records`，并由单独审计事件记录导出。

导出补充信息首先以当前 Record 的 Reporting 快照预填，再以同一 Record 最近一次导出信息补充空缺，最后使用空值；编制日期默认当天。普通报告不显示内部 Rule、Trace、参数、过程实例或 Record 标识。

显示精度只用于文档展示，不能回流 Calculator 或更改 Record。历史结果、来源和有效规则仍以生成该 Record 时保存的快照为准。

## Excel 职责

Excel R2 当前是输入 Adapter：模板 → OOXML 词法数值证据 → Decimal → 现有 Application / Domain / Calculator → 每个核算单元只读预览。它不消费 ReportModel 生成结果、不保存 Project / Workspace / Record，也不实现正式公式。Excel 结果导出仍未开始。R2 当前严格读取行为是 GHGTOOL 本地 Adapter 行为，不代表中央 Excel Numeric ingress 已冻结。

R2 的 B.1 是计算结果汇总，不属于输入表；因此模板只提供填写说明、基本信息及 B.2～B.9 输入工作表。工作表 B.4 使用“焙烧／炭化”全角斜线，因为 Excel 禁止名称含半角斜线。

本文件与报告 Schema 均为开发资料，不打包为正式运行资源。
