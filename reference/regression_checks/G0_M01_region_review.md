# G0 M01：region分组剩余覆盖复核

日期：2026-11-07（Asia/Shanghai）。结论：**category已有固定参考验证，A3-11最小channel参考Must已关闭；region仍缺独立分组预期、参考实现及固定回归，因此M01整体保持开放。** 在本轮核对范围内未发现未公开region实现，不重建已完成的类别或渠道测试，不宣布G0通过。

## 依据与复核范围

- [G0覆盖矩阵](G0_fixture_coverage.md)§3、M01及2026-11-06追加状态；2026-10-30表中“channel缺失”保留历史含义，当前状态以A3-11后续证据为准。
- [A3-11 Must评审](A3-11_Must_review.md)、[公开交付验证](A3-11_C07_publication.md)及[公开版本摘要](A3-11_full_regression_public_manifest.json)。已知公开提交为[0278598](https://github.com/yanchen-32/data-agent-x/commit/0278598657a947c502d444c71a32de1c2064ebaf)；本轮只读取本地提交对象，不查询远程最新状态。
- [有效DD02](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)§1、2、4及[指标目录](../../docs/engineering/02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)。两者仍登记于当前BASELINE/SYNC_MANIFEST，不使用历史归档替代有效规则。
- 阅读总体、类别、渠道参考源码及相关测试；静态扫描开发树src/reference/tests中23份Python，以及Fixture/人工台账/草案目录23份JSON。包含未跟踪和这些目录内的忽略文件，排除__pycache__，不执行待测函数。
- 核对三个本地分支的已提交活动Python文件；公开工作树干净，另一个登记历史设计工作树只读扫描11份活动Python，未发现region候选，其既有未提交状态保持原状。没有递归审查内部归档或其他磁盘副本。

## DD02要求与三种维度的差别

DD02要求先固定授权域、快照和filters.region_ids（[]全部或单个已登记ID），再取半开支付窗及成熟队列，最后按**一次一个维度**聚合。分母N和退款订单分子U必须使用同一Scope，同单多笔合格退款只计一次；率保留Fraction。每个维度内分组互斥穷尽，ΣN组=N总计、ΣU组=U总计；不能把三个维度的分组行一起累加当成守恒。

| 维度 | 分组身份的来源 | 已有能力或缺口 |
| --- | --- | --- |
| category | 订单通过(domain_id,snapshot_id,product_id)关联产品，再取category_id | 已有calculate_category_reference；合法产品的非关键类别缺失保留__unknown__，已知ID无展示名仍保留ID；缺失关键产品关联拒绝 |
| channel | 直接取订单channel_id，渠道目录按完整复合键提供展示名 | 已有calculate_channel_reference；当前仅支持已登记渠道，未知渠道拒绝是参考范围限制，不能当成DD02业务关键DQ规则 |
| region | 应取过滤后订单region_id，地区目录通过(domain_id,snapshot_id,region_id)关联展示信息 | 当前只有地区筛选和部分目录检查，没有按region_id返回的聚合或分组台账；不能将channel实现改名当作已验收region能力 |

AggregateRow身份应为(dimension_id,group_id)，展示名不参与身份；region行应明确dimension_id="region"，group_id为稳定地区ID。全地区Scope下需要有至少两个实际支付地区的区分力；单地区过滤后只输出该地区一个实际组是合法结果，不强求两个组，不为缺席地区补零分母退款率。总计与分组必须共享Scope，退款地区由所属支付订单确定，不能按退款发生日期或展示名另划分母。

DD02的“名称解析时未知地区须澄清/拒绝”和“非关键未知数据维度不得静默丢组”属于不同环节。后续region输入中的缺值表达、已知ID缺展示名及目录关联异常如何分类，须明确规则与边界；不能直接照抄当前最小渠道的未知ID范围拒绝，也不能把关键产品缺失降级成__unknown__。

## 已覆盖、未覆盖与证据不足

| 状态 | 项目 | 可定位证据与判断 |
| --- | --- | --- |
| 已覆盖（参考层） | 总体支付队列、成熟/水位、成功退款订单去重及Fraction | [cohort.py](../cohort.py)提供共享队列和比较门槛；不是生产鉴权、SQL或DQ Adapter |
| 已覆盖（参考层） | 类别ID/产品关联、同名、生命周期、合法未知与关键产品缺失 | [类别计算器](../category_cohort.py)与[类别测试](../../tests/test_reference_category_cohort.py)，07/08v2/09/10已有固定Oracle及回归；无需重复创建 |
| 已覆盖（参考层） | 单地区过滤后按渠道分组及C01～C07控制 | [渠道计算器](../channel_cohort.py)与[渠道测试](../../tests/test_reference_channel_cohort.py)，A3-11四条渠道行和两条总计、来源及守恒均有冻结验收；最小Must已关闭 |
| 已覆盖（可复用前提） | 地区过滤同时作用于分母和分子 | A3-05固定总计、test_single_region_filters_denominator_and_refunds_before_grouping类别变体、A3-11西北固定及C03全地区控制；均未输出region分组 |
| 已覆盖（可复用前提） | 地区目录重复/域快照混入拒绝及重排 | A3-11 C04/C07包含regions目录，但实际计算维度仍为channel，不证明地区分组身份或展示信息正确 |
| 未覆盖 | region固定双窗聚合及来源Oracle | 扫描的23份JSON中未发现dimension_id="region"聚合行；05只有过滤总计，11只冻结channel及总计，漏过滤反例也未冻结逐地区行 |
| 未覆盖 | region参考计算入口和固定回归 | 只发现calculate_reference、calculate_category_reference、calculate_channel_reference三个计算入口；没有region分组模块/通用维度计算实现或对应固定测试 |
| 未覆盖 | region同Scope多组与单地区单组的守恒、退款归属和来源 | 现有category/channel输出不能证明按region归组正确；需有真正的region结果与先行独立预期比较 |
| 证据不足 | 三维在同一冻结输入/Scope下的总计及候选集合对齐 | 两个已有计算器各自复用总体队列，但固定案例不同，尚无包含region的三维同Scope执行结果；代码共享前提不等于这条验收已通过 |
| 证据不足 | region同名/改名、未知/缺展示名、生命周期等扩展行为 | DD02规定身份与未知保留原则，但目前没有region执行证据；类别测试不能直接转记为region覆盖，也不在本轮新增全部组合为M01门槛 |
| 证据不足（范围外） | 生产三维SQL、真实授权、QueryEvidence与正式序列化 | 当前标准库参考函数及本地pytest不能替代；按G0生产/正式评测缺口推进，不由M01局部补齐推定完成 |

## 本地是否已有未公开region实现

没有发现可接续的region实现或固定Oracle。静态名称/AST检索唯一类似命中是类别测试`test_single_region_filters_denominator_and_refunds_before_grouping`，经阅读确认它调用calculate_category_reference并断言category行及过滤总计，属于地区过滤控制。

开发源码中的三个计算器、两套分组测试均与本地已知公开提交0278598逐字节一致；开发树reference/或tests/显示未跟踪，不能据此认定已有未公开分组能力。公开提交树与三个本地分支已提交树未发现region入口/region聚合实现；上述两个其他工作树的活动源码检查也未发现未公开region代码。

这是对当前仓库活动源码、固定JSON、本地分支和登记工作树的判断，不证明未挂载磁盘、外部仓库或任意历史归档中绝不存在同名文件。没有新执行pytest或将静态检索当作运行验收。

## 下一步只补M01的region缺口

1. 优先评估复用A3-11原始输入：它已有西北/东南两个地区、产品/目录与支付退款来源，不必为数量新增重复Fixture。另行假定获授权的全地区对照使用深拷贝，不覆写冻结西北Scope。已有全地区channel反例不是region冻结预期，本轮不从它自动生成region真值。
2. 先逐订单保存region人工台账和预期：全地区两窗实际地区组及总计、精确Fraction、支付/退款订单和来源集合；另核对单地区过滤后仅该实际地区一组、干扰地区不进入分子或分母。若两地区各窗都存在可为六行，否则按实际存在组输出，不以固定行数代替正确性。
3. 之后再确定最小region参考接口，复用总体队列/成熟/水位且独立按region_id归组，只接收input，不读取expected或生产业务代码。以固定预期、同Scope守恒和来源、输入隔离等实际回归闭环；已有总体/类别/渠道回归作为后续变更的回归检查，不在本轮重写。
4. 在选定的同一冻结输入/Scope下复用现有类别、渠道入口，与新增region结果核对总体及候选集合一致、各维分别守恒。这是补三维共同Scope的证据，不重做原07～11已完成的类别/渠道案例，也不把跨维贡献相加。

上述是缺口的验证方式，不是本轮已实现内容。region闭环后才能重新评审M01三维局部范围，不能借此关闭合法跨域、贡献、其他DQ、签收、生产或正式评测Must。C08仍是A3-11的Should，不重新打开已关闭的渠道最小Must。

## 证据版本与本轮状态

| 本轮读取对象 | SHA-256 |
| --- | --- |
| 有效DD02 | 3c5452e0121db488da05686bdbda8d8ec38dc4107ed71837862943e518fc83b0 |
| 指标目录 | 51b2d179259c7e6d077491d319bf5da7b0f477c817d55db90dcb10861c0a2bce |
| 总体参考函数 | 13b5ced6824c1b8548eaa55b8014f4f87c35562fbe24eead2f0408afbefa96c6 |
| 类别参考函数 | 53507d6ba6671e7ca7ca6cd4f955fa345b53be73bf98edf5fd638d5206f2b216 |
| 渠道参考函数 | 207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c |
| 类别测试 | f5be1f6e7740ed43f26231eaa62d51f75b59d4e16baf2e26821b71becd0387a5 |
| 渠道测试 | d4fb4abaf6ade2d2fadbf20385943011e02db9b3e015a90b66da452712477817 |

已核对公开摘要所绑定的[原始输出](A3-11_C07_public_pytest.txt)：历史公开渠道42项、相关110项、全量170项均为2026-11-06的本地结果，**不是本轮运行、CI或用户本人独立验收**。本轮只新增本复核记录并向G0矩阵追加入口，不修改测试、参考/生产源码、冻结输入/预期、原执行输出或路线图，不提交或推送。
