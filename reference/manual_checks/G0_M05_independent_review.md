# G0 M05 本人独立复核｜A3-06 与 A3-08 v2

2026-11-25（Asia/Shanghai），按用户委托由独立子进程核算。子进程只使用下方原始输入和冻结规则，保存初算后由主进程对照冻结 Oracle。用户随后确认已完成复核，并授权登记 A3-06、A3-08 v2 及其贡献分解的本人签收。初算仍署名为子进程。L3 状态沿用现有记录。[签收回执](G0_M05_user_confirmation.json)

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

## 独立子进程初算

依据 DD02 v1.2 第 1–2 节与 `06_multiple_refunds_per_order.json`、`08_category_entry_exit.json` 各自的 `input` 字段独立计算。

两例均为 `domain_a`、指标 `refund_rate_order_horizon`、时区 UTC、观察期 `H=604800` 秒（7 天），`filters.region_ids=[]` 覆盖全部地区。基期取支付时刻 `[2026-09-01T00:00:00Z, 2026-09-08T00:00:00Z)`，当前取 `[2026-09-08T00:00:00Z, 2026-09-15T00:00:00Z)`。按 `(domain_id, snapshot_id, order_id)` 关联，成功退款事件的时间须满足 `paid_at ≤ refund_at ≤ paid_at+H` 且 `refund_at ≤ as_of`。`N` 计有效支付订单，`U` 计至少有一笔合格退款的支付订单。以下逐单表与事件表的日期均为 2026 年 9 月，且时刻均为 `00:00:00Z`。

### A3-06｜按支付订单归并退款

| 支付窗口 | 订单完整键 `(domain_id, snapshot_id, order_id)` | 支付来源 `source_row_id` | 支付日期 | 含端点观察截止 `paid_at+H` | 合格退款事件 ID |
| --- | --- | --- | --- | --- | --- |
| 基期 | `(domain_a, fixture_multiple_refunds, R-B1)` | `r06-row-b1` | 09-02 | 09-09 | `RR-B1-A`、`RR-B1-B` |
| 基期 | `(domain_a, fixture_multiple_refunds, R-B2)` | `r06-row-b2` | 09-03 | 09-10 | ∅ |
| 当前 | `(domain_a, fixture_multiple_refunds, R-C1)` | `r06-row-c1` | 09-09 | 09-16 | `RR-C1` |
| 当前 | `(domain_a, fixture_multiple_refunds, R-C2)` | `r06-row-c2` | 09-10 | 09-17 | `RR-C2` |

| 退款事件完整键 `(domain_id, snapshot_id, refund_id)` | 退款来源 `source_row_id` | 退款日期 | 所属订单 `order_id` | 支付窗口 |
| --- | --- | --- | --- | --- |
| `(domain_a, fixture_multiple_refunds, RR-B1-A)` | `r06-refund-b1-a` | 09-04 | `R-B1` | 基期 |
| `(domain_a, fixture_multiple_refunds, RR-B1-B)` | `r06-refund-b1-b` | 09-05 | `R-B1` | 基期 |
| `(domain_a, fixture_multiple_refunds, RR-C1)` | `r06-refund-c1` | 09-11 | `R-C1` | 当前 |
| `(domain_a, fixture_multiple_refunds, RR-C2)` | `r06-refund-c2` | 09-12 | `R-C2` | 当前 |

| 窗口 | 有效支付订单（来源行） | 合格退款事件（来源行） | 去重后退款订单 | 事件数 | N | U | U/N |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 基期 | `R-B1`（`r06-row-b1`）、`R-B2`（`r06-row-b2`） | `RR-B1-A`（`r06-refund-b1-a`）、`RR-B1-B`（`r06-refund-b1-b`） | `{R-B1}` | 2 | 2 | 1 | `1/2` |
| 当前 | `R-C1`（`r06-row-c1`）、`R-C2`（`r06-row-c2`） | `RR-C1`（`r06-refund-c1`）、`RR-C2`（`r06-refund-c2`） | `{R-C1, R-C2}` | 2 | 2 | 2 | `1` |

