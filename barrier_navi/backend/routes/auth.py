"""認証・プロフィールAPIを提供するBlueprint。"""

from datetime import datetime
from typing import Any, Callable

import bcrypt
from flask import Blueprint, current_app, jsonify, request, session

from repositories.user_repository import UserRepository
from services.profile import PREFERENCE_FIELDS, build_profile_response, serialize_preference_value


def create_auth_blueprint(
    repository_factory: Callable[[], UserRepository],
    limiter: Any,
    api_error: Callable[[str, int], Any],
    require_authenticated_user: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> Blueprint:
    """既存の`/api/auth/*`契約を維持するBlueprintを生成する。"""
    auth = Blueprint("auth", __name__, url_prefix="/api/auth")

    @auth.post("/login")
    @limiter.limit("5 per minute")
    def login():
        data = request.get_json(silent=True) or {}
        identifier = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))
        if not identifier or not password:
            return api_error("ユーザー名とパスワードを入力してください", 400)

        try:
            user = repository_factory().find_for_login(identifier)
            if not user:
                return api_error("ユーザー名またはパスワードが正しくありません", 401)
            password_hash = user.get("password_hash")
            if not password_hash:
                current_app.logger.warning("Missing password hash for user_id=%s", user.get("id"))
                return api_error("ユーザー名またはパスワードが正しくありません", 401)
            try:
                password_hash_bytes = password_hash.encode("utf-8") if isinstance(password_hash, str) else password_hash
                password_valid = bcrypt.checkpw(password.encode("utf-8"), password_hash_bytes)
            except (TypeError, ValueError):
                password_valid = False
            if not password_valid:
                return api_error("ユーザー名またはパスワードが正しくありません", 401)

            try:
                repository_factory().touch_last_login(int(user["id"]), datetime.now())
            except Exception:
                current_app.logger.warning("Failed to update last_login_at for user_id=%s", user.get("id"))

            session.clear()
            session["user_id"] = int(user["id"])
            session.permanent = True
            return jsonify({"success": True, "data": {key: value for key, value in user.items() if key not in {"password", "password_hash"}}})
        except Exception:
            current_app.logger.exception("Login failed")
            return api_error("ログイン処理中にエラーが発生しました", 500)

    @auth.post("/logout")
    def logout():
        session.clear()
        return jsonify({"success": True, "message": "ログアウトしました"})

    @auth.post("/signup")
    @limiter.limit("3 per hour")
    def signup():
        data = request.get_json(silent=True) or {}
        username = str(data.get("username", "")).strip()
        email = str(data.get("email", "")).strip()
        password = str(data.get("password", ""))
        if not username or not email or not password:
            return api_error("すべての項目を入力してください", 400)
        if len(password) < 8:
            return api_error("パスワードは8文字以上で入力してください", 400)

        try:
            repository = repository_factory()
            if repository.username_exists(username):
                return api_error("このユーザー名は既に使用されています", 400)
            if repository.email_exists(email):
                return api_error("このメールアドレスは既に使用されています", 400)
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            repository.create_user(username, email, password_hash)
            return jsonify({"success": True, "message": "アカウントが作成されました"})
        except Exception:
            current_app.logger.exception("Signup failed")
            return api_error("ユーザー登録に失敗しました", 500)

    @auth.post("/reset-password")
    def reset_password():
        return api_error("パスワードリセット機能は現在ご利用いただけません", 501)

    @auth.get("/profile")
    @require_authenticated_user
    def get_profile():
        try:
            repository = repository_factory()
            user = repository.get_public_user(session["user_id"])
            if not user:
                return api_error("ユーザーが見つかりません", 404)
            try:
                preferences = repository.get_preferences(session["user_id"])
            except Exception:
                current_app.logger.warning("Profile preferences could not be loaded", exc_info=True)
                preferences = None
            return jsonify({"success": True, "data": build_profile_response(user, preferences)})
        except Exception:
            current_app.logger.exception("Profile retrieval failed")
            return api_error("プロフィールの取得に失敗しました", 500)

    @auth.route("/profile", methods=["PUT", "PATCH"])
    @require_authenticated_user
    def update_profile():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return api_error("JSON形式の更新内容を指定してください", 400)

        supplied_fields = [field for field in ("username", *PREFERENCE_FIELDS) if field in data]
        if not supplied_fields:
            return api_error("更新する項目を少なくとも1つ指定してください", 400)

        username = None
        if "username" in data:
            if not isinstance(data["username"], str) or not data["username"].strip():
                return api_error("ユーザー名は1文字以上の文字列で指定してください", 400)
            username = data["username"].strip()

        preference_values = {}
        for field in PREFERENCE_FIELDS:
            if field in data:
                try:
                    preference_values[field] = serialize_preference_value(field, data[field])
                except ValueError as error:
                    return api_error(str(error), 400)

        try:
            user_id = session["user_id"]
            repository = repository_factory()
            if not repository.user_exists(user_id):
                return api_error("ユーザーが見つかりません", 404)
            if username is not None:
                if repository.username_exists(username, excluding_user_id=user_id):
                    return api_error("このユーザー名は既に使用されています", 400)
                repository.update_username(user_id, username)
            if preference_values:
                if repository.preference_exists(user_id):
                    repository.update_preferences(user_id, preference_values)
                else:
                    repository.create_preferences(user_id, preference_values)
            return jsonify({"success": True, "message": "プロフィールを更新しました", "updated_fields": supplied_fields})
        except Exception:
            current_app.logger.exception("Profile update failed")
            return api_error("プロフィールの更新に失敗しました", 500)

    return auth
