"""セッション認証とプロフィール認可の回帰テスト。"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import bcrypt

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from api_server import app  # noqa: E402


class FakeDatabaseConnection:
    """認証APIのDB依存を切り離す最小限のテストダブル。"""

    password_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode("utf-8")
    user = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": password_hash,
    }

    def __init__(self, **_kwargs):
        pass

    def execute_query(self, query, params=None):
        if "FROM users WHERE username" in query:
            supplied_username = params[0]
            if supplied_username in {self.user["username"], self.user["email"]}:
                return [self.user.copy()]
            return []
        if "SELECT id, username, email FROM users WHERE id" in query:
            return [
                {
                    "id": self.user["id"],
                    "username": self.user["username"],
                    "email": self.user["email"],
                }
            ]
        if "FROM users_preferences" in query:
            return []
        return []

    def execute_non_query(self, _query, _params=None):
        return None

    def close(self):
        return None


class AuthenticationSessionTests(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret-key-for-session-tests",
            SESSION_COOKIE_SECURE=False,
        )
        self.client = app.test_client()
        self.db_patcher = patch("api_server.DatabaseConnection", FakeDatabaseConnection)
        self.db_patcher.start()
        self.addCleanup(self.db_patcher.stop)

    def login(self):
        return self.client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "correct-password"},
        )

    def test_profile_requires_authenticated_session(self):
        response = self.client.get("/api/auth/profile?user_id=999")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.get_json()["success"])

    def test_authenticated_profile_ignores_client_supplied_user_id(self):
        login_response = self.login()
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.get_json()["success"])

        response = self.client.get("/api/auth/profile?user_id=999")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["id"], 1)
        self.assertEqual(payload["data"]["username"], "testuser")

    def test_logout_revokes_session_access(self):
        self.login()
        logout_response = self.client.post("/api/auth/logout")
        self.assertEqual(logout_response.status_code, 200)

        profile_response = self.client.get("/api/auth/profile")
        self.assertEqual(profile_response.status_code, 401)

    def test_password_reset_is_explicitly_unavailable(self):
        response = self.client.post("/api/auth/reset-password", json={"email": "test@example.com"})
        self.assertEqual(response.status_code, 501)
        self.assertFalse(response.get_json()["success"])

    def test_untrusted_origin_is_not_allowed_by_cors(self):
        response = self.client.get(
            "/api/auth/profile",
            headers={"Origin": "https://untrusted.example"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    def test_login_attempts_are_rate_limited(self):
        rate_limited_client = app.test_client()
        remote_address = "203.0.113.42"
        for _ in range(5):
            response = rate_limited_client.post(
                "/api/auth/login",
                json={"username": "unknown-user", "password": "wrong-password"},
                environ_overrides={"REMOTE_ADDR": remote_address},
            )
            self.assertEqual(response.status_code, 401)

        response = rate_limited_client.post(
            "/api/auth/login",
            json={"username": "unknown-user", "password": "wrong-password"},
            environ_overrides={"REMOTE_ADDR": remote_address},
        )
        self.assertEqual(response.status_code, 429)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
