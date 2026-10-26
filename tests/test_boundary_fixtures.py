import json
from datetime import datetime, timedelta
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
    "06_multiple_refunds_per_order.json",
    "07_same_label_distinct_category_ids.json",
    "08_category_entry_exit.json",
    "08_category_entry_exit.v1.json",
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
    if "qualifying_refund_event_ids" in expected:
        refunds_by_id = {row["refund_id"]: row for row in data["refunds"]}
        assert len(refunds_by_id) == len(data["refunds"])
        horizon = timedelta(seconds=context["horizon_seconds"])
        as_of = datetime.fromisoformat(context["as_of"].replace("Z", "+00:00"))
        for window, event_ids in expected["qualifying_refund_event_ids"].items():
            count = expected["qualifying_refund_event_counts"][window]
            assert type(count) is int
            assert len(event_ids) == len(set(event_ids)) == count
            assert {
                refunds_by_id[event_id]["order_id"] for event_id in event_ids
            } == set(expected["counted_refund_order_ids"][window])
            for event_id in event_ids:
                refund = refunds_by_id[event_id]
                order = orders_by_id[refund["order_id"]]
                assert order["source_row_id"] in expected["cohort_source_row_ids"][window]
                assert refund["status"] == "success"
                paid_at = datetime.fromisoformat(order["paid_at"].replace("Z", "+00:00"))
                refund_at = datetime.fromisoformat(refund["refund_at"].replace("Z", "+00:00"))
                assert paid_at <= refund_at <= paid_at + horizon
                assert refund_at <= as_of
    assert_expected_arithmetic(expected)
    for variant in fixture.get("variants", []):
        assert variant["input_overrides"] and variant["calculation_basis"]
        assert_expected_arithmetic(variant["expected"])


