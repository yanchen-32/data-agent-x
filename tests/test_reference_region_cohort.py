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
            elif action == "append_catalog":
                data["dimensions"][change["catalog"]].append(copy.deepcopy(change["row"]))
            elif action in ("update_refund", "remove_refund"):
                rows = [row for row in data["refunds"] if row["refund_id"] == change["refund_id"]]
                assert len(rows) == 1
                if action == "update_refund":
                    rows[0].update(copy.deepcopy(change["fields"]))
                else:
                    data["refunds"].remove(rows[0])
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


def _assert_refund_control_sources_and_conservation(actual, data, evidence):
    scope = data["context"]["domain_id"], data["context"]["snapshot_id"]
    orders = {(row["domain_id"], row["snapshot_id"], row["order_id"]): row for row in data["orders"]}
    for index, window in enumerate(("baseline", "current")):
        paid_members, refunded_members = [], []
        for gid, ids in actual["group_order_ids"][window].items():
            refunded = actual["group_refunded_order_ids"][window][gid]
            assert set(refunded) <= set(ids)
            assert all(orders[(*scope, oid)]["region_id"] == gid for oid in ids)
            assert {orders[(*scope, oid)]["source_row_id"] for oid in ids} == set(
                evidence["group_cohort_source_row_ids"][window][gid]
            )
            # T/Z中每个退款订单恰有一个有效事件；资格由先行台账确定，不从函数生成。
            events = [row for row in data["refunds"] if (
                row["domain_id"], row["snapshot_id"], row["order_id"]
            ) in {(*scope, oid) for oid in refunded}]
            assert {row["refund_id"] for row in events} == set(evidence["group_refund_event_ids"][window][gid])
            assert {row["source_row_id"] for row in events} == set(evidence["group_refund_source_row_ids"][window][gid])
            row, = [r for r in actual["aggregate_rows"] if (
                r["window_index"], r["dimension_id"], r["group_id"]
            ) == (index, "region", gid)]
            assert (row["paid_orders"], row["refunded_orders"], row["rate"]) == (
                len(ids), len(refunded), Fraction(len(refunded), len(ids)),
            )
            paid_members.extend(ids)
            refunded_members.extend(refunded)
        assert len(paid_members) == len(set(paid_members)) == actual["metrics"][window]["N"]
        assert len(refunded_members) == len(set(refunded_members)) == actual["metrics"][window]["U"]
        assert set(paid_members) == set(actual["candidate_order_ids"][window])
        assert set(refunded_members) == set(evidence["counted_refund_order_ids"][window])


def test_region_reference_refund_follows_payment_window_and_region(region_fixture):
    data = _variant(region_fixture, "RG03.T")
    # 人工台账§5 T：09-05支付，09-09退款，09-12观察期末；归B/SE而非C。
    refund, = [row for row in data["refunds"] if row["refund_id"] == "KR11-S-B-W1"]
    assert refund["refund_at"] == "2026-09-09T00:00:00Z"
    assert refund["order_id"] == "K11-S-B-W1"
    assert refund["source_row_id"] == "r11-refund-s-b-web-1"
    actual = _calculate(data)
    frozen = region_fixture[1]["cases"]["RG02.A"]
    _assert_frozen(actual, frozen)
    assert actual["group_refunded_order_ids"]["baseline"]["region_southeast"] == ["K11-S-B-W1"]
    assert "K11-S-B-W1" not in actual["group_refunded_order_ids"]["current"]["region_southeast"]
    _assert_refund_control_sources_and_conservation(actual, data, frozen["evidence"])


def test_region_reference_keeps_positive_denominator_zero_refund_group(region_fixture):
    data = _variant(region_fixture, "RG03.Z")
    assert all(row["refund_id"] != "KR11-S-B-W1" for row in data["refunds"])
    # 人工台账§5 Z先行预期：仅B/SE退款单及来源移除，支付集合和当前窗不变。
    frozen = copy.deepcopy(region_fixture[1]["cases"]["RG02.A"])
    expected = frozen["expected"]
    expected["metrics"]["baseline"] = {"N": 5, "U": 1, "rate": "1/5"}
    expected["metrics"]["absolute_change_ratio"] = "7/15"
    expected["metrics"]["relative_change"] = "7/3"
    expected["group_refunded_order_ids"]["baseline"]["region_southeast"] = []
    for row in expected["aggregate_rows"]:
        if row["window_index"] == 0 and row["dimension_id"] is None:
            row.update(refunded_orders=1, rate="1/5")
        elif row["window_index"] == 0 and row["group_id"] == "region_southeast":
            row.update(refunded_orders=0, rate="0")
    evidence = frozen["evidence"]
    evidence["counted_refund_order_ids"]["baseline"].remove("K11-S-B-W1")
    evidence["group_refund_event_ids"]["baseline"]["region_southeast"] = []
    evidence["group_refund_source_row_ids"]["baseline"]["region_southeast"] = []
    actual = _calculate(data)
    _assert_frozen(actual, frozen)
    assert actual["outcome"] == "ready"
    row, = [r for r in actual["aggregate_rows"] if (r["window_index"], r["group_id"]) == (0, "region_southeast")]
    assert (row["paid_orders"], row["refunded_orders"], row["rate"]) == (2, 0, Fraction(0))
    assert isinstance(row["rate"], Fraction)
    assert actual["group_order_ids"]["baseline"]["region_southeast"] == ["K11-S-B-A1", "K11-S-B-W1"]
    assert actual["group_refunded_order_ids"]["baseline"]["region_southeast"] == []
    _assert_refund_control_sources_and_conservation(actual, data, evidence)


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


