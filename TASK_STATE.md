# 当前任务状态 — B-FGD

更新：2026-10-18。状态：**实施已送源独立验收，尚未取得独立验收结论**。C已完成下列送验证据；源验收正在执行关键链回归，并提出旧B.7模板兼容疑点，现先复现、对照main核查，关闭前不宣布最终验收PASS。不进入其他工作包，不合并。

## 送验对象与范围

- 私有PR：[PR50](https://github.com/adgo07/GHGTOOL/pull/50)，OPEN、未合并。
- 已完成验证的送验head：`7b43c23d31264dd5b5fe23d28599d05f6452d112`。
- 最后生产提交：`6e417b4f83e4a7d4d55193076063cb10816bbea2`；后续送验提交仅测试夹具与治理同步。本次仅整理本文件，不改变该生产对象或既有验证证据。
- base/main：`1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e`（PR49已合并）；CI260实测merge：`463aefd2489fce418455d67b854b26b88de7c09f`。
- 本包范围：`fgd.ratio` / `fgd.factor` / `fgd.conversion`及脱硫GUI、B.7、Canonical、项目保存重开、正式Record、冻结Word完整链。依据Mapping §9.1/§9.3、Issue016和已批准方案；原公式、Numeric与历史Record语义保持。

C负责共享实现与整链；M专属测试已集成并纳入最终联合/CI，现停止；F烟气准备未进入本包，保持停止。FGD_V2稳定设施/批次/组分身份，codec3读取1/2；旧输入不回填，升级另存项目副本，无数据库迁移。V1/V2正式入口共同按归一实际CAL校验同组整剂分母，独立旧组不合并。v8/2.6.0仅机械扩展B.7来源及企业设施编号，v2—v7原字节保留；旧模板业务兼容性以本轮复核为准。

## 已完成送验证据

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

旧B.7模板兼容核查：对照main及真实旧母版，确认1.0.0/2.0.0无J来源列和旧版I/TR空白适用缺省路径是否回归；先证明再决定修复，显式实测空白不得回落。当前尚未给出核查结论。

源独立验收尚未结束。原生Office保存回导、真实鼠标/中文IME/人工DPI、企业样例、干净目标机及商业许可履约仍OPEN/NOT_RUN。不CU、不删除旧工作树、不公开上传、不接烟气/热力/N/外部CO₂，不宣称SUPPORTED或商业发行就绪。除上述源验收反馈核查外，保持停止等待验收。
