# GHG-EXB01 实施报告（进行中）

日期：2026-10-10。GHG-EXB01仍在实施中；本报告记录阶段证据，不代表专项端到端验收通过。

## 平台 / Contract 预检查

业务仓 origin 已核验为 adgo07/GHGTOOL；分支 `codex/exb01-appendix-b-ingress` 以 `main@708f78a455790946b4a728029bba768d8fb295fc` 为初始基线，当前纳入最新 `origin/main@a51afbcf684e3845369977e42adc938866726d0b`。原工作区保留。
locked central：ee5feb0cc34dbd99790500fadd0c4c932e202a20；已按锁读取Architecture V2.1、Numeric Contract v1、Numeric Profiles v1。保持Decimal正式链、声明Profile、原始数值入口证据、显示不反馈、历史Record不漂移和分层；无中央Contract修改/锁升级。项目/Record公共Contract仍DRAFT。当前ACTIVE UI指南只应用本页必要接线。详见docs/exb01/APPENDIX_B_INPUT_DESIGN.md。

已有 Standard Issue 001～008 保持；无新标准原文解释或公式变化。表式映射不明确时定位问题，不猜测。

PR #38 的 GHG-UI-P3-AB 已合并，历史实现与测试证据见 `docs/ui/p3-ab/ACCEPTANCE.md`；原生人工验收仍 OPEN，AB 后 Phase 3 暂停，本任务不启动 P3-C/D/E/F。

## 已完成

1. 访问批准原母版并登记SHA256 c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4。
2. 保留原文件，仅在受控副本按授权删除B.2 J4:J18、B.6 G3、B.7 G3:G5、B.8 E3:E4共21公式及空缓存。未用openpyxl重存；新资源SHA e6a070bf28adb47939e24713f676136b5a023017d6f695e0031c68d51c389c3d。
3. 轻量ExcelTemplateService登记标准/模板ID/版本/资源/哈希，读取先核验、下载精确字节复制；结构校验只负责固定表头，不冒充完整业务校验。
4. 独立Luna 6/max核对：30个ZIP成员中26个payload逐字节不变，4个XML仅指定f/v删除；九表/布局/合并/验证/样式/其他值无差异，下载与资源精确一致。

## 实际验证与未执行项

本地Python3.12已确认导入来自当前worktree。命令：
`python -m unittest discover -s tests -p test_exb01_template_acceptance.py -v`
结果：2 tests，2 passed。独立QA首次有测试list/tuple断言差异，修正测试后通过；不隐藏失败历史。

本次合入PR38断言后的本地G03定向回归：`python -m unittest tests.test_g03_shell -v`，11 tests，11 passed，8.082s。此结果只覆盖G03，不代表EXB01完整回归或专项验收完成。

Astra 6/low 原生 Excel/WPS 保存共三次尝试，最近一次为 2026-10-10 01:13:20～21（北京时间）；均因 trusted Node process exited unexpectedly 未能启动工具，未操作任何文件，无保存产物。不得将 openpyxl 或离屏测试描述为原生验证。

Importer、UI闭环、R2删除与旧测试迁移正在实施。最终完整回归、Windows构建/发布审计、ZIP审计、最终head CI与最终独立专项验收尚未执行。完成后重写本报告为最终实际结果，不沿用PR37或旧head的通过证据。本包新PR不得自动合并。
