"""A3-11 C01～C07：固定结果、来源、关联、门槛、退款及输入隔离，不生成预期。"""

import copy
import hashlib
import json
from collections.abc import Iterator
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

import pytest

from reference.channel_cohort import calculate_channel_reference
from reference.cohort import calculate_reference


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/order_boundaries/11_single_region_channel_grouping.json"
MANUAL_PATH = ROOT / "reference/manual_checks/A3-11_expected.json"
FIXTURE_SHA256 = "d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8"
MANUAL_SHA256 = "c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e"
INPUT_SHA256 = "459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257"
EXPECTED_SHA256 = "27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91"
WINDOWS = ("baseline", "current")


def _canonical_sha256(value: dict) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@pytest.fixture
def channel_fixture() -> Iterator[tuple[dict, dict]]:
    """逐项重新加载冻结数据；包括失败测试在内，结束后仍检查内存和磁盘不变。"""
    fixture_bytes, manual_bytes = FIXTURE_PATH.read_bytes(), MANUAL_PATH.read_bytes()
    assert hashlib.sha256(fixture_bytes).hexdigest() == FIXTURE_SHA256
    assert hashlib.sha256(manual_bytes).hexdigest() == MANUAL_SHA256
    fixture, manual = json.loads(fixture_bytes), json.loads(manual_bytes)
    assert fixture["expected"] == manual["expected"]
    assert _canonical_sha256(fixture["input"]) == INPUT_SHA256 == manual["input_sha256"]
    assert _canonical_sha256(fixture["expected"]) == EXPECTED_SHA256
    original = copy.deepcopy((fixture, manual))
    try:
        yield fixture, manual["expected"]
    finally:
        assert (fixture, manual) == original
        assert FIXTURE_PATH.read_bytes() == fixture_bytes
        assert MANUAL_PATH.read_bytes() == manual_bytes


class _InputOnly(dict):
    """允许的调用边界是input，禁止通过同名字段寻找静态答案。"""

    def __getitem__(self, key):
        assert key != "expected", "渠道计算不得读取expected"
        return super().__getitem__(key)

    def get(self, key, default=None):
        assert key != "expected", "渠道计算不得读取expected"
        return super().get(key, default)

    def __contains__(self, key):
        assert key != "expected", "渠道计算不得探测expected"
        return super().__contains__(key)


def _rows_by_identity(result: dict) -> dict:
    rows = result["aggregate_rows"]
    assert len(rows) == 6
    identities = [(row["window_index"], row["dimension_id"], row["group_id"]) for row in rows]
    assert len(set(identities)) == len(identities)
    assert sum(row["dimension_id"] == "channel" for row in rows) == 4
    assert sum(row["dimension_id"] is None for row in rows) == 2
    return dict(zip(identities, rows))


def _key(row: dict, field: str) -> tuple[str, str, str]:
    return row["domain_id"], row["snapshot_id"], row[field]


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_channel_reference_a3_11_matches_six_frozen_rows_and_metrics(channel_fixture) -> None:
    fixture, expected = channel_fixture
    data = _InputOnly(fixture["input"])
    actual = calculate_channel_reference(data)

    # 只解码人工先行冻结的字符串，不从actual生成答案。
    expected_rows = [{**row, "rate": Fraction(row["rate"])} for row in expected["aggregate_rows"]]
    assert actual["outcome"] == expected["outcome"] == "ready"
    assert actual["reasons"] == expected["reasons"] == []
    assert _rows_by_identity(actual) == _rows_by_identity({"aggregate_rows": expected_rows})
    for row in actual["aggregate_rows"]:
        assert type(row["paid_orders"]) is int and type(row["refunded_orders"]) is int
        assert isinstance(row["rate"], Fraction)

    for window in WINDOWS:
        values = expected["metrics"][window]
        assert actual["metrics"][window] == {**values, "rate": Fraction(values["rate"])}
        assert isinstance(actual["metrics"][window]["rate"], Fraction)
        assert set(actual["candidate_order_ids"][window]) == set(expected["candidate_order_ids"][window])
    for field in ("absolute_change_ratio", "relative_change"):
        assert actual["metrics"][field] == Fraction(expected["metrics"][field])
        assert isinstance(actual["metrics"][field], Fraction)

    # 仅验证原总体字段没有改变；上述冻结比较才是独立数值验收。
    for field, value in calculate_reference(data).items():
        assert actual[field] == value
    assert set(actual["quality_checks"]) == {
        "all_orders_mature", "payments_watermark_covered", "refunds_watermark_covered",
    }


