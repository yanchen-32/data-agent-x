# M02：合法跨域同局部ID配对输入设计草案

日期：2026-11-16（Asia/Shanghai）。状态：**输入及独立逐单预期设计稿，未创建JSON Fixture、未冻结、未调用参考函数或运行pytest。** 已先核验[M01最小参考层关闭记录](../regression_checks/G0_M01_region_Must_closure.md)及其执行清单绑定文件仍一致，满足本轮进入M02准备的前提。M02尚未通过，G0保持未验收。

## 1. 唯一目标与依据

依据[DD02 §1/2/4](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)、[指标目录的数据关联规则](../../docs/engineering/02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)和[G0矩阵M02](../regression_checks/G0_fixture_coverage.md)，验证两个**分别合法**的固定域/快照Scope使用相同局部ID、相同展示名时，订单、退款、产品关联和聚合结果不能串数。

主维度选category：两个域复用product_1/product_2及category_1/category_2，但产品到类别映射相反。这样仅按product_id缓存目录或复用上一Scope结果会得到错误成员/数值。地区与渠道各只设一个相同ID及名称，用于满足合法输入，不重复M01的多维分组能力。

现有foreign目录/订单混入测试要求ValueError；本例的两个输入都不含外域行，均应ready。不能将两域事实拼成单个input再期待参考入口接受，也不把两个合法结果直接相加当作一次跨域查询。

## 2. 两个分别合法的Scope与输入契约

| 名称 | domain_id | snapshot_id | 地区过滤 | 主维度 |
| --- | --- | --- | --- | --- |
| M02-A | domain_m02_a | snapshot_m02_pair_v1 | [region_shared] | category |
| M02-B | domain_m02_b | snapshot_m02_pair_v1 | [region_shared] | category |

故意复用同一局部snapshot_id字符串，仅domain_id不同，避免两个字段同时变化掩盖遗漏域键的错误。两个完整Scope仍不同；每份合成输入及其哈希将分别绑定，不表示两域共享一份实际快照。有效Schema对domain_id/snapshot_id均为非空字符串，本地参考契约按完整域/快照关联；此处不创建生产快照注册或批准记录。

两个合成主体分别假定有权访问其域内的固定数据和region_shared。授权前提记录在案例元数据，不新增可伪造的input权限开关，不提供跨域访问权。所有事实及全部目录行必须与各自context的domain_id/snapshot_id完全一致。

每份input沿用现有context/orders/refunds/dimensions结构；以下共同字段逐字相同：

```json
{
  "metric_id": "refund_rate_order_horizon",
  "horizon_seconds": 604800,
  "business_timezone": "UTC",
  "windows": {
    "baseline": {"start": "2026-09-01T00:00:00Z", "end": "2026-09-08T00:00:00Z"},
    "current": {"start": "2026-09-08T00:00:00Z", "end": "2026-09-15T00:00:00Z"}
  },
  "as_of": "2026-09-23T00:00:00Z",
  "watermark": {
    "payments_through": "2026-09-15T00:00:00Z",
    "refunds_through": "2026-09-23T00:00:00Z"
  },
  "filters": {"region_ids": ["region_shared"]}
}
```

装配时在每份context中增加上表domain_id、snapshot_id，不向正式QuerySpec添加字段。主维度及合成授权说明属于Fixture元数据；input不读取expected。每条订单、退款、目录均显式填写两个Scope字段和下列source_row_id，不能从ID前缀推定Scope。

## 3. 目录及有区分力的产品关联

每域各有products两行、categories两行、regions一行、channels一行。完整业务键均为(domain_id,snapshot_id,对应局部ID)，各自唯一。

| Scope | product_id | category_id | 产品来源 |
| --- | --- | --- | --- |
| A | product_1 | category_1 | m02-a-product-1 |
| A | product_2 | category_2 | m02-a-product-2 |
| B | product_1 | category_2 | m02-b-product-1 |
| B | product_2 | category_1 | m02-b-product-2 |

两域categories目录均登记category_1/label=图书、category_2/label=电子；来源分别为m02-a-category-1/2、m02-b-category-1/2。两域regions均登记region_shared/label=西北，来源m02-a-region-shared、m02-b-region-shared；channels均登记channel_shared/label=网页，来源m02-a-channel-shared、m02-b-channel-shared。

“同名”发生在两个域之间，域内类别名称不同，不重复A3-07同域同名不同ID的目标。相同category_id及label的结果行也必须连同调用Scope辨认，不能仅按(dimension_id,group_id)跨域合并；现有参考返回行不带域字段，测试端保留input context与结果的配对关系。

## 4. 原始支付逐单台账

