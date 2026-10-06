# TASK_STATE

状态：CURRENT STATE；更新：2026-10-06。

## 当前工作包

- 工作包：**GHG-UAT02 — 核算录入与结果查看体验收口**。本地实现及验证完成，等待本包PR最新head的Windows CI与独立验收；本包不自行合并。
- 仓库：`adgo07/GHGTOOL`；已核对`origin=https://github.com/adgo07/GHGTOOL.git`及实际工作树。分支：`codex/ghg-uat02-accounting-usability`，从开工时最新`origin/main` `c61b29baa2f5d75deae5fc243874d2b1d947bf4a`独立创建；没有从PF01或其他未合并PR派生。
- RS01/RS02及UAT01-A/B已进入`main`；RS03-A用户UAT仍待独立推进，RS03-B、Golden Freeze、Release及第二标准未在本包启动。`GB/T 32151.34—2024`仍为`NOT SUPPORTED`。

## 平台、标准和Scope预检查

- `platform-lock.json`锁定中央`Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`，未升级。按该SHA读取Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；读取当前适用的UI Design Guidelines。适用MUST/MUST NOT：Presentation与Domain/Infrastructure隔离，正式Decimal结果由声明的项目Profile控制，显示格式不回流计算；本包不修改计算Profile、公共Contract或中央基线，无冲突。本任务不涉及新的中央公共Contract。
- 已读取`STANDARD_ISSUES_REGISTER.md`；本包只改既有UI行为及企业自填参数来源说明的错误等级，不改变标准解释、正式公式、Canonical值或已登记Standard Issue；无需新增标准问题。
- PF01拥有的`packages/ui/catalog_pages.py`、`packages/application/catalog_queries.py`、`data-source/carbon_accounting/catalog.json`、`specs/common/canonical_catalog.schema.json`、`packages/core/parameter_resolution.py`及共享标准数据均未修改。未修改`计算表/`用户文件、数据库schema、迁移、Excel/Word或第二标准。

## 实现断点

- 关闭的下拉框/数字框滚轮不再误改选项或数值；展开的下拉列表和键盘操作仍可用。公共滚动宿主在动态行1/5/20条、删除、折叠、展开后重新匹配当前页面高度，滚动范围随之变化。
- 脱硫剂内部组件ID隐藏；多过程实例新增放入次级管理入口，物料新增入口保留；排放源卡片与快捷导航使长表单更易查找和操作。
- 校验失败以“未完成：请修正N项问题”提示并定位首项；企业实测/自定义参数数值有效但缺来源文字时只给WARNING且保留真实空来源快照，缺必填数值、非化石电力证据和物料基准换算证据仍按原规则阻断。
- 细小非零排放值采用适应量级的展示，Domain Decimal和正式结果不变；`0.35`标示为“挥发分折算系数”；防重复计碳控制进专业层。结果过期、成功但含提醒等状态可见；正式记录审计详情默认隐藏、按需打开，历史快照仍只读。

## 本地验证与未执行项

- UAT02专项：`python -m unittest tests.test_uat02_usability tests.test_uat02_geometry -q`，**8/8通过，0失败、0错误、0跳过**。
- 定向回归：`QT_QPA_PLATFORM=offscreen python -m unittest tests.test_uat02_usability tests.test_uat02_geometry tests.test_g06_page tests.test_g07_records tests.test_accounting_projects_ui tests.test_uir03_advanced_details -q`，**77/77通过，0失败、0错误、0跳过**。
- 全量：`QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -t . -q`，**268项，退出码0，0失败、0错误、0跳过**。这是本地Windows/Python 3.12/PySide6的offscreen Qt测试，不冒充可见桌面人工验收。
- `python -m compileall -q apps packages scripts tests`、`python -m pip check`均通过；`python scripts/validate_canonical.py`通过：9 standards、12 sources、98 parameters、98 factors。
- `python scripts/initialize_databases.py --output-dir <隔离临时目录>`通过，catalog/user/records/projects四库从零生成；临时数据库已清理。
- `python scripts/build_standalone.py --output-root <隔离临时目录>`通过，并通过内置release/archive审计；`python scripts/smoke_standalone.py <artifact> --starts 2`通过，独立版隔离启动2次；临时构建产物已清理。
- 可见桌面人工操作与独立产品验收未在本地自动测试中完成，留给独立验收；GitHub Actions必须以最终PR head核对，不能借用旧run。

## 停止点

完成提交、推送和PR后，只等待最新head Windows CI及独立验收；不得自行合并本包、启动PF01/RS03-B、Golden Freeze或Release。