@pytest.mark.parametrize(
    ("variant_id", "reason", "failed_check"),
    (
        ("RG04.M-minus", "观察期未成熟", "all_orders_mature"),
        ("RG04.P-minus", "支付水位不足", "payments_watermark_covered"),
        ("RG04.R-minus", "退款水位不足", "refunds_watermark_covered"),
        ("RG04.E", "支付窗口无有效样本", None),
    ),
)
def test_region_reference_comparison_gates_suppress_all_published_results(
    region_fixture, variant_id, reason, failed_check,
):
    # 人工台账§6：A最晚成熟09-21，支付水位须覆盖窗口end 09-15。
    data = _variant(region_fixture, variant_id)
    assert data["context"]["filters"]["region_ids"] == []
    actual = _calculate(data)
    frozen = region_fixture[1]["cases"]["RG02.A"]["expected"]
    assert set(actual) == set(frozen)
    assert actual["outcome"] == "insufficient_evidence"
    assert actual["reasons"] == [reason]
    quality = {
        "all_orders_mature": True, "payments_watermark_covered": True, "refunds_watermark_covered": True,
    }
    if failed_check is not None:
        quality[failed_check] = False
    assert actual["quality_checks"] == quality
    assert actual["metrics"] == {
        "baseline": {"N": None, "U": None, "rate": None},
        "current": {"N": None, "U": None, "rate": None},
        "absolute_change_ratio": None, "relative_change": None,
    }
    assert actual["aggregate_rows"] == []
    assert actual["group_order_ids"] == actual["group_refunded_order_ids"] == {}
    # 候选只作诊断，不要求函数返回手算N/U；不足时也不能偷偷丢掉未成熟订单。
    for window in ("baseline", "current"):
        expected_ids = [] if variant_id == "RG04.E" and window == "baseline" else frozen["candidate_order_ids"][window]
        assert set(actual["candidate_order_ids"][window]) == set(expected_ids)
        assert len(actual["candidate_order_ids"][window]) == len(expected_ids)
    if variant_id == "RG04.E":
        invalid = {row["order_id"] for row in data["orders"] if not row["is_payment_valid"]}
        assert invalid == set(frozen["candidate_order_ids"]["baseline"])
        assert len(invalid) == 5  # 全地区基期五单，不能只关闭西北三单。


@pytest.mark.parametrize("variant_id", ("RG04.M-equal", "RG04.R-equal"))
def test_region_reference_comparison_gate_equalities_are_ready(region_fixture, variant_id):
    data = _variant(region_fixture, variant_id)
    assert data["context"]["filters"]["region_ids"] == []
    if variant_id == "RG04.M-equal":
        assert data["context"]["as_of"] == "2026-09-21T00:00:00Z"
    else:
        assert data["context"]["watermark"]["refunds_through"] == "2026-09-21T00:00:00Z"
    # 支付水位等号由原A已覆盖，不再创建同输入正例。
    assert data["context"]["watermark"]["payments_through"] == data["context"]["windows"]["current"]["end"]
    actual = _calculate(data)
    frozen = region_fixture[1]["cases"]["RG02.A"]
    _assert_frozen(actual, frozen)
    _assert_refund_control_sources_and_conservation(actual, data, frozen["evidence"])


