import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from reference.category_cohort import calculate_category_reference
from reference.cohort import calculate_reference


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "order_boundaries"
    / "07_same_label_distinct_category_ids.json"
)


@pytest.fixture
def category_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def entry_exit_fixture() -> dict:
    """旧计算回归固定读取v1；当前v2输入另做静态核验，不混用预期。"""
    return json.loads(
        (FIXTURE_PATH.parent / "08_category_entry_exit.v1.json").read_text(encoding="utf-8")
    )


def category_rows(result: dict, index: int) -> dict:
    return {
        row["group_id"]: row for row in result["aggregate_rows"]
        if row["window_index"] == index and row["dimension_id"] == "category"
    }


def assert_partition(result: dict) -> None:
    """检查实际归组台账互斥穷尽，且计数与实际总计一致。"""
    for index, window in enumerate(("baseline", "current")):
        rows = category_rows(result, index)
        totals = [
            row for row in result["aggregate_rows"]
            if row["window_index"] == index and row["dimension_id"] is None
        ]
        assert len(totals) == 1
        total = totals[0]
        assert total["group_id"] is None and total["group_label"] is None
        paid, refunded = [], []
        for group_id, row in rows.items():
            members = result["group_order_ids"][window][group_id]
            refunds = result["group_refunded_order_ids"][window][group_id]
            assert set(refunds) <= set(members)
            assert row["paid_orders"] == len(members)
            assert row["refunded_orders"] == len(refunds)
            assert row["rate"] == Fraction(len(refunds), len(members))
            assert isinstance(row["rate"], Fraction)
            paid.extend(members)
            refunded.extend(refunds)
        assert len(paid) == len(set(paid)) == total["paid_orders"]
        assert set(paid) == set(result["candidate_order_ids"][window])
        assert len(refunded) == len(set(refunded)) == total["refunded_orders"]
        for field in ("paid_orders", "refunded_orders"):
            assert sum(row[field] for row in rows.values()) == total[field]
        assert total["rate"] == Fraction(total["refunded_orders"], total["paid_orders"])
        assert isinstance(total["rate"], Fraction)


def test_category_reference_matches_six_frozen_rows_and_manual_sources(category_fixture: dict) -> None:
    original = copy.deepcopy(category_fixture)
    data = category_fixture["input"]

    actual = calculate_category_reference(data)

    # 只在测试端将先行冻结的十进制字符串转为精确分数，不回写 Fixture。
    expected_rows = [
        {**row, "rate": Fraction(row["rate"])}
        for row in category_fixture["expected"]["aggregate_rows"]
    ]
    assert actual["outcome"] == "ready"
    assert actual["aggregate_rows"] == expected_rows
    assert len(actual["aggregate_rows"]) == 6
    assert sum(row["dimension_id"] == "category" for row in actual["aggregate_rows"]) == 4
    assert sum(row["dimension_id"] is None for row in actual["aggregate_rows"]) == 2
    assert_partition(actual)
    order_sources = {row["order_id"]: row["source_row_id"] for row in data["orders"]}
    for window in ("baseline", "current"):
        for group_id, ids in actual["group_order_ids"][window].items():
            assert {order_sources[order_id] for order_id in ids} == set(
                category_fixture["expected"]["group_cohort_source_row_ids"][group_id][window]
            )
    assert actual["group_refunded_order_ids"] == {
        "baseline": {"category_a": [], "category_b": ["S-B-B1"]},
        "current": {"category_a": ["S-A-C1"], "category_b": []},
    }
    for key, value in calculate_reference(data).items():
        assert actual[key] == value
    assert category_fixture == original


def test_category_reference_ignores_expected_and_input_order(category_fixture: dict) -> None:
    class InputOnly(dict):
        def __getitem__(self, key):
            if key == "expected":
                raise AssertionError("不得读取expected")
            return super().__getitem__(key)

        def get(self, key, default=None):
            if key == "expected":
                raise AssertionError("不得读取expected")
            return super().get(key, default)

    data = InputOnly(category_fixture["input"])
    before = calculate_category_reference(data)
    data["expected"] = {"aggregate_rows": "故意错误；禁止访问"}
    for collection in (data["orders"], data["refunds"], *data["dimensions"].values()):
        collection.reverse()

    actual = calculate_category_reference(data)

    for key in ("aggregate_rows", "group_order_ids", "group_refunded_order_ids"):
        assert actual[key] == before[key]


