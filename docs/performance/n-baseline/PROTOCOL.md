# N 源码性能基线协议

对象：生产代码冻结在 `348077cd972a27b6eeb80b77b712e7cb35375988`。只新增测量脚本和本目录证据，不优化生产代码，不设未经批准的 SLA，不触发 GitHub Actions。

## 平台 / Contract 预检查

仓库 origin 已实际核对为 adgo07/GHGTOOL；分支 codex/b-closeout-n-baseline、上述 HEAD，初始工作区干净。主协调者已完成 fetch/默认分支核对并独占治理文件；测量者按分工不切分支、不 fetch、不提交。中央可信 clone 的 origin 已核对，Frozen 从 `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 读取 Architecture V2.1、Numeric Contract v1、Numeric Profiles v1；当前 ACTIVE GUIDE_INDEX/UI v0.2 从中央已合并 `c5fc6d438c9200060649e47c016b9b48218de72c` 读取。保持分层、共享 Canonical/Application、声明 Profile 一致、ambient 独立、full-value exact 和不可变 Record；计时仅为遥测，不回流业务数值。项目 p40/HALF_UP 是 ALLOWED PROJECT DIFFERENCE，不是平台默认。不改 Frozen、标准解释、公式、Profile、支持状态或数据库 Schema；无 Contract 冲突、无需修改中央。相关既有 Standard Issue 为016（软件补充）；本包不改变其软件解释，已知焓场景不执行017物性路径。

## 环境与样本

Windows x64 / CPython 3.12，沿用已安装依赖，不安装新包。Qt `offscreen`；环境实际版本、CPU、OS记录在 raw.json，不公开用户名、主机名或内部绝对路径。单一测量者串行执行，主协调者不同时跑测试、build或其他 benchmark。无法保证其他系统进程、频率、温控或杀毒负载恒定，未清磁盘 cache。

复用 `tests/benchmark_navigation.py:make_record` 建立200条轻量合成导航 Record，其手造结果只用于列表规模，绝不当作正式计算样本。独立临时 records/projects/catalog SQLite，20个合成项目；每个启动进程从同一 seed 复制数据库。业务阶段将其中一个项目保存为1个完整Canonical单元，不增项目数量。全部文件仅在 `tmp/n-baseline`，不读写用户数据库或参考工作簿。

业务工作簿从现有v11/2.9.0受控模板创建临时副本：B.9外购饱和蒸汽1t，独立已知焓2800kJ/kg，缺省热力因子、边界外；软件补充纳入20tCO₂。年度2026，合成企业。仅一个代表性场景，不覆盖IF97、全部排放源、企业大样本或极限规模，不是Golden或正式支持验收。

## 串行顺序与计时边界

各项1暖身+5实测，暖身单列且不进入统计。启动为6个全新独立源码进程，首个排除；fresh process不意味着磁盘冷cache。启动DB复制/seed构建均在计时外。

1. 启动：实际 `create_main_window`。分开记录子进程起点至创建返回（含业务导入、QApplication及SQLite Repository初始化）、同起点至show后首个queued callback被事件循环派发；另记父进程启动至子进程正常结束总时长。总时长含解释器启动/结果JSON写入/退出，是过程边界而非可见就绪。
2. 七页导航：完整窗口，程序化 `shell.navigate(route)` 至 `app.processEvents()` 返回，每次先导航到其他页。首样本含该页尚未加载时的构建成本；后五次反映缓存页。不是鼠标点击、可见首帧或人工响应时长。
3. Excel：实际 `ExcelImportPage.excel_adapter.import_preview`，包括工作簿读取、校验、共享预览；检验有效单元且零新增Record。
4. 项目打开：实际 `ExcelImportPage.open_project` +事件处理，包含SQLite读、Canonical恢复与预览呈现；校验恢复相同输入。项目选择之前的导航不计入。
5. 正式计算：实际 `CarbonAccountingUseCase(gui.calculator, records).calculate`，包括校验、Domain及不可变SQLite追加；每次成功写入新Record，六次共六条，绝不覆盖旧记录。计时不包含GUI点击/项目关联保存。
6. Word：同一已保存冻结Record经 `build_saved_record_report`→`render_report_docx`→`write_report_atomically`；包括读取冻结快照、模型、DOCX生成及独立目标文件保存。没有Calculator/Resolver调用；核对records.sqlite哈希不变。不包含人工补充/路径对话框、导出审计或原生Office打开。

计时用 `perf_counter_ns`，逐次整数纳秒原样保存，不预先四舍五入。统计median、nearest-rank p95（ceil(0.95*n)）、min、max；n=5时p95就是max，不能据此推断稳定尾延迟。RESULTS中的毫秒仅显示换算。每项失败数、验证条件及全局失败数记录；任何断言/子进程异常使运行失败，不把不完整结果当成功基线。失败的准备尝试须在RESULTS另列，不静默抹去。

测量前后对tracked生产路径apps/packages/resources/pyproject.toml/platform-lock.json逐文件摘要，并用git diff与冻结HEAD比较。该139文件摘要仅覆盖上述范围，不含data-source或tests；Canonical来源及复用fixture/benchmark是否未变由主协调者另行git diff核验，不由该摘要推断。其他治理文件由主协调者独占，不属于生产计时内容。本脚本拒绝不同HEAD或生产修改。重跑须使用新的临时运行目录，不能复用已经追加Record的seed。

## 执行与边界

从仓库根运行：`python -B -m scripts.measure_n_baseline`。设定 `QT_QPA_PLATFORM=offscreen`；PYTHONPATH提供当前依赖环境（不用机器绝对路径作为仓库身份）。实际解释器为CPython3.12.14 Windows x64，精确包版本见raw。脚本严格拒绝非348077cd972a27b6eeb80b77b712e7cb35375988的HEAD；本轮证据集成提交后，不能直接在新文档提交HEAD运行。复现须新建冻结348077c的隔离worktree，将本测量脚本复制到该树scripts/measure_n_baseline.py相对位置，并使用新的tmp/n-baseline临时目录（不得复用已追加记录的旧临时数据库），再按上述命令执行。

本地源码证据不等于GitHub Actions、不等于旧CI288/head2db制品、更不等于merge348精确EXE。原生Office、真实鼠标/IME/人工DPI、企业实样、干净目标机、Release、RS04/RS05仍OPEN。历史测量包1724已获源独立验收，记录见ACCEPTANCE.md；2026-10-21用户另授权收尾PR/源合并及合并后N新包，不改变本协议原测量事实，不宣布正式支持。

当前脚本采用text eol=lf。历史执行副本CRLF SHA与LF规范化SHA在SCRIPT_NORMALIZATION.json分列，仅换行不同；raw字节不变，没有重测。新增N序列应另存，先按HANDOFF定位与控制测量边界，不覆盖本基线。
