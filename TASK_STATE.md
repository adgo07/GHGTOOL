# 家族 UI 统一候选：待协调者独立验收

2026-10-28；Owner 本轮统一设计为实施依据。分支 `codex/ghg-family-ui-unify`，基线 `origin/main@6fc5909646b855494abee55cff6fd95f8d18b4be`。原 checkout 的用户修改未触碰；managed worktree 隔离实施。未创建 Goal、未建 PR、未自动合并。

已完成：共享控件样式合并；普通输入/按钮外框40 DIP、导航46 DIP；可见焦点与完整禁用态；正文1440不含外边距；窗口首次居中/恢复/掉屏约束（偏好写既有user.sqlite）；原图Logo按DPR重取与原生SVG；首页右上设置及入口上下文；表格最低44/默认48和长文换行；列表底部计数；页头actions槽；导入四区标题。

实际本地最终验证：Python 3.13.3 / PySide6 6.11.1，31项既有UI + 8项新UI + 1项正式记录保护，共40通过/0失败；compileall、diff --check、打包资源白名单检查通过。3.12.14虚拟环境虽存在，但该进程在本会话写临时目录被拒，8项初始化错误，不能宣称3.12测试通过。生产main在3.13的中文资源版本校验降级并等待提示，已停止，不能宣称完整生产启动通过。详见IMPLEMENTATION_REPORT。

四个代表视图和一个DPR2抽查已做离屏检查，不等于真实桌面验收。等待协调者用Astra串行检查生产入口及QA入口；EXE、CI、全量回归未执行。收到明确验收通过后才创建并attach PR。

本任务不涉及中央公共 Contract 语义修改；锁定central SHA仍为 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。中央UI设计候选 `e1486fb20c1dda33b7344ca860ff8f303c2183ee` 未声称已发布。无标准解释、标准支持范围、算法、Canonical、迁移、项目保存、正式Record或审计语义变化。先前PR60收口状态可从Git历史追溯，本轮不重新验收其全范围。
