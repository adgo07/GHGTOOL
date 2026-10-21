# 实施报告 — 首次打开核算页最小优化与交付清单

2026-10-21送验前本地断点。基线PR55 merge `bb28ffe4c4c2733de57a3c6be8a63ee8c3b1b9ec`（源已独立PASS）；生产改动 `dacddd56f546e564ca6263282f88231f8d274dd2`。最终PR head/CI/源验收以当前PR与交接回执为准，不把旧CI292或历史基线重标为本包。

## 平台 / Contract 预检查

已实际核工作树/canonical origin adgo07/GHGTOOL/fetch/main/head/状态，从最新main新建隔离分支。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，可信中央origin核验后按锁读取Architecture V2.1/Numeric Contract v1/Numeric Profiles v1；ACTIVE UI v0.2按当前正式已合并版本读取。MUST：分层、同Canonical/Application、声明Profile与ambient独立、全值精确比较、不可变Record/冻结Word、草稿/资格/正式校验与必要刷新保留；MUST NOT：遥测回流、跳验证/刷新、旧缓存换速、历史重算、擅改公式/标准/Frozen。Carbon p40/HALF_UP为允许项目差异，计时只为非业务遥测。本任务不涉及中央公共Contract，无新增冲突/中央缺口、不需中央变更。相关Standard Issue016/017/018/020沿用；本任务不改变软件解释，无新增标准事实。

## 实施与分工

root独占生产/性能实测和TASK/HANDOFF/REPORT；gpt-6.1-sol/medium文档子代理仅写docs/DELIVERY.md，未跑测试/build/测量/GUI，root统一复核。子任务静态更新v11/2.9.0/SHA、历史证据时点、包体provenance/hash锁定与Office/IME/鼠标/DPI/企业样例/干净机/许可门禁，全部本次未执行正式交付项OPEN，不新建路线或进入RS04/05。

生产仅shell.py一行：核算页以最终page_stack为parent构造，避免插栈重复换父/全树样式传播；无控件/业务内容减少，无缓存/lazy构造。提前样式候选导致6/30像素差异，已完全撤回，carbon_material_page.py零diff。Domain/Application/Resolver/Numeric/Record/Word/codec/数据库/模板/标准范围与中央锁不改。

## 测量结果与证据界限

先独立cProfile，再正式顺序before/after各20独立新进程，首开与缓存返回分开。顺序首开median3574.161→3383.047ms仅降5.3%，p953925.199→4398.563ms变差，不宣称稳定提速或达标。因其他构造/查询也变慢，追加独立ABBA20对新进程控制，和顺序结果并列不混合。控制legacy/final首开median3227.404→2701.934ms；配对中位差522.180ms、配对中位降幅16.336%，19/20对更快，1对更慢。addWidget median589.805→0.351ms，旧策略ParentChange/StyleChange每次1，新策略0，支持这一行避免重复样式传播的机制收益，未根治数秒控件构造或证明SLA。

有效两序列共80新进程、80首开和160缓存返回；每序列0进程/Qt回调失败、同worker SHA、同3个SQLite seed字节、相同查询/Resolver次数与初始化形状。Qt offscreen/合成200Record/20项目、固定请求窗口，环境快照只读，不改电源或清cache。首Paint只是离屏事件；p95只为本批经验值，新进程不等于磁盘冷cache。完整分项、原值、配对差、协议和SHA见docs/performance/n-first-open。

## 本地验证（与CI分开）

37对应回归/55.340s及43对应回归/158.445s均PASS，0失败/错误/跳过，准确unittest命令见RESULTS及VALIDATION。新增行为回归覆盖无插栈换父/样式变化、缓存保留草稿和仍执行refresh；负控制旧parent产生预期1断言失败/0错误，外层核验PASS，不计入80生产通过数。实际生产三尺寸30像素配对、初始/全源两完整命名控件/规范化输入/dirty配对全部相同。py_compile及git diff --check通过。未本地全量/build/原生操作/企业数据；一个稳定PR正常CI另核，旧CI292不背书新head。

## 失败与排除

v1计时包装器改变无参Qt槽arity，20进程before-01与两候选出现回调TypeError但进程0退出，全部保留为无效装置诊断，不以failures=[]冒称成功。保全v1字节后修签名并加sys.excepthook断言，1进程装置检查通过才重采，正式及ABBA均用固定修复worker。提前样式/组合候选的6组像素差异导致该方案撤回。顺序p95变差、配对1例更慢均保留，不择优覆盖。

## 停止与后续

本包只提交有机制/等价/回归支持的一行改动；剩余构造成本和环境波动如实开放，不继续扩大缓存或构造架构。稳定后单次push/新PR正常CI送源独立验收，不自动合并。正式交付清单子任务与研发验证分开；原生Office/IME/鼠标/人工DPI/企业样例/干净机/许可履约和Release继续OPEN，不升级SUPPORTED、不进RS04/05或商业交付。

新增保护测试模块补充默认offscreen环境后，单项复验1项/3.029s PASS（0失败/错误/跳过）；该用例已含在80个主回归中，不累计为81个不同用例。
