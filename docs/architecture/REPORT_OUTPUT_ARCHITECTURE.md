# 报告输出架构

状态：GHG-RPT02 实施口径；复用已合并PR37公共Word导出入口，待独立验收。

## 数据流

不可变Record及其输入、结果、参数、Trace、Provenance、Reporting和资格快照 → Application层只读ReportModel → Infrastructure层Word DOCX renderer。

ReportModel不依赖Qt、SQLite、python-docx或openpyxl，只消费该Record冻结快照；不读取当前表单、不调用Calculator、不查询当前Catalog补参数或重算来源选择。旧快照不足时显示已有历史信息并提示限制，展示修约不回流计算。

用户已取消核算结果Excel导出，只保留Word报告；输入模板与导入不取消。Word使用用户批准的附录B填报模板的业务布局，运行时仅加载版本化JSON布局定义，不读取Excel或执行表格公式。Word纸张、分页、字体为可读性适配，结构验收与WPS检查单独记录，不将自动化结构检查冒充人工操作验收。

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

## GHG-RPT02标准专属布局边界

保留一个ReportModel和一个DOCX renderer。`appendix_b.py`负责本标准冻结快照到业务表的映射，`appendix_b_layout.json`只保存批准表名、表头、合并关系、列宽比例与标准脚注；没有公式或万能DSL。其他标准需独立批准的布局/映射后接入同一ReportTable结构；未登记标准显式拒绝，不能套用炭素表式。

ReportTable增加多层表头、头部/正文合并、脚注及上下文标题。B.3～B.5每个过程独立扩展同一表式；B.6逐设施行；B.7同一设施合计合并显示，不将冻结设施合计误充每个组分排放量。B.9批准模板只有七列，对应排放量及冻结自动参考焓值在表后按方向和条序逐项列示。

B.1两条总量只取ES与ET。`frozen_totals`共用到记录详情，EI仍为净间接排放量。输出电力/热力明细以负号明确扣减；B.1输出量按模板列示原正值，说明其在总量中扣减。显示单位转换使用显式DecimalPolicy的UnitService，仅供展示，不重算排放、不写回Record。未启用、真实零、未填写和历史未记录分别标记。未冻结的派生燃料含碳量不从低位发热量和单位热值含碳量重算。

表式2.0.0追溯原批准模板SHA256与公式清理后SHA256。导出审计继续保存schema/template_version和DOCX哈希，DOCX属性记录布局ID及批准模板哈希。官方标准全文不进入包。
