# PR62 测试成本与覆盖核对

2026-10-29；本文件是本工作包证据，不是新路线。目标为保留覆盖、控制执行成本；不承诺30分钟，不增加40分钟预算，不改required范围，不拆工作流、不移夜间。

## 日志证据与口径

- main基线CI311 / run40302567376：全量1122项，2107.461秒；完整全量步骤2115秒。精确head Standalone Audit 另约262秒，G08 22项12.620秒。
- PR62 CI316 / run40725201083：全量1133项，1587.264秒，1失败；全量步骤1593秒。失败是缩放输出协议不匹配，Standalone未执行。
- 以上是GitHub Actions，不是本地。日志时间戳的测试整行通常在完成时输出，下面以相邻完成行间隔估计，包含当前测试setup/body与前例cleanup、类切换及日志缓冲；不能当作独立测试精确计时，更不能据此单独宣称某算法慢。

| CI316模块 | 累计相邻完成间隔估计（秒） |
|---|---:|
| test_g06_page | 147.4 |
| test_accounting_projects_ui | 98.5 |
| test_b_fgd_acceptance_fixes | 97.9 |
| test_b_fgd_chain | 97.7 |
| test_business_pages_visual | 73.7 |
| test_uat03_page | 72.2 |
| test_b_fume_chain | 67.8 |
| test_pr59_compatibility_navigation | 58.4 |

较大单次间隔为business_pages_visual因子模式控件53.2秒、FGD旧投影25.5秒、PR52实际关闭重开/冻结Word25.3秒、缩放父测试22.1秒。末项在第一档输出断言失败后即停，不能据此宣称三档全过。

## 重复验证覆盖表（本批保留全部）

| 入口 | ref / 范围 | 与其他入口重叠 | 保留理由 |
|---|---|---|---|
| Merge job独立UIR04 GUI脚本 | merge ref，实际GUI场景 | unittest部分业务断言 | 集成入口独立验收 |
| Merge job独立scale脚本 | merge ref，125%/150% | discover父测试三档 | 独立探针；原required步骤不擅改 |
| discover缩放父测试 | merge ref，100%/125%/150% | 上述两档 | 还检查子进程退出码及输出协议 |
| discover G08 | merge ref，真实wheel/sdist安装及交付 | exact-head G08 | merge集成与PR头不是同一对象 |
| Standalone GUI / scale / G08 | 精确PR head | merge同类场景 | 构建的源码必须精确head绑定 |
| standalone build/audit/archive/provenance/smoke/upload | 精确PR head可执行包 | 资源检查部分重复 | 实包与源码测试对象不同，不删 |

CI316独立scale两档38秒；CI311两档56秒，精确head两档60秒。真实wheel/sdist测试相邻间隔CI316约2.805秒、基线精确head约3.684秒；完整基线G08仅12.620秒。不是当前主要成本，不移除实际构建或污染环境安装探针。

## 本地实测与已实施的小改动

环境Python3.12.14 / PySide6 6.11.2，Windows，offscreen，TEMP/TMP为隔离目录；机器上存在其他仓库测试，时间仅供定位，非独占机器基准。

1. 缩放脚本逐阶段flush输出，保留60秒子进程保护与全部行数/尺寸/边界/重叠/删除断言。100%一次直接运行40.636秒：imports0.767、Qt0.013、catalog6.418、窗口/核算页6.285、动态行24.483、几何1.075、可达/删除1.019、清理0.576。无固定sleep；没有证据支持盲加预算。诊断初版三档132.485秒通过；新增实际DPR断言后最终149.765秒通过。CI317三档实际14.130/14.409/14.451秒全部通过。
2. 父缩放用例的setUp不再创建无断言用途的第二个核算窗口；每个子进程仍独立catalog、window和record repository。协议严格检查version/scale/实际DPR/work_area/PASS/failures/client/cleanup及exit0；超时保留配置、stdout、stderr/最后阶段。
3. 改前项目页两轮setup22.338/17.444秒，teardown0.003秒后Qt对象仍存活；显式DeferredDelete后失效。FGD窗口ready39.453秒、总39.465秒，结束后仍活、派发后失效。堆栈显示SQLite迁移初始化耗时，未改变数据库迁移或事务策略。
4. 项目恢复、FGD场景及Excel入口夹具改用既有dispose_test_widget；所有原close/exit检查仍先执行。项目测试class仅共享只读catalog文件，逐例新建服务、可变projects.sqlite、内存Records和页面，类结束哈希核验共享文件未修改。未缓存用户库或正式Record。
5. 未增加全局缓存或大重构。UAT02仅有5ms固定等待，随后已有100ms有上限稳定几何观测；本批不为数毫秒扩大该已验收几何算法。生产定时器随所属窗口销毁，本批不改其业务时序。

## 覆盖前后

AST核对原6个模块74个test_*方法名不变；CI317退修另覆盖SourceDirectory的14项，共7模块原88例方法名全部保留。没有删除/skip任何例或业务断言；缩放新增结构化协议，最小尺寸由仅上界改为正常工作区精确960×600并检查可用正文；小工作区同时检查适配尺寸和实际控件两端可达。

改后：共享目录一次11.363秒，项目两轮setup50.060/12.248秒、销毁1.504/0.070秒；FGD ready27.775秒、总28.010秒，所有对象在teardown后立即失效。并行I/O波动下不能宣称净提速。150%小工作区带抓图额外运行71.492秒（导入27.793秒），通过全部几何与可达断言；不套用或提高父测试60秒上限。CI317全量1133项1139.059秒有14个setup错误，均因借用项目setUp的SourceDirectory未同步class catalog生命周期；这14个业务体未执行，不能宣称19分钟达标。已补全该消费者独立初始化/结束校验/清理，保留14个测试体；定向15项已通过，288.347秒、0失败/0错误，两类catalog哈希/清理通过。新head required/包证据见IMPLEMENTATION_REPORT和PR最新回执。