def test_same_label_category_fixture_preserves_ids_sources_and_totals() -> None:
    """核对静态分组台账与输入约束，不生成预期或调用业务计算器。"""
    fixture = json.loads(
        (FIXTURE_DIR / "07_same_label_distinct_category_ids.json").read_text(encoding="utf-8")
    )
    data, expected = fixture["input"], fixture["expected"]
    context = data["context"]

    def key(row: dict, field: str) -> tuple[str, str, str]:
        return row["domain_id"], row["snapshot_id"], row[field]

    def utc(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    products = {key(row, "product_id"): row for row in data["dimensions"]["products"]}
    categories = {key(row, "category_id"): row for row in data["dimensions"]["categories"]}
    orders = {row["source_row_id"]: row for row in data["orders"]}
    assert len(products) == len(data["dimensions"]["products"]) == 2
    assert len(categories) == len(data["dimensions"]["categories"]) == 2
    assert len({key(row, "order_id") for row in orders.values()}) == len(orders) == 6
    assert {row["category_id"] for row in categories.values()} == {"category_a", "category_b"}
    assert {row["label"] for row in categories.values()} == {"图书"}
    assert set(expected["group_cohort_source_row_ids"]) == {"category_a", "category_b"}
    assert len(expected["aggregate_rows"]) == 6
    assert {row["window_index"] for row in expected["aggregate_rows"]} == {0, 1}

    all_sources = []
    for index, window in enumerate(("baseline", "current")):
        rows = [row for row in expected["aggregate_rows"] if row["window_index"] == index]
        assert len(rows) == 3
        totals = [row for row in rows if row["dimension_id"] is None]
        groups = [row for row in rows if row["dimension_id"] == "category"]
        assert len(totals) == 1 and len(groups) == 2
        assert {row["group_id"] for row in groups} == {"category_a", "category_b"}
        assert totals[0]["group_id"] is None and totals[0]["group_label"] is None
        assert totals[0]["paid_orders"] == expected["metrics"][window]["N"]
        assert totals[0]["refunded_orders"] == expected["metrics"][window]["U"]
        assert totals[0]["rate"] == expected["metrics"][window]["rate"]
        for field in ("paid_orders", "refunded_orders"):
            assert sum(row[field] for row in groups) == totals[0][field]
        for row in rows:
            assert set(row) == {
                "window_index", "dimension_id", "group_id", "group_label",
                "paid_orders", "refunded_orders", "rate",
            }
            assert_cohort_arithmetic({
                "N": row["paid_orders"], "U": row["refunded_orders"], "rate": row["rate"],
            })

        sources = []
        for group in groups:
            group_id = group["group_id"]
            category_key = context["domain_id"], context["snapshot_id"], group_id
            assert group["group_label"] == categories[category_key]["label"]
            source_ids = expected["group_cohort_source_row_ids"][group_id][window]
            assert group["paid_orders"] == len(source_ids) > 0
            group_order_ids = {orders[source_id]["order_id"] for source_id in source_ids}
            assert group["refunded_orders"] == len(
                group_order_ids & set(expected["counted_refund_order_ids"][window])
            )
            for source_id in source_ids:
                order = orders[source_id]
                assert products[key(order, "product_id")]["category_id"] == group_id
                paid_at = utc(order["paid_at"])
                assert order["is_payment_valid"] is True
                assert utc(context["windows"][window]["start"]) <= paid_at < utc(
                    context["windows"][window]["end"]
                )
                mature_at = paid_at + timedelta(seconds=context["horizon_seconds"])
                assert mature_at <= utc(context["as_of"])
                assert mature_at <= utc(context["watermark"]["refunds_through"])
            sources.extend(source_ids)
        assert len(sources) == len(set(sources))
        assert set(sources) == set(expected["cohort_source_row_ids"][window])
        assert utc(context["watermark"]["payments_through"]) >= utc(
            context["windows"][window]["end"]
        )
        all_sources.extend(sources)
    assert len(all_sources) == len(set(all_sources)) == len(orders)
    assert set(all_sources) == set(orders)


@pytest.mark.parametrize(
    ("window", "category_id", "order_sources", "refund_sources"),
    [
        ("baseline", "category_a", ("r07-row-a-b1",), ()),
        ("baseline", "category_b", ("r07-row-b-b1",), ("r07-refund-b-b1",)),
        (
            "current", "category_a",
            ("r07-row-a-c1", "r07-row-a-c2"), ("r07-refund-a-c1",),
        ),
        ("current", "category_b", ("r07-row-b-c1", "r07-row-b-c2"), ()),
    ],
    ids=("baseline-category-a", "baseline-category-b", "current-category-a", "current-category-b"),
)
def test_same_label_category_group_refunds_trace_to_source_rows(
    window: str,
    category_id: str,
    order_sources: tuple[str, ...],
    refund_sources: tuple[str, ...],
) -> None:
    """按人工台账核验四组来源；本例原始退款均合格，不实现通用筛选器。"""
    fixture = json.loads(
        (FIXTURE_DIR / "07_same_label_distinct_category_ids.json").read_text(encoding="utf-8")
    )
    data, expected = fixture["input"], fixture["expected"]
    orders = {row["source_row_id"]: row for row in data["orders"]}
    group_orders = [orders[source_id] for source_id in order_sources]
    group_keys = {
        (row["domain_id"], row["snapshot_id"], row["order_id"]) for row in group_orders
    }
    assert set(expected["group_cohort_source_row_ids"][category_id][window]) == set(order_sources)
    refunds = [
        row for row in data["refunds"]
        if (row["domain_id"], row["snapshot_id"], row["order_id"]) in group_keys
    ]
    assert {row["source_row_id"] for row in refunds} == set(refund_sources)
    assert len(refunds) == len(refund_sources)
    assert all(row["status"] == "success" for row in refunds)
    assert {row["refund_id"] for row in refunds} <= set(
        expected["qualifying_refund_event_ids"][window]
    )
    refunded_keys = {
        (row["domain_id"], row["snapshot_id"], row["order_id"]) for row in refunds
    }
    window_index = {"baseline": 0, "current": 1}[window]
    groups = [
        row for row in expected["aggregate_rows"]
        if (row["window_index"], row["dimension_id"], row["group_id"])
        == (window_index, "category", category_id)
    ]
    assert len(groups) == 1
    assert groups[0]["paid_orders"] == len(group_orders)
    assert groups[0]["refunded_orders"] == len(refunded_keys)
    assert Fraction(groups[0]["rate"]) == Fraction(len(refunded_keys), len(group_orders))


@pytest.mark.parametrize(
    "filename,order_count",
    [("08_category_entry_exit.v1.json", 6), ("08_category_entry_exit.json", 8)],
    ids=("frozen-v1", "draft-v2"),
)
def test_entry_exit_fixture_has_only_present_groups_and_consistent_static_totals(
    filename: str, order_count: int,
) -> None:
    """核对A3-08静态台账和分类，不调用参考计算器或生成预期。"""
    fixture = json.loads((FIXTURE_DIR / filename).read_text(encoding="utf-8"))
    data, expected = fixture["input"], fixture["expected"]
    context = data["context"]

    def key(row: dict, field: str) -> tuple[str, str, str]:
        return row["domain_id"], row["snapshot_id"], row[field]

    def utc(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    products = {key(row, "product_id"): row for row in data["dimensions"]["products"]}
    categories = {key(row, "category_id"): row for row in data["dimensions"]["categories"]}
    orders = {row["source_row_id"]: row for row in data["orders"]}
    assert len(products) == len(data["dimensions"]["products"]) == 3
    assert len(categories) == len(data["dimensions"]["categories"]) == 3
    assert len({key(row, "order_id") for row in orders.values()}) == len(orders) == order_count
    registered = {row["category_id"] for row in categories.values()}
    assert registered == {"category_a", "category_b", "category_c"}
    rows = expected["aggregate_rows"]
    assert len(rows) == len({
        (row["window_index"], row["dimension_id"], row["group_id"]) for row in rows
    }) == 6
    assert {row["window_index"] for row in rows} == {0, 1}
    present, all_sources = {}, []
    for index, window in enumerate(("baseline", "current")):
        totals = [row for row in rows if row["window_index"] == index and row["dimension_id"] is None]
        groups = [row for row in rows if row["window_index"] == index and row["dimension_id"] == "category"]
        assert len(totals) == 1 and len(groups) == 2
        assert totals[0]["group_id"] is None and totals[0]["group_label"] is None
        present[window] = {row["group_id"] for row in groups}
        assert set(expected["absent_group_ids"][window]) == registered - present[window]
        for absent in expected["absent_group_ids"][window]:
            assert window not in expected["group_cohort_source_row_ids"][absent]
            assert window not in expected["group_refund_source_row_ids"][absent]
        sources = []
        for group in groups:
            group_id = group["group_id"]
            assert group["group_label"] == categories[
                (context["domain_id"], context["snapshot_id"], group_id)
            ]["label"]
            source_ids = expected["group_cohort_source_row_ids"][group_id][window]
            assert len(source_ids) == group["paid_orders"] > 0
            group_orders = [orders[source_id] for source_id in source_ids]
            group_order_keys = {key(row, "order_id") for row in group_orders}
            refunds = [row for row in data["refunds"] if key(row, "order_id") in group_order_keys]
            assert {row["source_row_id"] for row in refunds} == set(
                expected["group_refund_source_row_ids"][group_id][window]
            )
            assert group["refunded_orders"] == len({key(row, "order_id") for row in refunds})
            assert_cohort_arithmetic({
                "N": group["paid_orders"], "U": group["refunded_orders"], "rate": group["rate"],
            })
            for order in group_orders:
                assert products[key(order, "product_id")]["category_id"] == group_id
                paid_at = utc(order["paid_at"])
                assert order["is_payment_valid"] is True
                assert utc(context["windows"][window]["start"]) <= paid_at < utc(
                    context["windows"][window]["end"]
                )
                mature_at = paid_at + timedelta(seconds=context["horizon_seconds"])
                assert mature_at <= utc(context["as_of"])
                assert mature_at <= utc(context["watermark"]["refunds_through"])
            sources.extend(source_ids)
        assert len(sources) == len(set(sources))
        assert set(sources) == set(expected["cohort_source_row_ids"][window])
        for field, metric in (("paid_orders", "N"), ("refunded_orders", "U")):
            assert sum(row[field] for row in groups) == totals[0][field] == expected["metrics"][window][metric]
        assert Fraction(totals[0]["rate"]) == Fraction(expected["metrics"][window]["rate"])
        assert utc(context["watermark"]["payments_through"]) >= utc(context["windows"][window]["end"])
        all_sources.extend(sources)
    assert len(all_sources) == len(set(all_sources)) == len(orders)
    assert set(all_sources) == set(orders)
    assert expected["group_lifecycle"] == {
        "shared": sorted(present["baseline"] & present["current"]),
        "exit": sorted(present["baseline"] - present["current"]),
        "entry": sorted(present["current"] - present["baseline"]),
    } == {"shared": ["category_a"], "exit": ["category_b"], "entry": ["category_c"]}
    if "source_ledger" in fixture:
        ledger = json.loads((FIXTURE_DIR / fixture["source_ledger"]).read_text(encoding="utf-8"))
        assert ledger["fixture_revision"] == fixture["fixture_revision"] == "2"
        assert ledger["scope"]["domain_id"] == context["domain_id"]
        assert ledger["scope"]["snapshot_id"] == context["snapshot_id"]
        assert ledger["group_lifecycle"] == expected["group_lifecycle"]
        assert len(ledger["order_ledger"]) == len(orders) == 8
        assert {row["source_row_id"] for row in ledger["order_ledger"]} == set(orders)
        for row in ledger["order_ledger"]:
            raw = orders[row["source_row_id"]]
            for field in ("order_id", "product_id", "paid_at"):
                assert row[field] == raw[field]
            assert utc(row["matures_at"]) == utc(raw["paid_at"]) + timedelta(
                seconds=context["horizon_seconds"]
            )
            assert row["source_row_id"] in expected["group_cohort_source_row_ids"][
                row["category_id"]
            ][row["window"]]
            assert set(row["refund_source_row_ids"]) == {
                refund["source_row_id"] for refund in data["refunds"]
                if key(refund, "order_id") == key(raw, "order_id")
            }
        refunds_by_source = {row["source_row_id"]: row for row in data["refunds"]}
        assert len(ledger["refund_ledger"]) == len(refunds_by_source) == 6
        assert {row["source_row_id"] for row in ledger["refund_ledger"]} == set(refunds_by_source)
        for row in ledger["refund_ledger"]:
            raw = refunds_by_source[row["source_row_id"]]
            for field in ("refund_id", "order_id", "refund_at"):
                assert row[field] == raw[field]
            assert row["source_row_id"] in expected["group_refund_source_row_ids"][
                row["category_id"]
            ][row["window"]]
        assert len(ledger["aggregate_rows"]) == len(rows)
        for manual, static in zip(ledger["aggregate_rows"], rows):
            assert {k: v for k, v in manual.items() if k != "rate_fraction"} == {
                k: v for k, v in static.items() if k != "rate"
            }
            assert Fraction(manual["rate_fraction"]) == Fraction(static["rate"])
