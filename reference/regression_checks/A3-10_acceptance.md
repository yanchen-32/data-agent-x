# A3-10 最终交付与验收状态核对

核对日期：2026-10-30。结论：已提交参考层修复与既有红绿灯证据一致；冻结输入及台账指纹匹配。参考层能力已交付，生产DQ状态映射尚未实现；用户本人独立人工验收待明确确认，不因测试通过或本次核对自动完成。

## 固定提交及证据来源

本次核对公开提交 [d7b702a6ea517d5e3e0ff437d39c714e8155023c](https://github.com/yanchen-32/data-agent-x/commit/d7b702a6ea517d5e3e0ff437d39c714e8155023c)，父提交为2ca58427b05d16bbae0dfbda3ccf4e9d09604d8e。通过`git show <commit>:<path>`读取已提交对象，权威回归记录为 [该提交的reference/regression_checks/A3-10.md](https://github.com/yanchen-32/data-agent-x/blob/d7b702a6ea517d5e3e0ff437d39c714e8155023c/reference/regression_checks/A3-10.md)，不把本地开发记录副本与公开记录互换。

本地公开工作树干净，分支release/public-v1.2.1与本地origin/main跟踪引用均指向所核提交。本轮未连接远程刷新引用，不将跟踪引用冒称实时远程查询；状态仅对应上述固定提交，不推定未来main内容。

## 已交付的参考层能力

- 所有提供给类别参考函数的订单，按完整`(domain_id,snapshot_id,product_id)`核对产品实体关联；检查位于目录核验之后、比较前提不足的提前返回之前。
- 缺失产品复合键抛出`ValueError`，带order_id、source_row_id及完整产品键，不正常返回含`__unknown__`的业务结果。A3-10故障明确为J10-C2 / r10-row-c2 / (domain_a,fixture_missing_product_join,product_missing)。
- ready和immature两种前提下均有拒绝检查，不能用其他比较前提不足绕过关键关联检查。
- 合法产品存在但category_id=null时仍保留未知组；已知类别ID缺展示名时保留原ID、label=None。目录重复键及域/快照混入仍拒绝。
- 原“缺失产品也作为合法未知”的冲突变体已更正为拒绝测试，非关键类别缺失测试继续保留；没有修改冻结答案消除失败。

这些结论来自已提交源码、测试断言和历史执行记录的只读核对，本轮没有导入或调用参考函数，也没有执行pytest。

## 冻结与实现指纹

以下SHA-256均从所核提交对象重新计算。A3-10两项冻结指纹与拒绝测试中的常量一致；A3-09的两项指纹仍由其原固定回归绑定。本地对应五份文件亦与提交对象逐字节一致。

| 对象 | SHA-256 |
| --- | --- |
| A3-10 Fixture：10_missing_product_join_blocks.json | 4f2b8b097451cdbf2c3b7f97ff115235c58dea2de2a45b147d93a02bf0371cc3 |
| A3-10独立台账：reference/manual_checks/A3-10.json | ce3e4aca7f5213792f0936df40bf61acb7505e84ad4bcbc8c7937845347b4fde |
| 修复后reference/category_cohort.py | 53507d6ba6671e7ca7ca6cd4f955fa345b53be73bf98edf5fd638d5206f2b216 |
| A3-09 Fixture：09_unknown_category_preserved.json | d9677959c20e91b6965e984035742a6524592896fbf9ce40728192a43bd8439e |
| A3-09先行预期：reference/manual_checks/A3-09_expected.json | 07dca84a024330d35ff1bfb68ff8159d2d7cf52a953926ee76afd1e07b7ae35f |

另核对已提交测试文件SHA-256为`f5be1f6e7740ed43f26231eaa62d51f75b59d4e16baf2e26821b71becd0387a5`，公开A3-10回归记录SHA-256为`4ad38a58613f1aee60340d8c8c4603cbbcfbb8ca47cbefe4a3adb2dbc4ee0356`。父提交的旧参考实现指纹仍为`9d1d11414f25bcfb61cb79b16e2a4c75d067c54e032c7a5fdd1e95b5456e78ba`，与历史更正说明一致；不回写旧记录的指纹。

## 红绿灯和兼容性证据登记

以下均为已提交记录中的2026-10-29本地执行证据，不是本轮重跑，不是CI或GitHub Actions结果：

| 历史阶段与范围 | 已记录结果 | 本次核对结论 |
| --- | --- | --- |
| 修复前新增固定拒绝测试 | 1 failed，36 deselected，0.11s；DID NOT RAISE ValueError | 真实红灯被保留；旧ready/unknown行为仅作错误诊断，非Oracle预期 |
| 修复后开发工作树 | 拒绝3 passed；兼容9 passed；相关67 passed；全量132 passed | 与原始命令及输出一致，含5项未公开Provider测试 |
| 修复后公开工作树 | 拒绝3 passed；兼容9 passed；相关67 passed；全量127 passed | 独立实际运行记录，不从132减5推算 |

兼容9项中明确包含A3-09固定冻结Oracle、合法category_id缺失、缺展示目录、两类目录重复键及域/快照混入四种组合。相关67项=38项分组参考计算+9项总体参考计算+20项静态检查；各专项与相关均为全量子集，不重复相加。

记录中的环境为CPython 3.10.12、pytest 9.1.1；公开运行显式使用PYTHONPATH=src，全量获准在沙箱外本地执行。历史通过数量不能当作CI状态，也不证明其他环境通过。本轮不触发、查询或推定CI结论。

## 尚未交付与本人独立验收状态

| 项目 | 最终登记 |
| --- | --- |
| A3-10参考层关键产品关联拒绝 | 已交付，有既有红灯→修复→绿灯证据 |
| A3-09合法未知类别兼容 | 有既有通过证据，冻结文件与原断言保留 |
| 冻结预期 | 仍为blocked_by_quality；两窗N/U/率与变化均null，aggregate_rows为空、归组台账为空 |
| 生产DQ状态映射 | 未实现；参考函数抛ValueError，不返回正式blocked_by_quality对象 |
| HTTP/API、DQ Adapter、数据库导入、任务状态机与恢复条件 | 不在本次参考层交付范围，未验收，不能由ValueError拒绝代替 |
| 用户本人独立人工验收 | 待本人独立复核并明确确认；当前核对请求不作为签字或已验收声明 |
| 首次盲审或第二位独立审核者签字 | 不宣称，原独立性限制保留 |
| CI / GitHub Actions | 本轮未运行或核验，不登记为通过 |
| 本状态记录 | 本地新增，尚未提交或推送，不据此修改路线图完成状态 |
