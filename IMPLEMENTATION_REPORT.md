# PR35范围收口与PR36整合实施报告

日期：2026-10-09。状态：IN PROGRESS。用户授权调整PR35，PR36合并后再合并PR35；PR36已合并main@9955ee88f197b8e7e4e6b8c479eb5af73619e7b1。

## 平台 / Contract 预检查

- 实际origin为adgo07/GHGTOOL，使用附加工作树的codex/rs03-excel-workflow；实际核对根目录、origin、fetch、分支、HEAD与状态，不覆盖原checkout或计算表用户文件。收口断点4b19b76基于e0c6c69，现整合最新main。
- 中央Frozen locked SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，沿用Architecture V2.1 / Numeric v1 / Profiles v1，并读取适用ACTIVE Policy/UI Guide。
- MUST：GUI/Excel共用Canonical/Application/Calculator；正式成功追加不可变Record、blocked与预览零Record；Project隔离；Word读取冻结Record；保持项目Decimal40/HALF_UP、ambient independence与exact comparison。
- MUST NOT：Excel另建算法、display rounding回流、当前Catalog重算历史、Qt状态冒充公共Contract；不升级Frozen baseline或新建数据库/依赖。
- 本包异常接口只在模块Application内实现，不改变公共Contract。Carbon Profile为ALLOWED PROJECT DIFFERENCE，无新Frozen冲突；中央Excel Numeric交换仍OPEN/PARTIAL。无需中央Contract变更。
- Standard Issue：无新问题；001～006既有解释不变，不修改公式、Resolver或标准适用范围。

## 范围与实现

保留R2模板、严格导入预览、有效Canonical项目保存/恢复、明确正式核算及不可变Record查看。删除Excel核算结果按钮、renderer和专属测试；Word报告保留。输入模板改版、Word分页/版式、新建核算重设计延期，不作为本包出口条件。

Word导出区分生成失败、写入失败和审计失败；同目录临时文件原子替换保护已有文件，补后缀后的目标冲突明确确认。审计失败如实提示文件已保存且审计未完成，不改Record。

项目关联失败区分marker未写入、marker已写入但关联未保存、关联已保存但marker清理失败；未知异常不承诺恢复信息已保存。异常定义置于Application，Persistence保留旧导入兼容。恢复仍保留当前最新项目输入、元数据和导航，不自动重算。

## 验证状态

收口部分本地定向25/25，异常分层修复20/20通过；完整PR36整合回归及精确head CI尚待执行。旧99a2038的334/334、Windows构建、CI173仅属历史证据，旧候选仍含已取消的Excel结果导出，不作为本次交付。

GPT-6 Luna/max子agent承担输出收口、恢复状态及独立审查。没有使用computer use；原生视觉、真实Excel/WPS打印和Word分页本次不宣称通过。
