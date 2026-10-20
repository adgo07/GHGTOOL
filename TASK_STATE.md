# 当前任务状态 — B总体收口盘点＋N性能基线测量

2026-10-20：IMPLEMENTED — 待源独立验收。PR53已合并，当前任务从最新main `348077cd972a27b6eeb80b77b712e7cb35375988` 隔离分支开始，原根用户工作簿/未跟踪内容和旧PR历史树未动。生产文件保持冻结；测量期间HEAD未变，当前仅准备脚本/文档/证据提交。

## 平台 / Contract 预检查

实际origin为adgo07/GHGTOOL，已fetch，默认main；PR53受验2dbb104是基线祖先，两者Git tree一致。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变；已从验证origin的中央clone按locked SHA读Architecture V2.1/Numeric v1/Profiles v1，ACTIVE UI v0.2按中央已合并main读取。MUST为分层、同Canonical/Application、声明Profile与子Profile可追溯、ambient独立、精确正式比较、冻结Record；MUST NOT为显示/遥测回流、旧Record重算、变更公式或自动升Frozen。Carbon p40/HALF_UP为允许项目差异；计时float仅非业务遥测。本任务不定义或修改中央公共Contract，无新增冲突/中央缺口。相关Issue016/017/018/020沿用批准决定，不新选解释。

## 分工与断点

- B：集成负责人独占治理文档，当前只读对账见 `docs/architecture/business-rules/CONSUMER_INVENTORY.md` 的2026-10-20表；8组业务、11字段策略与专属方法已定位。旧兼容保留，不误判为待删除分支；主要发现为治理时态陈旧，已同步并保留历史区。
- N：唯一测量者gpt-6.1-sol/medium，仅写 `scripts/measure_n_baseline.py` 与 `docs/performance/n-baseline/`。此前误配6-sol的准备者未实测/未写文件即停止，不存在重复样本。1暖身+5实测、单测量者串行；源码启动与离屏/合成数据限制如实保留。已完成14指标×5实测+14暖身，0计时失败；准确原值/环境/统计见RESULTS/raw。
- 未运行新全量CI/业务全回归，不重做PR53；生产代码未改。先前CI288全量1036/G08 18及实际包只背书原head2dbb104，不能冒作本包或merge348的精确新制品。

## 后续与开放项

原始数据复算与8项集成证据核验已通过（11字段、14组70实测值、206合成Record、6有效DOCX）；CLI help/py_compile/git diff --check通过。准确命令与一次临时查询表名错误见实施报告。为raw及执行脚本添加Git按字节保存属性，原SHA不变。提交稳定断点，送源独立验收；不自动合并。原生Office/鼠标/IME/人工DPI/企业实样/干净机及许可履约OPEN；N不做优化，RS04/RS05与SUPPORTED/商业交付未授权。GAP-009非阻塞provenance debt保留。无需创建goal工具或第二路线。

N稳定提交 `ccf3f325fe121a228e37545395a7e9e795f0dbcc`（脚本/协议/raw/结果与2文件字节保全属性）。B治理提交随后独立形成，最终交接head以Git与源验收回执为准，生产基线始终为348077c。