def test_product_association_not_display_name_controls_groups(category_fixture: dict) -> None:
    data = category_fixture["input"]
    products = data["dimensions"]["products"]
    products[0]["category_id"], products[1]["category_id"] = (
        products[1]["category_id"], products[0]["category_id"]
    )

    actual = calculate_category_reference(data)

    assert category_rows(actual, 0)["category_a"]["rate"] == Fraction(1)
    assert category_rows(actual, 0)["category_b"]["rate"] == Fraction(0)
    assert category_rows(actual, 1)["category_a"]["rate"] == Fraction(0)
    assert category_rows(actual, 1)["category_b"]["rate"] == Fraction(1, 2)
    assert_partition(actual)


@pytest.mark.parametrize("window_index", (0, 1), ids=("baseline", "current"))
def test_same_display_label_still_returns_two_distinct_category_groups(
    category_fixture: dict, window_index: int,
) -> None:
    actual = calculate_category_reference(category_fixture["input"])

    # 先检查原始行列表长度，再核对身份；不能用字典覆盖掩盖重复或丢组。
    groups = [
        row for row in actual["aggregate_rows"]
        if row["window_index"] == window_index and row["dimension_id"] == "category"
    ]
    assert len(groups) == 2
    assert {row["group_label"] for row in groups} == {"图书"}
    assert {(row["dimension_id"], row["group_id"]) for row in groups} == {
        ("category", "category_a"), ("category", "category_b"),
    }


@pytest.mark.parametrize(
    "labels",
    [
        {"category_a": "图书新版", "category_b": "图书"},
        {"category_a": "类别甲", "category_b": "类别乙"},
        {"category_a": "统一展示名", "category_b": "统一展示名"},
    ],
    ids=("rename-one", "rename-both-distinct", "rename-both-same"),
)
def test_label_rename_does_not_change_identity_or_counts(
    category_fixture: dict, labels: dict[str, str],
) -> None:
    original = copy.deepcopy(category_fixture)
    before = calculate_category_reference(category_fixture["input"])
    data = copy.deepcopy(category_fixture["input"])
    for category in data["dimensions"]["categories"]:
        category["label"] = labels[category["category_id"]]
    renamed_input = copy.deepcopy(data)

    actual = calculate_category_reference(data)

    # 所有六行都逐行比较；除了对应展示名外，身份、计数、精确率和总计均须不变。
    expected_rows = [
        {**row, "group_label": labels[row["group_id"]]}
        if row["dimension_id"] == "category" else row
        for row in before["aggregate_rows"]
    ]
    assert actual["aggregate_rows"] == expected_rows
    assert {
        key: value for key, value in actual.items() if key != "aggregate_rows"
    } == {
        key: value for key, value in before.items() if key != "aggregate_rows"
    }
    for row in actual["aggregate_rows"]:
        assert isinstance(row["rate"], Fraction)
    assert_partition(actual)
    assert data == renamed_input
    assert category_fixture == original


@pytest.mark.parametrize(
    "refund_at,status,wanted_u",
    [
        ("2026-09-09T00:00:00Z", "success", 1),
        ("2026-09-16T08:00:00+08:00", "success", 1),
        ("2026-09-16T00:00:00.000001Z", "success", 0),
        ("2026-09-11T00:00:00Z", "failed", 0),
    ],
    ids=("paid-inclusive", "horizon-inclusive-offset", "horizon-one-microsecond-late", "failed"),
)
def test_group_refunds_use_original_closed_observation_period(
    category_fixture: dict, refund_at: str, status: str, wanted_u: int,
) -> None:
    data = category_fixture["input"]
    data["refunds"][1].update(refund_at=refund_at, status=status)

    actual = calculate_category_reference(data)

    row = category_rows(actual, 1)["category_a"]
    assert (row["paid_orders"], row["refunded_orders"], row["rate"]) == (
        2, wanted_u, Fraction(wanted_u, 2)
    )
    assert_partition(actual)


