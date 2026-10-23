## PR57 构建可追溯性收口（2026-10-23）

CI297 对 c6edb51 的工程候选已核验通过，回执见 docs/ci/CI297_SUMMARY.json：实际下载并保全的 ZIP 与 Actions artifact 12361586214 摘要一致，319 文件集合、318 逐文件大小/hash、三项提交身份核对通过；包内 Qt6Core 文件版本 6.11.2.0。PNG/SVG 解码、两次隔离启动来自该 CI 日志，本地未执行 EXE。旧 CI296 原包继续 HOLD，不覆盖历史证据。

本次新增 build_environment：从实际构建进程采集 Python 完整 patch、PySide6/Essentials/Addons、Qt、shiboken6、PyInstaller、hooks 及系统/位数，按既有 requirements-build 固定组合检查；审计拒绝缺项和版本漂移。Python 仍允许 3.12 的不同 patch，完整身份记录但不冒称性能环境相同。图像诊断改为显式 --probe-images 输出路径，环境变量不再切换生产入口。业务树、四行 UI、模板、公式、历史 Record 和性能 raw 不变。

本任务不涉及中央公共 Contract；platform-lock 的 ee5feb0cc34dbd99790500fadd0c4c932e202a20 不变，无标准解释变化。当前修补的 CI 与实包待新提交验证，CI297 不背书本次代码；不重复性能测量、不宣称首开达标。原生 Office/鼠标/IME/DPI、企业样例、干净机、完整许可履约、Release、RS04–05 继续 OPEN，不自动合并。

---

以下为此前实施记录；其中待 CI297/新包核验的状态已由上述回执取代。

# 最后一次有限性能收口与工程候选交付报告

2026-10-21；生产提交58e788be36dc0d3263c48e59e5d464c2549139b5，最终送验head以本PR回执为准。PR56已源独立PASS、CI294 success并合并59cab091aab0df44b147f2bba3b960085dbae168，本轮从实际fetch的该main创建新隔离树。origin确认为adgo07/GHGTOOL，默认main，初态干净；根用户脏工作簿/资料及全部旧工作树和原始证据未修改。

## 平台 / Contract 预检查

实际读取本仓AGENTS、唯一路线、TASK/HANDOFF、台账、platform-lock；可信中央clone实际origin=adgo07/Qingzhou-contracts。Frozen锁ee5feb0cc34dbd99790500fadd0c4c932e202a20保持不变，Architecture V2.1按锁读取，ACTIVE UI v0.2按正式已合并适用版本另读，二者不混为Frozen。适用MUST：Presentation/Application/Domain隔离、共用业务真值、声明Profile/ambient独立/full-value比较、不变Record及冻结Word；MUST NOT：遥测回流、跳刷新/资格/验证、丢草稿、历史重算、公式/算法身份/数据库/模板/标准范围或Frozen升级。Carbon p40/HALF_UP为ALLOWED PROJECT DIFFERENCE，不是平台默认。本任务不涉及中央公共Contract变更，无新增冲突/中央缺口；沿用Issue016/017/018/020，不改变任何软件解释。

## 授权、分工与实际改动

源转达用户“进行收口并交付”，本轮限于已有热点的一轮最小可逆收口和工程候选准备；原生操作禁令继续。root为唯一生产作者/测量者；gpt-6.1-sol/medium静态代理只写docs/DELIVERY.md，没有测试/build/GUI/测量或其他文件写入。root复核其diff、真实v11哈希及样例锚点。新树与根用户文件隔离，未付费/改仓库可见性/购买服务。

业务/UI生产改动仅四行（后续构建交付修复另列）：来源卡片、统一能源卡片/能源行、过程行在最终布局parentWidget下创建。既有分项中来源卡片/子树构造为热点；本改动避免填充后插入时再换父，不改变样式应用时点或任何业务语句。未减少控件/内容/输入、未lazy/缓存、未跳资格/刷新/校验/持久化。Application/Domain/Resolver/Numeric/Record/Word/codec/数据库/模板/规则版本、中央锁与旧N数据零diff。无新增依赖、框架、产品阶段或第二路线。

## 有限候选与正式证据

只试一个四行候选，诊断ABBA2对/4新进程用于筛选，不混入正式结果。之后实际未改/候选各做三尺寸30像素和initial/all_sources_enabled两套完整规范化form、命名控件、dirty比较，全部逐项相同，0Qt回调错误。完整原始proof/PNG留在本轮tmp目录，仓内SNAPSHOT_PROOF包含摘要、原始proof SHA与30个图像哈希。离屏像素不是原生截图或人工DPI验收。

