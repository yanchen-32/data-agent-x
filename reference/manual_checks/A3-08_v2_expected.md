# A3-08 v2 独立推导与开发预期冻结

日期：2026-10-26。仅面向公开合成开发样例，不表示用户签字、生产验收或贡献分解验收。

## 先行推导与冻结边界

本次先提取当前 Fixture 的原始 `input`，逐单核算并保存 [独立预期 JSON](A3-08_v2_expected.json)，再读取现有 `expected`，最后仅把 `input` 传给既有 `calculate_category_reference()`。预期不是由参考函数、生产代码或 SQL 生成。本会话此前接触过目标数值，不能声称首次盲审或用户本人独立复核。原 v1 及 v2 创建台账不覆盖。

现有 `expected` 与本次先行推导一致，因此保持原字节，不为“冻结”重写相同数值。开发数值基线以以下指纹定位；当前 JSON 的 `draft_status` 等创建阶段文字保留，阶段进展以本记录和 `ORACLE.md` 为准。后续输入或业务规则改变须另记版本，不能仅替换 hash 消除差异。

| 对象 | SHA-256 |
| --- | --- |
| 当前 08_category_entry_exit.json（含 input 与 expected） | 79912e4cec13c3ab34482b02c24deeda4ec443caf569839e4ee5572958550e58 |
| 本次先行 A3-08_v2_expected.json | 1b1d63e22f6285cf43f64f8c2db1ce1da39070af6f801840cc47ba596aa159da |
| 规范化 input | 4cf45c7f2404ffd854393e21936fb288981491d98d5cd2e9951bcfedf46f49fb |

input 规范化使用 UTF-8 编码的 `json.dumps(input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))`。冻结不等于已有 v2 专项 pytest 哈希绑定；下方可复现对照命令实际校验这些 hash。

## 逐单核算

Scope 固定为 `domain_a / fixture_category_entry_exit_v2`，地区过滤为空；基期 [2026-09-01,2026-09-08)，当前 [2026-09-08,2026-09-15)，时间均为 UTC 零点。八笔支付有效。产品按完整 `(domain_id,snapshot_id,product_id)` 关联，product_a/b/c 唯一映射 category_a/b/c，不能省略域或快照，也不按标签合并身份。

| 订单 / 来源行 | 窗口 / 类别 | 支付 → 成熟 | 成功退款事件 / 来源行 / 时间 | N / U |
| --- | --- | --- | --- | --- |
| E2-A-B1 / r08v2-row-a-b1 | 基期 / A | 09-02 → 09-09 | 无 | 1 / 0 |
| E2-A-B2 / r08v2-row-a-b2 | 基期 / A | 09-03 → 09-10 | 无 | 1 / 0 |
| E2-B-B1 / r08v2-row-b-b1 | 基期 / B | 09-04 → 09-11 | ER2-B-B1 / r08v2-refund-b-b1 / 09-06 | 1 / 1 |
| E2-B-B2 / r08v2-row-b-b2 | 基期 / B | 09-05 → 09-12 | ER2-B-B2 / r08v2-refund-b-b2 / 09-07 | 1 / 1 |
| E2-A-C1 / r08v2-row-a-c1 | 当前 / A | 09-09 → 09-16 | ER2-A-C1 / r08v2-refund-a-c1 / 09-11 | 1 / 1 |
| E2-C-C1 / r08v2-row-c-c1 | 当前 / C | 09-10 → 09-17 | ER2-C-C1 / r08v2-refund-c-c1 / 09-12 | 1 / 1 |
| E2-C-C2 / r08v2-row-c-c2 | 当前 / C | 09-11 → 09-18 | ER2-C-C2 / r08v2-refund-c-c2 / 09-13 | 1 / 1 |
| E2-C-C3 / r08v2-row-c-c3 | 当前 / C | 09-12 → 09-19 | ER2-C-C3 / r08v2-refund-c-c3 / 09-14 | 1 / 1 |

日期均为2026年，时刻均为00:00Z。每单成熟时刻为支付加604800秒。六笔退款都是支付后2天，落在闭合 [paid_at,paid_at+7天] 且不晚于 as_of；U 按退款订单去重，不按退款事件数累加。基期 A 两单在完整退款输入中均没有退款；其余六单各有一笔有效退款。

最晚成熟为09-19，as_of与退款水位09-23覆盖全部成熟时刻；支付水位09-15覆盖两窗末端。支付、退款和目录复合键唯一，关联完整，两个窗口总计 N 均大于0，故预期 ready，允许发布指标。

## 精确结果、身份与守恒

