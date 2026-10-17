# PR46 燃料B1与电力B实施报告

日期：2026-10-17。代码实施已完成，等待最终运行汇总与源会话独立验收；不自动合并PR46、不关闭PR45。最终HEAD及GitHub执行结果以[原PR46](https://github.com/adgo07/GHGTOOL/pull/46)最新验收证据与检查为准。本报告明确区分提交时已结束和仍在运行的验证。

## 范围与平台 / Contract预检查

实际origin为`https://github.com/adgo07/GHGTOOL.git`，使用原PR46分支`codex/ghg-standard-input-unification`，已fetch并核对main `d0c26351200099a8e62c8adabadac266c77f7c8c`。已验收基线为`9d74e8a032f0bf2e6fa525deffea59f9172f883c`；其705/705与CI242仅为历史基线，不用于证明本轮新增范围。

中央锁定`ee5feb0cc34dbd99790500fadd0c4c932e202a20`不变，读取Architecture V2.1与Numeric Contract v1 FROZEN适用约束及当前ACTIVE UI指南。适用MUST/MUST NOT：分层、Decimal40/HALF_UP项目Profile与环境独立性、显示不回流、精确比较、可变Project与不可变Record分离、历史快照不随Catalog漂移；不得升级Frozen baseline或复制审阅引擎成为运行真值。本轮无中央Contract冲突或修改，无数据库迁移、公式/Numeric/标准范围改变。

涉及既有Standard Issue010/011/014/016及燃料来源决定；三层事实/技术判断/软件决定保持分离。表5是统计因子口径，不重标业务属性；只追加精确CONVENTIONAL购入分支，原FOSSIL分支与稳定ID保留。Owner直接批准完整三项：v5兼容接线、电力正式来源资格、燃料B1收口。先前自动审批拒绝的操作均未执行，改为可审阅补丁后获得本线程具体完整授权，现已正常应用。

不采用材料/过程/烟气/蒸汽R11后续规则，不实施N，不扩Word排版，不增加结果Excel导出，不启动computer use。原主目录用户修改及PR47原工作树未覆盖。

## 实际实现

1. **共享规则与真实资格**：`packages/core/business_field_policy.py`抽出完整字段求值，候选与生产共用来源资格、默认、锁定及非法来源纠错。`scripts/project_fuel_power_rules.py`机械投影五字段至`resources/business_rules/fuel_power.json`，无数值复制或第二份可编辑名单。Schema/HTML/审阅compact仍为开发工具。缺失/篡改资源明确失败，无旧规则兜底。
2. **Resolver证明**：`packages/core/parameter_resolution.py`保留多绑定关联，区分VERIFIED/ABSENT/AMBIGUOUS/PENDING；资格来自当前所选Factor、参数、来源表、审核、标准与适用期间。旧构造器缺证据为PENDING，不伪造ABSENT，不用来源字符串或bool授予资格。Application与Catalog Repository提供已核验关联；生产标准适配输出实际上下文。
3. **燃料闭环**：GUI/Excel/Domain共用来源资格；DIRECT新对象默认MEASURED且允许CALCULATED，LHV/FCh仅适用缺省或MEASURED。自定义不借目录缺省。同身份确认保留；身份、质量/体积路径、来源草稿独立；非法旧来源仍待更正。Escape取消未确认名称，不换身份、不清参数。
4. **电力闭环**：五表分组从同一资格表达读取，真实Resolver逐候选核验。无推荐表不自动补表4/5；表5可明确用于普通购电，原属性保持CONVENTIONAL。OTHER说明可选，统一适用性/年份提醒，有限数、非负和单位校验保留。购入/输出独立草稿，失效历史因子不替换为推荐值；非化石购入使用真实零绑定，输出按自身适用因子扣减。正式Domain再次校验资格，失配零Record。
5. **冻结追溯**：新Record既有provenance JSON保存实际采用五字段、三包修订和运行资源哈希；不改历史Record或数据库结构，不把全套R11宣称已采用。算法/Mapping公式版本不变，采用版本单独追溯。Word只读冻结Record，测试禁止重新计算或查实时Catalog。
6. **模板v5**：正式下载2.3.0，明确“直接计算值”→DIRECT/CALCULATED，旧“计算值”仍按热值计算、旧“实测值”仍DIRECT/MEASURED。v4/v3/v2保持原字节与身份，v4不得静默接受新标签。注册、导入、打包白名单、审计与报告模板身份同步。动态增行后按版本脚注识别，冲突脚注明确拒绝。

### 固定资源身份

| 资源 | SHA256 |
| --- | --- |
| 新v5模板 | `ce929968b8659889b0b6aba581b6782b96b8afcb8b378bc1b27c9768521e3d09` |
| 保留v4模板 | `e9b83462eabd97d5c7bd9aae1b4fa97a27d80006a205907c6671e626e8e57f6f` |
| 燃料/电力运行规则 | `691b6a20fff83e54194e9591a15bdc6a1ced3d6af5e3c1d9d5db49e4fbebcf79` |

v5由ArtifactTool authoring产物选择性合成；初候选A20空文本缺陷通过真实识别/导入回归发现，从作者产物取回文本后生成上述最终哈希。除`xl/worksheets/sheet2.xml`外所有OOXML部件字节与v4相同。模板下载复制受控原字节，未用openpyxl重存交付母版；测试填写副本不构成原生Office证明。

候选行业/软件修订`adoption-2026-10-17-fuel-power1`，通则`pr46-integration-2026-10-17-g05`。同源重生四件套61行、652技术组合（282 READY/370 BLOCKED）、450唯一意见范围，新增8表5范围，保留所有旧稳定分支与原意见0→0。ArtifactTool25夹具与同源checks通过，不能当作独立业务真值。

## 本地实际验证

解释器`.venv/Scripts/python.exe`，Python3.12.14；Qt测试为`QT_QPA_PLATFORM=offscreen`，并设置`PYTHONDONTWRITEBYTECODE=1`、`PYTHONIOENCODING=utf-8`。以下均为本地执行，不冒充Actions。

| 命令/测试范围 | 实际结果 |
| --- | --- |
| `scripts/project_fuel_power_rules.py` | PASS，机械投影精确一致 |
| `scripts/validate_canonical.py` | PASS，9 standards/12 sources/102 parameters/138 factors |
| `-m pip check` | PASS，无损坏依赖 |
| `-m unittest tests.test_b1_fuel_drafts tests.test_b1_fuel_consumers tests.test_b1_fuel_lifecycle tests.test_pr46_parameter_source_policy tests.test_pr46_fuel_confirmation tests.test_b_electricity_channels tests.test_b_electricity_table5_policy tests.test_fuel_power_runtime_policy tests.test_resolved_reference_bindings tests.test_fuel_power_template_v5 -q` | 80/80，0failure/0error，55.220s |
| `-m unittest tests.test_g06_carbon_material tests.test_exb01_template_acceptance tests.test_numeric_contract_v1_adoption tests.test_main_integration_ui -q` | 46/46，41.406s |
| `-m unittest tests.test_qzc_n01_c_numeric_unit_pilot tests.test_rs02_record_evidence -q` | 29/29，2.934s；原数值向量/精度/舍入/环境独立/冻结快照断言保留 |
| `tests.test_standard_input_policy`及P3-E下载方法 | 9/9，1.165s |
| `tests.test_uat03_rules` | 16/16，0.590s；44/12质量/体积原断言保留 |
| `tests.test_fuel_power_template_v5 tests.test_b_electricity_table5_policy` | 8/8，1.785s；含动态增行、脚注冲突、失配正式零Record |
| `scripts/uir04_manual_gui_acceptance.py` | 5场景PASS；实际离屏自动化，非人工原生操作 |
| `scripts/uir04_scale_acceptance.py --scale 1.25`与`--scale 1.5` | 两种缩放PASS，1366×768控件及动态行无重叠/水平滚动；非人工系统DPI验收 |
| `scripts/build_standalone.py --output-root build/fuel-power1-final-head` | exit0，固定`cd055518c42268db234008e78632e0f3d2b0718c`本地构建成功 |
| `scripts/inspect_release.py build/fuel-power1-final-head/QingzhouCarbonAccounting` | PASS，272files |
| `scripts/verify_release_archive.py build/fuel-power1-final-head/QingzhouCarbonAccounting` | PASS，273可见files，ZIP清单往返一致 |
| `scripts/smoke_standalone.py build/fuel-power1-final-head/QingzhouCarbonAccounting` | PASS，2次隔离启动 |

上述构建只证明所记cd05551对象，后续测试/脚注定位修订的最终HEAD构建由Windows CI重新执行，不能套用旧包provenance。

### 真实失败与修复

- 首轮三补丁72项2failure/0error，68.287s：v5空版本说明被识别成2.1.0；方向恢复时不可用历史因子被推荐项替换。修复后相关23/23，28.013s。新增追溯测试曾误读不存在字段1error，修正为真实provenance JSON后19/19联合通过。
- 探索性全量`-m unittest discover -s tests -t . -v`：763项，36失败断言/0error，924.547s，**失败**。此进程启动后实施/测试修复仍在另一进程推进，不能作为最终HEAD证据。失败清单保留在忽略build的`exploratory-failures.json`与`full-regression.log`。
- 36项覆盖旧LHV/FCh CALCULATED成功预期、旧模板2.2/允许项、缺身份的自定义燃料及无注册绑定的“官方”假对象、Numeric/Record相同旧输入夹具、非化石正式gate缺business_source、GUI缺省假对象。没有削弱校验：旧禁止来源改为定位拒绝；合法输入补齐真实Catalog/Resolver或显式实测身份，公式期望、比例/单位/零值/Decimal及历史断言均保留。所有相关模块/方法重跑通过。
- 中间定向测试曾错误读取被Adapter阻断的None calculation，2error，改为assert calculation为None后3/3；测试方法名误写、旧fixture参数拼错等历史执行错误在Git前序报告可恢复，不转述成产品失败。

## 最终运行与独立验收入口

提交此报告时，固定cd05551的第二轮完整本地回归仍在运行；期间又收口直接燃料目录夹具、表5正式负例和动态增行版本识别。因此不把该进程冒称最终HEAD完整通过。最后本地运行明细、最终base/head/merge SHA及**最终HEAD Windows CI完整回归、独立构建、审计、归档、启动和制品信息**统一补在原PR46最新验收证据与Actions检查；本报告不预判尚未结束的运行成功。

本轮交付不构成独立验收PASS或标准SUPPORTED。仅源会话根据实际diff/最终HEAD验收；不邀请第三方替代，不自动合并。

## 未闭合验收项

- v5原生Excel/WPS保存回导：NOT_RUN/OPEN。Owner Esc未解除，不使用computer use；程序重存与旧v4 WPS历史证据均不能代替。
- 真实鼠标、中文输入、人工系统DPI、企业真实样例：未执行。
- 最终HEAD Actions完成及源会话独立验收：以PR46最新检查/验收证据确认。
