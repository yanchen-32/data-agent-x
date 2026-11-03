# A3-11：实施起点与冻结契约检查

核对日期：2026-11-03（Asia/Shanghai）。结论：**未发现本地未公开的渠道Oracle实现；当前起点仍是已发布方案与已冻结开发Oracle v1，可按方案开始实现，但本轮不实施或求值。**

## 1. 本地状态与已发布依据

实际执行git status -sb、git branch -vv，读取公开分支提交树，并通过git ls-remote只读查询远程main和release/public-v1.2.1；没有fetch、切分支或同步工作树。

| 对象 | 本轮核对结果 |
| --- | --- |
| 当前开发main | status显示ahead 6、behind 14；仍有既有修改/删除/未跟踪成果，不是干净开发树，不覆盖或同步这些工作 |
| 独立公开工作树 | release/public-v1.2.1，HEAD=953e7ad55d28c4d4182182d83bc4816ab2c4fb84，工作树干净 |
| 远程main与公开分支 | 本轮实际查询均指向953e7ad55d28c4d4182182d83bc4816ab2c4fb84，不仅依据本地跟踪引用判断 |
| 拟新增reference/channel_cohort.py | 开发树和公开工作树均不存在；公开提交树也不包含 |
| 拟新增tests/test_reference_channel_cohort.py | 两工作树均不存在；没有渠道专项计算回归 |
| 拟新增reference/regression_checks/A3-11_channel.md | 两工作树均不存在，没有可冒称已运行的渠道回归记录 |

使用rg搜索开发树reference/tests/src的Python文件（含隐藏/忽略文件），并用AST检查函数名：没有channel命名的函数，也没有calculate_channel_reference实现。现有channel_id内容属于订单字段校验及Fixture静态关联检查；总体和类别计算器不是渠道实现。此结论限定于所核开发/公开工作树和该公开提交，不推断其他机器或未查询的分支。

