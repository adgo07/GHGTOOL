# PR62 家族 UI 统一与 CI 返修实施报告

2026-10-29。PR：[GHGTOOL #62](https://github.com/adgo07/GHGTOOL/pull/62)，分支 `codex/ghg-family-ui-unify`。本报告是稳定批次提交前快照，最终PR head、两required检查和精确包回执以PR最新交付记录为准；不得把此前运行冒用为新head证据。未合并，最终由源独立验收后通知Owner。

## 平台 / Contract 预检查

实际root、origin、fetch、branch、head、status已核对；origin为 `https://github.com/adgo07/GHGTOOL.git`，默认main。基线 `6fc5909646b855494abee55cff6fd95f8d18b4be`；本批开始业务仓head `2d555e165c41c30bdec8c075ff813f47061cc0f8`。隔离worktree复用原任务分支，原checkout用户数据/修改未触碰，未创建Goal。

locked central SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 未变。Architecture V2.1、Numeric v1/Profile v1冻结权威不升级；本任务不涉及中央公共 Contract。适用MUST/MUST NOT：维持Presentation/Application/Domain/Infrastructure分层；窗口偏好只用既有独立user设置；UI显示与内部标识处理不得回流计算；不得改变Canonical、项目/Record、标准解释或来源绑定。均满足，无Contract冲突、无中央缺口或adoption。中央当前适用UI指南为ACTIVE/EVOLVING，读取已验证origin的中央仓；家族设计候选 `e1486fb20c1dda33b7344ca860ff8f303c2183ee` 是Owner批准的本轮视觉依据，不称Frozen或已发布平台基线。

Standard Issue：已读台账；本任务不存在需改变的相关解释问题，无新问题编号，不改变既有软件解释/支持范围。算法、参数、单位/Numeric Profile、Excel母版/算法、Word报告、数据库迁移、项目保存/恢复和不可变正式Record语义不变。

## 产品结果与本批返修

- 共享样式集中化，迁移进行中：design_tokens集中字体/输入/按钮/页签/表格；页面和壳仍有局部QSS，不宣称唯一来源。普通输入/按钮外框40 DIP、导航46 DIP；焦点与禁用态完整，正文最大1440不含外边距。
- 首次窗口1280×800居中非最大化，后续独立user偏好恢复普通/最大化；按实际工作区收回，正常最小960×600，小屏含边框适配。普通正文窄屏不出现页面级横滚，复杂源编辑区允许有边界的局部滚动，实际左右端可达。
- 原图Logo按DPR取样；SVG原生渲染，保留23个预着色变体。本批补[来源/色板清单](docs/ui/family-ui-final/icon-provenance.json)与生成器；`--check`逐字节校验，不另建图标体系、不增加运行时资源。
- 首页右上设置、业务页设置上下文与返回保留；表格默认48/最小44、中文完整换行与底部计数、页头actions和导入四区标题保留。导入专门文案断言覆盖“模板与说明 / 文件选择 / 数据预览与检查 / 处理结果”，其他交互继续按对象和业务行为检查。
- CI316唯一失败是缩放stdout位置不匹配。本批恢复兼容人读前缀，并增加版本化JSON结果，严格验证scale/真实DPR/work_area/PASS/空failures/client/cleanup/exit0；保留三档完整几何/动态行/重叠/删除断言。加入flush分段计时，60秒超时报告命令、Qt配置、stdout和最后阶段stderr，不提高上限。
- 缩放父例取消无断言用途的重复窗口初始化；项目恢复只共享只读catalog，服务、projects库、records和页面逐例隔离，类结束哈希校验。项目/FGD/Excel入口夹具使用已有可靠销毁助手，保留原close检查后再销毁。无新增全局缓存、跳过测试、工作流拆分或预算修改。

## 耗时与覆盖证据

完整分析、重复覆盖对应与口径见[测试成本核对](docs/ui/family-ui-final/TEST_COST_REVIEW.md)。AST核对6个修改模块原74个test_*方法名全部保留，未删业务/来源/Record/几何断言。

改前项目页两轮setup22.338/17.444秒，teardown后对象仍活；FGD窗口39.453秒，结束后仍活。改后共享catalog一次11.363秒；两轮setup50.060/12.248秒、销毁1.504/0.070秒；FGD ready27.775秒、总28.010秒，全部结束即失效。本机其他测试并行且SQLite I/O波动明显，不能从上述非独占样本宣称净提速。确认的收益是可靠销毁、重复目录构建减少和可诊断性；全量是否接近30分钟由新headCI实际判定。

## 本地验证（本批）

环境Windows，Python3.12.14 / PySide6 6.11.2；只运行offscreen。TEMP/TMP指向本轮隔离临时目录，PYTHONDONTWRITEBYTECODE=1、QT_QPA_PLATFORM=offscreen。3.12对C盘worktree新输出目录仍有WinError5，抓图改用已授权隔离临时目录后复制6张，不改ACL或真实用户库。

| 命令 | 结果 |
|---|---|
| `python -u -m unittest tests.test_uir04_finalization.UIR04FinalizationTests.test_common_windows_scale_factors_keep_controls_visible -v` | **最终1通过/0失败，149.765秒**；真实DPR为1.0/1.25/1.5，各探针52.535/44.296/40.829秒，均exit0。此前诊断版1项132.485秒通过；诊断runner每30秒堆栈是观测，不是60秒保护失败。 |
| `python -u -m unittest tests.test_family_ui tests.test_g03_shell -v` | **24通过/0失败，224.698秒**；包含正常最小窗口可用正文和四标题断言。补强扣除边距后600 DIP正文断言后，该入口再验1/1通过，15.138秒。 |
| `python -u -m unittest tests.test_accounting_projects_ui tests.test_b_fgd_acceptance_fixes tests.test_rs03_excel_entrypoints -v` | **41通过/0失败/0错误，974.358秒，exit0**；项目21、FGD10、Excel入口10。 |
| `python scripts/uir04_scale_acceptance.py --scale 1.0` | PASS / exit0，40.636秒；catalog6.418、窗口6.285、动态行24.483、几何1.075、可达/删除1.019、清理0.576秒。 |
| `python scripts/uir04_scale_acceptance.py --scale 1.5 --work-area small --screenshot <隔离路径>` | PASS / exit0，client531×531，71.492秒；含抓图，导入27.793秒。**不是60秒子进程测试**，未增加任何保护预算。 |
| `python scripts/run_family_ui_review.py --data-dir <隔离目录> --capture-dir <隔离目录>`及DPR2 `--only-home` | 四页+DPR2离屏抓图成功，合成数据。 |
| `python scripts/generate_family_icon_variants.py --check` | 23个SVG PASS。 |
| `python -c "from scripts.build_standalone import _validate_approved_template_inputs; _validate_approved_template_inputs()"` | 资源白名单/模板hash PASS；此静态检查用本机Python3.13.3，不冒称3.12实包构建。 |
| `python -m compileall -q scripts tests`；`git diff --check` | PASS；compileall为本机3.13.3静态检查，3.12实际导入由上列回归覆盖。 |

图标来源首次跨检发现旧Windows工作区CRLF与Git权威LF字节不同，已明确来源hash按Git LF、变体按本地基础文件原换行逐字节比对；当前CRLF与全新LF检出模拟均23/23通过，未改资源。曾主动停止无输出及重复诊断进程，不计通过；初次C盘抓图PermissionError记为环境失败，后改隔离路径成功。没有反复运行全量取绿。

## GitHub Actions证据与交付边界

提交前最新CI316 / run40725201083：全量1133项1587.264秒，1失败；Standalone依赖跳过。旧CI311为main1122项2107.461秒成功，CI314/315的40分钟超时仅属历史；不能作为当前head验收。新批次完成本地验证后一次push；复用同head运行，核验完整Merge-ref与精确PR-head Standalone两required，及build/audit/archive/provenance/smoke/upload全部步骤、制品ID/名称/大小/digest。此处提交前尚无新head成功证据，不称已全绿或已交付EXE。

## 代表图与未执行项

[最终图集](docs/ui/family-ui-final/README.md)恰好6张、760869字节，已看图；[源码/图像清单](docs/ui/family-ui-final/capture-manifest.json)绑定产品源head与Git树、哈希、DPR、尺寸和脚本版本。本批不改产品源码apps/packages/resources，图像源绑定有效；外部原始抓图和隔离QA数据库不打包。

未执行本轮本地全量、真实桌面交互、多屏/DPI切换、Office/IME、干净机/企业样例；源独立最终验收未完成。本报告不宣布正式标准SUPPORTED、不自动合并或发布；源验收通过后通知Owner。