| 类别 / 身份 | 基期 N / U / 率 | 当前 N / U / 率 |
| --- | --- | --- |
| category_a / shared | 2 / 0 / 0 | 1 / 1 / 1 |
| category_b / exit | 2 / 2 / 1 | 缺席，无行 |
| category_c / entry | 缺席，无行 | 3 / 3 / 1 |
| 总计 | 4 / 2 / 1/2 | 4 / 4 / 1 |

基期有效支付集合为 {E2-A-B1,E2-A-B2,E2-B-B1,E2-B-B2}，退款订单集合为 {E2-B-B1,E2-B-B2}；当前有效支付集合为 {E2-A-C1,E2-C-C1,E2-C-C2,E2-C-C3}，退款订单集合为同一四单。

基期 ΣN=2+2=4、ΣU=0+2=2；当前 ΣN=1+3=4、ΣU=1+3=4。每单唯一归属一个类别，各组互斥且覆盖窗口全部有效支付，退款订单亦只在自己的支付组计数。总体率必须用汇总 U/N，而非相加或简单平均组率。

基期类别集合 S0={A,B}、当前 S1={A,C}：shared=S0∩S1={A}，exit=S0−S1={B}，entry=S1−S0={C}。目录中存在但该窗没有支付的类别不是业务分组；基期 C、当前 B 均不补行，也无退款率，不能写作 0/0 或0。A 的基期率0是实际 N=2/U=0，与缺席不同。生命周期由返回组 ID 集合推导，不冒充参考函数直接返回的字段。

两窗总体率 1/2→1，绝对变化=1−1/2=1/2，即增加50个百分点；相对变化=(1/2)/(1/2)=1，即增加100%。A 的率0→1，绝对变化1；其基期率为0，所以相对变化不可定义。B/C 缺少一窗，不构造跨窗组率差。这里只冻结总体变化，不增加组变化接口字段，更不计算贡献分解。

## 实际参考对照与运行证据

以下命令在先行 JSON 保存后于仓库根目录实际执行，退出码0。对照覆盖六条聚合行、Fraction、窗口总计变化、候选/退款订单集合、来源、守恒、缺席不输出及 input 不被修改；不回写任何预期。