4 笔支付均有效。基期最晚观察截止为 `2026-09-10T00:00:00Z`，当前为 `2026-09-17T00:00:00Z`。两者均早于 `as_of=2026-09-23T00:00:00Z`，也均在退款水位 `refunds_through=2026-09-23T00:00:00Z` 内。支付水位 `payments_through=2026-09-15T00:00:00Z` 覆盖基期窗口末端，且等于当前窗口末端。两窗均成熟可比。基期同一订单 `R-B1` 有两笔成功且在观察期内的退款，贡献两个事件和一个 `U`。当前两笔合格事件来自两个订单，贡献两个事件和两个 `U`。

### A3-08 v2｜类别分组与贡献

| 支付窗口 | 订单完整键 `(domain_id, snapshot_id, order_id)` | 产品完整键 `(domain_id, snapshot_id, product_id)` | 类别 ID | 支付来源 `source_row_id` | 支付／观察截止日期 | 合格退款事件 ID（来源行） |
| --- | --- | --- | --- | --- | --- | --- |
| 基期 | `(domain_a, fixture_category_entry_exit_v2, E2-A-B1)` | `(domain_a, fixture_category_entry_exit_v2, product_a)` | `category_a` | `r08v2-row-a-b1` | 09-02／09-09 | ∅ |
| 基期 | `(domain_a, fixture_category_entry_exit_v2, E2-A-B2)` | `(domain_a, fixture_category_entry_exit_v2, product_a)` | `category_a` | `r08v2-row-a-b2` | 09-03／09-10 | ∅ |
| 基期 | `(domain_a, fixture_category_entry_exit_v2, E2-B-B1)` | `(domain_a, fixture_category_entry_exit_v2, product_b)` | `category_b` | `r08v2-row-b-b1` | 09-04／09-11 | `ER2-B-B1`（`r08v2-refund-b-b1`，09-06） |
| 基期 | `(domain_a, fixture_category_entry_exit_v2, E2-B-B2)` | `(domain_a, fixture_category_entry_exit_v2, product_b)` | `category_b` | `r08v2-row-b-b2` | 09-05／09-12 | `ER2-B-B2`（`r08v2-refund-b-b2`，09-07） |
| 当前 | `(domain_a, fixture_category_entry_exit_v2, E2-A-C1)` | `(domain_a, fixture_category_entry_exit_v2, product_a)` | `category_a` | `r08v2-row-a-c1` | 09-09／09-16 | `ER2-A-C1`（`r08v2-refund-a-c1`，09-11） |
| 当前 | `(domain_a, fixture_category_entry_exit_v2, E2-C-C1)` | `(domain_a, fixture_category_entry_exit_v2, product_c)` | `category_c` | `r08v2-row-c-c1` | 09-10／09-17 | `ER2-C-C1`（`r08v2-refund-c-c1`，09-12） |
| 当前 | `(domain_a, fixture_category_entry_exit_v2, E2-C-C2)` | `(domain_a, fixture_category_entry_exit_v2, product_c)` | `category_c` | `r08v2-row-c-c2` | 09-11／09-18 | `ER2-C-C2`（`r08v2-refund-c-c2`，09-13） |
| 当前 | `(domain_a, fixture_category_entry_exit_v2, E2-C-C3)` | `(domain_a, fixture_category_entry_exit_v2, product_c)` | `category_c` | `r08v2-row-c-c3` | 09-12／09-19 | `ER2-C-C3`（`r08v2-refund-c-c3`，09-14） |

每笔有效支付的产品键在相同域和快照内只匹配一条产品维度记录，且该记录只指定一个类别 ID。上述合格退款事件的完整键均为 `(domain_a, fixture_category_entry_exit_v2, refund_id)`，每笔都在对应订单的观察区间内且 `status=success`。两窗最晚观察截止分别为 `2026-09-12T00:00:00Z` 和 `2026-09-19T00:00:00Z`。两者均早于 `as_of=2026-09-23T00:00:00Z` 且在 `refunds_through=2026-09-23T00:00:00Z` 内。`payments_through=2026-09-15T00:00:00Z` 覆盖两窗末端。两窗均成熟可比。

