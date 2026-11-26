# M05 A3-10 本人独立核验表｜产品关联与关键质量检查

2026-11-26（Asia/Shanghai），按用户委托由独立子进程完成初算，依据为下方原始输入和冻结规则。初算原稿已保存。请在下方对照区填写最终核查结果。

## 冻结规则
- 支付按 UTC 的半开窗口 `[start, end)` 归属。每笔入窗订单须在 `as_of` 时完成 7 天观察期，支付水位须覆盖窗末，退款水位须覆盖窗口内最晚观察截止。
- 退款按 `(domain_id, snapshot_id, refund_id)` 标识，通过 `(domain_id, snapshot_id, order_id)` 关联支付。成功事件须处于 `[paid_at, paid_at + H]` 内且 `refund_at <= as_of`。每窗支付订单数为 N，有合格退款的去重支付订单数为 U，率用精确的 U/N。
- 类别归组先按 `(domain_id, snapshot_id, product_id)` 查产品，再按类别 ID 聚合。合法产品关联上的非关键未知类别用 `__unknown__`，保留其订单和退款来源。关键关联错误须阻断发布。

规则依据。[DD02 §1–2](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md#data) · [指标目录](../../docs/engineering/02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)

## 原始输入

来源为 `tests/fixtures/order_boundaries/10_missing_product_join_blocks.json` 的 `input`。整文件 SHA-256 为 `4f2b8b097451cdbf2c3b7f97ff115235c58dea2de2a45b147d93a02bf0371cc3`，规范化输入 SHA-256 为 `4966e1e7b68ac237d88cbce97f511c2d5cc62bdd301183d567d4bd4be8e627a1`。

各行共用域 `domain_a` 和快照 `fixture_missing_product_join`。指标 `refund_rate_order_horizon`，时区 `UTC`，地区过滤 `[]`，观察期 604800 秒。

| 字段 | 原值 |
| --- | --- |
| `baseline.start` | `2026-09-01T00:00:00Z` |
| `baseline.end` | `2026-09-08T00:00:00Z` |
| `current.start` | `2026-09-08T00:00:00Z` |
| `current.end` | `2026-09-15T00:00:00Z` |
| `as_of` | `2026-09-23T00:00:00Z` |
| `payments_through` | `2026-09-15T00:00:00Z` |
| `refunds_through` | `2026-09-23T00:00:00Z` |

### 支付订单

| source_row_id | order_id | product_id | region_id | channel_id | paid_at | is_payment_valid |
| --- | --- | --- | --- | --- | --- | --- |
| `r10-row-b1` | `J10-B1` | `product_known` | `region_northwest` | `channel_web` | `2026-09-02T00:00:00Z` | `true` |
| `r10-row-b2` | `J10-B2` | `product_known` | `region_northwest` | `channel_web` | `2026-09-04T00:00:00Z` | `true` |
| `r10-row-c1` | `J10-C1` | `product_known` | `region_northwest` | `channel_web` | `2026-09-09T00:00:00Z` | `true` |
| `r10-row-c2` | `J10-C2` | `product_missing` | `region_northwest` | `channel_web` | `2026-09-12T00:00:00Z` | `true` |

### 退款事件

| source_row_id | refund_id | order_id | refund_at | status |
| --- | --- | --- | --- | --- |
| `r10-refund-b1` | `JR10-B1` | `J10-B1` | `2026-09-04T00:00:00Z` | `success` |
| `r10-refund-c2` | `JR10-C2` | `J10-C2` | `2026-09-14T00:00:00Z` | `success` |

### 产品目录

| product_id | category_id |
| --- | --- |
| `product_known` | `category_a` |

### 类别目录

| category_id | label |
| --- | --- |
| `category_a` | `已知类别A` |

### 地区目录

| region_id | label |
| --- | --- |
| `region_northwest` | `西北` |

### 渠道目录

| channel_id | label |
| --- | --- |
| `channel_web` | `网页` |

## 独立子进程初算

冻结范围为 `domain_a`、`fixture_missing_product_join`，时区 UTC，`H = 604800` 秒，`filters.region_ids = []`。基期支付窗口为 `[2026-09-01T00:00:00Z, 2026-09-08T00:00:00Z)`，当前窗口为 `[2026-09-08T00:00:00Z, 2026-09-15T00:00:00Z)`。四笔订单的支付均有效，地区和渠道键均各自匹配一行。

| 支付来源行 | 订单完整键 | 待匹配的产品完整键 | 精确匹配的产品数 | 质量判断及依据 |
| --- | --- | --- | ---: | --- |
| `r10-row-b1` | `(domain_a, fixture_missing_product_join, J10-B1)` | `(domain_a, fixture_missing_product_join, product_known)` | 1 | 基期，`paid_at = 2026-09-02T00:00:00Z`，截止 `2026-09-09T00:00:00Z`。产品与类别 `category_a` 关联成功。 |
| `r10-row-b2` | `(domain_a, fixture_missing_product_join, J10-B2)` | `(domain_a, fixture_missing_product_join, product_known)` | 1 | 基期，`paid_at = 2026-09-04T00:00:00Z`，截止 `2026-09-11T00:00:00Z`。产品与类别 `category_a` 关联成功。 |
| `r10-row-c1` | `(domain_a, fixture_missing_product_join, J10-C1)` | `(domain_a, fixture_missing_product_join, product_known)` | 1 | 当前，`paid_at = 2026-09-09T00:00:00Z`，截止 `2026-09-16T00:00:00Z`。产品与类别 `category_a` 关联成功。 |
| `r10-row-c2` | `(domain_a, fixture_missing_product_join, J10-C2)` | `(domain_a, fixture_missing_product_join, product_missing)` | 0 | 当前，`paid_at = 2026-09-12T00:00:00Z`，截止 `2026-09-19T00:00:00Z`。完整键下缺少产品记录，必需关联失败。 |

| 退款来源行 | 退款完整键 | 指向的订单完整键 | 匹配与时间检查 |
| --- | --- | --- | --- |
| `r10-refund-b1` | `(domain_a, fixture_missing_product_join, JR10-B1)` | `(domain_a, fixture_missing_product_join, J10-B1)` | 唯一回连 `r10-row-b1`，状态 `success`。`2026-09-02T00:00:00Z ≤ 2026-09-04T00:00:00Z ≤ 2026-09-09T00:00:00Z ≤ 2026-09-23T00:00:00Z`，分别为支付、退款、观察截止、`as_of`。 |
| `r10-refund-c2` | `(domain_a, fixture_missing_product_join, JR10-C2)` | `(domain_a, fixture_missing_product_join, J10-C2)` | 唯一回连 `r10-row-c2`，状态 `success`。`2026-09-12T00:00:00Z ≤ 2026-09-14T00:00:00Z ≤ 2026-09-19T00:00:00Z ≤ 2026-09-23T00:00:00Z`，分别为支付、退款、观察截止、`as_of`。 |

首个足以判定阻断的质量问题发生在 `r10-row-c2`。订单完整键 `(domain_a, fixture_missing_product_join, J10-C2)` 所引用的产品完整键 `(domain_a, fixture_missing_product_join, product_missing)` 匹配数为零。产品表在该域和快照只有 `product_known`，其类别 `category_a` 有对应记录。此处判定为订单到产品的必需关联缺失，触发关键质量阻断。

两笔退款的事件键各自唯一，订单关联与时间检查均通过。基期最晚观察截止 `2026-09-11T00:00:00Z`，当前最晚观察截止 `2026-09-19T00:00:00Z`，均由 `as_of = 2026-09-23T00:00:00Z` 和退款水位 `2026-09-23T00:00:00Z` 覆盖。支付水位 `2026-09-15T00:00:00Z` 覆盖基期末端且等于当前窗口末端。退款关联、成熟和水位均通过独立检查，关键质量阻断仍决定调查结果。

| 结果项 | 业务状态 | 发布值 |
| --- | --- | --- |
| 基期退款率 | 关键质量阻断，无可发布指标 | `null` |
| 当前退款率 | 关键质量阻断，无可发布指标 | `null` |
| 两窗变化 `Δrate` | 无可比的两窗指标 | `null` |
| 两窗相对变化 | 无可比的两窗指标 | `null` |
| 两窗总计、N/U、类别分组和贡献 | 指标聚合在质量检查处停止 | 无发布数据 |

合法类别未知以订单成功关联唯一产品为前提，产品记录的 `category_id` 为空时可归入 `__unknown__`。本例在产品关联阶段已触发阻断，因而没有可用于未知分组的产品记录。判断依据为冻结 DD02 v1.2 §1–2 与《指标目录与数据契约 v1.2》。初算与标准库复核一致，无更正。

## AI 对照冻结 Oracle（2026-11-26）

将已保存的子进程初算与本例 Fixture 的 `/expected` 逐项比较，核对初算原文及冻结预期的 SHA-256。以下核对项均一致，初算原文保留。

| 核对项 | 初算与冻结预期 | 实际差异 |
| --- | --- | --- |
| 缺失产品关联 | 当前窗口订单 `J10-C2`，来源行 `r10-row-c2`，产品完整键 `(domain_a, fixture_missing_product_join, product_missing)` 匹配数为 0。唯一缺失关联及其窗口一致 | 无 |
| 质量状态与理由 | 初算的关键质量阻断对应 `blocked_by_quality`。原因为订单产品复合键关联缺失。两窗订单来源、成熟和水位结论一致 | 初算使用业务描述，冻结值使用状态代码 |
| 发布范围 | 两窗 N、U、率与绝对、相对变化均为 `null`，分组聚合行、分组订单和退款订单集合均为空 | 无 |

## 本人最终核查与签收

AI 对照和本人签收已登记。M05 清单状态为 `confirmed_by_user`。

| 核对字段 | 子进程初算要点 | 冻结预期 | 实际差异 | 原因与修正 |
| --- | --- | --- | --- | --- |
| 关键关联、订单完整键和来源行 | | | | |
| 质量状态与理由 | | | | |
| 双窗指标、变化和分组的发布范围 | | | | |

本人确认及日期：用户已确认，2026-11-26（Asia/Shanghai，公开版省略署名）

登记依据。[本人签收回执](G0_M05_A3-10_user_confirmation.json)

对照位置为 Fixture 的 `/expected`。[冻结 Fixture](../../tests/fixtures/order_boundaries/10_missing_product_join_blocks.json)

子进程初算段落 SHA-256 为 `87d735e7e2ec98ad6abdb265c27752a692b23d6d6d0d33777cb76a09ca824704`。
