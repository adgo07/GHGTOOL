# B-HEAT 当前交接

更新：2026-10-18；ACTIVE / RELATED_REGRESSION。三项直接授权已核，旧待决已解除；PR49/50/51已合并，不改旧PR、不回到脱硫。当前codex/b-heat-integration，base a1aeebc1b6809397e61a2ffa7a2333a3b440c756，中央锁ee5feb0不改。

共享HEAT.1、codec5、C3准确资格、已知焓/固定IF97自动焓、边界/B.9/项目/正式Record/冻结Word/构建候选已接。方法/子Profile/许可/来源和失败对账见TASK_STATE、IMPLEMENTATION_REPORT及Mapping§9.7当前实施；原始R11与旧表不改，旧模板原字节、旧Record/Word冻结。

最新完成66/66 Numeric/Excel/自动Word组合，修复四处热力GUI旧期望及known非正值冻结5/5。更广组合曾因Word入口停顿终止，无完整统计，独立数据目录重跑报告/记录/Excel入口46/46通过（135.016s），最终热力/专属/IF97/GUI/Excel/Numeric/G08联合85/85通过（65.099s）；不得写全量通过。PR52已创建并attach，代码head f85e0583b1ae01578cc0c0fc3135e875b44b8dc8；CI276/run39128755391全量测试中。本地同head实际Windows包构建/审计/ZIP/2启动及EXE/PYZ+包内CoolProp/NumPy/Qt完整热力链通过，证据见docs/ci/B_HEAT_LOCAL_PACKAGE_PROOF.json。CI实际包尚待产出，后续精确head CI实包和最终独立验收必须另完成。

C独占共享消费者、资源、GUI、构建和治理；F仅交热力helper/tests，M外部CO₂准备分支不纳入本包，N不启动。原用户脏树、旧工作树和计算表不改。源会话原始用户消息01a14ee7-32ba-7283-ab49-ad6b89b633aa“全部同意”及紧前解释已实际读取，原版本/C3/017授权待决已解除；本会话补充的源交接、PR49、M/F及脱硫授权已收悉，PR49/50/51均已合并，不回到旧阶段或改旧PR。

下一步：完成PR52全量CI和精确head实际CI包，更新最终报告/PR并送源独立验收后停止。不得自行合并/启动下一包。原生Office、鼠标/中文IME/人工DPI、企业样例、干净目标机和商业许可履约保持OPEN；不CU、不商业发布、不宣布SUPPORTED，不改Frozen基线或另建路线。

## 送验前补充对账

只读扫查发现UIR04另有一个未被选定套件覆盖的旧热力夹具：未知边界先被阻断，仍期待旧泛化状态文案。单项真实重现1FAIL/3.921s，修为明确边界外并断言实际绝压消息，保留点击展开本源卡及不泄露内部ID，修后1/1、4.202s。生产代码与f85e058不变；本次仅测试/文档/可复现实包证据回执。CI276仍是旧受验head，不据其进行中状态宣称全量通过，需新head全量CI和精确head制品。新增原始授权回复再次明确B-HEAT接线及HEAT.1/v10兼容同步；不回旧阶段、不扩大范围。

## Canonical干净检出字节修复

实际e931c21 Git blob隔离复现：新增C3采用JSON本地CRLF而Git LF，原机械投影最后来源SHA为CRLF f816d704…、Git实际为LF 1dd97fd8…。按既有仓库LF规则保存源、机械重生heat.json为37844a5b09fce7350ebc172457b768b86b665a4be8398408c4e2727be1216ca3，生成器明确拒绝CRLF，不在读取时归一化哈希。结构全值比较仅末项source.sha256改变；fields/policies/前三来源完全相同，算法/公式/参数/解释不变。`python -B -m unittest tests.test_b_heat_runtime tests.test_g08_delivery -v`：30/30，16.363s，0失败/错误/跳过。原f85本地包证据只背书旧head；CI276/277均已被此修复取代，不称通过或引用其未知测试总数。新head须全量CI和精确head实包，再最终重写报告并送源验收。

## CI276真实结果与最后审阅资产修复

CI276旧head f85e058、测试merge a4de96d507c4a9bdcd121a5835a58f4022ce705a：实际1006项、2027.458s、1FAIL+2ERROR；standalone跳过，不是超时或通过。三项为UIR04旧边界/文案夹具、heat Canonical来源字节、Mapping更改后审阅定义资产登记旧hash。前两项已定向修；最后一项按PREFLIGHT机械重生同R11四件套，原三Canonical字节不改，新旧工作簿全部单元格值和Table名/范围相同；原仓内这一份意见0→0，不推断用户附件。实际3表61行、450个原有可见scope（既有442+Issue010追加8，未改）、8隐藏技术列/表、最大行高344点；23项Python资产/来源审阅测试18.334s全通过，25个真实ArtifactTool往返场景全通过，均为本地证据，不冒称CI执行了JS。原表和四件套在Git/本树tmp备份。四件套/4定义hash见docs/ci/B_HEAT_REVIEW_ASSET_PROOF.json；干净Git源证明见B_HEAT_CANONICAL_BYTE_PROOF.json。

有45秒单项堆栈界限的字段/来源卡/项目/codec+Word缩小组合49/49、187.332s通过，初次组合停顿未复现，原因不冒称已确定。CI277/278均被最后资产修复取代，当前源代码断点a7d5d46，最终受验head以PR52最新说明和实际制品manifest为准；固定稳定资产回执后才新全量CI/精确head实包，不自行合并。
