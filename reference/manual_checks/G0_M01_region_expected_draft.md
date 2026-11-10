# G0 M01：region独立预期台账草稿

日期：2026-11-07（Asia/Shanghai）。状态：**人工预期设计稿，未冻结、未运行region计算，不是用户本人独立验收。** 本轮只展开[11号Fixture](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)的input逐单推导；未导入或调用待测/总体/类别/渠道函数生成下列答案。作者已知历史渠道总计，不称首次盲审。旧expected不修改，本文件也不替代它。

规则来源：[DD02 §1/2/4](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)。局部region归类规则取自[region契约草案](G0_M01_region_plan.md)，该草案SHA-256为20200d0af6c99bf4118d7ea0d81ebd22ab1f3a03084148b79606da56d1949b2c，尚未批准冻结；涉及未知/目录缺失的预期须连同该规则先冻结再执行。

## 1. 固定输入与两个Scope

原输入域为domain_a，快照为fixture_single_region_channel_v1_draft；H=604800秒，所有下列时间均为2026年UTC零点。基期[09-01,09-08)，当前[09-08,09-15)，as_of=09-23，支付水位=09-15，退款水位=09-23。原始11笔支付均有效，六笔退款均为success。

- W：原冻结西北Scope，filters.region_ids=["region_northwest"]，不改输入。
- A：深拷贝后仅把filters.region_ids改为[]，另行声明“合成主体假定获两地授权”。它不是原任务Scope的更新，也不是生产授权证据。

原Fixture完整SHA-256为d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8，原独立expected为c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e，原规范化input为459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257。本轮不生成控制JSON或新基线哈希；后续应绑定A及各变体实际装配后的输入，不以原input哈希冒充变体哈希。

## 2. 逐订单支付与成熟依据

NW=region_northwest，SE=region_southeast；B=基期，C=当前。业务键均带上节固定域/快照，不按ID字面中的N/S判断地区，以下分组来自原始region_id字段。

| 订单ID | 窗口/地区 | paid_at | paid_at+H | 支付来源source_row_id |
| --- | --- | --- | --- | --- |
| K11-N-B-W1 | B/NW | 09-02 | 09-09 | r11-order-n-b-web-1 |
| K11-N-B-W2 | B/NW | 09-03 | 09-10 | r11-order-n-b-web-2 |
| K11-N-B-A1 | B/NW | 09-04 | 09-11 | r11-order-n-b-app-1 |
| K11-N-C-W1 | C/NW | 09-09 | 09-16 | r11-order-n-c-web-1 |
| K11-N-C-A1 | C/NW | 09-10 | 09-17 | r11-order-n-c-app-1 |
| K11-N-C-A2 | C/NW | 09-11 | 09-18 | r11-order-n-c-app-2 |
| K11-N-C-A3 | C/NW | 09-12 | 09-19 | r11-order-n-c-app-3 |
| K11-S-B-W1 | B/SE | 09-05 | 09-12 | r11-order-s-b-web-1 |
| K11-S-B-A1 | B/SE | 09-06 | 09-13 | r11-order-s-b-app-1 |
| K11-S-C-W1 | C/SE | 09-13 | 09-20 | r11-order-s-c-web-1 |
| K11-S-C-A1 | C/SE | 09-14 | 09-21 | r11-order-s-c-app-1 |

每笔支付属于对应半开窗口。W的最大成熟时刻为09-19，A为09-21；原as_of及退款水位09-23均覆盖，支付水位等于最大窗口end 09-15。原W/A均应ready，不能因A中东南更晚成熟而暗中删掉它们。

## 3. 逐退款归属依据

以下每个事件均在所属支付单[paid_at,paid_at+H]内且≤as_of，因此计入该支付窗/地区的退款订单集合；各事件当前对应不同订单。事件来源与支付来源分开，均保留完整Scope关联。

