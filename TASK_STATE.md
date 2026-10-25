# PR60：五页V2启动日志缺陷收口，待新head工程验证

2026-10-25。实际origin adgo07/GHGTOOL，复用codex/ui-five-business-pages-v2；入口45a8178fa92ef88eed8988c9d8dd671db93d32cb干净，fetch后main d7159f77ddb103376f5ca6bdd3a9532c101433e3。PR60未合并，原CI308/旧包不覆盖用户实测日志PermissionError缺陷。

最小修复：仅app.main在业务仓库初始化前捕获日志初始化OSError，固定中文提示并return1，不显示任意异常原文。日志路径不可写时仍安全拒绝启动；不声称用户实际访问原因已消除。未触碰用户日志/数据，不改ACL或管理员绕过，不删日志、不静默停正式Record审计。

修前隔离6项1通过/5错误2.556s；修后组29/29 88.703s；最终启动/隐私/G08/Record审计36/36 86.057s，数量重叠不累计。7项启动守卫含EXE入口、真实路径冲突、只读与独占占用、注入PermissionError及正常真实隔离库；消息框/事件循环替身不是原生验收。AST证明拆掉新增保护后app整文件与45一致；日志实现及r9 29项UI源不变，业务/数据库/模板/Word/依赖/workflow不改。详细命令/hash与边界见IMPLEMENTATION_REPORT及startup-logging-review.json。

当前待新head required CI与精确修后包，原五页图集/1106项/CI308仅是此前基线，不复用为本轮通过。此前smoke隔离LOCALAPPDATA不能证明真实用户路径可写；实际启动方式、文件占用/安全策略原因未确定。最终交源会话独立验收，不自动合并。平台锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，本任务不涉及中央公共Contract，无标准解释变化；不启动原生桌面。