| 窗口 | 行类型 | 类别 ID | 支付订单（来源行） | 退款订单及合格事件（来源行） | N | U | 率 | 权重 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 基期 | 总计 | — | `E2-A-B1`（`r08v2-row-a-b1`）、`E2-A-B2`（`r08v2-row-a-b2`）、`E2-B-B1`（`r08v2-row-b-b1`）、`E2-B-B2`（`r08v2-row-b-b2`） | `E2-B-B1`／`ER2-B-B1`（`r08v2-refund-b-b1`）、`E2-B-B2`／`ER2-B-B2`（`r08v2-refund-b-b2`） | 4 | 2 | `1/2` | `1` |
| 基期 | 类别 | `category_a` | `E2-A-B1`（`r08v2-row-a-b1`）、`E2-A-B2`（`r08v2-row-a-b2`） | ∅ | 2 | 0 | `0` | `1/2` |
| 基期 | 类别 | `category_b` | `E2-B-B1`（`r08v2-row-b-b1`）、`E2-B-B2`（`r08v2-row-b-b2`） | `E2-B-B1`／`ER2-B-B1`（`r08v2-refund-b-b1`）、`E2-B-B2`／`ER2-B-B2`（`r08v2-refund-b-b2`） | 2 | 2 | `1` | `1/2` |
| 当前 | 总计 | — | `E2-A-C1`（`r08v2-row-a-c1`）、`E2-C-C1`（`r08v2-row-c-c1`）、`E2-C-C2`（`r08v2-row-c-c2`）、`E2-C-C3`（`r08v2-row-c-c3`） | `E2-A-C1`／`ER2-A-C1`（`r08v2-refund-a-c1`）、`E2-C-C1`／`ER2-C-C1`（`r08v2-refund-c-c1`）、`E2-C-C2`／`ER2-C-C2`（`r08v2-refund-c-c2`）、`E2-C-C3`／`ER2-C-C3`（`r08v2-refund-c-c3`） | 4 | 4 | `1` | `1` |
| 当前 | 类别 | `category_a` | `E2-A-C1`（`r08v2-row-a-c1`） | `E2-A-C1`／`ER2-A-C1`（`r08v2-refund-a-c1`） | 1 | 1 | `1` | `1/4` |
| 当前 | 类别 | `category_c` | `E2-C-C1`（`r08v2-row-c-c1`）、`E2-C-C2`（`r08v2-row-c-c2`）、`E2-C-C3`（`r08v2-row-c-c3`） | `E2-C-C1`／`ER2-C-C1`（`r08v2-refund-c-c1`）、`E2-C-C2`／`ER2-C-C2`（`r08v2-refund-c-c2`）、`E2-C-C3`／`ER2-C-C3`（`r08v2-refund-c-c3`） | 3 | 3 | `1` | `3/4` |

| 类别 ID | 生命周期 | w0 | r0 | w1 | r1 | within | structure | entry | exit | 净贡献 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `category_a` | `shared` | `1/2` | `0` | `1/4` | `1` | `3/8` | `-1/8` | `0` | `0` | `1/4` |
| `category_b` | `exit` | `1/2` | `1` | — | — | `0` | `0` | `0` | `-1/2` | `-1/2` |
| `category_c` | `entry` | — | — | `3/4` | `1` | `0` | `0` | `3/4` | `0` | `3/4` |
| 合计 | — | — | — | — | — | `3/8` | `-1/8` | `3/4` | `-1/2` | `1/2` |

