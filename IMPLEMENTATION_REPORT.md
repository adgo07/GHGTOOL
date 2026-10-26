# UI 设计资料整理报告

日期：2026-10-26。范围：按用户要求合并 PR60，并整理供 ECQuota-Insight 与 EquipEffi 参考的碳排放 UI 设计资料。本次不实施产品 UI 改动。

## 交付

[碳排放软件 UI 设计参考](docs/ui/GHGTOOL_UI_DESIGN_REFERENCE.md) 包括中央 A/B/C 边界、七类页面、视觉参数、图标资产、交互状态、截图与源码索引、跨软件适配与验收场景。TASK_STATE / HANDOFF 已标明 PR60 按 Owner 指令合并，保留原生验证缺项及新建核算后续待办。

原 PR60 报告保留在 [PR60实施报告](docs/ui/reference-baseline/PR60_IMPLEMENTATION_REPORT.md)，仅统一文本换行与末尾空行；不将原失败或未验收状态改标成功。

## 平台与 Contract 预检查

实际 origin 为 `https://github.com/adgo07/GHGTOOL.git`，默认分支 main；fetch后从 PR60 合并提交 `6fc5909646b855494abee55cff6fd95f8d18b4be` 建立 `codex/ui-reference-design`。原未跟踪目录及用户资料保留，未纳入本次提交。

中央 lock 为 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`，未修改。本任务不涉及中央公共 Contract。相关 Frozen Contract：无新增设计或采用，未修改 Architecture / Numeric / Schema。适用 MUST / MUST NOT：不改变显示与正式计算隔离，不改变历史记录，不扩大功能或标准支持范围，不把 ACTIVE UI 指南升格为 Frozen。

已通过 GitHub 连接读取中央当前默认分支 GUIDE_INDEX、UI指南v0.2、产品家族规格v0.1、UI验收清单；读取对象blob记录在设计资料。无 Frozen 冲突，不需改中央 Contract。中央“GHGTOOL只读预览”是可由后续业务任务演进的能力快照，资料已明确与当前导入链的差异，未改中央文档。相关 Standard Issue：无新增或需决策项；既有台账已读取；本任务不改变既有软件解释。

## 合并证据

GitHub API 核验 PR60：open、非draft、mergeable，head `ac06ca7e9d508b3956fef15fdad3d08d4b955f0a`。两个required checks均completed/success。按精确head执行merge，API返回 `merged=true`，合并SHA为上述业务基线；随后fetch确认origin/main包含该合并。

这些为GitHub来源证据，不是本地重新运行。按用户明确指令合并，不将合并动作描述为新增独立验收PASS或商业发布。

## 本地验证

| 检查与命令方法 | 结果 |
| --- | --- |
| `git rev-parse --show-toplevel`、`git remote get-url origin`、`git fetch origin`、`git remote show origin`、`git branch --show-current`、`git rev-parse HEAD`、`git status --short` | 仓库、默认分支、基线与未跟踪文件已核验；初次受限环境fetch失败，获准执行后成功 |
| PowerShell读取capture-summary.json，逐项读取源码、统一CRLF为LF、计算SHA256与source_sha256比较 | 29通过 / 0失败；当前源码与r3捕获绑定一致 |
| PowerShell正则提取设计资料本地Markdown链接并逐项Test-Path | 42通过 / 0失败，含8张嵌入图；中央链接为GitHub已实际读取文件 |
| view_image阅读首页及r3标准列表、详情、导入、记录列表、依据、参数库、设置 | 8张已视觉核对，标注为既有离屏/合成数据，不冒充本次原生截屏 |
| git diff --check | 最终通过；初次发现TASK_STATE/HANDOFF末尾多余空行，已修复 |

未运行单元测试、全量测试、构建与原生UI：本次仅文档及状态更新，无生产代码改变，不重复长时业务测试。默认PATH中无python，未为本任务安装或修改运行环境。PR60的历史CI和本地失败分别链接保留。本资料分支的GitHub Actions以新PR实时状态为准，不能复用PR60检查声称本分支通过。

## 范围和待审阅事项

未修改应用、测试、资源、中央锁、标准映射、计算表用户文件或其他两个业务仓。没有执行后续新建核算改进，没有创建新的Goal或产品路线。资料送独立审阅，新PR不自动合并。

目标软件后续应先核验自身真实能力，再参考壳、标准库和记录结构，不能照搬碳排放项目保存、数值Profile或附录B业务。原生桌面、日志路径原因、IME/Office/人工DPI、企业样例、干净机及正式发布缺项保持原状态。
