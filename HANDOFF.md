## PR57 构建可追溯性收口（2026-10-23）

### CI298 审计入口退修（2026-10-23）

CI298/run39921526799 的 merge-ref 全量成功，精确 head job120314607512 在独立 audit 步骤因 ModuleNotFoundError: scripts 失败；archive/provenance/smoke/upload 未执行，无制品，3f821a7 不放行。修复 inspect_release 的文件路径入口引导，与 build_standalone 相同；scripts 仍仅为仓库工具，不移入产品包。

本地命令：QT_QPA_PLATFORM=offscreen；python -B -m unittest tests.test_g08_delivery.G08DeliveryTests.test_uploaded_archive_preserves_manifest_file_set tests.test_build_environment -v，5项/3.355s OK，0失败/错误/跳过。新增真实子进程在非仓库 cwd、无 PYTHONPATH/PYTHONHOME、Python -I 隔离模式执行脚本：合法合成包 PASS；空目录正常 FAIL，无导入异常。首次测试发现夹具含归档排除的 .gitkeep，调整为实际上传集合后通过，未降低审计规则。

仅修入口及测试/工具约定，不改业务、manifest 版本约束或性能证据；待新精确 head CI 和实包，不用 CI297/298 替代。原生及商业交付门禁继续 OPEN，本轮无原生操作、不自动合并。

CI297 对 c6edb51 的工程候选已核验通过，回执见 docs/ci/CI297_SUMMARY.json：实际下载并保全的 ZIP 与 Actions artifact 12361586214 摘要一致，319 文件集合、318 逐文件大小/hash、三项提交身份核对通过；包内 Qt6Core 文件版本 6.11.2.0。PNG/SVG 解码、两次隔离启动来自该 CI 日志，本地未执行 EXE。旧 CI296 原包继续 HOLD，不覆盖历史证据。

本次新增 build_environment：从实际构建进程采集 Python 完整 patch、PySide6/Essentials/Addons、Qt、shiboken6、PyInstaller、hooks 及系统/位数，按既有 requirements-build 固定组合检查；审计拒绝缺项和版本漂移。Python 仍允许 3.12 的不同 patch，完整身份记录但不冒称性能环境相同。图像诊断改为显式 --probe-images 输出路径，环境变量不再切换生产入口。业务树、四行 UI、模板、公式、历史 Record 和性能 raw 不变。

本任务不涉及中央公共 Contract；platform-lock 的 ee5feb0cc34dbd99790500fadd0c4c932e202a20 不变，无标准解释变化。当前修补的 CI 与实包待新提交验证，CI297 不背书本次代码；不重复性能测量、不宣称首开达标。原生 Office/鼠标/IME/DPI、企业样例、干净机、完整许可履约、Release、RS04–05 继续 OPEN，不自动合并。

---

以下为此前实施记录；其中待 CI297/新包核验的状态已由上述回执取代。

# 有限收口与工程候选交付 — 实施交接

2026-10-21；当前唯一阶段路线仍为REFERENCE_STANDARD_ROADMAP.md。PR56已源PASS并合并59cab091aab0df44b147f2bba3b960085dbae168，CI294两个job成功（历史1040/18），不重做该包或重标其制品。

root负责四行最终容器候选、独立性能证据、必要回归、工程候选保全及TASK/HANDOFF/REPORT；并行sol/medium静态代理独占docs/DELIVERY.md，已完成，仅补可执行合成样例、独立预期来源和永久保全步骤。真实企业样例及原生操作继续OPEN。

先候选诊断，再实际生产30像素与两完整状态对照，再独立20对正式ABBA序列。计时同worker/同三库字节/同机器依赖/相同操作、首开与缓存返回分列；运行时两组仅四处构造父容器不同，同样编译/包装机制。诊断与正式不混合、不覆盖旧证据。Qt offscreen不冒称原生首帧，新进程不冒称冷磁盘cache；不以小样p95宣称SLA。正式采样和回归/build严格串行。

四行候选不减控件、内容、输入/草稿、参数资格、刷新或验证，不改业务方法。若证据不足就保留PR56现状并停止性能优化。平台锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；Architecture2.1与ACTIVE UI v0.2边界分别保留，本任务无中央Contract变更、无标准解释变化。

稳定后必要回归、本地小提交，一个新PR正常CI。下载该精确head实际Actions ZIP保全到新目录，核API/upload摘要、真实manifest三项SHA、全文件集合/大小/hash、受控模板与许可材料；不覆盖用户文件。最终说明提供已验证/未验证/已知限制及本地包位置，源独立验收，不自动合并。原生Office、鼠标/IME/DPI、企业完整性、干净机与全产品许可履约仍OPEN，交工程候选不称商业Release/完整SUPPORTED，不进入RS04/05。

## 稳定送验断点

唯一候选四行已形成生产提交58e788be36dc0d3263c48e59e5d464c2549139b5；不再扩展性能工作。实际30像素/两完整状态相等，正式20对/40进程和114不同本地回归通过，实际命令/数量/耗时、4个不利配对与环境限制见IMPLEMENTATION_REPORT及n-final-closeout/VALIDATION、COMPARISON。正式paired median14.7399%不等于聚合median6.15%，仍有数秒构造与大波动，不声称SLA。

本包只运行一次正常PR CI；最终精确head、tested merge、实际ZIP/manifest/逐文件hash及本地保全路径在PR回执、最终交付目录CI_RECEIPT/DELIVERY_RECEIPT和交付说明中登记，不为事后状态再推纯文档/重跑CI。源负责独立验收，新PR不自动合并。正式交付门禁OPEN与工程候选已交付必须分列。

## CI296后候选HOLD与最小构建修复

CI296成功和原ZIP完整性不撤销，但不背书后续head。实包Qt6.12/Python3.12.10与本地Qt6.11.2/Python3.12.14不同，且qpdf插件携带Qt6Pdf依赖；先HOLD并保全原包。准确官方wheel/许可选项/PE链与原ZIP身份见当前报告及交付evidence/license-review，不因DLL名字误判GPL-only。

源已授权原PR57内最小构建修复：CI及交付安装消费已有requirements-build约束，不扩大pyproject支持范围；新产物排除未消费qpdf/Qt6Pdf组件、审计拒绝残留，CI实际包增加隔离PNG/SVG解码probe后再原两次启动。无新性能候选或复测。已实际本地G08 22/18.688s OK；需一次新精确CI、重新下载新ZIP至新目录核manifest/逐文件hash和实际依赖，再源独立验收。旧296目录不覆盖，不以删DLL后的旧包冒充新包；全产品许可履约/原生/企业门禁继续OPEN。