权威依据为公开提交中的[渠道实施方案](https://github.com/yanchen-32/data-agent-x/blob/953e7ad55d28c4d4182182d83bc4816ab2c4fb84/reference/manual_checks/A3-11_channel_oracle_plan.md)，通过git show读取。其完整文件SHA-256为`178c5061a1741f3f85688fdfc21c197a9fd4be604e1cc1db7031604cc3f3eb08`，与[本地方案](A3-11_channel_oracle_plan.md)一致。

另核对方案、正式Fixture、独立expected、冻结审核、原输入草案、台账初稿、cohort.py与category_cohort.py共八份文件：开发副本和公开工作树副本均与953e7ad提交对象逐字节一致。不因开发树reference目录未跟踪，就把这些已公开文件误判成未公开成果。

## 2. 已确认的输入与输出契约

拟实现接口为`calculate_channel_reference(data: Mapping[str, Any]) -> dict[str, Any]`，仅放在reference/channel_cohort.py。**只接收Fixture的input映射**，不接收完整Fixture、路径或expected，不读取grouping_dimension及冻结元数据，不导入生产业务代码。

| 契约部分 | 确认内容 |
| --- | --- |
| 固定输入 | 既有context/orders/refunds/dimensions；A3-11固定域/快照、单地区西北过滤、双半开支付窗、H=604800秒，原快照ID含_draft仍保留，不重新命名或换Scope |
| 总体复用 | 调用既有calculate_reference(input)，复用输入检查、有效支付队列、地区过滤、成熟/支付水位/退款水位、空窗判定、总体指标及变化；不复制或改写其业务语义 |
| 原有返回字段 | 原样保留outcome、reasons、quality_checks、candidate_order_ids、metrics；quality_checks只保留总体函数现有三个成熟/水位布尔值，不伪造expected中的目录/DQ计数 |
| 新增返回字段 | aggregate_rows、group_order_ids、group_refunded_order_ids；两个台账按baseline/current，再按channel_id保存排序的order_id列表 |
| ready输出 | **A3-11固定正例应返回六条聚合行：四条渠道行、两条总计行**，与冻结expected比较；不是通用函数对任何输入都固定六行 |
| 聚合行结构 | window_index、dimension_id、group_id、group_label、paid_orders、refunded_orders、rate；总计三个身份字段均为None，渠道行dimension_id=channel、group_id取订单channel_id，展示名来自同Scope渠道目录 |
| 精确数值 | N/U为整数，rate及已定义变化为Fraction；本地返回契约不是正式API十进制序列化；不平均渠道率 |
| 不足/异常 | overall不足时聚合行=[]、两组台账={}，保留原空metrics与候选诊断；关键关联检查先于不足返回。ValueError拒绝不是生产blocked_by_quality状态对象 |

测试端从既有静态预期读取来源、反例及诊断，不要求函数返回source_row_id、退款事件证据、counted_refund_order_ids或全部质量计数字段。分组订单台账与原始订单/退款关联后再核对来源，不能把测试端推导字段冒称函数实际返回字段。

## 3. 关键关联、退款归属与实现边界

- 产品/地区/渠道目录以(domain_id,snapshot_id,对应ID)索引，显式检查重复和域/快照混入，不用裸ID或label联接。全部原始订单的产品复合键必须成功关联，包括过滤外/窗口外订单及比较前提不足时；缺失产品须定位order_id、source_row_id和完整键，不能静默转为未知组。
- 渠道直接取订单channel_id，不经产品类别推断。目录label只显示，不改变身份或N/U。最小方案只承诺已登记渠道；未知渠道超出当前参考输入范围的拒绝不能被解释为新的业务关键DQ规则，DD02非关键未知保留要求仍待相应边界扩展。
- 总体函数没有返回合格退款订单集合；渠道层需从原始refunds独立重建。退款通过(domain_id,snapshot_id,order_id)归属订单，必须success、处于闭合[paid_at,paid_at+H]且不晚于as_of，同单多事件只使U增加一次。
- 先使用总体已过滤的每窗候选支付集合，再按订单渠道分组；退款集合与该窗候选集合相交后计U。按支付时间归属窗口，不按退款发生日期另划窗。东南四单及两笔退款不能进入固定西北分子或分母。
- 各组支付/退款集合互斥穷尽，总计与分组使用同Scope；ΣN组=N总计、ΣU组=U总计。独立分组汇总还须与overall指标对照，不以复制总体U或摊分比例代替计算。

回归从方案C01/C02起步：只传input，比较冻结六行的唯一身份、精确Fraction、两个组台账、总体变化及来源；随后按C03～C07验证过滤反例、复合键、门槛、退款去重和隔离，C08展示名补强仍为Should。此为起点确认，没有创建测试或记录新的通过数量。

生产Runtime、数据库/SQL、授权、DQ映射、贡献及跨维通用化均不在该最小参考实现内；原总体/类别函数及旧回归保持独立稳定。

## 4. 冻结SHA-256与本轮保护

以下四项均从当前磁盘只读计算，与[冻结审核记录](A3-11_freeze_review.md)、已发布方案及提交对象匹配：

| 对象 | SHA-256 |
| --- | --- |
| [11号Fixture完整文件](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json) | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| [独立expected完整JSON](A3-11_expected.json) | c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e |
| 规范化input | 459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 |
| 规范化expected | 27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91 |

规范化采用UTF-8编码的json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，不含末尾换行。Fixture.expected与独立记录.expected相等，正式input与原草案input相等。仅读取已冻结聚合行，确认静态列表为六行且键唯一；没有从订单求值或重新生成expected。

本轮只新增本检查记录；未调用参考函数、运行冻结审核中的求值/静态脚本或pytest，没有新增actual结果。2026-11-02公开工作树相关68项、全量128项为[先前发布记录](../regression_checks/A3-11_publication.md)的历史本地证据，不是本轮运行、渠道专项或CI。

未修改11号Fixture、expected、原草稿、已发布方案、生产/参考源码、Provider、旧记录、架构或路线图；不提交或推送，也不将此起点确认记为渠道能力、用户本人验收或G0通过。