@pytest.mark.parametrize("window", WINDOWS, ids=WINDOWS)
def test_channel_reference_a3_11_sources_scope_and_conservation(channel_fixture, window: str) -> None:
    fixture, expected = channel_fixture
    data = fixture["input"]
    actual = calculate_channel_reference(_InputOnly(data))
    rows = _rows_by_identity(actual)
    index = WINDOWS.index(window)
    total = rows[index, None, None]
    assert total["group_label"] is None
    scope = data["context"]["domain_id"], data["context"]["snapshot_id"]
    orders = {_key(row, "order_id"): row for row in data["orders"]}
    assert len(orders) == len(data["orders"])
    catalogs = {}
    for name, field in (("products", "product_id"), ("categories", "category_id"),
                        ("regions", "region_id"), ("channels", "channel_id")):
        entries = data["dimensions"][name]
        catalogs[name] = {_key(row, field): row for row in entries}
        assert len(catalogs[name]) == len(entries)
        assert all(key[:2] == scope for key in catalogs[name])
        assert {row["source_row_id"] for row in entries} == set(expected["catalog_source_row_ids"][name])

    groups = actual["group_order_ids"][window]
    assert set(groups) == set(actual["group_refunded_order_ids"][window]) == {"channel_app", "channel_web"}
    start = _instant(data["context"]["windows"][window]["start"])
    end = _instant(data["context"]["windows"][window]["end"])
    horizon = timedelta(seconds=data["context"]["horizon_seconds"])
    as_of = _instant(data["context"]["as_of"])
    assert data["context"]["filters"] == expected["applied_filters"] == {"region_ids": ["region_northwest"]}
    paid_ids, refunded_ids, paid_sources, refund_sources, event_ids = [], [], set(), set(), set()
    group_rows = []
    for gid, members in groups.items():
        row = rows[index, "channel", gid]
        group_rows.append(row)
        returned_refunds = actual["group_refunded_order_ids"][window][gid]
        assert len(members) == len(set(members)) > 0
        assert len(returned_refunds) == len(set(returned_refunds))
        assert set(members) == set(expected["group_order_ids"][window][gid])
        assert set(returned_refunds) == set(expected["group_refunded_order_ids"][window][gid])
        assert set(returned_refunds) <= set(members)
        member_keys = {(*scope, oid) for oid in members}
        source_ids = {orders[key]["source_row_id"] for key in member_keys}
        assert source_ids == set(expected["group_cohort_source_row_ids"][gid][window])
        assert row["group_label"] == catalogs["channels"][(*scope, gid)]["label"]
        for key in member_keys:
            order = orders[key]
            assert order["channel_id"] == gid and order["region_id"] == "region_northwest"
            assert order["is_payment_valid"] is True
            assert start <= _instant(order["paid_at"]) < end
            assert _key(order, "product_id") in catalogs["products"]
            assert _key(order, "region_id") in catalogs["regions"]
            assert _key(order, "channel_id") in catalogs["channels"]

        # A3-11每个已退款订单只有一个事件；这里查回来源，不重新实现通用Oracle。
        refunded_keys = {(*scope, oid) for oid in returned_refunds}
        events = [refund for refund in data["refunds"] if _key(refund, "order_id") in refunded_keys]
        assert len(events) == len(refunded_keys)
        assert {_key(refund, "order_id") for refund in events} == refunded_keys
        sources = {refund["source_row_id"] for refund in events}
        assert sources == set(expected["group_refund_source_row_ids"][gid][window])
        for refund in events:
            order = orders[_key(refund, "order_id")]
            paid = _instant(order["paid_at"])
            assert refund["status"] == "success"
            assert paid <= _instant(refund["refund_at"]) <= paid + horizon
            assert _instant(refund["refund_at"]) <= as_of
        paid_ids.extend(members)
        refunded_ids.extend(returned_refunds)
        paid_sources |= source_ids
        refund_sources |= sources
        event_ids |= {refund["refund_id"] for refund in events}
        assert (row["paid_orders"], row["refunded_orders"]) == (len(members), len(returned_refunds))
        assert row["rate"] == Fraction(len(returned_refunds), len(members))
        assert isinstance(row["rate"], Fraction)

    # 不只检查U<=N：同时证明同Scope、来源集合、互斥穷尽和计数守恒。
    assert len(paid_ids) == len(set(paid_ids))
    assert len(refunded_ids) == len(set(refunded_ids))
    assert set(paid_ids) == set(actual["candidate_order_ids"][window]) == set(expected["candidate_order_ids"][window])
    assert set(refunded_ids) == set(expected["counted_refund_order_ids"][window])
    assert paid_sources == set(expected["cohort_source_row_ids"][window])
    assert refund_sources == set(expected["qualifying_refund_source_row_ids"][window])
    assert event_ids == set(expected["qualifying_refund_event_ids"][window])
    assert len(event_ids) == expected["qualifying_refund_event_counts"][window]
    values = expected["metrics"][window]
    assert sum(row["paid_orders"] for row in group_rows) == total["paid_orders"] == values["N"] == len(paid_ids)
    assert sum(row["refunded_orders"] for row in group_rows) == total["refunded_orders"] == values["U"] == len(refunded_ids)
    assert total["rate"] == Fraction(values["rate"]) == Fraction(total["refunded_orders"], total["paid_orders"])
    assert isinstance(total["rate"], Fraction)
    assert (total["paid_orders"], total["refunded_orders"], total["rate"]) == (
        actual["metrics"][window]["N"], actual["metrics"][window]["U"], actual["metrics"][window]["rate"],
    )
    assert set(paid_ids).isdisjoint(expected["excluded_order_ids"])
    assert paid_sources.isdisjoint(expected["excluded_by_region_source_row_ids"])
    assert event_ids.isdisjoint(expected["excluded_by_region_refund_event_ids"])
    assert refund_sources.isdisjoint(expected["excluded_by_region_refund_source_row_ids"])
    for mode in ("only_denominator_filtered", "only_numerator_filtered"):
        wrong = expected["one_sided_filter_counterexamples"][mode][window]
        assert (total["paid_orders"], total["refunded_orders"]) != (wrong["N"], wrong["U"])
        assert total["rate"] != Fraction(wrong["rate"])


