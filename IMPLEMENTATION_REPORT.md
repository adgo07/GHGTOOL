# 五个业务页面 UI V2 — 暂停实施报告

本报告是安全断点，不是验收通过结论。用户优先退修PR59，本包暂停生产写入；独立分支codex/ui-five-business-pages-v2保留，未推送/PR/CI/发布。工作树位置通过聊天附件确定，不把机器绝对路径写成治理身份。

## 基线与范围

实际origin为adgo07/GHGTOOL，实际fetch后origin/main为092604639cd5b2b61fef1523f87fcd711d8aefea。原包apply_all.py先--repo/--diff只检查：6个既有Git blob匹配，10文件及限定方法保护通过，再--apply。两次原输出与真实patch在build/ui-five-pages-check/；原包/目标摘要在checkpoint-identity.json。未修改预期hash，不回退main，不整文件覆盖旧代码，不叠加单标准库旧包。

生产变更仅catalog_pages.py、pages.py指定五页方法、excel_import_components.py、record_tables.py及新增business_page_style.py。HomePage与其余受保护AST、7个新建核算/壳相关源文件检查未变；Catalog/Resolver/Calculator/数值/Schema/模板/Word业务/依赖不变。PR59未进入此基线，没有复制其生产代码。

## 已做的局部修正

- 导入详情设置受全局QSS覆盖，实际minimumHeight=60；组件局部QSS恢复改稿160目标，保留失败断言。
- 参数详情被分隔器压到约65高，补280最小高度，让改稿原定详情区可读。
- 标准要求中的原有软件说明明确标为非标准原文要求；官方URL/禁用/接线保留，原文按钮移至操作行，不增加来源区。
- 新摘要明确“原标准核算总量ET（冻结值）”，不把软件补充合计冒充标准ET，不改任何正式数值。
- 捕获改为每种尺寸独立窗口和临时库、记录页签显式0、初始状态断言；区分混合渲染夹具和真实合成Excel Adapter/临时项目保存场景。记录正式合成seed后，预览和项目保存不增加Record。源码/脚本/字体/图片hash和实际尺寸/Qt/DPR/回调异常均记录。
- 离屏环境未枚举字体，r1为缺字图已标INVALID；仅捕获/开发测试进程登记已有Windows系统字体，无产品字体包或新依赖。

## 执行证据

所有输出在build/ui-five-pages-check/，无未执行项冒称PASS。测试数量有重叠，不能相加为累计独立用例。

| 命令/组 | 真实结果 | 边界 |
|---|---|---|
| python -B -m unittest tests.test_standard_library_pilot tests.test_business_pages_visual -v | 首次14项：13通过/1失败，11.367s | 导入详情60/160真实失败，随后局部修 |
| README九模块原命令（逐模块名见readme-tests.log） | 64/64，36.883s | 增补守卫前；离屏默认字体环境 |
| 补充后test_business_pages_visual | 首次14项/1 error，17.009s；修夹具后14/14，9.280s | 新增故障注入误向tuple赋值，改为替换tuple，未改业务断言 |
| python -B build/ui-five-pages-check/run_with_windows_fonts.py | 70/70，37.694s | 同README九模块＋6新增守卫，已有系统字体登记；r3当前生产源 |
| python -B -m unittest tests.test_rs03_excel_project_workflow tests.test_rs03_excel_entrypoints tests.test_b_external_chain tests.test_rpt02_appendix_b -v | 39/39，68.485s | 真实合成Excel预览/保存/打开/正式核算/失效、成功追加/失败零Record、冻结Record/Word不重算；后续仅ET标签/详情高度变化，不冒称最终完整回归 |
| python -B scripts/capture_business_pages.py --output build/ui-five-pages-after-r3 | 60张，1440×1000/1180×800，Qt/PySide6 6.11.2，DPR1，回调异常0 | 本机字体字形守卫通过；真实离屏，非原生桌面/人工DPI/Office/IME |
| python -B scripts/validate_canonical.py | 9 standards /12 sources /102 parameters /138 factors，exit0 | Canonical原内容不变 |
| python -B -m compileall -q apps packages resources scripts tests | exit0 | 仅语法/编译 |
| python -B -m pip check | No broken requirements，exit0 | 使用已有依赖，未安装升级 |
| git diff --check；限定方法AST与保护文件检查 | PASS | 范围，不替代运行验收 |

## astra视觉HOLD与剩余项

astra已核当前28源码（27UI模块＋脚本）和r3的60图，hash均匹配；2026-10-24给出限定HOLD，未修改代码/运行测试/操作桌面。标准详情信息层级及官方按钮位置、导入三段和底部、设置路径与按钮、记录双页签及删除入口未见阻塞重叠。

须恢复后局部处理：标准列表状态徽标叠字，长编号省略及名称行高；参数搜索长行裁切、来源入口仅箭头及展开正文不足；记录列表企业/标准/状态裁切；B.9表头单位kJ/...截断；补拍正补充/待填补充区域。复选框蓝色无勾需先对照未改全局样式，不借此修改受保护全局主题。底部图有6对标准详情与顶图相同，后续证据可精简。

尚未执行：上述视觉修正及复验、本包最终完整回归、CI、精确head实包、原生桌面/人工DPI/IME/Office/企业样例、独立验收。没有宣布正式支持或发布。

## 平台 / Contract预检查

业务SHA/base见上；locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20。中央origin实际核验，ACTIVE指南从其已fetch的origin/main读取，非中央脏工作树；UI指南v0.2、家族规格、相关验收清单，Frozen Architecture按locked SHA读取。MUST/MUST NOT为分层、展示不回流计算、不可变历史Record/参数快照不漂移、UI state不成为公共Workspace、官方原文使用已登记URL。不修改lock、不adopt、不变公共语义，未发现需中央处理冲突。本任务不涉及中央公共 Contract。既有Standard Issue004/016/018、017、020；本任务不改变软件解释，无新增问题。按用户优先级暂停本包，转PR59独立修复，不混分支。
