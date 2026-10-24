# 五个业务页面 UI V2：本地完成，待独立PR / CI交付

2026-10-25。分支codex/ui-five-business-pages-v2，实际origin adgo07/GHGTOOL；最新fetch main d7159f77ddb103376f5ca6bdd3a9532c101433e3。复用原安全断点并正常吸收PR59，未重套旧包或改变预期hash。

五页呈现及局部表格可读性已完成，首页/壳/新建核算/业务/数据库/Canonical/模板/Word不改。受保护AST、8源逐字内容及Excel接线19/19均通过。

astra r9限定视觉PASS：干净生产head e2c7520ef58eb7623ddf0f8ba5a45be9193a1b30，60图/29源hash匹配，回调异常0。验证head5c0c34013db938f56924329b43861fa5890c52d3只同步G03旧呈现预期和阶段文档，29源hash与r9相同。本地原始完整CLI 1106/1106，2731.183s，源码前后hash一致；27/74/13/39定向组通过，数量重叠不累计。Canonical/编译/依赖/范围检查通过。原完整访问冲突与1104通过/2项旧呈现断言未通过的两轮原件保留，不冒称当轮PASS；根因未确定，后两整轮未复现访问冲突。

精选相对路径[证据页](docs/ui/business-pages-v2/review.html)包含28图、完整身份索引及限定回执。528份原始证据独立归档并校验；原始build暂留，不清理工作树。详细命令、数量、失败、SHA及未执行项见IMPLEMENTATION_REPORT。

当前待独立PR/required CI/本次精确head制品审计和源会话验收；不自动合并、不发布，不复用PR59旧CI。平台锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，当前适用UIv0.2已读；保持分层/显示隔离/冻结Record/来源资格，无冲突、adoption或中央修改。本任务不涉及中央公共 Contract。相关既有Issue004/016/018、017、020，不改变解释。未执行原生桌面/鼠标/IME/Office/人工DPI/企业样例/干净机验收。
