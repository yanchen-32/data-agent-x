# A3-11：最小渠道Oracle与固定回归实施方案

日期：2026-11-02。状态：**实施方案已形成，尚未编写或运行渠道计算**。本轮只核对源码与既有冻结契约，不重新求值、生成答案或修改冻结预期。

## 1. 目标、交付与复用边界

目标：在A3-11固定合成Scope内复用总体支付队列及比较前提，从原始订单和退款独立计算channel分组，验证过滤、复合键、六条行及来源。规则依据为[DD02 §1–2/4](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)和[指标目录](../../docs/engineering/02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)。

拟新增文件（本轮尚不创建）：

- `reference/channel_cohort.py`：`calculate_channel_reference(data: Mapping[str, Any]) -> dict[str, Any]`。
- `tests/test_reference_channel_cohort.py`：固定A3-11与必要控制回归。
- `reference/regression_checks/A3-11_channel.md`：实现后实际命令、结果及限制。

仅依赖标准库与[总体参考函数](../cohort.py)。不导入生产业务代码，不访问数据库、文件或网络，不加依赖，不修改生产Runtime、总体参考函数或[类别计算器](../category_cohort.py)。不把类别ID替换成渠道ID套算，不提取跨维通用引擎，不实现region分组或贡献分解。

| 责任 | 复用总体calculate_reference() | 渠道层新增责任 |
| --- | --- | --- |
| 输入检查 | 固定订单/退款域快照、订单/事件重复、孤立及支付前退款、RFC3339、H、地区数量、窗口合法性 | 渠道所需目录复合键与作用域检查、全部输入订单关键产品关联、最小渠道输入范围核验 |
| 队列与前提 | 有效支付、半开窗口、地区过滤、成熟、支付/退款水位、空窗判定 | 直接使用candidate_order_ids，不重新从全部订单另选分母，不再次扩大地区 |
| 分子与分组 | 已返回总体N/U/率/变化，**没有返回合格退款订单集合** | 从原始refunds重建合格退款订单集合，与每窗队列相交后按订单channel_id分组 |
| 结果与状态 | 原样保留outcome/reasons/quality_checks/candidate_order_ids/metrics | 增加聚合行和组订单/退款订单台账；不足时不发布任何组或总计行 |

这里与总体计算共享前提和队列，不声称是两套完全独立的总体算法。渠道层独立于类别分组及未来生产实现；真正的数值基线是已先行人工冻结的预期，不是另一次calculate_reference()的输出。

## 2. 输入契约与关键关联

函数只接收[固定Fixture](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)中的`input`映射，不接收整个Fixture或文件路径，不读取expected、grouping_dimension、冻结元数据或人工审核文件。函数固定计算channel，不新增dimension参数或修改context/QuerySpec。

| 输入部分 | 最小支持契约 |
| --- | --- |
| context | 既有domain_id/snapshot_id、metric_id、H、UTC/显式offset时间、双窗、as_of、水位和filters.region_ids（空或单ID）；合法性沿用总体函数 |
| orders/refunds | 现有逐行字段及source_row_id；数据先完成结构核验。退款的地区与渠道从关联订单取得，不从退款日期分支付窗 |
| dimensions.products | 按(domain_id,snapshot_id,product_id)唯一索引，全部输入订单均须关联成功；不使用category_id决定渠道 |
| dimensions.channels | 按(domain_id,snapshot_id,channel_id)唯一索引；本最小版本的订单channel_id均为已登记非空ID，label可为非空字符串或null；label仅显示 |
| dimensions.regions | 核对提供目录的域/快照及region_id键唯一性；单地区过滤ID须在本地合成目录中注册。这不实现鉴权或名称解析 |
| dimensions.categories | A3-11合法背景资料，不参与渠道分组；测试可核对其来源，但不借此扩大渠道函数到类别业务 |

先用显式循环查重复，再建目录索引，不能用字典覆盖隐藏重复键。提供的产品、地区、渠道目录行必须属于context固定域/快照，混入foreign域/快照即拒绝，不能按裸ID误关联。订单/退款索引均使用完整三元键；总体层先核验固定域/快照及重复后，裸order_id与该Scope内三元键等价，但渠道层仍显式保留完整键。

