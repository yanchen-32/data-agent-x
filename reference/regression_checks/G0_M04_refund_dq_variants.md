# M04 三项单故障变体静态核验

2026-11-23（Asia/Shanghai）。三份 JSON 分别由 A3-07 的冻结 `input` 深拷贝生成。每份只施加已提交人工清单指定的一项变更。基线输入与清单均与公开提交 `fdee38637864f20f6a035432e51eb611fed53e30` 的文件字节一致。[A3-07](../../tests/fixtures/order_boundaries/07_same_label_distinct_category_ids.json) · [人工验收清单](../manual_checks/G0_M04_refund_dq_acceptance_plan.md)

| 变体 | 静态核验结果 |
| --- | --- |
| [M04-01 重复退款复合键](../fixture_drafts/m04_01_duplicate_refund_event.json) | 只追加一行，副本与原行只有来源 ID 不同。完整事件键 `(domain_a, fixture_same_label_categories, SR-A-C1)` 重复 **1 组**，来源为 `r07-refund-a-c1` 和 `m04-01-refund-a-c1-duplicate`。两行均能关联 `S-A-C1`，退款时刻合法 |
| [M04-02 孤立退款](../fixture_drafts/m04_02_orphan_refund.json) | 只更改 `r07-refund-a-c1` 的 `order_id`。完整订单键 `(domain_a, fixture_same_label_categories, S-M04-MISSING)` 查无支付，孤立退款 **1 笔**，事件键与来源仍唯一 |
| [M04-03 支付前退款](../fixture_drafts/m04_03_refund_before_payment.json) | 只更改 `r07-refund-a-c1` 的 `refund_at`，时刻为 `2026-09-08T23:59:59.999999Z`。关联支付来自 `r07-row-a-c1`，时刻为 `2026-09-09T00:00:00Z`。早 **1 微秒**，支付前退款 **1 笔**，完整键与归属均合法 |

静态核验重新读取落盘 JSON，比对原始订单、目录、Scope、退款行差异以及故障个数。三份输入的支付订单键和目录复合键均唯一，产品、类别、地区及渠道关联均完整。支付与退款来源 ID 在各自输入中唯一，时间均可解析为带 UTC 标记的时刻。基期、当前有效候选支付分别为 2、4 笔。最晚成熟为 2026-09-19，支付水位 2026-09-15 恰好到达两窗的最晚末端，退款水位和 `as_of` 均为 2026-09-23。除表中的单一故障，事件身份、订单归属及相关时间校验均满足各自条件。

在 CPython 3.10.12 下通过 `python3 -B -` 执行标准库静态检查，三份落盘变体均匹配人工清单，退出码为 `0`。核验前后原 Fixture、清单和三份变体逐字节一致。三项业务阻断预期仍以已提交人工清单为准。当前证据范围为输入和单故障一致性，参考层拒绝回归与生产 DQ 验收另行登记。

| 对象 | 完整文件 SHA-256 | 规范化 `input` SHA-256 |
| --- | --- | --- |
| A3-07 | `e03a1c005e6f99f5e497e452bb3de5e75aa2096f83106f730a45ebcbbec737ac` | `cb458cfb0bc5555c8c680bab64885c0f2fd2e212951a12143260eb9ea3e339ca` |
| M04-01 | `56f61c74eb07b6df94e294a68f32791eb4f0f4c9ad8d6eee6e3934d10967952e` | `f7f283466f32ce5988308ffb3a8a4830fa8350277c3d3991e81b681efc336fdc` |
| M04-02 | `0787622080be1bd10a8a10e2a8e83bec42201671edc5981da3fff26aae68c226` | `2b3a809d80d621ea49b6f96b1796c00242df0632393596a6131cdcd61eb40151` |
| M04-03 | `cb8a24516c2792db82653a07c848cdcee36565212a71a336e843ed6955605d1a` | `0a0c4aa78e58ddede8b851d5c8b44074a399114127f0d31c47e53da9a28b20b1` |

清单文件 SHA-256 为 `6e8edd62e902f9417a46b84278d5eb8ccffea4d63937441580665a375747d784`。`input` 按 UTF-8、对象键排序、紧凑分隔和原有数组顺序计算指纹。
