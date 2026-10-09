# 当前任务状态

状态：IN_PROGRESS — GHG-EXB01 附录B正式Excel模板与输入
最后更新：2026-10-09

已确认 canonical origin 与最新 main，PR37已合并；从 main@708f78a455790946b4a728029bba768d8fb295fc 建立独立分支 codex/exb01-appendix-b-ingress。原checkout及用户修改/参考文件保留。

母版可访问，原SHA c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4。发现21个指定结果公式，按授权仅清理受控副本；新资源SHA e6a070bf28adb47939e24713f676136b5a023017d6f695e0031c68d51c389c3d。原文件未改。模板服务已实现精确字节复制；独立只读核对九表/布局/合并/验证/样式/其他值无差异。

R2专属生成/解析模块已删除，附录B整工作簿Adapter和OOXML词法读取已落盘，保留Canonical项目/Record闭环及旧EXCEL_R2证据。期间/地区/自定义燃料单位缺口不猜测；无法归组时定位单元格。Luna 6/max分担Importer、迁移测试与独立审查。补齐K1～K3已有正文核验绑定到正式Resolver的桥接，不改数值或公式。

已修复独立审查发现的项目上下文误导与资源打包边界：打开项目时锁定新导入字段并显示保存期间；Windows资源及setuptools数据精确文件清单。已有GUI五场景、125%/150%缩放通过；canonical校验、compileall、pip check通过。当前集中修正电力不同入口的单位表示兼容并补专项测试，尚未宣告完整回归通过。

原生Excel/WPS保存由Astra 6/low两次尝试（最新2026-10-09 20:30:46～49北京时间），均在@oai/sky初始化报trusted Node process exited unexpectedly；未操作任何文件，无原生保存产物。该验收项未通过，不能用openpyxl/离屏验证替代。

预检查与映射边界见docs/exb01/APPENDIX_B_INPUT_DESIGN.md。locked central不变；不改数据库、Calculator公式、Word版式或P3-C/D/E/F。尚未运行最终完整回归、Windows构建、原生保存验证或最终Head CI，不声明验收完成。下一稳定断点更新结果；新PR不得自动合并。
