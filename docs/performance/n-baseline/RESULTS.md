# N 源码性能基线结果

冻结生产HEAD：`348077cd972a27b6eeb80b77b712e7cb35375988`。本地执行完成，14项指标均有1次暖身及5次成功实测，计时失败0；没有生产代码改动或性能优化。受验1724已由源独立验收PASS（见[ACCEPTANCE.md](ACCEPTANCE.md)），本次收尾增量另核；不构成正式支持、Release或人工桌面验收。

测量时间：2026-10-20T15:00:32.429415+00:00 至 2026-10-20T15:02:35.953643+00:00（UTC）；Asia/Shanghai本地时间为2026-10-20 23:00:32–23:02:35（UTC+08）。原始UTC值保持不变。顺序和完整边界见[PROTOCOL.md](PROTOCOL.md)，未四舍五入整数纳秒见[raw.json](raw.json)。

| 指标 | median ms | p95 ms | min ms | max ms | 暖身 ms | 失败 |
|---|---:|---:|---:|---:|---:|---:|
| 启动：独立进程全程 | 1066.566 | 1647.194 | 1028.569 | 1647.194 | 17761.718 | 0 |
| 启动：创建返回 | 810.382 | 1246.521 | 782.414 | 1246.521 | 15669.979 | 0 |
| 启动：事件循环就绪 | 819.640 | 1259.835 | 791.737 | 1259.835 | 16236.252 | 0 |
| 导航：首页 | 58.547 | 60.718 | 55.609 | 60.718 | 60.468 | 0 |
| 导航：标准库 | 45.925 | 50.829 | 45.241 | 50.829 | 48.755 | 0 |
| 导航：新建核算 | 910.311 | 949.111 | 875.310 | 949.111 | 14543.466 | 0 |
| 导航：表格导入 | 866.606 | 871.283 | 855.330 | 871.283 | 1770.918 | 0 |
| 导航：核算记录 | 1069.087 | 1087.679 | 1044.582 | 1087.679 | 2415.227 | 0 |
| 导航：参数因子 | 1097.749 | 1102.733 | 1060.544 | 1102.733 | 1691.093 | 0 |
| 导航：设置 | 1097.762 | 1230.148 | 1060.565 | 1230.148 | 1133.739 | 0 |
| Excel读取/校验/预览 | 502.906 | 539.980 | 482.108 | 539.980 | 540.200 | 0 |
| Canonical项目打开 | 54.643 | 62.019 | 53.810 | 62.019 | 56.515 | 0 |
| 正式Application核算及追加Record | 65.610 | 68.114 | 65.089 | 68.114 | 64.841 | 0 |
| 冻结Record→Word模型/生成/保存 | 644.119 | 725.104 | 626.623 | 725.104 | 1112.841 | 0 |

p95使用nearest-rank；n=5时等于最大值，样本不足以支持稳定尾延迟结论。启动三个指标来自同一组进程，并非三个独立启动实验。导航前先离开目标页，统计列为缓存页返回；暖身包含首次尚未加载页面的构建成本（首页/标准库此前已进入，不称冷页）。

观察：新建核算首次采样14.543s，缓存返回median0.910s；表格导入/记录/参数因子/设置缓存导航约0.867–1.098s，而首页/标准库约0.046–0.059s。它们包含整个Qt事件泵处理，本包没有剖析瓶颈或判定SLA达标。首个fresh进程暖身全程17.762s，之后5次全程1.029–1.647s；未清磁盘cache，不能把差异解释为纯启动优化或稳定冷启动。

## 规模、验证和执行证据

