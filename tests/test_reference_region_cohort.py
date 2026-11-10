"""地区参考入口：冻结四/六行及必要的去重、Scope和隔离回归。"""

import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from reference.region_cohort import calculate_region_reference
from test_reference_channel_cohort import _InputOnly


ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = ROOT / "reference/manual_checks/G0_M01_region_expected.json"
ORACLE_SHA256 = "50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce"


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@pytest.fixture
def region_fixture():
    oracle_bytes = ORACLE_PATH.read_bytes()
    assert hashlib.sha256(oracle_bytes).hexdigest() == ORACLE_SHA256
    oracle = json.loads(oracle_bytes)
    bound_bytes = {item["path"]: (ROOT / item["path"]).read_bytes() for item in oracle["sources"].values()}
    for item in oracle["sources"].values():
        assert hashlib.sha256(bound_bytes[item["path"]]).hexdigest() == item["sha256"]
    fixture = json.loads(bound_bytes[oracle["sources"]["fixture"]["path"]])
    assert _sha(fixture["input"]) == oracle["sources"]["fixture"]["input_sha256"]
    before = copy.deepcopy((fixture, oracle))
    try:
        yield fixture["input"], oracle
    finally:
        assert (fixture, oracle) == before
        assert ORACLE_PATH.read_bytes() == oracle_bytes
        assert all((ROOT / path).read_bytes() == content for path, content in bound_bytes.items())


def _variant(region_fixture, variant_id):
    raw, oracle = region_fixture

    def assemble(key):
        variant = oracle["input_variants"][key]
        base = variant["base_variant_id"]
        data = copy.deepcopy(raw) if base == "source_input" else assemble(base)
        # 只重放本轮使用的固定输入变更，不计算expected。
        for change in variant["changes"]:
            action = change["operation"]
            if action == "replace_context":
                target = data["context"]
                for field in change["path"][:-1]:
                    target = target[field]
                target[change["path"][-1]] = copy.deepcopy(change["value"])
            elif action == "update_orders":
                rows = [row for row in data["orders"] if row["order_id"] in change["order_ids"]]
                assert len(rows) == len(change["order_ids"])
                for row in rows:
                    row.update(copy.deepcopy(change["fields"]))
            elif action == "append_refund":
                data["refunds"].append(copy.deepcopy(change["row"]))
            elif action == "update_catalog":
                rows = [row for row in data["dimensions"][change["catalog"]] if row[change["id_field"]] == change["id"]]
                assert len(rows) == 1
                rows[0].update(copy.deepcopy(change["fields"]))
            elif action == "reverse":
                target = data
                for field in change["path"]:
                    target = target[field]
                target.reverse()
            else:
                raise AssertionError(f"本轮未使用的变更类型：{action}")
        assert _sha(data) == variant["input_sha256"]
        return data

    return _InputOnly(assemble(variant_id))


def _calculate(data):
    before = copy.deepcopy(dict(data))
    try:
        return calculate_region_reference(data)
    finally:
        assert dict(data) == before


def _assert_frozen(actual, frozen):
    expected = copy.deepcopy(frozen["expected"])
    for row in expected["aggregate_rows"]:
        row["rate"] = Fraction(row["rate"])
    for window in ("baseline", "current"):
        expected["metrics"][window]["rate"] = Fraction(expected["metrics"][window]["rate"])
    for field in ("absolute_change_ratio", "relative_change"):
        expected["metrics"][field] = Fraction(expected["metrics"][field])
        assert isinstance(actual["metrics"][field], Fraction)
    assert set(actual) == set(expected)
    assert {k: v for k, v in actual.items() if k != "candidate_order_ids"} == {
        k: v for k, v in expected.items() if k != "candidate_order_ids"
    }
    for window in ("baseline", "current"):
        assert set(actual["candidate_order_ids"][window]) == set(expected["candidate_order_ids"][window])
        assert isinstance(actual["metrics"][window]["rate"], Fraction)
    identities = [(r["window_index"], r["dimension_id"], r["group_id"]) for r in actual["aggregate_rows"]]
    assert len(set(identities)) == len(identities)
    for row in actual["aggregate_rows"]:
        assert type(row["paid_orders"]) is int and type(row["refunded_orders"]) is int
        assert isinstance(row["rate"], Fraction)


