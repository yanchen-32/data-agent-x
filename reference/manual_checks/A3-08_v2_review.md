# A3-08 v2 冻结输入、版本差异与订单归属核对

核对日期：2026-10-27。结论：当前文件与既有冻结指纹一致，八笔订单、退款来源及静态预期吻合；未发现差异。本记录核验既有证据，不重新生成或冻结另一套答案，不冒称首次盲审、用户本人签字或生产验收。

## 核对依据与范围

读取 [当前v2 Fixture](../../tests/fixtures/order_boundaries/08_category_entry_exit.json)、[既有独立推导及冻结记录](A3-08_v2_expected.md)、[先行数值台账](A3-08_v2_expected.json)，并与 [v1冻结输入](../../tests/fixtures/order_boundaries/08_category_entry_exit.v1.json) 及 [v1台账](A3-08_review.json) 对照。本轮仅新增本记录；不修改任一Fixture、既有台账、Oracle、实现或测试。

## 冻结指纹

以下SHA-256均为本轮实际读取文件后计算，与既有冻结记录一致：

| 对象 | SHA-256 |
| --- | --- |
| 08_category_entry_exit.json（v2完整文件） | 79912e4cec13c3ab34482b02c24deeda4ec443caf569839e4ee5572958550e58 |
| 08_category_entry_exit.v1.json（v1完整文件） | b2ffe9d156a9e010f28bbfda072589c95b8ee8dd426f98a0da8c1515ed0cb580 |
| A3-08_v2_expected.json（v2先行预期） | 1b1d63e22f6285cf43f64f8c2db1ce1da39070af6f801840cc47ba596aa159da |
| A3-08_review.json（v1先行台账） | e6e0f2408aa31082232e7e8ccb74ecb48b76e06bdaced8266c790a96c97ddd3b |
| v2规范化input | 4cf45c7f2404ffd854393e21936fb288981491d98d5cd2e9951bcfedf46f49fb |

input规范化方法：`json.dumps(input, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')`。v2的`supersedes.sha256`准确指向上表v1指纹。完整文件指纹包含原始input、expected及元数据，不能与规范化input指纹混用。当前JSON中的初稿状态文字属于创建阶段证据，不为本轮核对改写；已有阶段进展以冻结记录为准。

## v1与v2的差异

| 核对项 | v1冻结历史 | v2当前快照 |
| --- | --- | --- |
| snapshot_id | fixture_category_entry_exit | fixture_category_entry_exit_v2 |
| 支付订单 / 退款事件数 | 6 / 2 | 8 / 6 |
| 基期A：N/U/率 | 1/0/0 | 2/0/0 |
| 基期B：N/U/率 | 1/1/1 | 2/2/1 |
| 当前A：N/U/率 | N=2，U=1，率=1/2 | N=1，U=1，率=1 |
| 当前C：N/U/率 | 2/0/0 | 3/3/1 |
| 基期总计：N、U、率 | 2、1、1/2 | 4、2、1/2 |
| 当前总计：N、U、率 | 4、1、1/4 | 4、4、1 |
| 总体绝对 / 相对变化 | −1/4 / −1/2 | 1/2 / 1 |
| A支付占比：基期→当前 | 1/2→1/2 | 1/2→1/4 |

域仍为domain_a，UTC双窗、7天成熟期、as_of及两类水位均保持原口径；产品与类别ID映射不变，目录复合键中的快照随版本隔离。v2订单ID前缀为E2-、退款ID前缀为ER2-，来源行前缀为r08v2-，不是向v1旧快照混入两单。v2共享A的率与支付占比均变化，退出B、新增C均有有效退款，为后续非平凡贡献测试提供输入；本阶段不核算贡献分解。

## 八笔订单归属与退款核对

基期为`[2026-09-01T00:00:00Z,2026-09-08T00:00:00Z)`，当前为`[2026-09-08T00:00:00Z,2026-09-15T00:00:00Z)`。以下日期均为2026年UTC零点，八单支付有效性均为true，地区过滤为空。

