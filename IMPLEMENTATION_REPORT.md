# RS03 Excel正式闭环实施报告

日期：2026-10-08。状态：AWAITING ACCEPTANCE。用户授权执行步骤4，并接受合并PR #34作为依赖；另明确批准Canonical项目存储及projects.sqlite增量迁移。当前提交本包独立候选，不自行合并。

## 平台 / Contract 预检查

- 已实际核对工作树根、origin、fetch、main、HEAD与工作区；canonical origin为adgo07/GHGTOOL。从PR34合并后的main创建并快进任务分支codex/rs03-excel-workflow，未覆盖原checkout或用户参考文件。
- 最终运行代码及本地验证对象：`99a2038d265644d435782a541da45bd59ebe8280`。随后仅提交治理/报告文档；最新PR head与远端验证对象以PR Checks及构建provenance为准。
- 中央Frozen locked SHA保持`ee5feb0cc34dbd99790500fadd0c4c932e202a20`；本轮沿用已读Architecture V2.1、Numeric v1与Numeric Profiles v1，并读取当前ACTIVE Product Delivery Policy/UI Guide。没有升级baseline。
- MUST：分层；Excel与GUI同Canonical Input、Application、Domain Calculator与Result；正式成功追加不可变Record、blocked零Record；可变Project隔离；报告读取冻结快照；保持本仓p40/ROUND_HALF_UP、ambient independence与full-value exact comparison。
- MUST NOT：另建Excel算法、数值经float进入正式计算、Qt状态冒充公共Workspace Contract、报告查询当前Catalog重算历史、预览生成Record、展示修约回流正式结果。
- 本模块Canonical codec与可选导入证据是内部实现，不新增或修改中央公共Contract；Workspace/Record相关公共内容仍DRAFT，Excel Decimal交换仍OPEN / PARTIAL，不能据本包冻结它们。无需中央Contract变更。Carbon Profile保持ALLOWED PROJECT DIFFERENCE；无新增Frozen冲突。
- Standard Issue：无新问题；001～006既有解释保持不变。本包不改变标准公式、Resolver、适用范围或标准支持状态。用户此前提供的Excel禁用入口文字已被main的R2预览能力取代，本轮按最新明确授权实施RS03，不移植PR27旧V1。

## 业务行为与实现

1. R2先校验并预览独立核算单元，预览与GUI正式入口使用同一配置的Calculator。有效单元可明确保存为项目，无效单元保留错误且不保存为可计算项目。预览和保存均不生成Record；修改输入应修正原工作簿后重新预览并保存新项目。
2. AccountingUnitWorkspace末尾新增可选Canonical Input和ingress_provenance。迁移003只向projects.sqlite追加可空字段，兼容001/002旧GUI项目；Qt form_state继续只表示Presentation。模块内allowlist codec保留Decimal、日期、枚举、嵌套类型与证据引用，拒绝float、非有限数、未知版本/类型/字段及重复JSON键；损坏数据明确报错，不静默清空。
3. 项目重开无需原Excel文件。NumericCellEvidence在原始导入时冻结单元归属、原始/标准化词法字符串与工作簿哈希，保存时不重新读取已变化的源文件。正式UseCase把导入证据附入既有raw_input快照，项目后续变化不会使正式Record来源漂移；GUI默认raw-input结构不变，records.sqlite Schema不变。
4. 用户明确点击正式计算才由同一CarbonAccountingUseCase追加Record。再次成功新增记录，致命校验/Record保存失败不标记完成。记录已写而项目关联失败时明确提示已有记录，不自动重算；既有pending recovery补链接及适用结果，保留当前已保存输入和项目元数据。恢复u2记录时不回放临时导航，当前已保存u1保持，可下拉切换u2查看记录。
5. Canonical项目从新建核算页打开时路由Excel页面，避免将完整输入还原成空Qt表单。记录创建/查看信号复用现有Shell路由与共享Repository；未创建新的持久化入口。
6. 记录页新增Excel核算报告导出。Excel renderer只接收与Word相同的冻结ReportModel，按基本信息、B.1～B.9及来源说明输出；业务列保留，必要单位/来源带字段标签集中说明，动态行无固定15行上限。所有显示值为literal text，无Excel公式、浮点转换或二次核算；结果文件不是R2重导入模板或中央权威Numeric交换格式。
7. 导出复用已有通用report_export_history，追加XLSX、模板版本、SHA-256与补充信息，不改正式Record或增加数据库。燃料排放展示修复为既有两位小数策略，参数保持模型精度（例如0.0153）；来源中的已知内部标准/版本词改为业务文案。Word共享上述模型显示修复，不扩展Word分页功能。

