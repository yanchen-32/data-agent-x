# A3-11：正式预期冻结与审核记录

日期：2026-11-02。结论：按原始input的前置技术复核完成，现有台账与逐单推导一致；**冻结开发数值Oracle v1**。本阶段不等于用户本人独立验收、渠道参考计算通过、生产approved或G0放行。

## 1. 前置复核、差异与冻结顺序

先仅读取[原始输入](../fixture_drafts/11_single_region_channel_grouping.json)与DD02口径，直接按订单/退款列举并保存[输入复核记录](A3-11_input_review.md)，然后重新读取2026-10-30[台账初稿](A3-11_expected_draft.md)对照，再手工写入[A3-11_expected.json](A3-11_expected.json)。本会话此前已知目标数值，不称首次盲审，不虚构第二审核者。独立性指未借用待测/参考业务代码推导，不代表用户已签字。

| 对照项 | 原初稿与本次逐单复核 | 处理 |
| --- | --- | --- |
| 输入/Scope | 原始11笔支付、6笔退款、两个渠道、西北过滤一致 | input不改，保留原快照ID中的_draft，避免隐式换Scope |
| 六条聚合行/精确率 | 数值一致 | 固定为四条channel行及两条总计行，组按稳定ID比较 |
| 来源与去留 | 7笔西北支付/4笔退款订单计入，4笔东南支付/2笔退款排除 | 将逐单依据整理为显式集合 |
| 总体/组率变化、漏过滤反例 | 分数和算术一致 | 维持原数值；反例单独命名，组率变化不称贡献 |
| 数值或来源差异 | **未发现** | 无数值修订，无修订理由需要补写；原初稿与设计原字节保留 |
| 表示及交付变化 | 原Markdown初稿转JSON静态expected，增加明确的审核/指纹/状态 | 这是结构整理及冻结，不是业务规则改版 |

静态expected先保存，正式[11_single_region_channel_grouping.json](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)随后只机械复制原input及已保存expected；不按原始数据编程生成新业务答案。冻结后才进行静态核验。JSON的rate/变化采用能由Fraction精确解析的字符串，非正式API十进制序列化结果；计数不使用浮点。

## 2. 冻结六条聚合行

| 窗口 | dimension_id / group_id | group_label | N | U | Fraction精确率 |
| --- | --- | --- | --- | --- | --- |
| 基期 | null / null | null | 3 | 1 | 1/3 |
| 基期 | channel / channel_app | 移动应用 | 1 | 1 | 1 |
| 基期 | channel / channel_web | 网页 | 2 | 0 | 0 |
| 当前 | null / null | null | 4 | 3 | 3/4 |
| 当前 | channel / channel_app | 移动应用 | 3 | 2 | 2/3 |
| 当前 | channel / channel_web | 网页 | 1 | 1 | 1 |

基期ΣN=1+2=3、ΣU=1+0=1；当前ΣN=3+1=4、ΣU=2+1=3。两个渠道在每窗支付/退款集合互斥且并集等于同Scope总计。总体绝对变化5/12 ratio，相对变化5/4；网页率0→1，组相对变化null；移动应用1→2/3，组相对变化−1/3。这不是贡献分解。

固定expected保存candidate_order_ids、cohort_source_row_ids、counted_refund_order_ids、合格退款事件与来源、每组支付/退款订单及来源、被地区排除的四单/两事件来源，以及六条目录来源。详细逐单决定见前置复核记录，全部事实均可追溯至原input；这些是本地台账字段，不假称现有参考函数已返回全部字段。

漏过滤反例维持全地区2/5→2/3、绝对变化4/15、相对变化2/3及每渠道计数；额外支付/退款来源分窗列出。单侧过滤诊断为只过滤分母2/3→1、只过滤分子1/5→1/2；两者不是有效Scope结果，也不是已执行的业务控制测试。

## 3. 冻结指纹

| 绑定对象 | SHA-256 |
| --- | --- |
| 原始草案完整文件 | bd522d87d50d59d126836d5b05a979d75ddae6e8da3fcd3716c7552e53596205 |
| 原始台账初稿 | 0a190a957ac70afab40d68bafd910c3003dfee944227c48efc549c4316dac2b3 |
| input（原始与正式均相同） | 459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 |
| 前置输入复核Markdown | 28498ead0ea560d1e60de75b99feb14a22f804e9735b94155d2a784e0fbe1427 |
| 独立expected记录完整JSON | c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e |
| expected（正式与独立记录均相同） | 27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91 |
| 正式Fixture完整文件 | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |

