# PR60 五页 V2：启动日志缺陷增补报告

用户实测45a8178候选EXE因日志初始化PermissionError出现Unhandled exception。此前CI308/离屏启动成功不覆盖该真实启动缺陷，PR60保持未合并。本轮最小修复及本地定向验证完成，待同一PR的新head required CI、精确新包与源独立验收。

## 诊断与最小决定

入口基线45a8178fa92ef88eed8988c9d8dd671db93d32cb，origin实核adgo07/GHGTOOL，分支codex/ui-five-business-pages-v2，fetch后main仍d7159f77ddb103376f5ca6bdd3a9532c101433e3，入口干净。复用现有PR工作树，不重建五页、不覆盖既有成果。

app.main在任何业务数据库初始化前直接调用configure_logging，日志目录mkdir或RotatingFileHandler打开失败均可抛OSError，原来没有启动边界保护。实际用户文件访问失败的原因仍未确定：受限进程权限不代表资源管理器正常用户启动的权限，不能由sandbox写失败推定用户ACL问题；文件占用、安全策略和启动方式仍待区分。本轮未访问或修改实际用户日志路径，不改ACL、不要求管理员运行、不删除日志、不迁移用户数据、不启动原生桌面。

选择固定中文提示并安全退出，不改日志路径或静默降级。仅app.main的日志初始化外增加OSError捕获；提示“应用日志无法打开”“应用日志无法创建或写入。核算记录和项目数据尚未打开”，提供检查日志文件夹可写性/可能占用的重试方向，return1，不显示任意异常原文。日志仍不可写时仍拒绝启动；本修复消除未处理异常，不声称消除了用户环境访问阻塞，也不把正常用户真实启动宣布已恢复。

configure_logging、RotatingFileHandler轮转配置、结构化事件/字段白名单逐字不变；正式Record及audit_log实现未改，失败在records/projects/settings仓库调用前退出，正常流程仍创建真实隔离库并进入原事件循环。严格AST证明：仅拆掉新日志try/except后，app.py整文件AST与45a8178一致，含create_main_window及全部原数据库/业务启动组合。packages/resources/scripts/workflow/依赖/platform-lock无变化，r9全部29项UI源hash仍匹配。

## 本地验证（数量重叠，不累计）

Windows/Python3.12.14。新启动测试使用隔离合成路径；消息框及应用事件循环替身，不是原生交互验收。真实文件系统负例为日志目录已有文件、application.jsonl已有目录、Windows只读文件、Windows独占共享拒绝句柄；另注入handler PermissionError及EXE入口转发负例。正常守卫使用真实隔离SQLite仓库和结构化日志，保留原日志内容、启动/退出事件。

| 命令 | 结果 |
|---|---|
| 修前 python -B -m unittest tests.test_startup_logging -v | 原6项：1正常通过/5错误，2.556s；五类错误均未处理，原件保留 |
| 修后 python -B -m unittest tests.test_startup_logging tests.test_logging tests.test_g08_delivery -v | 当时6项新用例＋原守卫共29/29，88.703s |
| 最终 python -B -m unittest tests.test_startup_logging tests.test_logging tests.test_g08_delivery tests.test_g07_records.G07RecordRepositoryTests -v | 36/36，86.057s；7项启动用例、日志隐私、22项交付、6项正式Record/审计守卫 |
| python -B -m compileall -q apps tests/test_startup_logging.py；git diff --check | exit0；通过 |
| app整文件受控AST；29项r9源SHA；未改业务/资源/依赖/工作流 | 全部通过 |

Record审计守卫包括审计插入失败必须回滚正式Record、成功记录追加与全快照、删除留审计且ID不复用。没有以诊断日志可用性替代正式审计。修前/修后原始日志已独立保留；本轮源hash、命令/数量/耗时、各日志SHA和范围证明见[startup-logging-review.json](docs/ui/business-pages-v2/startup-logging-review.json)。本地真实路径只记最终执行回执，不写进治理正文。

本轮没有重跑无变化的五页截图/视觉或本地完整1106项；启动边界已由36项直接守卫覆盖，完整回归由本次必需的merge-ref CI执行，结果必须按实际新head单独记录，不能把旧1106＋新增组拼成新完整通过。当前新CI/新制品未完成。

## 原五页基线身份与证据边界

保留批准的标准库/详情、参数因子库、表格导入、记录/详情、设置V2。原包仅在6旧blob/10目标匹配后受控应用，未重套或修改预期hash。原protected_tree、8个核算/壳源及Excel接线19/19的保护保持。r9限定视觉PASS，干净捕获e2c7520ef58eb7623ddf0f8ba5a45be9193a1b30，60图/29源匹配、回调异常0，原五项HOLD关闭，当前UI源未变；不把r9称作本轮启动错误提示截图。

原本地完整1106/1106（2731.183s）在5c0c34013db938f56924329b43861fa5890c52d3，原CI308在45a8178的merge-ref1106/G08 22成功及旧精确包，均是本轮增补之前的证据，不能证明新启动修复或真实用户路径可写。旧528份原始证据归档及早期完整运行异常原件保留，不覆盖、不重标；[五页图集](docs/ui/business-pages-v2/review.html)继续仅作原视觉范围证据。

此前smoke将LOCALAPPDATA/TEMP隔离到合成目录，因此覆盖新用户可写目录启动、PNG/SVG和中文资源，不覆盖既有实际用户目录的ACL、文件占用、压缩文件、安全策略、启动身份，也不是原生桌面/鼠标/IME/Office/人工DPI/企业样例/干净机验收。

## 平台 / Contract预检查

业务入口45a8178fa92ef88eed8988c9d8dd671db93d32cb，locked中央ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；沿用本会话已核验的中央当前合并UIv0.2/清单及locked Architecture V2.1。适用MUST/MUST NOT：保持分层，诊断日志不写任意企业/活动/秘密数据，显示不回流计算，正式Record/审计语义不降级，不改Canonical、Calculator、迁移、来源资格或标准支持状态。无冲突、偏差、adoption或中央修改。本任务不涉及中央公共 Contract。相关Standard Issue：本启动工程缺陷无标准解释问题；不改变既有软件解释或支持范围。

## 接续与停止条件

稳定本地批次一次push更新PR60，仅复用同head required checks；取得本次真实精确head ZIP，核GitHub digest/manifest/两job原始日志，执行本地审计、隔离离屏正常启动及启动后再审计。原生实际用户启动及真实访问原因仍待独立确认。交源会话独立验收，不自动合并、发布、修改ACL/预算/workflow或无变化重跑CI。
