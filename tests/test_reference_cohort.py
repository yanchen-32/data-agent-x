import copy
import hashlib
import json
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