def test_region_reference_absent_region_has_no_fabricated_zero_rate_row(region_fixture):
    data = _variant(region_fixture, "RG02.Q")
    assert data["context"]["filters"]["region_ids"] == []
    # 人工台账§6 Q：只停用两笔SE基期支付；保留原始退款，按支付队列排除。
    frozen = copy.deepcopy(region_fixture[1]["cases"]["RG02.A"])
    expected = frozen["expected"]
    expected["metrics"]["baseline"] = {"N": 3, "U": 1, "rate": "1/3"}
    expected["metrics"]["absolute_change_ratio"] = "1/3"
    expected["metrics"]["relative_change"] = "1"
    expected["candidate_order_ids"]["baseline"] = copy.deepcopy(expected["group_order_ids"]["baseline"]["region_northwest"])
    expected["group_order_ids"]["baseline"].pop("region_southeast")
    expected["group_refunded_order_ids"]["baseline"].pop("region_southeast")
    expected["aggregate_rows"] = [row for row in expected["aggregate_rows"] if (
        row["window_index"], row["group_id"]
    ) != (0, "region_southeast")]
    for row in expected["aggregate_rows"]:
        if row["window_index"] == 0 and row["dimension_id"] is None:
            row.update(paid_orders=3, refunded_orders=1, rate="1/3")
    evidence = frozen["evidence"]
    for field in ("group_cohort_source_row_ids", "group_refund_event_ids", "group_refund_source_row_ids"):
        evidence[field]["baseline"].pop("region_southeast")
    evidence["counted_refund_order_ids"]["baseline"].remove("K11-S-B-W1")
    actual = _calculate(data)
    _assert_frozen(actual, frozen)
    assert len(actual["aggregate_rows"]) == 5
    assert set(actual["group_order_ids"]["baseline"]) == {"region_northwest"}
    assert set(actual["group_order_ids"]["current"]) == {"region_northwest", "region_southeast"}
    assert "region_southeast" not in actual["group_refunded_order_ids"]["baseline"]
    assert any(row["refund_id"] == "KR11-S-B-W1" for row in data["refunds"])
    _assert_refund_control_sources_and_conservation(actual, data, evidence)


@pytest.mark.parametrize("variant_id", ("RG04.product-ready", "RG04.product-immature"))
def test_region_reference_rejects_critical_product_join_outside_filter(region_fixture, variant_id):
    with pytest.raises(ValueError) as error:
        _calculate(_variant(region_fixture, variant_id))
    message = str(error.value)
    for value in ("K11-S-C-A1", "r11-order-s-c-app-1", "domain_a", "fixture_single_region_channel_v1_draft", "product_rg04_missing"):
        assert value in message


@pytest.mark.parametrize(("catalog", "id_field"), (("regions", "region_id"), ("products", "product_id")))
def test_region_reference_rejects_duplicate_catalog_full_keys(region_fixture, catalog, id_field):
    # 矩阵§3：W中SE目录同样必须核验，重复完整键不能被字典覆盖。
    data = _variant(region_fixture, f"RG04.duplicate-{catalog}")
    assert data["context"]["filters"]["region_ids"] == ["region_northwest"]
    entries = data["dimensions"][catalog]
    duplicate = entries[-1]
    key = duplicate["domain_id"], duplicate["snapshot_id"], duplicate[id_field]
    matches = [row for row in entries if (row["domain_id"], row["snapshot_id"], row[id_field]) == key]
    assert len(matches) == 2
    assert len({row["source_row_id"] for row in matches}) == 2
    if catalog == "regions":
        assert duplicate[id_field] == "region_southeast"
        assert duplicate[id_field] not in data["context"]["filters"]["region_ids"]
    with pytest.raises(ValueError) as error:
        _calculate(data)
    message = str(error.value)
    assert "重复目录主键" in message
    assert id_field in message
    assert repr(key) in message


@pytest.mark.parametrize(("catalog", "id_field"), (("regions", "region_id"), ("products", "product_id")))
@pytest.mark.parametrize("scope_field", ("domain_id", "snapshot_id"))
def test_region_reference_rejects_foreign_catalog_scope(region_fixture, catalog, id_field, scope_field):
    # 矩阵§3：合法行保留，只追加同裸ID、不同Scope的故障行，不掺入第二种故障。
    data = _variant(region_fixture, f"RG04.foreign-{catalog}-{scope_field}")
    assert data["context"]["filters"]["region_ids"] == ["region_northwest"]
    entries = data["dimensions"][catalog]
    foreign = entries[-1]
    scope = data["context"]["domain_id"], data["context"]["snapshot_id"]
    local, = [row for row in entries if (
        row["domain_id"], row["snapshot_id"], row[id_field]
    ) == (*scope, foreign[id_field])]
    assert foreign[id_field] == local[id_field]
    assert foreign[scope_field] != local[scope_field]
    other_scope_field = "snapshot_id" if scope_field == "domain_id" else "domain_id"
    assert foreign[other_scope_field] == local[other_scope_field]
    assert foreign["source_row_id"] != local["source_row_id"]
    key = foreign["domain_id"], foreign["snapshot_id"], foreign[id_field]
    assert key != (*scope, local[id_field])
    assert len({(row["domain_id"], row["snapshot_id"], row[id_field]) for row in entries}) == len(entries)
    if catalog == "regions":
        assert foreign[id_field] == "region_southeast"
        assert foreign[id_field] not in data["context"]["filters"]["region_ids"]
    with pytest.raises(ValueError) as error:
        _calculate(data)
    message = str(error.value)
    assert "目录域或快照与固定输入范围不一致" in message
    assert id_field in message
    assert repr(key) in message


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
