"""DD02 小型合成 Fixture 的独立参考计算，不导入 dataagentx。"""

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Any


def _instant(value: str) -> datetime:
    """独立解析显式偏移时间；不复用应用或 Fixture 测试的辅助函数。"""
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})"
    if not isinstance(value, str) or not re.fullmatch(pattern, value) or value.endswith("-00:00"):
        raise ValueError("时间必须是显式偏移 RFC3339，最多微秒，不接受未知偏移")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def calculate_reference(data: Mapping[str, Any]) -> dict[str, Any]:
    """从 input 计算两窗支付队列、成熟/水位与退款订单数。

    仅用于小型合成样例；输入字段应先完成结构核验。
    不读取 expected、不访问数据库、不验证目录或授权，不作贡献分解。
    率和变化返回 Fraction；阻断时 metrics 为 None，候选订单另列诊断。
    重复订单/事件、域快照混入、孤立或支付前退款以 ValueError 拒绝，
    不冒充生产批次 DQ 的错误码、修复或批准流程。
    """
    context = data["context"]
    if context["metric_id"] != "refund_rate_order_horizon":
        raise ValueError("参考函数仅支持 refund_rate_order_horizon")
    seconds = context["horizon_seconds"]
    if type(seconds) is not int or seconds <= 0:
        raise ValueError("H 必须是正整数秒")
    horizon = timedelta(seconds=seconds)
    as_of = _instant(context["as_of"])
    payments_through = _instant(context["watermark"]["payments_through"])
    refunds_through = _instant(context["watermark"]["refunds_through"])
    regions = context["filters"]["region_ids"]
    if len(regions) > 1:
        raise ValueError("只支持单地区过滤或全域")

    orders: dict[str, tuple[Mapping[str, Any], datetime]] = {}
    for row in data["orders"]:
        if (row["domain_id"], row["snapshot_id"]) != (context["domain_id"], context["snapshot_id"]):
            raise ValueError("订单域或快照与固定输入范围不一致")
        if row["order_id"] in orders:
            raise ValueError("重复订单主键")
        if type(row["is_payment_valid"]) is not bool:
            raise ValueError("支付有效性必须是布尔值")
        orders[row["order_id"]] = (row, _instant(row["paid_at"]))

    cohorts: dict[str, list[str]] = {}
    window_ends = []
    for name in ("baseline", "current"):
        window = context["windows"][name]
        start, end = _instant(window["start"]), _instant(window["end"])
        if start >= end:
            raise ValueError("支付窗口必须满足 start < end")
        window_ends.append(end)
        cohorts[name] = [
            order_id for order_id, (row, paid_at) in orders.items()
            if row["is_payment_valid"] and start <= paid_at < end
            and (not regions or row["region_id"] in regions)
        ]

    deadlines = [orders[order_id][1] + horizon for ids in cohorts.values() for order_id in ids]
    quality = {
        "all_orders_mature": all(deadline <= as_of for deadline in deadlines),
        "payments_watermark_covered": all(end <= payments_through for end in window_ends),
        "refunds_watermark_covered": all(deadline <= refunds_through for deadline in deadlines),
    }
    reasons = []
    for key, reason in (
        ("all_orders_mature", "观察期未成熟"),
        ("payments_watermark_covered", "支付水位不足"),
        ("refunds_watermark_covered", "退款水位不足"),
    ):
        if not quality[key]:
            reasons.append(reason)
    if any(not ids for ids in cohorts.values()):
        reasons.append("支付窗口无有效样本")

    refunded_orders: set[str] = set()
    refund_ids: set[str] = set()
    for row in data["refunds"]:
        if (row["domain_id"], row["snapshot_id"]) != (context["domain_id"], context["snapshot_id"]):
            raise ValueError("退款域或快照与固定输入范围不一致")
        if row["refund_id"] in refund_ids:
            raise ValueError("重复退款事件")
        refund_ids.add(row["refund_id"])
        if row["order_id"] not in orders:
            raise ValueError("孤立退款")
        paid_at = orders[row["order_id"]][1]
        refund_at = _instant(row["refund_at"])
        if refund_at < paid_at:
            raise ValueError("退款早于支付")
        if row["status"] == "success" and paid_at <= refund_at <= paid_at + horizon and refund_at <= as_of:
            refunded_orders.add(row["order_id"])

    result = {
        "outcome": "insufficient_evidence" if reasons else "ready",
        "reasons": reasons,
        "quality_checks": quality,
        "candidate_order_ids": cohorts,
        "metrics": {
            "baseline": {"N": None, "U": None, "rate": None},
            "current": {"N": None, "U": None, "rate": None},
            "absolute_change_ratio": None,
            "relative_change": None,
        },
    }
    if reasons:
        return result

    for name, ids in cohorts.items():
        n, u = len(ids), len(set(ids) & refunded_orders)
        result["metrics"][name] = {"N": n, "U": u, "rate": Fraction(u, n)}
    baseline_rate = result["metrics"]["baseline"]["rate"]
    change = result["metrics"]["current"]["rate"] - baseline_rate
    result["metrics"]["absolute_change_ratio"] = change
    result["metrics"]["relative_change"] = change / baseline_rate if baseline_rate else None
    return result
