# PR46 独立验收退修实施报告

2026-10-17。Owner直接授权修复旧HEAD `7e6bdd5f45f30c7f44db0d4dbae4b808d9736159` 的阻断项。该HEAD独立验收NOT PASS；旧770项和CI245均通过，但未覆盖此次反例。继续原PR46，不自动合并或关闭PR45，修复后交源会话复验。

## 平台 / Contract预检查

origin实际核实为adgo07/GHGTOOL，原分支codex/ghg-standard-input-unification，main基线d0c26351200099a8e62c8adabadac266c77f7c8c。中央Frozen锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。保持Architecture V2.1分层、Numeric v1与本项目Decimal40/HALF_UP、环境独立性、完整值比较和显示不回流。Record/Workspace等DRAFT不冒称Frozen。

问题分类LOCAL DEFECT：按既有Issue010/014与Owner燃料B1/电力B决定修实现，不改变标准解释、公式、Numeric、数据库或历史Record。无中央Contract升级，无新的官方因子。不实施材料/过程/烟气/蒸汽后续规则、N、Word排版或CU。

## 修复与真实范围

1. 输出电力只resolve一次，同一真实结果控制资格、参数/值/单位/来源一致性、计算与快照；身份和值冲突明确阻断，原输入保持。缺ID的官方缺省不当OTHER，明确OTHER保留独立来源与可选说明。已核验Source版次与原Factor版本分别接受精确证明；raw_input保留真实来源版次，既有稳定快照版本格式不变。
2. 共享求值对小型结果作深复制，嵌套allowed/locking不再别名到缓存；不复制整份运行资源，规则SHA不变。
3. v5仅窄修B.2 row20的ht/customHeight。修复前严格ArtifactTool因`45, Boolean`拒绝；修复后严格读取及截图检查通过。新SHA `7438082b59e6ba294bb953ccc44db0c7a3a16eacbf4f8ddd83f063ce492bb890`；旧未发布错误SHA `ce929968b8659889b0b6aba581b6782b96b8afcb8b378bc1b27c9768521e3d09`仅历史证据。除sheet2.xml外所有ZIP内容不变，旧v2/v3/v4原字节保留。发布审计在现有白名单/hash检查中增加实际包内rowBoolean检查，不另造门禁。
4. Word读取当前Record的冻结输入模板版本，母版SHA仅在快照确有独立字段时输出；旧证据无母版SHA显示未记录，不拿用户填写工作簿sha256或当前layout伪造，不改历史记录。来源母版/报告布局身份与原输入身份分开。
5. 文档说明候选Mapping与已批准实际采用范围；生产仅五字段(fuel.direct_carbon/lhv/fch/oxidation、electricity.factor)。审阅表A4/checks兼容声明限于审阅视图，不冒称全PR没有模板/报告变化。四件套同源重生保留意见0→0，25夹具通过；没有添加新的业务规则。

## 真实验证及失败历史

本地Python3.12.14，Qt offscreen，临时隔离工作簿与SQLite，无用户数据写入。

|运行|实际结果|
|---|---|
|首轮baseline/channels/table5/runtime|20项10failure，12.545s；复合单位ASCII/Unicode精确别名未规范|
|单位规范后同组|20项5failure，17.914s；Source版次与Factor版本区别|
|尝试将实际Source中文版次写稳定快照|20项5error，16.314s；既有稳定标识约束拒绝，已撤销此尝试，raw_input保留版次|
|baseline/channels/table5/resolved-binding/新来源一致性|23/23，17.445s，OK|
|template/G08/runtime|31/31，7.274s，OK|
|G06/UAT03-page/UAT03-rules/EXB01|110项3failure，67.385s；旧输出电力夹具无ID却默认STANDARD_DEFAULT|
|G06/EXB01-RPT02/RPT02/新来源一致性/缓存隔离|50/50，10.784s，OK；电力夹具改明确OTHER，原数值/零值/单位断言不删|
|审阅表|25fixture PASS；61行、652组合、450意见范围；意见0→0，纯展示声明更新|
|v5|严格导入PASS；row20 XML与旧资源字节保护通过；非原生Office证明|

完整回归、最终HEAD构建/发布审计/归档/启动和GitHub CI尚待完成；未执行或运行中的项目不标PASS。最终精确HEAD、base/merge、真实计数和制品身份将在原PR46送验说明中汇总，后续文档若仅更新证据也须区分受验代码与新提交。

## 剩余验收缺项

v5原生Excel/WPS保存回导NOT_RUN/OPEN，正式外部交付前补；CU Esc未解除，不用程序重存或旧v4证据替代。真实鼠标/中文输入/人工系统DPI/企业样例OPEN。独立复验待新固定HEAD，当前不宣称最终验收PASS或标准SUPPORTED。

本轮不删除历史Record或分支，不关闭PR45、不合并PR46；主目录用户修改不覆盖。跨会话进度外发曾被自动审批拒绝，未绕过；本地实现和PR更新继续执行。
