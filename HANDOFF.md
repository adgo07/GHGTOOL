# C＋A 布局实施交接

用户已选定 C＋A 紧凑对齐方案，本轮已实施燃料、电力、原料煅烧三个区域。当前分支 `codex/ui-business-layout`，尚未推送或建立 PR。PR58 已合并，不重做中文化。

## 实现与边界

`source_directory.py` 只管理展示与定位；原启用按钮/状态、typed combo、草稿及恢复机制仍是原路径。目录按钮没有业务状态写入；校验定位通过 reveal 先切换目录，再滚动至字段。三个编辑页留在同一业务页面对象树内。

`compact_choices.py` 的单选外观是显式局部选项，不更改其它业务段。燃料新增条目和煅烧新增物料自动应用批准布局；未建立第二套来源资格。原计量/方向切换造成的禁用和分方向草稿行为保留。

页面顶部排放源启用入口和其他业务段仍保留；当前只将指定三段移入目录。禁止以截图通过宣称完整交付通过，未启动任何原生桌面操作。

## 复验入口

- `docs/ui/ca-layout/review.html`：10 张真实页面截图。
- `scripts/capture_accounting_ca.py <新的输出目录>`：offscreen 独立临时数据库、合成输入；不是生产入口，不修改用户项目。
- `tests.test_accounting_source_directory`：目录状态隔离、新条目、校验定位、换算展开。
- 当前验证数量和限制见 `IMPLEMENTATION_REPORT.md`，不要拿 PR58 的 CI302 背书本轮。

## 平台 / Contract 预检查

本仓 origin 已核实为 `adgo07/GHGTOOL`，已 fetch；复用隔离分支 `codex/ui-business-layout`，基线含 PR58 合并。中央 Frozen lock `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变，已读当前 UI 指南 v0.2。本任务不涉及中央公共 Contract；不改变标准解释、来源资格、Calculator、Canonical 或 Record，无新增 Standard Issue。
