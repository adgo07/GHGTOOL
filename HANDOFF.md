# PR60 启动日志缺陷增补交接

五页V2成果继续保留；用户实测45a8178旧候选包因日志初始化PermissionError出现Unhandled exception，原CI308及隔离smoke不覆盖此真实路径访问问题。复用当前PR60工作树/分支，未合并。仅授权补启动日志错误边界与相关测试/证据，不重做五页，不改业务/DB/迁移/Calculator/Canonical/模板/Word/依赖/工作流/来源资格。

最小方案已实施：app.main捕获configure_logging及日志目录解析的OSError，业务仓库调用前固定中文提示并return1。不删日志、不改ACL、不要求管理员运行、不迁移用户数据、不静默降级正式Record审计。不可写时仍拒绝启动；修复不等于确定或消除真实用户权限/占用/安全策略原因。消息框、事件循环替身的启动用例不冒称实际原生交互。

最终本地启动/隐私/G08/Record审计组36/36，86.057s；原失败日志和修后结果保留，数量/命令/源hash及AST保护见IMPLEMENTATION_REPORT和docs/ui/business-pages-v2/startup-logging-review.json。原五页r9源29项不变，不重采相同UI。原1106项与旧CI308只作增补前基线，本轮新head必须有自己的required CI和精确包。

接续：稳定批次一次push更新PR60，等新head merge-ref完整CI及exact-head候选包；保留原始ZIP/元数据/两job日志，核digest/manifest及source/pr_head/tested_merge，再本地审计、隔离离屏正常启动、启动后再审计。随后交源独立验收并停止，不自动合并或发布。旧smoke使用隔离LOCALAPPDATA/TEMP，不能声称验证真实用户目录或原生桌面；不启动原生桌面，不触碰用户工作簿/日志/ACL。

本仓platform-lock与路线不变，无公共Contract或标准解释变化。原528份证据及CI308原包仍保留；新增回执单独命名，不覆盖旧证据。
