# PR62 最终代表图

以下是实际Qt离屏抓图，使用隔离合成数据，不等于真实Windows交互验收；未调用桌面CU。恰好6张，共约1MB；全尺寸原始抓图与QA数据库留在本轮外部临时归档，不把数据库或几十张历史图带入仓库。

产品源为 `2d555e165c41c30bdec8c075ff813f47061cc0f8`，本轮返修未修改apps/packages/resources；因此该源绑定仍有效。精确Git树、源码/图片SHA256、尺寸、DPR及抓图脚本版本见[capture-manifest.json](capture-manifest.json)。桌面四图抓取之后脚本仅补Qt销毁，DPR2与小工作区图使用补齐清理的脚本，清单明确区分。小工作区抓图后，探针仅再补配置输出和实际DPR一致性断言；保留当时执行脚本的哈希，不冒称其为后来脚本字节。源码哈希同时提供现场CRLF字节和Git权威LF blob，便于跨机器核验。

- [首页](home.png)、[标准库](standards.png)、[新建核算](new-accounting.png)、[记录详情](record-detail.png)：1280×800 DIP / DPR1。
- [DPR2首页](home-dpr2.png)：1280×800 DIP，实际2560×1600像素；原图Logo及SVG原生渲染。
- [150%小工作区](small-150.png)：531×531 DIP，实际797×797像素；排放源紧凑导航与局部横滚。单帧展示当前位置，不把部分字段暂在视口外误称丢失；探针已实际检查活动量控件左端、右端、垂直位置及编辑区末端分别可达，保留所有动态行和删除断言。

图中G07示例是QA合成历史记录，非企业数据。标准库是当前实现/夹具状态截图，本工作包不改变标准状态或宣称正式SUPPORTED。

图标预着色资源的受控基础文件哈希、批准色板及中央候选来源见[icon-provenance.json](icon-provenance.json)。运行 `python scripts/generate_family_icon_variants.py --check` 校验23个变体逐字节一致；不加参数时可从受控基础SVG重复生成，基础哈希变化必须重新审查来源。本清单在docs，不增加运行时包资源或另建图标系统。