def test_channel_reference_a3_11_all_regions_matches_frozen_counterexample(channel_fixture) -> None:
    """另设假定已授权的全地区合成Scope；冻结西北Scope前后均须正确。"""
    fixture, expected = channel_fixture
    west_data = _InputOnly(fixture["input"])
    west_before = copy.deepcopy(dict(west_data))
    west = calculate_channel_reference(west_data)
    control_input = copy.deepcopy(fixture["input"])
    control_input["context"]["filters"]["region_ids"] = []
    control_before = copy.deepcopy(control_input)
    control_data = _InputOnly(control_input)
    control = calculate_channel_reference(control_data)
    west_again = calculate_channel_reference(west_data)
    assert dict(west_data) == west_before
    assert control_input == dict(control_data) == control_before
    assert fixture["input"]["context"]["filters"] == {"region_ids": ["region_northwest"]}
    assert control_data["context"]["filters"] == {"region_ids": []}
    assert west == west_again
    assert west["outcome"] == control["outcome"] == "ready"
    assert west["reasons"] == control["reasons"] == []

    frozen_rows = [{**row, "rate": Fraction(row["rate"])} for row in expected["aggregate_rows"]]
    west_rows, all_rows = _rows_by_identity(west), _rows_by_identity(control)
    assert west_rows == _rows_by_identity({"aggregate_rows": frozen_rows})
    # 全地区若被误用作西北输出，既有六行比较必须能识别；不编写错误算法。
    assert all_rows != west_rows
    counter = expected["unfiltered_counterexample"]
    scope = control_input["context"]["domain_id"], control_input["context"]["snapshot_id"]
    orders = {_key(row, "order_id"): row for row in control_input["orders"]}
    refunds = {_key(row, "refund_id"): row for row in control_input["refunds"]}
    assert len(orders) == len(control_input["orders"])
    assert len(refunds) == len(control_input["refunds"])
    horizon = timedelta(seconds=control_input["context"]["horizon_seconds"])
    as_of = _instant(control_input["context"]["as_of"])

    for index, window in enumerate(WINDOWS):
        extra_ids = set(counter["additional_order_ids"][window])
        extra_events = set(counter["additional_refund_event_ids"][window])
        extra_refunded = {refunds[(*scope, rid)]["order_id"] for rid in extra_events}
        assert extra_ids.isdisjoint(expected["candidate_order_ids"][window])
        assert extra_refunded <= extra_ids
        assert {orders[(*scope, oid)]["source_row_id"] for oid in extra_ids} == set(
            counter["additional_order_source_row_ids"][window]
        )
        assert {refunds[(*scope, rid)]["source_row_id"] for rid in extra_events} == set(
            counter["additional_refund_source_row_ids"][window]
        )
        assert all(orders[(*scope, oid)]["region_id"] == "region_southeast" for oid in extra_ids)
        start = _instant(control_input["context"]["windows"][window]["start"])
        end = _instant(control_input["context"]["windows"][window]["end"])
        added_paid, added_refunded, added_sources, added_refund_sources, added_events = set(), set(), set(), set(), set()
        assert set(control["group_order_ids"][window]) == set(counter["group_metrics"][window])
        assert set(control["group_refunded_order_ids"][window]) == set(counter["group_metrics"][window])

        for gid, values in counter["group_metrics"][window].items():
            members = set(control["group_order_ids"][window][gid])
            returned_refunds = set(control["group_refunded_order_ids"][window][gid])
            west_members = set(expected["group_order_ids"][window][gid])
            west_refunded = set(expected["group_refunded_order_ids"][window][gid])
            new_members = {oid for oid in extra_ids if orders[(*scope, oid)]["channel_id"] == gid}
            new_refunded = {oid for oid in extra_refunded if orders[(*scope, oid)]["channel_id"] == gid}
            assert set(west["group_order_ids"][window][gid]) == west_members
            assert set(west["group_refunded_order_ids"][window][gid]) == west_refunded
            assert members == west_members | new_members
            assert returned_refunds == west_refunded | new_refunded
            assert members - west_members == new_members
            assert returned_refunds - west_refunded == new_refunded
            for oid in members:
                order = orders[(*scope, oid)]
                assert order["channel_id"] == gid and order["is_payment_valid"] is True
                assert start <= _instant(order["paid_at"]) < end
            member_sources = {orders[(*scope, oid)]["source_row_id"] for oid in members}
            assert member_sources == set(expected["group_cohort_source_row_ids"][gid][window]) | {
                orders[(*scope, oid)]["source_row_id"] for oid in new_members
            }
            # 固定例每个退款订单一笔事件，按实际订单台账查回事件及原始来源。
            refunded_keys = {(*scope, oid) for oid in returned_refunds}
            events = [row for row in refunds.values() if _key(row, "order_id") in refunded_keys]
            assert len(events) == len(returned_refunds)
            assert {row["order_id"] for row in events} == returned_refunds
            for event in events:
                paid_at = _instant(orders[_key(event, "order_id")]["paid_at"])
                assert event["status"] == "success"
                assert paid_at <= _instant(event["refund_at"]) <= paid_at + horizon
                assert _instant(event["refund_at"]) <= as_of
            new_events = {row["refund_id"] for row in events} & extra_events
            event_sources = {row["source_row_id"] for row in events}
            assert event_sources == set(expected["group_refund_source_row_ids"][gid][window]) | {
                refunds[(*scope, rid)]["source_row_id"] for rid in new_events
            }
            row = all_rows[index, "channel", gid]
            assert (row["paid_orders"], row["refunded_orders"], row["rate"]) == (
                values["N"], values["U"], Fraction(values["rate_fraction"]),
            )
            assert isinstance(row["rate"], Fraction)
            assert row["group_label"] == west_rows[index, "channel", gid]["group_label"]
            added_paid |= new_members
            added_refunded |= new_refunded
            added_sources |= member_sources - set(expected["group_cohort_source_row_ids"][gid][window])
            added_refund_sources |= event_sources - set(expected["group_refund_source_row_ids"][gid][window])
            added_events |= new_events

        assert added_paid == extra_ids
        assert added_refunded == extra_refunded
        assert added_sources == set(counter["additional_order_source_row_ids"][window])
        assert added_refund_sources == set(counter["additional_refund_source_row_ids"][window])
        assert added_events == extra_events
        assert set(control["candidate_order_ids"][window]) == set(expected["candidate_order_ids"][window]) | extra_ids
        for result, indexed, values, rate_key in (
            (west, west_rows, expected["metrics"][window], "rate"),
            (control, all_rows, counter[window], "rate_fraction"),
        ):
            total = indexed[index, None, None]
            assert total["group_label"] is None
            paid, refunded = [], []
            for gid, ids in result["group_order_ids"][window].items():
                rids = result["group_refunded_order_ids"][window][gid]
                assert set(rids) <= set(ids)
                row = indexed[index, "channel", gid]
                assert (row["paid_orders"], row["refunded_orders"]) == (len(ids), len(rids))
                assert row["rate"] == Fraction(len(rids), len(ids))
                paid.extend(ids)
                refunded.extend(rids)
            assert len(paid) == len(set(paid)) == total["paid_orders"]
            assert len(refunded) == len(set(refunded)) == total["refunded_orders"]
            assert set(paid) == set(result["candidate_order_ids"][window])
            assert sum(indexed[index, "channel", gid]["paid_orders"] for gid in result["group_order_ids"][window]) == total["paid_orders"]
            assert sum(indexed[index, "channel", gid]["refunded_orders"] for gid in result["group_order_ids"][window]) == total["refunded_orders"]
            assert (total["paid_orders"], total["refunded_orders"], total["rate"]) == (
                values["N"], values["U"], Fraction(values[rate_key]),
            )
            assert result["metrics"][window] == {"N": values["N"], "U": values["U"], "rate": Fraction(values[rate_key])}
            assert isinstance(total["rate"], Fraction)
        assert control["metrics"][window] != west["metrics"][window]

    for field, counter_field in (("absolute_change_ratio", "absolute_change_fraction"),
                                 ("relative_change", "relative_change_fraction")):
        assert west["metrics"][field] == Fraction(expected["metrics"][field])
        assert control["metrics"][field] == Fraction(counter[counter_field])
        assert isinstance(control["metrics"][field], Fraction)
        assert control["metrics"][field] != west["metrics"][field]


