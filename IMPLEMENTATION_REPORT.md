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
