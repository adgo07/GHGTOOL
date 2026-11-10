# 中央 UI 指南呈现收口：证据

2026-11-10；基于已合并 PR62。8 张原尺寸 Qt **离屏**图在 [offscreen](offscreen)，1280×800 / DPR1，源码及图片校验见 [capture-manifest.json](capture-manifest.json)。使用独立合成数据，设置路径 `C:\GHGTOOL-QA\exports` 仅为虚构展示值，没有写入真实用户设置或创建该导出目录。首页保留的示例记录是旧快照回退样本。

复现：从仓库根，设置 `QT_QPA_PLATFORM=offscreen`、TEMP/TMP 到本仓已存在且可写的隔离临时目录，再运行 `python -B docs/ui/guideline-closeout/capture_offscreen.py --data-dir tmp/capture-data --capture-dir tmp/capture-review`。脚本不写正式用户库。此次实际执行的相同脚本先放在 `tmp/capture_copy_ui.py`，最终副本与其逐字节一致。

| 图 | 本轮观察 |
|---|---|
| home | 原五入口顺序、首页独立设置；项目空态一句+新建核算 |
| standards | 五列、单状态筛选、支持文案完整；通则角色与支持分开 |
| standard-detail | 三连续分区；通则不独立核算、软件说明限定直接可见 |
| record-detail | 原冻结值与旧记录回退提示，两页签；Word动作改名 |
| factors | 只读与来源浏览；数据值、单位和当前表注保留 |
| settings | 真实能力；说明与技术信息进ⓘ；标题同行，无真实用户路径 |
| new-accounting | 保留复杂表单与原默认值；顶部计算按钮明示生成记录 |
| import | 保留四区、必需上下文及正式计算顺序 |

作者已逐张查看以上8图；父代理已独立查看代表图。截图不是原生鼠标/IME/Office/高DPI/EXE验收。ⓘ鼠标、键盘打开，Escape/关闭说明及焦点恢复由真实 Qt 离屏交互用例验证。

指定 Astra medium 桌面代理读完 computer-use 及必要文档后尝试启动隔离源码；`sky.list_apps()` 两次及重置后的第三次都返回 `Computer Use helper already has an active request`，未取得窗口/截图，停止输入。其启动 PID11652 后续精确查询未发现，无其他进程被终止。**原生桌面 OPEN**。

已知保留：标准32151.5目录行实施日期为2026-10-01，截图仍标“即将实施”；属既有目录状态证据待核验，不在此次呈现工作中按系统时钟改源数据，不宣称全标准生命周期核验通过。
