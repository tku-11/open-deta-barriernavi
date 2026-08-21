"""barriernavi の実行設定とパス定義。"""

import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
FRONTEND_DIR = BASE_DIR / "frontend"
VIEW_DIR = FRONTEND_DIR / "view"
DIST_DIR = FRONTEND_DIR / "dist"

# プロジェクト直下の .env を、どの起動ディレクトリからでも確実に読み込む。
load_dotenv(ENV_PATH)


def env_flag(name: str, default: bool = False) -> bool:
    """環境変数を真偽値として解釈する。"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def database_config() -> dict[str, Any]:
    """MySQL接続設定を返す。"""
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "station"),
    }


def session_secret() -> str:
    """署名付きセッション用の必須秘密鍵を返す。"""
    secret = os.getenv("FLASK_SECRET_KEY")
    if not secret:
        raise RuntimeError("FLASK_SECRET_KEY を .env または環境変数に設定してください。")
    return secret


def session_config() -> dict[str, Any]:
    """FlaskのセッションCookie設定を返す。"""
    return {
        "SECRET_KEY": session_secret(),
        "SESSION_COOKIE_NAME": "barriernavi_session",
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": env_flag("SESSION_COOKIE_SECURE"),
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=8),
    }


def cors_allowed_origins() -> list[str]:
    """明示許可されたCORSオリジンを返す。"""
    return [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]


def rate_limit_storage_uri() -> str:
    """レート制限の共有ストレージURIを返す。"""
    return os.getenv("RATELIMIT_STORAGE_URI", "memory://")
