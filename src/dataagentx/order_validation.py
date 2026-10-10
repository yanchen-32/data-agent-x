from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class OrderRecord:
    """带支付时间的单品订单行；通过字段校验不代表通过完整数据质量检查。"""

    source_row_id: str
    domain_id: str
    snapshot_id: str
    order_id: str
    product_id: str
    region_id: str
    channel_id: str
    paid_at: datetime
    is_payment_valid: bool


ID_FIELDS = (
    "source_row_id",
    "domain_id",
    "snapshot_id",
    "order_id",
    "product_id",
    "region_id",
    "channel_id",
)


def validate_order(data: Mapping[str, object]) -> OrderRecord:
    """校验单行 Python 输入，返回 UTC 订单；非法字段抛出 ValueError。

    全部字段必填，拒绝额外字段及隐式类型转换，不修改输入。
    paid_at 接收带时区的 datetime，不解析外部 RFC3339 字符串。
    is_payment_valid=False 和 __unknown__ 维度仍保留；业务筛选另行执行。
    不检查批次唯一性、授权、维度关联、退款、观察成熟期或水位。
    """
    if not isinstance(data, Mapping):
        raise ValueError("订单必须是字段映射")

    required_fields = (*ID_FIELDS, "paid_at", "is_payment_valid")
    for field in required_fields:
        if field not in data:
            raise ValueError(f"缺少必填字段：{field}")
    if set(data) - set(required_fields):
        raise ValueError("订单包含未声明字段")

    identifiers: dict[str, str] = {}
    for field in ID_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} 必须是非空字符串")
        identifiers[field] = value

    paid_at = data["paid_at"]
    if not isinstance(paid_at, datetime) or paid_at.utcoffset() is None:
        raise ValueError("paid_at 必须是带时区的 datetime")

    is_payment_valid = data["is_payment_valid"]
    if not isinstance(is_payment_valid, bool):
        raise ValueError("is_payment_valid 必须是布尔值")

    return OrderRecord(
        **identifiers,
        paid_at=paid_at.astimezone(timezone.utc),
        is_payment_valid=is_payment_valid,
    )