| refund_id | 所属order_id | refund_at | 退款来源source_row_id |
| --- | --- | --- | --- |
| KR11-N-B-A1 | K11-N-B-A1 | 09-05 | r11-refund-n-b-app-1 |
| KR11-N-C-W1 | K11-N-C-W1 | 09-10 | r11-refund-n-c-web-1 |
| KR11-N-C-A1 | K11-N-C-A1 | 09-11 | r11-refund-n-c-app-1 |
| KR11-N-C-A2 | K11-N-C-A2 | 09-12 | r11-refund-n-c-app-2 |
| KR11-S-B-W1 | K11-S-B-W1 | 09-06 | r11-refund-s-b-web-1 |
| KR11-S-C-A1 | K11-S-C-A1 | 09-15 | r11-refund-s-c-app-1 |

地区目录来源分别为r11-region-northwest、r11-region-southeast，完整键均为(domain_a,fixture_single_region_channel_v1_draft,region_id)，label分别为西北/东南。产品关联固定product_book，来源r11-product-book；其类别和渠道字段不参与region分组。

## 4. 手工集合与六行预期

下表既是来源集合的分区依据，也是数值的人工Oracle；不得由待测输出填这些集合。

| 窗口/组 | 支付订单集合P_g | 退款订单集合R_g |
| --- | --- | --- |
| B/NW | K11-N-B-W1、K11-N-B-W2、K11-N-B-A1 | K11-N-B-A1 |
| B/SE | K11-S-B-W1、K11-S-B-A1 | K11-S-B-W1 |
| C/NW | K11-N-C-W1、K11-N-C-A1、K11-N-C-A2、K11-N-C-A3 | K11-N-C-W1、K11-N-C-A1、K11-N-C-A2 |
| C/SE | K11-S-C-W1、K11-S-C-A1 | K11-S-C-A1 |

A的手工预期：

| window_index | dimension_id / group_id | N | U | 精确率 | 计算依据 |
| --- | --- | --- | --- | --- | --- |
| 0 | None / None | 5 | 2 | 2/5 | (3+2)单，(1+1)退款单 |
| 0 | region / region_northwest | 3 | 1 | 1/3 | B/NW集合 |
| 0 | region / region_southeast | 2 | 1 | 1/2 | B/SE集合 |
| 1 | None / None | 6 | 4 | 2/3 | (4+2)单，(3+1)退款单 |
| 1 | region / region_northwest | 4 | 3 | 3/4 | C/NW集合 |
| 1 | region / region_southeast | 2 | 1 | 1/2 | C/SE集合 |

A总体绝对变化=2/3−2/5=4/15，相对变化=(4/15)/(2/5)=2/3。两窗各组支付及退款订单互斥穷尽，ΣN分别为5、6，ΣU分别为2、4；组率不能直接相加或平均。

W只保留B/NW、C/NW：基期总计及唯一地区组均N=3/U=1/率1/3，当前均N=4/U=3/率3/4，绝对变化=5/12，相对变化=5/4。每窗一地区行加一总计行，共四行。四笔SE订单和两笔SE退款的来源必须全部排除；不输出region_southeast或unknown行。单地区行与总计一致是退化契约，不是新的地区解释能力。

## 5. 退款控制的手工预期

- D：在A上只追加一笔success退款，refund_id=KR11-RG03-S-C-SECOND，order_id=K11-S-C-A1，refund_at=2026-09-16T00:00:00Z，source_row_id=r11-rg03-s-c-second，域/快照不变。该支付09-14、H末端09-21，原退款09-15、新退款09-16均合法。C/SE合格事件从1笔变2笔，退款订单仍为{K11-S-C-A1}，U仍1；A六行、总体变化和两类订单台账不变。该组退款事件来源新增一项，不能假定“一个退款订单只有一条事件”。
- T：在A上只把KR11-S-B-W1的refund_at从09-06改为2026-09-09T00:00:00Z，保留ID和来源。支付09-05、H末端09-12，退款仍有效；虽然事件发生在当前日历窗，仍属于B/SE支付队列。所有数值/订单集合和六条行不变，不转移到C/SE。
- Z：在A上只移除KR11-S-B-W1。B/SE支付仍2单、U=0、率0，须保留该地区行；基期总计N=5/U=1/率1/5，当前6/4/率2/3，绝对变化7/15，相对变化7/3，ready。其他组来源不变，该退款事件来源仅从基期计数集合移除。

## 6. 成熟、水位与空窗预期