关键产品缺失须覆盖**全部原始输入订单**，包括地区过滤外、窗口外或比较前提不足的订单，不能只校验候选队列。抛ValueError时定位order_id、source_row_id和缺失产品复合键，延续A3-10规则；目录重复/混域错误同样明确定位目录及键。ValueError是参考层拒绝，不返回伪造的生产blocked_by_quality对象。

本最小输入范围只承诺A3-11已登记完整关联的渠道正例及下述受控变体。channel_id为null/空值或没有渠道实体等未知渠道输入不在此轮验收；遇到时明确ValueError说明“超出最小渠道参考输入支持范围”，不静默丢单，不把它定性为新增关键DQ规则。DD02非关键未知维度保留要求仍在，后续须先冻结未知渠道规则与预期再扩展支持，不能由这个局部参考函数的范围拒绝声称其业务应阻断。已有渠道实体缺展示名仍保留channel_id，label=None。

## 3. 计算顺序

1. 调用一次`overall = calculate_reference(data)`；异常直接传播，不catch后改成ready。它已经检查所有原始支付/退款的Scope、键及时间，也已经形成过滤后的双窗候选队列。
2. 校验上述局部目录、关键产品关联及最小渠道输入范围。即使overall.outcome为insufficient_evidence，也先完成这些检查；关键关联故障不能被成熟/空窗不足掩盖。
3. 准备`{**overall, aggregate_rows: [], group_order_ids: {}, group_refunded_order_ids: {}}`。若overall非ready，立即返回，不发总计或渠道行；沿用原有空指标和候选诊断，不新增诊断计数或生产状态。
4. ready时按完整订单复合键建立索引。总体函数已完成RFC3339核验，渠道层用标准库datetime.fromisoformat及UTC归一化重读支付/退款/as_of，配合timedelta(H)；无需另写时间正则或导入生产解析器，也不更改总体私有解析接口。
5. 扫描原始退款：只将status=success、paid_at≤refund_at≤paid_at+H且refund_at≤as_of的订单复合键加入集合。集合按**订单**去重，不按退款事件数计U。原始事件即使来自东南也可先完成合法性核验，但只有与本窗候选队列相交后才能计入本窗分子。
6. 每窗从overall.candidate_order_ids映射到完整复合键集合P。按订单channel_id分出P_g，以R_g=P_g∩合格退款订单集合计U；N_g=len(P_g)、U_g=len(R_g)、rate_g=Fraction(U_g,N_g)。仅输出实际存在的组，不为缺席ID补零分母行。
7. 从P及P∩退款集合计出同Scope总计，并与overall.metrics中该窗N/U/率逐项核对；不一致则ValueError，不能通过复制总体U或按渠道占比摊分来掩盖错误。总计/组行均使用Fraction，不平均组率。
8. 每窗先总计、后按group_id排序输出渠道行；台账中的order_id列表排序。保留overall原字段内容与候选顺序，不原地排序或修改input。输出仅由本次局部对象组成，不累积跨调用状态。

以上为算法与约束说明，本轮不执行这些步骤求值。产品只负责关键关联，渠道直接取订单字段；不能通过产品复合键绕去category_id分组。

## 4. 输出契约与测试端字段

拟返回：

```text
{
  **overall,
  aggregate_rows: list[本地聚合行],
  group_order_ids: {baseline|current: {channel_id: list[order_id]}},
  group_refunded_order_ids: {baseline|current: {channel_id: list[order_id]}}
}
```

聚合行字段固定为window_index、dimension_id、group_id、group_label、paid_orders、refunded_orders、rate。总计身份三个字段为None，渠道行为dimension_id="channel"、group_id=订单channel_id、group_label=同Scope目录label。计数为int，rate为Fraction，None仅沿用不足/未定义变化语义；没有正式Decimal序列化或API对象。

A3-11期望六行，实际比较键为(window_index,dimension_id,group_id)。先对原列表检查长度及键唯一性，再建立索引逐行比较，避免字典覆盖重复行。本方案不重抄或新算六行值，直接绑定已冻结expected.aggregate_rows。若采用既定排序，也可再比较完整有序列表；候选/来源集合的语义不依赖冻结JSON中数组的排列。

