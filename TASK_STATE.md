# 当前任务状态 — B-EXTERNAL

2026-10-20：ACTIVE / PR53复核退修中。此前最终head 73c47a9已有CI287和实际制品证据，本轮兼容修复另行验证；从main@0f50642544b110ee461f1b32ef8a01091d0f44d0独立分支codex/b-external-integration开始，PR52已合并。原根用户修改和旧热力树两份未提交文档均未动。

## 平台 / Contract 预检查

实际origin已核adgo07/GHGTOOL，已fetch/default main。中央锁ee5feb0cc34dbd99790500fadd0c4c932e202a20不变，Architecture V2.1/Numeric v1/Profiles v1 Frozen；必须分层、同Canonical/Application、声明Profile一致/ambient独立/full-value exact、不可变Record与消费者只读冻结值。禁止显示修约回流、epsilon、改ES/EI/ET、伪造标准行、旧Record回填/重算或自动升级中央Frozen。Carbon Decimal40/HALF_UP为ALLOWED PROJECT DIFFERENCE，非平台默认；Issue016/Mapping11.1已有批准，旧声明即ERROR为LOCAL DEFECT。本包不改变标准解释或中央Contract，不需数据库迁移；Unit/Workspace等DRAFT不冒称Frozen。已读当前ACTIVE UI v0.2。

## 当前证据

- 干净8556933：python -B -m unittest discover -s tests -t . -v，1029/1029通过、1313.979s、0FAIL/0ERROR/0SKIP；tmp/b-external/frozen-head-full.log。
- 首轮全量1028项曾4FAIL/1ERROR，材料v11版本、通用codec假设及旧断言已修；64项复验通过后，上述冻结head全量通过。详见实施报告，不掩盖负向记录。
- 同head本地实际EXE/PYZ/包内原生依赖全链通过，无源码回退，含v11材料换算、软件补充/partial烟气/单位矩阵、GUI/Excel/SQLite/冻结Word、旧CI273实际合成记录2/2保护、2次隔离启动；313个manifest列项+manifest自身314可见文件ZIP往返通过。此为本地证据，非Actions。
- 同R11审阅资产20项Python/25场景往返通过，61行/450scope/每表8隐藏列/最高344pt和3份Canonical原字节不变；原九张表XML与旧v2—v10不改。

软件补充CAR-EXTERNAL-CO2-016.1、Calculator EXTERNAL.1、payload6/封套2、输入v11/2.9.0、新Schema3.1.0/历史3.0.0已接线。当前尚未触发本包CI，待稳定证据提交后仅推送一次。源为独立验收方，作者测试不等于独立PASS；不自动合并、不启动N抽查/RS04/RS05、不商业交付，零付费边界保持。


源独立接验增量：源已独立运行补充runtime/chain/excel共15项，35.383s，OK（源自行提供，非作者执行）。源指出所有状态的声明纳入提示不准确，本地仅按冻结status修正notes及PENDING状态标签：COMPLETED_*才称已纳入，PENDING为声明已选择/数值待补，NOT_INCLUDED与历史不声称声明或纳入；未核验外部计算/完整性及partial覆盖提示保留。python -B -m unittest tests.test_b_external_status_copy -v：2/2通过；实际旧CI273 DB/模型/Word2/2保护仍通过。求值、冻结数值、无节点行为、算法/Schema身份均不变。按源协调要求本地保留补丁、暂不推送，CI286继续取得现远端a242962证据，不取消或重复触发昂贵CI；最终head待统一收口。


CI286收口：首轮远端a242962两个作业success（merge4513b083：1029/1568.889s；head G08：18/12.375s），下载artifact12259330066 ZIP哈希8d7bc3f0378aeb5dee15f351aea995de1533f9d0d39bb3243daab37045b0f83c，322+manifest=323可见文件、真实包内链路、旧历史保护及2启动通过。该制品不含本地d645文案修复。源已独立15+2范围复验、文案关闭且无新增退修；当前按源安排将补丁/2测试/最终包内文案与母版复制断言/本回执集中推送一次，再取得最终head新显示代码证据。最终回执记录在PR53说明与本地tmp，不因纯文档反复触发CI；不合并/不CU。