@pytest.mark.parametrize("case_id", ("RG01.W", "RG02.A"))
def test_region_reference_matches_frozen_oracle_and_sources(region_fixture, case_id):
    data = _variant(region_fixture, case_id)
    frozen = region_fixture[1]["cases"][case_id]
    actual = _calculate(data)
    _assert_frozen(actual, frozen)
    evidence = frozen["evidence"]
    scope = data["context"]["domain_id"], data["context"]["snapshot_id"]
    orders = {(row["domain_id"], row["snapshot_id"], row["order_id"]): row for row in data["orders"]}
    refunds = {(row["domain_id"], row["snapshot_id"], row["refund_id"]): row for row in data["refunds"]}
    for index, window in enumerate(("baseline", "current")):
        members, refunded_members = [], []
        paid_sources, event_ids, refund_sources = set(), set(), set()
        for gid, ids in actual["group_order_ids"][window].items():
            refunded = actual["group_refunded_order_ids"][window][gid]
            assert set(refunded) <= set(ids)
            sources = {orders[(*scope, oid)]["source_row_id"] for oid in ids}
            assert sources == set(evidence["group_cohort_source_row_ids"][window][gid])
            assert all(orders[(*scope, oid)]["region_id"] == gid for oid in ids)
            # 只对RG01/RG02固定输入回查实际退款订单的原始事件；不重算退款资格Oracle。
            refunded_keys = {(*scope, oid) for oid in refunded}
            events = {
                key: row for key, row in refunds.items()
                if (row["domain_id"], row["snapshot_id"], row["order_id"]) in refunded_keys
            }
            observed_ids = {key[2] for key in events}
            observed_sources = {row["source_row_id"] for row in events.values()}
            assert observed_ids == set(evidence["group_refund_event_ids"][window][gid])
            assert {row["order_id"] for row in events.values()} == set(refunded)
            assert observed_sources == set(evidence["group_refund_source_row_ids"][window][gid])
            paid_sources |= sources
            event_ids |= observed_ids
            refund_sources |= observed_sources
            members.extend(ids)
            refunded_members.extend(refunded)
        assert len(members) == len(set(members)) == actual["metrics"][window]["N"]
        assert len(refunded_members) == len(set(refunded_members)) == actual["metrics"][window]["U"]
        assert set(members) == set(actual["candidate_order_ids"][window])
        assert set(refunded_members) == set(evidence["counted_refund_order_ids"][window])
        assert paid_sources == set(evidence["cohort_source_row_ids"][window])
        assert event_ids == set(evidence["qualifying_refund_event_ids"][window])
        assert refund_sources == set(evidence["qualifying_refund_source_row_ids"][window])
        rows = [r for r in actual["aggregate_rows"] if r["window_index"] == index and r["dimension_id"] == "region"]
        assert sum(r["paid_orders"] for r in rows) == actual["metrics"][window]["N"]
        assert sum(r["refunded_orders"] for r in rows) == actual["metrics"][window]["U"]
        assert set(members).isdisjoint(evidence["excluded_order_ids"])
        assert paid_sources.isdisjoint(evidence["excluded_order_source_row_ids"])
        assert event_ids.isdisjoint(evidence["excluded_refund_event_ids"])
        assert refund_sources.isdisjoint(evidence["excluded_refund_source_row_ids"])


def test_region_reference_deduplicates_refunds_for_southeast_order(region_fixture):
    data = _variant(region_fixture, "RG03.D")
    events = [r for r in data["refunds"] if r["order_id"] == "K11-S-C-A1"]
    assert len(events) == len({r["refund_id"] for r in events}) == 2
    actual = _calculate(data)
    # 原人工台账§5 D：仅事件数增加，四个地区组及两总计不变。
    _assert_frozen(actual, region_fixture[1]["cases"]["RG02.A"])
    assert actual["group_refunded_order_ids"]["current"]["region_southeast"] == ["K11-S-C-A1"]


