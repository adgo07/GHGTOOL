# GHG-UI-P3-E 实施报告

日期：2026-10-10。范围：附录B表格导入页Presentation统一；PR #43已通过独立验收，并与已合并P3-C进行无业务语义变更的分支整合。

## 基线与平台 / Contract 预检查

从已核实的Canonical origin `https://github.com/adgo07/GHGTOOL.git`最新 `origin/main@4792d30bf0f31a7bb55d5cb5c13e0cae86bd7813` 创建 `codex/ghg-ui-p3-e-table-import`。该基线包含P3-AB #38、RPT02 #39、EXB01 #40和P3-DF #41。页面/测试实现提交为 `15b5cfb284ad85461490e7da78b99b9bf571a2c3`。

本仓锁定中央Frozen baseline `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。本任务仅调整UI和专属Presentation组件，不涉及中央公共Contract；不改变Architecture、Numeric、标准支持范围或正式规则。Standard Issues Register 8项全部RESOLVED，本任务无新增Issue且不改变已有软件解释。

## 实现

ExcelImportPage现在以一个页面的四个紧凑区域表达模板、文件/核算信息、检查预览、项目保存/正式计算/结果。文件选择与预览成为两个明确动作。结果表对每个单元显示状态和展示用总量；选择单元后可读具体单元格、字段和工作簿提醒。致命工作簿检查错误以页面内文字呈现，不使用阻断式弹窗。

新增 `packages/ui/excel_import_components.py` 作为页面专属展示组件，不引入业务/数据访问规则。选择/预览、有效单元保存、打开项目、主动正式核算、Record关联均沿用EXB01已合并业务路径。无结果Excel导出入口。

代码保护比对确认只触及ExcelImportPage、新增页面组件、界面相关测试、截图和状态记录；Excel Adapter、Canonical、Decimal、Calculator、Projects/Records、数据库、模板、Word报告和正式导出语义均无差异。

## 验证与证据

本地Python 3.12完整回归453/453通过；定向回归34/34；P3-E专项5/5。GUI与Excel的正式结果在既有集成测试中按未修约Decimal逐项等值比较。完整命令、业务保护测试、截图哈希及OPEN项见 `docs/ui/p3-e/ACCEPTANCE.md`。

Windows独立版从已提交源码重建成功；发布目录审计267文件PASS；上传式ZIP往返268可见文件PASS；独立程序两次启动PASS。此为本机Windows结果，不是GitHub Actions结果；GitHub Windows CI须对最终PR head再验证。

## 未完成项与交付

截图为Windows Qt离屏生成，不冒充原生鼠标/键盘/DPI人工验收。原生Windows交互和系统缩放仍OPEN；EXB01既有Excel/WPS原生保存后回导缺项仍OPEN。该包不改业务语义，也不改变行业标准支持状态。

PR #43：https://github.com/adgo07/GHGTOOL/pull/43。独立验收已通过；分支整合在PR #42合并之后完成，当前Head CI及最终合并状态以GitHub Checks和PR页面为准。