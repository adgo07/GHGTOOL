# N 导航性能定位与最小优化：结果

2026-10-21；改前生产 `e186b5116f16861bc65fbb939abec750a39d7f0e`，改后生产 `2a8d83bc9031837a3496b95f97653e30a4437596`。全部本地源码/Qt offscreen证据；未宣称原生首帧或实际EXE性能。历史B/N基线及其源验收见 `../n-baseline/`，本包独立送验。

## 发现与修改

pilot与正式改前分项均定位到 `scroll_host.setStyleSheet`：已有大编辑页隐藏时，祖先重设样式仍遍历其后代，缓存导航中位数约1秒，祖先setter本身约0.98—1.05秒；geometry仅约0.9—7.5毫秒。guard诊断证实仅跳过相同字符串可将业务直达降至8—18毫秒，但HOME往返仍724—912毫秒。

因此只改shell背景绘制：`ContentHost`内一个无业务后代的背景兄弟层，沿用HOME渐变和业务纯色token；resize时覆盖host.rect并置底，鼠标穿透且不接收焦点。导航仍执行原refresh/布局/滚动恢复。背景仅比较实际styleSheet再设置，无新的业务缓存或失效机制。Domain、Application、Resolver、Numeric、Record、Word、项目codec、数据库和模板均无diff。

## 严格同库前后对照

before.json与after.json（after-02）各3新进程，每路线30稳态、3首用，共702主样本，0失败。三个种子数据库逐字节相同，计时worker脚本SHA一致；三批顺序、依赖、200合成Record/20项目和窗口相同。first_use阶段后所有页面已创建，再采稳态。每次目标先经HOME重置，HOME自身先经STANDARDS。

| 路线 | 改前 median / p95 ms | 改后 median / p95 ms | median 降幅 |
|---|---:|---:|---:|
| home | 1050.601 / 1327.944 | 29.251 / 32.886 | 97.2% |
| standards | 1023.337 / 1333.130 | 16.360 / 17.317 | 98.4% |
| new_accounting | 1060.928 / 1357.774 | 22.957 / 24.080 | 97.8% |
| excel_import | 1038.456 / 1323.839 | 22.353 / 23.771 | 97.8% |
| records | 1207.047 / 1520.322 | 161.562 / 172.972 | 86.6% |
| factors | 1095.848 / 1384.592 | 17.814 / 19.083 | 98.4% |
| settings | 1091.305 / 1434.492 | 14.254 / 15.653 | 98.7% |

业务直接导航单列：STANDARDS/RECORDS/FACTORS/SETTINGS中位数由1084.220/1112.471/1120.641/1086.701ms变为9.999/18.406/15.203/7.747ms。逐批逐场景全部查询调用次数一致，未通过减少查询/刷新提速。分项嵌套不可加总。

首用新建页总中位数4055.123→3409.126ms（约15.9%），但构造本身2990.889→3019.676ms，未解决约3秒控件构造成本；仅3值不足以证明构造退化或改善。首用p95是3值中的max（4210.888→3702.938ms）。记录页经HOME返回仍约162ms，保留原刷新行为。历史14.543秒首次值不是本次改前对照，不作跨运行提速结论。HOME/标准页已在窗口或重置步骤创建，first_use不代表它们的首次构造；原始created标志可核。

Paint探针在页面创建返回后/显示前安装，原始分项与可用样本数在COMPARISON；新建首Paint中位数4049.979→3403.942ms，只是离屏绘制事件，不是用户屏幕首帧。单次事件泵未发Paint时保留null，不补造等待值。

## 核验与局限

本地对应回归42+37=79项，0失败/错误/跳过；125%与150%各重复3项背景测试，均PASS。真实完整生产页两尺寸16组同状态像素完全一致；定向控件夹具另有18组像素对照，隐藏编辑页StyleChange=0，输入焦点/草稿/滚动通过。缩放是离屏自动检查，未替代原生DPI/IME/鼠标验收。

首轮定向3测试曾有7个失败断言（测试夹具未复现plain QWidget的QSS绘制标志及长布局），仅修测试后通过，原日志SHA保留。after-initial-diagnostic.json使用重建项目UUID/时间，保留作诊断；最终正式after使用原seed字节副本。全部诊断保留，无择优覆盖。

电源计划只读为平衡；后台进程CPU快照是累计量，无法完全控制负载，也不是利用率。未改电源/清cache，fresh进程不等于磁盘冷缓存；单机/合成规模不构成企业性能或SLA。首次构造优化、原生Office/中文IME/人工DPI/企业实样/干净机/许可门禁继续OPEN。本地未重跑全量套件/build/实包；本包正常一轮CI由PR核验，旧PR54 CI290不背书本改动。

## 可复核文件与命令

- PROTOCOL.md：采样与严格seed补测边界。
- before.json / after.json：正式702样本；COMPARISON.json：确定性统计、分项、Paint、查询一致性及raw SHA。
- pilot.json / guard.json / after-initial-diagnostic.json：保留诊断；production-parity.json：16组实际页像素摘要。
- VALIDATION.json：3库字节SHA、旧raw保全、依赖、准确回归命令/数量/耗时/失败和日志摘要。

在对应生产基线上复制测量脚本，以现有依赖执行：`python -B scripts/profile_n_navigation.py --run before-01 --workers 3 --repeats 10`；改后执行 `python -B scripts/repeat_n_from_seed.py after-02`。run目录须全新；种子与worker产物位于忽略的tmp/n-navigation。统计复算：`python -B scripts/summarize_n_navigation.py`。JSON字节保全，原raw SHA `ee02b8b7cb5ac4227f2afee5005aa1c90a7ab833c61c2c346fcc93425090edac`不变。
