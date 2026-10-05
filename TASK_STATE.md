# TASK_STATE

状态：CURRENT STATE；更新：2026-10-05。

## 当前工作包与基线

- 仓库：adgo07/GHGTOOL；origin 已核实为 https://github.com/adgo07/GHGTOOL.git。
- 工作包：GHG-UAT01-A — 普通核算录入与错误反馈体验修复。
- Base / 开工时最新 origin/main：`058d176a8a461b758db1a1d62395b032889d9b2a`（已执行fetch复核，main未前进）。分支 `codex/ghg-uat01-a-entry-usability` 从该main创建；开工时工作区干净。
- 平台锁定：platform-lock.json SHA-256 为 BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0；中央锁定 SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20 未升级。
- Contract预检查：Architecture V2.1、Numeric Contract v1、Numeric Profiles v1为locked Frozen；其余适用公共Contract维持原DRAFT / NOT FROZEN状态。本任务不涉及中央公共Contract，不修改baseline。
- Standard Issue：未改变标准解释；未新增标准问题；沿用4条已登记RESOLVED项目执行口径，非官方勘误。GAP-009继续为非阻塞provenance debt。
- PR #27保持OPEN / UNMERGED且未修改；UAT01-A使用独立分支和新PR。

## 实现状态

- UAT01-A：`IMPLEMENTED / AWAITING ACCEPTANCE`。
- 普通核算采用单一“计算排放量”动作；Domain一次返回问题，问题面板按必须修正/提醒及排放源/实例/字段组织；致命错误不生成伪结果或Record。
- 企业名称可选；简化普通层边界和专业控件；动态录入行使用自然布局；燃料输入整理了种类、单位、缺省/计算/实测来源与自定义燃料路径。
- 标准库增加C.1～C.5只读入口：C.1～C.3读取正式Canonical参数/因子，C.4/C.5从版本化Calculator数据展示；没有修改公式或标准数值。
- 旧Project可读取和保存；既有正式Record继续只读快照，不重算、不漂移；无破坏性migration。
- 本包不实施Excel、蒸汽自动计算、UAT01-B/RS03-B、Golden、Release或第二标准；GB/T 32151.34—2024仍为 `NOT SUPPORTED`。

## 本地验证

- 聚焦命令：`python -m unittest -q tests.test_g06_page tests.test_uir02_source_cards tests.test_uir03_advanced_details tests.test_uir04_finalization tests.test_accounting_projects_ui tests.test_g04_catalog`；83/83通过。
- 全量命令：`python -m unittest discover -s tests -t . -v`；250/250通过。
- Canonical：python scripts/validate_canonical.py 通过，9 standards、12 sources、98 parameters、98 factors。
- Canonical：`python scripts/validate_canonical.py`通过，9 standards、12 sources、98 parameters、98 factors。
- 编译：`python -m compileall -q apps packages scripts tests`通过；依赖：`python -m pip check`通过，无损坏依赖。
- 隔离数据库：`python scripts/initialize_databases.py --output-dir <temporary-directory>`通过，catalog/user/records/projects四库均创建。
- GUI缩放：`python scripts/uir04_scale_acceptance.py --scale 1.0`、`1.25`、`1.5`均通过，包含动态新增/删除行布局验证。
- Windows standalone：构建、release目录审计、ZIP往返审计通过；`python scripts/smoke_standalone.py <artifact> --starts 2`两次隔离启动通过。
- `git diff --check`通过。GitHub Actions exact-head CI待独立PR创建后核验，不引用旧head结果。

## 治理状态与停止点

- UAT01-A：`IMPLEMENTED / AWAITING ACCEPTANCE`；等待本包PR latest-head Windows CI与独立验收。
- UAT01-B：`NOT STARTED`。
- RS03-A USER UAT：`BLOCKED BY UAT01`；PR #27：`OPEN / UNMERGED`且未修改。
- RS03-B：`NOT STARTED`；标准仍为 `NOT SUPPORTED`。
- 不合并PR；latest-head CI和独立验收完成后停止。