- 200条轻量合成导航Record、20项目；1个Canonical业务单元。工作簿28540字节，v11/2.9.0，已知焓外购热力+外部CO₂20，不覆盖IF97或全来源。合成列表Record只测导航，正式核算由真实Application/Calculator完成。
- Excel六次预览均有效，新增Record为0。正式核算六次（含暖身）追加6条不同Record，原ET为0.30800000tCO₂；不覆盖已有200条导航Record。
- 六份Word均42407字节，报告Schema3.1.0；实际读取同一正式Record冻结快照，生成并原子保存DOCX，前后records.sqlite哈希不变。不计人工对话框、导出审计或Office打开。
- 生产范围apps/packages/resources/pyproject.toml/platform-lock.json共139个tracked文件，前后与冻结HEAD的git diff均为空，路径和内容串联摘要均为`fb3b28cbb8b4435d12d8707d0d03ffcca02cf56d26bc5f9bfdb71ce7ee3a48e5`。该139文件摘要仅覆盖上述范围，不含data-source或tests；主协调者将另行git diff核验Canonical来源及复用fixture/benchmark未变。治理文档由主协调者独占更新，不参与生产摘要。
- 命令：从仓库根、既有依赖PYTHONPATH及QT_QPA_PLATFORM=offscreen环境，使用CPython3.12.14执行`python -B -m scripts.measure_n_baseline`，退出码0。局部日志与临时SQLite/合成xlsx/docx仅位于`tmp/n-baseline`，不作为公开用户数据上传。
- 一次非计时环境准备失败：首个PowerShell命令重定向到不存在的tmp父目录，Python尚未启动；创建目录后首次真实测量成功。此项不计入业务或计时失败。后续补充CPU友好型号/RAM的CIM查询因权限拒绝，未提权重复查询；原始环境保留实际platform.processor标识及12逻辑CPU，不假填内存/型号。
- 证据一致性检查：14项×5原始样本、暖身数量、median/p95/min/max、生产前后摘要及公开raw路径隐私检查通过。未执行全量测试、build或CI：此包只增加测量和证据，生产不变，且用户要求最少费用与无并发干扰。

## 环境

Windows 10 build19045 / AMD64；Python3.12.14；Qt/PySide6/shiboken6 6.11.2；openpyxl3.1.5；python-docx1.2.0；lxml6.1.3；CoolProp8.0.0；NumPy2.3.3。CPU标识`Intel64 Family 6 Model 165 Stepping 3, GenuineIntel`，12逻辑CPU。沿用现有依赖，没有安装/升级依赖。未声明固定电源计划、CPU频率或后台系统负载。

## 平台 / Contract 预检查及限制

Frozen中央锁`ee5feb0cc34dbd99790500fadd0c4c932e202a20`不变。已按该SHA读取Architecture V2.1、Numeric v1、Profiles v1，按当前中央已合并版读取ACTIVE UI v0.2；适用MUST/MUST NOT详见协议。无中央Contract修改/冲突，无标准解释变化；相关Issue016既有软件决定不变。项目Decimal40/HALF_UP与正式full-value exact保持，计时遥测不回流计算。

Qt offscreen只证明离屏程序化路径；fresh process不证明磁盘冷cache。此处为merge348源码，不能复用旧CI288/head2db制品称作精确merge348 EXE测量。原生Office回导、真实鼠标/IME/人工DPI、企业实样、干净目标机、商业许可履约、Release、RS04/RS05仍OPEN。没有SLA、优化前后比较或企业生产规模结论。

当次实际运行的执行副本SHA256（现场CRLF）：`f3c15fec984bda9924f80ec1668c1788587768df3d968cced4939b63111ad18d`。原始JSON SHA256：`ee02b8b7cb5ac4227f2afee5005aa1c90a7ab833c61c2c346fcc93425090edac`。

2026-10-21收尾：当前仓库LF文本脚本SHA256为`0b63b81142fcdca549c3017af3a94d0cf494eebc7cf0223e55dedbd14b8a2b0f`，与历史执行副本仅换行不同；证明见[SCRIPT_NORMALIZATION.json](SCRIPT_NORMALIZATION.json)。raw保留原字节/原SHA；此后未重新测量，不把LF规范化冒作新实验。原未push/CI描述属于2026-10-20测量阶段，当前源已push受验1724，新增收尾/PR检查另行记录。
