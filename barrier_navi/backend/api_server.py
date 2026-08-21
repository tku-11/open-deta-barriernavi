"""barriernaviのFlaskアプリケーション入口。"""

import os
from functools import wraps
from typing import Any, Callable

from flask import Flask, jsonify, session
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
from routes.pages import create_pages_blueprint
from routes.scored_stations import create_scored_stations_blueprint
from routes.stations import create_stations_blueprint
from services.scoring import (
    BODY_METRIC_DEFINITIONS,
    HEARING_METRIC_DEFINITIONS,
    VISION_METRIC_DEFINITIONS,
    build_station_response,
    compute_score,
    evaluate_metric,
)

BASE_DIR = str(CONFIG_BASE_DIR)
FRONTEND_DIR = str(CONFIG_FRONTEND_DIR)
VIEW_DIR = str(CONFIG_VIEW_DIR)
DIST_DIR = str(CONFIG_DIST_DIR)
MYSQL_CONFIG = database_config()

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


def user_repository_factory() -> UserRepository:
    """テスト時に差し替え可能なユーザーリポジトリを生成する。"""
    return UserRepository(DatabaseConnection, MYSQL_CONFIG)


def station_repository_factory() -> StationRepository:
    """テスト時に差し替え可能な駅リポジトリを生成する。"""
    return StationRepository(DatabaseConnection, MYSQL_CONFIG)


def create_app() -> Flask:
    """設定と依存関係を組み立てたFlaskアプリケーションを生成する。"""
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

    def api_error(message: str, status_code: int):
        """利用者へ内部実装を露出しない統一エラー応答。"""
        return jsonify({"success": False, "error": message}), status_code

    @app.errorhandler(429)
    def rate_limit_exceeded(_error):
        return api_error("短時間に試行回数が上限に達しました。しばらくしてから再度お試しください", 429)

    def require_authenticated_user(view: Callable[..., Any]):
        """ログイン済みセッションを必須にし、利用者IDをサーバー側で確定する。"""
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            if not isinstance(user_id, int) or user_id <= 0:
                return api_error("ログインが必要です", 401)
            return view(*args, **kwargs)

        return wrapped

    app.register_blueprint(
        create_pages_blueprint(CONFIG_FRONTEND_DIR, CONFIG_VIEW_DIR, CONFIG_DIST_DIR)
    )
    app.register_blueprint(
        create_auth_blueprint(user_repository_factory, limiter, api_error, require_authenticated_user)
    )
    app.register_blueprint(
        create_scored_stations_blueprint(station_repository_factory, BODY_QUERY_COLUMNS, api_error)
    )
    app.register_blueprint(
        create_stations_blueprint(station_repository_factory, api_error)
    )
    return app


# 既存の `from api_server import app` と `py backend/api_server.py` を維持する。
app = create_app()


if __name__ == "__main__":
    print("Flask APIサーバーを起動します...")
    port = int(os.getenv("FLASK_PORT", "5000"))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    debug = os.getenv("FLASK_ENV", "production") == "development"
    print(f"http://{host}:{port} でアクセスできます")
    os.chdir(BASE_DIR)
    app.run(debug=debug, host=host, port=port)