| 订单ID / 支付来源行 | 支付日→成熟日 | 产品→类别 / 窗口 | 成功退款ID / 来源行 / 日期 | N、U贡献 |
| --- | --- | --- | --- | --- |
| E2-A-B1 / r08v2-row-a-b1 | 09-02→09-09 | product_a→category_a / 基期 | 无 | 1、0 |
| E2-A-B2 / r08v2-row-a-b2 | 09-03→09-10 | product_a→category_a / 基期 | 无 | 1、0 |
| E2-B-B1 / r08v2-row-b-b1 | 09-04→09-11 | product_b→category_b / 基期 | ER2-B-B1 / r08v2-refund-b-b1 / 09-06 | 1、1 |
| E2-B-B2 / r08v2-row-b-b2 | 09-05→09-12 | product_b→category_b / 基期 | ER2-B-B2 / r08v2-refund-b-b2 / 09-07 | 1、1 |
| E2-A-C1 / r08v2-row-a-c1 | 09-09→09-16 | product_a→category_a / 当前 | ER2-A-C1 / r08v2-refund-a-c1 / 09-11 | 1、1 |
| E2-C-C1 / r08v2-row-c-c1 | 09-10→09-17 | product_c→category_c / 当前 | ER2-C-C1 / r08v2-refund-c-c1 / 09-12 | 1、1 |
| E2-C-C2 / r08v2-row-c-c2 | 09-11→09-18 | product_c→category_c / 当前 | ER2-C-C2 / r08v2-refund-c-c2 / 09-13 | 1、1 |
| E2-C-C3 / r08v2-row-c-c3 | 09-12→09-19 | product_c→category_c / 当前 | ER2-C-C3 / r08v2-refund-c-c3 / 09-14 | 1、1 |

订单通过`(domain_a,fixture_category_entry_exit_v2,product_id)`唯一关联产品，再以稳定category_id归组，展示名不参与身份。退款通过同域、同快照的order_id关联订单，继承支付队列，而非按退款发生日期分窗。特别是09-11退款的E2-A-C1仍属于当前支付队列。

六笔success退款均为对应支付后2天，落在闭合观察期`[paid_at,paid_at+7天]`且不晚于as_of；N按有效支付订单计，U按具有合格退款的订单去重。基期退款订单为{E2-B-B1,E2-B-B2}，当前为{E2-A-C1,E2-C-C1,E2-C-C2,E2-C-C3}；基期A两单没有退款。

所有订单最晚09-19成熟；as_of和退款水位09-23覆盖，支付水位09-15覆盖双窗末端09-08与09-15。无未成熟或水位不足导致的比较阻断，静态outcome为ready。

## 汇总、身份与缺席规则

基期A为N=2/U=0/率=0，B为N=2/U=2/率=1；总计N=2+2=4、U=0+2=2、率=2/4=1/2。当前A为N=1/U=1/率=1，C为N=3/U=3/率=1；总计N=1+3=4、U=1+3=4、率=4/4=1。每单唯一归组且无遗漏，两个窗口均满足ΣN组=N总计、ΣU组=U总计。

基期类别集合{A,B}、当前{A,C}，因此shared={category_a}、exit={category_b}、entry={category_c}；两版身份集合相同但数值不同。这里的entry/exit表示所选支付队列中的出现/缺席，不表示目录永久上线或下线。基期C、当前B均无聚合行，不构造零分母退款率；基期A的真实零率与类别缺席不同。总体率1/2→1，绝对变化1/2（增加50个百分点），相对变化1（增加100%），不得简单相加或平均组率。

## 本轮实际检查与覆盖限制

通过标准库读取文件并断言上表四项文件哈希、规范化input哈希、冻结Markdown中的指纹及supersedes指向，实际输出：

```text
冻结核验通过：v2、v1、v2独立预期及v1台账共4项SHA-256一致。
规范化input哈希与既有记录一致，v2 supersedes准确指向v1冻结哈希。
```

本地实际运行既有静态检查：

```bash
.venv/bin/python -B -m pytest tests/test_boundary_fixtures.py -k entry_exit -o addopts='' -q -p no:cacheprovider
```

```text
....                                                                     [100%]
4 passed, 12 deselected in 0.07s
```

四项分别为v1/v2各一项通用完整性检查与各一项类别新增/退出静态检查。`--collect-only`已确认选择范围；12项未选择是本次定向核对，不代表完整回归。静态检查验证来源关联、窗口/类别归属、成熟水位和预期算术，不调用参考函数生成答案。本轮未重新调用`calculate_category_reference()`、未新增测试、未跑全量pytest；2026-10-26的参考对照与运行记录保持为历史证据，不冒称本次重跑。

v1/v2 Fixture、两版独立JSON台账及其既有说明保存前后核对SHA-256均未变化；未改写冻结哈希或预期。尚待v2专门pytest计算回归及用户独立人工验收，不修改路线图、不提交或推送远程仓库。