@pytest.mark.parametrize(
    ("catalog", "id_field"),
    (("products", "product_id"), ("regions", "region_id"), ("channels", "channel_id")),
    ids=("products", "regions", "channels"),
)
def test_channel_reference_c04_rejects_duplicate_catalog_keys(channel_fixture, catalog, id_field) -> None:
    fixture, _ = channel_fixture
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    duplicate = copy.deepcopy(data["dimensions"][catalog][0])
    duplicate["source_row_id"] += "-c04-duplicate"
    data["dimensions"][catalog].append(duplicate)
    before = copy.deepcopy(dict(data))

    with pytest.raises(ValueError, match="重复目录主键") as error:
        calculate_channel_reference(data)

    assert repr(_key(duplicate, id_field)) in str(error.value)
    assert dict(data) == before


@pytest.mark.parametrize(
    ("catalog", "id_field"),
    (("products", "product_id"), ("regions", "region_id"), ("channels", "channel_id")),
    ids=("products", "regions", "channels"),
)
@pytest.mark.parametrize("scope_field", ("domain_id", "snapshot_id"))
def test_channel_reference_c04_rejects_foreign_catalog_scope(
    channel_fixture, catalog, id_field, scope_field,
) -> None:
    fixture, _ = channel_fixture
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    local = data["dimensions"][catalog][0]
    foreign = copy.deepcopy(local)
    foreign[scope_field] = "foreign_" + scope_field
    foreign["source_row_id"] += "-c04-foreign"
    # 保留合法本地行，混入一个局部ID相同而域/快照不同的目录行。
    assert foreign[id_field] == local[id_field]
    assert _key(foreign, id_field) != _key(local, id_field)
    data["dimensions"][catalog].append(foreign)
    before = copy.deepcopy(dict(data))

    with pytest.raises(ValueError, match="目录域或快照") as error:
        calculate_channel_reference(data)

    assert id_field in str(error.value)
    assert dict(data) == before