所有支付均is_payment_valid=true，region_id=region_shared、channel_id=channel_shared；paid_at和成熟日均为2026年UTC零点。表中日期装配为YYYY-MM-DDT00:00:00Z，其他字段不得省略。

| Scope | order_id | product_id | 支付日 | 支付+7天 | 支付窗/类别 | 支付来源 |
| --- | --- | --- | --- | --- | --- | --- |
| A | order_b_1 | product_1 | 09-02 | 09-09 | 基期/category_1 | m02-a-order-b-1 |
| A | order_b_2 | product_2 | 09-03 | 09-10 | 基期/category_2 | m02-a-order-b-2 |
| A | order_c_1 | product_1 | 09-09 | 09-16 | 当前/category_1 | m02-a-order-c-1 |
| A | order_c_2 | product_2 | 09-10 | 09-17 | 当前/category_2 | m02-a-order-c-2 |
| B | order_b_1 | product_1 | 09-02 | 09-09 | 基期/category_2 | m02-b-order-b-1 |
| B | order_b_2 | product_2 | 09-03 | 09-10 | 基期/category_1 | m02-b-order-b-2 |
| B | order_c_1 | product_1 | 09-09 | 09-16 | 当前/category_2 | m02-b-order-c-1 |
| B | order_c_2 | product_2 | 09-10 | 09-17 | 当前/category_1 | m02-b-order-c-2 |
| B | order_c_3 | product_2 | 09-11 | 09-18 | 当前/category_1 | m02-b-order-c-3 |

A四笔、B五笔；跨域复用四个order_id合法，各域内部唯一。A最大成熟时刻09-17，B为09-18，均不晚于as_of及退款水位09-23；支付水位09-15等于双窗最大end，两窗均非空。全部产品、地区、渠道和类别关联完整，不注入关键DQ故障。

## 5. 原始退款逐事件台账

所有退款status=success，refund_at均为2026年UTC零点；事件携带各自域/快照并按完整订单键关联。

| Scope | refund_id | order_id | 退款日 | 独立资格/归属 | 退款来源 |
| --- | --- | --- | --- | --- | --- |
| A | refund_shared_1 | order_b_1 | 09-03 | 支付09-02至09-09内，基期/category_1 | m02-a-refund-1 |
| B | refund_shared_1 | order_b_2 | 09-04 | 支付09-03至09-10内，基期/category_1 | m02-b-refund-1 |
| B | refund_shared_2 | order_c_1 | 09-10 | 支付09-09至09-16内，当前/category_2 | m02-b-refund-2 |
| B | refund_shared_3 | order_c_3 | 09-12 | 支付09-11至09-18内，当前/category_1 | m02-b-refund-3 |

四笔事件均≤as_of，且在对应支付的闭合7天观察期。A当前无退款是合法零退款；B当前两事件对应不同订单，U=2。refund_shared_1跨域复用但关联不同order_id，不能让A的关联覆盖B，也不能按局部refund_id跨域去重。域内事件键唯一，没有孤立、支付前或重复事件负例。

## 6. 先行手工集合、数值与来源预期

以下先按第4/5节逐单填写，不调用任何参考函数。P为支付订单集合，R为退款订单集合；表中局部ID始终附属本行Scope，来源由上表一一对应。

| Scope/窗口/类别 | P | R | N/U/精确率 |
| --- | --- | --- | --- |
| A/基期/category_1 | {order_b_1} | {order_b_1} | 1/1，1 |
| A/基期/category_2 | {order_b_2} | {} | 1/0，0 |
| A/当前/category_1 | {order_c_1} | {} | 1/0，0 |
| A/当前/category_2 | {order_c_2} | {} | 1/0，0 |
| B/基期/category_1 | {order_b_2} | {order_b_2} | 1/1，1 |
| B/基期/category_2 | {order_b_1} | {} | 1/0，0 |
| B/当前/category_1 | {order_c_2,order_c_3} | {order_c_3} | 2/1，1/2 |
| B/当前/category_2 | {order_c_1} | {order_c_1} | 1/1，1 |

| Scope | 基期总计N/U/率 | 当前总计N/U/率 | 绝对变化ratio | 相对变化 |
| --- | --- | --- | --- | --- |
| A | 2/1，1/2 | 2/0，0 | −1/2 | −1 |
| B | 2/1，1/2 | 3/2，2/3 | 1/6 | 1/3 |

两者均应ready、reasons=[]、三个quality标志true，各自四条类别行加两条总计行，共六行；使用精确Fraction，不用浮点容差。每域每窗分别ΣN组=N总计、ΣU组=U总计，两个类别P/R互斥穷尽，不平均组率，不跨域或跨维相加。

