# PR64 呈现收口：CI旧文案断言已修，待新head验证与窗口验收

2026-11-10。分支 `codex/ui-guideline-closeout`，起点为已合并PR62的 `origin/main@224442530fcc61d8224c45e486688b2c27ec9324`。已核验canonical origin、fetch、默认main及工作区，独立worktree保留原用户未跟踪文件。无Goal；已由父代理push初始head `55ceff05cd76c672fe0fe40cbb691879db438a76` 并建立 [PR64](https://github.com/adgo07/GHGTOOL/pull/64)，未合并/发布。本次仅同PR测试断言及证据同步，不改产品/UI/CI配置。

完成5个UI生产文件的呈现增量：可选页头、40DIP/2DIP焦点的可访问ⓘ；首页及记录区分空态/读取失败并提供真实动作；标准支持词与通则角色分离；只读库、设置说明渐进展示；导入只删重复页头；新建3处纯文案明确生成记录。不改Calculator/标准解释/正式结果/DB/Canonical/模板/Word或Frozen lock。

本地已有回归按批28/28与18/18通过（重叠不累计）；标准/记录/设置24例原1旧列宽断言已在18例中精确修复复验。目录/pilot补查22例原1旧列宽断言失败，修后pilot6/6；新增最终copy5/5。父代理独立较早25/25，最终copy+settings9/9（重叠，不算34唯一用例）。全部命令/数量/失败和未执行项见[实施报告](IMPLEMENTATION_REPORT.md)。8张1280×800/DPR1 Qt离屏图及源码hash见[证据](docs/ui/guideline-closeout/README.md)。

父代理代码与范围内本地Qt独立检查已通过；原生桌面因helper三次active request失败保持OPEN，不宣称EXE/全产品/正式发布验收。复杂核算灰底/原生SpinBox等未全面重做；通则独立支持等级与既有32151.5目录状态证据待核验。PR64首轮Actions已执行，真实失败见下；本次修复尚未push/CI/打包，未改CI预算/required。

PR63仍OPEN/未合并，head `f4ed05d3195ba5d5edfe4172e00dffbd96a691cf`，不自动合并。产品文件重叠仅carbon_material_page.py的3处文案（顶部按钮及两处hint）；后续逐处协调，勿覆盖其未合并布局。原有原生Office/IME/人工DPI/干净机/企业样例等Gate继续OPEN，标准仍非SUPPORTED。

PR64首轮Actions run42828012360/job129870308784：1138例1137通过/1失败，1615.429s，唯一失败为UIR04空态测试仍断言旧“点击计算排放量”提示。本次只将该文案断言改为批准的新“计算通过后自动新增正式记录。”，其他空区隐藏/状态/计数/入口断言保留；相同模块真实失败入口与相邻错误/成功状态3/3本地通过，17.797s，命令及原CI失败来源见实施报告。尚未复跑本地全量，不把GitHub结果写成本地执行。

用户要求窗口验收通过后合并。初次UIA合取捕获阻塞，经仅截图恢复，Astra窗口代理独占桌面进行原生验收中，尚无完整PASS，结论以父代理PR回执为准；新head required CI及精确包也待本次push后核实。交父代理审查本地修复提交并统一push；窗口/CI前置条件未满足前不得自动合并，不启动下一阶段。
