# G0 M05 本人独立复核｜A3-06 与 A3-08 v2

先核算下方原始输入，保存本人初算和推导，再打开冻结 Oracle 逐项对照。使用最简分数，保留订单和退款的来源行。开始前记下此前是否接触过这些案例的预期或执行结果。

## 冻结规则

- 先限定域、快照和地区过滤。有效支付按 UTC 的 `paid_at` 进入半开区间 `[start, end)`。每笔入窗订单须在 `as_of` 时完成 7 天观察期，支付水位须覆盖窗末，退款水位须覆盖该窗最晚的观察截止时间。
- 退款事件用 `(domain_id, snapshot_id, refund_id)` 标识，通过 `(domain_id, snapshot_id, order_id)` 关联支付。退款须成功，时间须在 `[paid_at, paid_at + H]` 内且 `refund_at <= as_of`，归属该订单的支付窗口。`N` 为有效支付订单数，`U` 为有合格退款的不同支付订单数，退款率为 `U/N`。
- 类别按 `(domain_id, snapshot_id, product_id)` 关联，按 `category_id` 确定身份。令 `0` 为基期、`1` 为当前期，组权重 `w_t = N组,t / N总,t`，组率 `r_t = U组,t / N组,t`。按两窗的组 ID 集合判定 `shared`、`exit`、`entry`。只列出各窗实际存在的组，缺席侧组率留空。
- 共享组 `within = ((w1 + w0) / 2) × (r1 − r0)`、`structure = ((r1 + r0) / 2) × (w1 − w0)`。新增组 `entry = w1 × r1`，退出组 `exit = −w0 × r0`。贡献以比例差计。此处用精确分数检查四项贡献之和与总体率差 `R1 − R0`，并记录残差。贡献表达算术变化，因果解释需要另外的证据。

