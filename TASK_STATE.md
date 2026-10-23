# PR58 中文弹窗退修（2026-10-23，验证中）

受验基线 `572f32ae0ca335a2ea329d7bd48e7c01d454abfc`：实际 CI301/run39932777629 全量 1056 项/1031.702s，2 failures，精确包 job skipped。确认是新模态测试在共享 QApplication 全量环境中的状态依赖；单模块通过不构成完整验收。此前 CI299 仅背书已合并 PR57，不背书 PR58。

## 修复

三个同步弹窗入口均在配置/exec/读取返回值外层使用 finally/deleteLater，返回值先取得，不使用 WA_DeleteOnClose，不引入管理器。真实 Qt 测试在新进程执行：回调绑定具体实例，先断言可见且为当前模态窗口，再操作，异常显式传回、子进程有超时；保留实际 exec、Esc/×/Enter/放弃与文本返回验证。新增同一父窗口反复取消三类弹窗及异常路径，处理 DeferredDelete 后对象数恢复基线。

截图脚本拒绝脏工作树；公共摘要仅记录中文资源相对路径、SHA 与加载结果，不公开本机路径。修复提交后在干净提交重采；证据提交与代码提交分别注明，不冒称截图生成于自身回执提交。QFileDialog 原生策略不变，本轮没有原生文件对话框或系统语言验收，后续仍须单列。

## 平台 / Contract 预检查

origin adgo07/GHGTOOL、原 PR58 分支及隔离工作树已核实并 fetch。Frozen baseline `ee5feb0cc34dbd99790500fadd0c4c932e202a20` 不变。本任务不涉及中央公共 Contract；无标准解释变化，无新增 Standard Issue。仅修 UI 生命周期、测试和证据，不改业务、Numeric、数据库、Record、模板、Word、首页布局。

## 验证

本地 Python 3.12.14 / Qt 6.11.2，QT_QPA_PLATFORM=offscreen：`python -B -m unittest tests.test_ui_chinese -v`，9/9，9.363s，0失败/错误/跳过。包含真实子进程反复弹窗与释放回归。

`python -B -m unittest discover -s tests -t . -v` 已启动，完成前不推送、不宣告最终 PASS。随后核查新 head CI 全量及精确包：审计/归档/provenance/中文和图像探针/启动/上传，以及实际下载的文件集合/hash/工具链。原 CI301 失败历史保留。

PR57 已合并 `8f9fa119`。PR58 未合并，PR-B 未开始。原生 Office、鼠标/IME/人工 DPI、企业样例、干净机、商业许可与正式发布仍 OPEN；本轮不操作桌面，不自动合并。
