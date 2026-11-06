# A3-11 C05：控制变体的独立预期

日期：2026-11-05。先依据[DD02 §2](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)、[已冻结实施契约](A3-11_channel_oracle_plan.md)和[逐单输入复核](A3-11_input_review.md)直接填写[控制预期JSON](A3-11_C05_expected.json)，随后才编写/运行C05。没有调用参考或生产函数生成答案；已读过现有实现，不声称首次盲审或用户本人签字。原A3-11_expected.json及11号Fixture不改。

西北基期支付为K11-N-B-W1/W2/A1三单，当前为K11-N-C-W1/A1/A2/A3四单。最后一单K11-N-C-A3于09-12零点支付，H=604800秒，成熟时刻为2026-09-19T00:00:00Z；支付窗口最大end为09-15零点。原as_of及退款水位为09-23，支付水位为09-15。以下控制均从这一合法输入单独深拷贝，保持域、快照及西北过滤不变。

| 控制 | 唯一业务变更 | 独立预期 |
| --- | --- | --- |
| immature | as_of=09-18T23:59:59.999999Z | 7天观察少1微秒，仅all_orders_mature=False；insufficient_evidence，原因观察期未成熟 |
| payments_below | payments_through=09-14T23:59:59.999999Z | 窗口末端覆盖少1微秒，仅支付水位标志False；insufficient_evidence，原因支付水位不足 |
| refunds_below | refunds_through=09-18T23:59:59.999999Z | 最大成熟时刻覆盖少1微秒，仅退款水位标志False；insufficient_evidence，原因退款水位不足 |
| empty_baseline | 全部三笔西北基期支付设无效 | 基期候选为空、当前四单保留；三个成熟/水位标志仍True，但insufficient_evidence，原因支付窗口无有效样本 |
| maturity_equal | as_of=09-19T00:00:00Z | 恰满7天允许ready，复用原冻结六行和变化 |
| payments_equal | payments_through=09-15T00:00:00Z | 恰覆盖窗口end允许ready；复用原合法输入已有正例及原预期，不算新主Fixture |
| refunds_equal | refunds_through=09-19T00:00:00Z | 恰覆盖西北最大成熟日允许ready，复用原冻结结果 |
| zero_baseline_refunds | 只移除KR11-N-B-A1 | 基期N=3/U=0，当前N=4/U=3，ready；总体率0→3/4、绝对变化3/4，相对变化null |

时间均为2026年UTC；第一、三项与各自等号控制只差1微秒，其他门槛仍成立。东南最晚09-21才成熟，但它不属于西北候选队列，不能要求西北成熟/退款水位额外覆盖东南。关键产品关联仍完整，C04的全输入关键关联检查规则并未改变。

四个不足控制的正式发布结果一律为：两窗N/U/rate和两类变化全部null，aggregate_rows=[]、group_order_ids={}、group_refunded_order_ids={}。候选订单只作诊断；空基期不允许发布当前正常值，也不能将0/0当0。本组控制是合法结构下比较前提不足，期望返回insufficient_evidence，不把它们与关键关联ValueError或生产blocked_by_quality混为一谈。

零退款正例保留全部有效支付、完整成熟水位，只移除唯一西北基期退款KR11-N-B-A1。东南基期KR11-S-B-W1仍存在且必须排除；基期网页N=2/U=0、移动应用N=1/U=0，总计N=3/U=0、率0。当前仍为网页1/1/率1、移动应用3/2/率2/3、总计4/3/率3/4。由集合直接得绝对变化3/4−0=3/4，基期率0时相对变化不可定义，因此为null；**相对变化null不应使ready整体被阻断**。

JSON中blocked_publication为四个不足控制共享的静态发布预期，三个等号控制明确复用原先行冻结结果，零退款的六行和变化另以静态字面值保存。不从待测返回值构造这些预期，也不将新控制数值回写原Fixture。

本记录只确定控制预期，实际测试结果、指纹和剩余覆盖另追加至[渠道回归记录](../regression_checks/A3-11_channel.md)。
