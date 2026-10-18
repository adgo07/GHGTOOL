# 当前任务状态 — B-HEAT

更新：2026-10-18。状态：PREFLIGHT_COMPLETE / SPECIALIST_INTERFACES_DISPATCHED。PR51已由源独立核验并合并，merge a1aeebc1b6809397e61a2ffa7a2333a3b440c756；固定bbb/CI273、944项与实际包证据保持在docs/ci/B_FUME_SUMMARY.json，不修改旧阶段证据。当前唯一正式出口为V2§10的015热源边界、heat.factor与合法已知焓完整链；外部CO₂只专属准备，不进入本段生产/送验。

## 实际基线与分工

已实际核origin adgo07/GHGTOOL、fetch、默认main含PR51 merge；新独立codex/b-heat-integration从最新origin/main起步，HEAD为上述merge，起步干净。旧树和根用户资料未动。C独占共享Canonical/codec/Calculator/Application/Resolver资源/GUI/B.9/Record/Word/构建/治理及整链；F/M使用gpt-6.1-sol/medium。

| 所有者 | 固定范围/依赖 |
|---|---|
| F | packages/standards/carbon_material_heat.py、tests/test_b_heat_specialist.py；依赖当前main既有HeatInput/SteamEnthalpyEvaluation；不得改共享文件或造输入模型 |
| M | packages/standards/carbon_material_external_co2.py、tests/test_b_external_specialist.py；仅外部专属准备分支，后续B-EXTERNAL才整合 |
| C | 全部重叠共享文件/采用资源/版本/输入模板/报告/包；专属成果单次整合，不cherry-pick旧链或建平行规范 |
| N | 本轮不启动 |

## 最小接口（本段内协作，不是公共Frozen Contract）

F：evaluate_known_enthalpy(line:HeatInput,*,policy,numeric_profile_id)->既有SteamEnthalpyEvaluation。只消费明确已知焓，规范kJ/kg；不访问P/T/表/auto，返回USER_MANUAL、reference/table/bounds=None、interpolated=False；有限<=0照旧保留，C加WARNING，不擅变ERROR。专属UnitService显式注册kJ/kg、GJ/kg、GJ/t线性单位，倍率1/1000000/1000，不改公共注册库。KNOWN_ENTHALPY_METHOD_VERSION=CAR-HEAT-KNOWN-017.1。

F：classify_heat_boundary(*,energy_direction,source_boundary,fuel_emissions_accounted)->PURCHASED / INTERNAL_ALREADY_ACCOUNTED / EXPORTED。外送不改；购热界外正常，明确供热燃料在本企业重复计入时澄清；同边界且燃料已计不再计购热，未计/未知/边界未确认不猜算。C先分类，再对参与计算行求值；内部已计不强求无关HM/因子，不删除燃料、不算0假装购热。HeatInput尾字段由C唯一维护；F仅消费明确标量事实。

M：evaluate_external_co2_supplement(*,included,amount原词法或Decimal,unit,carbon_total_tco2可None,carbon_complete,known_scope_violation=False,known_period_mismatch=False,known_previously_counted=False,policy,numeric_profile_id)->专属只读ExternalCO2SupplementEvaluation（status/amount_tco2/supplementary_total_tco2/enterprise_complete/profile/method）。未纳入不校验草稿；纳入空待补不造0；有值含0须有限非负、tCO2/tCO₂且无已知违规。core None不能救场，core净值不擅设非负；只加一次，不返回/改ES/EI/ET/Record.total_amount，炭素缺口不变完整。名称/附件不进数值门禁。此结果不是新Canonical输入或平台公共模型。

## 平台 / Contract 预检查

业务base为PR51 merge；locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20不变。中央origin已验证/fetch；Architecture2.1、Numericv1/Profilesv1按locked读取，UIv0.2/产品家族/验收清单按当前正式合并入口读。MUST：分层、共享内核、声明Profile消费、ambient独立、full-value exact、原/规范/显示值分开、历史冻结；MUST NOT：隐式float/默认epsilon/显示回流/Qt状态当公共Workspace/自动Frozen升级。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE；本轮无中央缺口或修改。

