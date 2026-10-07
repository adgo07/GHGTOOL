# 核算 Application UseCase 收口实施报告

日期：2026-10-07。状态：AWAITING ACCEPTANCE；本地验证完成，交付独立 PR 等待验收。用户已接受并授权合并 PR #33，该 PR 已合入 main；本包执行用户授权的步骤3。

## 平台 / Contract 预检查

- 仓库实际 origin 为 adgo07/GHGTOOL，默认分支 main。任务分支 codex/carbon-accounting-usecase 从 PR33 合并后的 main `26fd95e497baade6a16f471e81b185743b3f9fcd` 创建；复用已附加工作树，不覆盖原 checkout 或用户文件。
- 本地代码与测试验证对象：`5acf1fa0a25a7804b03bd4a320a9add8a374ea4a`。后续治理文档提交不改变运行代码；最新 PR head 与 GitHub Actions 的证据以 PR Checks 为准。
- 中央锁定 SHA：`ee5feb0cc34dbd99790500fadd0c4c932e202a20`。已读取锁定 Architecture V2.1、Numeric Contract v1、Numeric Profiles v1，及当前 ACTIVE UI 指南。
- MUST：Presentation / Application / Domain / Infrastructure 分层；正式核算显式注入持久化；成功追加不可变记录和完整证据，blocked 不生成 Record；报告使用冻结快照；本仓声明的 p40 / ROUND_HALF_UP、ambient independence、full-value exact comparison 保持不变。
- MUST NOT：Domain 依赖 UI / SQLite、Application 创建具体存储、缺失生产依赖静默降级内存、预览创建 Record、显示修约回流计算、报告查询当前 Catalog 重算历史值。
- 本任务不涉及中央公共 Contract。DetailedRecordRepository 和 CalculationEvidence 为本模块内部接口，不声称中央 DRAFT Record Contract 已冻结；不改变 platform-lock.json 或 PLATFORM_BASELINE.md。
- 冲突分类：既有 Application 目录服务工厂直接依赖 SQLite 适配器为 LOCAL DEFECT；本包将该工厂移到 Infrastructure，纯空目录留在标准模型层。不是 PF01 新一轮功能重构。Carbon Numeric Profile 保留为 ALLOWED PROJECT DIFFERENCE，无需修改中央 Contract。
- Standard Issue：无新问题；既有 001～006 解释保持不变，含 005/006 日期口径。没有修改标准公式、Resolver 策略、适用范围或正式业务结果。

## 实现与行为

1. CarbonMaterialCalculator 只执行计算和校验，返回原 Outcome 及冻结的 CalculationEvidence；不创建 Record，不接触记录仓库。blocked 判断仍由 Calculator 决定。
2. CarbonAccountingUseCase 编排正式核算，以显式 DetailedRecordRepository 保存一条新的 Record 及六类证据；重复成功追加，失败不覆盖旧记录。SQLite 保持原事务、审计和数据库结构，无迁移。
3. CarbonAccountingPreviewUseCase 使用同一 Calculator，完全不配置记录仓库，结果 record=None；Excel R2 保持只读预览，不新增正式写入或结果导出。
4. 删除 Calculator 中 InMemoryRecordRepository 隐式兜底。内存适配器移至 Infrastructure，仅在测试和验收脚本显式注入；生产 SQLite 组合在 apps 启动入口。
5. GUI 正式计算统一调用 UseCase。保存失败记录底层异常并显示中文提醒，清除结果状态，不发送 record_created，也不关联项目结果。仅支持旧只读仓库的调用可以查看记录，正式计算明确失败。
6. app、product、AppShell、新建核算页面共用仓库一致性检查；显式提供不同仓库即拒绝，避免计算写入 A 而记录页读取 B。缺省查看仓库从正式 UseCase 取得。
7. 五条 AST 架构门禁保护 Domain/Application/Adapter 的依赖边界、UI 不创建正式 SQLite Record Adapter、Calculator 不构造或保存 Record。不是对动态反射或所有间接调用的证明。

本包不拆大文件、不扩大数据库数量，不改报告模型取数、Word 功能、标准支持状态或公共接口。不启动 RS03 正式闭环、RS04/RS05、新标准。

## 业务保持与测试证据

重构前从合并基线捕获完整 B.2～B.9 合成输入，固定计算时点；重构后复用同一 Canonical Input 和目录，精确比较 7 组 Outcome 与 6 类持久化快照，共 13/13 通过。总量仍为 `369.5575954191666666666666666666666666667`。比较包括全部精度的结果、参数、问题、trace、规则和报告来源，不比较每次新建的 Record ID。

