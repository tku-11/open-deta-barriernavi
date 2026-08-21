"""駅評価項目の平均値・中央値レスポンスを構築するサービス。"""

from typing import Any, Dict, Iterable, List

from services.scoring import definitions_for_mode


NUMERIC_FIELDS = (
    "num_platforms",
    "num_step_free_platforms",
    "num_elevators",
    "num_compliant_elevators",
    "num_escalators",
    "num_compliant_escalators",
    "num_other_lifts",
    "num_slopes",
    "num_compliant_slopes",
    "num_wheelchair_accessible_platforms",
)
FLAG_FIELDS = (
    "step_response_status",
    "has_tactile_paving",
    "has_guidance_system",
    "has_accessible_restroom",
    "has_accessible_gate",
    "has_fall_prevention",
)
RATIO_FIELDS = ("platform_ratio", "elevator_ratio", "escalator_ratio")


def calculate_median(values: Iterable[float]) -> float:
    """空値を除外し、既存API互換の中央値を返す。"""
    sorted_values = sorted(value for value in values if value is not None)
    count = len(sorted_values)
    if count == 0:
        return 0.0
    if count % 2 == 0:
        return (sorted_values[count // 2 - 1] + sorted_values[count // 2]) / 2.0
    return sorted_values[count // 2]


def build_average_response(aggregate: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """集計行を既存の平均値APIレスポンスデータへ変換する。"""
    total_stations = aggregate.get("total_stations", 0)
    averages = {
        "total_stations": total_stations,
        "mode": mode,
        "numeric_averages": {
            field: round(aggregate.get(f"avg_{field}") or 0, 2)
            for field in NUMERIC_FIELDS
        },
        "flag_averages": {
            field: round(aggregate.get(f"avg_{field}") or 0, 3)
            for field in FLAG_FIELDS
        },
        "ratio_averages": {
            field: round(aggregate.get(f"avg_{field}") or 0, 3)
            for field in RATIO_FIELDS
        },
    }

    metric_averages: Dict[str, Dict[str, Any]] = {}
    for field, definition in definitions_for_mode(mode).items():
        metric_type = definition.get("type", "flag")
        label = definition.get("label", field)
        if metric_type == "flag" and field in averages["flag_averages"]:
            average = averages["flag_averages"][field]
            metric_averages[field] = {
                "label": label,
                "type": "flag",
                "average": average,
                "percentage": round(average * 100, 1),
            }
        elif metric_type == "number" and field in averages["numeric_averages"]:
            metric_averages[field] = {
                "label": label,
                "type": "number",
                "average": averages["numeric_averages"][field],
            }
        elif metric_type == "ratio" and field in averages["ratio_averages"]:
            average = averages["ratio_averages"][field]
            metric_averages[field] = {
                "label": label,
                "type": "ratio",
                "average": average,
                "percentage": round(average * 100, 1),
            }

    return {
        "total_stations": total_stations,
        "mode": mode,
        "metric_averages": metric_averages,
        "raw_averages": averages,
    }


def _append_numeric_value(values: List[float], value: Any) -> None:
    if value is None:
        return
    try:
        values.append(float(value))
    except (TypeError, ValueError):
        return


def build_median_response(rows: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
    """中央値計算用の行を既存APIレスポンスデータへ変換する。"""
    numeric_values: Dict[str, List[float]] = {field: [] for field in NUMERIC_FIELDS}
    flag_values: Dict[str, List[float]] = {field: [] for field in FLAG_FIELDS}
    ratio_values: Dict[str, List[float]] = {field: [] for field in RATIO_FIELDS}

    for row in rows:
        for field in NUMERIC_FIELDS:
            _append_numeric_value(numeric_values[field], row.get(field))
        for field in FLAG_FIELDS:
            _append_numeric_value(flag_values[field], row.get(f"{field}_flag"))
        for field in RATIO_FIELDS:
            _append_numeric_value(ratio_values[field], row.get(field))

    medians = {
        "total_stations": len(rows),
        "mode": mode,
        "numeric_medians": {
            field: round(calculate_median(values), 2)
            for field, values in numeric_values.items()
        },
        "flag_medians": {
            field: round(calculate_median(values), 3)
            for field, values in flag_values.items()
        },
        "ratio_medians": {
            field: round(calculate_median(values), 3)
            for field, values in ratio_values.items()
        },
    }

    metric_medians: Dict[str, Dict[str, Any]] = {}
    for field, definition in definitions_for_mode(mode).items():
        metric_type = definition.get("type", "flag")
        label = definition.get("label", field)
        if metric_type == "flag" and field in medians["flag_medians"]:
            median = medians["flag_medians"][field]
            metric_medians[field] = {
                "label": label,
                "type": "flag",
                "median": median,
                "percentage": round(median * 100, 1) if median <= 1.0 else None,
            }
        elif metric_type == "number" and field in medians["numeric_medians"]:
            metric_medians[field] = {
                "label": label,
                "type": "number",
                "median": medians["numeric_medians"][field],
            }
        elif metric_type == "ratio" and field in medians["ratio_medians"]:
            median = medians["ratio_medians"][field]
            metric_medians[field] = {
                "label": label,
                "type": "ratio",
                "median": median,
                "percentage": round(median * 100, 1),
            }

    return {
        "total_stations": len(rows),
        "mode": mode,
        "metric_medians": metric_medians,
        "raw_medians": medians,
    }
