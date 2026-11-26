# G0 M05 剩余七例本人核验表

2026-11-26（Asia/Shanghai）。7 个案例的技术复核与冻结 Oracle 对照已完成，用户已核查七例的当前冻结版本并授权登记本人确认。表中初算由 AI 从各 Fixture 的 `input` 单独推导并保存，再打开 `/expected` 核对。同一来源的既有预期可能曾被看过，本记录为技术复核。

## 本人签收登记

确认来源为用户本人明确确认与授权，登记日期为 2026-11-26（Asia/Shanghai）。回执绑定本表及七例的冻结输入与预期。[本人签收回执](G0_M05_remaining_user_confirmation.json)

| 案例 | 已对照的关键结论 | 本人核查点 | 本人结论及日期 |
| --- | --- | --- | --- |
| [A3-01](#a3-01) | 当前单恰好成熟，支付水位覆盖窗末，退款水位比观察截止少 1 微秒，整次比较不发布。 | 找出差 1 微秒的是哪项水位，解释成熟为何仍然通过。 | 已确认（2026-11-26） |
| [A3-02](#a3-02) | 起点纳入、终点排除。退款观察截止等号纳入，晚 1 微秒排除。同一订单多笔合格退款在 U 中计一次。 | 核对 UR-1、UR-2 的相对截止时刻，以及 UR-3、UR-4 的去重结果。 | 已确认（2026-11-26） |
| [A3-03](#a3-03) | 完整业务键 (domain_a, fixture_duplicate, D-B) 重复 1 组，涉及 d-row-1、d-row-2，比较不发布。 | 指出重复的是哪个业务键，说明不同来源行为什么仍会阻断。 | 已确认（2026-11-26） |
| [A3-04](#a3-04) | 基期诊断 N=0、U=0，当前诊断 N=2、U=1、率 1/2。两窗发布指标和变化均为 null。 | 区分当前诊断率与发布率，解释空基期为何无法进行比较。 | 已确认（2026-11-26） |
| [A3-05](#a3-05) | 西北基期 N=2、U=1、率 1/2，当前 N=1、U=1、率 1，绝对变化 1/2。 | 核对东南订单及其退款为何都不参与西北比较。 | 已确认（2026-11-26） |
| [A3-07](#a3-07) | 两窗按两个类别 ID 各自计数，基期总率 1/2，当前总率 1/4。分组 N/U 汇总保持守恒。 | 指出同一展示名对应的两个 ID，任选一窗用来源订单复核分组守恒。 | 已确认（2026-11-26） |
| [A3-11](#a3-11) | 西北基期 N=3、U=1、率 1/3，当前 N=4、U=3、率 3/4，绝对变化 5/12。 | 任选一窗把两渠道的 N/U 加回总计，并核对东南订单及退款已排除。 | 已确认（2026-11-26） |

## 共同规则与版本

完整订单键为 `(domain_id, snapshot_id, order_id)`，退款事件键用同域同快照的 `refund_id`。先限制 Scope，再按 UTC 支付半开窗入列。成功退款位于支付时刻起的 7 天闭合观察区间且不晚于 as_of 时，该订单进入去重后的退款订单集合。成熟期、两类水位和双窗有效样本决定比较能否发布。分组身份按固定 ID。

七例均使用 UTC。基期为 `[2026-09-01 00:00, 2026-09-08 00:00)`，当前为 `[2026-09-08 00:00, 2026-09-15 00:00)`。各例的两类水位按支付、退款顺序列出。

规则来源。[DD02 v1.2 §1–2](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md#data) · [G0 预审](../regression_checks/G0_fixture_coverage.md) · [开发清单](../regression_checks/G0_development_manifest.json)

AI 初算先行记录 SHA-256 为 `9512c5866d048a40386d09f4dbdc9e30ba1ed104ce717f64eb79cc801582484f`。每例表内记录的文件和 JSON 指纹均与当前清单相符。

<a id="a3-01"></a>
## A3-01｜成熟与水位

当前单恰好成熟，支付水位覆盖窗末，退款水位比观察截止少 1 微秒，整次比较不发布。 [冻结 Fixture](../../tests/fixtures/order_boundaries/01_maturity_watermark.json)

范围为 `domain_a` / `fixture_maturity`，地区条件为 `[]`，截至 `2026-09-15T00:00:00Z`，两类水位分别为 `2026-09-15T00:00:00Z` 和 `2026-09-14T23:59:59.999999Z`。

| 订单 | 来源行 | 支付时刻 UTC | 观察截止 | 归属或排除理由 | 产品、组或地区 |
| --- | --- | --- | --- | --- | --- |
| `M-B` | `m-row-b` | `2026-09-01T00:00:00Z` | `2026-09-08T00:00:00Z` | 基期 | `product_book` / `region_northwest` |
| `M-C` | `m-row-c` | `2026-09-08T00:00:00Z` | `2026-09-15T00:00:00Z` | 当前 | `product_book` / `region_northwest` |

以下为候选诊断数，正式双窗 N、U、率、绝对变化和相对变化均为 `null`。

| 窗口 | 组或总计 | 支付订单集合 | 退款订单集合 | N | U | 率 |
| --- | --- | --- | --- | --- | --- | --- |
| 基期 | 总计 | `M-B` | ∅ | 1 | 0 | `0` |
| 当前 | 总计 | `M-C` | ∅ | 1 | 0 | `0` |

两窗最晚观察截止为 `2026-09-08T00:00:00Z` 与 `2026-09-15T00:00:00Z`。比较结果为 `insufficient_evidence`。

对照记录。比较状态及原因一致、两窗发布值及两类变化均为 null、候选来源与成熟、水位一致、逐单观察截止一致。核对范围内无实质差异。分数与冻结十进制字符串按精确数值比较。

文件 SHA-256 `115afb0b7d40387dc0ef39e22af64af7ede26854d7b923e5ca33ba921d9fadba`。规范化输入 SHA-256 `2617971e97393b5ec170861321e9c903ff51d29e39e4b10d650d4a56844d6f9a`。规范化预期 SHA-256 `98524cc05d73e02db015a6957c876b4cdf7bad02304b390e6d74534d3da9560c`。

本人核查点。找出差 1 微秒的是哪项水位，解释成熟为何仍然通过。

<a id="a3-02"></a>
## A3-02｜UTC 与窗口边界

起点纳入、终点排除。退款观察截止等号纳入，晚 1 微秒排除。同一订单多笔合格退款在 U 中计一次。 [冻结 Fixture](../../tests/fixtures/order_boundaries/02_utc_boundaries.json)

范围为 `domain_a` / `fixture_utc`，地区条件为 `[]`，截至 `2026-09-22T00:00:00Z`，两类水位分别为 `2026-09-15T00:00:00Z` 和 `2026-09-22T00:00:00Z`。

| 订单 | 来源行 | 支付时刻 UTC | 观察截止 | 归属或排除理由 | 产品、组或地区 |
| --- | --- | --- | --- | --- | --- |
| `U-BEFORE` | `u-row-before` | `2026-08-31T23:59:59.999999Z` | `2026-09-07T23:59:59.999999Z` | 支付窗外 | `product_book` / `region_northwest` |
| `U-B-START` | `u-row-b-start` | `2026-09-01T00:00:00Z` | `2026-09-08T00:00:00Z` | 基期 | `product_book` / `region_northwest` |
| `U-B-LAST` | `u-row-b-last` | `2026-09-07T23:59:59.999999Z` | `2026-09-14T23:59:59.999999Z` | 基期 | `product_book` / `region_northwest` |
| `U-C-START` | `u-row-c-start` | `2026-09-08T00:00:00Z` | `2026-09-15T00:00:00Z` | 当前 | `product_book` / `region_northwest` |
| `U-C-LAST` | `u-row-c-last` | `2026-09-14T23:59:59.999999Z` | `2026-09-21T23:59:59.999999Z` | 当前 | `product_book` / `region_northwest` |
| `U-END` | `u-row-end` | `2026-09-15T00:00:00Z` | `2026-09-22T00:00:00Z` | 支付窗外 | `product_book` / `region_northwest` |

| 退款事件 | 来源行 | 所属订单 | 退款时刻 | 计数判断 |
| --- | --- | --- | --- | --- |
| `UR-1` | `u-refund-row-1` | `U-B-START` | `2026-09-08T00:00:00Z` | 合格 |
| `UR-2` | `u-refund-row-2` | `U-B-LAST` | `2026-09-15T00:00:00Z` | 晚于观察截止 |
| `UR-3` | `u-refund-row-3` | `U-C-START` | `2026-09-08T00:00:00Z` | 合格 |
| `UR-4` | `u-refund-row-4` | `U-C-START` | `2026-09-09T00:00:00Z` | 合格 |
| `UR-5` | `u-refund-row-5` | `U-C-LAST` | `2026-09-21T23:59:59.999999Z` | 退款状态非成功 |

| 窗口 | 组或总计 | 支付订单集合 | 退款订单集合 | N | U | 率 |
| --- | --- | --- | --- | --- | --- | --- |
| 基期 | 总计 | `U-B-LAST`、`U-B-START` | `U-B-START` | 2 | 1 | `1/2` |
| 当前 | 总计 | `U-C-LAST`、`U-C-START` | `U-C-START` | 2 | 1 | `1/2` |

两窗最晚观察截止为 `2026-09-14T23:59:59.999999Z` 与 `2026-09-21T23:59:59.999999Z`。比较结果为 `ready`。

绝对变化 `0`，相对变化 `0`。

对照记录。比较状态及原因一致、两窗总计及精确变化一致、候选来源与成熟、水位一致、各窗退款订单集合一致、排除订单一致、UTC 窗界和五条退款事件处理一致。核对范围内无实质差异。分数与冻结十进制字符串按精确数值比较。

文件 SHA-256 `5c842684b3b917dc137607edd87fb558e79d777b94af845bb5edfcd580bf3b82`。规范化输入 SHA-256 `4f8410306b8bc4039212c2ace5e8340fca0acb08d305b2497cfa40f667f61711`。规范化预期 SHA-256 `6551c72bd346f34f71a15c1b95e898f5a27f461b7626990612ed81555d0b58e5`。

本人核查点。核对 UR-1、UR-2 的相对截止时刻，以及 UR-3、UR-4 的去重结果。

<a id="a3-03"></a>
## A3-03｜重复订单质量阻断

完整业务键 (domain_a, fixture_duplicate, D-B) 重复 1 组，涉及 d-row-1、d-row-2，比较不发布。 [冻结 Fixture](../../tests/fixtures/order_boundaries/03_duplicate_orders.json)

范围为 `domain_a` / `fixture_duplicate`，地区条件为 `[]`，截至 `2026-09-22T00:00:00Z`，两类水位分别为 `2026-09-15T00:00:00Z` 和 `2026-09-22T00:00:00Z`。

| 订单 | 来源行 | 支付时刻 UTC | 观察截止 | 归属或排除理由 | 产品、组或地区 |
| --- | --- | --- | --- | --- | --- |
| `D-B` | `d-row-1` | `2026-09-01T00:00:00Z` | `2026-09-08T00:00:00Z` | 基期 | `product_book` / `region_northwest` |
| `D-B` | `d-row-2` | `2026-09-01T00:00:00Z` | `2026-09-08T00:00:00Z` | 基期 | `product_book` / `region_northwest` |
| `D-C` | `d-row-3` | `2026-09-08T00:00:00Z` | `2026-09-15T00:00:00Z` | 当前 | `product_book` / `region_northwest` |

| 退款事件 | 来源行 | 所属订单 | 退款时刻 | 计数判断 |
| --- | --- | --- | --- | --- |
| `DR-1` | `d-refund-row-1` | `D-C` | `2026-09-10T00:00:00Z` | 关键 DQ 阻断，未计入发布指标 |

重复业务键定位以后终止比较，双窗 N、U、率、绝对变化和相对变化均为 `null`。历史本人复核来源仍待补齐，当前版本的复核可单独确认。 [历史证据核对](../regression_checks/A3-03_historical_acceptance.md)

对照记录。比较状态及原因一致、两窗发布值及两类变化均为 null、重复键与来源行一致。核对范围内无实质差异。分数与冻结十进制字符串按精确数值比较。

文件 SHA-256 `606d0c0aefaa385a59c81222e70f779a3a652af97c5bf27c17c8a26a5e0b85a7`。规范化输入 SHA-256 `3dedc50609d23226a5b794c62478d884a793978abda7b30bced61220398f35a9`。规范化预期 SHA-256 `ab5dab62e0b4c4d1fdec4fa151aa51a2153d74a60b952b411310d99fc06a10ef`。

本人核查点。指出重复的是哪个业务键，说明不同来源行为什么仍会阻断。

<a id="a3-04"></a>
## A3-04｜空基期及发布边界

基期诊断 N=0、U=0，当前诊断 N=2、U=1、率 1/2。两窗发布指标和变化均为 null。 [冻结 Fixture](../../tests/fixtures/order_boundaries/04_zero_denominator_window.json)

范围为 `domain_a` / `fixture_zero_denominator`，地区条件为 `[]`，截至 `2026-09-23T00:00:00Z`，两类水位分别为 `2026-09-15T00:00:00Z` 和 `2026-09-23T00:00:00Z`。

| 订单 | 来源行 | 支付时刻 UTC | 观察截止 | 归属或排除理由 | 产品、组或地区 |
| --- | --- | --- | --- | --- | --- |
| `Z-B-INVALID` | `z-row-b-invalid` | `2026-09-02T00:00:00Z` | `2026-09-09T00:00:00Z` | 非有效支付 | `product_book` / `region_northwest` |
| `Z-C-1` | `z-row-c1` | `2026-09-09T00:00:00Z` | `2026-09-16T00:00:00Z` | 当前 | `product_book` / `region_northwest` |
| `Z-C-2` | `z-row-c2` | `2026-09-10T00:00:00Z` | `2026-09-17T00:00:00Z` | 当前 | `product_book` / `region_northwest` |

| 退款事件 | 来源行 | 所属订单 | 退款时刻 | 计数判断 |
| --- | --- | --- | --- | --- |
| `ZR-1` | `z-refund-row-1` | `Z-C-1` | `2026-09-11T00:00:00Z` | 合格 |

以下为候选诊断数，正式双窗 N、U、率、绝对变化和相对变化均为 `null`。

| 窗口 | 组或总计 | 支付订单集合 | 退款订单集合 | N | U | 率 |
| --- | --- | --- | --- | --- | --- | --- |
| 基期 | 总计 | ∅ | ∅ | 0 | 0 | — |
| 当前 | 总计 | `Z-C-1`、`Z-C-2` | `Z-C-1` | 2 | 1 | `1/2` |

两窗最晚观察截止为 — 与 `2026-09-17T00:00:00Z`。比较结果为 `insufficient_evidence`。

对照记录。比较状态及原因一致、两窗发布值及两类变化均为 null、候选来源与成熟、水位一致、各窗退款订单集合一致、排除订单一致、空窗和诊断指标一致。核对范围内无实质差异。分数与冻结十进制字符串按精确数值比较。

文件 SHA-256 `5d2da96ec1dded382eb454fe68ee24f6bedaffeffbd45887e3526072a7d924c2`。规范化输入 SHA-256 `2dfc833a68f7e9896bb8e9fdbfe6a150e85eaf2587e47907652513448474b2f9`。规范化预期 SHA-256 `cda193b179f4f547762d357b8fbff1a0a50f44c4f1782c8df792a6052534d08d`。

本人核查点。区分当前诊断率与发布率，解释空基期为何无法进行比较。

<a id="a3-05"></a>
## A3-05｜单地区 Scope

西北基期 N=2、U=1、率 1/2，当前 N=1、U=1、率 1，绝对变化 1/2。 [冻结 Fixture](../../tests/fixtures/order_boundaries/05_single_region_filter.json)

范围为 `domain_a` / `fixture_region_filter`，地区条件为 `['region_northwest']`，截至 `2026-09-23T00:00:00Z`，两类水位分别为 `2026-09-15T00:00:00Z` 和 `2026-09-23T00:00:00Z`。

| 订单 | 来源行 | 支付时刻 UTC | 观察截止 | 归属或排除理由 | 产品、组或地区 |
| --- | --- | --- | --- | --- | --- |
| `F-N-B1` | `f-row-nb1` | `2026-09-02T00:00:00Z` | `2026-09-09T00:00:00Z` | 基期 | `product_book` / `region_northwest` |
| `F-N-B2` | `f-row-nb2` | `2026-09-03T00:00:00Z` | `2026-09-10T00:00:00Z` | 基期 | `product_book` / `region_northwest` |
| `F-N-C1` | `f-row-nc1` | `2026-09-09T00:00:00Z` | `2026-09-16T00:00:00Z` | 当前 | `product_book` / `region_northwest` |
| `F-S-B1` | `f-row-sb1` | `2026-09-03T00:00:00Z` | `2026-09-10T00:00:00Z` | 地区过滤 | `product_book` / `region_southeast` |
| `F-S-C1` | `f-row-sc1` | `2026-09-10T00:00:00Z` | `2026-09-17T00:00:00Z` | 地区过滤 | `product_book` / `region_southeast` |
| `F-S-C2` | `f-row-sc2` | `2026-09-11T00:00:00Z` | `2026-09-18T00:00:00Z` | 地区过滤 | `product_book` / `region_southeast` |

| 退款事件 | 来源行 | 所属订单 | 退款时刻 | 计数判断 |
| --- | --- | --- | --- | --- |
| `FR-N-B1` | `f-refund-row-nb1` | `F-N-B1` | `2026-09-04T00:00:00Z` | 合格 |
| `FR-N-C1` | `f-refund-row-nc1` | `F-N-C1` | `2026-09-12T00:00:00Z` | 合格 |
| `FR-S-B1` | `f-refund-row-sb1` | `F-S-B1` | `2026-09-05T00:00:00Z` | 所属订单未入 Scope |

| 窗口 | 组或总计 | 支付订单集合 | 退款订单集合 | N | U | 率 |
| --- | --- | --- | --- | --- | --- | --- |
| 基期 | 总计 | `F-N-B1`、`F-N-B2` | `F-N-B1` | 2 | 1 | `1/2` |
| 当前 | 总计 | `F-N-C1` | `F-N-C1` | 1 | 1 | `1` |

两窗最晚观察截止为 `2026-09-10T00:00:00Z` 与 `2026-09-16T00:00:00Z`。比较结果为 `ready`。

绝对变化 `1/2`，相对变化 `1`。

对照记录。比较状态及原因一致、两窗总计及精确变化一致、候选来源与成熟、水位一致、各窗退款订单集合一致、排除订单一致、地区 Scope 一致。核对范围内无实质差异。分数与冻结十进制字符串按精确数值比较。

文件 SHA-256 `d9f621f17385f2b7dcf2e58da70f79627adbf850e56e419f17de7e8baa233da8`。规范化输入 SHA-256 `45a77832c8daf80dd4d9a6c64e05f97ae9cbe1aa8c9f943b5a3f0f1cdf29c3fd`。规范化预期 SHA-256 `2d02934765537b105e3e363a40b7d39d3bfa7f78e34d018a20950a0235326f65`。

本人核查点。核对东南订单及其退款为何都不参与西北比较。

<a id="a3-07"></a>
## A3-07｜同名类别分组

两窗按 `category_a`、`category_b` 各自计数，两个 ID 的展示名均为「图书」。基期总率 1/2，当前总率 1/4。分组 N/U 汇总保持守恒。 [冻结 Fixture](../../tests/fixtures/order_boundaries/07_same_label_distinct_category_ids.json)

范围为 `domain_a` / `fixture_same_label_categories`，地区条件为 `[]`，截至 `2026-09-23T00:00:00Z`，两类水位分别为 `2026-09-15T00:00:00Z` 和 `2026-09-23T00:00:00Z`。

| 订单 | 来源行 | 支付时刻 UTC | 观察截止 | 归属或排除理由 | 产品、组或地区 |
| --- | --- | --- | --- | --- | --- |
| `S-A-B1` | `r07-row-a-b1` | `2026-09-02T00:00:00Z` | `2026-09-09T00:00:00Z` | 基期 | `product_a` / `category_a` / `region_northwest` |
| `S-B-B1` | `r07-row-b-b1` | `2026-09-03T00:00:00Z` | `2026-09-10T00:00:00Z` | 基期 | `product_b` / `category_b` / `region_northwest` |
| `S-A-C1` | `r07-row-a-c1` | `2026-09-09T00:00:00Z` | `2026-09-16T00:00:00Z` | 当前 | `product_a` / `category_a` / `region_northwest` |
| `S-A-C2` | `r07-row-a-c2` | `2026-09-10T00:00:00Z` | `2026-09-17T00:00:00Z` | 当前 | `product_a` / `category_a` / `region_northwest` |
| `S-B-C1` | `r07-row-b-c1` | `2026-09-11T00:00:00Z` | `2026-09-18T00:00:00Z` | 当前 | `product_b` / `category_b` / `region_northwest` |
| `S-B-C2` | `r07-row-b-c2` | `2026-09-12T00:00:00Z` | `2026-09-19T00:00:00Z` | 当前 | `product_b` / `category_b` / `region_northwest` |

| 退款事件 | 来源行 | 所属订单 | 退款时刻 | 计数判断 |
| --- | --- | --- | --- | --- |
| `SR-B-B1` | `r07-refund-b-b1` | `S-B-B1` | `2026-09-05T00:00:00Z` | 合格 |
| `SR-A-C1` | `r07-refund-a-c1` | `S-A-C1` | `2026-09-11T00:00:00Z` | 合格 |

| 窗口 | 组或总计 | 支付订单集合 | 退款订单集合 | N | U | 率 |
| --- | --- | --- | --- | --- | --- | --- |
| 基期 | 总计 | `S-A-B1`、`S-B-B1` | `S-B-B1` | 2 | 1 | `1/2` |
| 基期 | category_a | `S-A-B1` | ∅ | 1 | 0 | `0` |
| 基期 | category_b | `S-B-B1` | `S-B-B1` | 1 | 1 | `1` |
| 当前 | 总计 | `S-A-C1`、`S-A-C2`、`S-B-C1`、`S-B-C2` | `S-A-C1` | 4 | 1 | `1/4` |
| 当前 | category_a | `S-A-C1`、`S-A-C2` | `S-A-C1` | 2 | 1 | `1/2` |
| 当前 | category_b | `S-B-C1`、`S-B-C2` | ∅ | 2 | 0 | `0` |

两窗最晚观察截止为 `2026-09-10T00:00:00Z` 与 `2026-09-19T00:00:00Z`。比较结果为 `ready`。

绝对变化 `-1/4`，相对变化 `-1/2`。

对照记录。比较状态及原因一致、两窗总计及精确变化一致、候选来源与成熟、水位一致、各窗退款订单集合一致、6 条分组及总计、成员来源和 N/U 守恒一致。核对范围内无实质差异。分数与冻结十进制字符串按精确数值比较。

文件 SHA-256 `e03a1c005e6f99f5e497e452bb3de5e75aa2096f83106f730a45ebcbbec737ac`。规范化输入 SHA-256 `cb458cfb0bc5555c8c680bab64885c0f2fd2e212951a12143260eb9ea3e339ca`。规范化预期 SHA-256 `b9640a6dd7dbc73f1e50f94406659d3c869b7000f21282951c33f9e4a848a7e7`。

本人核查点。指出同一展示名对应的两个 ID，任选一窗用来源订单复核分组守恒。

<a id="a3-11"></a>
## A3-11｜单地区过滤后按渠道分组

西北基期 N=3、U=1、率 1/3，当前 N=4、U=3、率 3/4，绝对变化 5/12。 [冻结 Fixture](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)

范围为 `domain_a` / `fixture_single_region_channel_v1_draft`，地区条件为 `['region_northwest']`，截至 `2026-09-23T00:00:00Z`，两类水位分别为 `2026-09-15T00:00:00Z` 和 `2026-09-23T00:00:00Z`。

| 订单 | 来源行 | 支付时刻 UTC | 观察截止 | 归属或排除理由 | 产品、组或地区 |
| --- | --- | --- | --- | --- | --- |
| `K11-N-B-W1` | `r11-order-n-b-web-1` | `2026-09-02T00:00:00Z` | `2026-09-09T00:00:00Z` | 基期 | `product_book` / `channel_web` / `region_northwest` |
| `K11-N-B-W2` | `r11-order-n-b-web-2` | `2026-09-03T00:00:00Z` | `2026-09-10T00:00:00Z` | 基期 | `product_book` / `channel_web` / `region_northwest` |
| `K11-N-B-A1` | `r11-order-n-b-app-1` | `2026-09-04T00:00:00Z` | `2026-09-11T00:00:00Z` | 基期 | `product_book` / `channel_app` / `region_northwest` |
| `K11-N-C-W1` | `r11-order-n-c-web-1` | `2026-09-09T00:00:00Z` | `2026-09-16T00:00:00Z` | 当前 | `product_book` / `channel_web` / `region_northwest` |
| `K11-N-C-A1` | `r11-order-n-c-app-1` | `2026-09-10T00:00:00Z` | `2026-09-17T00:00:00Z` | 当前 | `product_book` / `channel_app` / `region_northwest` |
| `K11-N-C-A2` | `r11-order-n-c-app-2` | `2026-09-11T00:00:00Z` | `2026-09-18T00:00:00Z` | 当前 | `product_book` / `channel_app` / `region_northwest` |
| `K11-N-C-A3` | `r11-order-n-c-app-3` | `2026-09-12T00:00:00Z` | `2026-09-19T00:00:00Z` | 当前 | `product_book` / `channel_app` / `region_northwest` |
| `K11-S-B-W1` | `r11-order-s-b-web-1` | `2026-09-05T00:00:00Z` | `2026-09-12T00:00:00Z` | 地区过滤 | `product_book` / `channel_web` / `region_southeast` |
| `K11-S-B-A1` | `r11-order-s-b-app-1` | `2026-09-06T00:00:00Z` | `2026-09-13T00:00:00Z` | 地区过滤 | `product_book` / `channel_app` / `region_southeast` |
| `K11-S-C-W1` | `r11-order-s-c-web-1` | `2026-09-13T00:00:00Z` | `2026-09-20T00:00:00Z` | 地区过滤 | `product_book` / `channel_web` / `region_southeast` |
| `K11-S-C-A1` | `r11-order-s-c-app-1` | `2026-09-14T00:00:00Z` | `2026-09-21T00:00:00Z` | 地区过滤 | `product_book` / `channel_app` / `region_southeast` |

| 退款事件 | 来源行 | 所属订单 | 退款时刻 | 计数判断 |
| --- | --- | --- | --- | --- |
| `KR11-N-B-A1` | `r11-refund-n-b-app-1` | `K11-N-B-A1` | `2026-09-05T00:00:00Z` | 合格 |
| `KR11-N-C-W1` | `r11-refund-n-c-web-1` | `K11-N-C-W1` | `2026-09-10T00:00:00Z` | 合格 |
| `KR11-N-C-A1` | `r11-refund-n-c-app-1` | `K11-N-C-A1` | `2026-09-11T00:00:00Z` | 合格 |
| `KR11-N-C-A2` | `r11-refund-n-c-app-2` | `K11-N-C-A2` | `2026-09-12T00:00:00Z` | 合格 |
| `KR11-S-B-W1` | `r11-refund-s-b-web-1` | `K11-S-B-W1` | `2026-09-06T00:00:00Z` | 所属订单未入 Scope |
| `KR11-S-C-A1` | `r11-refund-s-c-app-1` | `K11-S-C-A1` | `2026-09-15T00:00:00Z` | 所属订单未入 Scope |

| 窗口 | 组或总计 | 支付订单集合 | 退款订单集合 | N | U | 率 |
| --- | --- | --- | --- | --- | --- | --- |
| 基期 | 总计 | `K11-N-B-A1`、`K11-N-B-W1`、`K11-N-B-W2` | `K11-N-B-A1` | 3 | 1 | `1/3` |
| 基期 | channel_app | `K11-N-B-A1` | `K11-N-B-A1` | 1 | 1 | `1` |
| 基期 | channel_web | `K11-N-B-W1`、`K11-N-B-W2` | ∅ | 2 | 0 | `0` |
| 当前 | 总计 | `K11-N-C-A1`、`K11-N-C-A2`、`K11-N-C-A3`、`K11-N-C-W1` | `K11-N-C-A1`、`K11-N-C-A2`、`K11-N-C-W1` | 4 | 3 | `3/4` |
| 当前 | channel_app | `K11-N-C-A1`、`K11-N-C-A2`、`K11-N-C-A3` | `K11-N-C-A1`、`K11-N-C-A2` | 3 | 2 | `2/3` |
| 当前 | channel_web | `K11-N-C-W1` | `K11-N-C-W1` | 1 | 1 | `1` |

两窗最晚观察截止为 `2026-09-11T00:00:00Z` 与 `2026-09-19T00:00:00Z`。比较结果为 `ready`。

绝对变化 `5/12`，相对变化 `5/4`。

对照记录。比较状态及原因一致、两窗总计及精确变化一致、候选来源与成熟、水位一致、各窗退款订单集合一致、排除订单一致、地区 Scope 一致、6 条分组及总计、成员来源和 N/U 守恒一致、东南退款来源的排除和独立冻结文件一致。核对范围内无实质差异。分数与冻结十进制字符串按精确数值比较。

文件 SHA-256 `d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8`。规范化输入 SHA-256 `459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257`。规范化预期 SHA-256 `27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91`。

本人核查点。任选一窗把两渠道的 N/U 加回总计，并核对东南订单及退款已排除。

## 复跑证据

CPython 3.10.12、pytest 9.1.1，本地开发工作树。开发 HEAD 为 `dac944de1efb9ae86e624756f80360bfba944ed3`，公开对照提交为 `cb247ffd767d9c38d32492bc92bf2d8ff4d12c49`。

标准库检查退出码 `0`，87 份证据通过。专项 pytest 退出码 `0`，实际为 `12 passed in 0.37s`。未签收标为 approved、缺少回执和回执错绑的拒绝用例均通过。

```bash
python3 -I -B reference/regression_checks/check_g0_development_manifest.py
PYTHONPATH=src .venv/bin/python -B -m pytest -v tests/test_g0_development_manifest.py -o addopts= -p no:cacheprovider
```

```text
20b7218955a231bbc9993dea8b729fddaaee68dba075f0831c3245323d0396e4  reference/regression_checks/G0_development_manifest.json
6deb24d28b1ef77793d81609470055fa60c75f9e84edb278be6a4a8a9a7d18aa  reference/regression_checks/check_g0_development_manifest.py
3626354af59185efda9e23c35bac8d6a48c1b4ca94f958066920489ab5a11562  tests/test_g0_development_manifest.py
```

本轮七例的本人确认见回执，其他四个主例沿用已有回执。阶段门结论见 G0 覆盖矩阵。
