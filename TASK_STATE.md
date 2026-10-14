# 当前任务状态

状态：PR46验收修订实现完成，代码独立审查通过；旧测试迁移已验证，最新远端Windows CI收口中，不自行合并。
最后更新：2026-10-14。

- origin已核实adgo07/GHGTOOL，独立分支codex/ghg-standard-input-unification；base main204dded5d03853617f79a1f05693e89b619df9d1；当前生产验收head8d87199f25bd17e56e2e8443e09575966d557f12。原主目录用户分支、Excel母版及参考文件未覆盖。继续PR46，PR45仍OPEN未合并。
- Owner批准本轮11项、统一导出目录、Word必要注释及全链清理；Issue010覆盖旧软件输入限制。详情见IMPLEMENTATION_REPORT，不把旧六包510项或旧CI219当成本轮验收。
- 名称确认/重选重置、单位草稿、STD/CALC/MEASURED分段、标题开关、FGD一组分/多组分安全、蒸汽持续标签、电力五表正式链及冻结Record实际表格已完成。
- 新模板2.1.0 SHA256 f303ad02ca03e0464f736dafc39967abd06366a902f1b502dd17470656eb1718；旧2.0精确哈希资源只读兼容。新算法CAR-SM01-2026-10-14-G06.5；公式/系数/Decimal Profile不变，历史EXCEL_R2及冻结Record不迁移。
- 独立审查发现并修复：恢复STD显示值与正式值分叉、旧直接实测来源污染新身份、失效电力及特殊口径自动回退（购入/输出均阻断）；26项组合通过。独立Luna复核生产head，15项燃料/FGD、29项G06通过，未发现剩余阻断/高/中级问题。
- 本地完整561项：550通过/9失败/2错误，616.685秒。RS03旧fixture补N14后两模块9项通过；另外3项旧UI断言迁移后3/3通过（4.324秒）。不是本地全量全绿，最终完整回归以PR最新Windows CI为准。
- 本地head8d87199 Windows构建通过，发布审计269文件、ZIP回导270可见文件、两次隔离启动通过；manifest source/pr-head/tested-merge一致。
- 当前2.1 WPS ET原生TEMP副本保存回导17/17通过，16个数据验证约束保留；WPS文字只读TEMP报告渲染11页/10业务表已逐页检查。Windows Qt原生平台100%/125%各20项程序检查与19次捕获（18个不同PNG）通过，证据在docs/ui/standard-input-evidence/rework。
- 中央锁定ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，Architecture V2.1/Numeric v1；未改Frozen/Profile/数据库结构，未增加第二标准或结果Excel导出。

未闭合：最新head GitHub Windows CI及最终证据diff复核；电脑操作工具截图超时/激活失败，真实鼠标与中文输入验收未执行，不能以QTest或截图代替；Owner真实企业样例、人工系统DPI操作验收仍开放。最终等待检查，不自行合并。