规则依据为 DD02 v1.2 第 1–2 节及指标目录 v1.2 中的 `refund_rate_order_horizon`。[DD02](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md#metric) · [指标目录](../../docs/engineering/02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)

## 原始输入

### A3-06

来源为 `tests/fixtures/order_boundaries/06_multiple_refunds_per_order.json` 的 `input`。文件 SHA-256 为 `a7fdc991ce7df027cc48630f76da1f733bc3a11742ea046d219b7acee1ed66fd`。

下列各行的域为 `domain_a`，快照为 `fixture_multiple_refunds`。地区过滤 `[]`，时区 `UTC`，观察期 604800 秒。

窗口与水位

| `字段` | `值` |
| --- | --- |
| `baseline.start` | `2026-09-01T00:00:00Z` |
| `baseline.end` | `2026-09-08T00:00:00Z` |
| `current.start` | `2026-09-08T00:00:00Z` |
| `current.end` | `2026-09-15T00:00:00Z` |
| `as_of` | `2026-09-23T00:00:00Z` |
| `payments_through` | `2026-09-15T00:00:00Z` |
| `refunds_through` | `2026-09-23T00:00:00Z` |

支付

| `source_row_id` | `order_id` | `paid_at` | `is_payment_valid` | `product_id` | `region_id` | `channel_id` |
| --- | --- | --- | --- | --- | --- | --- |
| `r06-row-b1` | `R-B1` | `2026-09-02T00:00:00Z` | `true` | `product_book` | `region_northwest` | `channel_web` |
| `r06-row-b2` | `R-B2` | `2026-09-03T00:00:00Z` | `true` | `product_book` | `region_northwest` | `channel_web` |
| `r06-row-c1` | `R-C1` | `2026-09-09T00:00:00Z` | `true` | `product_book` | `region_northwest` | `channel_web` |
| `r06-row-c2` | `R-C2` | `2026-09-10T00:00:00Z` | `true` | `product_book` | `region_northwest` | `channel_web` |

退款

| `source_row_id` | `refund_id` | `order_id` | `refund_at` | `status` |
| --- | --- | --- | --- | --- |
| `r06-refund-b1-a` | `RR-B1-A` | `R-B1` | `2026-09-04T00:00:00Z` | `success` |
| `r06-refund-b1-b` | `RR-B1-B` | `R-B1` | `2026-09-05T00:00:00Z` | `success` |
| `r06-refund-c1` | `RR-C1` | `R-C1` | `2026-09-11T00:00:00Z` | `success` |
| `r06-refund-c2` | `RR-C2` | `R-C2` | `2026-09-12T00:00:00Z` | `success` |

产品目录

| `product_id` | `category_id` |
| --- | --- |
| `product_book` | `category_books` |

地区目录

| `region_id` | `label` |
| --- | --- |
| `region_northwest` | `西北` |

渠道目录

| `channel_id` | `label` |
| --- | --- |
| `channel_web` | `网页` |

### A3-08 v2

来源为 `tests/fixtures/order_boundaries/08_category_entry_exit.json` 的 `input`。文件 SHA-256 为 `79912e4cec13c3ab34482b02c24deeda4ec443caf569839e4ee5572958550e58`。

下列各行的域为 `domain_a`，快照为 `fixture_category_entry_exit_v2`。地区过滤 `[]`，时区 `UTC`，观察期 604800 秒。

窗口与水位

| `字段` | `值` |
| --- | --- |
| `baseline.start` | `2026-09-01T00:00:00Z` |
| `baseline.end` | `2026-09-08T00:00:00Z` |
| `current.start` | `2026-09-08T00:00:00Z` |
| `current.end` | `2026-09-15T00:00:00Z` |
| `as_of` | `2026-09-23T00:00:00Z` |
| `payments_through` | `2026-09-15T00:00:00Z` |
| `refunds_through` | `2026-09-23T00:00:00Z` |

支付

| `source_row_id` | `order_id` | `paid_at` | `is_payment_valid` | `product_id` | `region_id` | `channel_id` |
| --- | --- | --- | --- | --- | --- | --- |
| `r08v2-row-a-b1` | `E2-A-B1` | `2026-09-02T00:00:00Z` | `true` | `product_a` | `region_northwest` | `channel_web` |
| `r08v2-row-a-b2` | `E2-A-B2` | `2026-09-03T00:00:00Z` | `true` | `product_a` | `region_northwest` | `channel_web` |
| `r08v2-row-b-b1` | `E2-B-B1` | `2026-09-04T00:00:00Z` | `true` | `product_b` | `region_northwest` | `channel_web` |
| `r08v2-row-b-b2` | `E2-B-B2` | `2026-09-05T00:00:00Z` | `true` | `product_b` | `region_northwest` | `channel_web` |
| `r08v2-row-a-c1` | `E2-A-C1` | `2026-09-09T00:00:00Z` | `true` | `product_a` | `region_northwest` | `channel_web` |
| `r08v2-row-c-c1` | `E2-C-C1` | `2026-09-10T00:00:00Z` | `true` | `product_c` | `region_northwest` | `channel_web` |
| `r08v2-row-c-c2` | `E2-C-C2` | `2026-09-11T00:00:00Z` | `true` | `product_c` | `region_northwest` | `channel_web` |
| `r08v2-row-c-c3` | `E2-C-C3` | `2026-09-12T00:00:00Z` | `true` | `product_c` | `region_northwest` | `channel_web` |

退款

| `source_row_id` | `refund_id` | `order_id` | `refund_at` | `status` |
| --- | --- | --- | --- | --- |
| `r08v2-refund-b-b1` | `ER2-B-B1` | `E2-B-B1` | `2026-09-06T00:00:00Z` | `success` |
| `r08v2-refund-b-b2` | `ER2-B-B2` | `E2-B-B2` | `2026-09-07T00:00:00Z` | `success` |
| `r08v2-refund-a-c1` | `ER2-A-C1` | `E2-A-C1` | `2026-09-11T00:00:00Z` | `success` |
| `r08v2-refund-c-c1` | `ER2-C-C1` | `E2-C-C1` | `2026-09-12T00:00:00Z` | `success` |
| `r08v2-refund-c-c2` | `ER2-C-C2` | `E2-C-C2` | `2026-09-13T00:00:00Z` | `success` |
| `r08v2-refund-c-c3` | `ER2-C-C3` | `E2-C-C3` | `2026-09-14T00:00:00Z` | `success` |

产品目录

| `product_id` | `category_id` |
| --- | --- |
| `product_a` | `category_a` |
| `product_b` | `category_b` |
| `product_c` | `category_c` |

类别目录

| `category_id` | `label` |
| --- | --- |
| `category_a` | `类别A` |
| `category_b` | `类别B` |
| `category_c` | `类别C` |

地区目录

| `region_id` | `label` |
| --- | --- |
| `region_northwest` | `西北` |

渠道目录

| `channel_id` | `label` |
| --- | --- |
| `channel_web` | `网页` |

## 本人初算

### A3-06｜按支付订单归并退款

逐单标出支付窗口、观察截止时刻、合格的 `refund_id` 与退款 `source_row_id`，并核对成熟期和两个水位。说明同一订单对应多笔合格退款时，事件数与 `U` 各如何计数。

| 窗口 | 有效支付订单 | 合格退款事件及来源 | 去重后退款订单 | 事件数 | N | U | U/N |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 基期 | | | | | | | |
| 当前 | | | | | | | |

观察截止、水位判断及计数说明：____

### A3-08 v2｜类别分组与贡献

逐单关联类别及合格退款。每窗保留一个总计和实际存在的类别组，在订单集合中带上支付来源行，在退款集合中带上合格事件及来源行。用分数填写权重、组率及贡献。

| 窗口 | 行类型 | 类别 ID | 支付订单及来源 | 退款订单及事件来源 | N | U | 率 | 权重 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 基期 | 总计 | | | | | | | |
| 当前 | 总计 | | | | | | | |

| 类别 ID | 生命周期 | w0 | r0 | w1 | r1 | within | structure | entry | exit | 净贡献 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| | | | | | | | | | | |
| | | | | | | | | | | |
| | | | | | | | | | | |

- 两窗分别列出 `ΣN组`、`ΣU组`、总计及 `Σw`。说明每笔支付为何恰好进入一个类别组。
- 写出 `shared`、`exit`、`entry` 的 ID 集合，解释缺席组和存在但零退款的组有何区别。
- 分别合计 `within`、`structure`、`entry`、`exit`，保留至少一个共享组的代入过程。计算 `R1 − R0`、贡献和及残差，说明贡献的单位与解释边界。

逐单依据、代入过程及守恒检查：____

## Oracle 对照与差异

本人初算待提交，Oracle 对照待开始。本人初算完成后保留原稿，按下表记录实际差异。此前接触预期或运行结果的情况由复核者本人填写。

| 案例及字段 | 本人初算 | 冻结值 | 实际差异 | 原因及订正 |
| --- | --- | --- | --- | --- |
| 待对照 | | | | |

对照依据为 A3-06 固定 Fixture 的 `expected`、A3-08 v2 的 `A3-08_v2_expected.json` 及 M03 的 `G0_M03_A3-08_v2_contribution_expected.json`。两份 v2 台账位于本目录。本人独立复核状态待确认，L3 状态沿用现有记录。
