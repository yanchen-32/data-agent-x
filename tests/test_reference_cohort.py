import copy
import hashlib
import json
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

import pytest

from reference.cohort import calculate_reference


ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "order_boundaries"
MANUAL_RECORD = ROOT / "reference" / "manual_checks" / "2026-10-14.json"


def assert_matches_static_expected(actual: dict, expected: dict) -> None:
    assert actual["outcome"] == expected["outcome"]
    assert actual["reasons"] == expected["reasons"]
    for check, value in actual["quality_checks"].items():
        assert value == expected["quality_checks"][check]
    for window in ("baseline", "current"):
        observed, wanted = actual["metrics"][window], expected["metrics"][window]
        assert observed["N"] == wanted["N"]
        assert observed["U"] == wanted["U"]
        assert observed["rate"] == (Fraction(wanted["rate"]) if wanted["rate"] is not None else None)
    for key in ("absolute_change_ratio", "relative_change"):
        wanted = expected["metrics"][key]
        assert actual["metrics"][key] == (Fraction(wanted) if wanted is not None else None)


@pytest.mark.parametrize("filename", ["01_maturity_watermark.json", "02_utc_boundaries.json"])
def test_reference_matches_precomputed_manual_record_and_fixture(filename: str) -> None:
    fixture = json.loads((FIXTURE_DIR / filename).read_text(encoding="utf-8"))
    manual = json.loads(MANUAL_RECORD.read_text(encoding="utf-8"))["cases"][filename]
    data = fixture["input"]
    original = copy.deepcopy(data)
    canonical_input = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical_input.encode()).hexdigest() == manual["input_sha256"]

    actual = calculate_reference(data)

    assert data == original
    assert actual["candidate_order_ids"] == manual["candidate_order_ids"]
    assert {window: len(ids) for window, ids in actual["candidate_order_ids"].items()} == manual["candidate_N"]
    assert_matches_static_expected(actual, manual)
    assert_matches_static_expected(actual, fixture["expected"])


@pytest.mark.parametrize("variant_index", [0, 1], ids=["watermark_equal", "as_of_one_microsecond_early"])
def test_reference_matches_existing_control_variant(variant_index: int) -> None:
    fixture = json.loads((FIXTURE_DIR / "01_maturity_watermark.json").read_text(encoding="utf-8"))
    variant = fixture["variants"][variant_index]
    data = copy.deepcopy(fixture["input"])
    for path, value in variant["input_overrides"].items():
        keys = path.split(".")
        target = data
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value

    assert_matches_static_expected(calculate_reference(data), variant["expected"])


def test_reference_rejects_duplicate_orders_instead_of_silent_deduplication() -> None:
    fixture = json.loads((FIXTURE_DIR / "03_duplicate_orders.json").read_text(encoding="utf-8"))

    with pytest.raises(ValueError, match="重复订单主键"):
        calculate_reference(fixture["input"])


def test_reference_blocks_empty_cohorts_instead_of_dividing_by_zero() -> None:
    fixture = json.loads((FIXTURE_DIR / "02_utc_boundaries.json").read_text(encoding="utf-8"))
    data = fixture["input"]
    data["orders"] = []
    data["refunds"] = []

    result = calculate_reference(data)

    assert result["outcome"] == "insufficient_evidence"
    assert result["reasons"] == ["支付窗口无有效样本"]
    assert result["metrics"]["baseline"]["rate"] is None
    assert result["metrics"]["current"]["rate"] is None


def assert_a3_04_input_diagnostics(
    data: dict, expected: dict, reviewed_candidates: dict[str, list[str]]
) -> None:
    """仅核对固定A3-04的诊断；不读取参考函数结果，不生成或回填Oracle。"""
    def instant(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    context = data["context"]
    assert context["filters"] == {"region_ids": []}
    scope = (context["domain_id"], context["snapshot_id"])
    for row in data["orders"] + data["refunds"]:
        assert (row["domain_id"], row["snapshot_id"]) == scope
    horizon = timedelta(seconds=context["horizon_seconds"])
    as_of = instant(context["as_of"])

    for window, reviewed_ids in reviewed_candidates.items():
        bounds = context["windows"][window]
        start, end = instant(bounds["start"]), instant(bounds["end"])
        paid_orders = {
            row["order_id"]: instant(row["paid_at"])
            for row in data["orders"]
            if row["is_payment_valid"] is True
            and start <= instant(row["paid_at"]) < end
        }
        assert set(paid_orders) == set(reviewed_ids)
        refunded_orders = {
            row["order_id"] for row in data["refunds"]
            if row["order_id"] in paid_orders and row["status"] == "success"
            and paid_orders[row["order_id"]] <= instant(row["refund_at"])
            <= paid_orders[row["order_id"]] + horizon
            and instant(row["refund_at"]) <= as_of
        }
        assert refunded_orders == set(expected["counted_refund_order_ids"][window])
        n, u = len(paid_orders), len(refunded_orders)
        diagnostic = expected["diagnostic_cohort_metrics"][window]
        assert (n, u) == (diagnostic["N"], diagnostic["U"])
        rate = Fraction(u, n) if n else None
        wanted = diagnostic["rate"]
        assert rate == (Fraction(wanted) if wanted is not None else None)


@pytest.mark.parametrize(
    "filename, reviewed_candidates",
    [
        pytest.param(
            "04_zero_denominator_window.json",
            {"baseline": [], "current": ["Z-C-1", "Z-C-2"]},
            id="A3-04",
        ),
        pytest.param(
            "05_single_region_filter.json",
            {"baseline": ["F-N-B1", "F-N-B2"], "current": ["F-N-C1"]},
            id="A3-05",
        ),
    ],
)
def test_reference_matches_frozen_boundary_fixture(
    filename: str, reviewed_candidates: dict[str, list[str]]
) -> None:
    """实际发布结果对照冻结预期；A3-04诊断另用输入规则核对。"""
    fixture = json.loads((FIXTURE_DIR / filename).read_text(encoding="utf-8"))
    data = fixture["input"]
    original = copy.deepcopy(fixture)

    actual = calculate_reference(data)

    assert actual["candidate_order_ids"] == reviewed_candidates
    assert_matches_static_expected(actual, fixture["expected"])
    if fixture["case_id"] == "A3-04":
        assert actual["outcome"] == "insufficient_evidence"
        assert actual["reasons"] == ["支付窗口无有效样本"]
        for window in ("baseline", "current"):
            assert actual["metrics"][window] == {"N": None, "U": None, "rate": None}
        assert actual["metrics"]["absolute_change_ratio"] is None
        assert actual["metrics"]["relative_change"] is None
        assert_a3_04_input_diagnostics(data, fixture["expected"], reviewed_candidates)
    else:
        assert data["context"]["filters"] == {"region_ids": ["region_northwest"]}
        assert actual["metrics"]["baseline"] == {"N": 2, "U": 1, "rate": Fraction(1, 2)}
        assert actual["metrics"]["current"] == {"N": 1, "U": 1, "rate": Fraction(1)}
        assert actual["metrics"]["absolute_change_ratio"] == Fraction(1, 2)
        assert actual["metrics"]["relative_change"] == Fraction(1)
        for window in ("baseline", "current"):
            assert isinstance(actual["metrics"][window]["rate"], Fraction)
        for key in ("absolute_change_ratio", "relative_change"):
            assert isinstance(actual["metrics"][key], Fraction)
    assert fixture == original
