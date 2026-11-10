# PR63：CI 失败已修复，待新 head 必需检查

2026-11-11。本轮GitHub Actions [42851736412](https://github.com/adgo07/GHGTOOL/actions/runs/42851736412/job/129953959407) 实际运行 head `5d1953f64fc988656ce71cb1ba9337d861be91d1` 的1156项：1153通过、3失败，2126.493s。全量已在原时限内完成；Standalone因依赖失败跳过，不能称此轮CI通过。

两项失败为FGD/燃料旧值测试仍断言旧“历史来源”文字，现只同步为“当前来源”，保留原始值、旧来源不冒充实测、显式确认等全部行为断言。第三项为960×600窄窗错误定位：数量输入框(38,445,528,40)超出内视口604×480，底部裁5像素；Qt ensureWidgetVisible只保证光标区域，现将原有整框校正同时应用于内外滚动区，不改输入/焦点取消规则或校验。

本地实际验证：

- `python -m unittest tests.test_family_ui tests.test_pr46_fuel_confirmation tests.test_g06_fgd_ui -v`：32/32，131.791s（ci-fixes.log）。原失败几何断言保留，并增加失败矩形信息。
- `python -m unittest tests.test_pr59_compatibility_navigation tests.test_accounting_source_directory.SourceDirectoryTests.test_validation_opens_conversion_and_external_disclosures_without_input_changes -v`：10/10，103.667s（navigation-final.log）。覆盖连续定位、切换源取消、目标删除/销毁、旧项目恢复、内外折叠展开。
- 复用原FamilyUi真实Qt测试场景另存离屏图：修后内框(38,424,528,40)完整位于604×480视口；外框(85,536,528,40)完整位于708×600视口，焦点仍是目标。见[定位修复图](docs/ui/new-accounting-v2/integration-review/21-ci-navigation-offscreen.png)。不是原生点击证据。

原生限定复验OPEN：两次明确选择GHG窗口，工具返回正确窗口元数据但截图为另一应用；Astra未发送任何输入并只关闭自有隔离实例。此前原生PASS不覆盖最后滚动定位修复；本次以实际Qt视口/焦点回归验证，未冒称原生复验通过。该工具限制不代表已知未修复产品失败。其他EXE/Office/系统多屏DPI等既有OPEN不变。

中央四份UI适用文件在本轮修复后再次在线核对，blob均与下方预检查一致；精简要求未回退。平台/Contract与Standard Issue预检查继续适用：仅Presentation滚动与测试断言，本任务不涉及中央公共Contract或标准解释变化。新head仍须全量及Standalone required checks通过后，按Owner授权合并；最终head/CI/合并状态以PR63回执为准。

---

# PR63 整合完成，待当前 head CI

2026-11-11。在 main/已合并 PR64 `d7a053b8354b98ab5ea3ad53618cf7de657a8809` 上整合 PR63，冲突已解决，PR64 精简文案、标准库窄窗与空态行为保留。用户授权回归和 CI 全通过后合并。当前正式 head、CI与合并状态以 [PR63](https://github.com/adgo07/GHGTOOL/pull/63) 最终回执为准。

已完成本地回归及范围内原生验收；初轮61项59通过/2失败（依赖/超时）均有后续修复复验。最终7/7条目布局、1/1三档缩放（每档原60s内）、10/10记录/输入/定位、补充25/25热力与旧值规则通过，重叠不累计。完整命令、失败与关闭证据见 IMPLEMENTATION_REPORT.md；本轮不把历史CI当作新head结果，1156项全量待required CI。没有扩大产品/标准范围或修改Frozen lock；旧项目、成功追加Record、模板/Word/业务规则保留。

中央2026-11-10精简规则已核对：重复说明缩短、辅助说明ⓘ默认收起且可键盘访问；关键限制、错误、停用/生成记录影响仍直接可见。性能修复只减少布局与样式重复工作，原三档缩放/CI时限未放宽。

下一步由父代理统一推送、核对同head全量及独立打包审计，全部通过后按用户授权合并；正式发布/Office/系统多屏DPI/真实企业样例等既有门禁仍OPEN，不启动下一产品阶段。原生原图见 docs/ui/new-accounting-v2/integration-review/。

---

## PR63 原实施记录（历史证据）

# 新建核算第二批当前状态（2026-10-29）

已整合PR60/PR62合并main2244425，产品源a0dabc8，Frozen锁ee5feb0不变。本任务不涉及中央公共Contract，17正式方法及show/hide配对AST与main相同；家族统一/40DIP/窗口品牌DPI/小屏/wheel、非UI层、原五页/模板/Word/依赖/workflow保护。

R8 astra视觉门禁通过：本轮18张代表图，承接R5全92张及R6燃料复核；92图片/171全页源/148旧项目源/两脚本hash核对。当前25张原样图，源a0dabc8。全页Record0，legacy结果图1条合成Record，其余0。

本地R24几何2/2 37.773s；R26原三档/原60秒保护1/1 171.652s，实际55.946/56.274/56.461；R27受影响40/40 478.760s；R28标签/几何2/2 34.274s。Canonical/compileall/pip check exit0。所有失败/剖析/中断保留，各组重叠不累计为全量。

2026-11-04 本地完整清单复验通过。冻结提交 6036f11 的 unittest discover 清单分五段执行，1150 项全部通过，五段退出码均为 0，测试累计 3238.659 秒，375 项源码哈希前后一致。前序中断和失败日志已保留。交付断点为稳定推送并创建独立 PR，随后取得同一 PR head 的 required CI 和精确包交源验收。详见 IMPLEMENTATION_REPORT。