@pytest.mark.parametrize("comparison", ("ready", "immature"))
@pytest.mark.parametrize(
    ("target_order_id", "region_id"),
    (("K11-N-C-A3", "region_northwest"), ("K11-S-C-A1", "region_southeast")),
    ids=("in-scope-northwest", "excluded-southeast"),
)
def test_channel_reference_c04_rejects_missing_product_before_comparison_gate(
    channel_fixture, target_order_id, region_id, comparison,
) -> None:
    fixture, _ = channel_fixture
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    target = next(row for row in data["orders"] if row["order_id"] == target_order_id)
    assert target["region_id"] == region_id
    # 只破坏目标订单的产品关联，不删除所有订单共用的合法产品。
    target["product_id"] = "product_missing_c04"
    product_key = _key(target, "product_id")
    products = {_key(row, "product_id") for row in data["dimensions"]["products"]}
    assert product_key not in products
    assert all(_key(row, "product_id") in products for row in data["orders"] if row is not target)
    if comparison == "immature":
        data["context"]["as_of"] = "2026-09-18T23:59:59.999999Z"
    before = copy.deepcopy(dict(data))

    overall = calculate_reference(data)
    assert overall["outcome"] == ("ready" if comparison == "ready" else "insufficient_evidence")
    assert overall["reasons"] == ([] if comparison == "ready" else ["观察期未成熟"])
    assert overall["quality_checks"] == {
        "all_orders_mature": comparison == "ready",
        "payments_watermark_covered": True,
        "refunds_watermark_covered": True,
    }
    candidates = set().union(*(set(ids) for ids in overall["candidate_order_ids"].values()))
    assert (target_order_id in candidates) == (region_id == "region_northwest")

    with pytest.raises(ValueError, match="订单产品复合键关联缺失") as error:
        calculate_channel_reference(data)

    message = str(error.value)
    assert f"order_id={target_order_id}" in message
    assert f"source_row_id={target['source_row_id']}" in message
    assert f"product_key={product_key!r}" in message
    assert dict(data) == before


def test_channel_reference_c04_preserves_legal_unknown_category(channel_fixture) -> None:
    """产品实体存在，仅非关键类别未知，不能误当关键产品关联缺失。"""
    fixture, expected = channel_fixture
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    for product in data["dimensions"]["products"]:
        product["category_id"] = None
    before = copy.deepcopy(dict(data))

    actual = calculate_channel_reference(data)

    assert actual["outcome"] == "ready" and actual["reasons"] == []
    expected_rows = [{**row, "rate": Fraction(row["rate"])} for row in expected["aggregate_rows"]]
    assert _rows_by_identity(actual) == _rows_by_identity({"aggregate_rows": expected_rows})
    assert actual == calculate_channel_reference(_InputOnly(fixture["input"]))
    assert dict(data) == before


@pytest.fixture
def c05_expected() -> Iterator[dict]:
    path = ROOT / "reference/manual_checks/A3-11_C05_expected.json"
    original_bytes = path.read_bytes()
    assert hashlib.sha256(original_bytes).hexdigest() == (
        "cbe71efb6734e3480f5d1ad93793d4338c240377dec5cb3335c01136c7565819"
    )
    record = json.loads(original_bytes)
    assert record["source_fixture_sha256"] == FIXTURE_SHA256
    assert record["source_expected_sha256"] == MANUAL_SHA256
    assert record["source_input_sha256"] == INPUT_SHA256
    original = copy.deepcopy(record)
    try:
        yield record
    finally:
        assert record == original
        assert path.read_bytes() == original_bytes


def _c05_input(fixture: dict, case: dict) -> dict:
    """只应用先行记录的输入变更，不在控制装配中计算预期。"""
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    for field, value in case.get("context_overrides", {}).items():
        if field == "watermark":
            data["context"][field].update(value)
        else:
            data["context"][field] = value
    for order in data["orders"]:
        if order["order_id"] in case.get("disable_order_ids", []):
            order["is_payment_valid"] = False
    if "remove_refund_ids" in case:
        data["refunds"] = [
            row for row in data["refunds"] if row["refund_id"] not in case["remove_refund_ids"]
        ]
    return data


def _assert_c05_state(actual: dict, case: dict, frozen: dict) -> None:
    assert actual["outcome"] == case["outcome"]
    assert actual["reasons"] == case["reasons"]
    assert actual["quality_checks"] == case["quality_checks"]
    candidates = case.get("candidate_order_ids", frozen["candidate_order_ids"])
    for window in WINDOWS:
        assert set(actual["candidate_order_ids"][window]) == set(candidates[window])


