"""固定合成Scope的地区参考计算；授权与快照预审由调用侧保证。"""

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Any

from reference.cohort import calculate_reference


def _key(row: Mapping[str, Any], field: str) -> tuple[str, str, str]:
    return row["domain_id"], row["snapshot_id"], row[field]


def _catalog(rows: Any, field: str, scope: tuple[str, str]) -> dict:
    if not isinstance(rows, list):
        raise ValueError(f"缺少或非法目录：{field}")
    indexed = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"目录行必须是映射：{field}")
        identifier = row.get(field)
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"目录{field}必须是非空字符串")
        key = row.get("domain_id"), row.get("snapshot_id"), identifier
        if key[:2] != scope:
            raise ValueError(f"目录域或快照与固定输入范围不一致：{field}, key={key!r}")
        if key in indexed:
            raise ValueError(f"重复目录主键：{field}, key={key!r}")
        if field == "region_id":
            if identifier == "__unknown__":
                raise ValueError("__unknown__是保留组ID，不能登记为普通地区")
            label = row.get("label")
            if label is not None and (not isinstance(label, str) or not label.strip()):
                raise ValueError(f"地区label必须为非空字符串或null：key={key!r}")
        indexed[key] = row
    return indexed


def _utc(value: str) -> datetime:
    # 总体参考入口已核验RFC3339；这里只解析为UTC供独立退款扫描使用。
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def calculate_region_reference(data: Mapping[str, Any]) -> dict[str, Any]:
    """只从input返回总体字段、地区聚合行及两类分组订单台账。

    复用总体过滤队列和成熟/水位检查，独立扫描退款并按完整订单键去重。
    已登记ID缺label保留ID；候选中非关键未登记ID归__unknown__。
    仅接受调用侧已预审的固定合成数据；未知归类不证明授权，不提供权限开关。
    不读取expected/文件，不依赖生产、类别或渠道代码，不修改输入。
    """
    if not isinstance(data, Mapping) or not isinstance(data.get("context"), Mapping):
        raise ValueError("input必须包含context映射")
    context = data["context"]
    scope = context.get("domain_id"), context.get("snapshot_id")
    if any(not isinstance(value, str) or not value.strip() for value in scope):
        raise ValueError("context必须包含非空domain_id和snapshot_id")
    filters = context.get("filters")
    if not isinstance(filters, Mapping) or set(filters) != {"region_ids"}:
        raise ValueError("filters必须显式且仅包含region_ids")
    selected = filters["region_ids"]
    if not isinstance(selected, list) or len(selected) > 1 or any(
        not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value) is None
        for value in selected
    ):
        raise ValueError("region_ids必须是空列表或单个合法注册ID，不能使用__unknown__")
    raw_orders = data.get("orders")
    if not isinstance(raw_orders, list):
        raise ValueError("orders必须是列表")
    for order in raw_orders:
        if not isinstance(order, Mapping):
            raise ValueError("订单行必须是映射")
        region_id = order.get("region_id")
        if not isinstance(region_id, str) or not region_id.strip():
            raise ValueError(
                "订单region_id必须是非空字符串："
                f"order_id={order.get('order_id')}, source_row_id={order.get('source_row_id')}"
            )

    overall = calculate_reference(data)
    dimensions = data.get("dimensions")
    if not isinstance(dimensions, Mapping):
        raise ValueError("input必须包含dimensions映射")
    products = _catalog(dimensions.get("products"), "product_id", scope)
    regions = _catalog(dimensions.get("regions"), "region_id", scope)
    if selected and (*scope, selected[0]) not in regions:
        raise ValueError(f"地区过滤ID未在固定Scope目录登记：{selected[0]}")
    # 检查全部原始输入，不能用地区过滤或比较不足掩盖关键产品故障。
    for order in raw_orders:
        product_key = _key(order, "product_id")
        if product_key not in products:
            raise ValueError(
                "订单产品复合键关联缺失："
                f"order_id={order['order_id']}, source_row_id={order['source_row_id']}, "
                f"product_key={product_key!r}"
            )

    result = {**overall, "aggregate_rows": [], "group_order_ids": {}, "group_refunded_order_ids": {}}
    if overall["outcome"] != "ready":
        return result

    orders = {_key(order, "order_id"): order for order in raw_orders}
    horizon = timedelta(seconds=context["horizon_seconds"])
    as_of = _utc(context["as_of"])
    refunded = set()
    for refund in data["refunds"]:
        order_key = _key(refund, "order_id")
        paid_at = _utc(orders[order_key]["paid_at"])
        refund_at = _utc(refund["refund_at"])
        if refund["status"] == "success" and paid_at <= refund_at <= paid_at + horizon and refund_at <= as_of:
            refunded.add(order_key)

    for index, window in enumerate(("baseline", "current")):
        cohort = {(*scope, oid) for oid in overall["candidate_order_ids"][window]}
        grouped: dict[str, set[tuple[str, str, str]]] = {}
        for order_key in cohort:
            original_id = orders[order_key]["region_id"]
            gid = original_id if (*scope, original_id) in regions else "__unknown__"
            grouped.setdefault(gid, set()).add(order_key)
        n, u = len(cohort), len(cohort & refunded)
        totals = overall["metrics"][window]
        if (n, u, Fraction(u, n)) != (totals["N"], totals["U"], totals["rate"]):
            raise ValueError("地区计算与总体参考计数或比率不一致")
        result["aggregate_rows"].append({
            "window_index": index, "dimension_id": None, "group_id": None, "group_label": None,
            "paid_orders": n, "refunded_orders": u, "rate": Fraction(u, n),
        })
        result["group_order_ids"][window] = {}
        result["group_refunded_order_ids"][window] = {}
        for gid, members in sorted(grouped.items()):
            refunded_members = members & refunded
            region = regions.get((*scope, gid))
            result["aggregate_rows"].append({
                "window_index": index, "dimension_id": "region", "group_id": gid,
                "group_label": region.get("label") if region is not None else None,
                "paid_orders": len(members), "refunded_orders": len(refunded_members),
                "rate": Fraction(len(refunded_members), len(members)),
            })
            result["group_order_ids"][window][gid] = sorted(key[2] for key in members)
            result["group_refunded_order_ids"][window][gid] = sorted(key[2] for key in refunded_members)
    return result
