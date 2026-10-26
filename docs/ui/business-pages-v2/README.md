# 五页 V2 证据

当前PR60收口证据为[refinement r3图集](refinements-r3/review.html)、[限定视觉回执](refinements-r3/astra-receipt.json)及[本地完整摘要](refinements-r3/local-full-summary.json)。产品代码 `fb56ad737b6d0a676e5f594f689e08e88f14aaa3`，astra 92图/29源限定PASS；本地裸字体完整运行1121通过/1失败，5371.075s。r3为Owner后续授权增量，不把原包白名单或旧r9/启动候选包改标为当前版本。正式最新PR/CI/ZIP/manifest见PR60与最终交付回执。

## 原版五页与启动增补的历史基线

PR60启动日志缺陷新增[独立摘要](startup-logging-review.json)。下列图集及1106项摘要属于增补前基线，当时29项UI源未变，但旧CI308/隔离smoke不覆盖真实用户日志路径访问。新head及新包以PR/API与最终回执为准。

打开[精选28图](review.html)。[capture-index.json](capture-index.json)保留r9全部60图/29源身份；精选之外的原图仍在本地原始证据归档，不伪装此目录已包含全部60图。[限定视觉回执](visual-review-receipt.json)记录astra范围及未执行项；[本地完整摘要](local-full-summary.json)和[定向摘要](local-verification.json)与CI来源分开。

捕获head e2c7520；完整测试head5c0c340只增加G03已批准呈现断言同步及阶段文档，29源哈希逐项相同。两个未通过的旧布局断言没有业务判定含义，期间/地区/边界/模板/按钮/保存/正式核算/历史记录业务断言完整保留。[范围证明](scope-proof.json)来自原包严格保护树与19/19接线检查。[原包身份](package-identity.json)保留首次受控应用身份，不重新应用旧包。

原始528文件ZIP CRC及逐文件SHA复核通过，含失败/中间图与原始日志，SHA 84a16bc933fab487430db34c365882db9d80e1f1264b08abe6ffc11935ea1ec4。这里只记录相对身份；本地保留地址见最终回执。本证据不等同于原生或发布验收。
