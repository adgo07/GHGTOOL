# 新建核算整页 V2 独立验收

受验提交：53a3ae83256aeb6ee8b95f426fb6d7297493b65c。结论：本地 UI 实施范围 PASS；不代表 CI、实包或原生交付验证通过。

源会话独立核对 origin、HEAD、干净工作区、差异范围与 git diff --check。变更限 UI、捕获脚本、测试与交接证据。7 个 UI 源文件及捕获脚本哈希与最终截图摘要一致。按登记的最后 8 行补丁反向重建 page，所得 SHA256 与 151 项测试身份记录完全一致。

源会话独立运行：python -B -m unittest tests.test_accounting_source_directory -v；13/13 OK，80.675 秒，Qt offscreen。覆盖八目录切换与完整输入保留、四态启用与键盘、来源草稿、响应式几何稳定性、热力只读预览、隐藏字段错误定位展开。执行方 151 项日志通过；最后 13 项与其中 12 项重叠，不累加。源会话未重跑 151 或完整 discover。

astra medium 最终截图视觉复核 PASS；42 张图，hover 为焦点+悬停组合态。原生鼠标、IME、系统 DPI、Office、企业样例、实包、CI 未执行。未 push、未建 PR、未合并。

平台/Contract：locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20 未改；本任务不涉及中央公共 Contract。未改变既有标准解释、计算公式或历史 Record。既有 Issue004/016/018、017、020 边界保持。
