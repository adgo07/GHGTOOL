# PR35范围收口与PR36整合实施报告

日期：2026-10-09。状态：LOCAL VERIFIED。用户授权调整PR35，PR36合并后再合并PR35；PR36已合并main@9955ee88f197b8e7e4e6b8c479eb5af73619e7b1。

## 平台 / Contract 预检查

- 实际origin为adgo07/GHGTOOL，使用附加工作树的codex/rs03-excel-workflow；实际核对根目录、origin、fetch、分支、HEAD与状态，不覆盖原checkout或计算表用户文件。收口断点4b19b76基于e0c6c69，已整合最新main，运行代码/本地验证head为a9a4ec57c121162bc0c81af869797cae9e746f81，后续仅验证文档。
- 中央Frozen locked SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，沿用Architecture V2.1 / Numeric v1 / Profiles v1，并读取适用ACTIVE Policy/UI Guide。
- MUST：GUI/Excel共用Canonical/Application/Calculator；正式成功追加不可变Record、blocked与预览零Record；Project隔离；Word读取冻结Record；保持项目Decimal40/HALF_UP、ambient independence与exact comparison。
- MUST NOT：Excel另建算法、display rounding回流、当前Catalog重算历史、Qt状态冒充公共Contract；不升级Frozen baseline或新建数据库/依赖。
- 本包异常接口只在模块Application内实现，不改变公共Contract。Carbon Profile为ALLOWED PROJECT DIFFERENCE，无新Frozen冲突；中央Excel Numeric交换仍OPEN/PARTIAL。无需中央Contract变更。
- Standard Issue：无新问题；001～006既有解释不变，不修改公式、Resolver或标准适用范围。

## 范围与实现

保留R2模板、严格导入预览、有效Canonical项目保存/恢复、明确正式核算及不可变Record查看。删除Excel核算结果按钮、renderer和专属测试；Word报告保留。输入模板改版、Word分页/版式、新建核算重设计延期，不作为本包出口条件。

Word导出区分生成失败、写入失败和审计失败；同目录临时文件原子替换保护已有文件，补后缀后的目标冲突明确确认。审计失败如实提示文件已保存且审计未完成，不改Record。

项目关联失败区分marker未写入、marker已写入但关联未保存、关联已保存但marker清理失败；未知异常不承诺恢复信息已保存。异常定义置于Application，Persistence保留旧导入兼容。恢复仍保留当前最新项目输入、元数据和导航，不自动重算。

## 本地验证

以下为Windows / Python3.12.14本地执行，绑定运行代码a9a4ec57c121162bc0c81af869797cae9e746f81。Qt offscreen，TEMP/TMP/LOCALAPPDATA分别隔离；日志在忽略目录build/step4/trim35。

| 命令 | 结果 |
|---|---|
| python -m unittest discover -s tests -t . -q | 344/344，546.994s，失败0、错误0、跳过0 |
| python -m compileall -q apps packages resources scripts tests | 退出0 |
| python -m pip check | 无依赖冲突，退出0 |
| python scripts/validate_canonical.py | 9 standards / 12 sources / 102 parameters / 138 factors，退出0 |
| python scripts/initialize_databases.py --output-dir build/step4/trim35/auxiliary/databases | 四库初始化退出0；实际迁移Catalog003 / User001 / Records004 / Projects003 |
| python scripts/uir04_manual_gui_acceptance.py | A～E五场景PASS，离屏自动化 |
| python scripts/uir04_scale_acceptance.py --scale 1.25 / --scale 1.5 | 两种缩放均PASS |
| git diff --check | 退出0 |

独立GPT-6 Luna/max子agent对同一runtime只读复核，62/62定向通过：
`python -m unittest tests.test_g08_delivery tests.test_rs03_excel_entrypoints tests.test_rpt01_report_excel tests.test_pr35_pending_marker_failures tests.test_rs03_excel_project_workflow tests.test_rs03_pending_link_recovery tests.test_project_workspaces tests.test_canonical_project_inputs tests.test_rs03_record_ingress_evidence tests.test_architecture_boundaries -v`。

覆盖：无Excel结果入口且R2模板仍可导出；Catalog不可用仍从历史Record导出Word；导出生成/写入/审计失败和补后缀覆盖确认；Record及六类快照不漂移；marker三态、零自动重算和重开保留最新项目元数据；GUI/Excel共享业务内核、分层门禁与G08交付。

PR36合入数据版本2026.10.08-electricity2023.1，构建清单同时保留catalog003与projects003，二者迁移独立。本包相对最新main未改Domain/Standards/Numeric/Record迁移；应用层仅把Excel来源证据冻结进既有raw_input。

## 远端证据与交付

本轮Windows standalone构建、目录/归档审计、provenance和隔离启动交由GitHub Actions精确PR head job执行；本地未重复构建，不写成本地成功。推送后的最新PR head、CI链接与状态记录在PR35描述及Checks；CI成功后按用户授权合并。

旧99a2038的334/334、Windows构建与CI173仅属历史证据，旧候选仍含已取消的Excel结果导出，不能作为本次交付。当前本地日志也不冒充远端CI结果。

GPT-6 Luna/max子agent承担输出收口、恢复状态与独立审查，主agent整合最新main和完成全量验证。没有使用computer use；原生Windows鼠标视觉、真实Excel/WPS打印及Word分页本次未执行，不宣称通过。输入模板改版、Word版式/分页/展示完善和新建核算重设计延期，正式数值/读取错误记录等缺陷不延期。

本包不升级平台基线、不提供.qzproj、不新建数据库/依赖，不启动新标准或RS04～RS06+；正式标准支持状态仍PARTIAL / NOT SUPPORTED。G08运行manifest的Projects版本可以以后补直接断言，现实现与源码断言/实际初始化均003，无实现级阻断。
