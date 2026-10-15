import json
from datetime import datetime
from fractions import Fraction
from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "order_boundaries"
FIXTURE_FILES = (
    "01_maturity_watermark.json",
    "02_utc_boundaries.json",
    "03_duplicate_orders.json",
    "04_zero_denominator_window.json",
    "05_single_region_filter.json",
)


def assert_cohort_arithmetic(values: dict, rate_key: str = "rate") -> None:
    """复核静态计数及比率；零分母不参与除法。"""
    assert type(values["N"]) is int and values["N"] >= 0
    assert type(values["U"]) is int and 0 <= values["U"] <= values["N"]
    if values["N"] == 0:
        assert values[rate_key] is None
    else:
        assert Fraction(values[rate_key]) == Fraction(values["U"], values["N"])


def assert_expected_arithmetic(expected: dict) -> None:
    """只复核已静态填写的数值，不从业务输入计算预期。"""
    for values in expected.get("diagnostic_cohort_metrics", {}).values():
        assert_cohort_arithmetic(values)

    counterexample = expected.get("unfiltered_counterexample")
    if counterexample is not None:
        for window in ("baseline", "current"):
            assert_cohort_arithmetic(counterexample[window], "rate_fraction")
        baseline_rate = Fraction(counterexample["baseline"]["rate_fraction"])
        change = Fraction(counterexample["current"]["rate_fraction"]) - baseline_rate
        assert Fraction(counterexample["absolute_change_fraction"]) == change
        assert Fraction(counterexample["relative_change_fraction"]) == change / baseline_rate

    metrics = expected["metrics"]
    if expected["outcome"] != "ready":
        for window in ("baseline", "current"):
            assert metrics[window] == {"N": None, "U": None, "rate": None}
        assert metrics["absolute_change_ratio"] is None
        assert metrics["relative_change"] is None
        return

    for window in ("baseline", "current"):
        values = metrics[window]
        assert_cohort_arithmetic(values)
        assert values["N"] > 0
    baseline_rate = Fraction(metrics["baseline"]["rate"])
    change = Fraction(metrics["current"]["rate"]) - baseline_rate
    assert Fraction(metrics["absolute_change_ratio"]) == change
    if baseline_rate == 0:
        assert metrics["relative_change"] is None
    else:
        assert Fraction(metrics["relative_change"]) == change / baseline_rate


@pytest.mark.parametrize("filename", FIXTURE_FILES)
def test_boundary_fixture_is_complete_and_expected_arithmetic_is_consistent(
    filename: str,
) -> None:
    fixture = json.loads((FIXTURE_DIR / filename).read_text(encoding="utf-8"))
    assert fixture["synthetic"] is True
    assert fixture["metric_version"] is None
    assert fixture["business_rules"] and fixture["calculation_basis"]
    assert (FIXTURE_DIR / fixture["oracle_record"]).is_file()
    for source in fixture["sources"]:
        assert (FIXTURE_DIR / source["path"]).is_file()
        assert source["sections"]

    data = fixture["input"]
    context = data["context"]
    source_ids = []
    for collection in ("orders", "refunds"):
        for row in data[collection]:
            source_ids.append(row["source_row_id"])
            assert row["domain_id"] == context["domain_id"]
            assert row["snapshot_id"] == context["snapshot_id"]
            time_field = "paid_at" if collection == "orders" else "refund_at"
            assert datetime.fromisoformat(row[time_field].replace("Z", "+00:00")).utcoffset() is not None
    assert len(set(source_ids)) == len(source_ids)
    for rows in data["dimensions"].values():
        for row in rows:
            assert row["domain_id"] == context["domain_id"]
            assert row["snapshot_id"] == context["snapshot_id"]

    expected = fixture["expected"]
    assert expected["outcome"] in ("ready", "insufficient_evidence", "blocked_by_quality")
    if expected["outcome"] == "ready":
        assert expected["reasons"] == []
    else:
        assert expected["reasons"]

    orders_by_source = {row["source_row_id"]: row for row in data["orders"]}
    orders_by_id = {row["order_id"]: row for row in data["orders"]}
    region_ids = context["filters"]["region_ids"]
    for window, row_ids in expected.get("cohort_source_row_ids", {}).items():
        assert len(row_ids) == len(set(row_ids))
        for row_id in row_ids:
            row = orders_by_source[row_id]
            assert row["is_payment_valid"] is True
            assert not region_ids or row["region_id"] in region_ids
        for order_id in expected.get("counted_refund_order_ids", {}).get(window, []):
            assert orders_by_id[order_id]["source_row_id"] in row_ids
        diagnostic = expected.get("diagnostic_cohort_metrics", {}).get(window)
        published = expected["metrics"][window]
        counts = diagnostic if diagnostic is not None else published
        if counts["N"] is not None:
            assert counts["N"] == len(row_ids)
            if "counted_refund_order_ids" in expected:
                refund_ids = expected["counted_refund_order_ids"][window]
                assert len(refund_ids) == len(set(refund_ids)) == counts["U"]
    if "empty_windows" in expected:
        assert expected["empty_windows"] == [
            window for window in ("baseline", "current")
            if expected["diagnostic_cohort_metrics"][window]["N"] == 0
        ]
    if "applied_filters" in expected:
        assert expected["applied_filters"] == context["filters"]
        assert len(region_ids) == 1
        assert set(region_ids) <= {
            row["region_id"] for row in data["dimensions"]["regions"]
        }
        excluded_rows = expected["excluded_by_region_source_row_ids"]
        for row_id in excluded_rows:
            assert orders_by_source[row_id]["region_id"] not in region_ids
        assert set(expected["excluded_order_ids"]) == {
            orders_by_source[row_id]["order_id"] for row_id in excluded_rows
        }
    assert_expected_arithmetic(expected)
    for variant in fixture.get("variants", []):
        assert variant["input_overrides"] and variant["calculation_basis"]
        assert_expected_arithmetic(variant["expected"])
