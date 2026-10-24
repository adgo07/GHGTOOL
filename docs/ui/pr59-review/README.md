# PR59 当前视觉与验证入口

当前树仅保留最终关键截图、去路径摘要和原始证据索引。最终截图由 scripts/capture_pr59_final.py 生成，使用真实 Qt 整窗、合成输入和隔离临时库；不是浏览器重绘或原生桌面验证。summary 的 code_head 与逐文件 SHA256 绑定代码，后续文档提交单独区分。

旧证据共 241 文件、82 张 PNG，原样归档为 pr59-historical-a96f8ed90a1d.zip；ZIP SHA256 为 6c3b91e82a8b8e81fbeb0a098862eac4db58b38323454aa129d1fcf52eb1b9d1。逐文件路径、大小、SHA256 见 ARCHIVE_INDEX.json；ZIP CRC 与解压后哈希均已核验。原始文件在工作树外保全，不重写原始日志；本索引和摘要采用相对路径。

历史 ca-layout、whole-page-review、integration 和 qt-lifecycle 的各批次继续绑定自己的父 HEAD 与源码哈希，旧失败、中断、视觉 HOLD 和后续 PASS 不混并。父 HEAD + 逐文件源码哈希仍有效，不因后续提交而作废；不把旧通过重标为当前源。压缩当前树不缩小已有 Git history。

当前实现、命令、数量和限制见根目录 IMPLEMENTATION_REPORT.md；阶段状态见 TASK_STATE.md。PR59 最新 CI 和候选包须核对实际 PR head，不使用旧 a96 的 CI304 或制品背书当前修改。
