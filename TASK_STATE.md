# 当前任务状态 — B-FGD

更新：2026-10-18。状态：**源独立验收反馈的旧B.7兼容回归已定向修复，送源复验；尚未取得最终验收结论**。当前对象为PR50最新head，精确SHA及对应CI/实际包证据见PR50最新说明与本地摘要；不得以原7b绿色替代新代码验证。不进入其他工作包，不合并。

## 送验对象与范围

- 私有PR：[PR50](https://github.com/adgo07/GHGTOOL/pull/50)，OPEN、未合并。
- 本次最后生产提交：`c52a3be86090069b1507c1e727ce4cc97196046c`；随后仅同步本状态和实施报告。
- 原送验head：`7b43c23d31264dd5b5fe23d28599d05f6452d112`，其CI260/实包证据保留为历史参考。
- base/main：`1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e`（PR49已合并）；CI260实测merge：`463aefd2489fce418455d67b854b26b88de7c09f`。
- 本包范围：`fgd.ratio` / `fgd.factor` / `fgd.conversion`及脱硫GUI、B.7、Canonical、项目保存重开、正式Record、冻结Word完整链。依据Mapping §9.1/§9.3、Issue016和已批准方案；原公式、Numeric与历史Record语义保持。

C负责共享实现与整链；M专属测试已集成并纳入最终联合/CI，现停止；F烟气准备未进入本包，保持停止。FGD_V2稳定设施/批次/组分身份，codec3读取1/2；旧输入不回填，升级另存项目副本，无数据库迁移。V1/V2正式入口共同按归一实际CAL校验同组整剂分母，独立旧组不合并。v8/2.6.0仅机械扩展B.7来源及企业设施编号，v2—v7原字节保留；旧模板兼容已按真实母版/main对照定向修复，旧字节保持。

## 本次兼容修复与验证

真实v2—v7母版12合法场景及v1历史结构fixture2场景：main14/14可算、修复前9回归。仅按版本恢复旧无来源列的既有表达，仍共用Resolver/来源求值器；真正空白适用缺省有明确告警，非法非空/多组分I/错缺绑定/v8显式实测空白保持拒绝，公式/来源集合/历史Record不变。

新增10测试方法覆盖104子场景（22合法/82拒绝），覆盖清单与完整命令见[IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md)。提交前受影响Excel/政策/Word/交付联合91/91、87.795s，与本次生产提交代码一致；日志`tmp/fgd-final-evidence/legacy-template-affected.log`。当前head针对性/CI/实际包的实际统计分别在PR50和`tmp/fgd-final-evidence/summary.json`按head记录，不外推历史结果。

## 原7b43c23送验证据（历史参考）

以下结果对应上述7b43c23送验对象，不能外推为后续生产变更的验证或源独立验收结论。

| 证据来源 | 命令或检查 | 实际结果 |
|---|---|---|
| 本地 | 30模块联合；完整命令见PR50与本地摘要 | 357/357，430.886s，0FAIL/0ERROR |
| GitHub Actions CI260 merge-ref | `python -m unittest discover -s tests -t . -v` | 873/873，1370.590s |
| GitHub Actions CI260 exact-head | `python -m unittest tests.test_g08_delivery -v` | 17/17，6.741s |
| CI260两个任务 | Canonical、compile、pip check、数据库、GUI、125%/150%缩放 | PASS |
| CI260 standalone | 目录/归档审计及隔离启动smoke | 277文件、278上传文件、2次启动PASS |
| 本地实际下载包 | 全manifest大小/哈希、head/merge provenance、普通/延迟PE导入 | 277条匹配；129PE；VirtualKeyboard路径/导入0、iapws路径0 |
| 本地EXE/PYZ业务代码及包内资源 | 禁止业务源码回退；2.8174/11.88、缺值/错绑定/V1不等量拒绝、冻结Word | PASS；仅2条Record；执行后包体再审计PASS；不是原生UI操作 |
| 实际PR49历史对象 | 旧MATERIAL.1生成Record/Word，最终源码及包内代码禁用Calculator/Resolver读取 | 冻结快照、报告模型及Word正文XML一致；仍1条Record |
| 同范围审阅四件套 | validator/builder/fixture/checks及raw LF/Git字节核验 | 25/25，意见0→0 |

CI260：[运行记录](https://github.com/adgo07/GHGTOOL/actions/runs/39085860291)，两任务SUCCESS。实际下载artifact `12121850125`，59,850,968字节；source_commit/pr_head_sha为7b43c23，tested_merge_sha为上述merge。

- ZIP SHA256：`c35647782e409c4c852bfffe547333770617fd32c4ff276fb585d744e8bbce2a`
- manifest SHA256：`30ad46142df611a649f1ab3048df412e997b99377cc1f4392891de83ebd9fa44`
- EXE SHA256：`329efa1c926ef80cd657745c44d2b690372134e02a2e17f6d8324531848055c6`

完整统计、命令和包体/历史对象核验见PR50及本次本地证据`tmp/fgd-final-evidence/summary.json`。实施过程、失败原因和修复依据见[IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md)及Git历史；本文件不再累加旧断点。旧714候选已撤回，CI258成功不替代本包最终证据；CI259的既有合法夹具失败及后续修正保留于实施报告/PR50。

## 平台 / Contract 与标准预检查

origin已核实为adgo07/GHGTOOL，默认main。locked central `ee5feb0cc34dbd99790500fadd0c4c932e202a20`不变；Architecture V2.1、Numeric v1及Profiles v1按锁读取，UI v0.2按ACTIVE读取。适用MUST为分层/共享内核、declared-profile consistency、ambient independence、full-value exact、历史不漂移；MUST NOT为业务epsilon、显示回流、复制算法、自动升级Frozen、Qt状态充当公共Workspace。p40/HALF_UP属ALLOWED PROJECT DIFFERENCE，无中央冲突，无需改中央Contract。相关Standard Issue016，未新增标准解释。本次状态文档整理不涉及中央公共Contract变更。

## 当前未决项与停止边界

旧B.7兼容回归已完成证明与定向修复，源需按当前稳定提交复验diff、新增兼容组及对应CI/实际包证据；不把历史68/873绿色当作旧路径覆盖。

源独立验收尚未结束。原生Office保存回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机及商业许可履约仍OPEN/NOT_RUN。不CU、不删除旧工作树、不公开上传、不接烟气/热力/N/外部CO₂，不宣称SUPPORTED或商业发行就绪。除本次兼容修复的验证与交接外，保持停止等待源复验。