相关Standard Issue015/017/019（016仅准备）；不重新裁定。017指定iapws分发未解决，F仅隔离原始许可/接口/参考调查；未获Owner具体实现选择及数值/包核验，不进产品依赖/包、不静默换库或回旧表。已知焓独立不受辅助auto失败阻断，旧C.4/C.5仅历史。当前尚未实现新物性子Profile，不称库为p40。

## 下一稳定断点与边界

C接管heat.factor同源资格/Resolver/采用值/快照、明确购热边界尾字段与版本/兼容，GUI/表格/项目恢复/Record/Word/真实包完整链。源正在向Owner提出017窄实现选择，不阻塞其他链。F/M已授权并已唤醒；当前C生产实现/本轮测试尚未执行，不能借PR51/专属准备称本包完成。

保留燃料/电力/材料/FGD/烟气、旧模板和历史Record/Word；不改计算表，不CU、不商业发布、不扩标准或N。原生Office/鼠标/中文IME/人工DPI/企业样例/干净目标机/商业履约继续OPEN。完成新私有PR+attach+新CI/精确包后停源验收，C不自行合并新PR。


## 2026-10-18 专属整合稳定断点

F交付4bdef411c503e726c74b1bfadd61e9e82e7f27e6，C只取packages/standards/carbon_material_heat.py与tests/test_b_heat_specialist.py两文件，未取M外部准备。C本地Python3.12.14执行`python -B -m unittest tests.test_b_heat_specialist tests.test_numeric_contract_v1_adoption -v`：29/29通过、0失败/错误/跳过，0.053s。此证据仅为helper及Numeric保护，不是GUI/Excel/正式Record/Word/包完整链。

heat.factor已机械生成待审资源候选，尚无生产消费者。自动审批拒绝一次组合编辑：包含路线、HeatInput和Calculator/Resolver行为变化，理由是缺少用户本人对具体热力接线的可核实授权且脚本替换范围过大。拒绝脚本没有执行。C已向用户提出具体边界、已知焓、同次Resolver、自动路径不回旧表及适配器接线授权，等待答复；正式接线暂停，文档与现有专属验证继续，不绕过拒绝。自动物性具体实现选择仍独立等待Owner。尚未执行本包全量、构建、GitHub Actions或实际包验证。

## 原始授权核实与领域链断点

已从源会话工具直接读取用户原始消息（turn01a14e3a，userMessage01a14e3a-3a98）：“PR51自检通过并合并后，启动下一步工作”；上一turn01a14e32明确热力/蒸汽完整链计划。携此证据按单职责最小补丁重新走正常审批已获接受，不重复执行被拒的大脚本；先前接线待授权状态已解除。017更换具体实现仍待Owner，不在该阶段授权中。

已接HeatInput边界尾字段、codec5（旧1—4读为UNCONFIRMED、保留原值）、独立已知焓及方法/Profile trace、015先分派再求值、heat.factor机械资源/真实Catalog资格提供者与同次Resolver采用。无公式/Numeric/数据库迁移或旧Record更新。C本地`python -B -m unittest tests.test_b_heat_runtime -v`：7/7、0失败/错误/跳过，1.000s。正式热力独立期望0.308；燃料保护比较原正式p40全值，未用显示8.624代替全值。

失败如实记录：首轮7项3FAIL（夹具使用2025目录适用期和理想燃料小数未考虑既有p40操作次序），第二轮7项10ERROR（测试误用AccountingPeriod字段名），修正后7项1FAIL暴露热力资格尚未加入正式提供者；接入后仍1FAIL，核查真实Catalog单位为tCO₂/GJ并兼容既有别名后上述7项通过。一次诊断脚本漏PYTHONPATH导致docx导入ERROR，不计作业务测试。尚未执行GUI/B9/Word/全量/包/本包CI。
