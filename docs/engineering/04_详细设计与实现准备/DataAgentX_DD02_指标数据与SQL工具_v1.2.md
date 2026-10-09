# DD02 指标数据与受控SQL工具 v1.2

日期：2026-10-09；基线DAX-RB-1.2。状态：设计规格已修订，应用实现/运行验收待完成。控制依据：[SRS v1.2](../01_需求基线/DataAgentX_SRS_v1.2.md)。本版完整替代同模块v1.0/v1.1实施指导，旧版保留历史。

<a id="data"></a>
## 1. 数据与质量

固定合成快照，订单单品/单次有效支付；raw保留source_row_id和可注入坏记录，normalized只放核验后的数据。导入staged/approved/quarantined；正常工具只用approved固定授权视图，DQ Adapter可读固定授权检查层，模型无raw权限。快照/目录/知识带hash、水位和规则版本，切换前排空任务。

检查重复主键/事件、必需时间缺失、孤立或早于支付退款、维度键重复/域混入、半开窗口、观察成熟、水位/零分母、结果完整性。关键问题阻断；未知非关键维度进入__unknown__并披露，不默默丢组。DQ检查profile由服务端注入，模型不能关闭；修复创建新快照。

<a id="metric"></a>
## 2. 指标、过滤与贡献

metric_id=refund_rate_order_horizon。先限定授权域/快照与filters.region_ids（[]全部或单ID），再取paid_at∈[start,end)订单，按同域/快照/订单EXISTS取成功退款在[paid_at,paid_at+H]且≤as_of，同单最多计一次。N为支付单数，U为合格退款单数，rate=U/N，N=0返回null及不足原因。每单paid_at+H≤as_of、支付水位覆盖窗口末端、退款水位覆盖最大paid_at+H，否则不可比。H=604800秒/UTC为登记合成默认，禁止把近期退款事件率混为本指标。

地区名称先由当前域目录解析为region_id，歧义澄清/未知拒绝/越权403。过滤必须在分组之前应用，所有总计与category/region/channel分解共享同Scope。QuerySpec无过滤覆写字段；冻结后不可由模型切换地区。要调查新地区显式新任务，禁止混合旧证据。最多一个地区过滤、单次一个维度，无多地区并集、任意条件或跨维联接。

计数精确整数，率/贡献Fraction；序列化Decimal精度50、ROUND_HALF_EVEN并去尾零/负零，展示百分数两位ROUND_HALF_UP。Δrate=r1−r0；相对变化r0=0时null。共享组i的within=(w1+w0)/2×(r1−r0)，structure=(r1+r0)/2×(w1−w0)；新增组entry=w1×r1，退出组exit=−w0×r0。权重为过滤后窗口支付占比；共享/新增/退出互斥，覆盖未知组，各分量和与总Δ残差≤1e-6。内部贡献单位ratio，显示百分点乘100；跨维分解不能相加或写因果。

<a id="sql"></a>
## 3. QuerySpec与数据库安全

| 工具 | 模型输入 | 服务端保证 |
| --- | --- | --- |
| metric_catalog.get | metric_id/version | 精确授权目录，不用RAG改公式 |
| quality.check | scope_hash | 绑定snapshot和必需检查，产DQ证据 |
| sql.query | template_id/scope_hash，分组模板需dimension | 注入同Scope过滤/窗口/H/目录/DQ，参数化执行 |
| analysis.run | 白名单operator、授权query证据ID | 四算子cohort_rate/compare_rates/decompose_rate_change/rank_contributors；拒任意代码 |

模板仅cohort_totals/cohort_by_dimension/registered_quality_summary；模型不传SQL、表列标识、账号、连接串或期限。dimension通过固定映射选择预审模板，region值走绑定参数，不能插入SQL文本。R0 Schema拒绝candidate_sql；复杂候选SQL AST解析不进入当前实现，不引入SQLGlot依赖。未来若选自由SQL需独立范围变更和完整AST/绑定/复杂度安全评审。

每域固定只读角色与过滤视图；不可登录owner持底表。查询身份无底表/其他域/app_state、DDL/DML/文件/网络/角色权限；固定search_path及只读事务。视图权限与实际权限探针验证，不以只读事务代替域隔离。模板源代码纳版本和review。攻击包含未注册模板/维度、区域ID注入字符串、跨域ID、过滤覆写、篡改scope_hash、提示注入和直接DB写探针，关键100%拒绝；合法完成率同时报告。

<a id="execution"></a>
## 4. 执行证据与评分边界

域连接借用→登记task/call/backend/generation→只读与min(10秒,剩余active)服务器期限→固定模板/参数→完整聚合后最多1001行探测超限，公开≤1000且truncated→提交/rollback并复位或丢弃连接。取消句柄绑定generation，迟到取消不能作用于下一借用者；状态不明连接隔离。服务端SQL停止由测试运维身份采证，权限不授模型。

QueryEvidence绑定scope_hash/数据与指标/模板/策略版本、执行SQLhash与安全参数摘要、DQ依赖、结果列型/完整性/耗时。AggregateRow使用dimension_id/group_id/group_label；总计前两者null，显示名不参与分组身份。结果不可截断后声称完整贡献。

T01 Scope Interpretation Accuracy：用户→metric/version/window/H/as_of/timezone/filter/dimensions全部正确，≥40合法标注请求且≥90%，另≥20澄清硬例全过。T02 Selection Accuracy：给定正确Scope只判template/dimension/引用，≥40且≥90%；SQL Execution Correctness：给定正确Spec与独立逐订单Oracle核对，支持模板核心硬例100%。危险拒绝与合法完成/误拒分别计分，不把Scope错误算成模板编译错误。覆盖单地区×三维、跨域同名、UTC/offset等价、退款边界/去重、未知/新增/退出/同名组。上述是待实现验收，当前参考计算不是PostgreSQL安全证据。
