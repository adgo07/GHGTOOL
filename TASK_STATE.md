# 当前任务状态 — B-FGD

更新：2026-10-18。状态：已启动，完成基线核实和批准边界读取，实施前接口设计中。

PR49已按Owner授权合并；main/本包起点为1ed2e4a3225d0ee322dd0fbe82cacdd6f8a5542e。材料受验head40778c7及CI256（832项全量、17项exact-head G08、实际包审计/归档/两次启动）证据保留于PR49收口记录，不能当本包测试。F01/F02/F03、v7/2.5.0及旧模板字节为保护基线。旧材料工作树和根用户修改保留。

## 本包范围与所有权

仅接管fgd.ratio、fgd.factor、fgd.conversion及脱硫GUI/B.7/Canonical/项目保存重开/正式Record/冻结Word完整链。依据Mapping §9.1/§9.3、Issue016与批准V2第8节；不新解释原公式、Numeric、来源资格，不夹带烟气/热力/外部CO₂。

| 所有者 | 独占写入范围 | 当前接口 |
|---|---|---|
| C共享集成 | policy/Resolver/混合Calculator/UI/Excel/codec/Project/报告/资源/构建/治理、整链测试 | 原Canonical/Application；生产接口经本包小提交发布给M |
| M脱硫核对 | 新tests/test_b_fgd_specialist.py | 先只读真实C.2和通用I/TR绑定、独立预期；待C确定API后补专属测试 |
| F烟气准备 | 原carbon_material_fume_segments.py/test_b_fume_segments.py | 557f2c6准备补丁保留，最新main静态兼容核对完成并停止，不接本包 |

I单批单有效组分且通用绑定适用才新建初始化90%；多组分不复制90%，空行不计有效组分，已填未完行不忽略。TR通用100%绑定独立C.2。EF真实精确C.2绑定锁定，否则批准实测，不猜物种。实测空白不回缺省，单多单保留草稿且不重标旧缺省。同批整剂分母校验，不跨批合并、不归一、不重复乘用量；设施/批次/组分用稳定身份。

## 平台 / Contract 预检查

origin已实际核实adgo07/GHGTOOL，fetch后从最新origin/main建立干净隔离codex/b-fgd-integration，默认main。locked central SHA ee5feb0cc34dbd99790500fadd0c4c932e202a20不变；Architecture V2.1、Numeric v1及Profiles v1按该SHA读取，UI v0.2按当前ACTIVE读取。MUST：分层、共享内核、declared-profile consistency、ambient independence、full-value exact、历史不漂移。MUST NOT：未声明float、隐式修约/业务epsilon、算法复制、自动升级Frozen、Qt状态充当公共Workspace。p40/HALF_UP属ALLOWED PROJECT DIFFERENCE；无中央Contract冲突，无需修改中央Contract。相关Standard Issue016，落实已有软件决定，不改变既有解释。

## 授权与验收边界

Owner已授权下一包及既有M/F/源协调、私有push/PR/CI。完成单一脱硫PR与最终head CI/实际包后送源独立验收，停止；不合并、不CU、不删除旧工作树、不公开上传、不商业发布。必要模板演进机械生成并保留旧字节，能复用v7则复用。原生Office/鼠标/中文IME/人工DPI/企业样例/干净目标机/商业履约仍OPEN。本包尚未运行测试，不宣称PASS或SUPPORTED。
