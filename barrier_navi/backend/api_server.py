"""
Flask APIサーバー - stationsデータベースからデータを提供
"""

import json
import os
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional

import bcrypt
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import (
    BASE_DIR as CONFIG_BASE_DIR,
    DIST_DIR as CONFIG_DIST_DIR,
    FRONTEND_DIR as CONFIG_FRONTEND_DIR,
    VIEW_DIR as CONFIG_VIEW_DIR,
    cors_allowed_origins,
    database_config,
    rate_limit_storage_uri,
    session_config,
)
from database_connection import DatabaseConnection
from repositories.station_repository import StationRepository
from repositories.user_repository import UserRepository
from routes.auth import create_auth_blueprint
from routes.scored_stations import create_scored_stations_blueprint
from routes.pages import create_pages_blueprint
from services.scoring import (
    BODY_METRIC_DEFINITIONS,
    HEARING_METRIC_DEFINITIONS,
    VISION_METRIC_DEFINITIONS,
    build_station_response,
    compute_score,
    definitions_for_mode,
    evaluate_metric,
)

BASE_DIR = str(CONFIG_BASE_DIR)
FRONTEND_DIR = str(CONFIG_FRONTEND_DIR)
VIEW_DIR = str(CONFIG_VIEW_DIR)
DIST_DIR = str(CONFIG_DIST_DIR)
MYSQL_CONFIG = database_config()

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config.update(session_config())

allowed_origins = cors_allowed_origins()
if allowed_origins:
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=rate_limit_storage_uri(),
)
app.register_blueprint(
    create_pages_blueprint(CONFIG_FRONTEND_DIR, CONFIG_VIEW_DIR, CONFIG_DIST_DIR)
)

def api_error(message: str, status_code: int):

    """利用者へ内部実装を露出しない統一エラー応答。"""
    return jsonify({"success": False, "error": message}), status_code


@app.errorhandler(429)
def rate_limit_exceeded(_error):
    return api_error("短時間に試行回数が上限に達しました。しばらくしてから再度お試しください", 429)


