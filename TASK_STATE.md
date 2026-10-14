# 当前任务状态

状态：PR46验收修订中；Owner批准11项修订及统一导出目录、Word注释和全链清理，继续原分支、不另建PR、不自行合并。
最后更新：2026-10-14。

- 身份：origin adgo07/GHGTOOL；base main=204dded5d03853617f79a1f05693e89b619df9d1；隔离分支codex/ghg-standard-input-unification。原主目录codex/ghg-ui-p3-df及用户模板/参考文件原样保留。
- PR45仍OPEN，head9cdbcaa6e7e88914036535a65f80b11d26d8839e，视觉成果经本分支5d09ae6明确整合；未在GitHub合并/关闭。
- 六包：共同输入政策/漏行修复；静态标准分派；共享燃料；多工序/脱硫/能源和项目兼容；冻结业务表；视觉与整体验证。当前均已实现；不新增第二正式标准、因子公告、数据库或框架。
- Contract：中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；Architecture V2.1/Numeric v1；当前UI指南v0.2为ACTIVE。p40/HALF_UP、完整精度、不可变Record与历史不漂移保持；标准问题009记录Owner自定义输入政策，001—008保留。
- 模板2.0.0候选SHA256：58b38c15d487bdc173f573a50e5b8f3446b5bb4df4693dd696a83742da5235b4；九表保护，B.2数据/单位及FCh独立，B.3—B.5类别/名称与工序归组，B.6多行，B.7多剂/组分；下载逐字节复制。旧模板1.0和项目codec v1继续可读，EXCEL_R2历史证据不迁移。未修改用户docs母版。
- 公共启动/壳/Excel/报告由静态注册分派；延迟页面与服务构造，未知标准/版本不回退；UI拒绝未开放入口不向Qt抛异常。新草稿保存稳定业务值，旧索引集中兼容，无数据库迁移。
- 新Record冻结FCm/FCV派生展示证据和采用来源类型；记录页/Word同一业务表投影，历史缺项不补算，不回查当前Catalog。报告模型3.0.0候选，算法版本CAR-SM01-2026-10-13-G06.4，公式/系数/Profile不变。
- 第6包：首页列宽/表头、标准筛选与支持文案、单行卡片/下置开关/浅色标题、统一14px输入和键盘二选控件已实现；普通电力提示去PDF物理页，完整定位保留tooltip/快照。

验证结果（均为本地，GitHub Actions结果另登记最终PR Checks/Conversation）：

- 完整回归：89246be3842b92be19f1d6df3a99b894205550f2，python -m unittest discover -s tests -t . -v，510通过/0失败/0错误，413.123秒。
- 此后仅电力提示展示与验收辅助脚本TEMP约束变更；相关formal_workflow/rules/dispatch 27项通过，15.699秒；正式输入/公式未变。最终head完整回归以PR Windows CI为准。
- 首轮482项：475通过/5失败/2错误；修复UI拒绝路由及旧常量/视觉/版本/来源断言。第二轮510项：509通过/1失败/0错误（436.176秒），为UI拒绝方式旧断言；分派9项复测通过（0.132秒），之后完整510项通过。先前各包命令在Git历史中保留，不累计冒充全量。
- Windows构建89246be通过：build_standalone --output-root dist；inspect_release 268文件通过；verify_release_archive 269可见文件/ZIP往返通过；smoke_standalone 2次隔离启动通过。首次成功构建输出被并行验证误清理，已重新构建并复核来源，不作为可交付产物。
- Canonical：9标准/12来源/102参数/138因子有效；compileall通过；pip check无冲突（首次venv缺pip，ensurepip补齐后实际运行）；四库从零初始化通过。
- UIR04程序驱动场景A—E 5项通过；离屏125%/150%动态布局通过，非人工操作证据。
- WPS ET 12.1.0.29158原生TEMP副本保存回导17/17通过：9表/保护/锁定图不变，无公式新增，21处仅空白None→空串，其他单元格值不变；完整输入/结果/16参数快照/15trace一致；预览零Record、正式新增一条。
- Windows Qt原生平台1366×768逻辑窗口、Qt scale1.0/1.25各20项通过；截图及源文件哈希见docs/ui/standard-input-evidence。未改变Windows系统DPI。
- WPS 12 Word兼容COM原生导出PDF，11页全部查看；1条合成Record→10张业务表，无裁切/空白页/内部编号。LibreOffice技能renderer实际失败（缺soffice），未声称Microsoft Word验收。
- 独立Luna审查base204dded→89246be：未发现阻断/高/中级生产问题；回导辅助脚本TEMP约束建议已采纳。最终小改与交付head继续复核。

未闭合：最终head GitHub Windows CI及最终独立验收；Owner真实企业样例和人工系统DPI操作验收。报告/截图均明确为合成数据，不用离屏测试替代原生验证。不自行合并、不实施其他阶段。

- 最新补充覆盖旧展示/来源政策：Issue010已登记；名称确认/重新选择重置、单位草稿防误用、真实来源分段控件、电力五表正式链、统一导出目录/必要Word注释及Record实际表格。前510项仅为旧head证据，本轮须重新验收。
