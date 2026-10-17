# PR46 燃料B1与电力B实施报告（执行中）

2026-10-17。基线head9d74e8a032f0bf2e6fa525deffea59f9172f883c已由源会话限定验收PASS；该固定提交保留完整基线整合报告和初跑失败记录。基线本地705/705及CI242两任务成功不是本B新head证据。本轮不合并PR46、不关闭45，不开始其他业务段/N，最终由源会话验收。

## 平台 / Contract预检查

实际origin为adgo07/GHGTOOL，原分支codex/ghg-standard-input-unification；重新核根/origin/fetch/branch/head/status，开工clean。锁定中央ee5feb0cc34dbd99790500fadd0c4c932e202a20，Architecture V2.1和Numeric v1适用：分层、声明Profile与ambient独立、Decimal权威入口、完整值精确判定、显示不回流、可变Project/不可变Record与历史不漂移。当前ACTIVE UI指南v0.2不构成Frozen升级。无公共Contract修改或冲突，不改p40/HALF_UP、公式或数据库。

相关Standard Issue为010/011/014/016；执行现行Mapping和已批准软件决定，不新增专业解释。LHV/FCh计算来源退出及DIRECT合法计算接入属于已有批准修正；尚未接线的材料/过程/烟气/蒸汽规则不顺手采用。

## 最小接口断点

- 抽出原候选完整field求值至core/business_field_policy.py；候选与运行适配共用最终资格、默认、锁定及非法来源纠错。上下文缺失/多匹配保留明确失败。
- 从三包已采用修订机械投影仅fuel.direct_carbon/lhv/fch/oxidation和electricity.factor及直接策略到受控运行资源，携带源哈希/修订/依赖。Schema/HTML/审阅compact不参与运行；不另录数值或维护来源集合。
- 构建核对源投影再生，发布审计/runtime核固定资源哈希；资源精确白名单，不放开data-source。GUI/Excel/Domain旧消费者尚未在本断点替换，不能宣称已经生产同源。
- 下一断点为Resolver多绑定只读关联证明及本次全部入口接线；非空ID不作为VERIFIED，未验证不得伪装ABSENT；已有用户来源不自动改成默认。不扩Record/DB，历史Record不回查。

## 实际命令与结果

1. `python -m unittest tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_revisions -q`：首跑19项，0failure/2error（抽取遗漏审阅helper导入）；修复后19/19，0failure/0error，1.458s。
2. `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 python -m unittest tests.test_fuel_power_runtime_policy tests.test_g08_delivery -q`：22/22，0failure/0error，5.260s。含独立来源/锁定/五表/OTHER/零路径预期、候选与runtime逐分支结果相等、源或派生资源失配、包内缺失/篡改失败，以及原交付保护。
3. `python scripts/project_fuel_power_rules.py --write`：成功机械生成；日常检查不带--write，不静默修复。

4. 联合命令曾误写不存在的`tests.test_business_rules_candidate_structure`，42项/1导入ERROR（非生产失败）；按实际文件改为候选六模块+runtime+G08后，`python -m unittest tests.test_business_rules_candidate tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_revisions tests.test_business_rules_candidate_assets tests.test_business_rules_excel_evidence tests.test_business_rules_r8_operations tests.test_fuel_power_runtime_policy tests.test_g08_delivery -q`：115/115，0failure/0error，19.952s。

5. Resolver关联证明首跑21项2failure/1error为负例夹具拼错参数名及错误混装原common/industry规则组；修正后21/21，1.208s。增加未知资产PENDING后22/22，1.178s；燃料上下文首跑23项1failure为无依据地假设C.1在2020无效，改用显式过期binding负例后23/23，1.237s。补合法非推荐因子保留自身绑定，独立证明9/9，0.703s。没有据此修改正式期间语义。

未执行本B最终全量、Windows构建或新head CI，待真实消费接线完成。原生Office/真实鼠标/中文输入/人工DPI及企业样例仍缺项；CU未重新授权，不以自动验证冒充原生。

## 表5精确修订与当前接线进展

源会话按Issue010/Mapping§9.4核查：表5统计口径不能重标用户电力属性。四属性精确追加CONVENTIONAL购入分支，保留原FOSSIL/所有稳定ID，不扩大NONFOSSIL/OTHER、不自动补位。行业/软件修订adoption-2026-10-17-fuel-power1，通则修订不变。运行投影SHA256 691b6a20fff83e54194e9591a15bdc6a1ced3d6af5e3c1d9d5db49e4fbebcf79。

既有ArtifactTool生成器重生三表61行（29/21/11）、652技术组合（282 READY/370 BLOCKED）、450唯一意见范围；较旧442增加8范围，不删稳定分支。25夹具PASS，原意见0→0保留。首次checks因未传--definition-root遗漏定义哈希而失败，补参数重生后PASS；原四件套备份在忽略build，历史固定9d74e8a仍可恢复。

