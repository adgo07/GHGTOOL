# PR46 验收修订实施报告

2026-10-14。继续原 PR46，未合并。当前修订覆盖此前六包交付的展示和输入政策；旧 head 的 510 项与 Windows CI219 仅为历史证据，不代表本轮验收通过。

## 平台 / Contract 预检查

业务基线 main：204dded5d03853617f79a1f05693e89b619df9d1；修订前 head：0e2780aa27c8a615f0086ba393b33fdad91682ef；本轮生产验收 head：8d87199f25bd17e56e2e8443e09575966d557f12。origin 已实查为 adgo07/GHGTOOL，独立分支 codex/ghg-standard-input-unification；保留原主目录用户改动。中央锁定 ee5feb0cc34dbd99790500fadd0c4c932e202a20，Architecture V2.1/Numeric v1 不变。适用 MUST：分层、共享正式 Calculator、完整 Decimal 精度、显示修约不回流、不可变 Record/冻结来源及历史不漂移。MUST NOT：第二算法、修改历史 Record、静默改来源、变更 Frozen/Profile。当前 UI 指南为 ACTIVE v0.2。

Issue010 已登记 Owner 批准的输入政策和五表接线，覆盖 Issue008/009 的旧软件限制；不修改标准原文、公式、系数、操作顺序或 Frozen Contract。没有中央 Contract 冲突或升级。

## 当前落实

- 名称输入与确认分离，目录/自定义精确匹配；删除自定义燃料复选框。单位改变保留可恢复旧草稿并清空活动量，不作隐式换算。恢复不覆写保存值；若保存的STD值与当期目录不同，显式要求重新确认，不静默计算另一个值。
- 新来源使用缺省/计算/实测相连分段按钮；历史 USER_DEFINED 保留原证据。目录 FCh 明确计算/实测来源时允许编辑，GUI/Excel/正式校验共同调整。
- 顶部与正文排放源开关共用状态，停用保留输入。脱硫新建一组分，新增项不改兄弟来源或各套同一比例。电力全国表1/4/5、区域表2、省级表3的查询、界面、Resolver、Canonical、快照及Excel均已接线。原选因子失效时保留ID并阻断购入/输出，表4/5不自动补位。
- Record 两个既有页签使用真正只读表格，Word 仅输出必要业务注释；完整追溯留在 source_detail，不回查 Catalog。
- 导出目录采用系统文档位置下“青舟温室气体核算/导出文件”，设置保存在现有 user.sqlite；模板与 Word 共用，单次另存不改设置，覆盖/权限/审计保留。
- 受控模板候选 2.1.0（SHA256 `f303ad02ca03e0464f736dafc39967abd06366a902f1b502dd17470656eb1718`）增加必要来源选择，仍逐字节复制；旧 2.0/1.0 和历史 EXCEL_R2 读取保留，用户 docs 母版不变。

## 全链清理

| 处理 | 实际范围及依据 |
|---|---|
| 删除 | record_experience 中 4 个死常量及旧聚合/专业/汇总包装函数共 182 行；pages 旧导入移除；记录页已消费同一冻结 ReportModel，测试迁到 B.1 ES/EI/ET 与缺项证据。 |
| 合并 | 重复 _bind_fuel_aliases 保留具直接含碳量路径的一版；燃料/碳酸盐共用 NameSelector，来源共用 SegmentedChoiceControl，模板/Word 共用 ExportLocationService。 |
| 保留兼容 | 旧能源隐藏控件仍被 objectName 序列化、_migrate_legacy_energy_rows 和校验定位读取，不能凭隐藏判死；旧模板资源及索引/USER_DEFINED 仅用于兼容，不向新录入伪造来源。 |
| 保留可达适配 | build_report_view 仍用于测试及动态验收脚本，保留冻结文本适配；不删动态 Qt/serializer/标准注册路径。 |

## 已实际执行的本轮验证

