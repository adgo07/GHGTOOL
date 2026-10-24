# PR59 两项 P2 修复与证据整理

当前：两项修复已实现，最终原始 CLI 全量 1082/1082 通过，0 失败/错误/跳过，3440.480 秒；原始 CLI 三模块联合回归 32/32 通过，216.654 秒。十四张最终图由 astra 限定视觉 PASS，118 项源码哈希匹配。未完成独立验收，未合并或发布。五页 V2 在另一分支保存后暂停，其视觉 HOLD 问题不属于本包完成范围。

## 修复和边界

FUME_V1 原时长控件移到监测段专用容器之外，显示“时长（天）”，保留原值、单位、版本、信号和计算路径。取消升级不改输入；明确升级保留原始状态。测试从旧 form_state 实际保存、重开项目，并验证旧 Canonical 编解码和跨 Repository 重开；实际计算按钮失败零 Record、成功新增、重复计算不覆盖。沿用原 p40 完整结果，不用显示值或容差替代精确比较。

错误定位展开真实目标后，以 QObject 上下文安排最多十二个事件轮次，等待主滚动区几何和范围稳定，确认目标矩形进入真实 viewport 后聚焦。新请求、来源切换（含离开再返回）、目标删除、路由切换和页面销毁取消旧请求，不强制固定高度。补齐物料水分、换算方法和基准错误的控件映射。宽窄回归实际点击错误条目，检查目标整个 QRect 在 mainScrollArea.viewport 内，以及输入、dirty、Record 不变。

三个核算组件的原色集中到命名表，被替换字符串求值逐字相同；全局样式函数和其他页面不改。Calculator、正式比较、标准解释/范围、来源资格、Canonical、数据库/迁移、项目/Record 模型、Excel/Word 业务、模板、依赖、workflow 及用户参考文件均未改变。

## 本地证据

环境：Windows、Python 3.12.14、PySide6/Qt 6.11.2、offscreen，合成输入、隔离库。开发截图进程仅注册已有系统字体，不安装或打包字体。

| 命令或范围 | 结果 | 限制 |
|---|---|---|
| 修复前实际复现 | FUME_V1 有值/缺值均隐藏；1180×850 首次点击越出 viewport | a96 旧源码，不背书修复 |
| python -B build/pr59-p2/run_targeted.py | 8/8，108.776 秒，Qt 回调异常 0 | 开发进程注册字体；随后颜色仅等值提取 |
| python -B -m unittest tests.test_pr59_compatibility_navigation tests.test_b_fume_chain tests.test_b_material_chain -v | 32/32，216.654 秒 | 原始 CLI，无字体注入或测试插桩 |
| python -B -m compileall -q apps packages resources scripts tests | 退出 0 | 当前源码 |
| python -B -m pip check | 退出 0；No broken requirements found | 当前本地环境 |
| python -B scripts/validate_canonical.py | 退出 0；9 标准/12 来源/102 参数/138 因子 | 不代表新增标准支持 |
| git diff --check | 退出 0 | CRLF 归一化提示不是失败 |
| 第一轮 python -B -m unittest discover -s tests -t . -v | 1081 通过、1 失败、0 错误；1082 项，2959.407 秒 | 源码/测试/资源哈希未变，Qt 已删除对象异常 0；原件不改写 |
| python -B -m unittest tests.test_uat02_usability tests.test_pr59_compatibility_navigation -v | 16/16 通过，201.330 秒 | 完整两模块，原 CLI，无字体注入 |
| 最终 python -B -m unittest discover -s tests -t . -v | 1082/1082 通过，0 失败/错误/跳过，3440.480 秒 | 源码/测试/资源哈希未变，Qt 已删除对象异常 0；无测试插桩或字体注入 |

第一轮全量唯一失败是原自动聚焦测试在两轮 Qt 事件后即检查焦点。诊断捕获两轮时 shell 高度为 2043→1948，pending 均为真，尚未达到本次批准的“布局稳定后聚焦”。提前聚焦试验全部撤回，产品源码与截图所列 118 项哈希再次逐项一致。只在原两轮事件后增加 100ms 内的正常事件观察，保留全部旧断言，并补整个输入框在真实 viewport 内的断言；不强制布局刷新、不提高已有 100ms 几何上限、45 秒模态或 60 秒缩放限制。测试提交 7444b9b2e1d5e744fe3b313cdb6b81b4bca03259。第二轮完整 CLI 独立通过，不将第一轮失败改写成通过。最终原始日志 SHA256：f416a3e43c75b9dfdaa0e33d2b41ca308d09504631f2f7da79795191d65b0d72；完整源清单与统计见 FULL_FINAL_SUMMARY.json，未改写原始日志。

中间失败原件保留：误引入夹具 TestCase 导致额外发现；打开项目误用 No 而非 Discard 导致取消加载；8 天断言误用显示简值；折叠换算暴露 UI 字段映射缺失。分别修正夹具、完整值断言及 UI 映射后再运行，未改计算真值；超时/中断不计为已完成回归。

## 身份及归档

先提交稳定代码，再捕获最终截图；summary 的 code_head 和逐文件 SHA256 绑定实际受验源，后续证据/文档提交另行区分。历史父 HEAD 配合源码哈希仍有效。

原 PR 证据 241 文件（82 PNG）已在工作树外按原始字节归档，ZIP 完整性和逐文件 SHA256 均通过，公开索引 docs/ui/pr59-review/ARCHIVE_INDEX.json。原日志不改写，公开摘要不含本机绝对路径；当前树移除重复原件，Git 历史保留，这不会缩小已有 Git history。原 a96 的本地 1074/1074、CI304 和候选包只证明旧身份，不能背书本次代码。

截图绑定生产源提交 7308473895faf4500f7c4fd1ad596531408d9eeb；后续仅测试等待提交 7444b9b2e1d5e744fe3b313cdb6b81b4bca03259，截图所列 118 项仍逐项相同。最终证据/文档提交另行区分。Git 按既有 .gitattributes 作 LF 归一化；本地证据记录实际工作树文件 SHA256，不混同 Git blob 哈希。CI、最终 PR head、tested merge ref 和精确候选包身份在提交后追加到 PR59 描述的交付回执，不为登记 CI 再推文档改变受验 head；不得使用旧 CI304 背书。

astra 的 PASS 仅覆盖十四图；08 时长标签贴近顶边为非阻塞建议，输入框完整可见。首次点击过程与计算行为由功能测试证明，不把视觉复核说成 astra 亲自执行 32 或 1082 项测试。

## 平台 / Contract 预检查

业务入口 HEAD a96f8ed90a1d9183a93de1c1185ab8906c979b07；实际工作树/origin/分支/HEAD/状态和 fetch 已核，origin 为 adgo07/GHGTOOL，默认 main，沿用原 PR59 分支。中央锁定 ee5feb0cc34dbd99790500fadd0c4c932e202a20；已核中央 origin、锁定 Architecture V2.1 和当前 UI 指南 v0.2。适用 MUST/MUST NOT：保持分层，Domain 不依赖 Qt/SQLite/Windows，显示不回流计算，UI State 不冒充公共 Workspace，正式 Record 不可变且参数快照不漂移。无新增冲突/偏差，无中央修改、baseline 升级或 Frozen adoption。本任务不涉及中央公共 Contract。

相关 Standard Issue：有，004/016/018、017、020；改变既有软件解释：否；无新标准问题。

原生桌面、鼠标/IME/系统 DPI、Office、企业真实样例未执行。离屏截图不冒称人工验收。最终由源会话独立验收，本包不自行合并或发布。