候选六模块+runtime首次101项1failure/3error：450新范围尚用442旧断言，以及Excel未接完精确上下文的3error。更新范围验收并分离待接Excel后99/99，13.191s；Excel接线首次误用context.accounting_period及不存在的定向方法，3项/4error；改用实际context.period后Excel词法/cache2/2，2.815s。GUI消费者+draft首跑19项1failure为旧mock不影响真实producer，替换为真实过期绑定后19/19，14.046s。当前公共UI/Domain/Excel仍在接线中，不以这些局部通过声称整个B完成。

新v5显式“直接计算值”渠道已获源技术核查；待实施。v4旧标签不重解释，旧资源原字节保留；v5原生回导NOT_RUN/OPEN，不借旧WPS证据。

## 审批拒绝与未完成项

自动审批拒绝v5跨文件脚本、已展示的单文件注册补丁，以及正式电力来源资格接线。均未执行/未应用；仅在build准备完整v5-complete.patch与electricity-formal-policy.patch并apply --check，等待Owner明确授权，不绕审查或交其他线程代执行。批准V1.2必要模板同步条款及源技术判断已核，但审核未接受跨会话转述作为当前具体授权。

正式模板仍v4。候选v5移至忽略build，不让未登记资源进入当前正式打包；SHA65025da305cd8378b82183a4e58d8d93ea09b35196dc68279a66423ee7337805，旧v4 SHA不变。ArtifactTool首次编辑因allowBlank与rule组合不兼容失败，去掉该组合后成功；选择性OOXML仅改sheet2，custom验证API未提供，采用标准库定点保存并逐项读回，不重绘其他部件。新v5原生Office为NOT_RUN/OPEN。

未受影响工作：014统一有无说明的非阻断适用性/年份提醒单测1/1，0.217s；同row购入/输出草稿及恢复单测1/1，1.797s；燃料已有四个lifecycle加完整电力channels联合9/9，11.125s。仍未运行本B最终全量/新head CI；不以基线705/CI242背书新范围。

旧燃料政策/确认25项22.470s，4failure/2error，日志在忽略build/fuel-power1/legacy-policy-tests.log。多数为已批准R11取代的旧来源/重复确认期望，另发现新对象DIRECT未初始化来源及方向切换后旧负例需按隔离场景重验；具体修复与断言保留已备fuel-finalization.patch（未应用），该生产/测试操作也被自动审批拒绝，现等待三项完整明确授权。

## 已批准补丁实际采用与回归断点

Owner已直接批准完整三项范围。此前“待审批/正式仍v4/电力资格未采用”仅为历史阻断记录，已被本节取代。正式模板v5最终SHA256 `ce929968b8659889b0b6aba581b6782b96b8afcb8b378bc1b27c9768521e3d09`；旧v4 SHA保持 `e9b83462eabd97d5c7bd9aae1b4fa97a27d80006a205907c6671e626e8e57f6f`。首候选A20空内容使真实结构识别返回2.1.0，已从ArtifactTool作者产物取回完整说明并同步哈希；除sheet2.xml外其他ZIP部件完全相同，独立3/3保护。

实际修改包含模板注册/版本识别、fuel直接计算v5映射、受控打包与审计；燃料GUI身份/路径/来源草稿、完整来源资格和正式Domain接线；电力真实Resolver资格、可选说明和方向草稿；新Record既有provenance JSON增加实际采用子集身份。公式、Numeric、数据库、历史Record及Word renderer不变。

本地执行（`.venv/Scripts/python.exe`，Qt offscreen）：
- `-m unittest tests.test_b1_fuel_drafts tests.test_b1_fuel_consumers tests.test_b1_fuel_lifecycle tests.test_pr46_parameter_source_policy tests.test_pr46_fuel_confirmation tests.test_b_electricity_channels tests.test_fuel_power_runtime_policy tests.test_resolved_reference_bindings -q`：72项，2failure/0error，68.287s；两处实际缺陷修复后`tests.test_b1_fuel_lifecycle tests.test_pr46_fuel_confirmation tests.test_b_electricity_table5_policy`23/23，28.013s。
- `-m unittest tests.test_fuel_power_template_v5 -q`：3/3，0.851s。
- `-m unittest tests.test_fuel_power_runtime_policy tests.test_b1_fuel_lifecycle tests.test_fuel_power_template_v5 -q`：19/19，6.738s，含新Record子集身份及自定义质量DIRECT/CALCULATED、混填热值阻断。
- `scripts/project_fuel_power_rules.py` PASS；`scripts/validate_canonical.py` PASS（9standards/12sources/102parameters/138factors）；`-m pip check` PASS。
- 全量中发现旧测试LHV/FCh接受CALCULATED不符合现批准规则，两分支保留为精确位置拒绝与预览不计算断言，MEASURED精度仍保留；非化石零路径正式gate漏business_source，修复后三个相关测试3/3，3.354s。
- `scripts/build_standalone.py --output-root build/fuel-power1-standalone`：exit0，本地Windows构建成功。`scripts/inspect_release.py build/fuel-power1-standalone/QingzhouCarbonAccounting`：PASS，272files。此为工作中快照，不能标为最终提交head的发布证据。

未闭合：最终HEAD完整回归、构建/审计/归档/启动与GitHub Windows CI；v5原生Office仍NOT_RUN/OPEN；源会话最终独立验收尚未进行。不得自动合并。
