# 首次打开核算页：结果与限制

2026-10-21。改前生产PR55 merge `bb28ffe4c4c2733de57a3c6be8a63ee8c3b1b9ec`；改后生产 `dacddd56f546e564ca6263282f88231f8d274dd2`。本地源码、合成数据库、Qt offscreen；当前候选不是正式Release或原生首帧验收。

## 最小改动与定位

独立cProfile诊断显示，完整控件树构造、末尾全树样式及插入QStackedWidget均有成本。运行时小候选分别比较最终父容器、提前静态样式及两者组合；提前样式虽看似更快，却导致6/30组FGD/电力位置快照中的分段控件宽度不同，因此完全撤回。最终生产仅shell.py一行：NEW_ACCOUNTING的控件直接以最终page_stack为parent构造，插栈时无需再次换父并向3409控件传播样式；控件、内容、默认值、刷新、校验和业务方法均保留。carbon_material_page.py零diff，没有引入缓存/lazy构造。

## 装置问题先更正

v1计时包装器使用`*args`，改变PySide6对无参槽自动丢弃信号实参的处理，出现Qt回调TypeError但进程仍以0退出。before-01的20进程及两个v1候选全部保留为无效诊断，不能以failures=[]宣称成功，不用于收益。原脚本字节见HARNESS_V1_INVALID.py.txt。修复真实arity并安装sys.excepthook断言后，1进程装置核验通过，才重采before-02/after-02；此后worker SHA固定为 `7ad87b464e8e27fa882cd3b8409222dafcb5fa36e1612c52468357579f684dd5`。未包装cProfile另列，不入正式样本。

## 顺序生产前后：收益弱、p95变差

before.json与after.json各20独立新进程，每进程首开1次、缓存返回2次；同机/依赖/请求窗口、同3库seed字节、同worker/操作。0进程失败、Qt回调错误为空；全部配对的查询/Resolver调用次数与初始化形状相同。

| 顺序系列 | n（前/后） | 改前 median / p95 ms | 改后 median / p95 ms |
|---|---:|---:|---:|
| 首开 | 20 / 20 | 3574.161 / 3925.199 | 3383.047 / 4398.563 |
| 缓存返回 | 40 / 40 | 25.995 / 32.751 | 24.674 / 35.340 |

首开median仅降5.3%，p95升高，不能宣称稳定提速或达标。ensure_page未包装子项的self中位数662.91→22.57ms，而Page构造2371.52→2839.83ms、Record读取146.27→164.68ms等也变慢，存在阶段环境/时序漂移疑虑。上述self只扣已包装子调用，不是完整native exclusive。

## ABBA机制对照：独立报告，不覆盖顺序结果

为核机制，追加20对新进程，顺序legacy/final、final/legacy交替。两策略均在相同外层factory中指定parent，准确对应生产一行差异，使用同原worker函数/seed，均加同样的Page事件与addWidget探针。该序列独立统计，不与顺序生产数据合并，不掩盖顺序p95变差。

| 机制控制系列 | n（每策略） | 旧parent median / p95 ms | 最终parent median / p95 ms |
|---|---:|---:|---:|
| 首开 | 20 | 3227.404 / 4121.573 | 2701.934 / 3393.953 |
| addWidget | 20 | 589.805 / 733.658 | 0.351 / 0.516 |
| 缓存返回 | 40 | 22.831 / 37.315 | 21.599 / 27.997 |

配对首开中位差522.180ms，配对中位降幅16.336%，19/20对更快；1对更慢（-284.991ms差），不声称每次更快。旧策略每次插栈均ParentChange=1/StyleChange=1，新策略全部为0。所有配对查询次数、3409控件/10源卡/54字段/444默认状态键及初始dirty一致；该证据支持消除重复换父/样式传播的最小改动。主体控件构造仍需数秒，未根治首开，也未证明稳定尾延迟或SLA。

## 等价与回归

- 实际完整生产页3窗口尺寸（1180×720、1280×800、1600×900），默认页与全源启用后的各业务位置共30组像素摘要完全一致；初始与全源启用两组规范化form、全部命名控件属性及dirty完整一致。比较独立创建状态时归一化32位随机UI身份；历史稳定身份另由项目回归守护。完整快照/PNG保留tmp，仓内SNAPSHOT_PROOF给完整文件SHA、状态/控件/像素摘要和拒绝候选差异。
- `python -B -m unittest tests.test_standard_dispatch tests.test_g03_shell tests.test_uat02_geometry tests.test_uir02_source_cards tests.test_navigation_background -v`：37项/55.340s，0失败/错误/跳过。
- `python -B -m unittest tests.test_accounting_projects_ui tests.test_uat02_usability tests.test_p3_ab_standards tests.test_record_summaries -v`：43项/158.445s，0失败/错误/跳过。采样和测试/build不并发。
- 新增行为测试验证插栈/复用无换父/样式变更、半填输入保留且3次refresh仍执行。负控制强制旧parent时该测试预期出现1个断言失败（0 errors，0.681s），外层检查确认PASS；不计入80项生产测试通过数，也不冒称产品回归失败。
- worker/3库字节/v1存档身份、旧N原始hash、业务与旧证据路径零diff均核验；本包脚本/测试/shell的py_compile与diff --check通过。原生桌面/Office/IME/人工DPI/企业样例/干净机未执行；本地未全量测试或build，研发工程CI由稳定PR另核，旧CI292不背书本改动。

## 复核入口与开放项

`python -B scripts/profile_n_first_open.py --run <全新run名> --workers 20`采顺序系列；`python -B scripts/profile_n_first_balanced.py --run <全新run名>`采独立机制控制。固定seed在tmp/n-first-open/seed，每次复制并核SHA；不得覆盖既有run。统计复算：`python -B scripts/summarize_n_first_open.py`。COMPARISON含分项/首Paint/配对差与raw SHA；VALIDATION含准确命令、依赖、数量、日志摘要与排除原因；DIAGNOSTICS保留装置检查、有效/无效候选及cProfile时间。

首Paint只代表离屏Paint事件，null如实保留，不能当实际屏幕帧。20值p95是该批经验最近秩，不是稳定尾延迟；fresh进程不是磁盘冷cache。电源平衡只读，后台累计CPU快照不能视为瞬时利用率或完全控制环境；未改电源/清cache。顺序结果与对照分开、拒绝与无效数据保留。

并行交付清单整理仅改现有docs/DELIVERY.md，核v11/2.9.0真实模板摘要与包体provenance机制，正式Office保存回导、IME鼠标DPI、企业样例、干净机及许可/Release门禁全部OPEN。研发N测量/回归/工程CI与正式交付门禁分开，不升级SUPPORTED、不进RS04/RS05、不作商业交付声明。

新增保护测试模块补充默认offscreen环境后，单项复验1项/3.029s PASS（0失败/错误/跳过）；该用例已含在80个主回归中，不累计为81个不同用例。
