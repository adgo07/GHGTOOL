## PR57 构建可追溯性收口（2026-10-23）

CI297 对 c6edb51 的工程候选已核验通过，回执见 docs/ci/CI297_SUMMARY.json：实际下载并保全的 ZIP 与 Actions artifact 12361586214 摘要一致，319 文件集合、318 逐文件大小/hash、三项提交身份核对通过；包内 Qt6Core 文件版本 6.11.2.0。PNG/SVG 解码、两次隔离启动来自该 CI 日志，本地未执行 EXE。旧 CI296 原包继续 HOLD，不覆盖历史证据。

本次新增 build_environment：从实际构建进程采集 Python 完整 patch、PySide6/Essentials/Addons、Qt、shiboken6、PyInstaller、hooks 及系统/位数，按既有 requirements-build 固定组合检查；审计拒绝缺项和版本漂移。Python 仍允许 3.12 的不同 patch，完整身份记录但不冒称性能环境相同。图像诊断改为显式 --probe-images 输出路径，环境变量不再切换生产入口。业务树、四行 UI、模板、公式、历史 Record 和性能 raw 不变。

本任务不涉及中央公共 Contract；platform-lock 的 ee5feb0cc34dbd99790500fadd0c4c932e202a20 不变，无标准解释变化。当前修补的 CI 与实包待新提交验证，CI297 不背书本次代码；不重复性能测量、不宣称首开达标。原生 Office/鼠标/IME/DPI、企业样例、干净机、完整许可履约、Release、RS04–05 继续 OPEN，不自动合并。

---

以下为此前实施记录；其中待 CI297/新包核验的状态已由上述回执取代。

# 最后一轮有限性能收口与工程候选交付

2026-10-21：源已独立PASS并按用户授权合并PR56，实际fetch main为59cab091aab0df44b147f2bba3b960085dbae168。本轮新隔离分支codex/n-final-closeout，根用户脏文件和所有历史原始证据保留。root唯一生产作者/测量者；gpt-6.1-sol/medium静态代理仅写docs/DELIVERY.md，已完成，无测试/build/GUI/采样。

## 平台 / Contract 预检查

本轮读实际AGENTS/唯一路线/TASK/HANDOFF/台账与platform-lock；可信中央origin已核。中央Frozen锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，Architecture2.1按锁，ACTIVE UI v0.2按正式已合并版本读取。本任务不涉及中央公共Contract变更；保持分层、同Application/Calculator与Profile/ambient/exact比较、不可变Record/冻结Word，不改公式/资格/数据库/模板/算法身份/标准解释或SUPPORTED。遥测不回流业务，不跳刷新/校验、不减草稿、不加缓存/lazy。沿用Issue016/017/018/020，无新增解释或中央缺口；Carbon p40/HALF_UP仍为允许项目差异。

## 有限收口断点

生产提交58e788be36dc0d3263c48e59e5d464c2549139b5：仅四处parent参数（来源卡片、统一能源卡片/行、过程行）直接使用最终layout.parentWidget，避免填充后再换父；不移样式时点、不减控件、不缓存/lazy。实际前后离屏三尺寸30像素、两完整form/命名控件/dirty状态完全相同，0Qt回调错。

独立正式ABBA20对/40新进程（40首开/80缓存返回），0进程/Qt失败，所有跟踪方法调用次数含查询/Resolver/刷新逐对一致。首开median3139.477→2946.261ms（聚合约6.15%），配对中位降412.398ms/14.7399%、16/20更快；4对更慢（最不利+3759.257ms），p956145.271→4555.587ms，候选max6836.219ms，不能宣称SLA。诊断与正式独立，旧N raw不改；采样时HEAD仍基线、四行工作区diff和production SHA另存，未把基线冒称含改动提交。原始值/分项/反例/环境/字节身份见docs/performance/n-final-closeout。

性能优化到此结束，不追加候选。采样结束后串行本地37/57.488s+43/187.071s+34/97.687s=114不同测试通过，0失败/错误/跳过，覆盖UI/草稿/项目、动态行、能源消费者和G08。规范数据9标准/12来源/102参数/138因子有效，修改脚本/生产文件编译与diff检查通过。未本地全量/build；新PR正常CI及实际候选保全结果以该head回执/交付凭据补充，不复用旧CI294。

## 交付边界

用户授权“收口并交付”本轮落实为可追溯工程候选：稳定后一个PR正常CI，源独立验收，不自动合并；下载实际精确代码head的ZIP至新建获准交付目录，保留ZIP/manifest/provenance/摘要/日志并核文件集合和逐文件hash。短期Actions链接不作为永久保全。无原生桌面/CU/Office/IME/人工DPI/干净机、无企业真实数据、无付费服务或商业Release，不进RS04/05/第二标准，不宣布完整SUPPORTED。上述正式产品门禁继续OPEN。

## 工程候选实包发现与已授权最小构建修复

CI296（PR57 fcc69c1）完整1040/1260.347s、G08 18/9.434s、构建/审计/2启动成功；原ZIP75,751,742 bytes与API/upload/local SHA b92384e4456aecaad0dc781a6910373c1c6b9f3a44477a044b58bba025c506c8相同，323路径/322逐文件hash/manifest三提交身份通过。但实包Qt/PySide6为6.12.0、Python3.12.10，与本地性能Qt6.11.2/Python3.12.14不同，并含未消费qpdf图像插件/Qt6Pdf.dll；交付HOLD，不外推本地性能。

静态原始材料证明该Qt6Pdf.dll来自官方PySide6_Pdf6.12.0.140 Windows wheel，字节相等；其METADATA提供LGPLv3/GPL选项，不是GPL-only结论。PE静态唯一直接导入者为qpdf.dll，产品只读品牌PNG/图标SVG，无PDF图像消费；未加载候选DLL/EXE验证运行依赖。完整许可/第三方履约仍OPEN。

根因是CI只安装pyproject宽范围，未消费已有requirements-build固定约束。源已转达用户授权同包最小修复：CI/交付安装统一-r/-c既有约束并复用已装固定build backend；按既有安全机制只从新构建产物排除未用qpdf插件及Qt6Pdf依赖；audit守卫、隔离PNG/SVG probe和必要G08测试。pyproject支持范围、Pythonpatch、业务/模板/性能均不改。修复后本地G08 22/18.688s OK（含18重跑+4新项，不与先前114混加），0失败/错误/跳过。保留PR57、CI296原包/HOLD；新精确head正常CI与新独立目录通过前不解除HOLD，不自动合并或商业放行。

本次本地验证：QT_QPA_PLATFORM=offscreen；python -B -m unittest tests.test_build_environment tests.test_g08_delivery -v，26项/37.703s，0失败/错误/跳过。构建环境为Python3.12.14、Qt/PySide6/shiboken6 6.11.2、PyInstaller6.22.3、hooks2026.8。未本地全量、未本地构建或执行EXE；新CI独立补证。
