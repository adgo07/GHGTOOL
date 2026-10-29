# PR62 家族 UI 统一：CI317夹具退修15项通过，待新headCI

2026-10-29。PR：[GHGTOOL #62](https://github.com/adgo07/GHGTOOL/pull/62)，分支 `codex/ghg-family-ui-unify`；修复起点已推送head `bb9c8040785897d1fcae5a5106fad596c7f2f803`。本文件为稳定修复提交前快照，新head及完整CI/包回执以PR最新交付记录为准。未合并。Owner授权同一PR修复、低风险测试瘦身及稳定批次push；最后交源独立验收，通过后通知Owner。

## 当前事实

- 最新CI317 / run40806310497：独立GUI15秒、两档scale28秒通过；全量1133项1139.059秒，**14 errors / 0 failures**，均为SourceDirectoryTests缺catalog_path的setup错误。Standalone依赖跳过，无精确head包。14项业务体未执行，不能把19分钟误称完整性能目标达成。
- 原输出协议问题已在CI三档100%/125%/150%实际DPR全部通过，各14.130/14.409/14.451秒；60秒保护未提高。
- 本轮夹具复用遗漏了借用setUp的SourceDirectoryTests。现补齐该类独立catalog的class初始化/结束校验与清理，所有14个原测试体不变；同进程14项+原项目夹具1项已15/15通过，288.347秒，0失败/0错误；两类catalog哈希校验与清理通过。已搜索全部借用者，无其他消费者。
- 前一稳定批次本地Python3.12.14/PySide6 6.11.2：66个不同定向用例通过；项目/FGD/Excel组41/41（974.358秒），家族/壳24/24（224.698秒），最终三档父例1/1（149.765秒），扣边距正文补验1/1（15.138秒）。未冒称覆盖遗漏的14项。
- 最终6张Qt图760869字节及源/Git树/图像hash已入仓；全尺寸图、执行脚本快照、CI317原始失败日志在外部持久归档。23个预着色SVG保留，受控生成/来源hash在CRLF和Git LF检出均通过。共享样式集中化，迁移进行中。

## 边界与下一步

不改标准范围/解释、Calculator、Canonical、项目保存、正式Record、迁移、中央Frozen或产品源码apps/packages/resources。锁定central SHA `ee5feb0cc34dbd99790500fadd0c4c932e202a20`；本任务不涉及中央公共Contract，无新Standard Issue。未触碰用户已有数据/修改，无Goal，无桌面CU。

真实失败入口本地验证已完成；再一次稳定修复push；不直接重跑旧head取绿，不提高40分钟预算、不改required范围。后续核实两required、精确head build/audit/archive/provenance/smoke/upload及artifact ID/name/size/digest。最终回执以PR最新交付记录为准。本轮本地全量、真实桌面/多屏/IME/Office/干净机未验；源独立验收未完成，不自动合并。

## 历史定位

CI313缩放工作区配置失败；CI314/315超时，已移除MainWindow应用全局滚轮过滤器；CI316全量1133项1587.264秒唯一失败为输出协议。本轮CI317的新夹具错误独立记录，不用旧CI或19分钟失败运行充当成功。历史实施详单从Git恢复，本文件以上述当前事实为准。