```bash
.venv/bin/python -B - <<'PY'
import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from reference.category_cohort import calculate_category_reference

fixture_path = Path("tests/fixtures/order_boundaries/08_category_entry_exit.json")
manual_path = Path("reference/manual_checks/A3-08_v2_expected.json")
fixture = json.loads(fixture_path.read_text())
manual = json.loads(manual_path.read_text())
assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == manual["source_sha256"]
assert hashlib.sha256(manual_path.read_bytes()).hexdigest() == "1b1d63e22f6285cf43f64f8c2db1ce1da39070af6f801840cc47ba596aa159da"
data = fixture["input"]
canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
assert hashlib.sha256(canonical).hexdigest() == manual["input_sha256"]
before = copy.deepcopy(data)
actual = calculate_category_reference(data)
assert data == before
assert actual["outcome"] == fixture["expected"]["outcome"] == "ready"
assert actual["reasons"] == fixture["expected"]["reasons"] == []
assert all(actual["quality_checks"].values())

def rows_with_fraction(rows, rate_key):
    return [{**{k: v for k, v in row.items() if k != rate_key},
             "rate": Fraction(row[rate_key])} for row in rows]

hand_rows = rows_with_fraction(manual["aggregate_rows"], "rate_fraction")
static_rows = rows_with_fraction(fixture["expected"]["aggregate_rows"], "rate")
assert len(actual["aggregate_rows"]) == len(hand_rows) == 6
assert actual["aggregate_rows"] == hand_rows == static_rows
assert all(isinstance(row["rate"], Fraction) for row in actual["aggregate_rows"])
raw_orders = {row["order_id"]: row for row in data["orders"]}
raw_refunds = {row["refund_id"]: row for row in data["refunds"]}
for row in manual["order_ledger"]:
    order = raw_orders[row["order_id"]]
    assert all(order[key] == row[key] for key in ("source_row_id", "product_id", "paid_at"))
    assert [raw_refunds[rid]["source_row_id"] for rid in row["refund_ids"]] == row["refund_source_rows"]
    assert all(raw_refunds[rid]["order_id"] == row["order_id"] for rid in row["refund_ids"])

present = {}
for index, window in enumerate(("baseline", "current")):
    ledger = [row for row in manual["order_ledger"] if row["window"] == window]
    assert sorted(actual["candidate_order_ids"][window]) == sorted(row["order_id"] for row in ledger)
    total = next(row for row in hand_rows if row["window_index"] == index and row["group_id"] is None)
    groups = [row for row in actual["aggregate_rows"] if row["window_index"] == index and row["group_id"] is not None]
    assert sum(row["paid_orders"] for row in groups) == total["paid_orders"]
    assert sum(row["refunded_orders"] for row in groups) == total["refunded_orders"]
    assert actual["metrics"][window] == {"N": total["paid_orders"], "U": total["refunded_orders"], "rate": total["rate"]}
    static_total = fixture["expected"]["metrics"][window]
    assert actual["metrics"][window] == {**static_total, "rate": Fraction(static_total["rate"])}
    present[window] = {row["group_id"] for row in groups}
    member_lists = []
    refunded_members = []
    for group_id in sorted(present[window]):
        members = [row for row in ledger if row["category_id"] == group_id]
        ids = sorted(row["order_id"] for row in members)
        refund_ids = sorted(row["order_id"] for row in members if row["U"])
        assert actual["group_order_ids"][window][group_id] == ids
        assert actual["group_refunded_order_ids"][window][group_id] == refund_ids
        assert sorted(row["source_row_id"] for row in members) == sorted(fixture["expected"]["group_cohort_source_row_ids"][group_id][window])
        assert sorted(sid for row in members for sid in row["refund_source_rows"]) == sorted(fixture["expected"]["group_refund_source_row_ids"][group_id][window])
        member_lists.extend(ids)
        refunded_members.extend(refund_ids)
    assert len(member_lists) == len(set(member_lists)) == total["paid_orders"]
    assert len(refunded_members) == len(set(refunded_members)) == total["refunded_orders"]
    assert sorted(refunded_members) == sorted(fixture["expected"]["counted_refund_order_ids"][window])
    for absent in manual["absent_group_ids"][window]:
        assert absent not in present[window]
        assert absent not in actual["group_order_ids"][window]
        assert absent not in actual["group_refunded_order_ids"][window]

lifecycle = {"shared": sorted(present["baseline"] & present["current"]),
             "exit": sorted(present["baseline"] - present["current"]),
             "entry": sorted(present["current"] - present["baseline"])}
assert lifecycle == manual["group_lifecycle"] == fixture["expected"]["group_lifecycle"]
for field, hand_field in (("absolute_change_ratio", "absolute_change_fraction"),
                          ("relative_change", "relative_change_fraction")):
    assert actual["metrics"][field] == Fraction(manual[hand_field])
    assert actual["metrics"][field] == Fraction(fixture["expected"]["metrics"][field])
print("PASS: 6 aggregate rows; frozen expected and input-only manual ledger match.")
print("PASS: baseline N=4/U=2/rate=1/2; current N=4/U=4/rate=1.")
print("PASS: absolute change=1/2; relative change=1.")
print("PASS: shared={category_a}; exit={category_b}; entry={category_c}.")
print("PASS: source traceability, disjoint/exhaustive groups, conservation, absent groups omitted.")
print("PASS: fixture/manual hashes verified; input unchanged; no expected values rewritten.")
PY
```

原始输出：

```text
PASS: 6 aggregate rows; frozen expected and input-only manual ledger match.
PASS: baseline N=4/U=2/rate=1/2; current N=4/U=4/rate=1.
PASS: absolute change=1/2; relative change=1.
PASS: shared={category_a}; exit={category_b}; entry={category_c}.
PASS: source traceability, disjoint/exhaustive groups, conservation, absent groups omitted.
PASS: fixture/manual hashes verified; input unchanged; no expected values rewritten.
```

本轮还实际执行已有相关测试：

```bash
.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py tests/test_reference_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
........................................................                 [100%]
56 passed in 0.18s
```

56项包括31项已有分组参考回归（其中A3-08四项绑定v1）、9项总体参考回归和16项静态检查（包含v2）。本轮不新增测试：v2计算覆盖来自上方单独执行的参考对照命令，不能把56项声称为v2专门pytest计算回归。本轮未重跑全量pytest，不复用创建阶段121项作为本次全量证据。

现有 expected 与先行预期无数值差异；未修改参考实现、Fixture或旧测试。结束前对比本轮开始时的SHA-256，九份Fixture、两份参考实现、旧v1手填台账、v2创建台账、两份相关测试及Provider实现/测试共17个文件均未变化；`git diff --check` 实际退出码0。

仍待v2专门pytest回归和用户独立人工验收；不更新路线图、不实现贡献分解、不提交或推送远程仓库。