def test_multiple_refund_events_still_count_one_group_order(category_fixture: dict) -> None:
    data = category_fixture["input"]
    data["refunds"].append({
        **data["refunds"][1], "refund_id": "SR-A-C1-SECOND",
        "source_row_id": "r07-refund-a-c1-second", "refund_at": "2026-09-12T00:00:00Z",
    })

    actual = calculate_category_reference(data)

    assert category_rows(actual, 1)["category_a"]["refunded_orders"] == 1
    assert actual["group_refunded_order_ids"]["current"]["category_a"] == ["S-A-C1"]
    assert_partition(actual)


def test_single_region_filters_denominator_and_refunds_before_grouping(category_fixture: dict) -> None:
    data = category_fixture["input"]
    data["orders"][-1]["region_id"] = "region_southeast"
    data["refunds"].append({
        **data["refunds"][1], "refund_id": "SR-SOUTHEAST", "order_id": "S-B-C2",
        "source_row_id": "r07-refund-southeast", "refund_at": "2026-09-14T00:00:00Z",
    })
    data["context"]["filters"]["region_ids"] = ["region_northwest"]

    actual = calculate_category_reference(data)

    rows = category_rows(actual, 1)
    assert (rows["category_b"]["paid_orders"], rows["category_b"]["refunded_orders"]) == (1, 0)
    assert actual["metrics"]["current"] == {"N": 3, "U": 1, "rate": Fraction(1, 3)}
    assert "S-B-C2" not in actual["candidate_order_ids"]["current"]
    assert_partition(actual)


@pytest.mark.parametrize("missing", ("product", "category_id"))
def test_unknown_category_preserves_orders_instead_of_dropping_them(
    category_fixture: dict, missing: str,
) -> None:
    data = category_fixture["input"]
    if missing == "product":
        data["dimensions"]["products"].pop(0)
    else:
        data["dimensions"]["products"][0]["category_id"] = None

    actual = calculate_category_reference(data)

    assert category_rows(actual, 0)["__unknown__"]["paid_orders"] == 1
    assert category_rows(actual, 1)["__unknown__"]["paid_orders"] == 2
    assert category_rows(actual, 1)["__unknown__"]["refunded_orders"] == 1
    assert_partition(actual)


def test_missing_display_catalog_preserves_known_category_id(category_fixture: dict) -> None:
    data = category_fixture["input"]
    data["dimensions"].pop("categories")

    actual = calculate_category_reference(data)

    assert set(category_rows(actual, 0)) == {"category_a", "category_b"}
    assert all(row["group_label"] is None for row in category_rows(actual, 0).values())
    assert_partition(actual)


@pytest.mark.parametrize("catalog", ("products", "categories"))
def test_duplicate_catalog_key_is_not_silently_overwritten(category_fixture: dict, catalog: str) -> None:
    data = category_fixture["input"]
    data["dimensions"][catalog].append(copy.deepcopy(data["dimensions"][catalog][0]))

    with pytest.raises(ValueError, match="重复目录主键"):
        calculate_category_reference(data)


@pytest.mark.parametrize("catalog", ("products", "categories"))
@pytest.mark.parametrize("field", ("domain_id", "snapshot_id"))
def test_catalog_id_without_matching_domain_and_snapshot_cannot_join(
    category_fixture: dict, catalog: str, field: str,
) -> None:
    data = category_fixture["input"]
    # 保持product_id/category_id相同，只改变域或快照，不能按单ID误关联。
    data["dimensions"][catalog][0][field] = "foreign_scope"

    with pytest.raises(ValueError, match="目录域或快照"):
        calculate_category_reference(data)


