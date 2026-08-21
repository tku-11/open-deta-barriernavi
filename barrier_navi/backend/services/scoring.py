"""カテゴリ別のバリアフリースコア計算サービス。"""

from typing import Any, Dict, List

BODY_METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "step_response_status": {"label": "段差への対応", "type": "flag", "required": 1},
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
    "platform_ratio": {"label": "段差が解消されているプラットホームの割合", "type": "ratio", "numerator": "num_step_free_platforms", "denominator": "num_platforms", "required": 0.8},
    "elevator_ratio": {"label": "移動等円滑化基準に適合しているエレベーターの割合", "type": "ratio", "numerator": "num_compliant_elevators", "denominator": "num_elevators", "required": 0.8},
    "escalator_ratio": {"label": "移動等円滑化基準に適合しているエスカレーターの割合", "type": "ratio", "numerator": "num_compliant_escalators", "denominator": "num_escalators", "required": 0.8},
    "num_other_lifts": {"label": "その他の昇降機の設置基数", "type": "number", "required": 2},
    "num_slopes": {"label": "傾斜路の設置箇所数", "type": "number", "required": 2},
    "num_compliant_slopes": {"label": "移動等円滑化基準に適合している傾斜路の設置箇所数", "type": "number", "required": 2},
    "num_wheelchair_accessible_platforms": {"label": "車いす使用者の円滑な乗降が可能なプラットホームの数", "type": "number", "required": 6},
}

HEARING_METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
}

VISION_METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "step_response_status": {"label": "段差への対応", "type": "flag", "required": 1},
    "has_tactile_paving": {"label": "視覚障害者誘導用ブロックの設置の有無", "type": "flag", "required": 1},
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
    "platform_ratio": {"label": "段差が解消されているプラットホームの割合", "type": "ratio", "numerator": "num_step_free_platforms", "denominator": "num_platforms", "required": 0.8},
    "num_compliant_elevators": {"label": "移動等円滑化基準に適合しているエレベーターの設置基数", "type": "number", "required": 4},
    "num_compliant_escalators": {"label": "移動等円滑化基準に適合しているエスカレーターの設置基数", "type": "number", "required": 4},
    "num_compliant_slopes": {"label": "移動等円滑化基準に適合している傾斜路の設置箇所数", "type": "number", "required": 2},
}


def definitions_for_mode(mode: str) -> Dict[str, Dict[str, Any]]:
    """カテゴリに対応する評価定義を返す。未知のカテゴリは身体を既定とする。"""
    if mode == "hearing":
        return HEARING_METRIC_DEFINITIONS
    if mode == "vision":
        return VISION_METRIC_DEFINITIONS
    return BODY_METRIC_DEFINITIONS


def evaluate_metric(value: Any, definition: Dict[str, Any], row: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """単一メトリクスをP1契約に従って評価する。"""
    metric_type = definition.get("type", "flag")
    required = definition.get("required", 1) or 1
    result: Dict[str, Any] = {"raw_value": value, "required": required}

    if metric_type == "flag":
        met = str(value).strip() == "1"
        result.update({"processed_value": "○" if met else "×", "ratio": 1.0 if met else 0.0, "met": met})
    elif metric_type == "ratio":
        numerator_key = definition.get("numerator")
        denominator_key = definition.get("denominator")
        if row and numerator_key and denominator_key:
            try:
                numerator = float(row.get(numerator_key, 0) or 0)
                denominator = float(row.get(denominator_key, 0) or 0)
            except (TypeError, ValueError):
                numerator = denominator = 0.0
            if denominator > 0:
                calculated_ratio = numerator / denominator
                percentage = calculated_ratio * 100
                result.update({
                    "processed_value": f"{int(numerator)}/{int(denominator)} ({percentage:.1f}%)",
                    "numerator": int(numerator),
                    "denominator": int(denominator),
                    "percentage": round(percentage, 1),
                    "ratio": calculated_ratio,
                    "met": calculated_ratio >= required,
                })
            else:
                result.update({"processed_value": "0/0 (0.0%)", "numerator": 0, "denominator": 0, "percentage": 0.0, "ratio": 0.0, "met": False})
        else:
            result.update({"processed_value": "-", "numerator": 0, "denominator": 0, "percentage": 0.0, "ratio": 0.0, "met": False})
    else:
        try:
            numeric_value = float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            numeric_value = 0.0
        ratio = min(numeric_value / required, 1.0) if required else 0.0
        result.update({"processed_value": numeric_value, "ratio": ratio, "met": numeric_value >= required})

    return result


def compute_score(row: Dict[str, Any], definitions: Dict[str, Dict[str, Any]], include_details: bool = False) -> Dict[str, Any]:
    """評価定義に基づく単純達成数スコアを計算する。"""
    met_items = 0
    details: List[Dict[str, Any]] = []

    for field, definition in definitions.items():
        metric_result = evaluate_metric(row.get(field), definition, row=row)
        if metric_result["met"]:
            met_items += 1
        if include_details:
            detail_item = {
                "key": field,
                "label": definition["label"],
                "value": metric_result["processed_value"],
                "raw_value": metric_result["raw_value"],
                "ratio": round(metric_result["ratio"], 2),
                "met": metric_result["met"],
                "type": definition["type"],
                "required": definition["required"],
            }
            if definition.get("type") == "ratio":
                detail_item.update({
                    "numerator": metric_result.get("numerator", 0),
                    "denominator": metric_result.get("denominator", 0),
                    "percentage": metric_result.get("percentage", 0.0),
                })
            details.append(detail_item)

    total_items = len(definitions)
    return {
        "met_items": met_items,
        "total_items": total_items,
        "percentage": round((met_items / total_items) * 100, 1) if total_items else 0,
        "details": details if include_details else None,
    }


def build_station_response(row: Dict[str, Any], mode: str = "body", include_details: bool = False) -> Dict[str, Any]:
    """一覧・詳細API向けの互換レスポンスを構築する。"""
    score = compute_score(row, definitions_for_mode(mode), include_details=include_details)
    response = {
        "station_id": row.get("id"),
        "station_name": row.get("station_name"),
        "prefecture": row.get("prefecture"),
        "city": row.get("city"),
        "operator": row.get("railway_operator"),
        "line_name": row.get("line_name"),
        "score": {
            "met_items": score["met_items"],
            "total_items": score["total_items"],
            "percentage": score["percentage"],
            "label": f"{score['met_items']}/{score['total_items']}点",
        },
    }
    if include_details:
        response["metrics"] = score["details"]
    return response
