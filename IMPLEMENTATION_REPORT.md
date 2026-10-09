# GHG-UAT03 V2实施报告

日期：2026-10-09。状态：实施收口，等待当前PR完整CI及用户实际操作验收。

## 平台 / Contract 预检查

实际业务起点main ff15061d2d765dbff869a0b182af4432d09398bc，origin/default branch/工作区已核验；独立codex/uat03-new-accounting-v2不覆盖用户实测文件。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；已读取locked Architecture V2.1、Numeric v1、Profiles v1及当前ACTIVE Policy/标准开发指南/UI v0.2/家族规格/验收清单。

MUST：UI/Application/Domain/Infrastructure分层；库与Resolver唯一默认参数链；共享Calculator；Decimal40/HALF_UP与ambient independence、full-value exact比较；输入保存保留完整decimal，展示修约不回流；成功新增不可变Record、致命失败不新增；Word只读正式快照；旧项目/历史Record保留。

MUST NOT：UI硬编码重复因子清单、UI另写正式公式、当前Catalog重算历史、Qt状态冒充公共Workspace、升级Frozen/增加标准范围/复制标准全文。本轮内部可选地区字段及UI适配不新增公共Contract；ALLOWED PROJECT DIFFERENCE继续为项目Numeric Profile。无需中央Contract修改。

Standard Issue：用户V2明确批准取消非化石电力自动证明前置；已在GHG-STD-32151-34-007/008登记Software Decision并实施；冻结Mapping保留。地区因子的适用性与实际来源需保持。既有001～006与44/12、蒸汽查表、过程K参数计算不变。

## 最终实现范围

按用户V2与三张参考图完成8个横向排放源开关、企业历史搜索、自定义日期整行显隐、明细首条保留与启停保留、燃料C.1/自定义及计算/实测含碳量两条路径、过程物料与烟气紧凑录入、统一电力/热力列表、当前已保存且未过期Record的Word导出入口。默认参数经Catalog/Resolver选择；手填来源不借目录身份；输入完整小数与Decimal40计算保持，结果/汇总显示修约不回流。

旧项目隐藏基准、换算证据、组分/来源类型和电力属性/证明字段保留。旧输出实测因子未编辑时保留历史MEASURED来源；改值或切换选择方式后清除旧标记，按USER_DEFINED保存。正式Word仍只读冻结Record，不重算、回查当前目录或改变历史记录。

没有重做Excel模板/Word版式、录入新公告、增加标准/数据库/依赖、升级Frozen或覆盖用户参考文件。本包改变已批准的软件选择边界（007/008），不改变标准公式、44/12、Numeric向量、蒸汽查表或历史Record。

## 本地执行证据

以下均为本地执行，不能写成GitHub Actions通过：

| 命令 / 范围 | 实际结果 |
|---|---|
| `python -m unittest discover -s tests -t . -v`，第二轮 | 393项，392通过、1失败，896.327s；唯一失败为动态几何测试仅等待5ms而尚未收敛。日志`build/uat03/final-full-suite.log`。不是最终全量通过声明。 |
| `python -m unittest tests.test_uat02_geometry tests.test_uat02_usability`，修正有限布局等待后 | 8/8通过；动态几何单项另重复4次通过。exact高度、增删收缩和滚动断言保留，未改生产布局。 |
| `python -m unittest tests.test_uat03_page tests.test_uat03_formal_workflow tests.test_uat03_responsive_fields -q`，最后来源标记补丁后 | 27/27通过，79.747s；`build/uat03/postfix-focused.log`。 |
| 独立agent：`python -m unittest tests.test_uat03_page tests.test_uat03_formal_workflow tests.test_accounting_projects_ui`，同补丁后 | 47/47通过，303.460s；`build/uat03/review/marker-final-focused.txt`。 |
| 稳定规则/快照/报告/Numeric独立定向套件 | 前序独立129/129通过；末次重点为上述47项，不把重叠项目相加。 |
| `python scripts/uir04_manual_gui_acceptance.py` | 自动驱动A～E五场景通过，非原生人工操作证据。 |
| `python scripts/uir04_scale_acceptance.py --scale 1.0/1.25/1.5`（分别执行） | 三档通过，1366×768无重叠。 |
| `python scripts/validate_canonical.py` | 9 standards / 12 sources / 102 parameters / 138 factors，通过。 |
| `python -m compileall -q apps packages resources scripts tests`；`python -m pip check`；`git diff --check` | 通过，无依赖破损或差异错误。 |
| `python scripts/initialize_databases.py --output-dir build/uat03/final-databases` | catalog/user/records/projects四库重建通过。 |

第一轮387项发现旧文案断言与direct含碳量焦点失败，均已修复。第二轮的几何失败及后续来源标记补丁如上分开记录；不把393项追溯宣称为最终head全量通过。当前head完整测试、打包、压缩包回读和启动审计由既有Windows CI执行，结果单独记录在PR；本报告不冒充CI结果。

## 独立验收与兼容边界

最终独立只读结论支持代码级通过；另独立几何/marker/self Canonical3/3、几何连续4/4通过（保留精确断言）。已关闭review发现的旧DRY/证据覆写、legacy电力语义丢失、旧输出MEASURED漂移及用户编辑后旧来源残留。实际SQLite探针核旧输出实测值和编辑后的手填值均进入对应真实raw Canonical及ParameterSnapshot；目录切换与旧Record不漂移有正式流程测试。

旧SELF_CONSUMED/FOSSIL/GEC/VALID在UI恢复和Canonical中保持；缺少对应`FuelInput.electricity_detail_id`时，正式计算沿用main已有的`GEN-VAL-SELF-CONSUMED-FOSSIL-ROUTE`阻断且不新增Record。main页面同样没有该链接控件，本包不新增链接功能或绕过防线；不得声称无链接的旧行成功生成Record。

代码复核断点为754ac23aaedee160c2d37e58666711e207a99816；几何等待仅变更测试。正式PR最新head及候选build provenance以PR与release manifest为准。原用户checkout与参考文件保留，任务独立分支未合并。

## 原生操作与交付限制

Astra/low子agent两次初始化原生Windows接口失败：`node_repl kernel exited unexpectedly` / `windows sandbox failed: helper_unknown_error: setup refresh had errors`。恢复执行后默认沙箱仍同错误；没有操作已有窗口或取得原生截图，未使用UIA/helper绕过。

1366×768、1920×1080的Qt离屏布局已查看，属于技术证据。原生排版、滚轮、下拉搜索、多行录入、错误定位与Word实际窗口操作尚未执行，需用户按`docs/uat03/USER_ACCEPTANCE.md`检查候选程序。此任务没有预先合并授权，标准正式支持状态不因本UI包升级。
