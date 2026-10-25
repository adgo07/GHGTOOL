# 新建核算全页第二批实施报告（进行中）

平台 / Contract预检查：业务仓受验基线ac06ca7e9d508b3956fef15fdad3d08d4b955f0a；中央Frozen锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。已按锁读取Architecture V2.1分层要求；Domain/Application不依赖Widget，显示不回流计算。当前正式中央origin/main c5fc6d438c9200060649e47c016b9b48218de72c的UI指南v0.2、产品家族规格v0.1适用；中央工作分支及其用户修改不作为正式指南。本任务不涉及中央公共 Contract，不改Frozen/Canonical/Schema/Numeric/Calculator/来源资格/标准范围。相关Standard Issue015、016、017、020仅保持既有解释，本轮无新解释。Carbon p40/HALF_UP仍是项目专属Profile，不是平台默认。

当前仅首包：Presentation中区分用户主动activate与程序select；九卡中的外部软件补充独立进入，声明沿用既有checkbox；燃料改“含碳量数据来源”。未改Domain/Application/持久化/正式输入规则。PR60受验分支保留，任务依赖ac06而非main已合并。

本地命令`python -B -m unittest tests.test_accounting_source_directory -v`，16/16，127.964s；没有CI/全量/包/原生结论。其余批准范围待实施，未完成整批。附件SHA256 `4922b39e0a3052ba956c54ad64951932e5535c60685f8c8ab1fb4bceacb89d73`，小包完成后持续更新TASK_STATE，阶段完成重写本报告。