def _assert_c05_ready_publication(actual: dict, publication: dict, frozen: dict) -> None:
    expected_rows = [{**row, "rate": Fraction(row["rate"])} for row in publication["aggregate_rows"]]
    assert _rows_by_identity(actual) == _rows_by_identity({"aggregate_rows": expected_rows})
    expected_metrics = copy.deepcopy(publication["metrics"])
    for window in WINDOWS:
        expected_metrics[window]["rate"] = Fraction(expected_metrics[window]["rate"])
        assert isinstance(actual["metrics"][window]["rate"], Fraction)
    for field in ("absolute_change_ratio", "relative_change"):
        value = expected_metrics[field]
        expected_metrics[field] = None if value is None else Fraction(value)
        if value is not None:
            assert isinstance(actual["metrics"][field], Fraction)
    assert actual["metrics"] == expected_metrics
    assert actual["group_order_ids"] == frozen["group_order_ids"]
    assert actual["group_refunded_order_ids"] == publication["group_refunded_order_ids"]
    for row in actual["aggregate_rows"]:
        assert isinstance(row["rate"], Fraction)


@pytest.mark.parametrize("case_id", ("immature", "payments_below", "refunds_below", "empty_baseline"))
def test_channel_reference_c05_blocks_insufficient_comparisons(channel_fixture, c05_expected, case_id) -> None:
    fixture, frozen = channel_fixture
    case = c05_expected["cases"][case_id]
    assert case["publication"] == "blocked"
    data = _c05_input(fixture, case)
    before = copy.deepcopy(dict(data))

    actual = calculate_channel_reference(data)

    _assert_c05_state(actual, case, frozen)
    for field, value in c05_expected["blocked_publication"].items():
        assert actual[field] == value
    # 对比总体只核验语义未改；状态/空发布答案来自先行C05记录。
    for field, value in calculate_reference(data).items():
        assert actual[field] == value
    if case_id == "empty_baseline":
        disabled = {row["order_id"] for row in data["orders"] if not row["is_payment_valid"]}
        assert disabled == set(case["disable_order_ids"]) == set(frozen["candidate_order_ids"]["baseline"])
        assert actual["candidate_order_ids"]["baseline"] == []
        assert actual["candidate_order_ids"]["current"]
        assert any(row["is_payment_valid"] and row["region_id"] == "region_southeast" for row in data["orders"])
    assert dict(data) == before


@pytest.mark.parametrize("case_id", ("maturity_equal", "payments_equal", "refunds_equal"))
def test_channel_reference_c05_allows_exact_comparison_boundaries(channel_fixture, c05_expected, case_id) -> None:
    fixture, frozen = channel_fixture
    case = c05_expected["cases"][case_id]
    assert case["publication"] == "frozen"
    data = _c05_input(fixture, case)
    before = copy.deepcopy(dict(data))

    actual = calculate_channel_reference(data)

    _assert_c05_state(actual, case, frozen)
    _assert_c05_ready_publication(actual, frozen, frozen)
    assert dict(data) == before


def test_channel_reference_c05_publishes_legal_zero_baseline_refunds(channel_fixture, c05_expected) -> None:
    fixture, frozen = channel_fixture
    case = c05_expected["cases"]["zero_baseline_refunds"]
    assert case["publication"] == "zero_baseline"
    data = _c05_input(fixture, case)
    before = copy.deepcopy(dict(data))
    removed = {row["refund_id"] for row in fixture["input"]["refunds"]} - {
        row["refund_id"] for row in data["refunds"]
    }
    assert removed == set(case["remove_refund_ids"])
    assert "KR11-S-B-W1" in {row["refund_id"] for row in data["refunds"]}

    actual = calculate_channel_reference(data)

    _assert_c05_state(actual, case, frozen)
    _assert_c05_ready_publication(actual, c05_expected["zero_baseline_publication"], frozen)
    assert actual["metrics"]["baseline"]["N"] > 0
    assert actual["metrics"]["baseline"]["U"] == 0
    assert actual["metrics"]["baseline"]["rate"] == Fraction(0)
    assert actual["metrics"]["relative_change"] is None
    assert actual["aggregate_rows"]
    assert dict(data) == before


@pytest.fixture
def c06_expected() -> Iterator[dict]:
    path = ROOT / "reference/manual_checks/A3-11_C06_expected.json"
    original_bytes = path.read_bytes()
    assert hashlib.sha256(original_bytes).hexdigest() == (
        "32ecd37ddf05767c5496362c8f0f3529d8a905412cd6c1b78ae8d8a42c52ae03"
    )
    record = json.loads(original_bytes)
    assert record["source_fixture_sha256"] == FIXTURE_SHA256
    assert record["source_expected_sha256"] == MANUAL_SHA256
    assert record["source_input_sha256"] == INPUT_SHA256
    definition = record["definition_source"]
    assert hashlib.sha256((ROOT / definition["path"]).read_bytes()).hexdigest() == definition["sha256"]
    original = copy.deepcopy(record)
    try:
        yield record
    finally:
        assert record == original
        assert path.read_bytes() == original_bytes


