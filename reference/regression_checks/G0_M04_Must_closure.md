# M04 退款 DQ 参考层局部验收

2026-11-23（Asia/Shanghai）。**M04 首批三类关键退款 DQ 及缺失时间控制通过复验，最小参考层 Must 局部关闭。** 四项负例各自触发预期的 `ValueError`，阻断正常比较结果。[人工验收清单](../manual_checks/G0_M04_refund_dq_acceptance_plan.md) · [专项测试](../../tests/test_reference_refund_dq.py)

| 验收项 | 本轮直接证据 |
| --- | --- |
| M04-01 重复退款事件键 | 同一完整退款事件键对应两条来源行，抛出 `ValueError("重复退款事件")` |
| M04-02 孤立退款 | 退款的完整订单键在当前域和快照查无支付记录，抛出 `ValueError("孤立退款")` |
| M04-03 支付前退款 | 退款时刻早于所属订单支付 1 微秒，抛出 `ValueError("退款早于支付")` |
| 缺失必需退款时间 | 从 A3-07 深拷贝，仅删除 `r07-refund-a-c1` 的 `refund_at`。入口抛出明确的 `ValueError`，包含 `refund_id=SR-A-C1` 和该来源行 |
| A3-06 合法对照 | 同单多个不同事件键仍只计一个退款订单，基期 `N=2/U=1`、当前 `N=2/U=2` 与冻结预期一致 |

三份落盘变体的单故障、完整键、来源和水位由静态核验确认。四个运行用例均断言对应异常及输入不变性。缺失时间修复前的 `KeyError` 及修复后的明确拒绝保留在历史记录中。[变体静态核验](G0_M04_refund_dq_variants.md) · [缺失时间修复前后记录](G0_M04_missing_refund_time_pytest.txt)

## 实际执行与版本绑定

以下三轮在本地开发工作树独立执行，使用 CPython 3.10.12、pytest 9.1.1。命令、原始输出、退出码及执行文件和输入 SHA-256 已保存。执行记录 SHA-256 为 `017deb048560167ae045c280e0498df0849fbe06b24a0d3bdefccdb4d5d0d9b3`。[原始执行记录](G0_M04_Must_closure_pytest.txt)

| 范围 | 通过 | 退出码 |
| --- | ---: | ---: |
| M04 专项 | 4 | 0 |
| 既有总体参考，含 A3-06 | 9 | 0 |
| 相关分组、跨域、贡献及静态 Fixture | 173 | 0 |

```bash
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_reference_refund_dq.py -rA -o addopts= -q -p no:cacheprovider
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_reference_cohort.py -rA -o addopts= -q -p no:cacheprovider
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_reference_category_cohort.py tests/test_reference_channel_cohort.py tests/test_reference_region_cohort.py tests/test_reference_cross_domain_cohort.py tests/test_reference_contribution.py tests/test_boundary_fixtures.py -o addopts= -q -p no:cacheprovider
```

公开对照基线为 `fdee386`。原总体和分组测试、A3-06/A3-07 与已提交规则文件均匹配该版本。修复后参考入口、专项、三份变体及本地配置按实际 SHA-256 绑定。执行记录另列 A3-06、A3-07、三份落盘变体以及内存构造的缺失时间输入的规范化指纹。所有绑定文件在执行前后逐字节一致。

本次局部关闭以参考入口抛出异常为验收行为。人工预期中的 `blocked_by_quality` 生产状态映射仍未验收，交由 M06 验证。金额类规则待契约定义，G0 整体验收独立登记。[覆盖矩阵](G0_fixture_coverage.md)
