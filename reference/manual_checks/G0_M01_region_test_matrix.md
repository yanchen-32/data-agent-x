# G0 M01：region独立预期与最小测试矩阵

日期：2026-11-07（Asia/Shanghai）。状态：**测试设计与人工预期草稿，未编写/执行region测试或实现。** 本文细化[实施方案](G0_M01_region_plan.md)的RG01～RG06，不重编渠道C01～C08，不新增主Fixture编号。

## 1. 冻结依据与尚未冻结的内容

已冻结依据为[DD02 §1/2/4](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)、[SRS §4.1.1/4.2/4.4](../../docs/engineering/01_需求基线/DataAgentX_SRS_v1.2.md)、原11号input及已有退款/不足规则；原文件和expected不变。region局部契约当前仍标“方案初稿”，尤其未登记源地区ID的unknown分类尚未批准冻结，不能因本次请求出现“冻结契约”字样就改称已冻结。本矩阵引用的方案SHA-256为20200d0af6c99bf4118d7ea0d81ebd22ab1f3a03084148b79606da56d1949b2c，原字节保持。

本轮先从[11号input](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)的逐单支付/退款保存[独立预期台账草稿](G0_M01_region_expected_draft.md)，再列测试矩阵。数值、来源集合、边界及错误状态由原始行和规则决定，不调用calculate_region_reference或任何已有计算器生成答案。台账未冻结，也不称首次盲审或用户本人验收。

输入命名：W为原西北Scope；A为原input深拷贝后仅设filters.region_ids=[]，并单列“合成主体假定获两地授权”。每个变体都从所指定W/A重新深拷贝，互不叠加；不改原任务Scope，不用测试中的[]作为生产扩权依据。目录与业务键均使用domain_a及fixture_single_region_channel_v1_draft。

## 2. 正常分组、过滤与退款：最小主路径

每行均给出业务规则、唯一变更及独立来源；预期数字是台账手填设计值，需先冻结再执行。组、总计的比率均解码为精确Fraction，不转float或采用误差容忍。

| 编号 | 业务规则 | 输入及变更 | 独立预期与来源 |
| --- | --- | --- | --- |
| RG01.W | 先过滤再分组，单地区组与总计同Scope | 原W不改 | 台账§2～4：每窗仅region_northwest，基期3/1/率1/3、当前4/3/率3/4，四条实际聚合行，绝对变化5/12。四笔东南支付及两笔东南退款来源排除；无东南/unknown行 |
| RG02.A | 合法多地区控制按稳定地区ID分组 | 只将W的过滤列表改为[]，作为独立A | 台账§2～4：基期NW=3/1、SE=2/1，总计5/2/率2/5；当前NW=4/3、SE=2/1，总计6/4/率2/3；六条行及精确率，绝对变化4/15，来源逐单可追溯。不是由channel行合并/换字段名生成 |
| RG02.Q | 缺席地区不生成虚假零分母率 | A中仅将两笔SE基期支付K11-S-B-W1、K11-S-B-A1设无效 | 台账§6 Q：基期只存在NW，3/1/率1/3；当前仍6/4/率2/3，ready，绝对变化1/3。不输出SE基期行，原SE基期退款仍在输入但不计U |
| RG03.D | 退款事件按订单去重 | A只追加台账§5 D列明的SE当前第二笔success事件KR11-RG03-S-C-SECOND | 该事件09-16在支付09-14至H末端09-21内；当前SE合格事件数2、退款订单集合仍{K11-S-C-A1}、U仍1，六行及总体变化不变；退款事件来源新增一项，订单台账不增 |
| RG03.T | 退款地区/窗口从支付订单取得 | A只将KR11-S-B-W1的refund_at改为09-09，ID/来源不改 | 台账§5 T：仍在09-05支付单的闭合观察期内，仍计基期SE，不能因事件落在当前日历窗而移入当前；原六行及所有订单集合不变 |
| RG03.Z | 正分母零退款仍有合法地区行 | A仅移除KR11-S-B-W1 | 台账§5 Z：基期SE=2/0/率0，保留该组；基期总计5/1/率1/5，当前6/4/率2/3，ready、绝对变化7/15。不同于整体空基期阻断 |

RG01.W同时检出漏过滤以及只过滤分母/分子：结果必须与其独立支付/退款订单集合逐项一致，不能仅以U≤N或总计一致判过。无需编写“错误计算器”；RG02.A证明东南数据在另一个合法合成Scope中确实有贡献。

## 3. RG04：目录、关键关联与比较门槛

### 目录和关键关联拒绝

故障ID/source_row_id使用本矩阵专属后缀，实施前将变更写入控制台账并检查唯一性。duplicate的新增来源固定为r11-rg04-region-dup或r11-rg04-product-dup；foreign的新增来源固定为`r11-rg04-{catalog}-{field}`，catalog为products/regions，field为domain_id/snapshot_id。原合法目录行保留，只追加一个故障行；不通过删除共享product_book同时破坏全部订单关联。

