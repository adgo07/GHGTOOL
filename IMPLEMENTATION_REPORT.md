# B总体收口盘点＋N性能基线测量 — 实施报告

状态：1724基线已获源独立PASS；2026-10-21收尾增量待源复核后统一PR与本轮检查，当前未合并/未优化。原测量日期仍为2026-10-20。

## 平台 / Contract 预检查

业务基线 `348077cd972a27b6eeb80b77b712e7cb35375988`（PR53 merge）、已fetch的main、origin adgo07/GHGTOOL均实际核验；PR53 head2dbb104与merge完整Git tree一致，但制品身份仍不同。中央锁 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`；按锁读Architecture2.1/Numeric1/Profiles1，ACTIVE UI v0.2按中央已合并版本读。必须分层/共享Canonical/声明Profile与子Profile可追溯/ambient独立/精确正式比较/Record不可变；禁止遥测或显示回流、历史重算、公式及Frozen升级。Carbon p40/HALF_UP是ALLOWED PROJECT DIFFERENCE。本包不定义或修改中央公共Contract；无新增冲突或CENTRAL CONTRACT GAP。相关Issue016/017/018/020不改变既有软件解释。

## B 盘点方法与结果

本轮以磁盘代码、Git对象与已保留测试/CI证据只读核对，未重新执行全部业务场景。8组渠道矩阵在现有 `docs/architecture/business-rules/CONSUMER_INVENTORY.md` 当前表：GUI与Excel适配同Canonical；预览无Record Repository，明确保存项目后走同Application正式核算；成功追加Record；报告/Word只读冻结快照。

4份受控投影采用11字段（燃料4、电力1、材料2、脱硫3、热力1）；烟气Issue020、外部CO₂ Issue016与工艺公式保持版本化Domain。不是所有算法JSON DSL化，也不是把剩余规则候选一概放行。旧MATERIAL_V1/FUME_V1/模板结构和历史缺省字段受显式兼容约束；旧C.4/C.5不参与新自动焓或失败回退。当前限定清单未识别新增需修生产Bug，不能据此声称全条件无缺陷。

发现并仅修治理陈旧时态：路线仍写B-HEAT执行/N不启动、AGENTS仍指后续PR46、消费者旧表未把历史观察与当前分清；当前状态/交接/报告仍是PR53执行候选。旧历史证据保留，PR53 API已核merged，当前表转到348基线。`CORE_CHECK/GAPS`保留原B2观察，不用旧C.4/C.5/证明门槛描述覆盖后续批准决定。

整体标准仍PARTIAL / NOT SUPPORTED；原B2的GAP-009为非阻塞附件provenance debt。未接管和交付剩项明确区分：P04A没有新增fuel.*字段策略并非漏做；原生Office（当前v11）、真实鼠标/IME/人工DPI、企业实样、干净目标机/正常退出及第三方许可履约仍OPEN。RS04 Golden/正式支持与RS05 Release未启动。

## N 实测与验证

已交付 `docs/performance/n-baseline/PROTOCOL.md`、`raw.json`、`RESULTS.md`。复用既有benchmark的合成Record，完整实际create_main_window/Application/Excel/Word路径；200轻量列表Record、20项目、1个已知焓外购热力+外部CO₂代表单元，不覆盖IF97/所有来源或企业规模。2026-10-20 23:00:32—23:02:35（Asia/Shanghai）串行执行，14指标各1暖身+5成功实测、失败0。

| 核心指标 | median ms | p95 ms |
| --- | ---: | ---: |
| 源码内部事件循环就绪 | 819.640 | 1259.835 |
| Excel读取/校验/预览 | 502.906 | 539.980 |
| Canonical项目打开 | 54.643 | 62.019 |
| 正式核算与Record追加 | 65.610 | 68.114 |
| 冻结模型/Word生成与保存 | 644.119 | 725.104 |

另有父进程全程、创建返回及7页导航的全部原值；n=5的nearest-rank p95等于max，不构成稳定尾延迟。首次fresh全程17.762s和首次新建页14.543s单列保留，未清磁盘cache、未固定电源/后台负载，不作瓶颈归因或SLA判断。Excel6次预览新增0；正式6次追加不同Record，实际合成库206条；6份Word可读，生成前后记录库哈希不变。

环境为Windows10/19045 x64、Python3.12.14、PySide6/Qt6.11.2、CoolProp8/NumPy2.3.3等，完整版本/CPU标识见raw。CPU友好型号/RAM的CIM补充查询权限不足，不伪填。一次shell重定向父目录未建导致Python未启动，建目录后唯一真实测量成功；此为准备失败，不计入14指标失败。测量期间只一个执行者，无其他性能/测试/build并发。N不改生产代码、不优化、不安装新依赖、不把源码/离屏/合成样例冒作精确EXE/人工操作/企业样例或SLA。

## 截至原测量/本地交付时点的历史证据和未执行项

PR53的CI288在head2dbb104：全量1036/1606.482s，G08 18/11.080s，0失败/错误/跳过；真实制品12272798465及其哈希见PR53最终说明。这是先前GitHub执行，不是本轮本地执行，也不冒作merge348的新精确制品。本轮不重做该全量/构建，不重触昂贵CI；不改workflow或绕过required checks。无需创建goal工具。完成测量和必要静态核验后送源独立验收，不自动合并。

## 本地命令、独立证据检查与结果

- `python -B -m scripts.measure_n_baseline`：唯一串行测量，退出0，14组×5成功实测+14暖身，无重跑；原始整数纳秒保留。脚本严格限定348 HEAD，复现需在该基线新隔离树复制脚本，不在文档提交后冒跑不同HEAD。
- `python -B tmp/b-closeout/check_evidence.py`：8项集成证据检查通过，4注册资源哈希/采用身份与11字段一致；独立重算14组统计；真实临时工作簿哈希、206合成记录/6份DOCX及公开raw隐私有效。首次该临时核验误用records表名，按实际Repository的accounting_records修正后通过，无生产/样本修改。可追踪结果保存到 `docs/architecture/business-rules/evidence/b-closeout-2026-10-20.json`。
- `python -B -m scripts.measure_n_baseline --help`、`python -B -m py_compile scripts/measure_n_baseline.py`、`git diff --check`均退出0；这些为CLI/编译/差异检查，不伪称业务测试全量。
- 139个已声明生产文件前后摘要一致；另独立 `git diff 348077c -- apps packages resources data-source tests pyproject.toml platform-lock.json` 为空，补齐Canonical来源与复用测试未改证据。当次运行执行副本SHA256 `f3c15fec984bda9924f80ec1668c1788587768df3d968cced4939b63111ad18d`；raw SHA256 `ee02b8b7cb5ac4227f2afee5005aa1c90a7ab833c61c2c346fcc93425090edac`。Git默认LF转换会改变现场证据，因此仅对这两文件加-text并声明CR为合法行尾，保留字节，不规范化原始数据、不重新采样。
- 未运行完整业务测试、build、新Actions/精确新制品、原生Office或桌面CU，原因分别为生产未改/用户最少CI与当前未授权范围；既有CI288身份单列。本轮未更改workflow/required checks、不绕过合并门禁；先本地稳定提交送源独立验收，不为纯文档PR触发完整Windows CI。未push/建PR/自动合并，未做性能优化/RS04/RS05/商业交付。

暂存差异首次因原始CRLF行尾报空白提示，按两文件专属CR-at-EOL属性保留原始字节；属性文件多余EOF空行已清除，随后cached差异检查通过。该属性仅解释现场证据行尾，不关闭全仓空白检查、不改原始样本。暂存区已独立核原始JSON与执行脚本SHA均与上述现场哈希完全一致。

N本地稳定提交 `ccf3f325fe121a228e37545395a7e9e795f0dbcc`；B治理与静态校验证据为独立后续提交。本包最终head通过Git/源验收交接定位，不生成文档自引用SHA循环。以上为原本地交付时点：当时没有push/PR/新CI；之后源已独立验收1724并推送，不能将该句解释成历史没有验收。

## 2026-10-21 定向收尾与验收落仓

源原始验收记录已实际读取，整理入 `docs/performance/n-baseline/ACCEPTANCE.md`；受验1724的PASS限于只读盘点/代表基线，源静态源码/生产diff与独立PowerShell复算14组70样本＋14暖身/哈希均有原记录。源未重跑benchmark/全量测试/CI，作者8项检查与DB/Word实物验证不改标成源执行。第三方指出的是仓内缺少验收落点，不是历史完全没有验收；本次不另造外部执行证据。

raw原字节/原SHA `ee02b8b7cb5ac4227f2afee5005aa1c90a7ab833c61c2c346fcc93425090edac` 不变。脚本由实际执行副本CRLF字节（SHA `f3c15fec984bda9924f80ec1668c1788587768df3d968cced4939b63111ad18d`）仅替换CRLF为LF；当前LF SHA `0b63b81142fcdca549c3017af3a94d0cf494eebc7cf0223e55dedbd14b8a2b0f`，git属性改为text eol=lf。`SCRIPT_NORMALIZATION.json`记录两类身份、字节数及纯换行一致性；不声称原运行是LF，无重测。此前两文件-text的描述属于历史保全时点，当前只有raw继续按字节保留。

当前源已push1724；本次补丁本地完成后先送源增量复核，再集中push/建PR/attach，保留required checks、仅正常一轮CI，不用旧CI288代替。本会话跟进PR/CI，源负责最终检查与合并。合并后下一N定位/优化由源触发，协议与等价性门禁已写现有HANDOFF，当前无生产修改、无优化、无桌面CU或新测量。最终PR/head/检查结果在PR及源回执记录，不为纯状态说明反复push。

收尾本地验证：`python -B tmp/bn-closeout-fix/verify_closeout.py`退出0，核原/现字节的精确CRLF→LF关系和AST、两类脚本哈希、raw原字节/哈希、生产范围无变化、Git LF属性、源原验收记录SHA及新增证据路径脱敏；`python -B -m py_compile scripts/measure_n_baseline.py`、`python -B -m scripts.measure_n_baseline --help`和`git diff --check`均退出0。没有新增性能样本或重跑benchmark；增量先源复核后集中push/PR，当前CI结果后续由新PR确认，不冒用原CI288。