各控制独立基于A深拷贝，不叠加单故障；候选订单仍为第4节集合，除空窗控制外不变。quality_checks仅核对总体原有三个布尔值，不把手工诊断N/U当成参考函数已返回的字段。

| 控制 | 唯一输入变更 | outcome / 唯一原因 | mature / payments / refunds |
| --- | --- | --- | --- |
| M− | as_of=2026-09-20T23:59:59.999999Z | insufficient_evidence / 观察期未成熟 | false / true / true |
| P− | payments_through=2026-09-14T23:59:59.999999Z | insufficient_evidence / 支付水位不足 | true / false / true |
| R− | refunds_through=2026-09-20T23:59:59.999999Z | insufficient_evidence / 退款水位不足 | true / true / false |
| M= | as_of=2026-09-21T00:00:00Z | ready / 无原因 | true / true / true |
| R= | refunds_through=2026-09-21T00:00:00Z | ready / 无原因 | true / true / true |

原A支付水位09-15已是P=等号正例，由正常样例覆盖，不另造同输入测试。M=/R=时原六笔退款均已发生，仍匹配第4节六行，不改变as_of以绕过成熟。

M−/P−/R−均不发布任一窗口指标及变化：metrics两个窗口的N/U/rate和两项变化全部None，aggregate_rows=[]，两类分组台账={}；候选诊断保留。不是ValueError或生产blocked_by_quality。

E：将A的五笔基期支付K11-N-B-W1、K11-N-B-W2、K11-N-B-A1、K11-S-B-W1、K11-S-B-A1全部设is_payment_valid=False，其他字段不变。基期候选为空，当前候选仍六单；quality三项true，唯一原因为支付窗口无有效样本，同样全比较不发布。不能照搬西北C05只关三笔，否则A仍有东南两笔基期支付，并未形成空基期。

Q：单独将A的两笔SE基期支付K11-S-B-W1、K11-S-B-A1设无效，其他支付仍有效。基期只剩NW组3/1/率1/3，SE组不输出；当前N=6/U=4/率2/3，绝对变化1/3、相对变化1，仍ready。E是总体空窗阻断，Q是缺席组不补行，两者不可混淆。

原西北C05的09-19边界只对W有效：as_of=09-19时W应ready，A尚有09-20/09-21成熟订单，不能沿用为全地区等号正例。本矩阵不复制原C05的时间常量或通道聚合行。

## 7. 身份/未知规则采用后的预期设计

本节以未冻结的region局部草案为前提，不能标为现有冻结行为或已验收；采用该契约时须先冻结本节及变更清单，再实现。

- L：A中两个地区label设为“同名地区”，其他字段不变。两地区ID、数值和来源保持第4节；只变group_label。单独将SE已登记条目的label设None或删除label字段，仍保留region_southeast及原2/1比率，不并入unknown。
- U：A中只将K11-S-C-A1的region_id设为__unknown__，或另一个无目录条目的有效非空ID region_unregistered_rg05，两种变体分开。原始支付/退款ID及来源不变：当前SE剩K11-S-C-W1，N=1/U=0/率0；unknown为K11-S-C-A1，N=1/U=1/率1；NW组仍4/3/率3/4；当前总计仍6/4/率2/3。基期不变，unknown基期不输出，共七条实际聚合行。原ID/unknown原因另记来源台账，不修改源订单伪装成已登记地区。
- W-U：对同一个U变体保持W西北过滤，两个U变体的该订单仍不属于西北候选，第4节W全部结果及排除来源不变；不是将未知组强塞进单地区Scope。
- F：W的过滤列表独立改为["region_unregistered_filter_rg05"]或["__unknown__"]时应ValueError；不是正常空窗或unknown数据组。另一个独立变体只将K11-S-C-A1.region_id设None，同样ValueError，不自动修成U。产品关键缺失、目录重复或混域始终拒绝，不降级为本节unknown。

以上预期均为基于来源集合的人工设计值，未从任何函数输出写入。没有修改11号原expected或其他冻结Fixture，未运行pytest；本稿与[测试矩阵](G0_M01_region_test_matrix.md)一同供后续规则/预期冻结使用，不构成M01关闭证据。