| 编号 | 业务规则 | 输入及变更 | 独立预期与来源 |
| --- | --- | --- | --- |
| RG04.duplicate | 原始目录重复不能被字典覆盖，过滤外目录也检查 | W；分别复制SE地区目录行或product_book行，仅source_row_id改为新值，完整业务键不变 | DD02 §1、草案§3：ValueError，定位目录和重复完整键。不能因SE不在W候选队列而放过地区目录重复；无正常结果，也不降级unknown |
| RG04.foreign | 目录关联使用域/快照复合键 | W；分别向products/regions追加一个保留相同局部ID的副本，只将domain_id改为domain_foreign_rg04，或只将snapshot_id改为snapshot_foreign_rg04；每次只选一种故障 | DD02 §1、指标目录：每个目录/Scope故障均ValueError，指出不一致的目录键/Scope；原合法行仍在，不能按裸ID忽略外域行或借其label关联 |
| RG04.product | 关键产品缺失优先于比较不足，覆盖过滤外订单 | W只改K11-S-C-A1的product_id为product_rg04_missing；分别在原ready及as_of=09-18T23:59:59.999999Z的合法immature前提下验证 | 草案§3及原A3-10规则：均ValueError，包含K11-S-C-A1、r11-order-s-c-app-1及(domain_a,fixture_single_region_channel_v1_draft,product_rg04_missing)。不是insufficient_evidence或合法unknown；SE过滤外身份不豁免关键检查 |

duplicate/foreign按必要的两个目录及两个Scope字段参数化，不复制渠道C04的channels目录检查、两地区目标×全笛卡尔组合或既有合法未知类别测试。产品和地区是本入口实际依赖的目录，拒绝分支有其自身契约依据。

### 成熟、水位及空基期

全地区A的最晚成熟为09-21，W为09-19；双窗最大end均为09-15。完整推导见台账§2/6。原渠道C05的09-19常量只适用于W，不能直接用作A的等号边界。

| 编号 | 业务规则 | 输入及唯一变更 | 独立预期与来源 |
| --- | --- | --- | --- |
| RG04.M− | 每笔纳入支付均满H | A，as_of=09-20T23:59:59.999999Z | 台账M−：仅all_orders_mature=false，唯一原因观察期未成熟，其余水位true；全比较不发布，不能静默删掉未成熟SE订单后ready |
| RG04.P− | 支付水位覆盖窗口end，不能用最后支付替代 | A，payments_through=09-14T23:59:59.999999Z | 台账P−：仅payments_watermark_covered=false，唯一原因支付水位不足；全比较不发布 |
| RG04.R− | 退款水位覆盖该Scope最大paid_at+H | A，refunds_through=09-20T23:59:59.999999Z | 台账R−：仅refunds_watermark_covered=false，唯一原因退款水位不足；全比较不发布，不能因现有事件都早于水位就判完整 |
| RG04.equal | 成熟/退款水位等号允许 | A分别将as_of或refunds_through设为09-21零点；每次只改一个字段 | 台账M=/R=：ready、三个quality标志true，仍为RG02.A六行。支付水位09-15等号已经由未改A覆盖，不另建同输入“正例” |
| RG04.scope | 成熟/退款水位在过滤后的队列判定 | 同一as_of=09-19零点，分别使用W和A，其他字段保持原值 | W最后成熟恰等于as_of，应ready并匹配RG01.W；A包含09-20/21才成熟的SE订单，应因未成熟不发布。不是全量原始订单都必须在单地区Scope中成熟 |
| RG04.E | 一窗无有效样本阻断整个比较 | A将台账E列明的五笔基期支付全部设无效 | 台账E：基期候选[]、当前保留六单；quality三个标志true，唯一原因为支付窗口无有效样本；两窗均不发布。只禁用W的三笔基期订单不构成A的空基期 |

“全比较不发布”统一断言为：outcome=insufficient_evidence；metrics两窗N/U/rate及absolute_change_ratio/relative_change全None；aggregate_rows=[]、group_order_ids={}、group_refunded_order_ids={}。按台账核对候选集合，但不要求参考函数返回不存在的诊断N/U字段。以上与ValueError拒绝、合法RG03.Z零退款、RG02.Q缺席组分开。

## 4. RG05：局部规则冻结后的身份/未知控制

本节不是新增已冻结业务事实。若采纳当前region草案的未知归类，须先将第4节局部规则及台账§7冻结；若规则审阅调整，先修订设计和台账，再实现，不能依据程序输出回填答案。这里不重复类别的同名/unknown测试，也不把它们记作region已覆盖。

