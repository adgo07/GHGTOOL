# HTML V4 到 Qt Widgets 参数映射

本页记录《GHGTOOL 全页面 HTML 交互原型 V4》到现有 PySide6/Qt Widgets 的最小视觉映射，作为 PR2 的实现说明；不新增主题框架。

| V4 设计项 | Qt 实现 |
| --- | --- |
| 页面画布：浅蓝顶部渐变、浅灰蓝正文 | 首页使用 `HOME_CANVAS_GRADIENT`；其余页面使用 `PAGE_BACKGROUND` |
| 品牌深蓝 `#18364F`、正文 `#213A4F`、辅助字 `#698198`、强调蓝 `#197CC2`、边线 `#DAE7F1` | `packages/ui/design_tokens.py` 的应用级 QSS 与首页局部样式 |
| 卡片白底、14 px 圆角、浅边框 | `QFrame#card`、首页入口卡和最近工作卡的局部 QSS |
| 中文界面字体 | Windows 使用 `Microsoft YaHei UI`，回退到 `Microsoft YaHei` |
| 首页 5 个横向入口卡片，标准库为重点卡 | `HomePage`；首页无侧栏，标准库卡片为蓝色强调样式 |
| 首页工作区与最近核算 | `HomePage` 从现有 Project 与不可变 Record 服务读取真实数据；没有数据时显示明确空状态，不使用原型样例数据 |
| 主导航与品牌区 | `AppShell`；侧栏 242 px、品牌区 120 px、导航项 44 px |
| 内容宽度 | 首页最大 1480 px；其他页面最大 1360 px |
| 页面边距 | 常规页面 32 px，窗口宽度不大于 1366 px 时 24 px；首页侧边距 54 px，窗口宽度不大于 1240 px 时 30 px |
| 表格、输入框、选项卡、焦点与悬停状态 | 使用 `application_stylesheet()`，页面仅保留必要的局部覆盖 |
| 下拉箭头 | 使用打包资源 `resources/icons/chevron-down.svg`，由 `scripts/inspect_release.py` 白名单管理 |
| 当前炭素材料模块的八类排放源入口 | `CarbonMaterialAccountingPage` 使用 V4 四列网格；这八类只属于 `GB/T 32151.34—2024` |

公共页面（首页、导航、标准库、参数库、记录列表与设置）使用中性文案。标准选择只把 `STANDARD_ID` 分发到 `CarbonMaterialAccountingPage`；其他标准继续展示目录信息与“核算未开放”，不会落入炭素材料页面。

验证截图与采集条件见 [V4 页面截图](v4-evidence/README.md)。截图为 Windows 平台 Qt 窗口的真实渲染，使用隔离的测试 Catalog、Project 与冻结 Record 样例。
