# 首次打开核算页：固定采样协议

2026-10-21；生产基线PR55 merge bb28ffe4c4c2733de57a3c6be8a63ee8c3b1b9ec。旧导航raw只读保留。root唯一生产写入者/性能测量者；文档代理仅写DELIVERY，不跑测试/build/GUI/测量。无原生桌面操作。

先在diagnostic-01独立运行cProfile（不入主统计），再冻结本协议与worker：正式before/after各20个独立新进程，顺序分2批×10；每进程真实compose完整catalog、窗口show及一次事件泵后，第一次HOME→NEW_ACCOUNTING计时，随后2次HOME→核算页缓存返回单列。原始值全部保留；n=20 empirical nearest-rank p95只描述本批，不视为SLA或稳定尾延迟；fresh进程不等于磁盘冷cache，不清cache/改电源。

固定CPython3.12.14及原依赖、Qt offscreen、请求窗口1280×800。固定3个seed数据库，200合成导航Record/20项目（来源上一导航批seed，旧文件不改）；每进程逐字节复制，前后核3库SHA。计时worker SHA与操作不变。各run唯一目录tmp/n-first-open，不覆盖旧样本，正式结果落本目录。后台CPU累计快照/电源计划只读，无法完全控制背景负载。

分项含Page构造、各业务区构造、样式、默认状态/dirty安装、仓储/目录查询、Resolver、shell布局和事件泵。包装器记录inclusive/self/calls：self只扣已包装子调用，不是完整native profiler的exclusive，不可跨分项加总；正式值无cProfile。Paint过滤器在page构造返回/入栈后、显示前安装，只记录首个offscreen Paint或null，不声称实际屏幕首帧。默认dirty、控件数量与初始化形状在计时外核验。查询/资格逻辑、校验、草稿、正式Profile/Record/Word不变。

依据证据试最小可逆候选，候选诊断另存。禁止以丢输入、跳刷新/验证、过期缓存或少显示必要内容提速；若涉及真实专业/重大架构选择只停相关项。对应回归和构建在正式采样之外串行。完成后单次稳定push/新PR正常CI交源独立验收，不自动合并，不进入RS04/RS05或商业交付。

## 装置修正与正式序列身份

首轮before-01及parent-probe-01/style-probe-01保留为无效装置诊断：v1计时包装器`*args`改变PySide6无参槽自动丢弃信号实参的行为，出现回调TypeError，但进程退出仍为0。不能以原failures数组为空宣称Qt成功，不纳入收益。v1原脚本字节存HARNESS_V1_INVALID.py.txt（仅历史存档，不在该路径直接运行）。

修正版本保留无参槽真实Python arity，并用sys.excepthook捕获Qt回调异常且在worker结束assert为空。1进程harness-check-02通过后，正式改前改为before-02的20新进程；worker SHA为7ad87b464e8e27fa882cd3b8409222dafcb5fa36e1612c52468357579f684dd5。正式after必须与此SHA及三库字节一致；v1数据绝不混入统计。独立未包装cProfile诊断不受此装置问题影响。

## 顺序结果与追加平衡机制对照

before-02/after-02各20进程保留为正式顺序生产结果：median3574.161→3383.047ms仅降5.3%，p953925.199→4398.563ms升高，不能称稳定提速或达标。查询/Resolver调用次数及默认形状相同，但其他构造/查询用时也变化，需排除阶段性环境漂移疑虑。

追加独立balanced-01：20对独立进程，策略顺序按legacy/final、final/legacy交替，形成ABBA平衡。所有进程同生产代码、同原worker函数SHA与3库seed；仅在相同外层factory包装中指定旧AppShell parent或最终page_stack parent，准确对应生产一行策略差。外层两策略都装相同Page事件探针和addWidget计时，记录换父/样式变化次数、插栈耗时。此为机制控制序列，单独统计，不替换/合并顺序数据，不用于掩盖顺序p95变差。若证据仍不足，不硬凑性能结论。该序列与回归/build串行。
