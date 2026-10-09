# 报告输出架构

状态：RPT01 + RS03 实施口径；PR35/36已合并，UAT03复用Word导出流程。

## 数据流

不可变Record及其输入、结果、参数、Trace、Provenance、Reporting和资格快照 → Application层只读ReportModel → Infrastructure层Word DOCX renderer。

ReportModel不依赖Qt、SQLite、python-docx或openpyxl，只消费该Record冻结快照；不读取当前表单、不调用Calculator、不查询当前Catalog补参数或重算来源选择。旧快照不足时显示已有历史信息并提示限制，展示修约不回流计算。

用户已取消核算结果Excel导出，只保留Word报告；输入模板与导入不取消。Word版式和分页完善延期，本包不宣称正式视觉验收通过。模型继续按附录B业务分节表达，不声称逐像素复制标准附录。

## 导出与审计

一份Word报告对应一条Record。联系人、地址、编制日期等补充信息仅用于该次导出，不回写Record。既有report_export_history和审计表保留，不新增数据库、不删除历史导出事件或改变Record状态。

文件生成、保存和审计分别处理：未保存时明确失败；已保存但审计失败时提示路径和审计未写入，不能误报文件不存在或宣称审计完成。覆盖原文件需确认，写入失败不能破坏原文件。

补充信息先从Reporting预填，再用同Record最近导出信息补空缺，最后保留空值；编制日期默认当天。普通报告不展示内部Rule、Trace、过程实例或Record标识。

## Excel输入

R2负责输入模板、严格校验、OOXML原始词法证据、Decimal及逐单元预览；预览与正式入口使用同一Calculator配置，不持有Record Repository。用户明确保存有效单元后再由CarbonAccountingUseCase正式核算；致命错误零Record、重复成功新增Record，不建立Excel算法或冻结公共Numeric交换。

projects迁移003保存可选Canonical Input及ingress_provenance；Qt form_state仍仅是Presentation State。allowlist codec保留Decimal、日期、枚举和嵌套输入，拒绝float、非有限数、未知类型/版本，不是公共Workspace Contract或.qzproj。项目通过Excel专用页面恢复，不静默映射为空GUI表单。

正式UseCase在raw_input的ingress_provenance冻结首次导入的工作簿哈希、模板/词法策略、单元身份和原始/标准化数值字符串；保存不重读变化后的文件，不改变公式、Resolver或records.sqlite Schema。

关联失败不重算、不撤销Record。分别反馈恢复标记写入失败、已保存标记后的关联失败、关联已保存后的标记清理失败；未保存标记时不能承诺重启自动恢复。

R2的B.1不是输入表；模板保留填写说明、基本信息和B.2～B.9，B.4使用全角斜线页签。本文是开发资料，不打包为运行资源。

## UAT03复用入口

新建核算结果区与记录页共用Presentation导出流程，仍由Application模型与Infrastructure DOCX renderer完成相同输出。新建页只有本次正式Record已保存且输入指纹未过期时可导出；修改后必须重算，不能读取未保存表单替代该Record。UI helper只编排对话框、文件写入和审计，不改公式或报告排版。