- 命令：`python build/usecase/characterization/compare_after.py`。
- 基线 JSON SHA256：`964b4f5141a85d725ed8b5bf03ca552db3d53ed47f7be3f68f7b4d8f759c5ef3`。
- 证据位于忽略的 build/usecase/characterization 与 logs；仅使用自建合成数据，无用户数据库。这是重构前后 characterization，不是独立标准 Golden truth。
- 定向最终检查：`python -m unittest tests.test_main_integration_ui tests.test_carbon_accounting_usecase tests.test_architecture_boundaries -q`，17/17 通过（9.497s），覆盖真实 SQLite、blocked、重复追加、事务失败、冻结证据不漂移及四入口仓库冲突。
- 全量、编译、依赖、Canonical、四库、UIR04、缩放与 standalone 结果见以下最终验证表。

## 最终本地验证

下表均为本地 Windows / Python 3.12.14 执行，使用冻结代码 head `5acf1fa0a25a7804b03bd4a320a9add8a374ea4a`；TEMP/TMP/LOCALAPPDATA 隔离在 build/usecase，QT 使用 offscreen。完整日志位于 build/usecase/logs/final-acceptance-20261007，发布日志位于 build/usecase/logs。

| 命令 | 结果 |
|---|---|
| `python -m unittest discover -s tests -t . -q` | 305/305 通过，380.235s，失败0，无跳过 |
| `python scripts/validate_canonical.py` | 9 standards / 12 sources / 98 parameters / 99 factors，通过 |
| `python -m compileall -q apps packages resources scripts tests` | 重跑通过，退出0 |
| `python -m pip check` | No broken requirements found |
| `python scripts/initialize_databases.py --output-dir build/usecase/databases` | catalog/user/records/projects 四库隔离初始化通过 |
| `python scripts/uir04_manual_gui_acceptance.py` | A～E五场景通过（自动化离屏执行） |
| `python scripts/uir04_scale_acceptance.py --scale 1.25` / `--scale 1.5` | 两种1366×768缩放场景通过 |
| `python scripts/build_standalone.py --output-root dist/usecase-acceptance` | Windows standalone构建通过 |
| `python scripts/inspect_release.py dist/usecase-acceptance/QingzhouCarbonAccounting` | 262个文件，目录/manifest/范围审计通过 |
| `python scripts/verify_release_archive.py dist/usecase-acceptance/QingzhouCarbonAccounting` | 263个可见文件，ZIP往返审计通过 |
| `python scripts/smoke_standalone.py dist/usecase-acceptance/QingzhouCarbonAccounting` | 两次隔离启动通过 |

build-manifest source_commit 与本地验证head一致；数据库版本为 catalog=002、user=001、records=004、projects=001。数据源、迁移目录、Numeric/Resolver实现与Frozen baseline文件无改动。

初次 compileall 使用额外的长 PYTHONPYCACHEPREFIX，3 个缓存写入因 Windows 路径长度失败；取消该前缀后重跑。该失败是验收环境配置问题，没有修改源码。实现期间临时 import 迁移顺序引起的定向失败均已修复并重新执行；最终结果以上表为准。

## 审查、限制与交付

GPT-6 Luna / max 子agent承担调用迁移、回归、边界只读审查与状态文档同步；主agent负责 Domain 提取、依赖一致性、打包及结果汇总。最终代码只读审查未发现阻断问题。

- Calculator 仍保留既有实例级规则累加状态；当前 GUI/Excel 同步调用。未来若引入后台并发，不应让并发调用共享同一个 Calculator，需先隔离调用状态。本包不新增并发。
- 本包没有执行 Windows 原生鼠标/视觉完整 UAT，也没有执行 Word 分页渲染。PR33 遗留的这两项及记录列表长标题可读性观察仍待独立验收；offscreen 自动化与启动 smoke 不替代它们。
- GitHub Actions 属远端验证，不能称为本地执行。报告成文时尚未发布本包 PR；提交后以最新 head 的合并集成与精确 head standalone 两个 jobs 为 CI 证据，不沿用 PR33 的历史成功代替本包验证。
- 当前仅交付本包候选，停止等待独立验收，不自行合并步骤3 PR。参考标准仍 PARTIAL / NOT SUPPORTED；本包通过不代表全产品或正式标准支持验收完成。