例如：一个工作簿有两个有效单元和一个无效单元，预览零Record；保存两个有效输入后仍零Record。打开某单元点击正式计算，成功追加一条记录；再次点击成功再新增一条。核算记录的Excel报告读取各次记录自己的输入和来源，不随当前目录变化。

## 本地验证

以下均为本地Windows / Python 3.12.14执行，运行代码head为99a2038；TEMP/TMP/LOCALAPPDATA隔离、Qt为offscreen。日志位于忽略的build/step4/final-acceptance/logs及build/step4/logs，不把远端CI写成本地结果。

| 命令/检查 | 结果 |
|---|---|
| `python -m unittest discover -s tests -t . -q` | 334/334，442.353s，失败0、错误0、跳过0 |
| `python -m compileall -q apps packages resources scripts tests` | 退出0 |
| `python -m pip check` | 无依赖冲突，退出0 |
| `python scripts/validate_canonical.py` | 9 standards / 12 sources / 98 parameters / 99 factors，退出0 |
| `python scripts/initialize_databases.py --output-dir build/step4/final-acceptance/databases` | 四库隔离初始化，退出0 |
| `python scripts/uir04_manual_gui_acceptance.py` | A～E五场景PASS；自动化离屏执行 |
| `python scripts/uir04_scale_acceptance.py --scale 1.25` / `--scale 1.5` | 两种缩放场景PASS |
| `python build/usecase/characterization/compare_after.py` | 7组Outcome + 6类快照共13/13 exact一致；复用前次合成基线，不是独立标准Golden truth |
| `python scripts/build_standalone.py --output-root dist/rs03-acceptance` | Windows standalone构建通过 |
| `python scripts/inspect_release.py dist/rs03-acceptance/QingzhouCarbonAccounting` | 263个文件；catalog/manifest/范围审计PASS |
| `python scripts/verify_release_archive.py dist/rs03-acceptance/QingzhouCarbonAccounting` | 264个可见文件，ZIP往返PASS |
| `python scripts/smoke_standalone.py dist/rs03-acceptance/QingzhouCarbonAccounting` | 2次隔离启动PASS |
| `python build/step4/package_upgrade_probe.py` | 打包EXE真实升级旧projects 002→003；旧输入/指纹保留，新增可选字段为空，Record数量0 |

完整合成B.2～B.9总量仍为`369.5575954191666666666666666666666666667`，报告显示369.56。Core、Standards、Numeric、Resolver、Catalog/Record迁移及Frozen文件无改动。build-manifest source_commit为99a2038，数据库版本catalog=002/user=001/records=004/projects=003。

## 独立审查与视觉证据

- GPT-6 Luna / max子agent承担项目存储、UI工作流、renderer、全量回归及独立审查；原生computer-use尝试使用GPT-6 Astra / low。主agent复核数值门禁、冻结导入证据、来源归属、显示模型及实际打包升级。
- PR34经独立代码审查与60/60技术复核，用户接受后合并；其305/305与CI #171是历史依赖证据，不冒充本包验证。
- 本包独立审查未发现实现级阻断；定向53/53通过，包含真实SQLite双单元关联恢复、Catalog不可用仍可导出历史报告、Record及六类快照不漂移。独立摘要在build/step4/design/rs03-design-audit.md。
- Excel新页面1366×768和1440×960共8张Qt离屏图覆盖空态、完整预览、项目重开和正式核算。两尺寸均验证预览/保存零Record、重开输入与来源精确一致、正式计算一条Record及查看路由。1366×768纵向滚动13px，操作按钮可达；1440×960无须滚动。不是原生Windows鼠标视觉UAT。
- 完整报告样本11页已做style近似图检查，修复27列膨胀、重复基本表、标题和日期换行高度；动态125行、公式前缀安全及逐值/单位/来源保留有测试。Artifact-tool部署缺入口文件而无法导入，改用openpyxl/Pillow与系统字体作近似QA，最终样本无裁切标记；字体回退与Excel实际打印不由此证明。

## 限制与交付边界

原生computer-use截图、坐标及窗口激活受限，尝试已停止；只取得旧候选首页原生树。原生滚轮/动态布局/记录视觉、Excel/WPS实际打印、Word分页及长标题可读性尚未完成，离屏、style近似与启动smoke不替代这些证据。项目恢复的导航状态只保持最后成功保存的状态；待恢复Record在其正确单元中可查。

本包不新增算法/数据库/主要技术栈、不升级平台基线、不提供.qzproj，不启动RS04～RS06+；标准仍PARTIAL / NOT SUPPORTED。候选交付独立PR后停止等待验收，不自行合并。GitHub Actions属于远端证据，以最新PR head的合并集成测试与精确head standalone两个jobs为准；CI链接和最终状态追加到PR描述，不把本地成功当作CI成功。