| 编号 | 业务规则 | 输入及变更 | 独立预期与来源 |
| --- | --- | --- | --- |
| RG05.label | 展示名不决定地区身份 | A两个已登记地区label改为“同名地区”；另一个独立变体仅将SE的label设None或移除label字段 | 台账L：已登记ID、N/U/Fraction和来源保持六行；同名仍两个组，缺label仍为region_southeast，label=None，不归unknown |
| RG05.unknown | 非关键未知数据保留、未知来源可追溯 | A仅改K11-S-C-A1.region_id为__unknown__，或无目录条目的region_unregistered_rg05；两种变体分开 | 台账U：当前SE=1/0/率0，unknown=1/1/率1，NW=4/3；总体仍6/4，基期不变，unknown基期不输出，总共七条实际行。需记录原region_id/归类原因及原支付/退款来源 |
| RG05.filtered | 未知保留不等于越过单地区过滤 | 对同一个U变体保持W过滤 | 台账W-U：该SE原订单/退款依然排除，W所有结果及来源保持；不强行输出unknown行，不扩Scope |
| RG05.invalid | 未知过滤参数/坏格式与未知数据分开 | W过滤列表分别改为["region_unregistered_filter_rg05"]、["__unknown__"]；另一个独立变体仅将K11-S-C-A1.region_id设None | 台账F及草案§4：ValueError，不是合法空窗/unknown组；不能自动改成[]、伪造403或调用生产权限判断。其他坏格式同属结构拒绝，后续按实际校验分支选代表参数，不穷举全部字段 |

## 5. RG06及所有正例共享的来源与隔离断言

以下是RG01/02/03/05等正例的共享验收层，不为每个断言再造一个Fixture或重复一套测试：

1. **先检查原列表，再建立结果索引。** 行身份键(window_index,dimension_id,group_id)唯一，所有地区行dimension_id="region"、稳定ID/label正确，总计身份为空；按实际存在组检查行数。各N/U为int、率为Fraction，逐项对照台账字面值，不只比较行数或宽松浮点。
2. **支付集合及来源。** 每个group_order_ids由实际返回ID连同固定域/快照查回原始orders；与台账手工P_g逐项比较，回查source_row_id、原region_id、产品键及支付窗。不能在测试里重新写一遍同样的分组算法来生成expected。unknown使用手工记录的原ID→组映射，不借待测归一化器判预期。
3. **退款集合及事件来源。** 实际group_refunded_order_ids逐组与台账R_g比较，且为本组支付集合子集；在原refunds中查回先行列明的事件、来源、success和观察期属性。D中同单两笔事件对应一个退款订单，不能套用渠道固定输入“一单仅一个事件”的来源辅助断言。
4. **来源守恒。** 各组支付集合两两不交、并集等于该Scope独立P；退款订单集合两两不交、并集等于独立R。ΣN/ΣU分别等于实际总计及台账总计，来源集合逐项匹配；W额外检查东南支付/退款来源全部排除。A中它们正确进入SE，而非只核对总体数值。
5. **输入与expected隔离。** 函数只接收input，复用既有_InputOnly保护方式禁止getitem/get/contains探测expected；调用前后deepcopy相等、主Fixture和旧expected字节/固定哈希不变。后续新预期也须先绑定冻结哈希，禁止读取当前文件重算“新基线”自证正确。只把手工率字符串转为Fraction，不用输出更新静态文件。

额外RG06控制：从W/A各自独立深拷贝，重复调用及订单/退款/地区目录重排，比较六/四条实际行和分组台账，候选只比较集合；交错W/A调用后原结果不变。复用现有C07已经验证的隔离检查思路，不拷贝渠道测试全文或改其函数名。

三维共同Scope检查只在同一合法W或A输入上调用现有category/channel入口和新增region入口，核对总体metrics与候选集合一致、各维分别ΣN/ΣU守恒；region的数值真值仍来自本台账，不把另一次函数输出当作Oracle，不把三个维度行/贡献相加。原类别/渠道固定测试保留，待未来实现变更时只作为原有回归套件执行。

## 6. 独立预期保存、复用与退出条件

旧05/06/09/10只复用明确业务规则和已有原始来源，不再创建同主题主例。原A3-11 C05只复用不足/空发布语义，C06只复用事件与订单去重原则；当前矩阵的主对照、两地成熟上界和SE退款目标均独立按11号input确定，不能把渠道行的dimension_id改成region或使用渠道分组求地区结果。

后续冻结记录至少包含：规则/方案版本、原Fixture及原input哈希、精确输入变更清单、实际变体input哈希、原始订单/目录/退款来源、P_g/R_g、N/U/率/总体变化及阻断原因。现有[人工台账草稿](G0_M01_region_expected_draft.md)先于region实现保存，未来机器可读预期只可从已审阅台账手工整理，不调用待测函数补数。异常预期是拒绝或不发布语义，不需要制造正常数值。

正确顺序为：确认并冻结局部规则和人工预期→实现小型region入口→从input实际计算并比较冻结值→相关参考及全量回归→归档真实命令、退出码、环境和版本。若差异先判Scope/集合/归类/实现，不自动改预期。无实际运行不得标通过；未来pytest参数化数量以实际收集为准，本矩阵不预报通过数。

本轮先保存手工数值，再用标准库Fraction核对所写常量的静态算术、核对原始订单/退款来源字面值；该审计不生成或写回答案，也不是pytest或业务函数运行。

本轮仅创建本矩阵和先行手工预期草稿，并给G0矩阵追加入口；未修改旧契约草案/Fixture/expected、源码、现有测试或旧执行证据，未调用参考函数、未执行pytest、未提交/推送。M01/G0仍开放；本地合成对照不等于生产授权、CI、正式评测或用户本人验收。
