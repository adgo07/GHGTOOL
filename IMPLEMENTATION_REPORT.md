# C＋A 三业务区布局实施报告

## 结果

按用户批准的紧凑版样板接入实际核算页，保留应用左侧导航。燃料三列排列，实测报告采用同排标签/输入对齐；电力购入/输出及来源选项、煅烧材料来源采用原 typed combo 的轻量单选视图。所有来源资格/禁用项/草稿仍由原逻辑决定，未复制业务规则。

目录切换不启停排放源；禁用页说明输入保留，并提供明确启用操作。固定编辑区起点并在内部滚动，避免煅烧展开推动其它目录位置。校验错误跳转会先揭示正确目录。新增和恢复的条目沿用相同布局，其它业务区不推广。

## 平台 / Contract 预检查

本仓 origin 已核实为 `adgo07/GHGTOOL`，已 fetch；复用隔离分支 `codex/ui-business-layout`，基线含 PR58 合并。中央 Frozen lock `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，已读当前 UI 指南 v0.2。本任务不涉及中央公共 Contract；不改变标准解释、来源资格、Calculator、Canonical 或 Record，无新增 Standard Issue。

## 本地验证

Python 3.12.14 / Qt 6.11.2 / offscreen。使用现有项目依赖环境，没有安装新依赖。

1. `python -B -m unittest tests.test_accounting_source_directory tests.test_compact_choices tests.test_uir02_source_cards tests.test_b1_fuel_consumers tests.test_b1_fuel_lifecycle tests.test_b1_fuel_drafts tests.test_b_material_gui_excel tests.test_b_material_draft_scope tests.test_electricity_region_persistence tests.test_pr46_electricity_source_consistency -q`：56/56，86.754s，0失败/错误。
2. `python -B -m unittest tests.test_accounting_projects_ui -q`：最终21/21，94.279s，0失败/错误，覆盖项目/核算单元保存、恢复、正式记录保护。本轮最终两组共77项；此前第一轮29项不重复相加。
3. `python -B scripts/capture_accounting_ca.py <新的输出目录>`：退出0；9次目录往返完整 form_state 相同，输入与实测报告文本保留；报告输入对齐误差≤2px；真实按钮切换和换算展开通过，回调异常0。1680×1120、1440×1000共10张截图已检查。
4. `git diff --check` 通过。源文件哈希及执行脚本哈希见 `docs/ui/ca-layout/summary.json`；本地工作区捕获不冒充精确head构建。

## 未执行与交付边界

未运行全量套件、CI、打包或原生桌面；本轮没有数据库、公式、标准范围、Excel或Word改动。未 push/PR/合并。原生Office、鼠标/IME/系统DPI、企业样例和正式交付门继续OPEN。本轮只达到三段布局的本地实施与定向自检断点，待视觉验收。
