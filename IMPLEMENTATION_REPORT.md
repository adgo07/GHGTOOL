# PR47集中有限修复实施报告

本轮修复审阅产物的排序身份安全、可读性、跨版本意见延续及必要业务表达，并对已合并R8作有限澄清。原434c106的A通过结论已撤回，旧71项/CI #232不替本轮背书；本报告不宣称新head验收PASS或生产已接入。

## 平台 / Contract预检查

实际仓库origin为https://github.com/adgo07/GHGTOOL.git，原分支codex/ghg-business-rules-a；fetch核实main b0c1aa723391772f9aef026b4c0a8619eb61a65b。映射澄清独立提交412d3ac3a9569dfa79b706267eae1cf5b08d1bee，其余修复在后续提交；最终受验head由原PR47最新提交及送验评论精确定位。

中央locked SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。Architecture V2.1、Numeric v1/Profiles v1继续适用：分层、共享Calculator/Resolver、声明Profile及ambient independence、高精度exact业务比较、显示修约不回流、可变Project与不可变Record分离及历史不漂移；不得第二算法、epsilon正式判定、自动升级Frozen。本任务不涉及中央公共Contract修改，无新中央冲突/采用。映射澄清不修改正式公式、原表或Numeric；独立Decimal例显式使用本项目p40/HALF_UP，不称平台默认。

Standard Issue：有，保留010及012—019身份；014产品输入选择已批准而专业问题OPEN，018/019OPEN不关闭。新增020为式(9)时间覆盖局部OPEN，仅登记同覆盖原则，不把T改成运行天数，不发明汇总算法。本轮细化已批准解释的执行表达，不新增专业来源或正式计算解释。

## 修改内容与边界

1. **文件安全与布局。** 同一个Table覆盖全部业务、意见、状态、编号、版本及键。三个实际范围A5:Y34/A5:U24/A5:T14；最高行高392/184/104pt。电力按真实source_path+direction分成19条，共29业务行，仍只有11业务概念；操作19、变化9。按中文字宽估算布局，超过409明确报错，未截高藏字或缩小正文。
2. **必要信息。** 操作表直接显示初始条件、触发动作、确认/取消；外部CO₂和蒸汽边界可读。FCh单位tC/GJ，主表从同源渠道说明提取质量/体积经发热量的作用域，不新增HEAT活动入口。启停源JSON明确旧结果stale不封合法重算，历史Record查看/Word不受草稿改变影响；失效条件纳入测试。
3. **意见延续。** 稳定对象及条件不含修订；意见属性/必要条件与原审阅版本/hash分离。当前内容指纹和意见基线指纹分开，包含真实技术条件/绑定/理由，不仅摘要计数；集合重排不改变对应语义指纹。未变继续关联，内容变需复核，删除/未知/歧义保留待映射。旧SUMMARY唯一对应时保留并需复核，旧条件级意见不猜贴。重复生成不洗掉需复核；人工选择已复核本版且上一当前内容仍匹配，才更新基线，原始审阅版本/hash保留。
4. **同源详情与复现。** HTML从同一候选技术投影派生，保留646字段条件详情、19操作、9变化；不是第二真值源。正式生成强制--details，校验revision/base/dependency与紧凑投影SHA绑定。主表给静态文件/对象锚点，HTML有对象目录；定位列是文本，未声称Excel一键超链。已有CLI新增--technical-review-json，能从同一bundle导出两份绑定投影；不增加生产依赖或框架。
5. **证据。** checks补实际Table范围、行高、视图省略范围、源/生成器身份、fixture派生与原生边界。新增可重复fixture脚本和小结果JSON。历史electricity-paths.json原head/as_of/原字节保留，checks明确历史身份；构造OOXML缓存测试与原生Office回导分开。

批准V1.2原始字节、Common、platform-lock、Catalog、正式GUI/Excel/Word、Calculator、DB/迁移/历史Record未改。Schema职责保留，不新建规则平台、削减台账或25项治理体系。未安装iapws、不换库，不承诺181MB发布增量或典型≤0.1%；未测体积/速度收益。

## 映射澄清单独提交

- R01：014是不因手填自动归实测，禁止冒用身份，不新开专业方法。
- R02：CC=0但UCC+DU>0时共同WFC-C仍必需；缺项不填0，不批准018展开。独立例55/3 tCO₂，对照错误省略输出项33。
- R03：未决冲突只限制实际依赖的路径；必需分项失败不能伪完整ES/EI/ET。
- R04：tCO₂限定本炭素标准，不冻结成全行业单位。
- R05：同时间覆盖原则；020保持局部OPEN，不改T含义或算法。
- R06：017是有数值变化的方法替换；物性官方参考验证、旧表迁移差异与业务exact比较分开。019原表不猜改，已知焓独立，不扩相态；具体库/依赖版本、许可和实际Windows包体在生产接入前验证。外部物性统计仅作为引用意见，本轮未实跑iapws或复现全网格。

