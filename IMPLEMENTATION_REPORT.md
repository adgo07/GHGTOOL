# B-HEAT 实施报告（进行中）

日期：2026-10-18。状态：预检查完成、F/M最小接口已发布；当前尚未实施生产接管或执行本包测试，不宣布完成。

## 范围与基线

已实际核origin/fetch/main/干净新树，codex/b-heat-integration从PR51合并a1aeebc1b6809397e61a2ffa7a2333a3b440c756起步。旧FUME证据和用户根工作树不改。唯一正式出口V2§10：015真实热源边界防重复、heat.factor同源资格/Resolver、合法已知焓与GUI/B.9/Canonical/SQLite项目/冻结Record/Word/包；外部016只M专属准备，不入本段消费者/送验。

C公共独占，F/M路径/接口已按TASK_STATE固定并下发，可依赖当前main既有HeatInput/SteamEnthalpyEvaluation等类型，避免等待整套尾字段。已知HM<=0按旧实现WARNING仍采用，不新增范围解释或误改ERROR。Core默认UnitService未注册kJ/kg，实际只读探针返回UnknownUnitError；F将在专属helper显式注册三种线性比焓单位，这不是已通过的功能测试或公共Unit规则冻结。

## 平台 / Contract 预检查

业务base上述merge，locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20保持。中央origin已核/fetch，Frozen Architecture2.1/Numericv1/Profilesv1按lock读取；当前ACTIVE UIv0.2路由从已合并main读取。MUST：平台无关Domain/分层/共享内核、声明Profile一致、ambient独立、full-value exact、输入/规范化/显示分开、历史不可漂移。MUST NOT：隐式float/业务epsilon/display回流/Qt状态当公共Workspace/自动Frozen升级。Carbon p40/HALF_UP为允许项目差异，无中央缺口/修改。

相关Issue015/017/019，016仅准备；依据原Owner决定，不重新裁定。017自动物性暂未获相容具体分发方案，F仅原始许可/官方参考和接口核查，无生产依赖/包/自实现替代/旧表回退。源已向Owner提出具体实现窄选择；该项不阻塞known、边界与factor。

## 当前执行证据与OPEN

实际生产测试：NOT_RUN，原因：本包接口刚固定，实施尚未完成。F/M独立准备、PR51 CI273/旧实包均不能冒称本包验证。后续按稳定断点补真实命令、通过/失败数、原始失败原因、CI与实际包身份。

保护燃料/电力/材料/FGD/烟气、旧模板、旧Record/Word及独立projects/records存储。原生Office、鼠标/中文IME/人工DPI、企业样例、干净目标机、商业履约继续OPEN。无CU/N/商业发布。新私有PR创建后attach，新源码CI和精确包送源验收，C不自行合并。


## 2026-10-18 专属整合稳定断点

F交付4bdef411c503e726c74b1bfadd61e9e82e7f27e6，C只取packages/standards/carbon_material_heat.py与tests/test_b_heat_specialist.py两文件，未取M外部准备。C本地Python3.12.14执行`python -B -m unittest tests.test_b_heat_specialist tests.test_numeric_contract_v1_adoption -v`：29/29通过、0失败/错误/跳过，0.053s。此证据仅为helper及Numeric保护，不是GUI/Excel/正式Record/Word/包完整链。

heat.factor已机械生成待审资源候选，尚无生产消费者。自动审批拒绝一次组合编辑：包含路线、HeatInput和Calculator/Resolver行为变化，理由是缺少用户本人对具体热力接线的可核实授权且脚本替换范围过大。拒绝脚本没有执行。C已向用户提出具体边界、已知焓、同次Resolver、自动路径不回旧表及适配器接线授权，等待答复；正式接线暂停，文档与现有专属验证继续，不绕过拒绝。自动物性具体实现选择仍独立等待Owner。尚未执行本包全量、构建、GitHub Actions或实际包验证。

## 原始授权核实与领域链断点

已从源会话工具直接读取用户原始消息（turn01a14e3a，userMessage01a14e3a-3a98）：“PR51自检通过并合并后，启动下一步工作”；上一turn01a14e32明确热力/蒸汽完整链计划。携此证据按单职责最小补丁重新走正常审批已获接受，不重复执行被拒的大脚本；先前接线待授权状态已解除。017更换具体实现仍待Owner，不在该阶段授权中。

已接HeatInput边界尾字段、codec5（旧1—4读为UNCONFIRMED、保留原值）、独立已知焓及方法/Profile trace、015先分派再求值、heat.factor机械资源/真实Catalog资格提供者与同次Resolver采用。无公式/Numeric/数据库迁移或旧Record更新。C本地`python -B -m unittest tests.test_b_heat_runtime -v`：7/7、0失败/错误/跳过，1.000s。正式热力独立期望0.308；燃料保护比较原正式p40全值，未用显示8.624代替全值。

失败如实记录：首轮7项3FAIL（夹具使用2025目录适用期和理想燃料小数未考虑既有p40操作次序），第二轮7项10ERROR（测试误用AccountingPeriod字段名），修正后7项1FAIL暴露热力资格尚未加入正式提供者；接入后仍1FAIL，核查真实Catalog单位为tCO₂/GJ并兼容既有别名后上述7项通过。一次诊断脚本漏PYTHONPATH导致docx导入ERROR，不计作业务测试。尚未执行GUI/B9/Word/全量/包/本包CI。
