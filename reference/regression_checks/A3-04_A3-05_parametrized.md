# A3-04 / A3-05 固定 Fixture 参数化回归记录

日期：2026-10-18。运行环境：Python 3.10.12、pytest 9.1.1。

## 测试组织与冻结依据

[test_reference_cohort.py](../../tests/test_reference_cohort.py) 将原有两个独立测试整理为 `test_reference_matches_frozen_boundary_fixture`，使用 `pytest.mark.parametrize` 收集 `[A3-04]`、`[A3-05]` 两个实例；没有重复保留旧测试来增加测试数量。原先的6项参考计算测试不变，因此该文件仍为8项，全量仍为78项。

每个实例直接将固定 Fixture 的 `input` 传给既有 [calculate_reference()](../cohort.py)，复用 `assert_matches_static_expected()` 比较结果状态、原因、参考函数实际提供的成熟/水位检查、两窗 N/U/率及两项变化。另与已人工列举的候选订单集合比对，并检查整个内存 Fixture 在测试后未被修改。

冻结依据继续使用 [A3-04](../../tests/fixtures/order_boundaries/04_zero_denominator_window.json)、[A3-05](../../tests/fixtures/order_boundaries/05_single_region_filter.json) 和 [ORACLE.md](../../tests/fixtures/order_boundaries/ORACLE.md)。不使用参考函数输出生成或回填任何预期。[2026-10-16 初始运行记录](A3-04_A3-05.md) 保持原样，其中的旧测试名称及运行结果是当时证据。

## A3-04：诊断与发布结果分开核验

- 参考函数实际返回的候选集合为基期 `[]`、当前 `[Z-C-1,Z-C-2]`，与人工集合一致。
- 发布结果为 `insufficient_evidence`，唯一原因“支付窗口无有效样本”；两窗发布 N/U/率、绝对变化和相对变化均为 null，成熟与两类水位检查与冻结预期一致。
- 测试侧 `assert_a3_04_input_diagnostics()` 只针对此固定样例，从原始输入独立检查域/快照一致性及全域过滤前提，再按有效支付和 `[start,end)` 取订单；按同一订单关联成功退款，要求退款时间在 `[paid_at,paid_at+H]` 且不晚于 as_of，以订单集合计数。同单多笔退款不增加 U，零分母时不作除法。
- 该局部核验得到基期 N=0/U=0/率=null，当前 N=2/U=1/率=1/2，并分别核对冻结的诊断计数、退款订单集合和率。它不接收或读取参考函数结果，也不实现成熟/水位处置、错误映射或通用 Oracle。
- `diagnostic_cohort_metrics` 只从 Fixture 的 `expected` 读取。未访问 `actual["diagnostic_cohort_metrics"]`，未给参考函数补造该返回字段，未把诊断值混入发布结果。

## A3-05：单地区与精确数值

输入仍固定筛选西北。候选订单为基期 `[F-N-B1,F-N-B2]`、当前 `[F-N-C1]`；结果为 `ready`，无不足原因，成熟和水位检查与静态预期一致。

基期 N=2/U=1/率=1/2，当前 N=1/U=1/率=1，绝对变化=1/2，相对变化=1。测试既对照冻结字符串的精确数值，也明确检查率和变化的返回类型为 `Fraction`，不使用浮点近似。

## 运行命令与实际结果

在开发工作树根目录运行：

```bash
.venv/bin/python -B -m pytest tests/test_reference_cohort.py::test_reference_matches_frozen_boundary_fixture -o addopts='' -v -p no:cacheprovider
# test_reference_matches_frozen_boundary_fixture[A3-04] PASSED
# test_reference_matches_frozen_boundary_fixture[A3-05] PASSED
# 2 passed

.venv/bin/python -B -m pytest tests/test_reference_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
# 13 passed

.venv/bin/python -B -m pytest -o addopts='' -q -p no:cacheprovider
# 78 passed
```

全量测试按此前 API 测试的运行方式，在获授权的沙箱外执行。上述数量属于当前开发工作树，包含本地 Provider 单测，不冒称已在公开分支运行。`git diff --check` 通过。

## 公开提交前回归

提交前在脱敏公开工作树使用同一开发环境的 Python 解释器执行全量 pytest，参数为 `-B -m pytest -o addopts='' -o pythonpath=src -q -p no:cacheprovider`，实际结果为73项通过。`pythonpath=src` 明确指向公开工作树源码，避免误用开发工作树的安装路径。公开快照不含本地 Provider 实现及其5项测试，因此与开发工作树78项的差额为5，不是测试失败或丢失本轮两个参数化实例。

## 静态文件保护与边界

变更前后使用 `sha256sum` 核对，以下文件保持一致：

| 文件 | SHA-256 |
| --- | --- |
| `04_zero_denominator_window.json` | `5d2da96ec1dded382eb454fe68ee24f6bedaffeffbd45887e3526072a7d924c2` |
| `05_single_region_filter.json` | `d9f621f17385f2b7dcf2e58da70f79627adbf850e56e419f17de7e8baa233da8` |
| `ORACLE.md` | `40e680dac3007cec3c23302fc78d39f62e203973c773d9832585db02d00b4fc8` |
| `reference/cohort.py` | `13b5ced6824c1b8548eaa55b8014f4f87c35562fbe24eead2f0408afbefa96c6` |
| 初始回归记录 `A3-04_A3-05.md` | `e1a88c0cfb285b0cd8b31c958e36dcab002bff789debb75db2d56607edd0bece` |

本地 Provider 实现及测试也未修改。不引入依赖或框架，不修改参考函数、静态预期或历史人工记录。本次只验证固定合成 Fixture 的回归，不代表生产 SQL、地区授权、批次 DQ 或调查系统已验收，不替代用户独立人工复核。
