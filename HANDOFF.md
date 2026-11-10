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

# 新建核算第二批交接（2026-10-29）

沿用codex/new-accounting-page-v2，非破坏性整合PR60/PR62合并main224442530fcc61d8224c45e486688b2c27ec9324。产品源a0dabc8ca49e744ef73704a126c2eaae2fc314dc；当前25图/源码清单、预检查与真实测试见IMPLEMENTATION_REPORT。批准附件SHA256=4922b39e0a3052ba956c54ad64951932e5535c60685f8c8ab1fb4bceacb89d73，仅本批新建核算全页。

Owner直接授权本批全部后续astra复核，R8门禁已通过：本轮18图+R5全92图+R6燃料复核，新图/源/脚本hash通过。旧原件/失败不覆盖。R24/R26/R27/R28对应回归通过，原60秒和40min预算/原断言/原测试方法保留。

Frozen锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，本任务不涉及中央公共Contract，不改Issue015/016/017/020解释。家族统一、配对/wheel及17正式方法保护，可变项目/不可变Record/Word链不变。

2026-11-04 本地完整清单复验通过。6036f11 的 1150 项按原发现顺序分五段运行，均通过，累计 3238.659 秒，源码哈希、退出码及日志已保全。交付断点为推送独立 PR、取得同 head required CI 与精确包并交源验收。

仅Qt offscreen合成隔离库，根用户工作簿不动，无原生CU/变通桌面/Office/IME/人工DPI/企业数据。
