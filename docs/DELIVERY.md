# G08 Windows 交付说明

本文档描述青舟温室气体排放核算软件 Windows V1.1.0 的 G08 交付候选包。它是便携式 `onedir` 目录，不是安装程序；G09 未实施。

## 当前生产与证据时点（2026-10-21 静态整理）

PR53已合并至main基线348077c；当前行业算法EXTERNAL.1、输入母版v11/2.9.0、payload6/封套2、新报告Schema3.1.0（无补充节点历史记录3.0.0）。本文后续PR46/52及v4/v10等内容是对应阶段的交付记录，不覆盖当前版本。

本节保留的PR53工程制品为[CI288](https://github.com/adgo07/GHGTOOL/actions/runs/39433861262)的head2dbb104（不是merge348或本轮文档head的精确新制品），全量1036/G08 18及包审计/2启动通过。此为PR53历史工程制品；后续N导航及首次新建优化的精确head、测量和CI以当前TASK_STATE、IMPLEMENTATION_REPORT与对应PR回执为准，本清单不重标旧制品。原生Office/鼠标/IME/人工DPI/企业样例/干净机/全产品许可履约与正式Release仍OPEN；工程制品不是商业交付许可。

## 版本与数据矩阵

| 项目 | 值 |
| --- | --- |
| 应用版本 | `1.1.0` |
| Canonical schema 版本 | `1.1.0` |
| Catalog data 版本 | `2026.10.08-electricity2023.1`（以 `data-source/carbon_accounting/catalog.json` 的 `data_version` 为唯一事实源） |
| Catalog / User / Records 数据库迁移 | `003` / `001` / `004` |
| Projects 数据库迁移 | `003` |

构建脚本会从 `data-source/carbon_accounting/catalog.json` 重新生成只读 `databases/catalog.sqlite`，并写入 `build-manifest.json`。发布前必须通过 `scripts/inspect_release.py` 的文件范围、哈希、数据库元数据和敏感文件检查。

## 构建

环境要求：Windows x64、Python 3.12 x64。开发环境中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[build]"
.\.venv\Scripts\python.exe scripts\build_standalone.py --clean
```

## 备份与整合注意

本版本尚无一键备份/恢复。关闭所有本软件实例后，复制完整用户data目录；存在user.sqlite或SQLite附属文件时一并保留。只备份records.sqlite无法恢复项目输入，不混用不同时间的记录库与项目库。恢复或降级前须检查版本兼容性并另存当前数据，不覆盖正在使用的数据。

PR35已整合PR36，交付版本组合为Catalog003与Projects003；旧head测试包不能冒充整合候选。

输出目录为：

```text
dist\QingzhouCarbonAccounting\QingzhouCarbonAccounting.exe
dist\QingzhouCarbonAccounting\databases\catalog.sqlite
dist\QingzhouCarbonAccounting\build-manifest.json
```

将整个 `dist\QingzhouCarbonAccounting` 目录复制到目标 Windows 机器即可启动。当前没有 MSI、安装向导、代码签名或自动升级服务；这是 G08 的明确限制。

## 启动与数据目录

双击 `QingzhouCarbonAccounting.exe`，或在该目录执行：

```powershell
.\QingzhouCarbonAccounting.exe
```

应用只读 Catalog 位于发布目录 `databases\catalog.sqlite`。用户数据与日志不写入程序目录：

- 核算记录：`%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting\data\records.sqlite`
- 项目与未完成输入：同一用户data目录中的`projects.sqlite`，项目恢复依赖此文件。
- 结构化日志：`%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting\logs\application.jsonl`

首次使用时，records与projects数据库会自动创建并执行已知迁移。数据库迁移只允许向前应用；未知的未来迁移版本会安全失败，不会自动删除或覆盖文件。

## 卸载与数据保留

便携式交付没有注册表安装项。删除发布目录不会删除 `%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting\data` 或 `logs`，因此历史记录和日志默认保留。若确需清理，请先关闭所有本软件实例并备份完整用户data目录（至少records.sqlite和projects.sqlite，包括存在的SQLite附属文件），再由用户手动删除上述数据目录；软件不会在卸载或启动失败时自动清理用户数据。

发布包不得包含标准全文、`计算表`、测试数据库、开发目录、环境文件或开发密钥。`build-manifest.json` 记录每个发布文件的 SHA-256 和大小，供验收与追溯使用；同时记录 `source_commit`（实际 checkout）、`pr_head_sha`（PR 精确 HEAD）和 `tested_merge_sha`（merge-ref 集成测试提交），避免把临时合并提交误认为 standalone 的源提交。

## 当前能力边界

- 计算链只覆盖 GB/T 32150—2025 通用规则和 GB/T 32151.34—2024 炭素材料生产企业模块。
- 其余计划标准只有目录与状态信息，不实现计算规则。
- 当前正式下载资源为 `resources/excel_templates/gb_t_32151_34_2024_appendix_b_v11.xlsx`（模板版本 `2.9.0`），SHA256 `b1e843a1eb8980c5a9bf4ee11d5b2369abcb89ebf4ca5b8659d8cccaefd166c4`；当前登记与锁定机制见下节，初始批准母版及去公式差异见 `docs/exb01/APPENDIX_B_INPUT_DESIGN.md`。下载复制受控字节，不重存。整工作簿经共享业务内核预览、明确保存Canonical项目、正式核算后追加Record；历史R2项目和记录可读，新R2文件导入取消。核算结果Excel导出取消，Word报告保留RPT02/PR39批准表式与分页，PR40联合验证。企业档案、层级、审批、.qzproj与云端不属于本包。
- 其他行业活动与上下游运输不猜算、不套算，不并入本标准ES/EI/ET；Issue016/PR53允许边界内其他活动的外部CO₂结果以用户明确选择作为独立软件补充，不新增行业算法、不自动纳入、不重算历史Record。
- 历史G08本地证据曾在 Windows 11 专业版 x64（版本 10.0.26200，Build 26200）完成 standalone 构建、审计和双启动验证；GitHub Actions 使用的 windows-latest 实际为 Windows Server 2025，仅作为 Windows/Python 3.12 CI，不宣称为 Windows 11 证据。Windows 10 22H2 未具备独立实机环境，未宣称已验证。

## 故障排查

1. **启动提示找不到 Catalog**：确认 `databases\catalog.sqlite` 与 exe 同在发布目录，重新运行构建脚本；不要把标准 PDF 复制进发布包。
2. **数据库迁移错误**：先关闭所有本软件实例并备份完整用户data目录（至少records.sqlite和projects.sqlite，包括存在的附属文件），保存 `application.jsonl` 后再提交问题；不要直接删除或手工修改迁移历史。
3. **无写入权限**：确认用户对 `%LOCALAPPDATA%\QingzhouEnergySuite\carbon_accounting` 有写权限，程序目录只需可读。
4. **查看日志**：日志是 JSON Lines，默认脱敏敏感字段；只收集与问题相关的时间段，避免上传用户数据。
5. **自动化测试环境**：`QT_QPA_PLATFORM=offscreen` 仅用于无显示器测试，不是生产启动参数。

## 构建后检查

```powershell
.\.venv\Scripts\python.exe scripts\inspect_release.py dist\QingzhouCarbonAccounting
.\.venv\Scripts\python.exe scripts\smoke_standalone.py dist\QingzhouCarbonAccounting
```


## 2026-10-17 商业依赖预检查（本地材料包，非销售放行）

本节记录2026-10-17当时的私有工程候选授权与材料；后续可见性以文末CI规则及Owner最新授权为准，不能据此推断当前仍私有或获得商业发布授权。本节来自真实Python3.12.14环境元数据；环境已安装不等于实际打包，最终实际包体清单须与该head构建manifest交叉核对。无购买许可、许可接受、正式专利/软著提交或对外分发。

| 组件 | 当前实际版本/元数据许可 | 使用方式与仍需交付核对 |
|---|---|---|
| Python | 3.12.14 | 自包含解释器；PSF许可及捆绑组件通知需随实际包核对 |
| PySide6 / Essentials / Addons / shiboken6 | 6.11.2；LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | 应用只使用QtCore/Gui/Widgets/Svg；wheel装有Addons不代表销售包允许全部模块，实际DLL/插件逐项核对。许可证/通知、对应库源码提供方案、替换/重新链接条件、用户条款均尚待发布前完成 |
| openpyxl / et_xmlfile | 3.1.5 / 2.0.0，MIT | 输入适配，须保留版权/许可通知；元数据未枚举license文件不能认为没有通知义务 |
| python-docx / lxml / typing_extensions | 1.2.0 MIT / 6.1.3 BSD-3-Clause / 4.16.0 PSF-2.0 | Word渲染/解析；lxml内嵌libxml2/libxslt等依其LICENSES继续核对 |
| PyInstaller / hooks-contrib | 6.22.3（GPL带打包例外）/2026.8 | 构建工具和运行bootloader边界分开；打包例外不覆盖第三方依赖许可，hooks许可文本单独留存核对 |
| packaging / altgraph / pefile / pywin32-ctypes / setuptools | 26.3 /0.17.5 /2024.8.26 /0.2.3 /84.0.0 | 构建环境组件，不把所有已安装工具都宣称在包内。具体许可见各版本dist-info原文 |
| iapws（历史选择） | 2026-10-16原017指定，未接入产品 | 已由2026-10-18批准的固定CoolProp/IF97实现取代；当前依赖、许可证据及开放项见下文B-HEAT章节 |
| LOGO / SVG / 模板 / 因子数据 | 本仓既有资源 | 本次不新增第三方字体/图标；现有权利链、标准表式及数据再分发权限仍需Owner按真实来源核对，公开下载不代表无限授权 |

官方原始依据：[Qt for Python商业使用](https://doc.qt.io/qtforpython-6/commercial/index.html)、[Qt许可与GPL-only模块](https://doc.qt.io/qt-6/licensing.html)、[Qt LGPL义务](https://www.qt.io/development/open-source-lgpl-obligations)、[PyInstaller 6.22.3例外正文](https://pyinstaller.org/en/v6.22.3/license.html)、[iapws发布许可](https://pypi.org/project/iapws/)。仅记录工程预检查；不将动态链接或可收费销售单独作为合规结论。面向客户的第三方通知/必要许可文本尚未完成，不宣称闭源销售资格已确认。

当前版本组合见requirements-build.txt，固定安装组合供复建，不改变pyproject支持范围；构建仍记录实际版本与来源身份。历史v6材料模板（当时）保留v2—v5原件，B.3—B.5各新增I—M共5辅助列和1说明行，母版下载仍验证后原字节复制。


历史包体实证（当时本地2368380构建，非当前交付包）：共267文件（manifest列266，manifest自身另计），自动收集13个Qt6 DLL和22个插件；其中`Qt6VirtualKeyboard.dll`及`PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll`被发现。原始PE import检查：只有该插件引用VirtualKeyboard DLL；应用源码没有VirtualKeyboard/QML消费者。依据[Qt 6.11原许可页](https://doc.qt.io/qt-6.11/licensing.html)的GPL模块列表，构建精确排除这两个未使用组件，包审计拒绝它们及未经放行的iapws，未替换GUI/物性实现，不影响原生Windows输入法代码路径；真实中文输入仍待人工验证。此原始预检查包不作为销售候选，原日志与清单仅保留本地。

原始包未发现LICENSE/COPYING/NOTICE文件；打包排除两文件只解决已发现的未使用GPL模块混入，仍不表示全部许可义务完成。最终实际包组件/哈希、公开来源和未完成文本/源码提供/替换条件由本包报告逐项记录，发布前继续补齐第三方交付材料。

CI251补充：实装Qt6.12将同一未使用VirtualKeyboard DLL收集到`PySide6/Qt6VirtualKeyboard.dll`；原审计成功拒绝漏排组件。构建排除列表只增加这个实证精确路径，旧root DLL/插件路径及边界保护保留。[Qt6.12官方许可页](https://doc.qt.io/qt-6.12/licensing.html)仍列VirtualKeyboard为GPL模块。未改依赖策略，6.12实包仍须独立审计；两种路径不等于允许任意Qt目录批量删除，原生IME仍NOT_RUN。

F02历史受控来源修订（PR49已合并）：当时下载v7/2.5.0，SHA e4203f0d5bf9133df5b6abde3bfede8b82905d11d795cd29ba590ea60f7ebb5a。运行python -B -m scripts.project_appendix_b_v7 --write机械生成，省略--write核原字节一致；以固定旧v6为输入，仅变三个材料表XML的下拉/说明，旧v2—v6保持。来源统一计算值/实测值，方法独立；2.4旧方法来源文字仅输入兼容，新2.5拒绝该文字。当前候选需新head CI实包审计；[CI252固定历史摘要](ci/CI252_SUMMARY.json)只背书PR49阶段的d5205f5，不是PR50或后续新版包证据，原生v6/v7 Office/IME仍OPEN，许可履约/商业发布未放行。


历史B-FGD候选（当时）下载v8/2.6.0，SHA a8ee7272ee4ac3665997f7ce93f78e8fd78c58cb4215ee477c01b76b6f87dff4；`python -B -m scripts.project_appendix_b_v8 --write`以固定v7为输入，仅机械修改B.7 XML，新增I/TR来源及可选企业设施编号，旧v2—v7原字节保留。I/TR实测空白不补缺省，标准缺省必须明确选择且同次Resolver真实适用。独立fgd.json投影由`python -B -m scripts.project_fgd_rules`核验。产品仍不含标准全文/iapws/VirtualKeyboard；本包最终head CI实包、原生Office和商业履约状态分别记录，不借旧制品放行。


PR50旧脱硫输入兼容边界：旧FGD_V1项目仍可打开、保存未完成输入；读取本身不新增设施/批次身份、不回填或重算历史Record。正式计算时，同一旧分组各组分须共用同一整剂净耗量，按显式单位归一后精确比较；例如同组10t与20t现明确拒绝并零新增Record，需先核实真实批次和整剂用量，不静默统一或自动拆批。10t与10000kg代表同量，资料引用不同不当作数量不同；不同已明确分组分别核算。此为已批准同组分母校验补漏，原排放公式、来源集合与Numeric不变。历史Record/Word继续只读冻结快照，不因新校验或Catalog升级漂移。旧无I/TR来源列的B.7 schema保留已批准的适用空白约定并明确告警，v8显式实测空白不回落。

## B-FUME交付候选增量

Issue020监测分段完整链采用CAR-SM01-2026-10-18-FUME.1；输入codec4兼容1/2/3，无数据库迁移。新模板v9/2.7.0仅改B.6，旧v2～v8原字节保留并随包受控登记；Word布局3.0.4冻结分段与覆盖说明。不得将有缺口的已覆盖合计称完整期间，不补零或年化；旧无区间输入不补造全年证据，升级副本缺区间仍拒绝正式计算。历史Record/Word不回填重算。精确受验head/新CI/实包以本包PR及docs/ci/B_FUME_SUMMARY.json固定对应关系为准，PR50已验收包不背书本包。原生Office/鼠标/IME/人工DPI、企业样例、干净目标机和商业履约仍OPEN。


## B-HEAT 固定物性实现（工程验证，不是商业发布）

Owner于2026-10-18原始消息01a14ee7-32ba批准验证后接入Python CoolProp8.0.0的明确IF97后端；固定NumPy2.3.3，revision ae81610e7d23efc57f9d051c8e70a4d66e87537f。原017指定iapws作为历史决定保留，当前具体实现受控替换；不安装/打包iapws、不回旧表，不更改IF97方法/相态范围或Carbon p40排放算术。

B-HEAT当时母版v10/2.8.0仅演进B.9；旧v2-v9保留原字节。v10最终候选SHA705a9326f6910bceaad34ce955975a6150731fa8ed2b50ddfe8c2c5188deb729。14份受控通知/来源文件在resources/licenses/steam_if97，来源清单记录两固定wheel/sdist SHA与原始来源；构建/包审计核原文件字节，不把MIT标签等同全包许可。CoolProp顶层/IF97及内嵌header依其各自MIT/MPL2/BSL/BSD等文本；NumPy实际wheel另含OpenBLAS/LAPACK及GPL3 WITH GCC Runtime Exception3.1原文，不能概括为全部MIT/BSD。MSVCP140随两wheel实际出现，VC再分发依据及全产品第三方商业履约继续OPEN。

F原始调查及REV2分别持久保存在docs/ci/B_HEAT_IF97_CANDIDATE_RAW.json和B_HEAT_IF97_CANDIDATE_REV2_RAW.json，原SHA保留。C独立核固定sdist的include/CoolProp/fluids/Helmholtz.h与Helmholtz.cpp的ENABLE_CATCH guard、root CMake CatchTestRunner的PRIVATE define/include、Python模块目标；结合实际wheel文件/符号检查，限定multicomplex为TEST_ONLY_NOT_SELECTED_RUNTIME。完整未公开编译命令/stripped符号限制保留，不能仅凭strings阴性作绝对证明；若分发其源码/测试或换配置，原NIST README指向的缺失LICENSE及foreign rights澄清仍OPEN，不能由CoolProp顶层MIT覆盖。

物性子Profile GHGTOOL_COOLPROP_IF97_PROPERTY_V1采用binary64，非Decimal40物性精度。原规范MPa/℃、实际库工作Pa/K binary64词法、库原始J/kg输出词法、SAT Q=1、采用Decimal焓、实际phase、方法/版本/revision/依赖分开冻结。API不提供IF97区号，不伪造region。官方参考容差仅为conformance，30MPa700K仅库验证，不表示产品接受超临界流体。正式自动仅干饱和或低于临界压力的合法单相过热，实际API域错误不放行、不外推；known合法路径不依赖自动参考。

本节历史阶段仅私有CI/工程候选验证；不CU、不商业发布，不以作者专属/本地/包内程序化验证替代正式客户履约或原生Office/IME/DPI/干净机验收。最终实际包身份和测试统计以本轮实施报告/仓内CI摘要为准。

工作状态门禁同时约束原输入和实际binary64 Pa/K：实际Pa须严格低于临界Pa，过热实际K须严格高于同压库Tsat并通过气相校验；极微小原差在工作值折叠时拒绝，不夹值/加epsilon/抬温。此为既有017原则落实，Profile、公式和known路径不变；24901e1的旧CI即使通过也不背书该修复，最终新head须重新CI/精确包。

## PR52-F01 报告单位退修与历史证据身份

PR52-F01当时输入模板为v10/2.8.0（烟气v9/2.7.0、脱硫v8/2.6.0为更早历史阶段）；当前模板见上文v11登记。CI280实际包为321份manifest文件、ZIP322份文件，仅背书fca产品代码。796文档回执的技术PASS因共享B.9 Pa/K投影错误被撤回，当前定向修复及后续CI/精确head实包以TASK_STATE和IMPLEMENTATION_REPORT为准，旧267文件包和CI280不得背书新补丁。压力/温度只由同Record冻结规范值或明确单位的原值显示转换到MPa/℃；K→℃减273.15，不重算物性，不回写Record，旧方法记录报告兼容保留。


## 现有交付验证清单（本节正式交付门禁全部 OPEN）

本节只整理现有交付门禁与证据出口，不启动RS04/RS05、不建立新路线、不新增标准解释或公共Contract。中央Frozen锁仍为 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`，适用UI指南为ACTIVE v0.2；本次文档整理不涉及中央公共Contract变更。相关既有Standard Issue016/017/018/020沿用，不改变软件解释。待验项由后续获授权的验收执行者逐项记录，未取得相应版本原始证据之前保留OPEN。

### 模板与包体身份锁定

- 运行时注册以 `packages/excel/templates.py` 的 `APPENDIX_B_TEMPLATE` 为准：模板ID `GHGTOOL_GBT_32151_34_2024_APPENDIX_B`、版本 `2.9.0`、资源v11及上文SHA256；当前工作簿包含B.1～B.9与“软件补充”。`ExcelTemplateService.read_bytes()`先核摘要，`copy_to()`直接写已核字节，不经openpyxl重存。填写并经Office保存后的工作簿有自己的哈希，导入按已登记版本的固定表头/合并区域/说明识别，不要求与空母版哈希相同。
- 历史资源v2～v10继续按各自固定SHA受控保留；它们与v11的实际包内字节由 `scripts/inspect_release.py` 的 `TEMPLATE_SHA256_BY_PATH` 核对。历史格式可读不等于恢复R2新下载/新导入，也不等于每个历史版本已通过当前Office验收。wheel/sdist/隔离安装资源的字节核验入口为 `scripts/verify_distribution_templates.py --output-dir <证据目录>`，输出 `proof.json`、构建/安装/资源日志及wheel/sdist摘要；本次交付清单整理子任务未运行。
- 应用 `1.1.0`、Catalog data/schema、四库迁移与固定依赖以实际候选 `build-manifest.json`、Canonical来源、`requirements-build.txt` 和实际环境记录交叉核对，不能单靠应用版本号区分包。构建记录 `source_commit`、`pr_head_sha`、`tested_merge_sha`；本地缺省三者均为checkout，CI的 `QZ_PR_HEAD_SHA` / `QZ_TESTED_MERGE_SHA` 应保留真实身份，不伪填为相同提交。
- Manifest对所列文件记录SHA256/大小但不列自身；验收另记manifest文件及整个实际ZIP的SHA256、文件大小、artifact/run/job ID与下载来源，核对包内路径集合和每个文件摘要。文件数是实包结果，不把历史267/322等数量当固定验收值。包内模板、规则、报告布局、物性依赖与许可通知须按该候选审计；`inspect_release.py`检查通过不替代人工许可履约结论。

### 待验场景与证据出口

| 门禁 | 当前状态 | 执行范围与应保留证据 |
|---|---|---|
| 最终候选构建、审计、双启动 | OPEN | 待最终产品版本锁定后，以其代码head确认既有CI/本地证据是否适用；保留精确命令、环境、退出码、通过/失败/跳过数量、完整日志摘要、manifest与ZIP摘要及真实provenance。验证入口为上文build、inspect、smoke；当前研发精确head工程候选CI即使已执行，本节正式交付门禁仍须单独核定，不借旧制品或研发CI宣布Release放行。 |
| 原生Excel保存回导 | OPEN | 在实际候选下载v11，核空母版字节；记录Excel完整版本/位数，填写B.1～B.9及可选独立补充，另存/关闭/重开后回导。覆盖中文文本、文本数字/小数/科学记数、空值/零/日期/百分数、单位、来源与错误输入；对照批准语义，核预览不写Record、明确保存项目后正式核算才追加Record。保留原始下载、填写前后及Office另存文件的各自SHA、步骤、截图、导入诊断和结果对照。不得要求Office保存后仍等于母版字节。 |
| 原生WPS保存回导 | OPEN | 与Excel分列应用版本、文件及结果；验证固定结构、下拉、插入业务行及回导，不用Excel通过代替WPS通过。PR46/v4旧head回导仅属历史证据，不外推v11。 |
| 原生Word查看与分页 | OPEN | 从同一冻结Record导出，记录Word版本与Record/报告身份，核中文、附录B表式、分页及补充说明；记录DOCX摘要与可脱敏截图。报告只消费冻结快照，验收不得查询现Catalog补算历史。 |
| 中文IME、鼠标与人工DPI | OPEN | 记录Windows版本、原生中文输入法版本、显示缩放/分辨率；检查中文企业名/中文路径、输入法组合与候选上屏、鼠标导航/滚轮/弹层、长表单错误定位，以及100%/125%/150%下可达性、截断与焦点。保留逐场景操作及截图；Qt离屏/合成鼠标/自动像素等价与缩放测试均不能替代本项。 |
| 企业样例闭环 | OPEN | 仅在后续明确授权和资料范围内使用真实或经批准脱敏企业样例，独立核实期间、边界、主要活动、来源与单位，完成GUI/Excel→Canonical项目保存/恢复→正式Record→Word。记录样例授权/脱敏身份、批准依据与独立期望值、差异及复核人；不以当前Calculator输出反造真值，不将客户原件/标准全文上传公开仓库。合成性能夹具不能替代企业样例。 |
| 干净目标机（Windows 10/11分列） | OPEN | 按下述步骤验证无开发环境启动、首次初始化、完整业务闭环与重启恢复；记录系统版本、标准用户权限、环境清单、包摘要、操作/日志、失败与修复复验。Windows Server CI不能代替Windows 10/11实机，开发机成功不等于干净机。 |
| 第三方交付履约与正式Release | OPEN | 对实际包内组件、许可文本/通知、对应源码/替换条件及VC再分发等逐项收口，保留Owner决策与正式验收；现有材料预检查、仓库公开、工程包通过均不构成商业交付完成。 |

干净机执行顺序（待后续授权执行）：

1. 固定验收候选ZIP/manifest/代码与CI身份，先核下载文件摘要；分别记录Windows 10/11系统版本、位数、权限及未安装Python/开发工具的环境事实。Office场景另记是否安装及其具体版本。
2. 完整解压到标准用户可读的中文路径；正常启动，不设置 `QT_QPA_PLATFORM=offscreen`。核首次Catalog读取与独立用户data目录初始化，程序目录不落用户库。
3. 用获准样例执行当前模板下载/保存回导、预览、项目保存、正式核算、记录查看及Word导出；错误输入应明确阻断且不生成正式Record。重复成功核算应新增Record，不覆盖上一条。
4. 正常退出后再次启动，核未完成输入/项目恢复、旧Record只读与导出一致；在关闭所有实例并备份完整data目录的前提下检查复制交付/数据保留，不破坏现有用户数据库。
5. 汇总每个系统/Office版本的通过、失败、未执行及原因，附包/模板/样例/报告/日志摘要；缺项继续OPEN，不以自动化冒充原生操作，也不据本清单宣布SUPPORTED。

验收证据随当前工作包的 `IMPLEMENTATION_REPORT.md` / `TASK_STATE.md` 及对应PR回执索引；原始日志和大文件在获准落点保存，只在仓内记录脱敏摘要、相对路径或受控链接及SHA256，不写机器固定路径。本次交付清单整理子任务仅静态阅读注册表、构建/审计脚本与既有文档，未运行测试、构建、性能测量、原生Office/桌面交互或企业数据验证。本节所列正式交付门禁通过数量为0，状态全部OPEN；同一工作包的N研发性能采样、回归及工程候选CI执行结果另以当前TASK_STATE、IMPLEMENTATION_REPORT与对应PR回执为准，不将研发验证等同最终产品Release门禁通过。

## GitHub Actions 费用边界与 CI 节约

本节是开发执行规则，不是账户预算已设置的证明。Actions零付费预算及超额停止配置须由Owner在GitHub账户端实际核实；仓内文字不能替代网页/API证据。本地规则维护不自动修改workflow、触发器、过滤条件或required checks。

1. **可见性与费用边界。** 可见性遵循Owner最新明确授权，当前仓库已公开；未经Owner明确授权不得擅自切换可见性、提高Actions付费预算或升级套餐以绕过额度。仓库公开不授权上传用户资料、客户数据或标准全文。额度不足不是自行付费的授权。
2. **本地先验，稳定批次再push。** 先完成本地定向测试和受影响的必要回归、生成物/来源哈希/依赖检查，处理已知失败后再推送可评审的稳定批次。不逐个小补丁触发Windows全量；本地仍可保持小提交，commit频率与push频率分开。不得为省用量跳过必要验证。
3. **先查同head已有运行。** push或rerun前查询对应head的既有运行和实际状态，复用有效证据，运行中先等待；已成功且无代码/环境/依赖或其他相关变化时不无变化rerun。失败先读完整日志、定位原因；需要重试时记录原因并选择满足验收的必要范围，不机械反复全量重跑。
4. **代码、文档、制品身份分列。** 文档/证明回执与业务代码head分开记录，制品同时保留实际source_commit、pr_head及tested_merge身份。仅文档变化可保留对应产品代码的既有证据，但不能把旧CI/制品改标为新head，也不能据此绕过required checks；正式合并须核实当时实际head与保护规则。
5. **按实际影响分类，不能只看扩展名。** Mapping/规则定义、Canonical来源与资源、模板、生成器/构建脚本、依赖/锁定文件、workflow及其来源绑定或定义哈希可能影响业务或交付，不能一概视为“纯文档”跳过。先分析影响并完成相应回归/机械重生/包审计；若拟调整CI过滤或触发策略，须另按当时任务授权和保护要求验证，本节不直接实施该调整。
6. **额度不足继续本地，不伪造闭环。** 继续可执行的本地修复、必要测试和文档整理，如实记录本地命令、通过/失败数量、未执行CI及原因、待补head与产物。保留CI缺项，不冒称全量或发布验收已完成，不用付费绕过，也不以本地通过代替要求的GitHub Actions证据。
7. **保留必要交付与证据。** 发布制品、精确版本构建、必要验证和独立验收证据继续保留；不得为省存储擅删、覆盖或缩短所需证据。复用证据仍须确认head/环境/范围适用；清理或调整保留策略须在明确授权内实施，不破坏可追溯性。
