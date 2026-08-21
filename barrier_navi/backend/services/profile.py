"""プロフィール値の検証・JSON変換・レスポンス構築サービス。"""

import json
from typing import Any, Dict, List, Optional

PREFERENCE_FIELDS = ("disability_type", "favorite_stations", "preferred_features")


def serialize_preference_value(field: str, value: Any) -> Optional[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    if field == "favorite_stations":
        station_ids: List[int] = []
        for station_id in value:
            try:
                normalized_id = int(station_id)
            except (TypeError, ValueError) as error:
                raise ValueError("favorite_stations must contain integer IDs") from error
            if normalized_id <= 0:
                raise ValueError("favorite_stations must contain positive IDs")
            station_ids.append(normalized_id)
        value = station_ids
    return json.dumps(value, ensure_ascii=False) if value else None


def _parse_list(value: Any, *, convert_ints: bool = False) -> List[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    if not convert_ints:
        return parsed
    converted: List[int] = []
    for item in parsed:
        try:
            converted.append(int(item))
        except (TypeError, ValueError):
            continue
    return converted


def build_profile_response(user: Dict[str, Any], preferences: Dict[str, Any] | None) -> Dict[str, Any]:
    """DB行を既存のプロフィールAPIレスポンス形状へ変換する。"""
    preferences = preferences or {}
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "disability_type": _parse_list(preferences.get("disability_type")),
        "favorite_stations": _parse_list(preferences.get("favorite_stations"), convert_ints=True),
        "preferred_features": _parse_list(preferences.get("preferred_features")),
    }
