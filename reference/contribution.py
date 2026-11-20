"""按 DD02 §2 对单次双窗参考聚合结果做精确贡献分解。"""

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any


_WINDOWS = ("baseline", "current")
_QUALITY_CHECKS = (
    "all_orders_mature",
    "payments_watermark_covered",
    "refunds_watermark_covered",
)


def _checked_counts(
    row: Mapping[str, Any], paid_field: str, refunded_field: str, identity: object,
) -> tuple[int, int]:
    paid = row.get(paid_field)
    refunded = row.get(refunded_field)
    if type(paid) is not int or type(refunded) is not int or paid <= 0 or not 0 <= refunded <= paid:
        raise ValueError(f"计数须为整数且满足 N > 0、0 <= U <= N：{identity!r}")
    rate = row.get("rate")
    if not isinstance(rate, Fraction) or rate != Fraction(refunded, paid):
        raise ValueError(f"退款率须为与 U/N 一致的 Fraction：{identity!r}")
    return paid, refunded


def calculate_contribution_reference(
    grouped_result: Mapping[str, Any], *, dimension_id: str,
) -> dict[str, Any]:
    """接收同一 Scope 的一次类别、地区或渠道参考聚合结果。

    输入沿用 outcome、reasons、quality_checks、metrics 和 aggregate_rows。
    上游聚合绑定 Scope，调用方须传入该次结果的全部行及两窗总计。
    返回以 ratio 为单位的 Fraction、实际组窗和生命周期。输入不可比、
    标记为不完整、行身份冲突或统计不守恒时抛出 ValueError。
    """
    if not isinstance(grouped_result, Mapping):
        raise ValueError("分组结果必须为映射")
    if dimension_id not in ("category", "region", "channel"):
        raise ValueError("贡献分解须指定 category、region 或 channel 中的一个维度")
    if grouped_result.get("outcome") != "ready" or grouped_result.get("reasons") != []:
        raise ValueError("贡献分解要求双窗结果可比")
    quality = grouped_result.get("quality_checks")
    if not isinstance(quality, Mapping) or any(quality.get(check) is not True for check in _QUALITY_CHECKS):
        raise ValueError("贡献分解要求成熟期及两类水位检查通过")
    if grouped_result.get("truncated", False) is not False or grouped_result.get("complete", True) is not True:
        raise ValueError("贡献分解要求完整且未截断的聚合结果")

    metrics = grouped_result.get("metrics")
    rows = grouped_result.get("aggregate_rows")
    if not isinstance(metrics, Mapping) or not isinstance(rows, Sequence):
        raise ValueError("贡献分解要求双窗总计 metrics 和聚合行 aggregate_rows")

    totals: dict[str, dict] = {}
    for window in _WINDOWS:
        metric = metrics.get(window)
        if not isinstance(metric, Mapping):
            raise ValueError(f"缺少窗口总计：{window}")
        n, u = _checked_counts(metric, "N", "U", window)
        totals[window] = {"N": n, "U": u, "rate": Fraction(u, n)}

    seen = set()
    total_windows = set()
    by_window: dict[str, dict[str, dict]] = {window: {} for window in _WINDOWS}
    for row in rows:
        if not isinstance(row, Mapping) or not {"window_index", "dimension_id", "group_id"} <= row.keys():
            raise ValueError("聚合行须包含窗口、维度及组 ID")
        index, row_dimension, group_id = row["window_index"], row["dimension_id"], row["group_id"]
        if type(index) is not int or index not in (0, 1):
            raise ValueError("聚合行 window_index 须为 0 或 1")
        if row_dimension is None:
            if group_id is not None or row.get("group_label") is not None:
                raise ValueError("总计行的组 ID 与展示名须为 null")
        elif row_dimension != dimension_id or not isinstance(group_id, str) or not group_id.strip():
            raise ValueError("分组行须属于指定单维度且具有非空组 ID")

        identity = (index, row_dimension, group_id)
        if identity in seen:
            raise ValueError(f"重复聚合行身份：{identity!r}")
        seen.add(identity)
        window = _WINDOWS[index]
        n, u = _checked_counts(row, "paid_orders", "refunded_orders", identity)
        total = totals[window]
        if row_dimension is None:
            if (n, u) != (total["N"], total["U"]):
                raise ValueError(f"聚合总计行与 metrics 不一致：{window}")
            total_windows.add(window)
        else:
            weight = Fraction(n, total["N"])
            rate = Fraction(u, n)
            by_window[window][group_id] = {
                "N": n, "U": u, "weight": weight, "rate": rate, "weighted_rate": weight * rate,
            }

    for window, groups in by_window.items():
        if window not in total_windows:
            raise ValueError(f"缺少窗口聚合总计行：{window}")
        for count in ("N", "U"):
            if sum(group[count] for group in groups.values()) != totals[window][count]:
                raise ValueError(f"分组 {count} 与窗口总计不守恒：{window}")

    baseline = by_window["baseline"]
    current = by_window["current"]
    lifecycle = {
        "shared": sorted(baseline.keys() & current.keys()),
        "exit": sorted(baseline.keys() - current.keys()),
        "entry": sorted(current.keys() - baseline.keys()),
    }
    contribution_totals = {term: Fraction(0) for term in ("within", "structure", "entry", "exit")}
    groups = {}
    for group_id in sorted(baseline.keys() | current.keys()):
        before, after = baseline.get(group_id), current.get(group_id)
        if before is None:
            windows = {"current": after}
            contributions = {"entry": after["weighted_rate"]}
        elif after is None:
            windows = {"baseline": before}
            contributions = {"exit": -before["weighted_rate"]}
        else:
            windows = {"baseline": before, "current": after}
            w0, w1 = before["weight"], after["weight"]
            r0, r1 = before["rate"], after["rate"]
            contributions = {
                "within": (w1 + w0) / 2 * (r1 - r0),
                "structure": (r1 + r0) / 2 * (w1 - w0),
            }
        groups[group_id] = {
            "windows": windows,
            "contributions": contributions,
            "net_contribution": sum(contributions.values(), Fraction(0)),
        }
        for term, value in contributions.items():
            contribution_totals[term] += value

    delta = totals["current"]["rate"] - totals["baseline"]["rate"]
    if "absolute_change_ratio" in metrics:
        reported_delta = metrics["absolute_change_ratio"]
        if not isinstance(reported_delta, Fraction) or reported_delta != delta:
            raise ValueError("总体变化须为与双窗总计一致的 Fraction")
    contribution_sum = sum(contribution_totals.values(), Fraction(0))
    return {
        "dimension_id": dimension_id,
        "unit": "ratio",
        "group_lifecycle": lifecycle,
        "groups": groups,
        "totals": {
            **totals,
            "contributions": contribution_totals,
            "contribution_sum": contribution_sum,
            "absolute_change_ratio": delta,
            "residual": delta - contribution_sum,
        },
    }
