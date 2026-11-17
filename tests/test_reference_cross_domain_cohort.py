"""M02合法跨域正例：独立冻结结果、完整键来源及交错调用，不生成Oracle。"""

import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from reference.category_cohort import calculate_category_reference
from test_reference_category_cohort import assert_partition
from test_reference_channel_cohort import _InputOnly


ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = ROOT / "reference/manual_checks/G0_M02_cross_domain_expected.json"
ORACLE_SHA256 = "d6b831e08c943a259a56c4ed24db0dd153585c994c759685002dbc6be86ba8a6"
CASES = ("M02-A", "M02-B")
WINDOWS = ("baseline", "current")


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _key(row, field):
    return row["domain_id"], row["snapshot_id"], row[field]


@pytest.fixture
def cross_domain_fixture():
    raw = ORACLE_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORACLE_SHA256
    oracle = json.loads(raw)
    assert oracle["rule_binding_version"] == "M02-DD02-v1.2-design-v1"
    sources = {entry["path"]: (ROOT / entry["path"]).read_bytes() for entry in oracle["sources"].values()}
    for entry in oracle["sources"].values():
        assert hashlib.sha256(sources[entry["path"]]).hexdigest() == entry["sha256"]
    inputs = {}
    for case_id in CASES:
        case = oracle["cases"][case_id]
        source = oracle["sources"][case["input_source"]]
        fixture = json.loads(sources[source["path"]])
        inputs[case_id] = fixture["input"]
        assert _sha(fixture["input"]) == fixture["input_sha256"] == source["input_sha256"]
        assert fixture["input"]["context"] == case["context"]
        assert _sha(case["expected"]) == case["expected_sha256"]
    before = copy.deepcopy((inputs, oracle))
    try:
        yield inputs, oracle
    finally:
        assert (inputs, oracle) == before
        assert ORACLE_PATH.read_bytes() == raw
        assert all((ROOT / path).read_bytes() == content for path, content in sources.items())


def _calculate(data):
    before = copy.deepcopy(dict(data))
    try:
        return calculate_category_reference(data)
    finally:
        assert dict(data) == before


