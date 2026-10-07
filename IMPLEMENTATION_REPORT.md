# 最新 main 集成验收与普通缺陷修复

日期：2026-10-07。状态：AWAITING ACCEPTANCE。步骤1已完成；步骤2的自动化和发布验证已执行，Windows原生鼠标/视觉与Word排版验收未完成，不宣布完整UAT或正式标准支持通过。

## 平台 / Contract 预检查

- 授权：步骤1（状态同步、Excel入口统一）和步骤2（集成验收、已确认普通缺陷小补丁）。不启动步骤3 UseCase、Excel正式写入或新标准。
- Git已确认实际工作树、origin和默认main；仓库为adgo07/GHGTOOL。开工fetch后的main：`124a16a6490d161bc2db8d1734e554454fca4ac6`；任务分支codex/main-integration-acceptance从该点创建。原checkout和用户未跟踪文件未覆盖。
- PF01 #30、UAT02 #31、RPT01 #32已合并；旧PR #27远端已关闭且未合并。本包只读核验，不关闭、重开或合并其他PR。
- 中央锁定SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`。读取锁定Architecture V2.1、Numeric Contract v1、Numeric Profiles v1及当前ACTIVE UI指南。不改变platform-lock.json或PLATFORM_BASELINE.md。
- MUST：分层、共用Domain Calculator、Decimal p40/HALF_UP声明Profile及ambient independence、成功Record不可变、显示修约仅作用Presentation。
- MUST NOT：显示值回流计算/正式比较、Excel另建算法、报告回查当前Catalog重算历史记录、预览保存Record/Project、将DRAFT称为FROZEN。
- 不定义或改变中央公共Contract。问题均为本地普通缺陷，无需改中央Contract；保留本仓Numeric Profile差异。
- Standard Issue预检查：001～006均RESOLVED；热力回归涉及既有005/006日期口径。未新增解释、修改公式、Resolver策略、适用范围或既有软件解释。
- 按用户要求，测试扩展、发布回归和辅助渲染由GPT-6 Luna、max子agent承担；主agent负责修复、边界判断及汇总。

## 实现内容

1. HANDOFF与唯一路线文件纠正PF01合并状态、Excel R2能力和PR #27状态。R2提供十张可见输入表模板、严格校验及逐核算单元只读预览；RS03正式写入/结果导出未启动。
2. Excel首页及导航改为“Excel 导入预览”，移除禁用式语义和NoFocus，说明预览不生成项目或正式记录。
3. Excel预览总量采用既有Presentation格式器，避免未经格式化的长Decimal字符串；内部精度与比较不变。
4. 构建manifest的Catalog版本从001修为实际002；发布审计比较manifest与真实数据库版本，测试验证故意写回001会被拒绝。
5. 辅助图发现首页已有记录时底部仍称“暂无核算记录”。改为中性提示，并增加有记录时不出现误导提示的回归断言。

## 新增集成测试

新增两组共9条，使用真实生产入口和隔离数据库。不是标准Golden Case；入口间一致不构成独立的标准公式正确性证明。

- Excel 6条：B.2～B.9映射；全活动预览与同Canonical Input正式Calculator的全精度结果、分项、参数/trace一致；坏单元隔离；错误元数据/缺表；OOXML NaN/Infinity拒绝；活动与实测参数十进制精度保留。
- GUI 3条：GUI与R2预览精确一致且预览不保存；重复成功新增两条SQLite Record而失败不改历史；Catalog不可用后GUI按钮仍从冻结Record导出报告、原记录和报告模型不漂移、导出审计增加事件。
- 报告样例QA：完整B.2～B.9输入经R2 importer/resolver、同一Calculator及显式SQLite Repository保存，再经软件报告模型/renderer导出B.1～B.9 DOCX。1条隔离记录、14张表、章节和关键字段结构检查通过；不是正式企业报告，也未证明分页通过。

## 本地验证

最终代码与测试checkpoint：`e1328f2ef0244f2ee9944d29ea79dfd72ca282dc`。最终重跑291/291通过（328.146秒；wrapper 340.437秒），exit 0；此前完整回归checkpoint `3af0a5788149cac7f44893e6c34fd1b9cea52ba0`已291/291通过（406.896秒）。后续治理文档提交不改生产实现。

Windows Python 3.12.14、PySide6 6.11.2、openpyxl 3.1.5、python-docx 1.2.0、PyInstaller 6.22.3。TEMP/TMP、LOCALAPPDATA及数据库均隔离；未触碰用户正式数据库、旧安装包或计算表/。以下均为本地执行，CI单列。

| 命令 | 结果 |
|---|---|
| `python -m unittest discover -s tests -t . -q` | 最终checkpoint 291/291通过，328.146秒，exit 0 |
| `python -m unittest tests.test_g03_shell tests.test_g08_delivery -q` | 18/18 |
| `python -m unittest tests.test_main_integration_excel -v` | 新增6/6 |
| `python -m unittest tests.test_main_integration_ui -v` | 新增3/3；最终首页断言已在291条全量中通过 |
| `python scripts/validate_canonical.py` | 最终checkpoint通过：9 standards / 12 sources / 98 parameters / 99 factors |
| `python -m compileall -q apps packages resources scripts tests`、`python -m pip check` | 最终checkpoint通过，无损坏依赖 |
| `python scripts/initialize_databases.py --output-dir build/integration-acceptance/databases` | 四库成功；catalog/user/records/projects：002/001/004/001 |
| `python scripts/uir04_manual_gui_acceptance.py` | 5/5；本次是offscreen自动场景，名称含manual不代表人工实测 |
| `python scripts/uir04_scale_acceptance.py --scale 1.0`及1.25/1.5 | 3/3；1366×768离屏几何检查 |
| `python scripts/build_standalone.py --output-root dist/integration-acceptance` | 最终checkpoint构建成功，65.655秒 |
| `python scripts/inspect_release.py dist/integration-acceptance/QingzhouCarbonAccounting` | 最终构建262文件通过 |
| `python scripts/verify_release_archive.py dist/integration-acceptance/QingzhouCarbonAccounting` | 最终构建263可见文件ZIP往返通过 |
| `python scripts/smoke_standalone.py dist/integration-acceptance/QingzhouCarbonAccounting` | 最终构建隔离双启动2/2通过，16.215秒 |

最终构建manifest的source_commit / pr_head_sha / tested_merge_sha均为e1328f2ef0244f2ee9944d29ea79dfd72ca282dc；manifest SHA-256为addadc6839d12a76f01343f2f407ba7d0fec05851f8c0265290a47971af480e0，EXE SHA-256为6616d202a774a1a2459c8d807981a8ba4adf3d9fcbf15ad5a0a50c41bf3debf6。后续治理文档head与此构建checkpoint有意区分。

日志在build/integration-acceptance/logs/，含命令、checkpoint、解释器和退出码。Qt六图/manifest在qt-render/；Word样例、输入、结构检查与渲染失败说明在report-qa/。均为ignored本地QA产物，不是正式用户数据。

首次边修改边跑的282条checkpoint出现1 failure（旧文案断言）、1 error（新增测试SQLite连接未关闭导致Windows临时目录清理失败）；修复后稳定checkpoint全量通过。非有限数fixture首次被openpyxl读取阶段拒绝，测试接受WorkbookFatalError或单元错误两种有效拒绝路径；未删除计算断言或放松容差。

深路径安装PySide6构建依赖遇Windows路径长度限制，换短路径隔离venv后成功。初次离屏图字体呈方框，只在QA脚本注册本机已有Microsoft YaHei UI、Segoe UI和Arial后六图可读，未改生产字体设置。

## 原始问题的验收边界

| 问题 | 最新主线与本包证据 |
|---|---|
| 滚轮误改、增行挤压 | UAT02滚轮/20行展开收起/scroll host几何回归通过；辅助图末行和添加按钮可见；原生鼠标待实测 |
| 新增过程/物料、0.35、产品碳说明 | 沿用已合并UI解释与层级，UAT/advanced details回归通过；不删除多过程能力或改变规则 |
| 来源可空、计算失败无反馈 | 来源提醒与缺值阻断分离、错误定位/隐藏结果现有回归通过；新增失败不写Record通过 |
| 脱硫UUID、C.2缺省 | C.2逐项选择/因子及未知旧输入阻断现有测试通过，未重新录入官方值 |
| 热力0.11 | PF01既有Canonical/期间Resolver修复及购入/输出热力集成通过，不在UI硬编码 |
| 所有数字最多两位 | Excel长小数已修复；主线仍保留小量、参数输入精度及科学计数显示，未宣布全局严格最多两位完成 |
| 核算记录复杂 | 普通详情/审计渐进展示测试通过；辅助图详情可读，左列表长标题在1440宽仍截断，留作后续观察项 |
| 标准库跳转、因子库 | PF01页面/导航回归纳入全量；完整原生视觉走查未做 |
| Word报告 | 快照导出、B.1～B.9结构/字段、导出审计通过；分页、横纵版切换、裁切未视觉验收 |

## 原生与视觉限制

- 最终e1328f2构建由GPT-6 Astra低推理子agent以独立LOCALAPPDATA实际启动。原生控件树确认中文首页/侧栏与预览不保存声明；Tab/Space成功进入新建核算，标题、标准与未计算状态可读。未完成Excel/记录页原生导航、完整表单填报或鼠标检查；详细结果位于build/integration-acceptance/native-qa/。
- 原生截图FrameArrived超时，恢复后仍window capture超时；点击报coordinate input geometry is unavailable。没有把离屏图冒充原生截图，拥有的测试进程已关闭。
- 六张1440×960 offscreen辅助图逐张查看：首页、初始核算、20行燃料上下部、Excel预览、记录详情；不能替代真实DPI、鼠标和Windows视觉UAT。
- documents渲染器因bundled LibreOffice缺失报soffice.exe was not found on PATH，未生成PDF/PNG，未逐页检查。DOCX含6个横/纵向分区，后续需检查分页、表宽、页码、裁切。本包未安装新依赖或调用用户Office。

## GitHub Actions与停止点

本报告成文时新PR尚未发布；提交后检查最新head GitHub Actions，以PR Checks为CI证据。不引用PF01历史Run 166替代本包CI，本地与CI证据分开。

交付候选后停止等待独立验收，不自行合并。RS03-B、RS04/RS05、Excel正式写入/导出、UseCase收口和生产InMemory隐式兜底整改均未启动。总体仍PARTIAL/NOT SUPPORTED；下一步补原生鼠标/视觉、Word分页及记录列表可读性验收，再启动后续工作包。