@pytest.mark.parametrize(
    "case_id",
    ("second_success_baseline", "second_success_current", "failed_baseline", "failed_current",
     "after_horizon_baseline", "after_horizon_current", "after_as_of_baseline", "after_as_of_current"),
)
def test_channel_reference_c06_refund_events_keep_frozen_order_metrics(channel_fixture, c06_expected, case_id) -> None:
    fixture, frozen = channel_fixture
    case = c06_expected["cases"][case_id]
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    context = data["context"]
    scope = context["domain_id"], context["snapshot_id"]
    assert c06_expected["scope"] == {"domain_id": scope[0], "snapshot_id": scope[1]}
    event = {**c06_expected["scope"], **copy.deepcopy(case["additional_refund"])}
    orders = {_key(row, "order_id"): row for row in data["orders"]}
    original_events = {_key(row, "refund_id"): row for row in data["refunds"]}
    order_key = _key(event, "order_id")
    order = orders[order_key]
    window, gid = case["window"], case["channel_id"]
    assert order["channel_id"] == gid and order["region_id"] == "region_northwest"
    assert order["is_payment_valid"] is True
    assert order["order_id"] in frozen["group_order_ids"][window][gid]
    assert (order["order_id"] in frozen["counted_refund_order_ids"][window]) is case["target_is_already_refunded"]
    assert _key(event, "refund_id") not in original_events
    source_ids = {
        row["source_row_id"] for rows in (data["orders"], data["refunds"], *data["dimensions"].values())
        for row in rows
    }
    assert event["source_row_id"] not in source_ids
    paid_at, refund_at = _instant(order["paid_at"]), _instant(event["refund_at"])
    horizon = timedelta(seconds=context["horizon_seconds"])
    as_of = _instant(context["as_of"])
    assert _instant(context["windows"][window]["start"]) <= paid_at < _instant(context["windows"][window]["end"])
    assert paid_at <= refund_at  # 不混入支付前退款故障。
    prior_target_events = [row for row in original_events.values() if _key(row, "order_id") == order_key]
    if case["kind"] == "second_success":
        assert case["target_is_already_refunded"] and case["expected_event_qualifies"]
        assert event["status"] == "success" and paid_at <= refund_at <= paid_at + horizon
        assert refund_at <= as_of
        prior = original_events[(*scope, case["original_refund_id"])]
        assert prior_target_events == [prior]
        assert _key(prior, "order_id") == order_key and prior["status"] == "success"
        assert paid_at <= _instant(prior["refund_at"]) <= paid_at + horizon
        assert _instant(prior["refund_at"]) <= as_of
        assert prior["refund_id"] != event["refund_id"]
        assert prior["source_row_id"] != event["source_row_id"]
    else:
        assert not prior_target_events
        assert case["target_is_already_refunded"] is False
        assert case["expected_event_qualifies"] is False
        if case["kind"] == "failed":
            assert event["status"] == "failed"
            assert paid_at <= refund_at <= paid_at + horizon and refund_at <= as_of
        elif case["kind"] == "after_horizon":
            assert event["status"] == "success"
            assert refund_at == paid_at + horizon + timedelta(microseconds=1)
            assert refund_at <= as_of
        else:
            assert case["kind"] == "after_as_of" and event["status"] == "success"
            assert refund_at == as_of + timedelta(microseconds=1)
            assert refund_at > paid_at + horizon  # 成熟前提下不是孤立as_of边界。

    data["refunds"].append(event)
    before = copy.deepcopy(dict(data))
    assert len({_key(row, "refund_id") for row in data["refunds"]}) == len(data["refunds"])
    assert len({row["source_row_id"] for row in data["refunds"]}) == len(data["refunds"])
    target_events = [row for row in data["refunds"] if _key(row, "order_id") == order_key]
    assert len(target_events) == (2 if case["kind"] == "second_success" else 1)

    actual = calculate_channel_reference(data)

    assert actual["outcome"] == c06_expected["expected_outcome"] == "ready"
    assert actual["reasons"] == []
    assert actual["quality_checks"] == {
        key: frozen["quality_checks"][key]
        for key in ("all_orders_mature", "payments_watermark_covered", "refunds_watermark_covered")
    }
    expected_rows = [{**row, "rate": Fraction(row["rate"])} for row in frozen["aggregate_rows"]]
    rows = _rows_by_identity(actual)
    assert rows == _rows_by_identity({"aggregate_rows": expected_rows})
    expected_metrics = copy.deepcopy(frozen["metrics"])
    for name in WINDOWS:
        expected_metrics[name]["rate"] = Fraction(expected_metrics[name]["rate"])
        assert set(actual["candidate_order_ids"][name]) == set(frozen["candidate_order_ids"][name])
        assert isinstance(actual["metrics"][name]["rate"], Fraction)
    for field in ("absolute_change_ratio", "relative_change"):
        expected_metrics[field] = Fraction(expected_metrics[field])
        assert isinstance(actual["metrics"][field], Fraction)
    assert actual["metrics"] == expected_metrics
    assert actual["group_order_ids"] == frozen["group_order_ids"]
    assert actual["group_refunded_order_ids"] == frozen["group_refunded_order_ids"]
    target_row = rows[WINDOWS.index(window), "channel", gid]
    assert target_row["refunded_orders"] - len(frozen["group_refunded_order_ids"][window][gid]) == (
        c06_expected["expected_U_change"]
    )
    assert actual["group_refunded_order_ids"][window][gid].count(order["order_id"]) == (
        1 if case["target_is_already_refunded"] else 0
    )
    for row in actual["aggregate_rows"]:
        assert isinstance(row["rate"], Fraction)
    assert dict(data) == before


