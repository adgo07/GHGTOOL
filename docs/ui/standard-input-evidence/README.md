# 标准输入与冻结业务表：窗口证据

`100/` 与 `125/`：真实 Windows Qt 平台启动、QTest/程序驱动窗口与 `QWidget.grab()` 客户区截图；1366×768 逻辑窗口、Qt scale 1.0/1.25，各20项检查、15张截图。使用合成工作簿及隔离数据库，不包含用户业务数据。重现：

```powershell
python scripts/standard_input_ui_acceptance.py --scale 1.0 --width 1366 --height 768 --output-dir build/standard-input-evidence/100
python scripts/standard_input_ui_acceptance.py --scale 1.25 --width 1366 --height 768 --output-dir build/standard-input-evidence/125
```

JSON登记源文件哈希、图片物理尺寸和DPR。Qt scale测试不是Windows系统DPI切换，不等同人工操作验收。

`word-wps/`：WPS 12原生Word兼容COM引擎只读打开临时DOCX、导出PDF后以PDFium渲染；11页全部检查，无空白页、标题线、截断或内部编号泄漏。采用1条合成Record、10张业务表；不是Microsoft Word、LibreOffice或真实企业填报验收。技能自带LibreOffice renderer实际失败（未安装soffice），保留这一限制。模板与报告数据完整性由正式链路测试保护，截图不作为数值真值。
