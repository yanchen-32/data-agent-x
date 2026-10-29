"""小型合成输入的类别分组参考计算；只依赖标准库及总体参考 Oracle。"""

from collections.abc import Mapping
from datetime import datetime, timedelta
from fractions import Fraction
from typing import Any

from reference.cohort import calculate_reference


def _key(row: Mapping[str, Any], field: str) -> tuple[str, str, str]:
    return row["domain_id"], row["snapshot_id"], row[field]


def _catalog(
    rows: list[Mapping[str, Any]], field: str, scope: tuple[str, str],
) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    """仅接受固定域/快照的局部目录，不让字典覆盖掩盖重复键。"""
    indexed = {}
    for row in rows:
        if (row["domain_id"], row["snapshot_id"]) != scope:
            raise ValueError("目录域或快照与固定输入范围不一致")
        identifier = row[field]
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"目录{field}必须是非空字符串")
        key = _key(row, field)
        if key in indexed:
            raise ValueError(f"重复目录主键：{field}")
        indexed[key] = row
    return indexed


def calculate_category_reference(data: Mapping[str, Any]) -> dict[str, Any]:
    """从 input 生成双窗类别行和总计行，不读取 expected 或生产代码。

    总体 Oracle 提供原有输入检查、支付队列和比较前提；此处不改变它。
    分组按产品复合键关联后取 category_id，展示目录只提供 label。
    所有输入订单须唯一关联产品，缺失关联抛出ValueError，不能降级为未知类别。
    合法产品的类别ID缺失归入 __unknown__；已知ID缺展示名仍保留ID、label=None。
    输入结构须先核验；本函数不是生产导入、鉴权或正式 AggregateRow 序列化器。
    比较前提不足时不发布任何聚合行，仅保留总体候选订单诊断。
    """
    overall = calculate_reference(data)
    context = data["context"]
    scope = context["domain_id"], context["snapshot_id"]
    dimensions = data["dimensions"]
    products = _catalog(dimensions["products"], "product_id", scope)
    categories = _catalog(dimensions.get("categories", []), "category_id", scope)
    for product in products.values():
        category_id = product.get("category_id")
        if category_id is not None and (
            not isinstance(category_id, str) or not category_id.strip()
        ):
            raise ValueError("产品category_id必须为非空字符串或null")
    for category in categories.values():
        label = category.get("label")
        if label is not None and (not isinstance(label, str) or not label.strip()):
            raise ValueError("类别label必须为非空字符串或null")

    # 与总体输入检查、目录检查一致：关键关联覆盖全部固定Scope输入，先于比较门槛。
    for order in data["orders"]:
        product_key = _key(order, "product_id")
        if product_key not in products:
            raise ValueError(
                "订单产品复合键关联缺失："
                f"order_id={order['order_id']}, source_row_id={order['source_row_id']}, "
                f"product_key={product_key!r}"
            )

    result = {
        **overall,
        "aggregate_rows": [],
        "group_order_ids": {},
        "group_refunded_order_ids": {},
    }
    if overall["outcome"] != "ready":
        return result

    # 总体 Oracle 已逐行核验 RFC3339、固定 Scope、主键和退款关联。
    orders = {_key(row, "order_id"): row for row in data["orders"]}
    paid_times = {
        key: datetime.fromisoformat(row["paid_at"].replace("Z", "+00:00"))
        for key, row in orders.items()
    }
    as_of = datetime.fromisoformat(context["as_of"].replace("Z", "+00:00"))
    horizon = timedelta(seconds=context["horizon_seconds"])
    refunded = set()
    for refund in data["refunds"]:
        order_key = _key(refund, "order_id")
        paid_at = paid_times[order_key]
        refund_at = datetime.fromisoformat(refund["refund_at"].replace("Z", "+00:00"))
        if (
            refund["status"] == "success"
            and paid_at <= refund_at <= paid_at + horizon
            and refund_at <= as_of
        ):
            refunded.add(order_key)

    for index, window in enumerate(("baseline", "current")):
        cohort = {(*scope, order_id) for order_id in overall["candidate_order_ids"][window]}
        groups: dict[str, set[tuple[str, str, str]]] = {}
        for order_key in sorted(cohort):
            product = products[_key(orders[order_key], "product_id")]
            category_id = product.get("category_id")
            groups.setdefault(category_id or "__unknown__", set()).add(order_key)

        n, u = len(cohort), len(cohort & refunded)
        if (n, u) != (overall["metrics"][window]["N"], overall["metrics"][window]["U"]):
            raise ValueError("类别计算与总体参考计数不一致")
        result["aggregate_rows"].append({
            "window_index": index, "dimension_id": None, "group_id": None,
            "group_label": None, "paid_orders": n, "refunded_orders": u,
            "rate": Fraction(u, n),
        })
        result["group_order_ids"][window] = {}
        result["group_refunded_order_ids"][window] = {}
        for category_id, members in sorted(groups.items()):
            category = categories.get((*scope, category_id))
            refunded_members = members & refunded
            result["aggregate_rows"].append({
                "window_index": index, "dimension_id": "category", "group_id": category_id,
                "group_label": category.get("label") if category is not None else None,
                "paid_orders": len(members), "refunded_orders": len(refunded_members),
                "rate": Fraction(len(refunded_members), len(members)),
            })
            result["group_order_ids"][window][category_id] = sorted(key[2] for key in members)
            result["group_refunded_order_ids"][window][category_id] = sorted(
                key[2] for key in refunded_members
            )
    return result
