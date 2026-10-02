# governance: consolidate GHGTOOL reference-standard roadmap and current-state docs

> 本 PR 为**治理收口 / 路线修正**任务（GHG-GOV-R1），不做业务开发。全部改动为 Markdown 治理文档。

## 1. Baseline

| 项目 | 值 |
|---|---|
| repository | `https://github.com/adgo07/GHGTOOL.git`（`adgo07/GHGTOOL`） |
| default branch | `main` |
| base SHA | `cae2ff33b2f09d115db950fae4b0829f698ec8fa` |
| execution branch | `governance/consolidate-reference-standard-roadmap-and-current-state` |
| execution head | `642c26e278986904cad4841475ed8157b0787eac`（已推送到 `origin`） |

分支从**最新 `origin/main`** 创建（`git fetch origin` 后确认 `origin/main` 与该 SHA 一致）。

> 本机无 GitHub CLI 与 CI token，因此 PR 需手动创建：
> `https://github.com/adgo07/GHGTOOL/pull/new/governance/consolidate-reference-standard-roadmap-and-current-state`

## 2. 本 PR 同时完成两件事（不拆成两个 PR）

1. **GHGTOOL 后续整体产品路线修正与收口**；
2. **当前仓库治理文档、历史状态和冲突表述清理**。

原因：清理过程中必然触及 `AGENTS.md / HANDOFF.md / TASK_STATE.md / IMPLEMENTATION_REPORT.md / REFERENCE_STANDARD_ROADMAP.md / README.md`，若先只清理一部分再改路线，会人为制造一段新的口径不一致。merge 后仓库立即只存在一套清晰的当前口径。

## 3. 唯一产品路线

`REFERENCE_STANDARD_ROADMAP.md` 成为本仓**唯一**产品级后续路线：

```text
GHG-RS01  GB/T 32151.34 完整参考标准业务收口
     ↓
GHG-RS02  生命周期 / Record / 结果解释 / Trace 最终闭环
     ↓
GHG-RS03  Excel 正式闭环
     ↓
GHG-RS04  Golden / Formal Support Candidate Gate
     ↓
GHG-RS05  Windows 正式版 Release Gate
     ↓
GHG-RS06+ 第二标准及后续演进
```

未新增 `MASTER_PLAN_V2` / `POST_V1_PLAN` / `S0-S6_PLAN` 等任何平行路线文件；第三方提案的合理内容已吸收进现有 Roadmap。

## 4. 改动文件

| 文件 | 处理 |
|---|---|
| `REFERENCE_STANDARD_ROADMAP.md` | 重写为唯一当前路线（GHG-RS01～RS06+、Standard Completeness Matrix、Golden Gate、UI 项归属） |
| `HANDOFF.md` | 由 9 月 Windows V1 历史全文（约 877 行）重写为当前阶段交接（约 175 行） |
| `TASK_STATE.md` | 由历史流水账（约 160 KB）重写为当前状态文件 + 精简里程碑表 |
| `IMPLEMENTATION_REPORT.md` | 由历史追加日志（约 190 KB）重写为本工作包实施报告，并确立“每阶段重写”规则 |
| `AGENTS.md` | 按任务类型读取纪律、执行授权与停止条件、SHA 纪律修正（未推倒重来） |
| `README.md` | 同步当前 Reference Standard / 支持状态 / Windows / Excel / 下一阶段 |
| `UI_CURRENT_STATE_AUDIT.md` | 明确为专项证据（非 Roadmap），新增阶段归属 |
| `docs/DELIVERY.md` | 同步 catalog data version、projects 迁移数与 Excel 阶段状态 |
| `docs/governance/NUMERIC_CONTRACT_V1_ADOPTION_REPORT.md` | 补充“PR #17 已合并”的合并后说明（不改历史正文） |

## 5. 清理的陈旧 / 冲突类别

- 历史绝对路径（`D:\project\...`、`D:\MD仓库\...`）从当前正文移除；
- 项目保存旧禁令与 `.qzproj` 混淆统一为“两件事”；
- “三个物理隔离数据库”修正为实际四库（`catalog` / `user` / `records` / `projects`）；
- Excel “V1 永久 OUT OF SCOPE”与 RS03 正式闭环的区别写清；
- `44/12` / `44/16` / GWP 统一为 Numeric v1 语义（**不是** ordinary unit conversion）；
- 历史 PR / SHA 噪声与已失效验收门禁从当前正文移除（Git history 保存）；
- 过度人工审批规则修正为“可直接执行清单 + 8 类必须停止询问”；
- UI 盘点项建立 RS01/RS02/RS03/技术债归属，不再派生 UIR05～UIRxx。

## 6. 明确未做

- 未修改任何业务代码、Calculator、Canonical、Rule、SQLite schema/迁移、Excel、UI 业务语义或标准解释；
- 未修改 `platform-lock.json`、`PLATFORM_BASELINE.md` 或任何中央 Contract；
- 未启用 Excel、未实现第二标准、未编 Golden、未启动 `GHG-RS01`。

## 7. 验证

### Local（EXECUTED）

环境：本地 Python **3.12.14** 虚拟环境（`uv venv --python 3.12 .venv` + `uv pip install -e .`，PySide6 6.11.2；`.venv/` 已 gitignore）。

| 命令 | 结果 |
|---|---|
| `python -m unittest discover -s tests -t . -v` | **Ran 214 tests — OK**（0 失败/错误/跳过，68.740 s） |
| `python scripts/validate_canonical.py` | `valid: 9 standards, 12 sources, 7 parameters, 7 factors` |
| `python scripts/initialize_databases.py --output-dir tmp/ggh-gov-r1/dbs` | catalog / user / records / projects 四库从零重建成功 |
| `python scripts/uir04_manual_gui_acceptance.py` | 场景 A～E 全部 PASS |
| `python scripts/uir04_scale_acceptance.py --scale 1.25 / 1.5` | 均 PASS |
| `python -m unittest tests.test_g08_delivery` | Ran 10 tests — OK |
| `uv pip check` | All installed packages are compatible |
| `python -m compileall -q apps packages resources scripts tests` | exit 0（需设置 `PYTHONPYCACHEPREFIX` 指向新建目录） |

说明：本机对 Python 子进程在**已存在的** `build/`、`*/__pycache__/` 内的写入返回 `Permission denied`（本机执行环境限制，非仓库缺陷）。因此 `compileall` 通过 `PYTHONPYCACHEPREFIX` 改写缓存目录，数据库初始化输出到 `tmp/`。未冒充任何未执行结果。

### GitHub Actions（Windows / Python 3.12）

EXECUTED — 见本 PR 最新 head 的 Windows CI（merge-ref full tests + exact PR-head standalone audit）。

本地替代范围证据：`git diff --name-only` 确认改动仅限 Markdown 治理文档，未触及 `apps/`、`packages/`、`migrations/`、`scripts/`、`tests/`、`data-source/`、`conformance/`。

## 8. Next step

**GHG-RS01 — GB/T 32151.34 完整参考标准业务收口**。本 PR 不启动 RS01，完成后停止等待独立验收。
