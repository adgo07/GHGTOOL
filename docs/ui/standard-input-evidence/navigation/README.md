# 导航性能基准证据

本目录留存原版 d36 基线的可恢复计时摘要，以及当前开发工作区一次完整的 after JSON 输出。数据均为临时合成数据，未读取或写入用户数据库。

## d36 原版基线

原始完整 JSON 和精确 CLI 命令没有保存在当前工作树，也未能从现有证据文件中恢复；baseline-summary.md 仅记录此前实际保留的计时摘要，**不是完整 JSON，也不补造未留存字段**。当时记录的源 HEAD 为 d36e50c89b87542ab83f63586dd5f6bad243134b，数据规模为 200 条合成记录、20 个合成项目。

## 开发中间版本

第一次摘要查询接线之后、批量行分配与重复方法清理之前，另一次实测冷点击返回为 1103.331 ms、缓存重访中位数为 742.773 ms。该结果属于保留重复 _workspace_associations 定义的慢中间实现，**不是 d36 原版基线**，也不是最终 after。

## 当前 after

after.json 是最终工作区的一次完整 JSON stdout。运行时间：2026-10-14 20:11:49 +08:00；解释器：Python 3.12.14；源 HEAD：d36e50c89b87542ab83f63586dd5f6bad243134b。HEAD 未变，但工作区有未提交修改，故此结果由下列源码文件 SHA-256 共同标识。启动页数在 AppShell 构造函数返回后立即快照：1 页；首次进入记录页后为 3 页。

命令（PowerShell；本次只启动一次，stdout 同时保存为 after.json）：

    .\.venv\Scripts\python.exe tests/benchmark_navigation.py --records 200 --projects 20 --repeats 5

实跑时使用 Tee-Object -FilePath docs/ui/standard-input-evidence/navigation/after.json -Encoding utf8 保存完整输出。脚本创建 200 条合成核算记录和 20 个合成项目；记录列表返回 200 行。冷首次点击返回 302.465 ms、首次绘制 317.29 ms；缓存重访点击返回中位数 93.682 ms；同路由点击返回 0.379 ms。各计时单位均为毫秒，指标定义见 tests/benchmark_navigation.py。

| 工作区源码/脚本 | SHA-256 |
| --- | --- |
| packages/ui/pages.py | 87D7958F2A922B3F094F6911702543F6447408D15D97808C93C8084501EA3DCF |
| packages/ui/shell.py | DEA92F63B0C6E4CE6651960B640FBD350BDC7249D8BFBB4285B476DFFC8C0732 |
| packages/persistence/records_repository.py | E70C90F79A81757A8DB1416BDDB6CEB296651801D4D1941D29734CF8E06D030A |
| packages/core/repositories.py | 2C065FA24D23A6E97F8157EFF6DD16147470A108A8D8CD447FA20553B6820E3B |
| packages/persistence/in_memory_records.py | 31DC5A1396D37DF7FD097373B5C6B3303251FCFFF7C4720FD0822EE16BEEE75A |
| packages/core/record_summaries.py | 771B728395514FB41C32AEEED75929D7647E19B9B08524486FF47AE214DBA16F |
| tests/benchmark_navigation.py | 43ABCC70F6F65BB8FD969A2719C74322A2FC1D19D6786DB5B05AEC5E9C67D384 |
| tests/test_record_summaries.py | 829E586536E271DBF4A5E8670D7D8A54C3B87CF9872FA780302196D933AAFC21 |
| after.json | 53449EC40683E80BCE25C821F6CC3402CE51D09131B5C23EED3FC246512AC21B |
