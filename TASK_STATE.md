# 当前任务状态 — PR50 B-FGD定向退修

更新：2026-10-18。状态：**F01—F03已真实复现并定向修复，本地回归完成；等待本轮固定受验对象的独立复验结论**。原a683通过结论仅限原覆盖，本轮重新OPEN；不合并、不进入下一包。

## 对象与范围

- 仓库adgo07/GHGTOOL，私有[PR50](https://github.com/adgo07/GHGTOOL/pull/50)保持OPEN/未合并；开工head a6830e98f3e41f8748dfd86bfcefa58603fab150，fetch后main 1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e。
- 本轮仅UI/Excel未完成输入保留、设施新窗口恢复、必要回归与历史文档收口。生产文件由C独占；M/F停止，用户根目录未改。
- 不改公式/来源集合/Calculator/codec/DB/模板/规则资源，不新增设施数据库。唯一产品路线仍REFERENCE_STANDARD_ROADMAP.md。

## 已验证事实

a683真实Qt/Excel/Application/SQLite：F01两批漏成一批并生成1Record；F02编辑身份的第二组分漏检并生成1Record；F03新窗口/新服务保留ID但丢显示。原始仓内证据：[PR50_FGD_A683_REPRO.json](docs/ci/PR50_FGD_A683_REPRO.json)。

本轮修复：有业务的空组分批次交致命校验，完全未触占位可忽略；B.7编辑身份保留、原母版全静态占位区分；设施ID/显示名先全量去重建候选再选择，旧未知关系保留提示。来源草稿、同设施多批、删除前批、取消升级保持；旧项目可开存，旧Record不回填/重算。

- a683实际14项3FAIL/87.790s保留；误直接导入测试类引入11原链项已纠正，不掩盖三真实失败。
- 首轮修后三反例3/3、21.717s；边界/旧模板/整链28/28、229.747s。
- 受影响联合126/126、355.499s；仅测试增强后的F02直接Application反例1/1、8.586s，未完正式零Record，补齐2.8174。完整命令/日志边界见IMPLEMENTATION_REPORT。
- 新增10方法覆盖F01/F02正式零Record、11.88/2.8174/1.76/9.9独立预期、真实新窗口/服务与SQLite恢复，旧B.7版本组同时回归。

当前固定受验提交、对应CI/实际包证据按[仓内摘要](docs/ci/PR50_FGD_RETAKE_SUMMARY.json)和PR50说明追溯，既有a683/CI262只作原覆盖背景，不替代本轮结果。摘要可引用固定生产对象；后续证据文档提交不得改写对应关系或自指制品身份。

## 平台 / Contract 与标准预检查

locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；沿用Architecture V2.1、Numeric v1/Profiles v1及ACTIVE UI v0.2。MUST：分层/共享内核、declared-profile consistency、ambient independence、full-value exact、历史不漂移。MUST NOT：业务epsilon、显示回流、复制算法、自动Frozen升级、Qt状态充当公共Workspace。p40/HALF_UP为ALLOWED PROJECT DIFFERENCE，无中央冲突/变更；相关Issue016，未新增标准解释。

## 历史与停止边界

CI252原字节迁docs/ci（SHA256 92d63cff11f5ecbf9ec002f0a5fad7646197c9d72b7fe267794a338630858f17），仅背书原PR49阶段固定提交，HANDOFF/DELIVERY引用已更新；数字/身份未篡改。旧FGD_V1同组归一CAL不同正式拒绝、旧项目开存及历史Record不重算已明确。

原生Office保存回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机及商业履约仍OPEN/NOT_RUN。完成本轮CI/实包交接后停止等独立验收；不合并、不CU、不扩包、不删旧工作树、不商业发布。