以下冻结字段**只在测试端使用**，不要求函数返回：applied_filters、group_cohort_source_row_ids、group_refund_source_row_ids、合格/排除退款事件及来源、目录来源、group_rate_change_diagnostics、漏过滤/单侧过滤反例。quality_checks只保留总体函数已有的三个成熟/水位布尔值，不能与expected里包含全部目录/DQ计数的对象直接整块比较。总体函数不返回counted_refund_order_ids；按实际group_refunded_order_ids的并集与冻结该字段对照即可。

## 5. 冻结绑定、测试隔离及来源验证

采用新的函数作用域pytest fixture：每次从磁盘重新加载A3-11及[独立预期](A3-11_expected.json)，只传input，调用前deepcopy，调用后核对输入/expected/独立预期及磁盘字节不变。变体只改deepcopy，不改共享fixture或冻结文件。已有category_rows()和assert_partition()硬编码category，**不能直接复用**；新测试只借鉴检查模式，在本文件写简短channel专用辅助函数，不为复用测试工具而修改旧类别测试。

共享测试装载辅助函数硬编码并核验[冻结审核记录](A3-11_freeze_review.md)中的既有常量，不从当前文件动态计算“新基线”再自证一致：

| 对象 | 既有SHA-256 |
| --- | --- |
| 固定Fixture完整文件 | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| 独立预期记录完整文件 | c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e |
| 规范化input | 459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 |
| 规范化expected | 27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91 |

规范化沿用UTF-8编码的json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，无末尾换行；同时确认Fixture.expected与独立记录.expected相等。只在测试端将各rate和总体变化字符串解析为Fraction，不按实际输出重新填expected，不转float或宽松近似比较。

来源核对按以下顺序，既不新增返回字段，也不另写完整Oracle：

1. 将实际group_order_ids中的订单ID与固定Scope组成三元键，在原始orders中唯一查回source_row_id/region_id/channel_id/paid_at；逐组比较冻结订单集合与group_cohort_source_row_ids，确认西北、窗口、目录键及展示名来源正确。
2. 对实际group_refunded_order_ids逐组比较冻结退款订单集合；再以相同Scope订单键在原refunds中查回事件。本固定例每个退款订单只有一个事件，可以唯一定位退款ID与source_row_id，直接与先行冻结qualifying_refund_event_ids及group_refund_source_row_ids比较，并断言success/闭合观察期/as_of。不按退款发生日期另划基期/当前，也不按原始事件数充当U。
3. 各窗所有实际组的支付集合两两不交、并集等于实际候选队列，并与冻结cohort_source_row_ids一致；退款组集合两两不交、并集等于冻结counted_refund_order_ids，且为支付集合子集。逐行N/U对应各自集合大小，ΣN/ΣU与实际总计、冻结总计均一致。
4. 四个东南订单ID/来源不得出现于任一组或候选集合；两笔东南退款ID/来源不得成为已计U的证据。目录来源与冻结catalog_source_row_ids对应，并显式包含域和快照，不能仅用label对齐。

多退款控制变体不能沿用“每单唯一事件”的假设；只验证该控制下订单去重后组/总体结果与原冻结行相同，并分别核对所追加事件确属同一订单。当前函数没有事件证据返回字段，本例的原始事件追溯不等于已实现通用QueryEvidence。

## 6. 最小回归清单

这些是**计划测试**，尚未创建或执行；参数化数量以实现后pytest实际收集为准，不预报通过数。