def test_region_reference_results_calls_and_reordering_are_isolated(region_fixture):
    data = _variant(region_fixture, "RG02.A")
    first = _calculate(data)
    snapshot = copy.deepcopy(first)
    repeated = _calculate(data)
    first["metrics"]["baseline"]["N"] = -1
    first["aggregate_rows"][0]["paid_orders"] = -1
    first["group_order_ids"]["current"]["region_northwest"].clear()
    _assert_frozen(_calculate(_variant(region_fixture, "RG01.W")), region_fixture[1]["cases"]["RG01.W"])
    _assert_frozen(_calculate(data), region_fixture[1]["cases"]["RG02.A"])
    _assert_frozen(_calculate(_variant(region_fixture, "RG06.A-reverse-combined")), region_fixture[1]["cases"]["RG02.A"])
    assert repeated == snapshot


def test_region_reference_maturity_uses_filtered_scope(region_fixture):
    _assert_frozen(_calculate(_variant(region_fixture, "RG04.scope-W")), region_fixture[1]["cases"]["RG01.W"])
    actual = _calculate(_variant(region_fixture, "RG04.scope-A"))
    assert actual["outcome"] == "insufficient_evidence"
    assert actual["reasons"] == ["观察期未成熟"]
    assert actual["quality_checks"] == {
        "all_orders_mature": False, "payments_watermark_covered": True, "refunds_watermark_covered": True,
    }
    assert actual["aggregate_rows"] == []
    assert actual["group_order_ids"] == actual["group_refunded_order_ids"] == {}
    assert actual["metrics"] == {
        "baseline": {"N": None, "U": None, "rate": None},
        "current": {"N": None, "U": None, "rate": None},
        "absolute_change_ratio": None, "relative_change": None,
    }


@pytest.mark.parametrize("variant_id", ("RG04.product-ready", "RG04.product-immature"))
def test_region_reference_rejects_critical_product_join_outside_filter(region_fixture, variant_id):
    with pytest.raises(ValueError) as error:
        _calculate(_variant(region_fixture, variant_id))
    message = str(error.value)
    for value in ("K11-S-C-A1", "r11-order-s-c-app-1", "domain_a", "fixture_single_region_channel_v1_draft", "product_rg04_missing"):
        assert value in message


@pytest.mark.parametrize("variant_id", ("RG05.unknown-explicit", "RG05.unknown-unregistered"))
def test_region_reference_preserves_preapproved_noncritical_unknown(region_fixture, variant_id):
    actual = _calculate(_variant(region_fixture, variant_id))
    rows = {row["group_id"]: row for row in actual["aggregate_rows"] if row["window_index"] == 1}
    assert actual["outcome"] == "ready" and len(actual["aggregate_rows"]) == 7
    assert (rows["__unknown__"]["paid_orders"], rows["__unknown__"]["refunded_orders"], rows["__unknown__"]["rate"]) == (1, 1, Fraction(1))
    assert rows["__unknown__"]["group_label"] is None
    assert (rows["region_southeast"]["paid_orders"], rows["region_southeast"]["refunded_orders"]) == (1, 0)
    assert actual["group_order_ids"]["current"]["__unknown__"] == ["K11-S-C-A1"]
    assert actual["group_refunded_order_ids"]["current"]["__unknown__"] == ["K11-S-C-A1"]
    assert actual["metrics"]["current"] == {"N": 6, "U": 4, "rate": Fraction(2, 3)}


def test_region_reference_missing_label_preserves_registered_id(region_fixture):
    actual = _calculate(_variant(region_fixture, "RG05.label-null"))
    expected = copy.deepcopy(region_fixture[1]["cases"]["RG02.A"])
    for row in expected["expected"]["aggregate_rows"]:
        if row["group_id"] == "region_southeast":
            row["group_label"] = None
    _assert_frozen(actual, expected)


@pytest.mark.parametrize("variant_id", ("RG05.invalid-filter-unregistered", "RG05.invalid-filter-sentinel", "RG05.invalid-order-null"))
def test_region_reference_rejects_invalid_filter_or_order_region(region_fixture, variant_id):
    with pytest.raises(ValueError):
        _calculate(_variant(region_fixture, variant_id))