input及expected规范化均用UTF-8编码的json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，不含末尾换行；完整文件指纹直接对磁盘字节计算。快照名保留_draft是原输入身份，不表示生产批准；metric_version=null仍待批准manifest绑定。以上为开发Oracle v1，不是生产dataset_manifest。

## 4. 冻结后的可复现静态核验

以下命令只读取已经保存的预期，核对其算术、集合、输入关联及指纹，不生成或写回expected。含按原始输入检查既定候选集合及退款合法性；它不提供通用渠道计算接口，不导入reference或生产业务代码，不能取代后续独立渠道参考计算回归。仓库根目录运行：

```bash
python3 -B - <<'PY'
import hashlib, json
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

fixture_path = Path("tests/fixtures/order_boundaries/11_single_region_channel_grouping.json")
manual_path = Path("reference/manual_checks/A3-11_expected.json")
fixture = json.loads(fixture_path.read_text())
manual = json.loads(manual_path.read_text())
draft_path = Path(manual["source_draft"])
draft = json.loads(draft_path.read_text())
canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(fixture_path) == "d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8"
assert sha(manual_path) == "c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e"
assert sha(draft_path) == manual["source_draft_sha256"]
assert sha(Path(manual["source_ledger"])) == manual["source_ledger_sha256"]
assert fixture["input"] == draft["input"]
data, expected = fixture["input"], fixture["expected"]
assert expected == manual["expected"]
assert hashlib.sha256(canonical(data)).hexdigest() == manual["input_sha256"] == fixture["input_sha256"]
assert hashlib.sha256(canonical(expected)).hexdigest() == "27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91"
context = data["context"]
instant = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
key = lambda row, field: (row["domain_id"], row["snapshot_id"], row[field])
scope = context["domain_id"], context["snapshot_id"]
orders = {row["order_id"]: row for row in data["orders"]}
refunds = {row["refund_id"]: row for row in data["refunds"]}
assert len(orders) == len(data["orders"]) == 11
assert len(refunds) == len(data["refunds"]) == 6
all_rows = data["orders"] + data["refunds"] + [row for rows in data["dimensions"].values() for row in rows]
assert len({row["source_row_id"] for row in all_rows}) == len(all_rows) == 23
assert all((row["domain_id"], row["snapshot_id"]) == scope for row in all_rows)
catalogs = {}
for name, field in (("products", "product_id"), ("categories", "category_id"), ("regions", "region_id"), ("channels", "channel_id")):
    rows = data["dimensions"][name]
    catalogs[name] = {key(row, field): row for row in rows}
    assert len(catalogs[name]) == len(rows)
    assert set(expected["catalog_source_row_ids"][name]) == {row["source_row_id"] for row in rows}
for order in orders.values():
    assert order["is_payment_valid"] is True
    for name, field in (("products", "product_id"), ("regions", "region_id"), ("channels", "channel_id")):
        assert key(order, field) in catalogs[name]
    product = catalogs["products"][key(order, "product_id")]
    assert key(product, "category_id") in catalogs["categories"]
    matures = instant(order["paid_at"]) + timedelta(seconds=context["horizon_seconds"])
    assert matures <= instant(context["as_of"])
    assert matures <= instant(context["watermark"]["refunds_through"])
for refund in refunds.values():
    order = orders[refund["order_id"]]
    paid = instant(order["paid_at"])
    assert refund["status"] == "success"
    assert paid <= instant(refund["refund_at"]) <= paid + timedelta(seconds=context["horizon_seconds"])
    assert instant(refund["refund_at"]) <= instant(context["as_of"])
assert expected["applied_filters"] == context["filters"] == {"region_ids": ["region_northwest"]}
assert expected["outcome"] == "ready" and expected["reasons"] == []
assert len(expected["aggregate_rows"]) == 6
identities = [(row["window_index"], row["dimension_id"], row["group_id"]) for row in expected["aggregate_rows"]]
assert len(set(identities)) == 6
for index, window in enumerate(("baseline", "current")):
    bounds = context["windows"][window]
    assert instant(context["watermark"]["payments_through"]) >= instant(bounds["end"])
    members = set(expected["candidate_order_ids"][window])
    assert members == {oid for oid, order in orders.items() if order["region_id"] == "region_northwest" and instant(bounds["start"]) <= instant(order["paid_at"]) < instant(bounds["end"])}
    assert {orders[oid]["source_row_id"] for oid in members} == set(expected["cohort_source_row_ids"][window])
    refunded = set(expected["counted_refund_order_ids"][window])
    event_ids = set(expected["qualifying_refund_event_ids"][window])
    assert refunded <= members
    assert {refunds[rid]["order_id"] for rid in event_ids} == refunded
    assert {refunds[rid]["source_row_id"] for rid in event_ids} == set(expected["qualifying_refund_source_row_ids"][window])
    assert len(event_ids) == expected["qualifying_refund_event_counts"][window]
    groups = expected["group_order_ids"][window]
    returned = [row for row in expected["aggregate_rows"] if row["window_index"] == index]
    total, = [row for row in returned if row["dimension_id"] is None]
    rows = {row["group_id"]: row for row in returned if row["dimension_id"] == "channel"}
    assert set(groups) == set(rows) == {"channel_web", "channel_app"}
    assert total["group_id"] is None and total["group_label"] is None
    assert set(groups["channel_web"]).isdisjoint(groups["channel_app"])
    assert set(groups["channel_web"]) | set(groups["channel_app"]) == members
    all_refunded = set()
    for gid, ids in groups.items():
        group_members = set(ids)
        group_refunded = set(expected["group_refunded_order_ids"][window][gid])
        row = rows[gid]
        assert len(ids) == len(group_members)
        assert all(orders[oid]["channel_id"] == gid for oid in group_members)
        assert {orders[oid]["source_row_id"] for oid in ids} == set(expected["group_cohort_source_row_ids"][gid][window])
        assert group_refunded == group_members & refunded
        assert not all_refunded & group_refunded
        all_refunded |= group_refunded
        sources = {refunds[rid]["source_row_id"] for rid in event_ids if refunds[rid]["order_id"] in group_members}
        assert sources == set(expected["group_refund_source_row_ids"][gid][window])
        assert (row["paid_orders"], row["refunded_orders"]) == (len(ids), len(group_refunded))
        assert Fraction(row["rate"]) == Fraction(row["refunded_orders"], row["paid_orders"])
        assert row["group_label"] == catalogs["channels"][(*scope, gid)]["label"]
    assert all_refunded == refunded
    metric = expected["metrics"][window]
    assert (total["paid_orders"], total["refunded_orders"]) == (metric["N"], metric["U"]) == (len(members), len(refunded))
    assert sum(row["paid_orders"] for row in rows.values()) == total["paid_orders"]
    assert sum(row["refunded_orders"] for row in rows.values()) == total["refunded_orders"]
    assert Fraction(total["rate"]) == Fraction(metric["rate"]) == Fraction(metric["U"], metric["N"])
    counter = expected["unfiltered_counterexample"]
    extra = set(counter["additional_order_ids"][window])
    assert not extra & members
    assert all(orders[oid]["region_id"] == "region_southeast" and instant(bounds["start"]) <= instant(orders[oid]["paid_at"]) < instant(bounds["end"]) for oid in extra)
    assert {orders[oid]["source_row_id"] for oid in extra} == set(counter["additional_order_source_row_ids"][window])
    extra_events = set(counter["additional_refund_event_ids"][window])
    assert all(refunds[rid]["order_id"] in extra for rid in extra_events)
    assert {refunds[rid]["source_row_id"] for rid in extra_events} == set(counter["additional_refund_source_row_ids"][window])
    assert (counter[window]["N"], counter[window]["U"]) == (len(members | extra), len(refunded | {refunds[rid]["order_id"] for rid in extra_events}))
    counter_groups = counter["group_metrics"][window]
    for gid, row in counter_groups.items():
        assert row["N"] == len(set(groups[gid]) | {oid for oid in extra if orders[oid]["channel_id"] == gid})
        assert row["U"] == len(set(expected["group_refunded_order_ids"][window][gid]) | {refunds[rid]["order_id"] for rid in extra_events if orders[refunds[rid]["order_id"]]["channel_id"] == gid})
        assert Fraction(row["rate_fraction"]) == Fraction(row["U"], row["N"])
    assert sum(row["N"] for row in counter_groups.values()) == counter[window]["N"]
    assert sum(row["U"] for row in counter_groups.values()) == counter[window]["U"]
    assert Fraction(counter[window]["rate_fraction"]) == Fraction(counter[window]["U"], counter[window]["N"])
for values, rate, change, relative in ((expected["metrics"], "rate", "absolute_change_ratio", "relative_change"), (expected["unfiltered_counterexample"], "rate_fraction", "absolute_change_fraction", "relative_change_fraction")):
    before = Fraction(values["baseline"][rate])
    delta = Fraction(values["current"][rate]) - before
    assert Fraction(values[change]) == delta
    assert Fraction(values[relative]) == delta / before
for gid, diag in expected["group_rate_change_diagnostics"].items():
    before, after = [Fraction(next(row["rate"] for row in expected["aggregate_rows"] if row["window_index"] == index and row["group_id"] == gid)) for index in (0, 1)]
    assert Fraction(diag["absolute_change_ratio"]) == after - before
    assert diag["relative_change"] is None if before == 0 else Fraction(diag["relative_change"]) == (after - before) / before
excluded = set(expected["excluded_order_ids"])
assert excluded == set(orders) - set().union(*[set(ids) for ids in expected["candidate_order_ids"].values()])
assert {orders[oid]["source_row_id"] for oid in excluded} == set(expected["excluded_by_region_source_row_ids"])
excluded_events = set(expected["excluded_by_region_refund_event_ids"])
assert all(refunds[rid]["order_id"] in excluded for rid in excluded_events)
assert {refunds[rid]["source_row_id"] for rid in excluded_events} == set(expected["excluded_by_region_refund_source_row_ids"])
assert excluded_events | set().union(*[set(ids) for ids in expected["qualifying_refund_event_ids"].values()]) == set(refunds)
for name, values in expected["quality_checks"].items():
    assert values is True if name.endswith("_covered") or name == "all_orders_mature" else values == 0
for mode in ("only_denominator_filtered", "only_numerator_filtered"):
    values = expected["one_sided_filter_counterexamples"][mode]
    for window in ("baseline", "current"):
        assert Fraction(values[window]["rate"]) == Fraction(values[window]["U"], values[window]["N"])
print("A3-11冻结静态核对完成：六条行、精确分数、来源/地区排除、分组互斥穷尽、N/U守恒、反例算术及指纹一致。")
print("未导入参考或生产业务代码，未生成或回写expected；渠道实际计算回归仍待实现。")
PY
```

