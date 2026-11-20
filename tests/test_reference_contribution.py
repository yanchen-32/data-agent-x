import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from reference.category_cohort import calculate_category_reference
from reference.contribution import calculate_contribution_reference


ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = ROOT / "reference/manual_checks/G0_M03_A3-08_v2_contribution_expected.json"
ORACLE_SHA256 = "8a583a41f4bb557c016fd1c548345d9f824ed1450911f6bf262252e0cf271a0d"


@pytest.fixture
def a3_08_contribution():
    raw = ORACLE_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORACLE_SHA256
    oracle = json.loads(raw)
    source = oracle["sources"]["fixture"]
    fixture_path = ROOT / source["path"]
    fixture_raw = fixture_path.read_bytes()
    assert hashlib.sha256(fixture_raw).hexdigest() == source["sha256"]
    data = json.loads(fixture_raw)["input"]
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == source["input_sha256"]
    assert data["context"] == oracle["context"]
    yield calculate_category_reference(data), oracle
    assert ORACLE_PATH.read_bytes() == raw
    assert fixture_path.read_bytes() == fixture_raw


def test_a3_08_v2_matches_frozen_contribution_oracle(a3_08_contribution):
    grouped, oracle = a3_08_contribution
    before = copy.deepcopy(grouped)
    actual = calculate_contribution_reference(grouped, dimension_id="category")
    expected = oracle["expected"]

    assert actual["dimension_id"] == oracle["dimension_id"]
    assert actual["unit"] == oracle["unit"]
    assert actual["group_lifecycle"] == expected["group_lifecycle"]
    assert set(actual["groups"]) == set(expected["groups"])
    for gid, frozen in expected["groups"].items():
        windows = {
            window: {
                "N": row["N"],
                "U": row["U"],
                **{field: Fraction(row[field]) for field in ("weight", "rate", "weighted_rate")},
            }
            for window, row in frozen["windows"].items()
        }
        result = actual["groups"][gid]
        assert result == {
            "windows": windows,
            "contributions": {term: Fraction(value) for term, value in frozen["contributions"].items()},
            "net_contribution": Fraction(frozen["net_contribution"]),
        }
        assert all(
            isinstance(row[field], Fraction)
            for row in result["windows"].values()
            for field in ("weight", "rate", "weighted_rate")
        )
        assert all(isinstance(value, Fraction) for value in result["contributions"].values())
        assert isinstance(result["net_contribution"], Fraction)

    frozen_totals = expected["totals"]
    actual_totals = actual["totals"]
    for window in ("baseline", "current"):
        metric = frozen_totals[window]
        assert actual_totals[window] == {**metric, "rate": Fraction(metric["rate"])}
        assert isinstance(actual_totals[window]["rate"], Fraction)
    assert actual_totals["contributions"] == {
        term: Fraction(value) for term, value in frozen_totals["contributions"].items()
    }
    assert all(isinstance(value, Fraction) for value in actual_totals["contributions"].values())
    for field in ("contribution_sum", "absolute_change_ratio", "residual"):
        assert actual_totals[field] == Fraction(frozen_totals[field])
        assert isinstance(actual_totals[field], Fraction)
    assert grouped == before
    actual["groups"]["category_a"]["windows"]["baseline"]["N"] = 99
    assert grouped == before


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("outcome",), "insufficient_evidence", "可比"),
        (("reasons",), ["观察期未成熟"], "可比"),
        (("quality_checks", "all_orders_mature"), False, "成熟期及两类水位"),
        (("quality_checks", "payments_watermark_covered"), False, "成熟期及两类水位"),
        (("quality_checks", "refunds_watermark_covered"), False, "成熟期及两类水位"),
        (("truncated",), True, "未截断"),
        (("complete",), False, "完整"),
        (("aggregate_rows", 1, "window_index"), False, "window_index"),
        (("aggregate_rows", 1, "dimension_id"), "channel", "指定单维度"),
        (("aggregate_rows", 1, "group_id"), "", "非空组 ID"),
        (("aggregate_rows", 1, "paid_orders"), 0, "计数"),
        (("aggregate_rows", 1, "paid_orders"), True, "计数"),
        (("aggregate_rows", 1, "refunded_orders"), -1, "计数"),
        (("aggregate_rows", 1, "refunded_orders"), 3, "计数"),
        (("aggregate_rows", 1, "rate"), Fraction(1, 2), "与 U/N 一致"),
        (("metrics", "baseline", "rate"), 0.5, "Fraction"),
        (("metrics", "absolute_change_ratio"), Fraction(1, 3), "总体变化"),
    ],
)
def test_rejects_invalid_aggregate_fields(a3_08_contribution, path, value, message):
    grouped, _ = a3_08_contribution
    row = grouped
    for field in path[:-1]:
        row = row[field]
    row[path[-1]] = value
    before = copy.deepcopy(grouped)
    with pytest.raises(ValueError, match=message):
        calculate_contribution_reference(grouped, dimension_id="category")
    assert grouped == before


