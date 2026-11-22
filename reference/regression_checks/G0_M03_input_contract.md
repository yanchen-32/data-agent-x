# M03 贡献输入契约核查

2026-11-22（Asia/Shanghai）。核查版本为公开提交 `7d509cd`。**`complete` 和 `truncated` 在当前 M03 本地参考入口均为可选字段。** 现有三个生产者都不输出这两个字段。处理合法参考输出时采用缺省值符合现有契约，本项没有需要补拒绝断言的 Must 缺口。

## DD02 要求与字段归属

DD02 §2 要求总计和单个维度分组使用同一 Scope。§4 要求查询证据绑定完整性，并禁止将截断结果作为完整贡献。完整性是业务前提。生产契约通过外层对象携带证明，字段归属如下。[DD02](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md#execution) · [有效对象 Schema v1.2.1](../../docs/engineering/04_详细设计与实现准备/DataAgentX_对象Schema_v1.2.1.json)

| 对象 | `complete` | `truncated` |
| --- | --- | --- |
| 本地 category/channel/region 聚合结果 | 可选，现有生产者省略 | 可选，现有生产者省略 |
| 生产 `EvidenceEnvelope` 的 query 分支及其 `QueryPayload` | 外层证据必填 | 查询 payload 必填 |
| 生产 `ToolResult` | 必填 | 必填，值为 `true` 时 `complete` 须为 `false` |
| 生产 `AggregateRow` | 行定义无此字段 | 行定义无此字段 |

## 参考层怎样判断是否可分解

三个参考入口复用总体退款率核算。它们在 `ready` 时枚举筛选后候选订单的全部实际分组，输出双窗分组和总计行，并保留 `outcome`、`reasons`、`quality_checks` 和 `metrics`。这个路径的完整性来自同一批候选订单的全量遍历。贡献函数要求上游可比，核对三项成熟与水位检查、单维度身份、双窗总计行与 `metrics` 一致，以及每窗分组 N/U 守恒。只删除正分母分组而保留原总体时，缺行会触发守恒拒绝。[总体参考](../cohort.py) · [类别](../category_cohort.py) · [渠道](../channel_cohort.py) · [地区](../region_cohort.py) · [贡献入口](../contribution.py)

字段省略时，现有入口继续校验聚合结果。显式传入时要求 `complete is True` 和 `truncated is False`，因此 `complete=False`、`truncated=True` 或 `null` 均会拒绝。当前 M03 调用方应直接传入同一 Scope 的一次完整参考聚合。任意外部子集如果同时重算组行和总计，也可能通过守恒，因而调用边界仍须提供可信来源。生产 `analysis.run` 应按 DD02 §3/§4 校验授权证据、同 Scope、必填完整性标志及截断状态。缺失或不满足的证据应在生产边界阻止完整贡献发布，不能转用参考层缺省值。这部分保留在 M06 生产验收。

## 实际核验

在本地用 `PYTHONPATH=src .venv/bin/python -B -` 读取同一份 A3-11 冻结 `input`，依次连接三个参考入口和贡献函数。三次均为 `ready`，顶层均省略两个标志。分别补入单个或两个合法标志，贡献结果保持一致。显式不完整、截断和 `null` 均被拒绝。移除一个组行而保留原总计也均触发 N 守恒拒绝。该次核验退出码为 0。[A3-11 输入](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)

| 参考维度 | 聚合行 | 总体变化 | 残差 |
| --- | ---: | ---: | ---: |
| category | 4 | `5/12` | `0` |
| channel | 6 | `5/12` | `0` |
| region | 4 | `5/12` | `0` |

既有 pytest 套件 **68 项通过**，用时 0.39 秒，退出码为 0。专项已有显式截断、显式不完整和缺组拒绝用例，因此保留现有实现及测试。本记录仅判定两个标志的契约归属。[贡献专项](../../tests/test_reference_contribution.py) · [三维同 Scope 用例](../../tests/test_reference_region_cohort.py)

```bash
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_reference_contribution.py tests/test_reference_region_cohort.py -o addopts= -q -p no:cacheprovider
```