实际运行于本地开发工作树，Python 3.10.12，最终退出码0：

```text
A3-11冻结静态核对完成：六条行、精确分数、来源/地区排除、分组互斥穷尽、N/U守恒、反例算术及指纹一致。
未导入参考或生产业务代码，未生成或回写expected；渠道实际计算回归仍待实现。
```

保留执行差异：首次运行时，静态核验脚本误把one_sided_filter_counterexamples里的note说明文本作为诊断对象遍历，在该检查处报TypeError、退出1。随后只修正脚本为显式枚举两个诊断对象，上述命令再次执行退出0；Fixture、独立expected及原台账数值/来源/指纹均未变。这是核验脚本错误，不是草稿数值错误，也不是渠道业务实现红灯。

## 5. 现有静态pytest及验收状态

只在tests/test_boundary_fixtures.py的既有FIXTURE_FILES中登记新文件，复用现有完整性/静态算术/来源检查，没有新增渠道求值实现或计算测试。实际命令：

```bash
.venv/bin/python -B -m pytest tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
.....................                                                    [100%]
21 passed in 0.13s
```

退出码0，包含原20项静态检查与新增一项A3-11通用完整性检查。六行与分组集合的额外核验见上一节命令；不把仅通用参数化通过说成渠道参考结果已对照。

- 已完成：按原始输入技术复核、与初稿对照（无数值或来源差异）、开发Oracle v1冻结、静态算术/来源/守恒/指纹检查及上述21项静态pytest。
- 未完成：独立渠道参考计算、固定实际计算回归、生产SQL/授权/DQ/贡献/正式序列化、用户本人独立验收及G0放行。
- 本轮未跑全量pytest、类别/总体参考测试、公开工作树pytest或CI；21项为本地开发工作树的实际结果。未提交或推送。
- 原始input、原草案、台账初稿、01～10及08v1、两个参考计算器保持不变；旧G0矩阵/清单仍为十主例审查快照，不以数量增为11关闭其Must缺口。后续修改业务输入或预期应另记版本与理由，不回填待测输出覆盖v1。