def _assert_frozen_result_and_sources(actual, data, frozen):
    expected = copy.deepcopy(frozen["expected"])
    for row in expected["aggregate_rows"]:
        row["rate"] = Fraction(row["rate"])
    for window in WINDOWS:
        expected["metrics"][window]["rate"] = Fraction(expected["metrics"][window]["rate"])
    for field in ("absolute_change_ratio", "relative_change"):
        expected["metrics"][field] = Fraction(expected["metrics"][field])
        assert isinstance(actual["metrics"][field], Fraction)
    assert actual["outcome"] == "ready"
    assert set(actual) == set(expected)
    assert {k: v for k, v in actual.items() if k != "candidate_order_ids"} == {
        k: v for k, v in expected.items() if k != "candidate_order_ids"
    }
    rows = actual["aggregate_rows"]
    assert len(rows) == 6
    identities = [(r["window_index"], r["dimension_id"], r["group_id"]) for r in rows]
    assert len(set(identities)) == 6
    for row in rows:
        assert type(row["paid_orders"]) is int and type(row["refunded_orders"]) is int
        assert isinstance(row["rate"], Fraction)
    assert_partition(actual)

    assert data["context"] == frozen["context"]
    scope = frozen["context"]["domain_id"], frozen["context"]["snapshot_id"]
    orders = {_key(row, "order_id"): row for row in data["orders"]}
    refunds = {_key(row, "refund_id"): row for row in data["refunds"]}
    assert len(orders) == len(data["orders"]) and len(refunds) == len(data["refunds"])
    assert all(key[:2] == scope for key in (*orders, *refunds))
    catalogs = {}
    for name, field in (("products", "product_id"), ("categories", "category_id"), ("regions", "region_id"), ("channels", "channel_id")):
        catalogs[name] = {_key(row, field): row for row in data["dimensions"][name]}
        assert len(catalogs[name]) == len(data["dimensions"][name])
        assert len(catalogs[name]) == len(frozen["catalog_ledger"][name])
        for key, row in catalogs[name].items():
            ledger = frozen["catalog_ledger"][name][row[field]]
            assert key[:2] == scope and key == tuple(ledger["key"])
            assert row["source_row_id"] == ledger["source_row_id"]
            if name == "products":
                assert row["category_id"] == ledger["category_id"]
            else:
                assert row["label"] == ledger["label"]

    evidence = frozen["evidence"]
    for index, window in enumerate(WINDOWS):
        metrics = actual["metrics"][window]
        assert type(metrics["N"]) is int and type(metrics["U"]) is int
        assert isinstance(metrics["rate"], Fraction)
        candidates = actual["candidate_order_ids"][window]
        assert len(candidates) == len(set(candidates)) == metrics["N"]
        assert set(candidates) == set(expected["candidate_order_ids"][window])
        assert {(*scope, oid) for oid in candidates} == {tuple(key) for key in evidence["cohort_order_keys"][window]}
        paid_keys, refunded_keys, event_keys = set(), set(), set()
        paid_sources, refund_sources = set(), set()
        for gid, members in actual["group_order_ids"][window].items():
            group_paid = {(*scope, oid) for oid in members}
            group_refunded = {(*scope, oid) for oid in actual["group_refunded_order_ids"][window][gid]}
            assert group_refunded <= group_paid
            assert not paid_keys & group_paid and not refunded_keys & group_refunded
            sources = {orders[key]["source_row_id"] for key in group_paid}
            assert sources == set(evidence["group_cohort_source_row_ids"][window][gid])
            for key in group_paid:
                order = orders[key]
                ledger = frozen["source_order_ledger"][order["order_id"]]
                assert key == tuple(ledger["order_key"])
                assert order["source_row_id"] == ledger["source_row_id"]
                assert order["paid_at"] == ledger["paid_at"]
                assert ledger["assigned_window"] == window and ledger["assigned_category_id"] == gid
                product_key = _key(order, "product_id")
                assert product_key == tuple(ledger["product_key"])
                assert catalogs["products"][product_key]["category_id"] == gid
                assert (*scope, gid) == tuple(ledger["category_key"])
                row, = [r for r in rows if (r["window_index"], r["dimension_id"], r["group_id"]) == (index, "category", gid)]
                assert row["group_label"] == catalogs["categories"][(*scope, gid)]["label"]
            # 固定配对的全部事件资格已由先行台账冻结；只回查实际退款订单的事件来源。
            events = {key: row for key, row in refunds.items() if _key(row, "order_id") in group_refunded}
            expected_events = {
                tuple(frozen["source_refund_ledger"][rid]["refund_key"])
                for rid in evidence["group_refund_event_ids"][window][gid]
            }
            assert set(events) == expected_events
            assert {row["source_row_id"] for row in events.values()} == set(evidence["group_refund_source_row_ids"][window][gid])
            assert {_key(row, "order_id") for row in events.values()} == group_refunded
            for key, refund in events.items():
                ledger = frozen["source_refund_ledger"][refund["refund_id"]]
                assert key == tuple(ledger["refund_key"])
                assert _key(refund, "order_id") == tuple(ledger["order_key"])
                assert refund["source_row_id"] == ledger["source_row_id"]
                assert refund["status"] == ledger["status"] == "success"
                assert refund["refund_at"] == ledger["refund_at"]
                assert ledger["assigned_window"] == window and ledger["assigned_category_id"] == gid
            paid_keys |= group_paid
            refunded_keys |= group_refunded
            event_keys |= set(events)
            paid_sources |= sources
            refund_sources |= {row["source_row_id"] for row in events.values()}
        assert paid_keys == {tuple(key) for key in evidence["cohort_order_keys"][window]}
        assert refunded_keys == {tuple(key) for key in evidence["counted_refund_order_keys"][window]}
        assert len(paid_keys) == metrics["N"] and len(refunded_keys) == metrics["U"]
        assert paid_sources == set(evidence["cohort_source_row_ids"][window])
        assert event_keys == {(*scope, rid) for rid in evidence["qualifying_refund_event_ids"][window]}
        assert refund_sources == set(evidence["qualifying_refund_source_row_ids"][window])


@pytest.mark.parametrize("case_id", CASES)
def test_cross_domain_scope_matches_frozen_oracle_and_sources(cross_domain_fixture, case_id):
    inputs, oracle = cross_domain_fixture
    data = _InputOnly(copy.deepcopy(inputs[case_id]))
    actual = _calculate(data)
    _assert_frozen_result_and_sources(actual, data, oracle["cases"][case_id])


@pytest.mark.parametrize("sequence", (("M02-A", "M02-B", "M02-A"), ("M02-B", "M02-A", "M02-B")), ids=("A-B-A", "B-A-B"))
def test_cross_domain_interleaving_keeps_each_frozen_scope(cross_domain_fixture, sequence):
    inputs, oracle = cross_domain_fixture
    data = {case: _InputOnly(copy.deepcopy(inputs[case])) for case in CASES}
    original = copy.deepcopy(data)
    a, b = (data[case] for case in CASES)
    assert a["context"]["domain_id"] != b["context"]["domain_id"]
    assert a["context"]["snapshot_id"] == b["context"]["snapshot_id"]
    for collection, field, intersection in (("orders", "order_id", "local_order_id_intersection"), ("refunds", "refund_id", "local_refund_id_intersection")):
        assert {r[field] for r in a[collection]} & {r[field] for r in b[collection]} == set(oracle["pair_contract"][intersection])
        assert {_key(r, field) for r in a[collection]}.isdisjoint({_key(r, field) for r in b[collection]})
    results = []
    for case_id in sequence:
        actual = _calculate(data[case_id])
        _assert_frozen_result_and_sources(actual, data[case_id], oracle["cases"][case_id])
        assert data == original
        for returned, snapshot in results:
            assert returned == snapshot
        results.append((actual, copy.deepcopy(actual)))
