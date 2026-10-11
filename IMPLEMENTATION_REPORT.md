# GHGTOOL HTML V4 — PR1 实施报告

日期：2026-10-11。范围：必要业务适配；PR2 全页面 Presentation 尚未开始，须等待 PR1 验收合并。

## 基线与平台 / Contract 预检查

仓库为 `https://github.com/adgo07/GHGTOOL.git`。PR1 从经 fetch 核验的 `origin/main@408e29cbd0f42d88077534ef50c4d787f2fad3cc` 建立独立工作树与 `codex/ghg-html-v4-pr1`。本地中央 Frozen baseline 为 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。本任务不涉及中央公共 Contract，不修改 platform-lock；标准疑似问题登记无新增项，不改变标准解释。

## 已实现

- 燃料新实测碳氧化率映射为 `MEASURED`，要求本燃料检测定位并将逐燃料证据冻结进 Record；旧项目 `USER_DEFINED` 语义保留，共享证据不会覆盖专属检测证据。
- FGD 页面改为脱硫剂名称/配方组；允许同名独立组，组用量接入既有逐组分计算，单组分可用90%缺省值，多组分含量改为实测，C.2 因子锁定，自定义因子标记为化学计算。
- 脱硫剂名称贯通 Canonical 输入、Project 状态、Excel B.7、Record 与 Word/记录详情 B.7。旧项目逐组分用量不合并，缺失名称保持缺失。没有改计算公式、Record Schema 或 SQLite migration。
- 本包未改热力或物料计算。现有定向用例确认自动蒸汽焓值与手填物料名称路径继续工作；C.4 饱和温度来源未确认，保持 OPEN。

## 验证

- 修改的生产/测试 Python 文件通过 `py_compile`；`git diff --check` 无空白错误。
- 定向回归命令实际结果：核心 PR1 用例 13/13、更新后 Record/兼容用例 4/4、来源/热力/物料复核 3/3、最终用量断言 1/1，全部通过（用例间有重复）。
- 一次早期 91 项模块组合运行得到 2 failures、15 errors：多数错误是旧 FGD 测试仍调用设施/逐组分输入方式；一项失败暴露了共享证据被新逐燃料证据错误抑制，已修复并保留原有共享关联；另一项对应多组分含量现需实测。更新测试后，改动直接涉及用例定向重跑通过。该次不是全量测试结论。
- 首轮 GitHub Windows CI run #205 在 merge ref 执行 465 项后报 3 failures（无 errors 摘要）；失败涉及 FGD 新分组测试输入仍填逐组分用量、燃料来源控件可见性断言沿用旧交互，以及页面 FieldSpec 未登记脱硫剂名称。后续本地定向重跑还发现正式流程测试试图覆盖已锁定 C.2 因子，已改为验证自定义因子标记“化学计算”。
- 修正后 6 个定向用例通过，覆盖以上 UI/FieldSpec、C.2 与自定义因子、实测氧化率和逐燃料证据；py_compile 与 git diff --check 通过。Windows CI 需由新 head 重新执行，以上本地结果不代表全量回归。

## 尚未闭合

PR1 未自动合并；Windows CI 和独立验收状态以 PR 当前检查/Review 记录为准。C.4 饱和温度来源仍 OPEN；PR1 验收合并前不得开始 PR2。