## 命令与真实结果

本轮使用既有Python3.12虚拟环境；下列python短名指该运行时。ArtifactTool来自load_workspace_dependencies现有bundle，通过临时Junction供生成器副本使用，副本SHA与scripts源相同；没有npm/pip新增生产依赖。临时Junction已核实后移除。

```powershell
python -m unittest tests.test_business_rules_candidate tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_assets tests.test_business_rules_excel_evidence tests.test_business_rules_candidate_revisions tests.test_business_rules_r8_operations tests.test_pr48_mapping_arithmetic -q
```

**77/77，0fail/0error，7.804s。** 包含正式XLSX、Table边界/行高、关键操作/FCh可读性、来源路径、历史Numeric/Excel证据及独立式(6)算术例。单独映射算术1/1通过；CLI扩展后的候选模块38/38通过。最终联合已覆盖二者，不重复相加统计。

```powershell
python scripts/validate_business_rules_candidate.py --review-json build/review-r9.json --technical-review-json build/technical-r9.json data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json data-source/carbon_accounting/business-rules/software_policy.json
node scripts/test_business_rules_review.mjs --input build/review-r9.json --technical-input build/technical-r9.json --output build/review-feedback-fixture.json
```

实际执行对应文件位于build/business-rules-authoring；同源CLI复现两份投影逐字节一致。JS实际R9派生fixture **18/18场景PASS**（主16、方向隔离2），由真实对象抽取并记录版本/删除/属性/技术绑定变更；Table实际数据范围反转后ArtifactTool导出重开/再生成。连续两轮需复核保持、显式确认当前版后关联、旧确认遇新内容仍需复核；技术绑定数量不变内容变仍提示，反转技术行不误提示。这个结果不是原生Excel排序。细节和hash见review-feedback-fixture.json；工作簿0正式意见，与用户备份0意见相符。

生成器SHA256：68a6b5f1a4325391eaec71c13633a645ffe3c3c6711c9322349528785e4d8d13；正式工作簿：88cfeecb349ed05cf07b705d7a38cd391d7883107e022add9bca85d8c0c35018；正式LF投影：7b38a82ef8fd4478fe4221e139b1074c35eb24b542ad0470c76819725561eb3a。源JSON、详情、fixture、生成器身份及实际范围均写入checks；不是用hash替代正确性测试。

开发过程：中文化使旧措辞断言失败（一次64项中63通过/1失败，补认等价“已修改”后64/64）；正式产物更新前资产检查3项不同步失败，更新后上述77通过。初始fixture长命令曾触发Windows206；中途生成器更新造成详情hash断言失败、一次结果写build遇EPERM，分段落盘及TEMP输出后最终18场景成功。独立审阅发现并修复了重复生成洗复核状态、真实绑定变化被折叠计数掩盖的问题，没有以删断言规避。最终生成器改用固定code-unit排序，避免系统locale差异造成误提示；生成HTML曾因行尾空白导致暂存diff检查失败，已在生成器统一清理并重新生成、复跑18场景及77项联合测试，未绕过检查。

三份实际规则包通过Draft202012 Schema验证（0错误）；两个mjs的node --check、改动Python compileall与git diff --check通过。最新fetch仍为main b0c1aa7，原远端PR47为434c106；没有继承其CI作为本轮证明。

## 未闭合验收与停止点

**原生Excel未完成。** Astra子agent完整读取computer-use技能并初始化/枚举应用、复制临时文件；sky.launch_app长时间无返回，根代理中止后工具显示aborted by user after2079.6s。未取得窗口证据，未打开、填写、排序、保存关闭或原生视检；不是Owner主动取消。未杀进程，用户正式文件未被该原生尝试修改。不得将临时40766字节复制品或ArtifactTool18场景作为原生通过证据。

本轮未本地执行完整全量/Windows构建；新head Windows CI须另核实并与本地结果区分，不继承#232。实际长电力行及23/24关键操作已ArtifactTool渲染检查，中文余量不足曾调整布局后复看；不等同Office显示验收。

本轮向原PR47提交、自动送方案设计独立验收，然后停止。无新的Owner业务选择；014专业、018、019、020仍OPEN。即使A通过也等待Owner确认，不合并47/46，不启动46/B/N；原生缺项与最终CI状态由验收明确处理，不擅自宣布完整PASS。
