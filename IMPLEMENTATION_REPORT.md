# PR47 R8 候选规则对齐实施报告

已将 PR48 批准 R8 映射同步到原 PR47 分支，候选规则和非工作簿专项验证完成。正式审阅表已在用户文件释放、实际备份后更新，完整专项 71/71 通过，待提交并交最终独立验收。本报告不宣称生产已采用 R8 或本轮验收 PASS。

## 平台 / Contract 预检查

仓库 origin 为 https://github.com/adgo07/GHGTOOL.git，分支 codex/ghg-business-rules-a；实际 base b0c1aa723391772f9aef026b4c0a8619eb61a65b，当前 merge head 84e7fd9ac948806ee4d5c6b15cadbb156d7e5318。PR48 merged 状态与实际 fetch 均已核实。最终 head 应由原 PR47 提交及评论精确定位。

中央 locked SHA：ee5feb0cc34dbd99790500fadd0c4c932e202a20。既有 Architecture V2.1 / Numeric v1 / Profiles v1 继续适用：分层、正式 Calculator/Resolver 唯一入口、高精度与 exact 比较、显示修约不回流、Project 与不可变 Record 分离、历史快照不漂移。禁止第二算法、epsilon 正式判定和自动升级 Frozen。本任务不涉及中央公共 Contract 修改；无公共冲突或新 Contract adoption。

Standard Issue：012/013 保留，010 已批准的五表选择证据补回；014 的产品选择不再待 Owner 决策，但专业依据仍 OPEN；015/016/017 按 R8 已批准决定对齐，018/019 保持 OPEN。本轮改变候选表达，未改变正式生产计算解释或标准支持范围。

## 实际修改与保护边界

行业候选保留 11 个业务字段、41 项政策、原 10 条规则；Software 无内部字段镜像，保留 19 项业务操作及 8 项变化。未重新引入此前删除的 442 项镜像，也未新增通用框架。

燃料目录缺省与实测资格分开，自定义未绑定燃料初始实测且无自动数值；直接含碳量路径保留计算/实测资格。物料 CALCULATED 必须声明既有已批准收到基换算路径，该声明不能替代必要数值及基准验证。脱硫使用本批有效组分数；热力选择实测时没有 0.11 偷回填。电力五表适用条件保留，库外手填是输入方式而非实测身份，非化石购电零值仍需要独立适用绑定。

外购 CO₂ 补充保持 ES/EI/ET 分立；IAPWS 只登记未来版本化物性边界，不安装、不实现，不以旧表自动回退。候选 Loader 只增加严格上下文与来源不适用检查，不接 GUI/Excel 正式计算链。

AGENTS、路线、README、语义政策、HANDOFF 和历史证据只作必要局部纠偏；报告 schema 仅补维护边界说明，结构、类型、版本、必填性与投影不变。Mapping 原文、批准 V1.2 原始字节、Common、platform-lock、Catalog、数据库、正式公式、生产 GUI/Excel/Word 实现均未改。V1.2 SHA256：98abf84ea7f7af3887d60c3c1e128c272d73ccbf73892d76581ad1771bfad876。

## 历史负担与五点调整

1. 015 采用最新已批准边界，旧盘点中的待决状态不再成为新的审批步骤。
2. 01—07 在本包只收口规则和文档；生产消费者替换属于 PR46，未提前执行。
3. Schema 继续负责结构、类型、版本、必填性及渠道投影，不把它扩成第二业务引擎。
4. 只合并确属同一业务概念的定义，标准差异与渠道差异保留；不按文件大小机械拆分。
5. 资源登记不能替代实际模板、来源与发布资源的独立验证。

11/12/17 按已证实职责最小处理；08/09/10/13/14/16/18—25 没有足够删除证据的职责保留或延期。不另建长期 25 项治理台账，不宣称产生安装包体积或运行速度收益。

## 验证：命令与真实结果

- Python3.12：`python build/business-rules-authoring/run_r8_nonworkbook.py`，68/68 通过，0 fail、0 error，7.528s。开发辅助命令明确排除三项正式工作簿断言，不能称完整回归。
- 三份实际候选 JSON Schema 校验通过；`node --check scripts/build_business_rules_review.mjs`、候选与测试 compileall、`git diff --check` 已通过。
- 独立只读审阅：结构/路径/修订/操作共 21 项通过，另 4 项资产保护检查通过；不替代最终 head 验收。
- 临时工作簿：业务 11 / 操作 19 / 变化 8；0 公式、0 错误单元格；冻结、表格和状态验证保留；重排后模拟意见 6/6 保留，删除定义的意见进入变化页。相同投影已更新为正式工作簿；用户已保存意见为 0，备份保留。
- 临时工作簿渲染已查看，不能当作原生 Office 验证。只读 C.1 单位归一后映射/目录数值核对 78/78 一致，不等于重新核验全部官方来源。

开发中首次专项曾出现 1 项来源上下文回归，随后修复；扩展专项曾出现 1 项物料来源组合缺口，随后修复并通过上述 68 项。一次文件独占备份检查失败，未成功备份或覆盖用户工作簿；不能以 PowerShell 最终退出码 0 抹去内部异常。未执行的项目见下节。

最终联合命令：`python -m unittest tests.test_business_rules_candidate tests.test_business_rules_candidate_paths tests.test_business_rules_candidate_assets tests.test_business_rules_excel_evidence tests.test_business_rules_candidate_revisions tests.test_business_rules_r8_operations -q`。实际 71/71，通过，0 fail、0 error，5.543s。

工作簿 SHA256：03ff175623a82f2112496e81f2787a97eeb6d69cee9f3d79d05b1dd81d0f29d6；审阅 LF 投影 SHA256：966b195c679952d3d542658be3c661ad2a7e328473ac6d0f27f1f08be190c459。生成器实际反馈：38 行、保留原反馈 0 条。一次临时依赖链接使用了不存在的路径，失败后按实际 loader 路径纠正；未安装依赖，临时 Junction 已移除。

## 未闭合项与停止点

1. 文件占用已解除，独占访问及最新文件备份成功，正式 workbook 和证据已更新；三项实际工作簿断言及完整专项已通过。
2. 本轮最终提交与新 head CI 随原 PR47 更新；尚未跑本地全量、Windows 构建、原生 Excel/WPS 或 GUI 验证，不引用旧 head 成功代替。
3. 完成后自动送「方案设计」独立验收并停止；不合并 PR47/46、不接生产、不实施 B/N。
自动审批曾拒绝一次广泛治理改写，理由是范围过宽且可能覆盖既有约束；该命令未执行。已采用可审查的局部修改，保留硬规则与历史证据，不重试广泛重写。