def test_channel_reference_c07_repeated_calls_and_results_are_isolated(channel_fixture) -> None:
    """重复及交错调用不共享可变状态；复用既有input访问和冻结文件保护。"""
    fixture, _ = channel_fixture
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    before = copy.deepcopy(dict(data))
    first = calculate_channel_reference(data)
    snapshot = copy.deepcopy(first)
    repeated = calculate_channel_reference(data)
    assert repeated == snapshot

    # 显式修改先前返回的各层容器，检出结果缓存或跨调用可变对象别名。
    first["reasons"].append("c07_caller_mutation")
    first["quality_checks"].clear()
    first["metrics"]["baseline"]["N"] = -1
    first["aggregate_rows"][0]["paid_orders"] = -1
    first["candidate_order_ids"]["baseline"].clear()
    first["group_order_ids"]["baseline"]["channel_web"].clear()
    first["group_refunded_order_ids"]["baseline"]["channel_app"].clear()
    assert repeated == snapshot
    assert dict(data) == before

    # C03已有独立反例数值；这里只检查另一合法Scope不会污染原Scope。
    other = _InputOnly(copy.deepcopy(fixture["input"]))
    other["context"]["filters"]["region_ids"] = []
    other_before = copy.deepcopy(dict(other))
    all_regions = calculate_channel_reference(other)
    all_regions_snapshot = copy.deepcopy(all_regions)
    assert all_regions["metrics"] != snapshot["metrics"]
    assert calculate_channel_reference(data) == snapshot
    assert calculate_channel_reference(_InputOnly(copy.deepcopy(fixture["input"]))) == snapshot
    assert all_regions == all_regions_snapshot
    assert repeated == snapshot
    assert dict(data) == before
    assert dict(other) == other_before


@pytest.mark.parametrize(
    "target", ("orders", "refunds", "products", "categories", "channels", "regions", "all"),
)
def test_channel_reference_c07_reordering_preserves_groups_and_candidate_sets(channel_fixture, target: str) -> None:
    """分别及联合逆序后重复计算，候选队列仅比较集合。"""
    fixture, _ = channel_fixture
    original = calculate_channel_reference(_InputOnly(fixture["input"]))
    data = _InputOnly(copy.deepcopy(fixture["input"]))
    # 冻结产品/类别目录各仅一行；深拷贝中补合法未引用项，使逆序有区分力。
    for name, id_field in (("products", "product_id"), ("categories", "category_id")):
        if target not in (name, "all"):
            continue
        rows = data["dimensions"][name]
        assert len(rows) == 1
        unused = copy.deepcopy(rows[0])
        unused[id_field] += "_c07_unused"
        unused["source_row_id"] += "_c07_unused"
        references = data["orders"] if name == "products" else data["dimensions"]["products"]
        assert all(row.get(id_field) != unused[id_field] for row in references)
        rows.append(unused)
    augmented_before = copy.deepcopy(dict(data))
    augmented = calculate_channel_reference(data)
    assert dict(data) == augmented_before
    if target == "all":
        selected = (data["orders"], data["refunds"], *data["dimensions"].values())
    elif target in ("orders", "refunds"):
        selected = (data[target],)
    else:
        selected = (data["dimensions"][target],)
    for rows in selected:
        # 每个逆序控制均有实质变化，避免单行目录让测试空转。
        assert len(rows) > 1 and rows[0] != rows[-1]
        rows.reverse()
    before = copy.deepcopy(dict(data))

    reordered = calculate_channel_reference(data)
    assert dict(data) == before
    repeated = calculate_channel_reference(data)
    assert dict(data) == before
    restored = calculate_channel_reference(_InputOnly(fixture["input"]))

    # 原始→重排→同一重排输入重复→原始，检出跨调用状态污染。
    for result in (augmented, reordered, repeated, restored):
        assert _rows_by_identity(result) == _rows_by_identity(original)
        assert result["group_order_ids"] == original["group_order_ids"]
        assert result["group_refunded_order_ids"] == original["group_refunded_order_ids"]
        for window in WINDOWS:
            assert set(result["candidate_order_ids"][window]) == set(original["candidate_order_ids"][window])
            assert isinstance(result["metrics"][window]["rate"], Fraction)
        assert all(isinstance(row["rate"], Fraction) for row in result["aggregate_rows"])
        for field in ("outcome", "reasons", "quality_checks", "metrics"):
            assert result[field] == original[field]
    assert dict(data) == before
