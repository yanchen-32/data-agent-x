"""A3-11 C01/C02：固定渠道结果、过滤及来源回归，不生成预期。"""

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
