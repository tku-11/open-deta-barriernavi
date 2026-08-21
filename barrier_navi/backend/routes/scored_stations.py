"""スコア付き駅一覧・詳細APIを提供するBlueprint。"""

import json
from typing import Any, Callable, Dict, List

from flask import Blueprint, jsonify, request

from repositories.station_repository import StationRepository
from services.scoring import build_station_response, definitions_for_mode


def create_scored_stations_blueprint(
    repository_factory: Callable[[], StationRepository],
    query_columns: List[str],
    api_error: Callable[[str, int], Any],
) -> Blueprint:
    """P1のスコアAPI契約を維持するBlueprintを生成する。"""
    stations = Blueprint("scored_stations", __name__)

    def station_list(mode: str):
        try:
            definitions = definitions_for_mode(mode)
            keyword = request.args.get("keyword", default="", type=str).strip()
            prefecture = request.args.get("prefecture", default=None, type=str)
            line_name = request.args.get("line_name", default=None, type=str)
            limit = min(max(request.args.get("limit", default=20, type=int), 1), 100)
            offset = max(request.args.get("offset", default=0, type=int), 0)
            sort_order = request.args.get("sort", default="none", type=str)

            filters: List[str] = []
            filters_param = request.args.get("filters", default=None, type=str)
            if filters_param:
                try:
                    parsed = json.loads(filters_param)
                    if isinstance(parsed, list):
                        filters = [item for item in parsed if isinstance(item, str)]
                except json.JSONDecodeError:
                    pass

            rows = repository_factory().list_scored_rows(
                query_columns,
                definitions,
                keyword=keyword,
                prefecture=prefecture,
                line_name=line_name,
                filters=filters,
            )
            all_data = [build_station_response(row, mode=mode) for row in rows]
            if sort_order == "score-asc":
                all_data.sort(key=lambda item: item["score"]["percentage"])
            elif sort_order == "score-desc":
                all_data.sort(key=lambda item: item["score"]["percentage"], reverse=True)
            paged_data = all_data[offset:offset + limit]
            return jsonify({"success": True, "data": paged_data, "count": len(paged_data), "total_count": len(all_data)})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    def station_detail(station_id: int, mode: str):
        try:
            row = repository_factory().get_scored_row(station_id, query_columns)
            if row is None:
                return jsonify({"success": False, "error": "Station not found"}), 404
            return jsonify({"success": True, "data": build_station_response(row, mode=mode, include_details=True)})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    stations.add_url_rule("/api/body/stations", endpoint="body_stations", view_func=lambda: station_list("body"), methods=["GET"])
    stations.add_url_rule("/api/body/stations/<int:station_id>", endpoint="body_detail", view_func=lambda station_id: station_detail(station_id, "body"), methods=["GET"])
    stations.add_url_rule("/api/hearing/stations", endpoint="hearing_stations", view_func=lambda: station_list("hearing"), methods=["GET"])
    stations.add_url_rule("/api/hearing/stations/<int:station_id>", endpoint="hearing_detail", view_func=lambda station_id: station_detail(station_id, "hearing"), methods=["GET"])
    stations.add_url_rule("/api/vision/stations", endpoint="vision_stations", view_func=lambda: station_list("vision"), methods=["GET"])
    stations.add_url_rule("/api/vision/stations/<int:station_id>", endpoint="vision_detail", view_func=lambda station_id: station_detail(station_id, "vision"), methods=["GET"])
    return stations
