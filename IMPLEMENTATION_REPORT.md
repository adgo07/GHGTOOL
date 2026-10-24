# 五个业务页面 UI V2 实施报告

本地实施、限定视觉复核与完整回归已完成，当前准备独立范围 PR / required CI / 精确 head 候选包；尚未合并、发布或完成源会话独立验收。

## 身份与实施范围

实际 origin 为 adgo07/GHGTOOL，分支 codex/ui-five-business-pages-v2。复用原4230226断点，正常吸收PR59合并后的main d7159f77ddb103376f5ca6bdd3a9532c101433e3；最终fetch确认main未变。原包仅在原基线6旧blob/10目标匹配后受控应用，原包apply_all SHA e52441f1311767faad0a4d13a44416303039925c11efbd18eda7b1866970da3a。未重套旧包、改预期hash或整文件覆盖生产源。

生产仅五页呈现：标准库及详情、参数与因子库、表格导入、记录及详情、设置；一个局部business_page_style helper。标准编号及名称按最终字体/列宽呈现，徽标保留原模型文本供选择与辅助功能，仅避免cellWidget下重复绘字；参数来源可展开正文；记录徽标紧凑完整；冻结B.9等表头完整显示原单位。表格列宽变化通过Qt排队连接在表头布局完成后重排行高，保留最终提示最小高度，参数搜索单独留12px末行绘制空间，不加定时器或业务状态。

原首页、导航、壳、新建核算、Application/Core/Calculator/持久化/Canonical资源/依赖/workflow均未改。原包protected_tree核对所有未授权方法通过；8个核算/壳保护源与main一致；Excel原构造和新构造+布局的connect AST多重集合19/19相同。ReportTableCard只改显示宽度，不改冻结表式、投影、模板或Word。原标准ET、外部补充、软件合计分别展示；合成截图8.62/20.00/28.62仅是冻结完整值的显示修约，待补不补零。全局主题未改，复选框指示器与原主题对照像素一致。

## 视觉与测试身份

r9从干净生产提交e2c7520ef58eb7623ddf0f8ba5a45be9193a1b30采集，真实Qt6.11.2/offscreen、DPR1、1440×1000与1180×800、合成隔离库；开发进程只登记本机已有Windows字体，产品无新增字体包。58页面图+2主题对照图、29源hash全部匹配，callback_errors为空。astra turn 01a16fcc-4e56-7252-8940-65401e991c57独立只读复验PASS（限截图）；52页面图与已审r8逐字节相同、6张变化图重查，原五项HOLD关闭。该结论不证明访问冲突根因、不代替业务/原生/CI/发布验收。

本地完整验证head 5c0c34013db938f56924329b43861fa5890c52d3相对r9仅改G03旧布局预期和阶段文档，29项捕获源与完整测试源逐项SHA相同；生产未再次变化，不以旧图冒称新源图。后续证据/阶段文档提交不会重标该测试或截图head；最终PR head以PR/API及交付回执为准。

## 本地真实验证（数量重叠，不累计）

| 命令或范围 | 实际结果 |
|---|---|
| python -B -m unittest discover -s tests -t . -v | 1106/1106，2731.183s；原CLI，PYTHONFAULTHANDLER=1，无字体注入；源码前后hash一致，deleted Qt对象异常0 |
| python -B build/ui-five-pages-check/run_with_windows_fonts.py | 74/74，207.860s；原九模块及4个可读性守卫，开发进程已有Windows字体 |
| python -B -X faulthandler -m unittest tests.test_b_material_draft_scope tests.test_b_material_gui_excel tests.test_build_environment tests.test_business_field_policy_isolation tests.test_business_pages_visual -v | 27/27，164.197s；无字体注入的相邻模块组合 |
| python -B -m unittest tests.test_g03_shell -v | 13/13，19.338s；批准布局预期同步，业务断言保留 |
| python -B -m unittest tests.test_rs03_excel_project_workflow tests.test_rs03_excel_entrypoints tests.test_b_external_chain tests.test_rpt02_appendix_b -v | 39/39，166.620s；其后也包含在1106项原始整轮中 |
| python -B scripts/validate_canonical.py | 9标准/12来源/102参数/138因子，exit0 |
| python -B -m compileall -q apps packages resources scripts tests | exit0 |
| python -B -m pip check；git diff --check | 无依赖冲突；通过 |

完整原始日志SHA e2c33a8d1096ef4da28a71b728d74f7aa965e6083fdeee1e9978f3062b73b93a。以上均为本地执行，不能写成GitHub Actions结果。测试使用工作区TEMP及合成库，不操作用户工作簿或参考文件。GitHub CI尚待本次独立PR真实运行，不复用PR59旧CI/候选包。

## 失败、修复及证据保留

652301a上的首次完整CLI于1297.813s在第340项附近访问冲突0xC0000005退出，无最终测试摘要。单用例通过；相邻27项26通过/1失败136.004s，发现未注入字体下行高54<原提示63；首次仅补提示仍失败（27项26通过/1失败177.421s，同源74项通过220.792s）。诊断显示列宽回调在表头原生布局未完成时测量；Qt排队连接修复后27/74组通过。其后e2c完整1106项跑完2860.222s，1104通过/1失败/1错误，未复现访问冲突；两处是G03旧settingsSurface与01获取模板呈现断言，改为批准的两真实设置区块及顺序、Adapter原模板说明和三工作区标题，全部期间/地区/边界/模板/按钮/初始状态/首页导航业务断言保留。5c完整1106/1106通过；两轮均未复现原访问冲突，仍不宣称根因已确定。

旧缺字r1、中间r2/r3HOLD、R4脚本错误定位补充、R5标题尾部空白可视判定、R6未完全解决裁切、R7脏树开发图、R8旧干净图及全部原始失败/诊断日志均保留，不重标为通过。原始证据528文件已在独立保留目录逐文件SHA/ZIP CRC复核，归档SHA 84a16bc933fab487430db34c365882db9d80e1f1264b08abe6ffc11935ea1ec4；本工作树忽略build暂不清理。

仓库精选28图、全部60图/29源哈希索引、限定视觉回执及本地完整摘要见[证据页](docs/ui/business-pages-v2/review.html)。完整原始ZIP为本地保留证据，真实保留路径在最终交付回执，不写机器绝对路径进治理正文。

## 平台 / Contract预检查

验证业务head5c0c34013db938f56924329b43861fa5890c52d3，main d7159f77ddb103376f5ca6bdd3a9532c101433e3；中央origin再次核验并fetch，适用当前正式合并c5fc6d4的UIv0.2及清单。locked中央ee5feb0cc34dbd99790500fadd0c4c932e202a20、Architecture V2.1及本仓Numeric Profile不变。MUST/MUST NOT：保持分层；Domain不依赖Qt/SQLite/Windows；显示不回流计算；历史Record只消费冻结快照，不查当前Catalog补算；UI state非公共Workspace；不改来源资格/标准状态。无冲突、adoption或中央修改。本任务不涉及中央公共 Contract。

相关Standard Issue：有，既有004/016/018、017、020；改变软件解释：否；无新标准问题，不宣布SUPPORTED。原生桌面/鼠标/系统DPI/IME/Office/企业真实样例/干净机未执行；离屏及脚本缩放测试不冒称这些验收。

## 剩余交付

稳定证据批次独立PR，复用同head required checks；下载本次真实精确head制品并审计，结果分开标注GitHub和本地。不得改变workflow/付费预算/可见性、不得无变化重复触发CI。随后停止等待源会话独立验收，不自动合并或发布。
