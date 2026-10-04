# GHG-RS02-B — Result Explanation & Record Experience Closure

状态：实现与本机可执行检查完成；PR #26 latest-head Windows CI已通过，等待独立最终验收。RS03未启动；标准状态 NOT SUPPORTED。本报告不写入自身所在提交的Head SHA，最终检查状态见[PR Checks](https://github.com/adgo07/GHGTOOL/pull/26/checks)。

## 1. 基线与平台预检查

- 仓库：adgo07/GHGTOOL；origin：https://github.com/adgo07/GHGTOOL.git。
- Base / 执行开始时最新 origin/main：781d40163495af68ea1c110a8dda8896861d70c6，含RS02-A / PR #25合并结果。
- 分支：codex/ghg-rs02-b-result-explanation，从上述最新main创建；工作树开始时干净。
- platform-lock.json SHA-256：BE9052155BBCAE94C782E2C7BDBAA384358CC605C27E81C5BF62A2957247FDD0；中央 locked SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20未改动。
- 按locked SHA确认Architecture V2.1、Numeric Contract v1、Numeric Profiles v1为相关Frozen Contract；Workspace/Attempt/Record/Result v1仍为DRAFT / NOT YET RELEASED。本任务不涉及中央公共Contract，不改baseline或platform-lock。
- 沿用4条历史RESOLVED Standard Issue，不改变标准原文解释，不新增标准问题；GAP-009继续为不阻塞实现的provenance debt。

## 2. 实际改动

- 普通结果摘要用中文分别表达直接排放、购入/输出能源形成的净间接排放、包含间接排放的总量；计算成功后滚动到结果卡片。ET/ES/EI及内部ID保留在专业信息中。
- Record详情重组为只读业务视图：基本信息、核算结果、标准报告数据、活动数据和证据、参数/因子、数据质量/提示及默认折叠的专业Trace。
- B.1显示直接排放与含间接排放总量；B.2—B.9从选中Record自己的Input / Calculation / Trace / Reporting / Parameter快照展示逐项业务值、实例小计、依据和来源。无纸质报告复制或导出。
- 多实例结果按稳定业务实例分组；Parameter Snapshot与Trace使用精确实例前缀匹配。新增加 graph-1 与 graph-10 的回归，保证相似编号不串用。
- 新建核算结果“查看正式核算记录”通过精确record_id导航到对应Record。Record中显示的Project关联注明是当前可变工作区关系，并非不可变Record Snapshot。
- 计算指纹与报告指纹分离：纯报告资料变更保留当前计算结果，提示需重新计算新增Record以固化报告内容；影响计算的输入仍使结果过期。
- 月度/自定义周期可成功计算、保存Record，同时单独显示不符合年度报告周期要求；不会显示为核算失败。
- 历史Record只读读取自身快照，不使用当前Catalog补值或运行新Calculator。Present、Empty、Legacy missing、Corrupt四种快照状态有不同提示；不重算、不漂移。
- 汇总核对只比较持久化CalculationResult与Trace；多实例分组小计对照已存计算行。软删除与审计流程没有改变。无新Record/Project迁移。
- 治理同步：Roadmap将结果解释和历史Record标为已实现但待最终门禁；CORE_CHECK Matrix更新为26行、OK 24、GAP 0、later-stage 2（RS03、RS04）、独立N/A 0；Coverage Audit重新分类为EXISTING 13、DERIVED 1、SOFTWARE_DATA 11、ENTERPRISE_OFFLINE 1、LATER_STAGE 1；UI Audit记录GHG-UI-001/002/005闭环。没有修改GAPS、Canonical、Calculator公式、platform-lock或Frozen Contract。

主要代码与测试文件：packages/ui/record_experience.py（新增）；packages/ui/pages.py、packages/ui/carbon_material_page.py、packages/ui/field_specs.py、packages/ui/shell.py；packages/persistence/records_repository.py；packages/standards/carbon_material.py；tests/test_rs02_record_evidence.py、tests/test_accounting_projects_ui.py、tests/test_g06_page.py、tests/test_uir04_finalization.py。

## 3. 兼容、汇总核验与历史稳定性

- Old Project：继续沿用既有form_state；不新增或执行破坏性Workspace/Project migration。纯报告资料变化不会误判为计算值陈旧。
- Old Record：按已保存内容呈现。缺失Trace、缺失报告快照、合法空快照和损坏快照不会通过当前Catalog/Calculator补值。
- Project→Record：精确记录ID打开新Record；普通列表不暴露内部标准ID或原始状态enum。
- Multi-instance：稳定过程/能源来源身份独立显示；精确前缀防止graph-1误匹配graph-10。
- Aggregation verification：Record detail只核对已保存计算结果与Trace汇总；逐实例小计逐项与存储计算行对比。不触发重算。
- 历史Record和软删除/审计没有写入更新；生命周期语义未变。

## 4. 测试与验证

- 定向：python -m unittest tests.test_rs02_record_evidence tests.test_g06_carbon_material tests.test_g02_persistence tests.test_g05_multi_electricity -v；45/45通过。覆盖只读快照视图、B.1/B.2与依据、四类快照状态、年度资格分离、多实例身份/聚合、防串号、Calculator回归、数据库构建/逻辑重建/迁移幂等和快照重开。
- 全量：python -m unittest discover -s tests -t . -v；发现139项，128项通过；11个PySide6测试模块在导入时因ModuleNotFoundError: No module named PySide6失败。本机全量测试未完成，不将导入错误计为通过；Windows/Python 3.12 CI承担这些Qt UI测试。
- Canonical：python scripts/validate_canonical.py 通过，9 standards、12 sources、98 parameters、98 factors。
- Compile/dependency：python -m compileall -q packages tests通过；python -m pip check通过，无损坏依赖。
- 数据库：定向持久化测试通过四库创建、Catalog逻辑重建、迁移幂等与Record快照重开；未增加迁移。
- GUI：本机缺PySide6，不能执行Qt UI acceptance；Windows latest-head CI已运行全量测试及UI acceptance并通过。
- git diff --check提交前通过。
- GitHub CI：PR #26 latest-head 的 Windows/Python 3.12 Merge-ref Full Tests（245项）与 PR-head Standalone Audit 均通过；精确head与run链接见PR Checks。后续若推送新提交，必须重新核对新latest-head的两项结果。本报告不把自身提交SHA写回正文，避免自引用提交。

## 5. 阶段状态与停止边界

GHG-RS02-B实现与latest-head CI已完成，当前等待独立最终验收。RS02在独立验收通过后可进入最终门禁；RS03 NOT STARTED；PR不合并；GB/T 32151.34—2024仍为NOT SUPPORTED。
