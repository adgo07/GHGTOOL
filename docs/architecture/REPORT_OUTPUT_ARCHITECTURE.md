# 报告输出架构

状态：RPT01 + RS03 实施口径（RS03候选等待独立验收）

## 数据流

```text
成功的不可变 AccountingRecord
  + 该记录保存的输入、结果、参数、Trace、Provenance、Reporting 与资格快照
       ↓
packages/application/reporting/ — 平台无关、只读 ReportModel
       ↓
packages/infrastructure/reporting/ — Word DOCX / Excel XLSX renderer
```

ReportModel 位于 Application 层，不依赖 Qt、SQLite、python-docx 或 openpyxl。它只消费选定记录的冻结快照；不得读取当前编辑页面、调用 Calculator、查询当前 Catalog 补历史参数，也不得按当前规则重算结果。旧记录的快照不足时，报告显示可取得的历史信息并提示限制。

Word 与 Excel 结果输出共享同一 ReportModel 和字段语义。两个 renderer 不得各自遍历 Record 或建立独立取数逻辑。模型以附录 B 的业务分节表达数据，在对应位置列出已保存的排放量、小计和合计；不增加“标准原字段 / 软件计算字段”等来源分类，也不声称是标准附录的逐像素复制件。

## 记录与补充信息

一份 Word 或 Excel 报告对应一条不可变正式 Record。报告补充信息（如联系人、地址、编制日期和说明）只用于该次报告，不回写 Record；每次成功导出追加一条 `records.sqlite` 的 `report_export_history` 事件，记录格式、报告模板版本、文件名、SHA-256 和补充信息。该表为追加式，不增加数据库、不修改 `accounting_records`，并由单独审计事件记录导出。

导出补充信息首先以当前 Record 的 Reporting 快照预填，再以同一 Record 最近一次导出信息补充空缺，最后使用空值；编制日期默认当天。普通报告不显示内部 Rule、Trace、参数、过程实例或 Record 标识。

显示精度只用于文档展示，不能回流 Calculator 或更改 Record。历史结果、来源和有效规则仍以生成该 Record 时保存的快照为准。

## Excel 职责

Excel R2 输入 Adapter负责模板、严格校验、OOXML原始词法证据、Decimal及逐单元预览。预览使用正式入口的同一Calculator配置，但不持有Record Repository。有效单元经用户明确操作后保存为本地项目，再由CarbonAccountingUseCase正式核算；无效单元不保存为可计算项目、不生成Record。Excel不实现第二套公式。R2词法策略是本模块实现，中央Excel Decimal交换仍OPEN / PARTIAL。

项目单元的可选Canonical Input与ingress_provenance通过增量迁移003保存到projects.sqlite；旧Qt form_state继续只表示Presentation State。模块内allowlist JSON codec精确保留Decimal、日期、枚举与嵌套输入，拒绝float、非有限数、未知类型和版本。它不是公共Workspace Contract，也不是.qzproj。Excel项目通过专用Excel页面重开和核算，不能静默还原成空GUI表单。

正式UseCase在原始输入快照的独立ingress_provenance字段冻结导入证据；该字段不改变Calculator输入、公式、参数选择或records.sqlite Schema。工作簿哈希、模板与词法策略、原单元标识以及单元格原始/标准化字符串随该次Record保存。再次核算追加新Record，项目关联使用既有pending recovery机制，保存关联失败不重算或覆盖已生成Record。

Excel结果renderer只接收冻结ReportModel，与Word使用相同显示值。基本信息、B.1～B.9及来源说明按节输出，保留原表业务列；单位与来源在需要时汇入一列有字段标签的说明。所有显示值写为literal text，不产生Excel公式、不进行浮点转换或二次计算；这是供阅读的报告，不是R2可重导入模板或权威数值交换格式。适用排放结果采用模型既有两位小数展示，参数保留模型精度。导出复用已有格式通用的追加式report_export_history，记录XLSX、SHA-256与补充信息。

R2 的 B.1 是计算结果汇总，不属于输入表；因此模板只提供填写说明、基本信息及 B.2～B.9 输入工作表。工作表 B.4 使用“焙烧／炭化”全角斜线，因为 Excel 禁止名称含半角斜线。

本文件与报告 Schema 均为开发资料，不打包为正式运行资源。
