# G0：十个主Fixture覆盖矩阵与缺口优先级

审查日期：2026-10-30。结论：**十个主样例均能定位业务规则、独立预期、来源和参考验证，但不能据此宣布G0通过**。当前主要缺口是三维分组闭环、合法跨域同名正例、贡献分解Oracle/计算，以及质量负例与验收证据闭环。

本次审查在下列明确范围内完成；目标能力仍需补齐。只新增审查文档与 [机器可读清单](G0_fixture_inventory.json)，不修改Fixture、冻结Oracle、参考实现、测试、宪章或路线图，不补写尚不存在的通过记录。

## 1. 审查边界与证据层级

主要依据为 [项目宪章R0边界](../../docs/PROJECT_CHARTER.md)、[路线图M1](../../docs/ROADMAP.md)、[DD02 §1–4](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)、[指标目录](../../docs/engineering/02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)及 [DD06 §1/3/4](../../docs/engineering/06_评测与验收/DataAgentX_DD06_评测与验收设计_v1.2.1.md)。DD02明确要求单地区×三维、跨域同名、UTC/offset等价、退款边界/去重及未知/新增/退出/同名组；宪章明确category/region/channel单维聚合。

仓库当前没有独立名为G0的完整放行表；SRS中的G01等是目标编号，不是本任务的G0验收。本文以本次请求及上述契约作为审查范围。Must/Should是**本次覆盖缺口的建议优先级**，不改写SRS优先级或暗中新增正式放行门槛。标为“生产/正式评测”的Must不能与当前Fixture层工作混为一谈。

