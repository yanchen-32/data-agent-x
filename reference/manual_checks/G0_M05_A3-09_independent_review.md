# M05 A3-09 本人独立核验表｜类别归组与退款订单

2026-11-26（Asia/Shanghai），按用户委托由独立子进程完成初算，依据为下方原始输入和冻结规则。初算原稿已保存。请在下方对照区填写最终核查结果。

## 冻结规则
- 支付按 UTC 的半开窗口 `[start, end)` 归属。每笔入窗订单须在 `as_of` 时完成 7 天观察期，支付水位须覆盖窗末，退款水位须覆盖窗口内最晚观察截止。
- 退款按 `(domain_id, snapshot_id, refund_id)` 标识，通过 `(domain_id, snapshot_id, order_id)` 关联支付。成功事件须处于 `[paid_at, paid_at + H]` 内且 `refund_at <= as_of`。每窗支付订单数为 N，有合格退款的去重支付订单数为 U，率用精确的 U/N。
- 类别归组先按 `(domain_id, snapshot_id, product_id)` 查产品，再按类别 ID 聚合。合法产品关联上的非关键未知类别用 `__unknown__`，保留其订单和退款来源。关键关联错误须阻断发布。

规则依据。[DD02 §1–2](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md#data) · [指标目录](../../docs/engineering/02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)

## 原始输入

来源为 `tests/fixtures/order_boundaries/09_unknown_category_preserved.json` 的 `input`。整文件 SHA-256 为 `d9677959c20e91b6965e984035742a6524592896fbf9ce40728192a43bd8439e`，规范化输入 SHA-256 为 `6d504013cfcf21f98b4cac416ac2acc39283136212ee867f83d837fa6801ed56`。

各行共用域 `domain_a` 和快照 `fixture_unknown_category_preserved`。指标 `refund_rate_order_horizon`，时区 `UTC`，地区过滤 `[]`，观察期 604800 秒。

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
| `r09-row-k-b1` | `K9-B1` | `product_known` | `region_northwest` | `channel_web` | `2026-09-01T00:00:00Z` | `true` |
| `r09-row-k-b2` | `K9-B2` | `product_known` | `region_northwest` | `channel_web` | `2026-09-03T00:00:00Z` | `true` |
| `r09-row-u-b1` | `U9-B1` | `product_unknown` | `region_northwest` | `channel_web` | `2026-09-04T00:00:00Z` | `true` |
| `r09-row-u-b2` | `U9-B2` | `product_unknown` | `region_northwest` | `channel_web` | `2026-09-07T00:00:00Z` | `true` |
| `r09-row-k-c1` | `K9-C1` | `product_known` | `region_northwest` | `channel_web` | `2026-09-08T00:00:00Z` | `true` |
| `r09-row-k-c2` | `K9-C2` | `product_known` | `region_northwest` | `channel_web` | `2026-09-10T00:00:00Z` | `true` |
| `r09-row-u-c1` | `U9-C1` | `product_unknown` | `region_northwest` | `channel_web` | `2026-09-11T00:00:00Z` | `true` |
| `r09-row-u-c2` | `U9-C2` | `product_unknown` | `region_northwest` | `channel_web` | `2026-09-14T00:00:00Z` | `true` |

### 退款事件

| source_row_id | refund_id | order_id | refund_at | status |
| --- | --- | --- | --- | --- |
| `r09-refund-u-b1` | `R9-U-B1` | `U9-B1` | `2026-09-06T00:00:00Z` | `success` |
| `r09-refund-u-b2` | `R9-U-B2` | `U9-B2` | `2026-09-09T00:00:00Z` | `success` |
| `r09-refund-k-c1` | `R9-K-C1` | `K9-C1` | `2026-09-10T00:00:00Z` | `success` |
| `r09-refund-u-c1` | `R9-U-C1` | `U9-C1` | `2026-09-13T00:00:00Z` | `success` |
| `r09-refund-u-c2` | `R9-U-C2` | `U9-C2` | `2026-09-16T00:00:00Z` | `success` |

### 产品目录

| product_id | category_id |
| --- | --- |
| `product_known` | `category_a` |
| `product_unknown` | `null` |

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

冻结范围为 `domain_a`、`fixture_unknown_category_preserved`，时区 UTC，`H = 604800` 秒，`filters.region_ids = []`。基期支付窗口为 `[2026-09-01T00:00:00Z, 2026-09-08T00:00:00Z)`，当前窗口为 `[2026-09-08T00:00:00Z, 2026-09-15T00:00:00Z)`。八笔支付均有效。窗口以支付时刻归属，`K9-B1` 落在基期左端，`K9-C1` 落在当前左端，`R9-U-B2` 虽发生在当前支付窗口，其关联订单仍属于基期。

支付订单完整键为 `(domain_a, fixture_unknown_category_preserved, order_id)`，退款事件完整键为 `(domain_a, fixture_unknown_category_preserved, refund_id)`。表中 ID 代入对应键位，每个合格事件按其自身的 `(domain_id, snapshot_id, order_id)` 唯一回连到所在行的订单。八个订单键和五个退款事件键各自唯一。八笔订单的地区和渠道完整键均分别命中 `(domain_a, fixture_unknown_category_preserved, region_northwest)` 与 `(domain_a, fixture_unknown_category_preserved, channel_web)`。

| 窗口 | 支付订单、时刻与来源行 | 产品完整键 | 类别 ID | 观察截止时刻 | 合格退款事件、时刻与来源行 |
| --- | --- | --- | --- | --- | --- |
| 基期 | `K9-B1` / `2026-09-01T00:00:00Z` / `r09-row-k-b1` | `(domain_a, fixture_unknown_category_preserved, product_known)` | `category_a` | `2026-09-08T00:00:00Z` | 无 |
| 基期 | `K9-B2` / `2026-09-03T00:00:00Z` / `r09-row-k-b2` | `(domain_a, fixture_unknown_category_preserved, product_known)` | `category_a` | `2026-09-10T00:00:00Z` | 无 |
| 基期 | `U9-B1` / `2026-09-04T00:00:00Z` / `r09-row-u-b1` | `(domain_a, fixture_unknown_category_preserved, product_unknown)` | `__unknown__` | `2026-09-11T00:00:00Z` | `R9-U-B1` / `2026-09-06T00:00:00Z` / `r09-refund-u-b1` |
| 基期 | `U9-B2` / `2026-09-07T00:00:00Z` / `r09-row-u-b2` | `(domain_a, fixture_unknown_category_preserved, product_unknown)` | `__unknown__` | `2026-09-14T00:00:00Z` | `R9-U-B2` / `2026-09-09T00:00:00Z` / `r09-refund-u-b2` |
| 当前 | `K9-C1` / `2026-09-08T00:00:00Z` / `r09-row-k-c1` | `(domain_a, fixture_unknown_category_preserved, product_known)` | `category_a` | `2026-09-15T00:00:00Z` | `R9-K-C1` / `2026-09-10T00:00:00Z` / `r09-refund-k-c1` |
| 当前 | `K9-C2` / `2026-09-10T00:00:00Z` / `r09-row-k-c2` | `(domain_a, fixture_unknown_category_preserved, product_known)` | `category_a` | `2026-09-17T00:00:00Z` | 无 |
| 当前 | `U9-C1` / `2026-09-11T00:00:00Z` / `r09-row-u-c1` | `(domain_a, fixture_unknown_category_preserved, product_unknown)` | `__unknown__` | `2026-09-18T00:00:00Z` | `R9-U-C1` / `2026-09-13T00:00:00Z` / `r09-refund-u-c1` |
| 当前 | `U9-C2` / `2026-09-14T00:00:00Z` / `r09-row-u-c2` | `(domain_a, fixture_unknown_category_preserved, product_unknown)` | `__unknown__` | `2026-09-21T00:00:00Z` | `R9-U-C2` / `2026-09-16T00:00:00Z` / `r09-refund-u-c2` |

| 窗口 | 窗口末端 | 最晚观察截止时刻 | 成熟判断 | 支付水位覆盖 | 退款水位覆盖 |
| --- | --- | --- | --- | --- | --- |
| 基期 | `2026-09-08T00:00:00Z` | `2026-09-14T00:00:00Z` | 最晚截止 ≤ `as_of = 2026-09-23T00:00:00Z` | `2026-09-15T00:00:00Z` ≥ 窗口末端 | `2026-09-23T00:00:00Z` ≥ 最晚截止 |
| 当前 | `2026-09-15T00:00:00Z` | `2026-09-21T00:00:00Z` | 最晚截止 ≤ `as_of = 2026-09-23T00:00:00Z` | `2026-09-15T00:00:00Z` = 窗口末端 | `2026-09-23T00:00:00Z` ≥ 最晚截止 |

| 窗口 | 类别或总计 | 支付订单集合 | 去重后的退款订单集合 | N | U | U/N（精确分数） |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 基期 | `category_a` | `{K9-B1, K9-B2}` | `∅` | 2 | 0 | `0/1` |
| 基期 | `__unknown__` | `{U9-B1, U9-B2}` | `{U9-B1, U9-B2}` | 2 | 2 | `1/1` |
| 基期 | 总计 | `{K9-B1, K9-B2, U9-B1, U9-B2}` | `{U9-B1, U9-B2}` | 4 | 2 | `1/2` |
| 当前 | `category_a` | `{K9-C1, K9-C2}` | `{K9-C1}` | 2 | 1 | `1/2` |
| 当前 | `__unknown__` | `{U9-C1, U9-C2}` | `{U9-C1, U9-C2}` | 2 | 2 | `1/1` |
| 当前 | 总计 | `{K9-C1, K9-C2, U9-C1, U9-C2}` | `{K9-C1, U9-C1, U9-C2}` | 4 | 3 | `3/4` |

`product_known` 在完整产品键下唯一命中，类别完整键 `(domain_a, fixture_unknown_category_preserved, category_a)` 也唯一命中。 `product_unknown` 在完整产品键下同样唯一命中，其 `category_id` 为空，属于非关键类别未知。按 `(category, __unknown__)` 分组并披露该组，四笔对应订单继续参加分母，其中满足退款条件的订单继续参加分子。

五笔列出的事件均为 `success`，满足 `paid_at ≤ refund_at ≤ paid_at + H` 且 `refund_at ≤ as_of`。先逐退款事件核对资格，再按完整订单键取存在至少一次合格退款的订单，每单计一次。该输入的合格事件恰好分属五笔订单，基期两笔、当前三笔。

基期 `ΣN组 = 2 + 2 = 4 = N总计`，`ΣU组 = 0 + 2 = 2 = U总计`。当前 `ΣN组 = 2 + 2 = 4 = N总计`，`ΣU组 = 1 + 2 = 3 = U总计`。两窗通过成熟和水位判断，输入所示类别缺失按未知组规则处理。计算依据为冻结 DD02 v1.2 §1–2 与《指标目录与数据契约 v1.2》。初算与标准库复核一致，无更正。

## AI 对照冻结 Oracle（2026-11-26）

将已保存的子进程初算与本例 Fixture 的 `/expected` 逐项比较，核对初算原文及冻结预期的 SHA-256。以下核对项均一致，初算原文保留。

| 核对项 | 初算与冻结预期 | 实际差异 |
| --- | --- | --- |
| 退款订单集合及来源 | 基期为 `{U9-B1, U9-B2}`，当前为 `{K9-C1, U9-C1, U9-C2}`。逐窗合格退款事件、支付来源及逐组退款来源一致 | 无 |
| 六条聚合行及未知组 | 两窗均保留 `__unknown__`，各为 N=2、U=2、率 1。基期总计 N=4、U=2、率 1/2，当前 N=4、U=3、率 3/4；已知组数值也逐行匹配 | `1/2` 与 `0.5`、`3/4` 与 `0.75` 仅表示不同 |
| 可比性与守恒 | 两窗成熟和水位均满足。基期 `ΣN=4、ΣU=2`，当前 `ΣN=4、ΣU=3`，均与各窗总计一致 | 无 |

## 本人最终核查与签收

AI 对照和本人签收已登记。M05 清单状态为 `confirmed_by_user`。

| 核对字段 | 子进程初算要点 | 冻结预期 | 实际差异 | 原因与修正 |
| --- | --- | --- | --- | --- |
| 两窗支付与合格退款归属 | | | | |
| 去重后的退款订单集合 | | | | |
| 分组身份、N/U/率与守恒 | | | | |

本人确认及日期：用户已确认，2026-11-26（Asia/Shanghai，公开版省略署名）

登记依据。[本人签收回执](G0_M05_A3-09_user_confirmation.json)

对照位置为 Fixture 的 `/expected`。[冻结 Fixture](../../tests/fixtures/order_boundaries/09_unknown_category_preserved.json)

子进程初算段落 SHA-256 为 `b99080c5f4d27611b404bb77b3a292a4d2e3b7b015236601b70b670790fca80f`。