def require_authenticated_user(view):

    """ログイン済みセッションを必須にし、利用者IDをサーバー側で確定する。"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not isinstance(user_id, int) or user_id <= 0:
            return api_error("ログインが必要です", 401)
        return view(*args, **kwargs)

    return wrapped


def user_repository_factory() -> UserRepository:
    """テスト時に差し替え可能なユーザーリポジトリを生成する。"""
    return UserRepository(DatabaseConnection, MYSQL_CONFIG)


app.register_blueprint(
    create_auth_blueprint(user_repository_factory, limiter, api_error, require_authenticated_user)
)




BODY_BASE_COLUMNS = [
    "id",
    "station_name",
    "railway_operator",
    "line_name",
    "prefecture",
    "city",
]
BODY_QUERY_COLUMNS = BODY_BASE_COLUMNS + [
    "step_response_status",
    "has_guidance_system",
    "has_accessible_restroom",
    "has_accessible_gate",
    "has_fall_prevention",
    "has_tactile_paving",
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
]


def station_repository_factory() -> StationRepository:
    """テスト時に差し替え可能な駅リポジトリを生成する。"""
    return StationRepository(DatabaseConnection, MYSQL_CONFIG)


app.register_blueprint(
    create_scored_stations_blueprint(station_repository_factory, BODY_QUERY_COLUMNS, api_error)
)


# ---------------------------------------------------------
# ★これを新しく追加してください（共通の検索・取得ロジック）
# ---------------------------------------------------------


@app.route('/api/stations', methods=['GET'])
def get_stations():
    try:
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        prefecture = request.args.get('prefecture', default=None, type=str)
        stations = station_repository_factory().list_raw_stations(limit, offset, prefecture)
        return jsonify({"success": True, "data": stations, "count": len(stations)})
    except Exception:
        return api_error("サーバー内部でエラーが発生しました", 500)


@app.route('/api/stations/<int:station_id>', methods=['GET'])
def get_station(station_id):
    try:
        station = station_repository_factory().get_raw_station(station_id)
        if station is None:
            return jsonify({"success": False, "error": "Station not found"}), 404
        return jsonify({"success": True, "data": station})
    except Exception:
        return api_error("サーバー内部でエラーが発生しました", 500)


@app.route('/api/stations/count', methods=['GET'])
def get_stations_count():
    try:
        return jsonify({"success": True, "count": station_repository_factory().count_stations()})
    except Exception:
        return api_error("サーバー内部でエラーが発生しました", 500)


@app.route('/api/stations/prefectures', methods=['GET'])
def get_prefectures():
    try:
        return jsonify({"success": True, "data": station_repository_factory().list_prefectures()})
    except Exception:
        return api_error("サーバー内部でエラーが発生しました", 500)


@app.route('/api/stations/statistics', methods=['GET'])
def get_statistics():
    try:
        return jsonify({"success": True, "data": station_repository_factory().get_statistics()})
    except Exception:
        return api_error("サーバー内部でエラーが発生しました", 500)


@app.route('/api/stations/averages', methods=['GET'])
def get_station_averages():
    """全駅の各項目の平均値を取得"""
    try:
        mode = request.args.get('mode', default='body', type=str)  # body, hearing, vision
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # 全駅の数値を取得
        query = """
            SELECT 
                COUNT(*) as total_stations,
                -- 数値型項目の平均値
                AVG(num_platforms) as avg_num_platforms,
                AVG(num_step_free_platforms) as avg_num_step_free_platforms,
                AVG(num_elevators) as avg_num_elevators,
                AVG(num_compliant_elevators) as avg_num_compliant_elevators,
                AVG(num_escalators) as avg_num_escalators,
                AVG(num_compliant_escalators) as avg_num_compliant_escalators,
                AVG(num_other_lifts) as avg_num_other_lifts,
                AVG(num_slopes) as avg_num_slopes,
                AVG(num_compliant_slopes) as avg_num_compliant_slopes,
                AVG(num_wheelchair_accessible_platforms) as avg_num_wheelchair_accessible_platforms,
                -- フラグ型項目の平均値（設置率：1の割合）
                AVG(CASE WHEN step_response_status = 1 THEN 1.0 ELSE 0.0 END) as avg_step_response_status,
                AVG(CASE WHEN has_tactile_paving = 1 THEN 1.0 ELSE 0.0 END) as avg_has_tactile_paving,
                AVG(CASE WHEN has_guidance_system = 1 THEN 1.0 ELSE 0.0 END) as avg_has_guidance_system,
                AVG(CASE WHEN has_accessible_restroom = 1 THEN 1.0 ELSE 0.0 END) as avg_has_accessible_restroom,
                AVG(CASE WHEN has_accessible_gate = 1 THEN 1.0 ELSE 0.0 END) as avg_has_accessible_gate,
                AVG(CASE WHEN has_fall_prevention = 1 THEN 1.0 ELSE 0.0 END) as avg_has_fall_prevention,
                -- 割合型項目の平均値（計算用の元データ）
                AVG(CASE WHEN num_platforms > 0 THEN num_step_free_platforms / num_platforms ELSE 0.0 END) as avg_platform_ratio,
                AVG(CASE WHEN num_elevators > 0 THEN num_compliant_elevators / num_elevators ELSE 0.0 END) as avg_elevator_ratio,
                AVG(CASE WHEN num_escalators > 0 THEN num_compliant_escalators / num_escalators ELSE 0.0 END) as avg_escalator_ratio
            FROM stations
        """
        
        result = db.execute_query(query)
        db.close()
        
        if not result or len(result) == 0:
            return jsonify({
                "success": False,
                "error": "データが見つかりません"
            }), 404
        
        data = result[0]
        total_stations = data.get('total_stations', 0)
        
        # 結果を整形
        averages = {
            "total_stations": total_stations,
            "mode": mode,
            "numeric_averages": {
                "num_platforms": round(data.get('avg_num_platforms') or 0, 2),
                "num_step_free_platforms": round(data.get('avg_num_step_free_platforms') or 0, 2),
                "num_elevators": round(data.get('avg_num_elevators') or 0, 2),
                "num_compliant_elevators": round(data.get('avg_num_compliant_elevators') or 0, 2),
                "num_escalators": round(data.get('avg_num_escalators') or 0, 2),
                "num_compliant_escalators": round(data.get('avg_num_compliant_escalators') or 0, 2),
                "num_other_lifts": round(data.get('avg_num_other_lifts') or 0, 2),
                "num_slopes": round(data.get('avg_num_slopes') or 0, 2),
                "num_compliant_slopes": round(data.get('avg_num_compliant_slopes') or 0, 2),
                "num_wheelchair_accessible_platforms": round(data.get('avg_num_wheelchair_accessible_platforms') or 0, 2),
            },
            "flag_averages": {
                # フラグ型項目の平均値（設置率として0.0〜1.0で返す）
                "step_response_status": round(data.get('avg_step_response_status') or 0, 3),
                "has_tactile_paving": round(data.get('avg_has_tactile_paving') or 0, 3),
                "has_guidance_system": round(data.get('avg_has_guidance_system') or 0, 3),
                "has_accessible_restroom": round(data.get('avg_has_accessible_restroom') or 0, 3),
                "has_accessible_gate": round(data.get('avg_has_accessible_gate') or 0, 3),
                "has_fall_prevention": round(data.get('avg_has_fall_prevention') or 0, 3),
            },
            "ratio_averages": {
                # 割合型項目の平均値（0.0〜1.0で返す）
                "platform_ratio": round(data.get('avg_platform_ratio') or 0, 3),
                "elevator_ratio": round(data.get('avg_elevator_ratio') or 0, 3),
                "escalator_ratio": round(data.get('avg_escalator_ratio') or 0, 3),
            }
        }
        
        # モード別の評価項目定義に基づいて、該当する項目のみを返す
        if mode == 'body':
            definitions = BODY_METRIC_DEFINITIONS
        elif mode == 'hearing':
            definitions = HEARING_METRIC_DEFINITIONS
        elif mode == 'vision':
            definitions = VISION_METRIC_DEFINITIONS
        else:
            definitions = BODY_METRIC_DEFINITIONS
        
        # 評価項目ごとの平均値を整理
        metric_averages = {}
        for field, definition in definitions.items():
            metric_type = definition.get("type", "flag")
            label = definition.get("label", field)
            
            if metric_type == "flag":
                # フラグ型：設置率を取得
                flag_key = field
                if flag_key in averages["flag_averages"]:
                    metric_averages[field] = {
                        "label": label,
                        "type": "flag",
                        "average": averages["flag_averages"][flag_key],
                        "percentage": round(averages["flag_averages"][flag_key] * 100, 1)
                    }
            elif metric_type == "number":
                # 数値型：平均値を取得
                numeric_key = field
                if numeric_key in averages["numeric_averages"]:
                    metric_averages[field] = {
                        "label": label,
                        "type": "number",
                        "average": averages["numeric_averages"][numeric_key]
                    }
            elif metric_type == "ratio":
                # 割合型：平均割合を取得
                ratio_key = field
                if ratio_key in averages["ratio_averages"]:
                    metric_averages[field] = {
                        "label": label,
                        "type": "ratio",
                        "average": averages["ratio_averages"][ratio_key],
                        "percentage": round(averages["ratio_averages"][ratio_key] * 100, 1)
                    }
        
        return jsonify({
            "success": True,
            "data": {
                "total_stations": total_stations,
                "mode": mode,
                "metric_averages": metric_averages,
                "raw_averages": averages  # デバッグ用に全データも含める
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error("サーバー内部でエラーが発生しました", 500)


def calculate_median(values: List[float]) -> float:
    """中央値を計算する関数"""
    if not values:
        return 0.0
    
    sorted_values = sorted([v for v in values if v is not None])
    n = len(sorted_values)
    
    if n == 0:
        return 0.0
    
    if n % 2 == 0:
        # 偶数個の場合：中央の2つの値の平均
        median = (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2.0
    else:
        # 奇数個の場合：中央の値
        median = sorted_values[n // 2]
    
    return median


@app.route('/api/stations/medians', methods=['GET'])
def get_station_medians():
    """全駅の各項目の中央値を取得"""
    try:
        mode = request.args.get('mode', default='body', type=str)  # body, hearing, vision
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # 全駅のデータを取得（中央値計算のため）
        query = """
            SELECT 
                -- 数値型項目
                num_platforms,
                num_step_free_platforms,
                num_elevators,
                num_compliant_elevators,
                num_escalators,
                num_compliant_escalators,
                num_other_lifts,
                num_slopes,
                num_compliant_slopes,
                num_wheelchair_accessible_platforms,
                -- フラグ型項目（0/1に変換）
                CASE WHEN step_response_status = 1 THEN 1.0 ELSE 0.0 END as step_response_status_flag,
                CASE WHEN has_tactile_paving = 1 THEN 1.0 ELSE 0.0 END as has_tactile_paving_flag,
                CASE WHEN has_guidance_system = 1 THEN 1.0 ELSE 0.0 END as has_guidance_system_flag,
                CASE WHEN has_accessible_restroom = 1 THEN 1.0 ELSE 0.0 END as has_accessible_restroom_flag,
                CASE WHEN has_accessible_gate = 1 THEN 1.0 ELSE 0.0 END as has_accessible_gate_flag,
                CASE WHEN has_fall_prevention = 1 THEN 1.0 ELSE 0.0 END as has_fall_prevention_flag,
                -- 割合型項目（計算値）
                CASE WHEN num_platforms > 0 THEN num_step_free_platforms / num_platforms ELSE 0.0 END as platform_ratio,
                CASE WHEN num_elevators > 0 THEN num_compliant_elevators / num_elevators ELSE 0.0 END as elevator_ratio,
                CASE WHEN num_escalators > 0 THEN num_compliant_escalators / num_escalators ELSE 0.0 END as escalator_ratio
            FROM stations
        """
        
        result = db.execute_query(query)
        db.close()
        
        if not result or len(result) == 0:
            return jsonify({
                "success": False,
                "error": "データが見つかりません"
            }), 404
        
        total_stations = len(result)
        
        # 各項目の値をリストに集約
        numeric_values = {
            "num_platforms": [],
            "num_step_free_platforms": [],
            "num_elevators": [],
            "num_compliant_elevators": [],
            "num_escalators": [],
            "num_compliant_escalators": [],
            "num_other_lifts": [],
            "num_slopes": [],
            "num_compliant_slopes": [],
            "num_wheelchair_accessible_platforms": [],
        }
        
        flag_values = {
            "step_response_status": [],
            "has_tactile_paving": [],
            "has_guidance_system": [],
            "has_accessible_restroom": [],
            "has_accessible_gate": [],
            "has_fall_prevention": [],
        }
        
        ratio_values = {
            "platform_ratio": [],
            "elevator_ratio": [],
            "escalator_ratio": [],
        }
        
        # データを集約
        for row in result:
            # 数値型項目
            for key in numeric_values.keys():
                value = row.get(key)
                if value is not None:
                    try:
                        numeric_values[key].append(float(value))
                    except (TypeError, ValueError):
                        pass
            
            # フラグ型項目
            flag_mapping = {
                "step_response_status": "step_response_status_flag",
                "has_tactile_paving": "has_tactile_paving_flag",
                "has_guidance_system": "has_guidance_system_flag",
                "has_accessible_restroom": "has_accessible_restroom_flag",
                "has_accessible_gate": "has_accessible_gate_flag",
                "has_fall_prevention": "has_fall_prevention_flag",
            }
            for key, db_key in flag_mapping.items():
                value = row.get(db_key)
                if value is not None:
                    try:
                        flag_values[key].append(float(value))
                    except (TypeError, ValueError):
                        pass
            
            # 割合型項目
            for key in ratio_values.keys():
                value = row.get(key)
                if value is not None:
                    try:
                        ratio_values[key].append(float(value))
                    except (TypeError, ValueError):
                        pass
        
        # 中央値を計算
        medians = {
            "total_stations": total_stations,
            "mode": mode,
            "numeric_medians": {},
            "flag_medians": {},
            "ratio_medians": {},
        }
        
        # 数値型項目の中央値
        for key, values in numeric_values.items():
            medians["numeric_medians"][key] = round(calculate_median(values), 2)
        
        # フラグ型項目の中央値（0または1になることが多いが、計算は実行）
        for key, values in flag_values.items():
            median = calculate_median(values)
            medians["flag_medians"][key] = round(median, 3)
        
        # 割合型項目の中央値
        for key, values in ratio_values.items():
            median = calculate_median(values)
            medians["ratio_medians"][key] = round(median, 3)
        
        # モード別の評価項目定義に基づいて、該当する項目のみを返す
        if mode == 'body':
            definitions = BODY_METRIC_DEFINITIONS
        elif mode == 'hearing':
            definitions = HEARING_METRIC_DEFINITIONS
        elif mode == 'vision':
            definitions = VISION_METRIC_DEFINITIONS
        else:
            definitions = BODY_METRIC_DEFINITIONS
        
        # 評価項目ごとの中央値を整理
        metric_medians = {}
        for field, definition in definitions.items():
            metric_type = definition.get("type", "flag")
            label = definition.get("label", field)
            
            if metric_type == "flag":
                # フラグ型：中央値を取得
                flag_key = field
                if flag_key in medians["flag_medians"]:
                    median_value = medians["flag_medians"][flag_key]
                    metric_medians[field] = {
                        "label": label,
                        "type": "flag",
                        "median": median_value,
                        "percentage": round(median_value * 100, 1) if median_value <= 1.0 else None
                    }
            elif metric_type == "number":
                # 数値型：中央値を取得
                numeric_key = field
                if numeric_key in medians["numeric_medians"]:
                    metric_medians[field] = {
                        "label": label,
                        "type": "number",
                        "median": medians["numeric_medians"][numeric_key]
                    }
            elif metric_type == "ratio":
                # 割合型：中央値を取得
                ratio_key = field
                if ratio_key in medians["ratio_medians"]:
                    median_value = medians["ratio_medians"][ratio_key]
                    metric_medians[field] = {
                        "label": label,
                        "type": "ratio",
                        "median": median_value,
                        "percentage": round(median_value * 100, 1)
                    }
        
        return jsonify({
            "success": True,
            "data": {
                "total_stations": total_stations,
                "mode": mode,
                "metric_medians": metric_medians,
                "raw_medians": medians  # デバッグ用に全データも含める
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error("サーバー内部でエラーが発生しました", 500)


@app.route('/api/stations/search', methods=['GET'])
def search_stations():
    """駅名で検索"""
    try:
        keyword = request.args.get('keyword', default='', type=str)
        limit = request.args.get('limit', default=50, type=int)
        
        if not keyword:
            return jsonify({
                "success": False,
                "error": "Keyword parameter is required"
            }), 400
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        stations = db.execute_query(
            "SELECT * FROM stations WHERE station_name LIKE %s LIMIT %s",
            (f"%{keyword}%", limit)
        )
        db.close()
        
        return jsonify({
            "success": True,
            "data": stations,
            "count": len(stations)
        })
    except Exception as e:
        return api_error("サーバー内部でエラーが発生しました", 500)


@app.route('/api/lines', methods=['GET'])
def get_lines():
    """路線名一覧を取得（プルダウン用）"""
    try:
        db = DatabaseConnection(**MYSQL_CONFIG)

        rows = db.execute_query(
            "SELECT DISTINCT line_name FROM stations WHERE line_name IS NOT NULL AND line_name != ''"
            )
        db.close()
        
        lines_set = set()
        for row in rows:
            line_val = row['line_name']
            if line_val:
                split_lines = line_val.split('・')
                for line in split_lines:
                    clean_line = line.strip()
                    if clean_line:
                        lines_set.add(clean_line)
        
        # 五十音順などでソートして返す
        return jsonify({
            "success": True,
            "data": sorted(list(lines_set))
        })
    except Exception as e:
        return api_error("サーバー内部でエラーが発生しました", 500)




if __name__ == '__main__':
    print("Flask APIサーバーを起動します...")
    port = int(os.getenv("FLASK_PORT", "5000"))
    host = os.getenv("FLASK_HOST", "0.0.0.0")  # Docker環境では0.0.0.0が必要
    debug = os.getenv("FLASK_ENV", "production") == "development"
    print(f"http://{host}:{port} でアクセスできます")
    # 作業ディレクトリをプロジェクトルートに変更
    os.chdir(BASE_DIR)
    app.run(debug=debug, host=host, port=port)

