from datetime import datetime, timedelta, timezone

import pytest

from dataagentx.order_validation import OrderRecord, validate_order


@pytest.fixture
def order_data() -> dict[str, object]:
    return {
        "source_row_id": "row-1",
        "domain_id": "domain-a",
        "snapshot_id": "snapshot-1",
        "order_id": "order-1",
        "product_id": "product-1",
        "region_id": "region-northwest",
        "channel_id": "channel-web",
        "paid_at": datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc),
        "is_payment_valid": True,
    }


def test_valid_order_returns_record_without_mutating_input(
    order_data: dict[str, object],
) -> None:
    original = order_data.copy()

    order = validate_order(order_data)

    assert order == OrderRecord(
        source_row_id="row-1",
        domain_id="domain-a",
        snapshot_id="snapshot-1",
        order_id="order-1",
        product_id="product-1",
        region_id="region-northwest",
        channel_id="channel-web",
        paid_at=datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc),
        is_payment_valid=True,
    )
    assert order_data == original


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("order_id", ""),
        ("domain_id", "  "),
        ("snapshot_id", None),
        ("source_row_id", 1),
        ("product_id", False),
        ("region_id", []),
        ("channel_id", {}),
    ],
)
def test_invalid_identifier_is_rejected(
    order_data: dict[str, object], field: str, value: object
) -> None:
    order_data[field] = value

    with pytest.raises(ValueError, match=field):
        validate_order(order_data)


@pytest.mark.parametrize(
    "field",
    [
        "source_row_id", "domain_id", "snapshot_id", "order_id",
        "product_id", "region_id", "channel_id", "paid_at", "is_payment_valid",
    ],
)
def test_missing_required_field_is_rejected(
    order_data: dict[str, object], field: str
) -> None:
    del order_data[field]

    with pytest.raises(ValueError, match=f"缺少必填字段：{field}"):
        validate_order(order_data)


@pytest.mark.parametrize("paid_at", [None, "2026-09-01T08:00:00Z", datetime(2026, 9, 1)])
def test_invalid_payment_time_is_rejected(
    order_data: dict[str, object], paid_at: object
) -> None:
    order_data["paid_at"] = paid_at

    with pytest.raises(ValueError, match="paid_at"):
        validate_order(order_data)


def test_offset_payment_time_is_normalized_to_utc(
    order_data: dict[str, object],
) -> None:
    order_data["paid_at"] = datetime(
        2026, 9, 1, 8, 0, 0, 123456, tzinfo=timezone(timedelta(hours=8))
    )

    order = validate_order(order_data)

    assert order.paid_at == datetime(2026, 9, 1, 0, 0, 0, 123456, tzinfo=timezone.utc)
    assert order.paid_at.tzinfo is timezone.utc


@pytest.mark.parametrize("value", ["true", 1, None])
def test_payment_validity_requires_a_boolean(
    order_data: dict[str, object], value: object
) -> None:
    order_data["is_payment_valid"] = value

    with pytest.raises(ValueError, match="is_payment_valid"):
        validate_order(order_data)


def test_false_payment_validity_is_preserved(order_data: dict[str, object]) -> None:
    order_data["is_payment_valid"] = False

    assert validate_order(order_data).is_payment_valid is False


def test_unknown_dimension_is_preserved(order_data: dict[str, object]) -> None:
    order_data["region_id"] = "__unknown__"

    assert validate_order(order_data).region_id == "__unknown__"


def test_undeclared_field_is_rejected(order_data: dict[str, object]) -> None:
    order_data["unexpected"] = "value"

    with pytest.raises(ValueError, match="未声明字段"):
        validate_order(order_data)
