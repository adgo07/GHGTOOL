# GHG-UAT01-A — 普通核算录入与错误反馈体验修复

状态：本地实现与验证完成；等待独立UAT01-A PR的latest-head Windows CI及独立验收。UAT01-B未启动；RS03-A USER UAT因UAT01阻塞；PR #27保持OPEN / UNMERGED；标准仍为 `NOT SUPPORTED`。本报告不写自身提交SHA；最终head与CI以本包PR Checks为准。

## 1. 基线与平台预检查

- 仓库：adgo07/GHGTOOL；origin：https://github.com/adgo07/GHGTOOL.git。
- Base / 开工时最新origin/main：`058d176a8a461b758db1a1d62395b032889d9b2a`；已执行fetch复核，origin/main仍为该SHA。
- 分支：`codex/ghg-uat01-a-entry-usability`，从上述main创建；开工时工作树干净。提交及PR latest head由Git和GitHub记录确定。
- platform-lock.json SHA-256：`BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0`；中央locked SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`未改动。
- Architecture V2.1、Numeric Contract v1、Numeric Profiles v1为本任务相关locked Frozen Contract；本任务不涉及中央公共Contract，不改baseline或platform-lock。
- 沿用4条历史RESOLVED Standard Issue；未改变标准解释、未新增标准问题。PR #27只读，未修改。

## 2. 实际改动

- 新核算页移除独立“检查数据”动作，保留单一“计算排放量”；由Domain正式校验一次返回错误和提醒，按问题类别、排放源、实例、字段展示并支持定位；失败不生成结果或Record。
- 移除普通界面的冗余边界框、专业详情入口及普通用户技术控件；边界、来源状态、Reporting、Evidence和Trace等业务语义仍保留。
- 企业名称允许留空。燃料输入支持预置种类及“其他/手动输入”，展示质量/体积单位、自动推荐计量方式、C.1缺省参数和各参数来源；未知燃料不继承标准缺省值。
- 动态行区域使用响应式表单布局；完成燃料、电力、热力、过程及FGD新增/删除行的缩放验收。
- 标准库增加C.1～C.5只读入口：C.1～C.3从正式Canonical参数/因子读取；C.4/C.5从版本化Calculator蒸汽表读取；表内保留真实来源定位，蒸汽自动计算留给UAT01-B。
- 空白和显式0保持不同语义；既有Project可继续打开/保存；历史Record不重算、不漂移，Record生命周期未改。
- 未修改正式排放公式、Numeric Contract、Excel、PR #27、UAT01-B/RS03-B、Golden、Release或第二标准。

改动文件涉及标准Domain与Presentation、Catalog只读显示、缩放验收脚本、对应UI/Project/Catalog测试，以及Roadmap、TASK_STATE、HANDOFF和本报告。另将`uir04_manual_gui_acceptance.py`同步到分组树形校验面板和企业名称可选的新交互，避免人工GUI验收脚本继续使用旧列表API和旧必填预期。

## 3. 兼容与历史稳定性

- Project：继续兼容现有`form_state_json`；不新增破坏性Project migration；旧输入保持可读，未确认标准因子时重新计算会被阻断并提供可操作提示。
- Record：成功记录继续只读并保留原参数/结果快照；本包不重算或批量迁移历史Record。全量回归中的历史快照稳定性测试通过。
- 单位切换和日期编辑：标准缺省因子不适用时不会被错误用于计算；日期范围编辑的短暂无效状态不会永久清除用户选择的标准缺省来源。
- 公式：无改变；C.4/C.5只读展示不复制人工表数据，不改正式蒸汽数值或Calculator算法。

## 4. 测试与验证

- 聚焦：6个UI/项目/目录测试模块，83/83通过。
- 全量：`python -m unittest discover -s tests -t . -v`，250/250通过。
- Canonical：`python scripts/validate_canonical.py`通过，9 standards、12 sources、98 parameters、98 factors。
- 编译与依赖：`python -m compileall -q apps packages scripts tests`通过；`python -m pip check`通过。
- 数据库：`python scripts/initialize_databases.py --output-dir <temporary-directory>`通过，隔离创建catalog、user、records、projects四库。
- GUI/缩放：`python scripts/uir04_scale_acceptance.py --scale 1.0`、`1.25`、`1.5`均通过；覆盖多个动态区域添加/删除行及布局尺寸检查。
- 人工GUI验收：`python scripts/uir04_manual_gui_acceptance.py`通过，5个场景覆盖燃料与购电成功、煅烧计算、基准不一致集中阻断、有效非化石电力证明、企业名称留空成功；此次同步修正了树形面板读取方式及空企业名验收预期。
- Windows standalone：独立版构建、release目录审计、ZIP往返审计通过；`python scripts/smoke_standalone.py <artifact> --starts 2`两次隔离启动通过。
- `git diff --check`通过。PR提交后须核对Windows / Python 3.12 Merge-ref Full Tests与PR-head Standalone Audit的head_sha均为最新PR head；准确run和head不写入本报告以避免自引用提交，最终结论见PR Checks与交付报告。

## 5. 阶段状态与停止边界

GHG-UAT01-A：`IMPLEMENTED / AWAITING ACCEPTANCE`。UAT01-B：`NOT STARTED`。RS03-A USER UAT：`BLOCKED BY UAT01`；PR #27：`OPEN / UNMERGED`且未修改。RS03-B、Golden Freeze、Release Gate及第二标准未启动；GB/T 32151.34—2024仍为`NOT SUPPORTED`。不合并本包PR，等待独立验收。
