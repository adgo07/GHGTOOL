# 标准分派与业务一致性：实施及交付报告

2026-10-14。六个连续工作包已实现，提交一个独立PR等待验收；不自行合并。最新PR head及GitHub Actions结果以该PR的Checks/Conversation为证据，下面明确区分本地结果与待完成项。

## 平台 / Contract 预检查

Canonical origin为adgo07/GHGTOOL；最新确认base main为204dded5d03853617f79a1f05693e89b619df9d1。隔离分支codex/ghg-standard-input-unification；用户主目录分支和脏文件未改。PR45 head9cdbcaa6e7e88914036535a65f80b11d26d8839e仍OPEN，其视觉实现以本分支5d09ae6明确整合，不在GitHub合并或关闭原PR。

中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20未变。适用Architecture V2.1分层和Numeric v1 declared-profile、ambient independence、full-value exact、显示修约不回流要求；Carbon p40/HALF_UP为合法项目差异。内部标准注册/项目封装不发布中央公共Contract，无Frozen升级。当前中央UI指南v0.2为ACTIVE。相关Standard Issue001—008保留，新009记录Owner自定义输入政策；未将软件决定写成标准明文，未新增因子或第二行业公式。

## 按批准问题逐项交付

| 问题 | 实现及证据 | 状态 |
|---|---|---|
| 共同来源政策 | 标准模块共享catalog/custom身份；目录FCh只读且正式防绕过，自定义必要参数可填、不借默认；自定义碳酸盐不自动标为实测/化学计算 | 完成 |
| 公共标准分派 | 小型静态注册、惰性服务/页面、标准间草稿隔离；启动/壳/Excel/报告不直接构造.34服务；未知标准/版本严格拒绝，UI不抛未处理异常 | 完成 |
| 燃料 | 独立两行编辑器；规范名称与搜索别名分离；FCm/FCV/FCh分开；质量/体积×计算/实测四场景跨入口完整值/单位/来源等价 | 完成 |
| 工序与物料 | B.3—B.5类别/实际名称/工序/序号明确归组；碳与挥发分共享质量只计一次；同名跨过程不混合、冲突定位拒绝；工序业务名可恢复 | 完成 |
| 脱硫 | 每组独立脱硫剂名称/用量/多组分，数据与来源分行；新增组分后再新增脱硫剂，旧组分量兼容 | 完成 |
| 电力五表 | 完整目录查阅，地域层级与因子口径区分；GUI/Excel用同一Resolver候选；未批准的区域/其他全国口径禁选说明，不静默互换 | 完成（未扩大正式口径） |
| 热力 | .34新录入仅饱和/过热蒸汽；热水/其他不可录入或导入；旧项目读取保留 | 完成 |
| 受控Excel | 模板2.0.0九表保护/解锁；B.2数据/单位子列，FCh独立；B.3—B.5新增明确身份；B.6全行消费；下载复制原字节、精确SHA打包 | 完成 |
| 项目/历史 | 模块内部standard/input版本封装及codec分派；旧v1/旧模板/旧Qt索引/EXCEL_R2证据可读；未知格式不猜，不改库结构 | 完成 |
| Record/Word表式 | 共用冻结业务表；短来源与表下完整证据分开；新派生值随Record冻结、旧缺项不补算；Word不读活Catalog，不重算 | 完成 |
| 首页/标准库 | 最近记录状态列扩大、余宽给企业、表头居中；筛选一行、支持列104、名称伸展；文案“已实现核算”不升级SUPPORTED | 完成 |
| 卡片/字号/二选 | 名称单行16px、开关/状态下置、浅色标题、输入14px；稳定二选用键盘可达radio，底层既有typed值/旧HEAT读值保留 | 完成 |
| 术语/重复清理 | “手填”改“填写”；普通电力提示去PDF页，完整定位保留tooltip/冻结证据；重复燃料清单、UI报告投影移除；兼容路径独立保留 | 完成 |
| 原生填写/报告核查 | WPS ET保存回导17项；WPS Word兼容引擎11页逐页检查；只用TEMP合成样例 | 完成（合成数据） |
| 原生Windows与缩放 | Windows Qt原生平台100%/125%各20项程序检查及截图；离屏125%/150%增删布局另记 | 部分：未人工切换系统DPI |
| 真实企业完整UAT | 没有提供已核验的真实企业业务数据；未捏造实测样例 | 未执行，交Owner实际操作验收 |

模板当前SHA256：58b38c15d487bdc173f573a50e5b8f3446b5bb4df4693dd696a83742da5235b4；用户docs母版未覆盖。旧模板1.0作为兼容夹具保留，历史输入/Record不迁移。报告模型3.0.0候选；原来源母版SHA与当前输入模板SHA分别追溯。Calculator版本CAR-SM01-2026-10-13-G06.4增加输入政策和冻结展示证据，原公式/系数/操作顺序/Numeric Profile不变。

