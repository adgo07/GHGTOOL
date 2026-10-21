# N 导航性能定位与最小优化：采样协议

2026-10-21；基线 main `e186b5116f16861bc65fbb939abec750a39d7f0e`。旧 `../n-baseline/raw.json` 保留，不作为本次改后样本。root 是唯一生产修改者和测量者；并行代理仅只读静态分析，测量期间无测试/build。

## 先定位，再修改

`profile_n_navigation.py --run pilot-01 --workers 1 --repeats 1` 是诊断预试验，结果单独保留、不纳入主统计。确认计时和瓶颈后，以同一脚本、运行时、同机、同数据和顺序执行 before/after 各3个新进程，每进程先逐页首用，再10轮稳态（每路线30个稳态值、3个首用值）。首用不冒称磁盘冷缓存；没有人为清缓存/改电源。记录电源计划及采样前后累计CPU最高的8个进程，累计CPU不是瞬时利用率，后台环境无法完全控制。

## 数据与操作

复用旧基线 `compose()` 的真实生产窗口/完整catalog配置和 `benchmark_navigation.make_record()`；全新临时SQLite含200合成导航Record/20空项目，不读企业或用户库。固定窗口1280×800、Qt offscreen。每个目标先返回HOME（HOME自身先转STANDARDS），调用程序导航并做一次 `app.processEvents()`，与旧基线导航边界一致。另按STANDARDS→RECORDS→FACTORS→SETTINGS直接业务导航，单列结果，不混合统计。

## 分项与限制

记录同步navigate、事件泵、show_route、ensure_page、祖先setStyleSheet、geometry、记录/项目查询的次数与纳秒值。分项有嵌套，不能相加当总耗时；ensure_page首用包含完整构造，返回时是缓存查找。页面Paint过滤器在ensure返回后、显示前安装，首Paint时间可能为空（当前页面已可见或一次事件泵没派发），不额外等待制造用户首帧结论。Qt离屏Paint不是屏幕可见帧、人工鼠标、DPI或原生体验验收。首次构建大项必要时另开诊断，不能把带profiler的值混入主统计。

原始JSON写入唯一 `tmp/n-navigation/<run>/raw.json`，禁止覆盖；最终复制到本目录并保留字节与SHA。每批记录production摘要、基线diff、实际head和脚本SHA，未提交代码必须由diff明确辨认。median与nearest-rank p95均从原始值复算，n=3首用p95实际是max，不推断稳定尾延迟/SLA。

只实施证据支持的小改动；不得跳刷新/校验/持久化、少显示必要内容或引入陈旧缓存。草稿、来源资格、Numeric、Record/Word、标准范围和中央锁不变。对应shell/geometry/draft/record refresh回归在采样外串行执行。新PR由源独立验收，不自动合并。

## 数据一致性复核补充（采样后登记）

首轮after-01使用相同生成方法/规模，但项目UUID与保存时间不同；该批保留作诊断，不作为正式改前改后对照。最终after-02通过 `repeat_n_from_seed.py after-02` 将before-01/seed的3个数据库逐字节复制，仍调用完全未改的 `profile_n_navigation.py --worker`（同SHA、同worker和操作/重复数）。外层仅变更种子准备方式，运行不与回归并发。对照报告记录3库SHA相等及外层脚本SHA；不覆写任何已采原值。复现guard-01需在e186的生产代码上运行同名探针，after生产代码已无祖先setter，不应冒作guard实现。
