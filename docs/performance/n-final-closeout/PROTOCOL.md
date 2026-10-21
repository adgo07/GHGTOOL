# 最终有限收口测量协议

基线为PR56 merge59cab091aab0df44b147f2bba3b960085dbae168。只试一个四行候选：来源卡片、统一能源卡片/行和过程行以最终layout的parentWidget创建；不移动样式时点、不缓存/lazy/减少控件，不改业务。

1. 候选诊断diagnostic-01独立2对/4新进程，ABBA顺序；仅筛选，不并入正式结果。脚本后补生产字节身份字段，诊断与正式control SHA分别保留，不伪称相同control字节。
2. 实际生产未改/四行候选各用原snapshot脚本生成30图（1180×720、1280×800、1600×900；初始及全部8源组启用/定位）和两套完整规范化form/命名控件/dirty状态；独立于计时。原始proof/PNG保全tmp/n-first-open/final-before-01和final-after-01，不是原生截图。
3. 正式formal-abba-01：20对/40新进程，偶数对legacy/final、奇数对final/legacy。每组执行相同AST提取/compile机制，legacy严格取基线四个方法，final仅替换四行，方法全文SHA记录；实际生产四行diff/全生产字节SHA记录。共40首开、80缓存返回，不与PR56旧序列或诊断混用。
4. 复用未改scripts/profile_n_first_open.py的worker（SHA7ad87b464e8e27fa882cd3b8409222dafcb5fa36e1612c52468357579f684dd5）；每进程复制同三库seed（200合成Record/20项目）；同依赖路径/窗口1280×800/Qt offscreen，首开HOME→NEW_ACCOUNTING后两次HOME→缓存返回。同worker捕获Qt回调错误，查询/Resolver次数、控件数/默认状态比较。任何回调错误/退出失败均不得作有效收益。
5. 正式测量与测试/build不并行；不控制其他用户进程/电源/磁盘cache。环境快照记录power plan与累计CPU，不是利用率或负载恒定证明。新进程不等于磁盘冷cache，offscreen Paint不等于实际屏幕首帧；报告median/nearest-rank p95/min/max及逐对差异/不利样本，不宣称稳定SLA。
6. 只有兼容与正式收益证据支持才保留；否则撤回唯一候选并结束性能优化。之后执行必要回归，稳定一个PR/正常CI，不重跑未变旧包。四行之外不继续寻找下一候选。

控制脚本字节保全：正式采样后提交核对发现全局LF规则会转换控制脚本末尾一个CRLF，改变其SHA。未改测量或重采；仅以路径限定 `scripts/profile_n_final_closeout.py -text whitespace=cr-at-eol` 保留实际采样字节，正式control SHA仍与提交字节一致。其他业务Python规则不变。Git内部normalization hash不等于原文件SHA256；最终以实际字节复核。