| 编号/优先级 | 计划测试 | 核心断言及预期来源 |
| --- | --- | --- |
| C01 / 必须 | A3-11固定六行和总体字段 | only input调用；ready；原列表六行、键不重复、四channel行/两总计；各行N/U/身份/label及Fraction与既有冻结JSON和独立记录比较；总体metrics逐字段转Fraction后比较；原有overall字段与calculate_reference(input)一致仅作复用一致性检查，不替代静态真值 |
| C02 / 必须 | 按baseline/current参数化：来源、过滤与分组守恒 | 按上一节核对实际组订单/退款订单、支付/退款事件来源及东南排除；两组互斥穷尽、ΣN/ΣU守恒；与两类单侧过滤冻结诊断不相等，防止只过滤分子或分母仍因U≤N而漏检 |
| C03 / 必须 | 漏过滤反例受控对照 | 深拷贝后显式另设filters.region_ids=[]的合成全地区控制Scope，假定此控制另有授权，不是修改原任务冻结Scope或覆写生产权限。实际按窗口/渠道与既有unfiltered_counterexample比较精确数值和追加来源；证明漏过滤会改变结果，不编写一套错误计算器制造“实际” |
| C04 / 必须 | 目录复合键与关键产品关联拒绝 | products/regions/channels目录重复键、domain_id或snapshot_id改为foreign_scope均拒绝；只改局部ID相同而Scope不同，不能裸ID关联。产品缺失在ready及immature两种比较前提下均拒绝并定位订单/来源/键；包括过滤外东南订单的关键关联，不将错误降级成未知渠道 |
| C05 / 必须 | 沿用总体不足门槛，不发布聚合 | 仅未成熟、仅支付水位不足、仅退款水位不足、仅基期空窗四种deepcopy控制；成熟/水位尽量单故障，其余条件保持合法。比较overall的outcome/reasons/三个quality标志、候选与空metrics均未变，aggregate_rows=[]、两组台账={}；不是ValueError生产DQ映射 |
| C06 / 必须 | 独立退款扫描仍按订单去重及观察期 | 向已合格退款订单追加不同refund_id的success事件（观察期内），六行与总体值不变；另追加failed、支付后H之后或as_of之后的合法时间事件，不增加U。追加前先静态确定事件属性，不引入重复事件ID、孤立或支付前退款等其他故障；实际门槛仍交给总体函数检查 |
| C07 / 必须 | 不读expected、输入不变、可重复执行 | 包装input映射对expected的getitem/get/contains等访问直接报错；fixture.deep_copy及文件哈希前后不变，冷/重复调用无跨调用污染。逆序订单/退款/目录后，聚合行和两个组台账相同；不强求总体candidate_order_ids原始顺序相同，比较其集合或与该变体overall一致 |
| C08 / Should | 渠道展示名变更 | 只改两个渠道label（含同名或null）时，ID/N/U/Fraction/来源不变，仅对应group_label改变；不能把category同名测试当成渠道实现已覆盖 |

控制注意事项：C05空基期应标记**所有西北基期订单**支付无效，而不是只改最前两行；东南原始订单仍合法但不进入Scope。C06的as_of后退款控制可落在H后，不声称它孤立验证as_of：成熟已满足时H内不可能再出现as_of后事件，独立改变as_of会触发不足门槛。不要为凑四个“独立边界”制造不可能的成熟场景。C04验证合法单Scope的错误混入，不等于G0所缺合法双Scope同名正例。

未知渠道、region维度、跨域合法正例、贡献和正式精度另按G0缺口推进，不要求本最小参考函数提前承担所有维度/生产能力。

## 7. 实施顺序、运行证据与退出条件

实施时先添加只读取固定输入/预期的装载与C01回归，观察新接口未实现的收集/导入失败，只记为实施前失败，不能记为业务红灯；随后新增最小channel_cohort.py并完成C01/C02，再补其余必须控制。固定预期和既有cohort/category业务语义均保持原样。若结果不符，先定位Scope、订单集合、去重或关联；只有确认独立Oracle本身错误才另记版本和修订依据，不回填待测输出覆盖v1。

以下为**实现后的计划命令，本轮未执行**，文件尚不存在：

```bash
.venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider
.venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
.venv/bin/python -B -m pytest -o addopts='' -q -p no:cacheprovider
```

专项通过后运行相关测试，相关通过后再全量；若后续失败或环境阻塞，保留真实命令/输出/原因，不声称通过。记录开发工作树及解释器/pytest环境；公开工作树结果另记，不把本地记为CI。现有冻结审核记录的21项是先前静态证据，不是本方案已执行或渠道计算已通过。

完成条件：必须清单实际通过，固定六行/精确率/总体变化/来源与先行预期一致，门槛和关键错误不被绕过，冻结指纹不变，原总体/类别测试无回归，真实执行证据归档。达到后也只表示最小渠道参考能力，G0其余Must、生产能力及用户本人验收分别判断。

## 8. 本轮交付范围

本轮只新增本方案。未创建channel_cohort.py或渠道测试，未调用calculate_reference()或其他业务函数求值，未生成actual结果，未重跑pytest，未修改冻结Fixture/expected、源码、旧记录、项目架构或路线图。仅检查文档引用、既有冻结哈希和文件完整性；不提交或推送。