独立正式ABBA20对/40新进程：相同未改worker SHA7ad87b464e8e27fa882cd3b8409222dafcb5fa36e1612c52468357579f684dd5、同200合成Record/20项目三库字节、机器/依赖路径/窗口与动作；偶数对old/final、奇数对final/old，每进程首开后两次缓存返回。两策略同样AST提取/compile与包装，只有四处parent不同；最终四方法全文哈希与实际生产一致。所有跟踪方法调用次数逐对相同（含查询/Resolver/刷新），3409控件/10卡片/54字段/444初态keys及dirty一致，0进程/Qt回调失败。采样与回归/build严格串行，未控制其他用户进程或电源/cache。

| 首开统计（ms） | 基线parent | 最终parent |
|---|---:|---:|
| n | 20 | 20 |
| median | 3139.477 | 2946.261 |
| nearest-rank p95 | 6145.271 | 4555.587 |
| min / max | 2629.599 / 8356.523 | 2322.481 / 6836.219 |

配对中位降412.398ms/14.7399%，16/20对更快；聚合median仅约6.15%，两种统计分开。4个不利对及全部分项保留（最不利候选慢3759.257ms；统一能源/末尾样式分项中位也变慢）。来源卡片inclusive中位1608.661→1367.320ms，嵌套分项不可相加。首开仍需数秒且有明显波动；不宣称稳定尾延迟、SLA、冷磁盘cache或原生首帧。缓存返回与首开分列，详见RESULTS/COMPARISON及raw。

采样HEAD仍基线59cab091，四行在工作区；raw记录完整production_diff及生产字节SHA9b8a65a149e8c29438dd3de57a03f8800ebefc55f3afcc50a335f2775b6046df，后续生产提交另列，未把基线冒称含改动提交。诊断脚本在正式前增加生产身份字段，两批control SHA各自保留。旧PR56样本和本轮诊断/正式均不混合、不覆盖。

控制脚本采样字节含末尾一个CRLF；提交核对发现全局LF规则会改变SHA，因此只对此计时脚本路径设-text/CR-at-EOL，保留实际采样字节并核提交SHA，未重采或改生产。其他Python规则不变。

**性能工作到此结束，不再追加候选或循环优化。**

## 本地验证（采样结束后执行）

实际Python3.12.14，PySide6/Qt/shiboken6 6.11.2、openpyxl3.1.5、python-docx1.2.0、lxml6.1.3、CoolProp8.0.0、NumPy2.3.3，QT_QPA_PLATFORM=offscreen；测试临时目录独立。

| 命令（均python -B -m unittest … -v） | 数量 / 秒 | 结果 |
|---|---|---|
| tests.test_standard_dispatch tests.test_g03_shell tests.test_uat02_geometry tests.test_uir02_source_cards tests.test_navigation_background | 37 / 57.488 | OK |
| tests.test_accounting_projects_ui tests.test_uat02_usability tests.test_p3_ab_standards tests.test_record_summaries | 43 / 187.071 | OK |
| tests.test_b_heat_chain tests.test_b_external_excel tests.test_b_external_chain tests.test_g08_delivery | 34 / 97.687 | OK |

合计114不同用例，0失败/错误/跳过；已解析日志确认无重复ID。覆盖与本四处UI构造有关的动态新增、草稿/项目恢复、开关、参数来源、热力/表格/冻结Word和G08，未本地重跑未变旧Domain专项或全量。`python -B scripts/validate_canonical.py`有效9 standards/12 sources/102 parameters/138 factors；`python -B -m py_compile packages/ui/carbon_material_page.py scripts/profile_n_final_closeout.py scripts/summarize_n_final_closeout.py`与diff检查通过。原始本地测试日志在本轮tmp目录；数量/版本见VALIDATION.json。

## 工程候选与交付出口

当前始终保持一个PR57；原计划一轮CI296已完成，实包核验发现下述构建缺陷后，用户授权最小修复及一次新精确head CI；本地未做全量或standalone build，不把CI写成本地结果，不复用旧CI294。最终head、tested merge、真实G08/全量数量与制品审计/启动统计以本PR回执补充；不为CI后纯状态再push重跑。

本轮会在获准工作空间新建独立交付目录，保存该精确head实际Actions ZIP、原样manifest、ZIP/manifest及逐文件hash/size、provenance、原始CI日志与凭据、受控模板和合成验证输入/独立算式/简明说明；不覆盖用户文件或把7天Actions链接当永久保全。只有实际下载、完整文件集合/逐文件摘要及受控资源审计通过，才在最终交付凭据写“已保全”。该凭据与PR说明记录最终真实路径、摘要与数量，源码报告此处不是预填成功。

DELIVERY复用现有流程，补了购热0.308与独立补充20.308的合成样例、空白/真0/拒绝区别、旧R2历史样例边界、本地ZIP保全与证据索引。静态核v11/2.9.0实际SHA b1e843a1eb8980c5a9bf4ee11d5b2369abcb89ebf4ca5b8659d8cccaefd166c4、固定依赖及蒸汽13份许可原文+来源清单14文件；最终包仍须按实际manifest核对，不据此声称全产品许可已履约。

