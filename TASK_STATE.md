# 当前任务状态

状态：GHGTOOL HTML V4 正式落地 — PR1 必要业务适配进行中；PR2 等待 PR1 验收合并后再开始。

最后更新：2026-10-11。工作分支：`codex/ghg-html-v4-pr1`；基线为经 `git fetch origin` 核实的 `origin/main@408e29cbd0f42d88077534ef50c4d787f2fad3cc`。原 `codex/ghg-ui-p3-df` 脏工作区保持未动。

- PR1 覆盖燃料碳氧化率实测证据、脱硫剂分组与多组分含量、名称从 GUI/Excel/项目/Canonical/Record 到 Word B.7 的传递及旧快照兼容。
- Calculator 正式公式、历史 Record、数据库 Schema 和 migration 均未改；旧 USER_DEFINED 来源保留，旧记录/项目缺少的名称继续为空，不推断。
- PR1 首轮 Windows CI（run #205）全量套件执行 465 项后报 3 failures。已补齐 FGD 名称 FieldSpec、按组级用量更新测试，并校正氧化率证据显隐与 C.2 锁定测试；本地定向 6/6 通过，语法与 diff 检查通过。修订后的 Windows CI 待重跑；独立验收仍以 GitHub Checks/review 为准，不把本地结果描述为 CI。C.4 饱和温度来源仍 OPEN，不阻塞已确定范围。
- PR2 仅在 PR1 验收合并后开始；首页样板截图需先由 Owner 确认。

中央 Frozen baseline 继续锁定 `ee5feb0cc34dbd99790500fadd0c4c932e202a20`。
