# 当前任务状态 — B总体收口盘点＋N性能基线测量

2026-10-21：受验1724已获源独立PASS（仅B盘点/N代表基线），源已推送至原同名分支；本次收尾增量待源复核后统一push/PR并完成当前required checks。测量冻结348077c不变，当前未启动优化。

## 平台 / Contract 预检查

实际origin为adgo07/GHGTOOL，已fetch，默认main；PR53受验2dbb104是基线祖先，两者Git tree一致。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变；已从验证origin的中央clone按locked SHA读Architecture V2.1/Numeric v1/Profiles v1，ACTIVE UI v0.2按中央已合并main读取。MUST为分层、同Canonical/Application、声明Profile与子Profile可追溯、ambient独立、精确正式比较、冻结Record；MUST NOT为显示/遥测回流、旧Record重算、变更公式或自动升Frozen。Carbon p40/HALF_UP为允许项目差异；计时float仅非业务遥测。本任务不定义或修改中央公共Contract，无新增冲突/中央缺口。相关Issue016/017/018/020沿用批准决定，不新选解释。

## 分工与断点

- B：集成负责人独占治理文档，当前只读对账见 `docs/architecture/business-rules/CONSUMER_INVENTORY.md` 的2026-10-20表；8组业务、11字段策略与专属方法已定位。旧兼容保留，不误判为待删除分支；主要发现为治理时态陈旧，已同步并保留历史区。
- N：唯一测量者gpt-6.1-sol/medium，仅写 `scripts/measure_n_baseline.py` 与 `docs/performance/n-baseline/`。此前误配6-sol的准备者未实测/未写文件即停止，不存在重复样本。1暖身+5实测、单测量者串行；源码启动与离屏/合成数据限制如实保留。已完成14指标×5实测+14暖身，0计时失败；准确原值/环境/统计见RESULTS/raw。
- 未运行新全量CI/业务全回归，不重做PR53；生产代码未改。先前CI288全量1036/G08 18及实际包只背书原head2dbb104，不能冒作本包或merge348的精确新制品。

## 后续与开放项

原始数据复算与8项集成证据核验已通过（11字段、14组70实测值、206合成Record、6有效DOCX）；CLI help/py_compile/git diff --check通过。准确命令与一次临时查询表名错误见实施报告。raw按字节保留，执行副本历史SHA与当前LF脚本SHA分列，见SCRIPT_NORMALIZATION.json；无重测。原受验记录已落仓 `docs/performance/n-baseline/ACCEPTANCE.md`；作者8项核验与源PowerShell复算分列。按用户新授权送源增量复核后集中push/建PR，源负责最终检查和合并，本会话不并行合并。原生Office/鼠标/IME/人工DPI/企业实样/干净机及许可履约OPEN；本包不做优化；合并后由源触发定位先行的N新包。RS04/RS05与SUPPORTED/商业交付未授权。GAP-009非阻塞provenance debt保留。无需创建goal工具或第二路线。

N稳定提交 `ccf3f325fe121a228e37545395a7e9e795f0dbcc`（脚本/协议/raw/结果与2文件字节保全属性）。B治理提交随后独立形成，最终交接head以Git与源验收回执为准，生产基线始终为348077c。