## 本地命令与真实结果

| 命令/检查 | 结果 |
|---|---|
| `python -m unittest discover -s tests -t . -v`，89246be3842b92be19f1d6df3a99b894205550f2 | 510通过，0失败，0错误，413.123秒 |
| 最后普通电力提示/TEMP约束后：`python -m unittest tests.test_uat03_formal_workflow tests.test_uat03_rules tests.test_standard_dispatch -q` | 27通过，0失败/错误，15.699秒；生产计算未改 |
| `python scripts/validate_canonical.py` | 有效：9标准、12来源、102参数、138因子 |
| `python -m compileall -q apps packages resources scripts tests` | 通过 |
| `python -m pip check` | No broken requirements；首次venv缺pip，ensurepip补齐后实际重跑 |
| `python scripts/initialize_databases.py --output-dir build/standard-input-db-check` | catalog/user/records/projects四库从零初始化通过 |
| `python scripts/uir04_manual_gui_acceptance.py`（offscreen） | A—E共5个程序驱动场景通过；名字含manual不代表人工验收 |
| `python scripts/uir04_scale_acceptance.py --scale 1.25` / `--scale 1.5` | 两种离屏增删布局通过 |
| `python scripts/build_standalone.py --output-root dist`，89246be | Windows构建通过；manifest来源精确绑定89246be |
| `python scripts/inspect_release.py dist/QingzhouCarbonAccounting` | 268文件通过，精确模板/资源白名单/数据范围审计 |
| `python scripts/verify_release_archive.py dist/QingzhouCarbonAccounting` | 269可见文件，ZIP往返清单通过 |
| `python scripts/smoke_standalone.py dist/QingzhouCarbonAccounting` | 2次隔离启动通过 |
| `python scripts/standard_input_ui_acceptance.py --scale 1.0/1.25 --width 1366 --height 768 --output-dir ...` | 各20项Windows原生Qt平台检查通过；客户端截图/哈希在docs/ui/standard-input-evidence |
| 原生COM `native_excel_roundtrip.ps1` + `verify_roundtrip.py` | 17/17通过，失败/未执行0；命令、版本、路径和全部业务对比在excel-wps证据目录 |
| 原生WPS Word兼容COM→PDF→PDFium | 11页已全部查看，1条合成Record/10张业务表；无裁切/空页/内部编号 |

首轮完整482项为475通过/5失败/2错误（368.757秒），修复1个未开放标准UI信号异常及旧常量/布局/版本/来源断言；第二轮510项为509通过/1失败（436.176秒），为同一UI拒绝方式旧断言，分派9项复测通过后第三轮完整510项通过。最后电力提示只修展示，最终head全量由新PR Windows CI再次核验，不借用PR45的通过结果。日志中故意注入的持久化/元数据异常属于失败路径测试。

WPS ET实测版本12.1.0.29158（COM12.0），独立新PID、打开前0工作簿，只保存TEMP副本。9表/保护/锁定图保留，前后公式均0；21处仅空白None→空串，其余单元格值无变化。工作簿SHA派生身份归一化后，完整输入/结果/16参数快照/15trace及warnings一致，数值/来源/因子/归属不忽略；预览零Record，正式新增1条，总量635.3858298933333333333333333333333333334 tCO2。

LibreOffice技能renderer实际失败（无soffice），改用已核实的WPS12原生Word兼容引擎，未声称Microsoft Word人工验收。原生Qt截图采用QWidget.grab程序驱动，Qt scale不是Windows系统DPI。第一次成功构建输出被并行验证误识别清理，已禁止代理清理仓库并重建；该操作不在提交的回导脚本内，最终交付使用重新审计的产物。

## 独立审查、CI与待验收项

Luna独立只读审查base204dded→89246be，未发现阻断、高或中级生产问题，覆盖B.2—B.9归组、来源/精度、codec历史、注册分派、冻结报告及打包。建议的辅助脚本TEMP约束已补齐；最终普通电力提示及该约束单独复核。CI按最终PR head运行，两项Windows job及merge-ref/head来源以PR Checks/Conversation登记；本报告提交时不提前宣称CI通过。

未闭合项：最终PR Windows CI、最终独立验收、Owner真实企业样例、人工系统DPI操作验收。Microsoft Word与LibreOffice兼容性未实测；已完成的是本机WPS。未执行第二标准、因子公告、结果Excel导出、中央Contract升级或全面架构重构。阶段停止于可审查PR，不自动合并，不启动其他阶段。