## PR53 复核退修（2026-10-20）

平台 / Contract 预检查：继续原 PR53 分支，开工核对 origin 为 adgo07/GHGTOOL、fetch 后 head 73c47a98044c00591d6717d1d47d3a05f5aecffe、工作区干净。locked central ee5feb0cc34dbd99790500fadd0c4c932e202a20 不变；Architecture V2.1 / Numeric v1 / Profiles v1 的分层、Profile 一致、ambient 独立及不可变 Record MUST 不变。不得更改公式、Numeric、旧 Record 或把 Presentation State 定义为公共 Workspace Contract；属于本地兼容缺陷与提示修复，无中央 Contract 修改。相关 Standard Issue 为016；本轮不改变既有软件解释。

此前最终显示补丁已有 [CI287](https://github.com/adgo07/GHGTOOL/actions/runs/39410582292) 与实际下载制品证据：head 73c47a9，merge ff2a373，GitHub 全量1031/1698.091s、G08 18/8.369s，0失败/错误/跳过。artifact12260549104，75,747,968字节，ZIP SHA256 df8e32283b05265c15ddab918816a21e2571a5c3fa0452df41784190837b37c9，manifest SHA256 2ac64788c0f1689679921ae8c99c64ab70de4ed430345ca1421c96dcedd87f4b，322列项+manifest自身323文件；实际EXE/PYZ、包内原生依赖、状态文案、母版复制、旧CI273记录保护及2启动通过。源另独立核验API与322文件哈希（源提供证据，非作者执行）。CI286继续保留为不含显示补丁的历史证据；CI287不能证明本轮新指纹修复。

F01修复前：实际PR52 merge 0f506425旧代码运行GUI计算/保存生成SQLite项目，当前代码动态关闭重开两次均误报stale并隐藏结果；历史calculation fingerprint a283337c88c506af90bf6c346710889924a3782ce6529b4ca69087d3f05f0844，新增空字段后变为2cc2d1c35c137ae97277503a9d543b1b5d2d41fa508a2e1ef262af68b399464f。仅根external_co2=None按缺省缺失处理，显式纳入/不纳入保留差异；合成旧SQLite/Word/生成脚本与proof纳入回归，非删除新字段手造旧指纹。F02只改GUI业务提醒。模板能力归并为有界已知版本表，未知未来版本拒绝，2.4专有别名和旧热力种子规则保留，母版/XML字节不动。投影片段README说明其构建用途。交付验证缺pip明确前置失败，不skip，原强制CI不变。

本地首轮新回归5项中3通过、2ERROR（测试引用错误的热力行键及Importer类名，业务恢复/Word断言已通过）；已修正测试接口。稳定产品断点1fb4cd50ca77b3c31bc3e63c44abe94cc0eaad49；`python -B -m unittest tests.test_b_external_review tests.test_b_external_excel tests.test_b_fgd_legacy_templates tests.test_b_material_source_review tests.test_fuel_power_template_v5 tests.test_b_heat_chain tests.test_g08_delivery -v`：本地56/56通过，218.023s，0失败/错误/跳过；日志SHA256 6774aad6a74e3d4b35a9973aea5a3523be09eb882d8fbbca8e41a95ada815b73。`python -B scripts/validate_canonical.py`：9 standards/12 sources/102 parameters/138 factors有效；`python -B -m compileall -q apps packages resources scripts tests docs/ci/B_EXTERNAL_PACKAGE_VERIFIER.py`通过。真实wheel/sdist安装资源验证已执行，缺pip测试验证明确失败且不构建。未追加本地全量，跨模块全量由必需Windows merge-ref CI执行，避免重复昂贵检查；原生CU与N抽查未执行，按任务边界延期。下一步一次稳定推送，取得新head CI/实际制品及源独立验收；最终回执落PR53当前checks/说明与本地proof，不为纯文档再触发CI，不合并。
