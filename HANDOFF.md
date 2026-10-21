# N 导航性能定位与最小优化 — 实施交接

2026-10-21：源已合并PR54，merge `e186b5116f16861bc65fbb939abec750a39d7f0e`；本包从该main另建隔离分支。唯一产品路线仍为REFERENCE_STANDARD_ROADMAP.md。旧B盘点、14指标基线及源独立验收保留于docs/performance/n-baseline，不重测/覆写历史raw。

## 平台 / Contract 预检查

实际origin canonical，已fetch并核默认main/祖先关系。中央Frozen锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`：Architecture2.1/Numeric1/Profiles1按锁读取；ACTIVE UI v0.2按已合并版本读取。不升级锁或标准范围。分层、同Canonical/Application、声明Profile/ambient独立/精确正式比较、不可变Record及冻结Word必须保留。计时是非业务遥测，不能回流计算；本任务不修改中央公共Contract，无新增冲突。现有Issue016/017/018/020沿用，不改变标准解释或正式算法身份。

## 范围与执行

root为唯一生产写入者和唯一测量者，静态代理只读定位并已结束。先执行独立pilot确认分项，再固定before/after各3新进程、每进程10轮稳态；首用3值单列。协议见docs/performance/n-navigation/PROTOCOL.md。使用完整生产compose、200合成Record/20项目、1280×800/offscreen，不读真实用户库，不CU。每次采样唯一目录，单机串行且不与测试/build并发；电源只读，不改设置/清cache。

首个pilot表明祖先QSS重设占缓存导航大部分，布局量级较小。先验证相同样式幂等的路径覆盖；HOME/业务仍须换背景时，才验证把原背景绘制隔离在无业务后代的兄弟层。不得取消refresh、验证、草稿、显示或持久化提速；任何生命周期/失效变化须有证据。视觉只做自动离屏等价检查，不冒称原生DPI验收。

## 交付与停止

对应导航/滚动/动态高度/草稿/项目恢复/外部写入刷新回归与同机前后测量完成后，小提交、一个稳定PR/必要CI送源独立验收；不自动合并。需专业选择或重大架构取舍仅停止相关项上报。不得扩大到公式、Numeric、旧Record、数据库迁移、中央Frozen、RS04/RS05或商业交付。原生Office/IME/人工DPI/企业实样/干净机/许可门禁仍OPEN。当前结果、命令、失败与证据由TASK_STATE/IMPLEMENTATION_REPORT和新N目录同步，不以旧CI冒充新head。

## 送验前稳定断点

最小生产提交2a8d83b，严格同库前后702主样本/0失败；79对应回归、125%/150%各3项背景测试、真实7页两尺寸16组像素等价均通过。缓存导航median降86.6%—98.7%；新建首次构造仍约3秒，后续不擅自扩大。原始JSON、确定性复算、准确命令/日志SHA、首轮测试夹具失败与不同UUID诊断均保留于新N目录/忽略tmp。此为本地源码离屏证据，正式PR head/CI与独立验收另以回执记录；不把原PR54 CI290冒作本包证据。
