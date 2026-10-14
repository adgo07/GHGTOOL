# PR46验收修订证据

本地生产验收head `8d87199f25bd17e56e2e8443e09575966d557f12`；base main `204dded5d03853617f79a1f05693e89b619df9d1`。截图manifest逐个登记实际源文件SHA，不沿用旧head的510项证据。

- `100/`、`125/`：Windows Qt原生平台、1366×768逻辑窗口、QT_SCALE_FACTOR 1.0/1.25各20项程序检查和19次捕获（18个不同PNG）。使用QTest/控件API与QWidget.grab，不是系统DPI调整或真实鼠标交互；程序字体为本机Microsoft YaHei。脚本 `capture_windows_qt.py` 只接受TEMP合成工作簿。
- `excel-wps/`：当前2.1受控模板、完整合成九表，用独立且空白的WPS ET COM实例原生保存TEMP副本；17项全部通过，原源文件不改。完整输入、计算结果、快照/trace一致，预览零Record、正式一次新增一条。
- `word-wps/`：最终冻结合成Record经WPS文字兼容COM只读导出11页PDF，再渲染逐页PNG；B.1～B.9共10张业务表。未关闭可能共享的应用实例，打开文档数前后均0，只关闭本次TEMP文档，不改用户文档。已检查全部11页、短来源/必要注释、扣减意义和冗余尾注移除。PDF元数据Creator=WPS文字；不是Microsoft Word或真实企业UAT。

当前模板2.1 SHA256：`f303ad02ca03e0464f736dafc39967abd06366a902f1b502dd17470656eb1718`。旧2.0资源SHA固定保留作为只读结构兼容，下载只提供当前2.1。旧WPS证据目录未覆盖。

复现模板保存：先以tests.exb01_fixture_helper生成TEMP合成工作簿，再运行上一层 `../excel-wps/native_excel_roundtrip.ps1`（单独进程，该脚本会exit）；之后调用 `../excel-wps/verify_roundtrip.py <repo> <before> <saved> <run-dir> f303ad02ca03e0464f736dafc39967abd06366a902f1b502dd17470656eb1718 gb_t_32151_34_2024_appendix_b_v3.xlsx`。最后两参数显式选当前版本；省略时仍复现历史2.0证据。

未闭合：电脑操作工具曾出现窗口owner不匹配，显式AppUserModelID后仍截图超时/激活失败；未执行任何真实点击或中文输入，不能计为通过。真实企业样例、人工Windows DPI操作及Owner最终验收仍开放。


已核实的Windows CI #221（run38546946024，交付head e500edc65fa1191acf0197454d6ad012118f19e0）：merge-ref d30568374d7a332bc231251c34fceada06b79081完整561/561通过（747.623秒）；精确PR-head交付专项14/14通过（4.293秒），构建、271文件审计、272可见文件ZIP回导、两次启动及provenance校验全部通过。Artifact11885782152名称与head一致，ZIP59,785,100字节。后续纯证据文档提交不修改生产；最新PR head与Checks、候选下载入口以PR46正文为准，不混用本地和CI来源。