@pytest.mark.parametrize("block", ("immature", "payments", "refunds", "empty_baseline"))
def test_group_publication_inherits_overall_blocking_semantics(category_fixture: dict, block: str) -> None:
    data = category_fixture["input"]
    if block == "immature":
        data["context"]["as_of"] = "2026-09-18T23:59:59.999999Z"
    elif block == "payments":
        data["context"]["watermark"]["payments_through"] = "2026-09-14T23:59:59.999999Z"
    elif block == "refunds":
        data["context"]["watermark"]["refunds_through"] = "2026-09-18T23:59:59.999999Z"
    else:
        for row in data["orders"][:2]:
            row["is_payment_valid"] = False

    actual = calculate_category_reference(data)

    assert actual["outcome"] == "insufficient_evidence"
    assert actual["aggregate_rows"] == []
    assert actual["group_order_ids"] == actual["group_refunded_order_ids"] == {}
    for key, value in calculate_reference(data).items():
        assert actual[key] == value


def test_category_reference_a3_08_matches_frozen_rows_and_lifecycle(entry_exit_fixture: dict) -> None:
    """直接计算固定输入，对照先行人工预期，不补造参考函数未返回的分类字段。"""
    original = copy.deepcopy(entry_exit_fixture)
    data, expected = entry_exit_fixture["input"], entry_exit_fixture["expected"]

    actual = calculate_category_reference(data)

    expected_rows = [
        {**row, "rate": Fraction(row["rate"])} for row in expected["aggregate_rows"]
    ]
    assert actual["outcome"] == expected["outcome"] == "ready"
    assert actual["reasons"] == expected["reasons"] == []
    for check, value in actual["quality_checks"].items():
        assert value == expected["quality_checks"][check]
    assert actual["aggregate_rows"] == expected_rows
    assert len(actual["aggregate_rows"]) == 6
    assert sum(row["dimension_id"] == "category" for row in actual["aggregate_rows"]) == 4
    assert sum(row["dimension_id"] is None for row in actual["aggregate_rows"]) == 2
    assert_partition(actual)

    baseline, current = category_rows(actual, 0), category_rows(actual, 1)
    assert set(baseline) == {"category_a", "category_b"}
    assert set(current) == {"category_a", "category_c"}
    assert {
        (baseline["category_a"]["dimension_id"], baseline["category_a"]["group_id"]),
        (current["category_a"]["dimension_id"], current["category_a"]["group_id"]),
    } == {("category", "category_a")}
    # 分类只由实际出现组集合核对，不访问actual["group_lifecycle"]等不存在字段。
    assert {
        "shared": sorted(set(baseline) & set(current)),
        "exit": sorted(set(baseline) - set(current)),
        "entry": sorted(set(current) - set(baseline)),
    } == expected["group_lifecycle"]
    for window, rows in (("baseline", baseline), ("current", current)):
        assert not set(expected["absent_group_ids"][window]) & set(rows)
        assert set(actual["group_order_ids"][window]) == set(rows)
        assert set(actual["group_refunded_order_ids"][window]) == set(rows)
        assert all(row["paid_orders"] > 0 for row in rows.values())
        wanted = expected["metrics"][window]
        assert actual["metrics"][window] == {
            "N": wanted["N"], "U": wanted["U"], "rate": Fraction(wanted["rate"]),
        }
    # 当前C是真实N>0的零退款率，不同于当前B缺席、根本没有一行。
    assert current["category_c"]["paid_orders"] == 2
    assert current["category_c"]["refunded_orders"] == 0
    assert current["category_c"]["rate"] == Fraction(0)
    for field in ("absolute_change_ratio", "relative_change"):
        assert actual["metrics"][field] == Fraction(expected["metrics"][field])
        assert isinstance(actual["metrics"][field], Fraction)
    assert entry_exit_fixture == original