@pytest.mark.parametrize(
    ("index", "duplicates", "message"),
    [
        pytest.param(0, True, "重复聚合行", id="duplicate-total"),
        pytest.param(1, True, "重复聚合行", id="duplicate-group-id"),
        pytest.param(0, False, "缺少窗口聚合总计行", id="missing-total"),
        pytest.param(1, False, "分组 N", id="missing-group"),
    ],
)
def test_rejects_duplicate_or_incomplete_rows(a3_08_contribution, index, duplicates, message):
    grouped, _ = a3_08_contribution
    rows = grouped["aggregate_rows"]
    if duplicates:
        duplicate = rows[index].copy()
        if duplicate["dimension_id"] is not None:
            duplicate["group_label"] = "另一个显示名"
        rows.append(duplicate)
    else:
        rows.pop(index)
    with pytest.raises(ValueError, match=message):
        calculate_contribution_reference(grouped, dimension_id="category")


@pytest.mark.parametrize(
    ("counts", "message"),
    [
        pytest.param({"paid_orders": 3, "rate": Fraction(0)}, "分组 N", id="N-only"),
        pytest.param({"refunded_orders": 1, "rate": Fraction(1, 2)}, "分组 U", id="U-only"),
    ],
)
def test_rejects_nonconservation_with_all_rows_present(a3_08_contribution, counts, message):
    grouped, _ = a3_08_contribution
    category_a = grouped["aggregate_rows"][1]
    category_a.update(counts)
    with pytest.raises(ValueError, match=message):
        calculate_contribution_reference(grouped, dimension_id="category")


def test_rejects_total_row_that_disagrees_with_metrics(a3_08_contribution):
    grouped, _ = a3_08_contribution
    grouped["aggregate_rows"][0].update(paid_orders=5, rate=Fraction(2, 5))
    with pytest.raises(ValueError, match="聚合总计行与 metrics 不一致"):
        calculate_contribution_reference(grouped, dimension_id="category")


@pytest.mark.parametrize(("index", "window"), [(0, "baseline"), (1, "current")], ids=["baseline", "current"])
def test_rejects_zero_total_denominator_even_if_marked_ready(a3_08_contribution, index, window):
    grouped, _ = a3_08_contribution
    # 空窗省略所有组行，并让 metrics 与聚合总计行的 N/U 同为 0。
    grouped["metrics"][window].update(N=0, U=0, rate=None)
    grouped["metrics"].update(absolute_change_ratio=None, relative_change=None)
    rows = grouped["aggregate_rows"]
    rows[:] = [
        row for row in rows
        if row["window_index"] != index or row["dimension_id"] is None
    ]
    total = next(row for row in rows if row["window_index"] == index)
    total.update(paid_orders=0, refunded_orders=0, rate=None)
    before = copy.deepcopy(grouped)

    with pytest.raises(ValueError, match=rf"N > 0.*{window}"):
        calculate_contribution_reference(grouped, dimension_id="category")
    assert grouped == before


@pytest.mark.parametrize("dimension", ["region", "channel"])
def test_all_groups_turn_over_with_zero_baseline_and_unknown_entry(a3_08_contribution, dimension):
    grouped, _ = a3_08_contribution
    for row in grouped["aggregate_rows"]:
        if row["window_index"] == 0:
            row.update(refunded_orders=0, rate=Fraction(0))
        if row["dimension_id"] is not None:
            row["dimension_id"] = dimension
            if row["window_index"] == 0 and row["group_id"] == "category_a":
                row["group_id"] = "baseline_only"
            if row["window_index"] == 1 and row["group_id"] == "category_c":
                row["group_id"] = "__unknown__"
    grouped["metrics"]["baseline"].update(U=0, rate=Fraction(0))
    grouped["metrics"].update(absolute_change_ratio=Fraction(1), relative_change=None)
    grouped["aggregate_rows"].reverse()

    result = calculate_contribution_reference(grouped, dimension_id=dimension)
    assert result["group_lifecycle"] == {
        "shared": [], "entry": ["__unknown__", "category_a"], "exit": ["baseline_only", "category_b"],
    }
    assert result["groups"]["__unknown__"]["contributions"] == {"entry": Fraction(3, 4)}
    assert result["groups"]["baseline_only"]["contributions"] == {"exit": Fraction(0)}
    assert result["totals"]["contributions"] == {
        "within": Fraction(0), "structure": Fraction(0), "entry": Fraction(1), "exit": Fraction(0),
    }
    assert result["totals"]["absolute_change_ratio"] == Fraction(1)
    assert result["totals"]["residual"] == Fraction(0)
