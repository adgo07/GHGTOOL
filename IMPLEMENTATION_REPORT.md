# PR-B：新建核算页面整页优化实施报告

## 结果与范围

2026-10-24完成本地实施，等待源会话独立最终验收。复用已认可整页样板和既有隔离分支，未推送、未建PR、未执行CI、未合并。产品标准支持状态不升级。

- 八类目录与十个底层身份继续消费原控件；目录仅浏览，启用仍调用原处理函数。已启用、未启用、部分启用、历史待确认具有不同文字/轨道/符号，支持键盘与焦点反馈。
- 保留品牌和全局侧栏、唯一mainScrollArea；只有当前来源贡献内容高度。编辑区按可用宽度3/2/1列重排，换列后按实际内容高度传播，不使用固定编辑高度或内层滚动。
- 三工序统一物料边界、行头删除与就地换算；烟气先身份/时段再参数；脱硫保留设施—批次—组分层次；热力先边界再焓方式和适用参数。燃料DIRECT保留未参与字段/草稿，电力其他来源收起目录字段但保值。
- 顶部项目/核算动作、唯一外部补充/问题/结果/参数快照保持整体层次。错误定位会展开所属换算/外部明细，不改输入、来源、基准或纳入声明。
- 热力数值editingFinished仅连接原只读preview一次；不调用正式核算、不写Record、不覆盖数值/旧结果。正式校验与算法保持原实现。

## 本地验证与受验身份

环境为Python 3.12.14、Qt 6.11.2、offscreen，合成输入和独立临时数据库。命令及原始输出均保存在 `docs/ui/whole-page-review/final/`。

1. `python -B -m unittest tests.test_accounting_source_directory tests.test_accounting_projects_ui tests.test_uir02_source_cards tests.test_b1_fuel_drafts tests.test_b_material_draft_scope tests.test_pr46_electricity_source_consistency tests.test_uat03_responsive_fields tests.test_b_fume_segments tests.test_b_fgd_specialist tests.test_b_heat_specialist tests.test_b_material_identity tests.test_b_heat_report_units -v`：151项通过、0失败，394.851秒，见 `regression.log`。
2. 最后仅补展开定位后，`python -B -m unittest tests.test_accounting_source_directory -v`：13项通过、0失败，79.044秒，见 `directory-final.log`。其中12项与主回归重复，不能相加声称164项独立用例。
3. 在最后一项测试增加控件相对当前页面可见的直接断言后，单独执行该定位用例：1项通过、7.929秒，见 `locator-visible-final.log`。它属于上述13项的重复补强，不增加独立计数。
4. `python scripts/capture_accounting_ca.py docs/ui/whole-page-review/final-refresh`：完成42张真实Qt图，最后归档为 `final/`；当前7个UI源文件与捕获脚本SHA256逐一匹配，回调错误为0。故意缺项核算零Record，随后一次成功追加一条临时Record；修改后Word出口禁用。见 `summary.json`、`capture.log`。
5. `git diff --check`及暂存差异检查通过。两次中间长回归在修复迭代中中断，不计为最终通过证据；早期裁切及销毁后回调均已修复。

**不把151项声称为全部在最终head执行。** 其受验生产源码身份见 `tested_151_identity.json`（捕获时父HEAD及7个源哈希）；最后生产差异仅为 `error_locator_final_delta.patch` 的8行展示层补齐，由13项专项覆盖。该文件的补丁前源码重建哈希已与主回归受验哈希匹配。最终提交完整SHA由送验消息和Git HEAD给出，不制造自引用SHA。

项目UI回归覆盖半填/旧项目SQLite重开、动态身份、来源草稿、结果过期和正式Record链。最终专项覆盖3/2/1阈值往返、真实壳1680/1180/1440往返、展开/收起、动态增删、长短来源切换、字段容器完整性、尺寸收敛、导航不改dirty/form_state、跨源错误定位以及热力有效/缺失/非法值编辑完成后保值与零Record。没有新增算法、Canonical模型、DB迁移、依赖、模板或报告规则。

## 视觉证据及限制

当前入口 `docs/ui/whole-page-review/final/review.html`；原根目录21张第一阶段图完整保留为已认可历史样板。最终42图覆盖八类常规与1180×850窗口、三工序换算、烟气多段、脱硫多组分/批次、热力已知/自动、顶部、四态、公共问题/成功与过期结果。1180窗口实际编辑区宽614；单列由430宽实际控件自动测试证明，不声称产品允许低于既有最小窗口。

astra/medium视觉会话已对所覆盖画面给出PASS，无剩余阻塞视觉缺陷；最后定位补丁不改变视觉布局。焦点清楚，悬停图为“聚焦+悬停”组合态，不宣称四态全部独立hover已验。占位标题较小/略上移是保留的非阻塞一致性备注。

未执行完整discover、GitHub Actions、打包/实包、原生鼠标/IME/系统DPI/物理屏幕、Office、企业真实样例或新性能量化；不冒称Windows正式发布或商业验收。截图不替代标准计算正确性、人工DPI或原生交互证明。

## 平台 / Contract 预检查

实际核对worktree、origin与fetch、分支、HEAD、工作区；沿用 `codex/ui-business-layout`，实施起点 `1c1ff710ee443b73a4f11c0a465939866947c403`，origin为adgo07/GHGTOOL，默认分支main，已核对origin/main为当前分支祖先。已有未提交样板完整保全。

中央origin已验证为adgo07/Qingzhou-contracts。locked SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`不升级，已读锁定Architecture V2.1与当前UI指南v0.2。适用MUST/MUST NOT：保持Presentation/Application/Domain分层；显示不得反馈正式比较；UI State不得成为公共Workspace；历史Record不漂移；不得复制算法。此次无Contract冲突、无中央修改需求。本任务不涉及中央公共 Contract。

相关Standard Issue：是，既有004/016/018、017、020的原字段展示；新增问题：否；改变既有软件解释：否。公式、来源资格、标准适用、Numeric Profile、Canonical、数据库和历史Record未修改。