- 基期 `ΣN组=2+2=4=N`、`ΣU组=0+2=2=U`、`Σw=1/2+1/2=1`，且 `Σ(w×r)=(1/2)×0+(1/2)×1=1/2=R0`。
- 当前 `ΣN组=1+3=4=N`、`ΣU组=1+3=4=U`、`Σw=1/4+3/4=1`，且 `Σ(w×r)=(1/4)×1+(3/4)×1=1=R1`。
- 基期类别集合 `{category_a, category_b}`，当前类别集合 `{category_a, category_c}`。`shared={category_a}`、`exit={category_b}`、`entry={category_c}`。三集合互斥，合并覆盖两窗类别集合。
- `category_c` 在基期缺席，`category_b` 在当前缺席。对应窗口没有该类别的支付，因此明细组行缺席，组率无定义。表中 `—` 表示缺席侧的组数据没有值，计算该侧占比或加权率时其份额为 `0`。基期的 `category_a` 有两笔支付、零笔合格退款订单，组行存在，`r0=0/2=0`，权重为 `2/4=1/2`，所以该组属于 `shared`。贡献列的 `0` 表示该类别没有该分量。
- `category_a` 的 `within=((1/4+1/2)/2)×(1−0)=3/8`，`structure=((1+0)/2)×(1/4−1/2)=−1/8`，净贡献 `1/4`。`category_b` 的 `exit=−(1/2)×1=−1/2`。`category_c` 的 `entry=(3/4)×1=3/4`。
- `R1−R0=1−1/2=1/2`，四项贡献和 `3/8−1/8+3/4−1/2=1/2`，残差 `(R1−R0)−Σ贡献=0`，满足 `≤1e-6`。内部贡献单位为比率，展示乘以 `100` 换算为百分点。四分量分别为 `+37.50`、`−12.50`、`+75.00`、`−50.00` 个百分点，净变化为 `+50.00` 个百分点。分解说明该类别维度下各项对总率差的算术贡献，不能据此判定因果或与其他维度的贡献相加。

## Oracle 对照与差异

初算保存后才读取冻结预期。对照使用精确 `Fraction` 及成员集合，逐单核验完整键、观察截止、事件归属和来源。未发现实质差异或需要更正的计算错误，原稿保留。A3-06 及 A3-08 v2 固定 Fixture 的 SHA-256 与本表原始输入登记一致。

| 案例及字段 | 子进程初算 | 冻结值 | 实际差异及处理 |
| --- | --- | --- | --- |
| A3-06 基期 | 2 个事件，退款订单 `{R-B1}`，N=2、U=1、率 `1/2` | 同事件集合、支付来源和退款订单，率 `0.5` | `Fraction("0.5") = 1/2`，数值差为 0 |
| A3-06 当前 | 2 个事件，退款订单 `{R-C1, R-C2}`，N=2、U=2、率 `1` | 同事件集合、支付来源和退款订单，率 `1` | 一致，退款事件来源另逐条匹配原始输入 |
| A3-08 v2 六条聚合行 | 按（N，U，率）记录，基期总计 `(4, 2, 1/2)`，A `(2, 0, 0)`，B `(2, 2, 1)`。当前总计 `(4, 4, 1)`，A `(1, 1, 1)`，C `(3, 3, 1)` | 固定 Fixture 六行及 v2 冻结逐单台账 | 六行、支付和退款来源、生命周期集合及两窗缺席组均一致 |
| A3-08 v2 组权重与组率 | A 权重 `1/2 → 1/4`、组率 `0 → 1`。B 仅基期，权重 `1/2`、组率 `1`。C 仅当前，权重 `3/4`、组率 `1` | M03 Oracle 的实际存在窗口、权重、组率及加权率 | 一致，缺席侧留空 |
| A3-08 v2 贡献及守恒 | `within=3/8`、`structure=-1/8`、`entry=3/4`、`exit=-1/2`。组净贡献 A `1/4`、B `-1/2`、C `3/4`。贡献和与总体率差均为 `1/2`，残差 `0` | M03 Oracle 的逐组分量、净贡献、总量与残差 | 一致。冻结 Oracle 省略不适用的类别贡献分量，初算以 `0` 表示，对照时按零贡献比较 |

冻结对照依据。[A3-06 固定 Fixture](../../tests/fixtures/order_boundaries/06_multiple_refunds_per_order.json) · [A3-08 v2 固定 Fixture](../../tests/fixtures/order_boundaries/08_category_entry_exit.json) · [A3-08 v2 逐单台账](A3-08_v2_expected.json) · [M03 贡献 Oracle](G0_M03_A3-08_v2_contribution_expected.json)

子进程原始初算正文 SHA-256 为 `72fa7d98e4aa05f0c9b72c0448016fb01187cd90d796982d76db053ee55b3e7a`。填表时对齐了两处表头分隔线，保留原计算与推导。
