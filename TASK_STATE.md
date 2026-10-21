# 当前任务状态 — N 导航定位与最小优化

2026-10-21：PR54已由源正常合并，merge为 `e186b5116f16861bc65fbb939abec750a39d7f0e`。从实际fetch后的main建立隔离分支 `codex/n-navigation-performance`；origin核实adgo07/GHGTOOL。旧B/N原始基线与源验收保留于 `docs/performance/n-baseline/`。

## 平台 / Contract 预检查

中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变；验证中央origin后按锁读取Architecture2.1/Numeric1/Profiles1，ACTIVE UI v0.2按已合并main读取。适用MUST为分层、同Canonical/Application、Profile传播/ambient独立、精确正式比较、冻结Record；MUST NOT为遥测回流、跳校验/刷新、历史重算、公式/标准范围/Frozen升级。Carbon p40/HALF_UP属允许项目差异，非平台默认；计时是非业务遥测。本任务不修改中央公共Contract、无新增冲突。Issue016/017/018/020沿用，本任务不改变标准解释。

## 当前断点

生产提交 `2a8d83bc9031837a3496b95f97653e30a4437596`：仅shell背景兄弟层及3项回归，无业务缓存或逻辑修改。root单写入/单测量，静态代理已只读结束。正式before/after各351样本，3库字节相同、同worker SHA、查询次数一致，0失败；缓存导航median由1023—1207ms变为14—162ms。新建首次3409ms，构造仍约3020ms，未解决。详见docs/performance/n-navigation/RESULTS/COMPARISON/VALIDATION。

本地对应回归42+37=79，0失败/错误/跳过；125%与150%各3背景测试PASS；真实生产页16组像素等价。首次夹具7失败断言及UUID不同的首轮after均保留，正式严格同库补测未改worker/生产。未本地全量或build；稳定后集中一个PR及正常CI，最终head/检查由PR回执核，不挪用旧CI290。不自动合并。

旧B/N raw SHA保持ee02b8b7cb5ac4227f2afee5005aa1c90a7ab833c61c2c346fcc93425090edac，原验收保留。无CU/企业库/系统设置改变/公式或Profile、Record/Word、迁移、Frozen或标准范围变更。原生Office/IME/人工DPI/企业实样/干净机及许可门禁继续OPEN；RS04/05与商业交付未启动。源独立验收前不扩大优化。