- 燃料确认、同种重置、单位草稿、来源编辑、恢复与上下开关：6/6 通过；另分段键盘测试通过。
- FGD：独立 4 项、G06 两项和定向组合 10 项均通过（不同组合不累加为全量）。
- Record/报告清理组合 51 项通过；rs02_record_evidence 9 项通过。首次组合旧文案 2 项失败已迁到冻结业务字段并通过。
- 统一导出/设置/UI/应用组合 42 项通过，Python 3.12.14。
- 新模板真实 WPS ET 12.1.0.29158 原生保存回导：17/17 通过、0失败、0未执行；九表/保护/锁定图、完整输入/正式结果/来源快照一致；16个数据验证约束原生保存前后相同，预览无 Record、正式一次新增一条。验收 helper 首次误读 v2 路径导致仅 SHA 检查失败，改为显式版本参数后通过；历史证据未覆盖。
- Word：当前 TEMP 合成冻结 Record 生成 10 张业务表，WPS 兼容 COM 只读打开并导出 11 页 PDF；打开文档数前后均为 0，未 Quit 可能共享实例。最终2.1元数据已同步，11页联系图全部查看；B.1～B.9完整、无裁切/空白页，B.8必要扣减注保留，B.9逐条结果尾注及“第x行第y列”删除。证据见本轮word-wps目录，不称Microsoft Word验收。
- 两次完整回归调试未完成：首次卡在内容测试探测用户Documents，faulthandler确认 `export_location.py:168 NamedTemporaryFile`；第二次RS03旧fixture缺FCh来源N14导致3项失败，模板下载测试也未隔离路径探测；另C1一项仍模拟已移除泛化菜单。均停止并保留日志，不伪报完整统计。后迁移为TEMP chooser/成功提示mock、补N14，并保留原结果/精度/关联保护断言。
- 独立审查定位并修复：燃料/FGD恢复STD显示与正式值分叉；旧直接实测来源污染新身份；特殊电力口径/失效ID购入与输出自动回退。燃料9 + FGD6 + RS03完整10 + C1定向1，共26项通过，0失败/错误，75.791秒。
- 本地完整回归：`python -m unittest discover -s tests -t . -v`，head8d87199：561项，550通过/9失败/2错误，616.685秒。剩余8个失败为RS03旧fixture漏填2.1 FCh来源N14，已补并完整两模块9项通过（11.544秒）；另3项旧UI断言按显式名称确认、文本正常编辑/箭头展开及电力placeholder迁移后，定向3/3通过（4.324秒）。修正后的完整回归已由下述Windows CI通过；不能将本地此轮写成全绿。
- 本地Windows：`python scripts/build_standalone.py --output-root dist/pr46-reviewed` 成功；`inspect_release.py` 269文件审计通过，`verify_release_archive.py` 270可见文件ZIP回导通过，`smoke_standalone.py --starts 2` 两次隔离启动通过。source/pr-head/tested-merge均8d87199；此为本地来源，GitHub Actions另记。
- Windows Qt原生平台程序驱动：1366×768逻辑窗口，Qt scale1.0/1.25各20检查、各19次捕获（18个不同PNG）通过。涵盖正文开关、连接式分段、两类能源/过热蒸汽、记录真实表格；未改变Windows系统DPI，非真实鼠标/人工验收。
- `python scripts/validate_canonical.py`：9标准、12来源、102参数、138因子有效；`python -m pip check` 无依赖冲突；diff-check通过。

## 最终独立审查与远端CI

已核实的Windows CI #221（run38546946024，交付head e500edc65fa1191acf0197454d6ad012118f19e0）：merge-ref d30568374d7a332bc231251c34fceada06b79081完整561/561通过（747.623秒）；精确PR-head交付专项14/14通过（4.293秒），构建、271文件审计、272可见文件ZIP回导、两次启动及provenance校验全部通过。Artifact11885782152名称与head一致，ZIP59,785,100字节。后续纯证据文档提交不修改生产；最新PR head与Checks、候选下载入口以PR46正文为准，不混用本地和CI来源。

独立Luna已复核交付head e500edc：8d之后没有生产运行时代码差异，最终12项定向通过（17.326秒）；旧fixture/控件断言迁移保留原业务断言，未发现剩余阻断/高/中级生产缺陷。

## 未闭合

代码独立审查在head8d87199通过（燃料/FGD15项、G0629项），最终证据diff已在e500edc复核。原生电脑操作工具在身份修正后仍截图超时/激活失败，尚无真实鼠标或中文输入操作通过证据；Qt 程序检查不能代替它。真实企业样例/人工系统 DPI 验收仍待 Owner 实际操作。完成本轮后更新同一 PR46，等待独立验收，不自行合并。
