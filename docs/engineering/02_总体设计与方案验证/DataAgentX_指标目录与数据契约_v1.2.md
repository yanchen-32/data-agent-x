# DataAgentX 指标目录与数据契约 v1.2

日期2026-10-09；DAX-RB-1.2；当前完整口径见[DD02](../04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)。旧v1.0仅历史。

| 项 | 冻结定义 |
| --- | --- |
| metric_id / version | refund_rate_order_horizon / 由已批准manifest绑定实际版本，不虚构已安装版本 |
| 粒度 | 同域/同快照单品订单、一次有效成功支付 |
| 分母N | 支付时间[start,end)且在授权域/快照/地区内的有效支付订单数 |
| 分子U | 上述订单至少一次成功退款在[paid_at,paid_at+H]且≤as_of；EXISTS同单只计一次 |
| 可比前提 | 全单成熟paid_at+H≤as_of，支付水位覆盖窗口end，退款水位覆盖max(paid_at+H)，必需DQ通过 |
| 单地区过滤 | filters.region_ids=[]全部或一个授权注册ID；先过滤后聚合，名称仅映射/显示，跨域ID拒绝 |
| 分组 | 每查询一个category/region/channel；键dimension_id+group_id，未知__unknown__；分组互斥穷尽 |
| 时间 | 外部Z/显式offset RFC3339最多6小数→内部UTC微秒Z；无偏移/-00:00/闰秒拒绝 |
| 数值 | U/N；N=0 null，Δratio和相对变化分开；Fraction→Decimal50/HALF_EVEN规范串，展示百分数2位HALF_UP |
| 贡献 | 共享within/structure对称分解，新增entry/退出exit；公式见DD02，ratio单位、残差≤1e-6；非因果、不跨维相加 |

orders/refunds/products/regions/channels按domain/snapshot复合键关联。支付/退款必需时间与维度唯一性坏数据阻断；非关键未知维度保留。raw层检查不被normalized唯一约束取代。全部输入固定生成器/种子/source_row_id/文件hash、导入状态、水位/目录/规则版本；Oracle独立逐订单计算，不能复用被测SQL编译器。

合成默认H=604800秒，business_timezone=UTC，基期2026-09-01至09-08/当前09-08至09-15，as_of=2026-09-23T00:00:00Z。实际snapshot/version/ID字典仍待导入绑定；示例不是已存在业务数据。Scope冻结后不静默改地区、时间、H或域；新地区另建显式任务。