代码锚点为已提交公开版本 [d7b702a](https://github.com/yanchen-32/data-agent-x/commit/d7b702a6ea517d5e3e0ff437d39c714e8155023c)；本地核心输入、参考源码和相关测试与该提交另作字节比对。本次pytest在开发工作树执行，**不是公开工作树执行或CI**；本轮不刷新远程引用，不推定未来main仍是同一版本。

| 层级 | 实际含义 | 不能替代的证据 |
| --- | --- | --- |
| 固定主Fixture | 01～10的十份主JSON，输入、业务规则、calculation_basis及expected静态保存 | 数量十不等于机制全面、本人验收或G0通过 |
| 历史版本 | 08_category_entry_exit.v1.json，原六单快照与四项回归继续保留 | 不是第11个独立主例，不以v1通过代替v2 |
| 嵌入控制变体 | A3-01-EQUAL、A3-01-IMMATURE，共两个，有显式input_overrides和静态预期 | 不是两个新主例，也不是未见盲测样本 |
| 测试内变体 | 改名、退款时间/状态、地区、目录错误、比较门槛等，在测试中复制/修改输入 | 不自动成为固定Fixture或独立人工Oracle |
| 算术反例 | A3-05未过滤反例、A3-09丢弃未知组反例 | 不是新固定输入；有反例说明不等于已执行另一条完整计算路径 |
| 独立预期 | ORACLE.md及先行逐单记录，不由参考函数输出回填 | 独立于计算代码不等于首次盲审、第二审核者或用户本人签字 |
| 参考验证 | 标准库总体/类别函数对照；关键异常以ValueError拒绝 | 不等于PG/SQL、生产DQ状态、授权或QueryEvidence已实现 |
| 生产/正式评测 | DQ Adapter、授权数据视图、受控SQL、确定性分析、证据链、正式数据封存等 | 不由基础API测试、本地pytest总数或设计文件推定已通过 |

冻结JSON里的“尚待计算”等文字按创建阶段快照保留。当前行为应结合后续回归记录和源码判断，不能为消除历史文案差异重写冻结文件。

## 2. 十个主Fixture逐例矩阵

下表的“验证”指现有测试路径及本轮相关回归，不表示每个冻结outcome都由参考函数以同名生产对象返回。03/10的关键拒绝与正式blocked_by_quality映射特别区分。输入规模为原始支付行/退款事件行，不能当作正确率分母。

| 主例与固定输入 | 业务规则及输入规模 | 独立预期摘要 | 独立依据/来源 | 参考验证及证据边界 |
| --- | --- | --- | --- | --- |
| A3-01 [成熟水位](../../tests/fixtures/order_boundaries/01_maturity_watermark.json) | 2/0；成熟与两类水位分别检查，等号允许 | 主输入退款水位差1微秒，insufficient_evidence，两窗指标null；EQUAL控制两窗1/0/率0；IMMATURE控制同时披露未成熟和退款水位不足 | [ORACLE](../../tests/fixtures/order_boundaries/ORACLE.md)、[先行台账](../manual_checks/2026-10-14.json)和[逐单说明](../manual_checks/2026-10-14.md) | 总体测试的test_reference_matches_precomputed_manual_record_and_fixture及两个控制测试；input哈希绑定。不是把无退款直接当零率 |
| A3-02 [UTC与offset边界](../../tests/fixtures/order_boundaries/02_utc_boundaries.json) | 6/5；事实时间为+08:00，支付半开、退款闭合、微秒边界、failed排除及同单去重 | 两窗均N=2/U=1/率1/2，变化0；起点前与当前end支付排除；normalized_paid_at_utc列出六单UTC时刻 | 同上先行台账及[ORACLE](../../tests/fixtures/order_boundaries/ORACLE.md)，逐退款决定可追溯 | 总体固定样例对照；已有固定offset输入，不能登记为“缺少offset”。同一整份输入换表示后的等价配对仍可补强 |
| A3-03 [重复订单](../../tests/fixtures/order_boundaries/03_duplicate_orders.json) | 3/1；同域/快照D-B重复，来源行d-row-1/d-row-2不同 | 1个重复业务键组涉及2行；blocked_by_quality；两窗指标及变化null | [ORACLE重复键推导](../../tests/fixtures/order_boundaries/ORACLE.md)，expected.duplicate_order_groups定位来源 | test_reference_rejects_duplicate_orders_instead_of_silent_deduplication实际要求ValueError；不直接验证生产blocked_by_quality序列化 |
| A3-04 [零分母](../../tests/fixtures/order_boundaries/04_zero_denominator_window.json) | 3/1；基期原始支付无效，不能用0/0=0 | 诊断基期0/0，当前2/1/率1/2；正式两窗指标及变化均null | [ORACLE](../../tests/fixtures/order_boundaries/ORACLE.md)、[04/05独立复核](../manual_checks/A3-04_A3-05_review.md) | test_reference_matches_frozen_boundary_fixture[A3-04]核对候选集合、正式空指标，测试侧按输入另验诊断；诊断不是参考函数新增字段 |
| A3-05 [单地区过滤](../../tests/fixtures/order_boundaries/05_single_region_filter.json) | 6/3；西北Scope先过滤分子和分母，东南来源排除 | 西北基期2/1/率1/2，当前1/1/率1，绝对变化1/2；未过滤反例为−1/3 | [ORACLE](../../tests/fixtures/order_boundaries/ORACLE.md)、[04/05独立复核](../manual_checks/A3-04_A3-05_review.md) | test_reference_matches_frozen_boundary_fixture[A3-05]核对固定总计；类别函数另有地区过滤变体。**地区过滤不是地区分组**；未过滤反例不计新增主例 |
| A3-06 [同单多退款](../../tests/fixtures/order_boundaries/06_multiple_refunds_per_order.json) | 4/4；不同refund_id的正常多事件，同单U最多加1 | 两窗事件数各2，退款订单U分别1、2；N各2，率1/2→1 | [ORACLE](../../tests/fixtures/order_boundaries/ORACLE.md)、[独立计算与运行记录](A3-06.md)，事件及订单来源均列明 | test_reference_a3_06_counts_refund_orders_not_events；不是重复refund_id错误的负例 |
| A3-07 [同名不同ID](../../tests/fixtures/order_boundaries/07_same_label_distinct_category_ids.json) | 6/2；两个类别同名“图书”，按稳定ID和产品复合键分组 | 基期A=1/0、B=1/1；当前A=2/1、B=2/0；总率1/2→1/4，四类别行+两总计 | [ORACLE](../../tests/fixtures/order_boundaries/ORACLE.md)、[先行人工台账](../manual_checks/A3-07_review.json)及[说明](../manual_checks/A3-07_review.md) | test_category_reference_matches_six_frozen_rows_and_manual_sources、同名/改名及产品关联变体；静态按窗×类别追溯退款。此为同域同名，不是跨域同名正例 |
| A3-08 v2 [共享/新增/退出](../../tests/fixtures/order_boundaries/08_category_entry_exit.json) | 8/6；A共享、B退出、C新增，缺席不补率 | 基期A=2/0、B=2/2；当前A=1/1、C=3/3；总计4/2→4/4，率1/2→1 | [v2先行台账](../manual_checks/A3-08_v2_expected.json)、[逐单说明](../manual_checks/A3-08_v2_expected.md)、[ORACLE](../../tests/fixtures/order_boundaries/ORACLE.md) | [v2四项专用回归](A3-08_v2.md)，Fixture/台账/input三哈希绑定，来源及守恒；v1另四项仅历史回归。数据足以支撑非平凡贡献，但**没有冻结贡献值或贡献函数** |
| A3-09 [合法未知类别](../../tests/fixtures/order_boundaries/09_unknown_category_preserved.json) | 8/5；产品真实存在，仅category_id=null | 基期已知2/0、未知2/2；当前已知2/1、未知2/2；总率1/2→3/4，未知均Fraction(1) | [先行台账](../manual_checks/A3-09_expected.json)、[创建说明](../manual_checks/A3-09.md)、[回归](A3-09.md) | test_category_reference_a3_09_matches_frozen_unknown_category_oracle固定绑定；六行、原始来源、精确Fraction和不丢单。本人独立验收仍[待确认](A3-09_acceptance.md) |
| A3-10 [关键产品关联缺失](../../tests/fixtures/order_boundaries/10_missing_product_join_blocks.json) | 4/2；仅J10-C2/r10-row-c2引用缺失产品键 | 冻结预期blocked_by_quality，两窗指标及变化null、无聚合行；不得归unknown | [来源台账](../manual_checks/A3-10.json)、[先行Oracle](../manual_checks/A3-10.md)、[红绿灯记录](A3-10.md) | 固定拒绝测试+ready/immature拒绝变体，以ValueError定位完整键；A3-09继续兼容。正式DQ映射未实现，本人验收[待确认](A3-10_acceptance.md) |

对应执行入口为 [总体参考测试](../../tests/test_reference_cohort.py)、[类别参考测试](../../tests/test_reference_category_cohort.py)及 [Fixture静态检查](../../tests/test_boundary_fixtures.py)。所有主例都有对应ORACLE章节与本轮覆盖的参考验证路径，但其中只有8例走返回值/数值或前提不足对照，03/10走异常拒绝；不能把两例异常测试说成正式质量状态对象已通过。

## 3. 扩展覆盖矩阵：有数据不等于有能力

| 必查方向 | 固定Fixture | 已有控制/单元覆盖 | 实现及实质缺口 |
| --- | --- | --- | --- |
| category分组 | 07/08v2/09有明确组ID、六行预期及来源；10规定不发布 | 同名、改名、产品关联、未知、目录异常、地区过滤后类别计数 | 有标准库类别参考实现及固定比较；不是生产SQL |
| region分组 | 05有两个地区及过滤总计，但没有dimension_id=region的固定分组输出 | 单地区过滤约束分子/分母及类别结果 | **缺region分组Oracle、参考实现与固定比较**。region_id字段存在不算分组覆盖 |
| channel分组 | 全部主例的订单均为channel_web，没有第二个实际渠道，也无channel聚合行 | 无channel分组验证路径 | **缺有区分力的多渠道输入、Oracle、实现及回归**。不能以一行渠道目录判覆盖 |
| 单地区×三维共享Scope | 05验证西北总计；07变体验证地区过滤后的类别 | test_single_region_filters_denominator_and_refunds_before_grouping | 类别有局部证据，地区/渠道缺闭环；需确保同Scope、先过滤后分组及ΣN/U一致 |
| 跨域同名/同ID | 十个主输入均为domain_a；07仅同域同名 | 目录domain_id/snapshot_id变为foreign_scope会被拒绝 | 负例不能证明合法两个授权Scope分别计算且不串数；缺配对正例及后续真实权限隔离 |
| UTC offset等价 | **02已有+08:00事实与UTC规范化清单、边界及独立预期** | refund观察期offset上界变体；单行订单datetime offset→UTC测试 | 核心正例已覆盖，不列为Must缺失；整份Z/+offset等价配对、其他偏移/上下文字段可Should补强 |
| 贡献分解输入 | 08v2共享A率0→1、权重1/2→1/4；B退出有退款、C新增有退款；09保留未知组 | 08验证身份及守恒，09验证未知不丢单 | **输入已具备非平凡条件，但没有within/structure/entry/exit独立冻结预期、贡献参考计算或残差测试**；不能把生命周期判断当贡献分解 |
| 来源追溯 | 十例均有source_row_id与规则/预期；03定位重复来源，04/05含排除集合，06区分事件/订单，07～10有分组或故障台账 | 07按窗×类别静态追退款；08～10原始订单/退款/产品键追溯；01/02 input哈希 | 原始行到本地Oracle可追溯，不是“没有来源”；统一批准数据版本/生成机制/审阅签收及生产QueryEvidence仍未闭环 |
| 其他关键DQ | 03重复订单、10缺失产品为固定负例；06是合法多事件 | 目录重复/域快照混入有拒绝变体；时间单行格式有校验测试 | 重复refund_id、孤立退款、支付前退款虽有参考拒绝代码，但未发现对应固定负例或直接参考回归；不能把06当重复事件ID覆盖 |

### 贡献输入的专门判断

08v2中A的N从2到1、总N两窗均4，故支付占比1/2→1/4；A的U从0到1，率0→1，组内与结构项均有辨识空间。B在基期N=2/U=2，C在当前N=3/U=3，新/退出组都有非零退款。v1的C零退款历史也可作为后续退化对照，但不计第11个独立主例。

本轮只核对输入可用性，**不在审查里替用户新增贡献真值**。应先按DD02公式独立逐组手算并冻结within/structure/entry/exit，再写独立Fraction参考实现，检查合计等于总Δ及残差≤1e-6、ratio与百分点转换。09未知组当前两窗权重和率都稳定，能检验保留，但不能替代“未知组有非零贡献”的新硬例。会计分解不等于因果解释。

## 4. 缺口优先级与下一步验证方式

### 4.1 Must：优先补齐当前数据/Oracle证据

| ID / 优先级 | 缺口与阶段 | 已有覆盖，避免重复建设 | 下一步与可核验完成条件 |
| --- | --- | --- | --- |
| M01 / Must | G0三维固定分组闭环缺region/channel | category固定Oracle与参考函数，05地区过滤，单地区类别变体均可复用 | 独立设计region/channel有区分力输入和双窗组/总计预期，再实现/比较各维。全域下至少两个实际ID；单地区过滤后地区维度只有选中地区一组可以合法，不强求两个组。验证各维同Scope、互斥穷尽、Fraction及来源追溯，不能只断言行数 |
| M02 / Must | G0合法跨域同名/同ID隔离正例缺失 | 07同域同名及目录域/快照混入拒绝已覆盖，勿再写同一负例充数 | 建立两个分别合法的域/快照Scope，复用相同标签/局部ID但安排不同订单与退款，先手算各自预期，再证明不串数。不要把foreign行塞入单Scope然后只测ValueError来冒充正例；真实DB授权隔离另在M06验收 |
| M03 / Must | G0贡献Oracle/独立计算及残差覆盖缺失 | 08v2非平凡输入、09未知组、现有分数/来源/守恒辅助函数可复用 | 先冻结逐组权重、率与四类贡献，不从待测函数反推；再独立标准库/Fraction计算。比较所有贡献项、正负符号、总Δ、残差和单位，拒绝以“仅组生命周期正确”判过 |
| M04 / Must | G0关键退款DQ直接负例不完整 | 03重复订单、10产品缺失、目录重复/跨Scope变体已有；06正常多退款不等于事件ID重复 | 分别补唯一故障的重复refund_id、孤立退款、支付前退款，以及必需退款时间缺失；其他时间/键合法，来源明确，先写独立不发布预期，再核对参考拒绝。现有支付字段datetime单行测试不能代替原始退款输入验证；本条不强行将DD06正式T03的24例规模搬入当前十例 |
| M05 / Must | G0独立复核、版本与证据签收闭环尚缺 | 十例都有原始来源和先行推导；01/02绑定input哈希，08v1/v2、09、10有不同程度的固定文件/台账绑定；本审查另附十例哈希 | 建立维护性数据版本清单与逐案审阅状态，绑定输入/预期/规则/参考代码/实际结果；手工合成如实记manual，不杜撰生成器或种子。标注已知预期、同人复核限制，取得真实用户独立复核/确认；不无依据要求或宣称第二审核者。当前清单不是approved dataset_manifest或签字 |

### 4.2 Should：已有路径上的边界补强

| ID / 优先级 | 缺口 | 已有覆盖 | 下一步验证方式 |
| --- | --- | --- | --- |
| S01 / Should | 整份输入不同时间表示的等价配对未固定 | 02已经覆盖+08:00事实→UTC及边界；退款offset端点、单行支付offset正常化已有测试 | 不改02冻结输入，建立同瞬间Z/+offset配对控制，覆盖支付、退款、window、as_of和水位，比较候选集合/各组/总计完全一致；再按冻结语法补负offset或非法偏移拒绝。不要登记为“从零补offset” |
| S02 / Should | 成熟/支付水位的孤立固定边界可更清楚 | 01主例退款水位不足、EQUAL等号、IMMATURE同时含未成熟与水位不足；类别测试内另有单独immature/payments/refunds控制 | 固定“仅未成熟且水位完整”“仅支付水位差1微秒”等独立预期，保留已覆盖控制，避免耦合故障掩盖判断原因；不重复新增同一EQUAL输入 |
| S03 / Should | 未知组新增/退出及非零贡献、退化组合不足 | 08为已知类别生命周期，09未知组两窗shared且占比/率稳定，08v1有真实零退款组 | 在M03之后用新快照补未知组entry/exit或权重变化、净Δ接近0、零退款组等，独立算预期；区别缺席无行、真实正分母零率与未知组身份 |
| S04 / Should | 不可有限小数与展示精度样例较弱 | 主要正式预期为0、1/2、1/4、3/4；05未过滤反例含1/3和2/3，但不是正式序列化验证 | 加可手算的非终止分数及零基期正变化例；独立核对精确Fraction和相对变化null，再在正式序列化层验Decimal50/HALF_EVEN、展示HALF_UP、去负零。输入样例补强不等于序列化已实现 |

### 4.3 Must但属于生产/正式评测阶段，不偷换当前Fixture审查范围

| ID / 优先级 | 未实现/未验收能力 | 已有局部覆盖 | 下一步验证方式 |
| --- | --- | --- | --- |
| M06 / Must（M1/生产） | blocked_by_quality状态映射、DQ证据/恢复、新快照批准、受控PG SQL与真实授权、结果完整性及正式数值序列化 | 01/04在本地参考函数返回insufficient_evidence；03/10用ValueError拒绝；Scope只是合成前提，category行率为内存Fraction | 在生产DQ Adapter/QuerySpec→受控模板SQL→分析/QueryEvidence链路做集成验证，检查禁止继续查询/发布、故障来源、恢复条件/新快照、两域权限探针、完整结果及规范序列化；不要让参考函数伪造TaskView。当前src仍是health/items基础API，不能用127/132项历史pytest替代这些证据 |
| M07 / Must（正式评测） | dataset_manifest/public_case/private_label隔离、机制/生成与种子登记、批准版本、独立评分及CI/正式归档 | 当前十例是公开开发样例，metric_version=null，预期已公开；已有本地回归与文件哈希，不是未见盲测集 | 按DD06另建真实可审计清单、机制分组和私有答案隔离，冻结实际配置/评分器，真实执行并归档；不能把公开expected改名为private_label就称未见。正式120例、分层规模及三轮要求不等同当前G0十例检查，不凭本审查宣称达到 |

建议顺序：M01三维闭环与M02合法隔离正例可分别准备，M03先冻结贡献真值再编码，M04补关键DQ直接负例，M05贯穿逐案复核；M06/M07进入各自实现阶段。此清单是技术依赖顺序，不是个人逐日日程，也不授权本轮实施这些功能。

## 5. 本轮实际检查及结论边界

本轮用单次临时标准库脚本、不导入reference或生产函数，逐个读取11份JSON（十主例及08v1），并应用两个已有01控制覆盖项。按原始支付/退款行独立检查Scope、来源唯一性、半开窗、观察期、成熟水位、计数/精确分数及已有类别组汇总；03遇重复键只定位不偷偷去重，10遇缺失产品只确认关键错误及不发布预期。独立检查与现有静态预期一致，未生成或回写新Oracle。

本次检查A3-02的六单UTC规范化时刻与输入+08:00表示一致；04诊断为基期0/0、当前2/1，仍保留正式指标null。审查产生的diagnostic_totals只收录于 [清单](G0_fixture_inventory.json)，不是参考函数新增返回字段。覆盖JSON中的source ID和台账来源并不证明实际数据库导入或真实授权。

本地实际执行：

```bash
.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py tests/test_reference_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
...................................................................      [100%]
67 passed in 0.28s
```

退出码0，包含38项类别、9项总体及20项静态检查。**本轮未运行全量pytest、公开工作树pytest或CI，也未运行生产SQL。** [A3-10提交记录](https://github.com/yanchen-32/data-agent-x/blob/d7b702a6ea517d5e3e0ff437d39c714e8155023c/reference/regression_checks/A3-10.md) 的开发132项、公开127项是2026-10-29历史本地证据，不作为本轮重跑结果。

### 限定审查单元的质量观察

下列为逐项人工观察统计，不是测试通过率或G0正确率；分母分别指列明的主例、扩展检查族或本次结论，不能相加。0/N仅表示限定检查未观察到错误，不代表N个生产场景已验收。数据验证技能的自动汇总脚本需要Node，本环境没有node/nodejs，故脚本未运行、未生成自动评分；以下判断以逐例来源与矩阵为依据。

| 类别 | 观察到的缺陷 | 评估 |
| --- | --- | --- |
| 覆盖完整性（五个扩展检查族） | 3 / 5 | 三维闭环、合法跨域同名、贡献闭环有实质缺口；offset已有固定证据，原始来源可追溯，但两者仍有补强/生产边界 |
| 说明清晰度（本次结论） | 0 / 1 | 已区分固定、历史、控制、变体及生产能力，未据数量判过 |
| 视觉与交互一致性 | N/A | 交付静态技术矩阵，无交互应用或图表，未开展UI验收 |

| 类别 | 观察到的缺陷 | 评估 |
| --- | --- | --- |
| 规则适用性与独立预期 | 0 / 10 | 十主例规则及先行预期可定位；保留非首次盲审/本人未确认限制，不声称新增审核者 |
| 固定预期算术/关键拒绝边界 | 0 / 10 | 本轮独立检查与相关回归未见现有十例数值或关键拒绝矛盾；不是SQL准确率 |
| 图内一致性 | N/A | 无图表、tooltip或展示数值绑定 |
| 原始来源追溯 | 0 / 10 | 限原始行→本地台账/预期；未把生产QueryEvidence或批准manifest纳入已通过范围 |
| 跨材料一致性 | 0 / 10 | 限当前输入/预期/参考验证；03/10异常拒绝与冻结状态对象差异已披露，不误判为生产映射通过 |
| 已有十类质量/边界控制 | 0 / 10 | 仅指主例所声明规则；M04的未覆盖DQ、M06的生产流程仍未验收，不是所有DQ全覆盖 |
| 结论支持（不判G0通过） | 0 / 1 | 三个扩展检查族缺口及独立验收状态足以限制结论，无需借总测试数宣告完成 |

## 6. 验收状态与文件保护

- 审查交付：列明的十主例及扩展方向已核对，矩阵与下一步验证方式已登记；不声称遍历所有业务组合。
- 固定参考回归：有本轮67项本地通过证据；当前十类均有验证路径，关键异常以参考拒绝验证。
- G0放行：**不宣布通过**；M01～M05仍需补齐/明确核验，生产及正式评测按各自阶段处理。
- 用户本人独立人工验收：未据现有记录认定完成。[A3-09](A3-09_acceptance.md)、[A3-10](A3-10_acceptance.md)均待本人明确确认；本审查不代签其他样例。
- CI、生产、正式盲测：未由本次审查验收；公开开发输入不是未见盲测。
- 保护范围：结束时复核69个原有测试、参考、来源记录和项目说明文件的SHA-256未变；只新增本矩阵及清单。未修改路线图复选框、未提交或推送。`git diff --check`退出码0。

## 7. 后续局部证据：A3-11最小渠道参考（2026-11-06）

以上十主例审查和表格保留原时点。本地A3-11现已按独立冻结六行完成渠道C01～C07，渠道42项、相关110项、开发全量175项实际通过且冻结指纹不变，详见[Must关闭评审](A3-11_Must_review.md)、[原始输出](A3-11_full_regression_pytest.txt)和[运行版本清单](A3-11_full_regression_public_manifest.json)。C07尚未提交，本轮未推送或验证公开工作树；这些是本地计算证据，不是CI或用户本人签收。

仅关闭A3-11最小渠道参考的Must。M01获得“固定地区过滤后多渠道分组、总计、来源和控制”的局部闭环证据；region固定分组尚未闭环，因此**M01整体仍开放，G0仍未验收**。未知渠道支持、C08展示名、合法跨域、贡献、其他DQ/签收和生产/正式评测缺口保持各自状态，不以本次渠道通过推定完成。原机器清单仍是十主例审查快照，不修改其冻结哈希或扩充为批准评测集。

## 后续公开交付验证（2026-11-06）

以上保留开发阶段范围与状态；本次已在公开候选工作树实际通过渠道42项、相关110项、全量170项，源码与冻结指纹不变，见[公开交付验证](A3-11_C07_publication.md)。C07及本评审随此次公开追加提交交付；公开版本摘要绑定45份运行文件，完整内部开发清单保留本地。本地公开pytest仍不是CI或本人验收，仅关闭A3-11最小渠道参考Must，G0与C08保持原边界。

## 8. M01剩余region缺口复核（2026-11-07）

[本轮复核记录](G0_M01_region_review.md)已对照有效DD02、A3-11 Must评审及已知公开提交0278598，确认类别固定参考能力和渠道C01～C07不需重做；地区过滤/目录校验不等于region分组。开发树23份活动Python及23份相关JSON、本地三个分支提交树及其他登记工作树的活动源码中，未发现未公开region分组实现或dimension_id="region"的固定预期。

M01仍缺region先行逐单Oracle、参考计算和固定输出/来源/守恒回归，以及包含region的三维共同Scope结果对齐证据，整体保持开放；可先评估复用11号原始输入的双地区及单地区控制，不覆写已有冻结数据。region扩展行为与生产能力中证据不足的部分已单列，不将类别/渠道测试挪作region验收。本轮只读审查并记录，未新增/重跑pytest、未提交/推送，G0仍不放行。

## 9. region最小契约与用途决定（2026-11-07）

已形成[region实施方案初稿](../manual_checks/G0_M01_region_plan.md)：单地区Scope下仅一个实际组，数值等同总计，不另造地区调查功能；独立小型region参考入口用于合法多地区Scope的有区分力验证。优先复用11号原始输入，合成全地区控制只改深拷贝并单列授权假设；不把清空过滤列表视为生产授权扩大。

草案明确稳定ID/完整复合键、先过滤后分组、退款按支付单归属、未知数据与未知过滤参数及缺展示名的区别，并规划人工Oracle、三维共同Scope和最小回归。本轮没有实现或计算新预期，M01/G0不关闭，原冻结数据及A3-11渠道Must状态保持不变。

## 10. region独立预期与最小测试矩阵（2026-11-07）

已先依据11号原始input保存[人工预期台账草稿](../manual_checks/G0_M01_region_expected_draft.md)，再细化[RG01～RG06测试矩阵](../manual_checks/G0_M01_region_test_matrix.md)，逐项绑定业务规则、输入变更和独立预期来源。全地区合成控制的最晚成熟/退款水位上界为09-21，原西北为09-19；不能复制渠道C05常量或将channel行改名当作region预期。

台账含逐订单/退款来源、双窗地区组与总计、去重/跨窗退款、阻断与来源守恒；局部未知值规则仍属region契约草案，尚未冻结或验收。本轮没有创建region计算器/测试或执行pytest，旧输入/预期与代码不变；M01和G0仍开放，合成全地区控制不扩大生产授权。

## 11. region阶段文档公开交付（2026-11-10）

§8～10材料随本次公开文档提交交付，原审查文字及草稿状态不追溯改写；[阶段记录](G0_M01_region_publication.md)列明公开范围、下一次文件和验收顺序。A3-11最小渠道Must已完成，C08仍为非阻塞Should，M01/G0保持开放；region局部规则与人工预期尚未冻结，也没有region实现/测试通过证据。本次只做文档及静态证据核对，未运行pytest，不改变生产Runtime或授权范围。

## 后续region规则审定（2026-11-10）

已形成[本地参考规则审定v1](../manual_checks/G0_M01_region_rule_review.md)，对未登记源ID、__unknown__、已登记ID缺展示名、非法过滤参数及目录关键异常逐项给出结论。未知留组的前提是数据已属于获准固定输入且缺失仅为非关键维度问题；授权无法确认时在计算前拒绝，不以unknown恢复权限。地区过滤先于归组，已知ID缺label保留身份，未知过滤ID不能转[]或正常空窗。

原2026-11-07草案、台账及矩阵保持原文和原哈希，本记录以新增审定补充限定其待决分支，不修改既有DD02/SRS/Schema或冻结输入/预期。规则结论已形成，机器可读预期及实现/执行仍未完成；M01/G0继续开放，渠道Must和C08非阻塞Should边界不变。

## 后续region Oracle v1冻结（2026-11-10）

已直接结构化已提交的114行人工台账，保存[机器可读Oracle](../manual_checks/G0_M01_region_expected.json)及[冻结记录](../manual_checks/G0_M01_region_freeze_review.md)：RG01.W四行与RG02.A六行的数值、Fraction、订单/退款及逐单来源固定，绑定原Fixture/input、M01-region-rules-v1与来源哈希；另登记40个已明确控制输入的变更/指纹，不把它们的完整业务输出或执行结果冒称已冻结/通过。

实际只做静态来源/算术/守恒及变体指纹重放核对，未调用参考函数、未运行pytest，原草案/数据/规则文件不变。region实现及计算回归仍待完成，M01/G0保持开放；合成全地区授权假设不作为生产权限证据，C08仍为非阻塞Should。

## 后续最小region入口实现（2026-11-10）

已新增calculate_region_reference(input)，复用总体过滤队列/成熟水位并独立以完整订单键去重退款、按region_id分组。RG01.W四行/RG02.A六行实际匹配先行冻结Oracle，首批13项、相关123项和开发全量188项通过，详见[回归记录](G0_M01_region.md)和[原始输出](G0_M01_region_pytest.txt)。原Fixture/Oracle/规则与总体、类别、渠道代码保持不变，生产Runtime未修改。

本次只验证固定正常输入和代表性控制，完整RG03～RG06矩阵、三维共同Scope对照仍待实际验证，M01整体不关闭，G0不放行；C08仍为非阻塞Should。本轮是开发工作树本地pytest，不是公开分支结果、CI、生产授权或本人验收，未提交/推送。

## region实现公开交付验证（2026-11-10）

以上保留各开发阶段及旧输出对应版本；本次公开候选工作树已实际通过地区13项、相关123项、全量183项，详见[公开交付记录](G0_M01_region_implementation_publication.md)和公开版本清单。规则/冻结Oracle/region入口/当前断言版本随本次追加交付，原Fixture及既有计算器不变。M01/G0仍开放、C08非阻塞；公开本地pytest不是CI、真实授权或本人验收。

## M01参考层局部关闭复核（2026-11-13）

已按当前39项地区测试版本实际通过开发树专项39项、相关参考及静态149项，以及基于本地公开7530cb9隔离准备的公开候选全量209项，退出码均0；详见[RG01～RG06逐项评审](G0_M01_region_local_Must_review.md)、[原始输出](G0_M01_region_local_review_pytest.txt)和[版本清单](G0_M01_region_local_review_manifest.json)。两套运行文件各59份指纹前后不变，冻结Fixture/expected、规则和计算器未修改。

本次发现的是来源断言证据缺口，不是pytest计算失败：RG03.D尚未直接核对两笔合格事件ID/source_row_id与去重订单来源；RG05全地区未知变体尚未完整回查原ID归组和支付/退款来源。因此M01参考层继续开放，先在原控制内补齐这两处来源断言再评审，不新增主Fixture或修改答案来消除差异。原13项及后续数值/过滤/身份/成熟水位/三维守恒/独立重排的真实通过状态保留。

label-absent和W联合逆序仍未执行，按最小规则已有替代代表控制，作为非阻塞补强如实列出；C08继续是非阻塞Should。其余M02～M07不因本轮本地回归而关闭。公开候选未提交/推送，不记为GitHub Actions CI、用户本人L3、G0放行或生产Runtime/DQ验收。
