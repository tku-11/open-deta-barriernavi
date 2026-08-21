"""生データ、統計、検索、路線の駅APIを提供するBlueprint。"""

from typing import Any, Callable

from flask import Blueprint, jsonify, request

from repositories.station_repository import StationRepository
from services.station_statistics import build_average_response, build_median_response


def create_stations_blueprint(
    repository_factory: Callable[[], StationRepository],
    api_error: Callable[[str, int], Any],
) -> Blueprint:
    """既存の生データ・統計・検索・路線API契約を維持するBlueprintを生成する。"""
    stations = Blueprint("stations", __name__)

    @stations.route("/api/stations", methods=["GET"])
    def get_stations():
        try:
            limit = request.args.get("limit", default=100, type=int)
            offset = request.args.get("offset", default=0, type=int)
            prefecture = request.args.get("prefecture", default=None, type=str)
            rows = repository_factory().list_raw_stations(limit, offset, prefecture)
            return jsonify({"success": True, "data": rows, "count": len(rows)})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/stations/<int:station_id>", methods=["GET"])
    def get_station(station_id: int):
        try:
            station = repository_factory().get_raw_station(station_id)
            if station is None:
                return jsonify({"success": False, "error": "Station not found"}), 404
            return jsonify({"success": True, "data": station})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/stations/count", methods=["GET"])
    def get_stations_count():
        try:
            return jsonify({"success": True, "count": repository_factory().count_stations()})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/stations/prefectures", methods=["GET"])
    def get_prefectures():
        try:
            return jsonify({"success": True, "data": repository_factory().list_prefectures()})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/stations/statistics", methods=["GET"])
    def get_statistics():
        try:
            return jsonify({"success": True, "data": repository_factory().get_statistics()})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/stations/averages", methods=["GET"])
    def get_station_averages():
        try:
            mode = request.args.get("mode", default="body", type=str)
            aggregate = repository_factory().get_average_aggregates()
            if aggregate is None:
                return jsonify({"success": False, "error": "データが見つかりません"}), 404
            return jsonify({"success": True, "data": build_average_response(aggregate, mode)})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/stations/medians", methods=["GET"])
    def get_station_medians():
        try:
            mode = request.args.get("mode", default="body", type=str)
            rows = repository_factory().list_median_source_rows()
            if not rows:
                return jsonify({"success": False, "error": "データが見つかりません"}), 404
            return jsonify({"success": True, "data": build_median_response(rows, mode)})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/stations/search", methods=["GET"])
    def search_stations():
        try:
            keyword = request.args.get("keyword", default="", type=str)
            limit = request.args.get("limit", default=50, type=int)
            if not keyword:
                return jsonify({"success": False, "error": "Keyword parameter is required"}), 400
            rows = repository_factory().search_by_station_name(keyword, limit)
            return jsonify({"success": True, "data": rows, "count": len(rows)})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    @stations.route("/api/lines", methods=["GET"])
    def get_lines():
        try:
            return jsonify({"success": True, "data": repository_factory().list_lines()})
        except Exception:
            return api_error("サーバー内部でエラーが発生しました", 500)

    return stations
