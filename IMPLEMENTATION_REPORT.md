# 实施报告 — N导航背景性能优化

2026-10-21送验前本地断点。生产改动提交 `2a8d83bc9031837a3496b95f97653e30a4437596`；最新PR head、CI和源验收以PR/交接回执为准。本包基线为PR54 merge `e186b5116f16861bc65fbb939abec750a39d7f0e`；旧B/N收口及CI290仅属于原阶段。

## 平台 / Contract 预检查

已实际确认工作树、canonical origin adgo07/GHGTOOL、fetch、main和基线祖先关系，在隔离codex分支实施。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`，验证中央origin后按锁读取Architecture2.1/Numeric1/Profiles1，ACTIVE UI v0.2按已合并main读取。MUST：分层/同Canonical与Application、声明Profile/ambient独立/精确正式比较、Record不可变及冻结消费者；MUST NOT：跳业务刷新/验证/持久化、遥测回流、历史重算、擅改公式/标准范围/Frozen。Carbon p40/HALF_UP是ALLOWED PROJECT DIFFERENCE，计时为非业务遥测。本任务不修改中央公共Contract，无冲突/中央缺口，无需中央变更。相关Standard Issue016/017/018/020沿用，未改变软件解释，未新增标准事实。

## 修改与证据

root唯一生产写入者/测量者，代理只读静态分析并已结束。先pilot，再before三批、幂等诊断、生产最小改动、对应回归、after、种子一致性复核后after严格补测，全部性能样本不与测试/build并发。仅shell.py新增背景兄弟层：保持token、覆盖host尺寸、置底/鼠标穿透/无焦点，避免祖先QSS遍历缓存编辑器。刷新、布局、滚动恢复、草稿和正式业务逻辑原样保留。

正式前后各351导航样本，0失败；200合成Record/20项目、同机同依赖同操作，三个SQLite种子字节相同，worker SHA相同。缓存导航median由1023—1207ms变为14—162ms，降86.6%—98.7%；新建返回1060.928→22.957ms。首用新建4055.123→3409.126ms，但构造2990.889→3019.676ms基本未改善，后续不擅自lazy重构。完整分项、Paint、查询次数一致性、原始值和局限见docs/performance/n-navigation/RESULTS.md及JSON。

## 本地验证（与CI分开）

- `python -B -m unittest tests.test_g03_shell tests.test_uat02_geometry tests.test_uir02_source_cards tests.test_standard_dispatch tests.test_record_summaries tests.test_navigation_background -v`：42项/46.970s，0失败/错误/跳过。
- `python -B -m unittest tests.test_accounting_projects_ui tests.test_uat02_usability tests.test_p3_ab_standards -v`：37项/150.578s，0失败/错误/跳过。
- `QT_SCALE_FACTOR=1.25`和`1.5`分别运行`python -B -m unittest tests.test_navigation_background -v`：各3项/1.144s和0.584s，均0失败/错误/跳过。
- `python -B scripts/probe_n_background_parity.py`：实际完整生产7页/两尺寸含长页底部共16组像素完全相同；定向夹具另18组，StyleChange=0及焦点/草稿/滚动通过。仅离屏视觉证据。
- `python -B scripts/summarize_n_navigation.py`与证据核验：702主样本、3seed逐字节一致、worker同SHA、每场景查询次数一致、旧raw SHA保留、权威业务路径零diff均通过。
- `python -B -m py_compile`核本包5测量/统计脚本、shell和新增测试通过；`git diff --check`通过。未本地跑全量套件、build、真实企业库或原生交互；本包一轮正常PR CI另核，不能挪用历史CI290。

## 失败、更正与剩余

初始定向3测试有7个失败断言，原因是测试夹具的旧QWidget子类QSS模拟及长布局构造；只修测试后PASS，日志SHA保留。after-01重建项目UUID/时间，保留作诊断，正式after-02改为原数据库副本；计时worker未改。环境后台无法完全控制，CPU累计快照/平衡电源只读，不改设置或清cache。旧raw、诊断及初次after均不覆盖。

新建首次构造约3秒与记录页经HOME返回约162ms仍有余量；无扩大架构优化。原生Office/IME/鼠标/人工DPI/企业实样/干净机/许可门禁仍OPEN；无公式/Numeric/Record/Word/codec/数据库迁移/模板/中央Frozen/标准范围变更，不进入RS04/RS05或商业交付。稳定后一个PR/必要CI送源独立验收，不自动合并。
