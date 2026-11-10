# 中央 UI 指南呈现收口：证据

2026-11-10；基于已合并 PR62。初始head `55ceff0` 的8张原尺寸 Qt **离屏**图在 [offscreen](offscreen)，1280×800 / DPR1，源码及图片校验见 [capture-manifest.json](capture-manifest.json)。使用独立合成数据，设置路径 `C:\GHGTOOL-QA\exports` 仅为虚构展示值，没有写入真实用户设置或创建该导出目录。首页保留的示例记录是旧快照回退样本。

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


## 原生小屏FAIL与局部修复

父代理/Astra实际原生验收在整窗961×631（约960×600客户区）发现标准名称列被Stretch压至约40DIP，表头不全、每字一行，首行约238高：[修复前截图](native/standards-small-before.jpg)。这是确定FAIL，初始8张宽屏离屏图未覆盖此问题；不得继续用它们证明小屏PASS。

仅标准库专属表在剩余空间不足240DIP时固定名称列240、表内横滚；足够时恢复Stretch。未改其余四列/global header minimum或页面宽度。真实Qt新增960→1440→960回归验证名称≥240且首行≤120、表头文字空间、支持列160/横滚可达、页面无横滚、编号/名称点击、详情返回和筛选保留。作者最终补强单例1/1（0.475s）；父代理独立pilot7+已有resize视觉1共8/8（1.624s）。源码后续差异hash单列于manifest，原图hash和初始来源保留。

指定Astra实际原生操作、父代理独立看图确认：961×631整窗名称正常换行，表内横滚可到软件支持并拖回编号，名称/编号进详情与返回正常；最大化1280×672名称伸展且底部无横滚，再恢复961×631换行正常且表内横滚恢复。原小窗布局FAIL关闭，范围内布局复验PASS。

持久证据：[小窗名称](native/standards-small-after.jpg)、[横滚到软件支持](native/standards-small-support.jpg)、[宽窗恢复](native/standards-wide-restored.jpg)、[再次小窗](native/standards-small-restored.jpg)。未经本作者另行桌面操作，实际执行来源为父代理/Astra回执。

**字体清晰度仍OPEN，待用户肉眼答复；以上不是整体原生全PASS或正式发布验收。**