@pytest.mark.parametrize("window_index,window", [(0, "baseline"), (1, "current")])
def test_category_reference_a3_08_traces_order_and_refund_sources(
    entry_exit_fixture: dict, window_index: int, window: str,
) -> None:
    """以实际归组订单反查原始来源行、产品复合键和退款来源，不重算业务Oracle。"""
    original = copy.deepcopy(entry_exit_fixture)
    data, expected = entry_exit_fixture["input"], entry_exit_fixture["expected"]
    scope = data["context"]["domain_id"], data["context"]["snapshot_id"]
    orders = {
        (row["domain_id"], row["snapshot_id"], row["order_id"]): row
        for row in data["orders"]
    }
    products = {
        (row["domain_id"], row["snapshot_id"], row["product_id"]): row
        for row in data["dimensions"]["products"]
    }

    actual = calculate_category_reference(data)

    actual_sources, actual_refund_sources, actual_refunded_orders = set(), set(), set()
    for group_id in category_rows(actual, window_index):
        members = actual["group_order_ids"][window][group_id]
        source_ids = {orders[(*scope, order_id)]["source_row_id"] for order_id in members}
        assert source_ids == set(expected["group_cohort_source_row_ids"][group_id][window])
        assert not actual_sources & source_ids
        actual_sources.update(source_ids)
        for order_id in members:
            row = orders[(*scope, order_id)]
            product_key = row["domain_id"], row["snapshot_id"], row["product_id"]
            assert products[product_key]["category_id"] == group_id

        refunded = actual["group_refunded_order_ids"][window][group_id]
        assert set(refunded) <= set(members)
        # 本固定样例两笔原始退款都合格；这里只追溯已返回的退款订单。
        source_refunds = [
            row for row in data["refunds"]
            if (row["domain_id"], row["snapshot_id"], row["order_id"])
            in {(*scope, order_id) for order_id in refunded}
        ]
        refund_sources = {row["source_row_id"] for row in source_refunds}
        assert refund_sources == set(expected["group_refund_source_row_ids"][group_id][window])
        assert {row["order_id"] for row in source_refunds} == set(refunded)
        assert {row["refund_id"] for row in source_refunds} <= set(
            expected["qualifying_refund_event_ids"][window]
        )
        assert all(row["status"] == "success" for row in source_refunds)
        assert not actual_refund_sources & refund_sources
        actual_refund_sources.update(refund_sources)
        actual_refunded_orders.update(refunded)

    assert actual_sources == set(expected["cohort_source_row_ids"][window])
    assert actual_refunded_orders == set(expected["counted_refund_order_ids"][window])
    assert actual_sources == {
        orders[(*scope, order_id)]["source_row_id"]
        for order_id in actual["candidate_order_ids"][window]
    }
    assert_partition(actual)
    assert entry_exit_fixture == original


def test_category_reference_a3_08_matches_frozen_manual_ledger(entry_exit_fixture: dict) -> None:
    """绑定先行Fixture和手填台账快照，再核对实际计算；不重算hash来迎合变更。"""
    fixture_path = FIXTURE_PATH.parent / "08_category_entry_exit.v1.json"
    manual_path = (
        Path(__file__).resolve().parent.parent / "reference" / "manual_checks" / "A3-08_review.json"
    )
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == (
        "b2ffe9d156a9e010f28bbfda072589c95b8ee8dd426f98a0da8c1515ed0cb580"
    )
    assert hashlib.sha256(manual_path.read_bytes()).hexdigest() == (
        "e6e0f2408aa31082232e7e8ccb74ecb48b76e06bdaced8266c790a96c97ddd3b"
    )
    manual = json.loads(manual_path.read_text(encoding="utf-8"))
    assert manual["fixture_sha256"] == hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    data = entry_exit_fixture["input"]
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == manual["input_sha256"]
    original = copy.deepcopy(entry_exit_fixture)

    actual = calculate_category_reference(data)

    wanted = [
        {
            **{key: value for key, value in row.items() if key != "rate_fraction"},
            "rate": Fraction(row["rate_fraction"]),
        }
        for row in manual["aggregate_rows"]
    ]
    assert len(actual["aggregate_rows"]) == len(wanted) == 6
    assert actual["aggregate_rows"] == wanted
    assert all(isinstance(row["rate"], Fraction) for row in actual["aggregate_rows"])
    assert actual["candidate_order_ids"] == manual["cohort_order_ids"]
    assert actual["group_order_ids"] == manual["group_order_ids"]
    assert actual["group_refunded_order_ids"] == manual["group_refunded_order_ids"]
    assert actual["quality_checks"] == manual["quality_checks"]
    assert actual["outcome"] == manual["outcome"] == "ready"
    assert actual["metrics"]["absolute_change_ratio"] == Fraction(manual["absolute_change_fraction"])
    assert actual["metrics"]["relative_change"] == Fraction(manual["relative_change_fraction"])
    assert_partition(actual)
    assert entry_exit_fixture == original
