# 当前任务状态

状态：PR46第二轮反馈修订中：逐字段来源、来源简写、电力短标签、公共分段外观及导航实测优化；继续原PR，不自行合并。
最后更新：2026-10-14。

- origin已核实adgo07/GHGTOOL，独立分支codex/ghg-standard-input-unification；base main204dded5d03853617f79a1f05693e89b619df9d1；当前生产验收head8d87199f25bd17e56e2e8443e09575966d557f12。原主目录用户分支、Excel母版及参考文件未覆盖。继续PR46，PR45仍OPEN未合并。
- Owner批准本轮11项、统一导出目录、Word必要注释及全链清理；Issue010覆盖旧软件输入限制。详情见IMPLEMENTATION_REPORT，不把旧六包510项或旧CI219当成本轮验收。
- 名称确认/重选重置、单位草稿、STD/CALC/MEASURED分段、标题开关、FGD一组分/多组分安全、蒸汽持续标签、电力五表正式链及冻结Record实际表格已完成。
- 新模板2.1.0 SHA256 f303ad02ca03e0464f736dafc39967abd06366a902f1b502dd17470656eb1718；旧2.0精确哈希资源只读兼容。新算法CAR-SM01-2026-10-14-G06.5；公式/系数/Decimal Profile不变，历史EXCEL_R2及冻结Record不迁移。
- 独立审查发现并修复：恢复STD显示值与正式值分叉、旧直接实测来源污染新身份、失效电力及特殊口径自动回退（购入/输出均阻断）；26项组合通过。独立Luna复核生产head，15项燃料/FGD、29项G06通过，未发现剩余阻断/高/中级问题。
- 本地完整561项：550通过/9失败/2错误，616.685秒。RS03旧fixture补N14后两模块9项通过；另外3项旧UI断言迁移后3/3通过（4.324秒）。不是本地全量全绿，最终完整回归以PR最新Windows CI为准。
- 本地head8d87199 Windows构建通过，发布审计269文件、ZIP回导270可见文件、两次隔离启动通过；manifest source/pr-head/tested-merge一致。
- 当前2.1 WPS ET原生TEMP副本保存回导17/17通过，16个数据验证约束保留；WPS文字只读TEMP报告渲染11页/10业务表已逐页检查。Windows Qt原生平台100%/125%各20项程序检查与19次捕获（18个不同PNG）通过，证据在docs/ui/standard-input-evidence/rework。
- 已核实的Windows CI #221（run38546946024，交付head e500edc65fa1191acf0197454d6ad012118f19e0）：merge-ref d30568374d7a332bc231251c34fceada06b79081完整561/561通过（747.623秒）；精确PR-head交付专项14/14通过（4.293秒），构建、271文件审计、272可见文件ZIP回导、两次启动及provenance校验全部通过。Artifact11885782152名称与head一致，ZIP59,785,100字节。后续纯证据文档提交不修改生产；最新PR head与Checks、候选下载入口以PR46正文为准，不混用本地和CI来源。
- 独立Luna最终复核e500edc：8d之后无生产差异，12项旧fixture/UI回归定向通过，原业务/精度/关联断言未弱化，证据来源和边界一致。
- 中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，Architecture V2.1/Numeric v1；未改Frozen/Profile/数据库结构，未增加第二标准或结果Excel导出。

未闭合：电脑操作工具截图超时/激活失败，真实鼠标与中文输入验收未执行，不能以QTest或截图代替；Owner真实企业样例、人工系统DPI操作验收仍开放。最终等待检查，不自行合并。


第二轮新范围（2026-10-14）：Issue011已先登记；Owner明确目录燃料FCh默认缺省可修改、自定义燃料参数全部由使用者填写。共享来源政策待逐字段独立核对；导航先计时再优化，不能把静态慢路径当已测唯一根因。Luna子代理分别承担来源/正式Excel链、导航计时优化及共享展示组件，root负责核算页接线和整合。此前d36 CI222/561通过只证明第二轮之前的基线，不替代新验收。

第二轮稳定断点：核算页已消费共享 parameter_source_policy；目录FCh保留STD/CALC/MEASURED显式选择，自定义燃料不带数值默认；FGD EF统一Canonical来源tokens，旧STD/CALC仅restore边界解释，I/TR按实际组件数与通用Resolver绑定展示。添加第二组件保留首行STD90草稿并拦截重算；删除回单保留实测值。物料唯一实测以只读来源标签显示，旧计算来源有明确确认入口。`python -m unittest tests.test_pr46_fuel_confirmation tests.test_g06_fgd_ui -v` 本地18/18通过，61.291s。期间新增物料cell变量遮蔽导致Qt父子布局循环，已定位并改为cell_layout；此前异常耗时测试被终止，不计为通过。全量/新母版WPS/本轮Windows CI尚未执行，不沿用上一轮完成结论。

独立来源审查修复断点：燃料来源切换按field/source分开保留运行时草稿，首次改源不冒用缺省数值；FGD旧STD/CALC/CATALOG保留原始机器码与数值，明确确认后才采用新来源；百分比双向转换通过Decimal指数精确位移，不受caller ambient context影响。`python -m unittest tests.test_pr46_percentage_precision tests.test_pr46_fuel_confirmation tests.test_g06_fgd_ui -q` 本地21/21通过，60.612s。更早`tests.test_g06_page tests.test_uat03_formal_workflow`34项为30pass/1fail/3error(153.665s)，error定位到新Domain FGD门禁引用未定义accounting_period，后端代理已修，仍需复验；不得把这次失败记为通过。

当前追加验证：后端来源/规则/Record证据组合69项通过(2.700s)，关联材料/Numeric/canonical项目45项通过；修复期间NameError后的`tests.test_g06_page tests.test_uat03_formal_workflow -q`本地34/34通过(161.052s)。Windows Qt实际windows平台source-policy脚本100%/125%/150%各12项状态检查、7张截图通过；共21张截图，属于QTest/程序驱动与QWidget.grab，不能冒充原生人工鼠标/中文输入验收。不同来源草稿已进入既有form_state JSON，仅Presentation state，无数据库/Canonical模型变更。canonical验证9 standards/12 sources/102 parameters/138 factors通过，pip check无破损依赖。Excel v2.2资源与字段策略仍由Luna子代理收口，未启动本轮完整回归/构建/CI。
