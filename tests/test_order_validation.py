from datetime import datetime, timedelta, timezone, tzinfo

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


@pytest.mark.parametrize("value", ["true", 0, 1, None])
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


@pytest.mark.parametrize("field", ["domain_id", "snapshot_id"])
def test_scoped_identifier_accepts_schema_length_limit(
    order_data: dict[str, object], field: str
) -> None:
    order_data[field] = "a" * 256

    assert getattr(validate_order(order_data), field) == "a" * 256


@pytest.mark.parametrize("field", ["domain_id", "snapshot_id"])
def test_scoped_identifier_rejects_value_over_schema_length_limit(
    order_data: dict[str, object], field: str
) -> None:
    order_data[field] = "a" * 257

    with pytest.raises(ValueError, match=field):
        validate_order(order_data)


@pytest.mark.parametrize("data", [None, [], "order"])
def test_non_mapping_input_is_rejected(data: object) -> None:
    with pytest.raises(ValueError, match="订单必须是字段映射"):
        validate_order(data)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "paid_at",
    [
        datetime.min.replace(tzinfo=timezone(timedelta(hours=8))),
        datetime.max.replace(tzinfo=timezone(timedelta(hours=-8))),
    ],
)
def test_unrepresentable_utc_time_raises_validation_error(
    order_data: dict[str, object], paid_at: datetime
) -> None:
    order_data["paid_at"] = paid_at

    with pytest.raises(ValueError, match="paid_at 转为 UTC 后超出"):
        validate_order(order_data)


def test_time_with_unknown_offset_is_rejected(order_data: dict[str, object]) -> None:
    class UnknownOffset(tzinfo):
        def utcoffset(self, dt: datetime | None) -> timedelta | None:
            return None

    order_data["paid_at"] = datetime(2026, 9, 1, tzinfo=UnknownOffset())

    with pytest.raises(ValueError, match="paid_at 必须是带时区的 datetime"):
        validate_order(order_data)