## 未执行与已知限制

无原生桌面/CU/替代控制、原生Excel/WPS/Word、鼠标/IME/人工DPI、Windows10/11干净机或真实企业资料验证；合成样例不是企业验收，离屏测试不替代上述门禁。无商业许可采购/法律放行/代码签名/安装器/商业Release，不宣布完整SUPPORTED，不自动进入RS04/05或下一标准。当前交付是可追溯工程候选；正式交付清单门禁OPEN。源负责独立验收，新PR不自动合并。

## CI296实包核验、HOLD及已授权最小构建修复

CI296 run39624195759：merge job119305201523测试c71fc4348bd1841f0458a7d988d8aaa49b7321a1，1040/1260.347s/OK；exact-head job119317483271，18/9.434s/OK、审计322/归档323/来源与两启动成功。原artifact12358366858，75,751,742 bytes，ZIP SHA256 b92384e4456aecaad0dc781a6910373c1c6b9f3a44477a044b58bba025c506c8，原manifest56,914 bytes SHA a51e986f1c8f8d9e3d22076c243fce6ff2879b46589bb0e80048b9e6d6058158。已本地实际保全，323路径无重复/越界，322逐文件大小/hash、manifest副本及source/pr_head=fcc69c1、testedmerge=c71fc434全部核对。此为旧候选真实证据，未删改/重封装，不冒作修复后包。

新发现：CI安装日志/实包静态PE版本为PySide6/Qt6.12.0、Python3.12.10；本地正式计时/114回归是Qt6.11.2、Python3.12.14，不外推本地数字到实包。实包Qt6Pdf.dll来自官方PyPI PySide6_Pdf6.12.0.140 Windows wheel（wheel SHA4971ba1a0ca15e7c29cfd808e9600aeb46b2305dad01456eb09fa3197166268e），DLL4,623,672 bytes SHA5caf5744e017df85455c5c7e11028c5ec2765633a7ca64a11d7b64d127f6c4cc逐字节相等。METADATA提供LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only，不能说GPL-only；wheel只附Commercial引用文本，不代表全部LGPL/PDFium等第三方履约已完成。[官方wheel元数据](https://pypi.org/pypi/PySide6_Pdf/6.12.0.140/json)及[Qt PDF官方许可说明](https://doc.qt.io/qt-6/qtpdf-licensing.html)保留；后者当前重定向6.140文档快照，不能替代该wheel材料。

PE静态扫描149个可执行格式文件无解析失败，唯一直接import Qt6Pdf.dll的文件为PySide6/plugins/imageformats/qpdf.dll；apps/packages无QtPdf/QPdf/PDF图像消费者，QPixmap只用品牌PNG/图标SVG。文件存在、PE导入关系不等于已测运行时加载情况；没有运行本地候选EXE/PYZ或原生控制。交付立即HOLD，源暂不最终签PASS。

根因：pyproject允许PySide6>=6.8,<7和PyInstaller宽范围，而CI两个job只pip install -e .[build]，未消费已有requirements-build.txt，导致Qt6.12/hooks2026.9等漂移。用户通过源明确授权最小构建修复：CI/交付安装先-r现有固定约束，再--no-build-isolation -c同文件安装editable，固定已验证Qt/PySide/shiboken/Essentials/Addons6.11.2与hooks2026.8，复用已有固定setuptools；不改变普通源码开发支持范围或强行对齐Pythonpatch。仅从新产物排除未消费qpdf插件及root/nested Qt6Pdf.dll，逐路径软链/越界守卫复用既有机制；audit以包范围拒绝残留，不作GPL-only断言。不删除源材料、历史包或其他Qt库。

新增仅工程probe：standalone entry在专用测试环境变量下离屏解码真实PNG/SVG、写新临时proof后退出；普通入口仍main、不进入新产品流程。smoke先核该实际包probe，再原两次隔离启动，确保排除不破坏产品图像。新增G08四项覆盖排除/保留范围、路径安全、资源守卫和真实图像解码。修复后本地命令python -B -m unittest tests.test_g08_delivery -v：22 tests/18.688s/OK，0失败/错误/跳过（18重跑+4新项，不能与原114直接加总当新head全量）。之后仅一次必要新精确CI/原ZIP保全到新目录；HOLD在实际新包及源验收前保留。移除未用组件不是商业法律放行，其他许可/第三方通知、原生/企业/正式Release门禁仍OPEN。

本次本地验证：QT_QPA_PLATFORM=offscreen；python -B -m unittest tests.test_build_environment tests.test_g08_delivery -v，26项/37.703s，0失败/错误/跳过。构建环境为Python3.12.14、Qt/PySide6/shiboken6 6.11.2、PyInstaller6.22.3、hooks2026.8。未本地全量、未本地构建或执行EXE；新CI独立补证。