每域候选与总退款集合为组集合并集。A基期候选{order_b_1,order_b_2}、退款{order_b_1}；当前候选{order_c_1,order_c_2}、退款{}。B基期候选同局部ID集合、退款{order_b_2}；当前候选{order_c_1,order_c_2,order_c_3}、退款{order_c_1,order_c_3}。两域基期总率故意相同，但成员及产品关联不同；只比总计不能检出全部错误。

来源比较必须按本Scope完整键回查，逐组与本表P/R对应的支付/退款source_row_id配对。A当前所有退款来源集合为空；B当前category_1退款来源为{m02-b-refund-3}、category_2为{m02-b-refund-2}。B当前category_1支付来源为{m02-b-order-c-2,m02-b-order-c-3}、category_2为{m02-b-order-c-1}；其余单元素来源按逐单表直接定位。相同局部ID不代表来源相同，不能把m02-a-*来源写入B结果证据。

## 7. 后续文件布局与最小可执行验证方案

建议后续先创建两个独立草稿输入reference/fixture_drafts/m02_cross_domain_scope_a.json与m02_cross_domain_scope_b.json，各自按本稿逐表装配input；先行独立预期另存reference/manual_checks/G0_M02_cross_domain_expected.json。三份文件在本轮均未创建，不计新增主Fixture或冻结Oracle；正式命名、完整文件与规范化input哈希待实际落盘后记录，不预先虚构哈希。

预期文件应绑定两个输入、规则/DD02版本、逐单来源和本设计稿版本，静态转录本节P/R、六行及变化；不调用calculate_reference/category_reference填预期。合成机制登记为人工设计，不杜撰随机种子或生产approved manifest。

最小回归步骤：

1. 每份input预检域/快照一致，完整订单/事件/目录键在域内唯一，产品关联完整，来源及时间与本稿一致；不将两个JSON拼为一个计算输入。
2. 各自只传input给既有calculate_category_reference；分别与先行冻结的A/B六行、N/U/Fraction、候选P、退款R和逐组来源比较，检查组内及总体守恒。无需新增计算器或改生产Runtime。
3. 同一进程按A→B→A、B→A→B交错调用，每次都对照各自先行Oracle，不能把第一次运行输出作为第二次expected；调用前后input及冻结文件不变。类别映射反转、B多一笔支付和两笔当前退款应检出目录/退款缓存按裸ID复用。
4. 结果及来源按(context.domain_id,context.snapshot_id,局部业务键)绑定。不要断言A/B的裸order_id集合不相交——它们应有交集；应断言完整事实键不相交，且每次结果的来源只来自所属Scope。聚合行没有域字段，须在测试端与输入Scope一起标识。
5. 真实执行后分别记录合法完成、错误关联/串数或意外拒绝，不以foreign_scope拒绝测试替代本配对正例。不扩展三维或多地区组合来凑数量，既有相关测试只作回归保护。

现有参考入口已在接收单Scope时校验域/快照，因此在该前提内用局部ID字典不必然错误；本配对主要验证两次合法调用及目录关联不串数，不能单凭通过就声称数据库JOIN含完整谓词、角色/视图隔离或授权探针通过。后者仍属于M06。

## 8. 当前完成状态

本轮完成两个Scope、完整装配规则、9笔支付/4笔退款及目录来源、逐单分类、独立P/R与双窗数值设计。没有调用参考/生产代码、创建正式Fixture/expected、执行pytest、修改旧冻结契约或实现，也没有提交/推送。M01本地关闭状态保持；M02仍为准备阶段，CI、本人独立验收、G0及生产授权状态均不推进。

## 9. 本轮实际静态自检

先保存上述手工设计，再以python3标准库静态解析本稿表格核对；环境为CPython 3.10.12。检查只比较已写支付/退款/产品映射、P/R及Fraction算术、时间和来源唯一性，不调用reference/dataagentx，不创建或回填任何JSON预期。实际执行退出码0：

```text
静态台账核对：9笔支付、4笔成功退款、4条产品关联及8条类别预期一致；25条来源唯一。
A：1/2→0，绝对变化-1/2，相对变化-1；B：1/2→2/3，绝对变化1/6，相对变化1/3。
两Scope分别满足半开支付窗、7天成熟、水位、成员互斥穷尽及N/U守恒。
退出码0；只校验已写Markdown台账，未调用参考/生产代码、未运行pytest、未写回答案。
```

此处是设计稿静态自检，不能登记M02计算回归通过或正式冻结；尚无两个JSON实际输入的哈希和运行证据。
