# M03：A3-08v2独立贡献台账草稿

日期：2026-11-18（Asia/Shanghai）。状态：**人工先行贡献预期草稿，非正式冻结JSON或参考计算输出。** 本次复用既有逐单人工台账，先将以下权重、率及四类贡献逐步写成精确分数并保存，再另用标准库Fraction检查算术与来源；不调用calculate_category_reference、待实现贡献函数、生产代码或SQL生成答案。

本会话已知既有组N/U及目标总体变化1/2，不声称首次盲审、第二审核人或用户本人独立验收。旧A3-08v1/v2输入、expected及人工台账均保留原字节；本稿单独补充贡献，不追改旧Oracle“未计算贡献”的历史声明。

## 1. 依据、输入与来源版本

唯一公式沿用[DD02 §2](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md#metric)和[已固定的M03公式/边界](G0_M03_formula_boundary_review.md)。N/U及支付、退款成员复用[08v2逐单说明](A3-08_v2_expected.md)与[独立组/总计Oracle](A3-08_v2_expected.json)，仅回查[原Fixture的input](../../tests/fixtures/order_boundaries/08_category_entry_exit.json)确认来源，不从参考函数反推贡献。

| 绑定对象 | SHA-256 |
| --- | --- |
| DD02 v1.2 | 3c5452e0121db488da05686bdbda8d8ec38dc4107ed71837862943e518fc83b0 |
| 指标目录 v1.2 | 51b2d179259c7e6d077491d319bf5da7b0f477c817d55db90dcb10861c0a2bce |
| 本轮引用的M03公式/边界记录 | f81fa9941ca9a74ed1b2ae8aa00a1ec0487cc2cce195e65cc65965f30449d995 |
| 08v2完整Fixture | 79912e4cec13c3ab34482b02c24deeda4ec443caf569839e4ee5572958550e58 |
| 08v2规范化input | 4cf45c7f2404ffd854393e21936fb288981491d98d5cd2e9951bcfedf46f49fb |
| 既有人工逐单说明 | 5100c04b432ca3eb21214f6b8d14d4dbd9be3313798aab854f98d88098d9dbb6 |
| 既有组/总计Oracle | 1b1d63e22f6285cf43f64f8c2db1ce1da39070af6f801840cc47ba596aa159da |

规范化input指纹沿用UTF-8 json.dumps(input,ensure_ascii=False,sort_keys=True,separators=(',',':'))，数组不重排，不含尾换行；与完整文件哈希区分。以上仅绑定本草稿所用版本，不创建新的生产metric_version或approved manifest。

## 2. 固定Scope、产品关联及逐单来源

固定domain_id=domain_a、snapshot_id=fixture_category_entry_exit_v2，维度category，filters.region_ids=[]。基期为[2026-09-01T00:00:00Z,2026-09-08T00:00:00Z)，当前为[2026-09-08T00:00:00Z,2026-09-15T00:00:00Z)。H=604800秒；as_of及退款水位为2026-09-23T00:00:00Z，支付水位为2026-09-15T00:00:00Z。

下表中的订单、退款事件、产品和类别ID一律附属上述Scope：完整订单键=(domain_a,fixture_category_entry_exit_v2,order_id)，事件键末位换为refund_id，产品键末位换为product_id。不得按裸ID跨Scope复用。退款按支付订单的窗口及类别归属，U按订单而非事件数计数。

| 稳定类别ID | 产品复合键末位 | 原始目录定位 |
| --- | --- | --- |
| category_a（A） | product_a | input.dimensions.products[0]及categories[0] |
| category_b（B） | product_b | input.dimensions.products[1]及categories[1] |
| category_c（C） | product_c | input.dimensions.products[2]及categories[2] |

此Fixture的产品/类别目录没有source_row_id，以上用绑定文件内的数组位置及完整键定位，不虚构目录来源行；支付和退款保留原source_row_id。展示名只显示，不决定组身份。

以下日期均为2026年UTC零点，N/U为该支付订单对所属组计数的贡献；“无”是完整退款台账中没有该订单的事件。

| 支付窗/类别 | 订单ID | 支付来源 | 支付日→成熟日 | 成功退款事件 | 退款来源 | 退款日 | 单笔N/U |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline/A | E2-A-B1 | r08v2-row-a-b1 | 09-02→09-09 | 无 | 无 | 无 | 1/0 |
| baseline/A | E2-A-B2 | r08v2-row-a-b2 | 09-03→09-10 | 无 | 无 | 无 | 1/0 |
| baseline/B | E2-B-B1 | r08v2-row-b-b1 | 09-04→09-11 | ER2-B-B1 | r08v2-refund-b-b1 | 09-06 | 1/1 |
| baseline/B | E2-B-B2 | r08v2-row-b-b2 | 09-05→09-12 | ER2-B-B2 | r08v2-refund-b-b2 | 09-07 | 1/1 |
| current/A | E2-A-C1 | r08v2-row-a-c1 | 09-09→09-16 | ER2-A-C1 | r08v2-refund-a-c1 | 09-11 | 1/1 |
| current/C | E2-C-C1 | r08v2-row-c-c1 | 09-10→09-17 | ER2-C-C1 | r08v2-refund-c-c1 | 09-12 | 1/1 |
| current/C | E2-C-C2 | r08v2-row-c-c2 | 09-11→09-18 | ER2-C-C2 | r08v2-refund-c-c2 | 09-13 | 1/1 |
| current/C | E2-C-C3 | r08v2-row-c-c3 | 09-12→09-19 | ER2-C-C3 | r08v2-refund-c-c3 | 09-14 | 1/1 |

逐单成熟均被既有as_of/退款水位覆盖，支付水位等于当前窗口末端；六笔成功退款均在各自支付后2天、闭合7天观察期内。没有新增异常或变更过滤。本轮复用这些已核算前提，不用程序输出替换原始人工依据。

## 3. 生命周期、分母及逐组权重/率

G0={category_a,category_b}，G1={category_a,category_c}，因此shared={category_a}、exit={category_b}、entry={category_c}。三类互斥且覆盖并集。基期C、当前B没有支付组，不补行、不定义缺席组退款率。

逐窗汇总：

```text
N0 = N_A0 + N_B0 = 2 + 2 = 4
U0 = U_A0 + U_B0 = 0 + 2 = 2
R0 = U0/N0 = 2/4 = 1/2

N1 = N_A1 + N_C1 = 1 + 3 = 4
U1 = U_A1 + U_C1 = 1 + 3 = 4
R1 = U1/N1 = 4/4 = 1
Δ  = R1 - R0 = 1 - 1/2 = 1/2
```

| 实际支付组 | N/U | 权重w=N组/N总体 | 退款率r=U组/N组 | 加权率w×r |
| --- | --- | --- | --- | --- |
| baseline/A | 2/0 | 2/4=1/2 | 0/2=0 | (1/2)×0=0 |
| baseline/B | 2/2 | 2/4=1/2 | 2/2=1 | (1/2)×1=1/2 |
| current/A | 1/1 | 1/4 | 1/1=1 | (1/4)×1=1/4 |
| current/C | 3/3 | 3/4 | 3/3=1 | (3/4)×1=3/4 |

基期权重1/2+1/2=1，当前1/4+3/4=1；加权率分别0+1/2=1/2和1/4+3/4=1。权重分母只取该窗过滤后N，不取两窗订单总数8。A基期率为0是正分母的真实零退款，不是缺席。

## 4. 共享A：对称within与structure

A基期两笔支付来源r08v2-row-a-b1/a-b2，无退款；当前唯一支付来源r08v2-row-a-c1，退款ER2-A-C1来自r08v2-refund-a-c1。对应w_A0=1/2、r_A0=0、w_A1=1/4、r_A1=1。

```text
平均权重 = (w_A1 + w_A0)/2
         = (1/4 + 1/2)/2 = (1/4 + 2/4)/2 = (3/4)/2 = 3/8
组率差   = r_A1 - r_A0 = 1 - 0 = 1
within_A = 平均权重 × 组率差 = (3/8)×1 = 3/8

平均组率    = (r_A1 + r_A0)/2 = (1 + 0)/2 = 1/2
权重差      = w_A1 - w_A0 = 1/4 - 1/2 = 1/4 - 2/4 = -1/4
structure_A = 平均组率 × 权重差 = (1/2)×(-1/4) = -1/8

A净贡献 = within_A + structure_A = 3/8 - 1/8 = 2/8 = 1/4
独立恒等式回查 = w_A1*r_A1 - w_A0*r_A0
               = (1/4)×1 - (1/2)×0 = 1/4
```

结构项保留负号：A的支付权重从1/2降至1/4，平均组率为1/2，故结构项为-1/8。不能只看A率升至1就把两个贡献都写成正数。A不是entry/exit，不为其另外计新增或退出项。

## 5. 退出B与新增C

B仅基期存在，支付E2-B-B1/B2分别来自r08v2-row-b-b1/b-b2；两单退款ER2-B-B1/B2分别来自r08v2-refund-b-b1/b-b2。N_B0=2、U_B0=2，故只用基期w_B0=1/2、r_B0=1：

```text
exit_B = -w_B0*r_B0 = -(2/4)×(2/2) = -(1/2)×1 = -1/2
```

B当前缺席，不填r_B1=0，不计算B的within/structure或跨窗组率差。此-1/2是按冻结公式移去基期加权率的代数项，不是声称“退出类别使业务改善”的因果结论。

C仅当前存在，支付E2-C-C1/C2/C3分别来自r08v2-row-c-c1/c-c2/c-c3；退款ER2-C-C1/C2/C3分别来自r08v2-refund-c-c1/c-c2/c-c3。N_C1=3、U_C1=3，故只用当前w_C1=3/4、r_C1=1：

```text
entry_C = w_C1*r_C1 = (3/4)×(3/3) = (3/4)×1 = 3/4
```

C基期缺席，不填r_C0=0，不计算C的within/structure或跨窗组率差。新增/退出贡献都按相应窗口的总体N为权重分母，不把它们单独当作N=1的平均类别。

## 6. 四类贡献、严格合计及残差

以下全部为精确ratio；“—”表示不适用，不是缺席窗的零退款率，也不要求未来接口补零贡献字段。

| 类别/身份 | within | structure | entry | exit | 该组适用项之和 |
| --- | --- | --- | --- | --- | --- |
| A/shared | 3/8 | -1/8 | — | — | 1/4 |
| B/exit | — | — | — | -1/2 | -1/2 |
| C/entry | — | — | 3/4 | — | 3/4 |
| 四类总计 | 3/8 | -1/8 | 3/4 | -1/2 | 1/2 |

逐项通分，不使用浮点或显示值：

```text
C = 3/8 + (-1/8) + 3/4 + (-1/2)
  = 3/8 - 1/8 + 6/8 - 4/8
  = (3 - 1 + 6 - 4)/8 = 4/8 = 1/2

residual = Δ - C = 1/2 - 1/2 = 0
```

另一方向按组加总：A的1/4 + B的(-1/2) + C的3/4 = (1-2+3)/4 = 2/4 = 1/2，与总体R1-R0一致。不能仅通过残差为0代替四个分量分别正确；本稿每项均按DD02指定公式逐步计算。

贡献对应within=37.5个百分点、structure=-12.5个百分点、entry=75个百分点、exit=-50个百分点，合计50个百分点。这些显示值只帮助阅读，验算使用以上Fraction。总体相对变化为1，与本贡献和1/2不是同一个量；所有贡献不作因果解释，也不能与region/channel分解相加。

## 7. 检查、待办与验收状态

本稿先于本轮程序验算保存。后续标准库检查只核对手填分数和已有逐单来源，结果以[独立算术/来源核验输出](../regression_checks/G0_M03_A3-08_v2_manual_check.txt)为准；不是调用待实现贡献函数回填预期，也不是pytest或CI。

本轮不创建机器可读贡献expected、不实现贡献参考入口、不修改旧Fixture/Oracle，也不扩大生产Runtime。下一步可先审核这份草稿，再据此整理独立机器预期及正式冻结记录；参考计算与固定回归须在先行预期保存后另行实施。当前M03 Must/G0仍开放，用户本人独立验收仍未取得；本稿及核验记录仅在本地，尚未提交/推送。
