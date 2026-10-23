# 仓库工具入口

`scripts/` 是仓库构建与验证工具，不纳入产品安装包的 package discovery。支持以文件路径直接执行的脚本，必须在导入 `scripts.*` 或本仓 `packages.*` 前，按自身 `__file__` 将仓库根加入 `sys.path`，不能依赖调用目录、editable 安装或外部 `PYTHONPATH`。对应测试应在无 `PYTHONPATH`、非仓库工作目录下执行真实子进程，并同时检查合法输入成功、非法输入正常审计失败。
