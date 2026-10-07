# 当前任务状态

状态：IN PROGRESS — 核算 Application UseCase 收口
最后更新：2026-10-07

## 授权与预检查

- 用户明确接受并授权合并PR #33，且授权按已说明范围执行步骤3。
- PR #33已合并；本包从最新main `26fd95e497baade6a16f471e81b185743b3f9fcd`创建分支codex/carbon-accounting-usecase。复用已附加、干净工作树；原checkout与用户文件保留。
- 中央锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`：已读取锁定Architecture V2.1、Numeric v1、Numeric Profiles v1及当前ACTIVE UI指南；不升级Contract或baseline。
- 本任务不涉及中央公共Contract。DetailedRecordRepository与计算证据是本模块内部接口，不声称中央DRAFT Record已冻结。
- Standard Issue 001～006既有解释不变；本包不改变标准规则、公式、Resolver策略、Numeric Profile或适用范围，无新增标准解释问题。

## 当前稳定断点

- Calculator仅计算并冻结完整证据；正式UseCase显式依赖详细Repository，成功一次保存Record/快照/审计，blocked不写；preview不创建临时Record。
- GUI/Excel调用Application；保存失败中文反馈且不显示成功、不关联项目。生产SQLite组合在apps入口；测试假repo显式注入。
- 为使Application边界真实成立，既有目录SQLite工厂移到Infrastructure；只读空目录移至纯标准模块，查询和因子语义不变。
- 重构前main全B.2～B.9合成样例已捕获，重构后7组输出+6类持久化快照精确一致（业务结果/参数/trace/provenance/报告等）；此为characterization，不是标准Golden。
- 定向用例与迁移测试通过，组间有重叠；架构AST门禁5/5。最终全量、构建及CI尚待代码冻结后执行。
- 无数据库迁移、历史Record修改、用户数据库或计算表改动。

## 交付边界

仅完成本包核算编排与持久化职责收口，不实现Excel正式写入/结果导出、新标准或RS04/RS05；不扩充Word功能。PR33遗留原生鼠标/视觉、Word分页与长标题观察项仍保留。交付本包独立PR后停止等待验收，不自行合并步骤3 PR。
