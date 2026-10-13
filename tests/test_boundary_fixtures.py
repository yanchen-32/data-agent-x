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
)


def assert_expected_arithmetic(expected: dict) -> None:
    """只复核已静态填写的数值，不从业务输入计算预期。"""
    metrics = expected["metrics"]
    if expected["outcome"] != "ready":
        for window in ("baseline", "current"):
            assert metrics[window] == {"N": None, "U": None, "rate": None}
        assert metrics["absolute_change_ratio"] is None
        assert metrics["relative_change"] is None
        return

    for window in ("baseline", "current"):
        values = metrics[window]
        assert type(values["N"]) is int and values["N"] > 0
        assert type(values["U"]) is int and 0 <= values["U"] <= values["N"]
        assert Fraction(values["rate"]) == Fraction(values["U"], values["N"])
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
    assert_expected_arithmetic(expected)
    for variant in fixture.get("variants", []):
        assert variant["input_overrides"] and variant["calculation_basis"]
        assert_expected_arithmetic(variant["expected"])
