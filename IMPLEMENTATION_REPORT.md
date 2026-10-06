# GHG-UAT02 — 核算录入与结果查看体验收口

状态：`IMPLEMENTED / AWAITING INDEPENDENT ACCEPTANCE`。本报告描述本工作包分支的实际源码与本地验证；PR head、最新GitHub Actions run及独立验收结论须由最终PR另行核对。本包不自行合并。

## 1. 基线与平台 / Contract 预检查

- 仓库：`adgo07/GHGTOOL`；实际`origin`已核对为`https://github.com/adgo07/GHGTOOL.git`。基线：开工时最新`origin/main` `c61b29baa2f5d75deae5fc243874d2b1d947bf4a`（含PR #29 UAT01-B合并结果）；分支`codex/ghg-uat02-accounting-usability`。未以PF01或其他开放PR作基线。
- 本仓`platform-lock.json`仍锁定`Qingzhou-contracts@ee5feb0cc34dbd99790500fadd0c4c932e202a20`。按锁定SHA核对Architecture V2.1、Numeric Contract v1、Numeric Profiles v1的分层、声明Profile一致性和ambient独立性要求；按当前正式版本核对UI Design Guidelines。UI只改展示/交互，正式数值仍由项目Carbon Decimal Profile与既有Calculator决定；没有改中央Frozen Contract、锁定SHA、Numeric Profile或共享公共语义。本任务不涉及新的中央公共Contract，未发现冲突。
- 已读取`STANDARD_ISSUES_REGISTER.md`；没有新的标准歧义或值录入，未改既有软件解释。本包把企业自填参数缺来源文字从致命错误改为非致命提醒，是用户明确提出的录入体验门禁调整；必填数值、非化石电力证明、非收到基换算证据等硬门禁保留。没有改正式公式、Canonical、标准表、标准支持范围或既有Standard Issue。

## 2. 实际实现

| 位置 | 本包行为 | 未改变的边界 |
|---|---|---|
| `packages/ui/carbon_material_page.py` | 关闭的下拉框/数字框滚轮交给页面滚动；失败提示定位首项；来源提醒文案；快捷排放源定位；多过程实例增加入口收进次级管理；FGD内部ID隐藏；物料摘要、系数说明和细小结果适应量级；防重复计碳设置渐进展示；输入改动后显示结果过期提示 | 不创建第二套计算，不改稳定内部ID、项目保存或Record生命周期 |
| `packages/ui/shell.py` | 监听当前页面布局请求，并在Qt嵌套布局稳定后合并复核滚动宿主高度 | 不增加导航和新页面 |
| `packages/ui/source_cards.py` | 启用排放源可折叠，未启用卡片收紧摘要 | 排放源Domain状态不变 |
| `packages/ui/pages.py`、`record_experience.py` | 记录审计详情放入默认隐藏的只读对话框；普通摘要更突出已启用排放源、分项结果与提醒；小非零数值不显示为0.00 | 历史Record快照只读、不重新按现行目录计算 |
| `packages/standards/carbon_material.py` | 企业实测/化学计算/自定义参数有合法数值但缺来源文字时产生WARNING；快照保留缺失事实，不伪造来源；标准/官方参数缺来源仍ERROR | 公式、单位、Decimal、非化石证明与基础资料硬门禁不变 |

新增`tests/test_uat02_usability.py`和`tests/test_uat02_geometry.py`覆盖关闭/展开控件滚轮与键盘、1/5/20条动态行、删除/折叠/展开后页面高度及滚动范围、内部ID隐藏、次级入口、缺来源说明的Record警告及缺数值阻断、首项错误定位、小值展示和审计详情。既有`test_g06_page.py`及`test_uir03_advanced_details.py`仅同步已批准的展示文案/精度预期，没有放宽计算断言。

## 3. Scope与回归审计

- 未修改PF01拥有的标准目录、查询、Canonical schema/数据、参数解析或共享reference data；未修改`计算表/`、迁移、数据库schema、Excel/Word、第二标准、云端或新一级导航。
- 既有计算公式、Canonical来源和值、标准查表/插值、正式Record不可变/新增/删除审计规则均未改变。参数来源门禁的WARNING调整仅适用于企业自填类别，官方来源不合格仍阻断。
- 页面输入保留与本地项目恢复、单元切换、历史记录查看仍由既有路径承担；本包测试及全量回归覆盖其稳定性。GAP-009仍为非阻塞来源债，标准尚未`SUPPORTED`。

## 4. 本地测试与构建证据

环境：Windows 11、Python 3.12.14、PySide6 6.11.2、PyInstaller 6.22.3。UI自动测试使用`QT_QPA_PLATFORM=offscreen`，并不冒充可见桌面人工UAT。

| 命令 | 真实结果 |
|---|---|
| `python -m unittest tests.test_uat02_usability tests.test_uat02_geometry -q` | 8/8通过，0失败/错误/跳过 |
| `QT_QPA_PLATFORM=offscreen python -m unittest tests.test_uat02_usability tests.test_uat02_geometry tests.test_g06_page tests.test_g07_records tests.test_accounting_projects_ui tests.test_uir03_advanced_details -q` | 77/77通过，0失败/错误/跳过；覆盖G06/G07、项目恢复与UIR03 |
| `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -t . -q` | 268项，退出码0，0失败/错误/跳过 |
| `python -m compileall -q apps packages scripts tests` | 通过 |
| `python -m pip check` | 通过，无损坏依赖 |
| `python scripts/validate_canonical.py` | 通过：9 standards、12 sources、98 parameters、98 factors |
| `python scripts/initialize_databases.py --output-dir <隔离临时目录>` | catalog/user/records/projects四库从零初始化通过；目录已清理 |
| `python scripts/build_standalone.py --output-root <隔离临时目录>` | Windows onedir构建通过，脚本内置release/archive审计通过；未发布该临时产物 |
| `python scripts/smoke_standalone.py <artifact> --starts 2` | 2次隔离启动均通过；临时产物已清理 |

初次定向回归曾真实检出“删行后滚动宿主仍保持旧高度”，不是把失败掩盖为通过；在`AppShell`修复Qt布局请求与后置复核后，UAT02几何专项、77项定向回归及全量回归均已重新执行通过。

未执行：可见桌面人工点击、实际用户业务UAT，以及最终PR latest-head GitHub Actions（PR创建后核对）。CI不能替代本地已执行项，本地offscreen测试也不能替代人工视觉验收。

## 5. 交付与停止点

只提交本包范围内代码、测试及本仓治理文档，推送独立分支并创建面向`main`的PR；验证GitHub Actions确实对应最终PR head。PR保持未合并，等待Sol/用户独立验收；不启动PF01、RS03-B、Golden Freeze、Release或第二标准。
