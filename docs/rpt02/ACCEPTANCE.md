# GHG-RPT02 附录B报告验收证据

日期：2026-10-10。状态：实现交付候选，等待独立验收；不自动合并。最终Head和CI以PR #39的head/checks为准。

## 权威与保护边界

模板原始SHA256：`c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4`；清理后：`78042e02b57701cfcb3b4a3fb86dbb6ec8e4fa66ec74cfed768433153d5fdc7e`。分支副本只删除21个指定公式，值差异21、样式差异0、合并差异0；原工作目录模板保持原哈希。逐单元格证据见[evidence/template-comparison.json](evidence/template-comparison.json)。运行时只读打包布局JSON，不读Excel或执行公式。

继续使用一个ReportModel、一个DOCX renderer及PR37公共导出流程。报告阶段只读取该Record的原始输入、结果、参数、Trace、Provenance、Reporting、Qualification；不调用Calculator、不查当前Catalog、不写历史快照或追加核算Record。样例生成器为准备演示Record调用正式Application用例，报告渲染阶段不再计算，二者职责明确分开。

## 表式逐项结论

| 验收项 | 结论与证据 |
|---|---|
| B.1 | 三列及模板合并，十项来源、预留行、ES和ET两条总量；EI不替代ET。Canonical样例ES=19.53、ET=71.86；Excel样例两者27.03，分别与冻结结果相符。 |
| B.2 | 十列、两层合并表头，碳/热值/氧化率独立来源；量纲不适用与历史缺失明确表示。历史未冻结的派生含碳量不补算。 |
| B.3～B.5 | 五列，碳与挥发分投入/产出按模板分组，分组纵向合并；材料按实际行扩展，每过程独立表、尾行冻结过程结果，不分摊。 |
| B.6 | 七列，每设施一行，冻结烟气/焦油/热值/含碳量/氧化率/时长/结果。 |
| B.7 | 七列，设施/批次下碳酸盐扩行，设施结果合并；历史逐组分结果未冻结时不补算。 |
| B.8 | 五列，电量统一显示MWh；输出排放显示负号扣减。购买与输出显式快照按方向分别关联。 |
| B.9 | 保持七列，保留批准模板“动力总量”用词；排放量逐条在表后列示，输出为负号，已冻结自动参考焓值单独说明，未替换采用值。 |
| 表头、列序、单位、脚注 | 单测逐表比对批准工作簿与布局JSON；标准脚注保留。Excel交互填写提示不当作标准脚注或Word运行逻辑。模板原始副本对照与独立只读复核均一致。 |
| 比例与缺失 | ratio经UnitService转percent，0显示0；未启用、未填写、历史未记录、可选无物流区分；仅显示修约，不回流计算。 |

## 正式Record与Word样例

- [Canonical全源Record Word](samples/GHG-RPT02_GUI_Canonical_Record_Appendix_B.docx)及[WPS PDF](samples/GHG-RPT02_GUI_Canonical_Record_Appendix_B.pdf)：由正式共享Application生成、保存再读取的Record；标量兼容输入，不伪称原生GUI按钮人工实测。
- [Excel R2 Record Word](samples/GHG-RPT02_Excel_R2_Record_Appendix_B.docx)及[WPS PDF](samples/GHG-RPT02_Excel_R2_Record_Appendix_B.pdf)：真实R2预览单元经正式Application保存；预览与正式结果full-value精确一致。
- [多源正式Record Word](samples/GHG-RPT02_MultiSource_Record_Appendix_B.docx)及[WPS PDF](samples/GHG-RPT02_MultiSource_Record_Appendix_B.pdf)：燃料2，各过程/设施2，34条物料明细，购入/输出电力热力各2；ES=606.02、ET=679.08。独立[完整快照](samples/GHG-RPT02_MultiSource_Record_Snapshots.json)和[扩行/哈希证据](samples/multisource-evidence.json)。
- [完整Record及冻结快照](samples/records-and-snapshots.json)与[样例哈希/同输入比对](samples/acceptance-evidence.json)。演示数据均标明非企业凭证。

同一R2输入去除导入来源包、归一化生成型input_id后，经Canonical/Application与Excel/Application生成的B.1～B.9内容哈希完全一致。真实GUI自动交互测试另验证同一Record从新建页和记录页导出的Word正文XML相同；记录数仍1、导出历史2条。

## WPS验证

WPS COM 12.0对最终DOCX只读打开并导出PDF：Canonical11页、Excel10页、多源14页，无空白正文页。多过程第二表从新页开始，过程末条明细和小计相邻，标准脚注跟随表格末行；B.9跨页仍重复七列表头。已查看所有页缩略图及关键表的清晰页图，中文、表头、合并与边框可见，未见裁切。独立副本通过WPS修改表格单元格、保存并由python-docx复读确认；原交付DOCX哈希不变。结果见[evidence/wps-render-results.json](evidence/wps-render-results.json)。

合成分页压力QA只用于排版：80条燃料、22页（21个表格页），每个表格页均检出两层表头，80条完整出现；不冒充正式企业Record。见[evidence/pagination-proof.json](evidence/pagination-proof.json)。Documents技能的LibreOffice渲染器因本机无soffice未执行，使用实际WPS渲染和Poppler页图完成替代验证。

## 未闭合与限制

1. 独立验收人尚未在最终Head逐项签收；原生Windows鼠标操作与系统DPI人工验收仍OPEN，Qt离屏自动检查不等同人工签收。
2. 已覆盖现有R2真实导入；EXB01尚未作为已合并基线接入，需其合并后补做整合联测，未修改导入器。
3. 历史或兼容输入没有逐物料快照、派生燃料含碳量、逐碳酸盐结果时，报告明确缺失，不补算。购买/输出电力自动快照若IID、单位、因子均相同而方向归属证据不足，来源安全标记“历史来源快照无法唯一关联”，不会猜造。
4. 只实现当前批准标准专属布局。未来标准通过现有ReportTable布局字段与标准映射函数接入；未建立通用DSL或第二套报告系统。

全量回归、Windows构建、最终Head CI及旧失败日志的真实数量见根目录IMPLEMENTATION_REPORT.md；本文件不把待执行检查写成通过。

独立复核补充（2026-10-10）：最终冻结前收口历史电力来源安全边界。单个候选也须与冻结EF精确匹配；购入/输出同编号且仅剩一个无方向证据的快照时标记无法唯一关联；已转交直接燃料路径的自用化石电力不参与购电来源碰撞判断。新增回归连同定向套件30项通过（tmp/rpt02-focused-30.log）；cbaba59全量因本次安全修正主动停止、无完整summary，不计为通过。修正后重新冻结Head并执行全量、构建与CI，最终结果记于PR39正文。
