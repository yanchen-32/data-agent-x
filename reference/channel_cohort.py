"""小型合成Scope的渠道参考计算，不属于生产Runtime。"""

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Any

from reference.cohort import calculate_reference


def _key(row: Mapping[str, Any], field: str) -> tuple[str, str, str]:
    return row["domain_id"], row["snapshot_id"], row[field]


def _catalog(
    rows: list[Mapping[str, Any]], field: str, scope: tuple[str, str],
) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    indexed = {}
    for row in rows:
        if (row["domain_id"], row["snapshot_id"]) != scope:
            raise ValueError(f"目录域或快照与固定输入范围不一致：{field}")
        identifier = row[field]
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"目录{field}必须是非空字符串")
        key = _key(row, field)
        if key in indexed:
            raise ValueError(f"重复目录主键：{key!r}")
        indexed[key] = row
    return indexed


def _utc(value: str) -> datetime:
    # 原始时间语法已由总体参考函数核验，此处只做标准库解析与UTC归一化。
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def calculate_channel_reference(data: Mapping[str, Any]) -> dict[str, Any]:
    """只从input计算双窗渠道行、总计及组订单台账，率返回Fraction。

    复用总体队列/成熟/水位，从原始退款独立重建合格退款订单集合。
    局部输入字段须先结构核验；只支持已登记的非空渠道ID，未知渠道明确
    拒绝为参考支持范围限制，不将它定性为业务关键DQ或静默丢单。
    所有订单的关键产品关联先检查，不因地区过滤或比较不足绕过。
    不读取expected，不调用生产代码，不访问文件/网络，不实现授权或生产DQ。
    """
    overall = calculate_reference(data)
    context = data["context"]
    scope = context["domain_id"], context["snapshot_id"]
    dimensions = data["dimensions"]
    products = _catalog(dimensions["products"], "product_id", scope)
    channels = _catalog(dimensions["channels"], "channel_id", scope)
    regions = _catalog(dimensions["regions"], "region_id", scope)
    for channel in channels.values():
        label = channel.get("label")
        if label is not None and (not isinstance(label, str) or not label.strip()):
            raise ValueError("渠道label必须为非空字符串或null")
    for region_id in context["filters"]["region_ids"]:
        if (*scope, region_id) not in regions:
            raise ValueError(f"地区过滤ID未在固定Scope目录登记：{region_id}")

    # 完整输入的关键关联检查先于比较不足返回，不只检查纳入支付队列的订单。
    for order in data["orders"]:
        product_key = _key(order, "product_id")
        if product_key not in products:
            raise ValueError(
                "订单产品复合键关联缺失："
                f"order_id={order['order_id']}, source_row_id={order['source_row_id']}, "
                f"product_key={product_key!r}"
            )
        channel_id = order["channel_id"]
        if (
            not isinstance(channel_id, str) or not channel_id.strip()
            or (*scope, channel_id) not in channels
        ):
            raise ValueError(
                "超出最小渠道参考输入支持范围："
                f"order_id={order['order_id']}, source_row_id={order['source_row_id']}, "
                f"channel_id={channel_id!r}"
            )

    result = {
        **overall,
        "aggregate_rows": [],
        "group_order_ids": {},
        "group_refunded_order_ids": {},
    }
    if overall["outcome"] != "ready":
        return result

    orders = {_key(order, "order_id"): order for order in data["orders"]}
    paid_times = {key: _utc(order["paid_at"]) for key, order in orders.items()}
    horizon = timedelta(seconds=context["horizon_seconds"])
    as_of = _utc(context["as_of"])
    refunded_orders = set()
    for refund in data["refunds"]:
        order_key = _key(refund, "order_id")
        paid_at, refund_at = paid_times[order_key], _utc(refund["refund_at"])
        if (
            refund["status"] == "success"
            and paid_at <= refund_at <= paid_at + horizon
            and refund_at <= as_of
        ):
            refunded_orders.add(order_key)

    for index, window in enumerate(("baseline", "current")):
        cohort = {(*scope, oid) for oid in overall["candidate_order_ids"][window]}
        groups: dict[str, set[tuple[str, str, str]]] = {}
        for order_key in cohort:
            groups.setdefault(orders[order_key]["channel_id"], set()).add(order_key)
        n, u = len(cohort), len(cohort & refunded_orders)
        rate = Fraction(u, n)
        totals = overall["metrics"][window]
        if (n, u, rate) != (totals["N"], totals["U"], totals["rate"]):
            raise ValueError("渠道计算与总体参考计数或比率不一致")
        result["aggregate_rows"].append({
            "window_index": index, "dimension_id": None, "group_id": None,
            "group_label": None, "paid_orders": n, "refunded_orders": u, "rate": rate,
        })
        result["group_order_ids"][window] = {}
        result["group_refunded_order_ids"][window] = {}
        for channel_id, members in sorted(groups.items()):
            refunded_members = members & refunded_orders
            result["aggregate_rows"].append({
                "window_index": index, "dimension_id": "channel", "group_id": channel_id,
                "group_label": channels[(*scope, channel_id)].get("label"),
                "paid_orders": len(members), "refunded_orders": len(refunded_members),
                "rate": Fraction(len(refunded_members), len(members)),
            })
            result["group_order_ids"][window][channel_id] = sorted(key[2] for key in members)
            result["group_refunded_order_ids"][window][channel_id] = sorted(
                key[2] for key in refunded_members
            )
    return result
