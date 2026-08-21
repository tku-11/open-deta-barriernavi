"""プロフィール部分更新のP1契約テスト。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from api_server import app  # noqa: E402


class FakeProfileDatabaseConnection:
    calls = []

    def __init__(self, **_kwargs):
        pass

    def execute_query(self, query, params=None):
        self.calls.append(("query", query, params))
        if "SELECT id FROM users WHERE id" in query:
            return [{"id": 1}]
        if "SELECT id FROM users WHERE username" in query:
            return []
        if "SELECT user_id FROM users_preferences" in query:
            return [{"user_id": 1}]
        return []

    def execute_non_query(self, query, params=None):
        self.calls.append(("execute", query, params))
        return None

    def close(self):
        return None


class ProfilePatchContractTests(unittest.TestCase):
    def setUp(self):
        FakeProfileDatabaseConnection.calls = []
        app.config.update(TESTING=True)
        self.client = app.test_client()
        with self.client.session_transaction() as flask_session:
            flask_session["user_id"] = 1
        self.db_patcher = patch("api_server.DatabaseConnection", FakeProfileDatabaseConnection)
        self.db_patcher.start()
        self.addCleanup(self.db_patcher.stop)

    @staticmethod
    def executed_queries():
        return [call for call in FakeProfileDatabaseConnection.calls if call[0] == "execute"]

    def test_patch_preserves_omitted_preferences_and_clears_explicit_empty_array(self):
        response = self.client.patch(
            "/api/auth/profile",
            json={"preferred_features": []},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["updated_fields"], ["preferred_features"])

        writes = self.executed_queries()
        self.assertEqual(len(writes), 1)
        query = writes[0][1]
        self.assertIn("preferred_features = NULL", query)
        self.assertNotIn("disability_type", query)
        self.assertNotIn("favorite_stations", query)

    def test_put_remains_backward_compatible_with_patch_semantics(self):
        response = self.client.put(
            "/api/auth/profile",
            json={"disability_type": ["body"]},
        )
        self.assertEqual(response.status_code, 200)
        query = self.executed_queries()[0][1]
        self.assertIn("disability_type = %s", query)
        self.assertNotIn("favorite_stations", query)

    def test_username_only_update_does_not_write_preferences(self):
        response = self.client.patch(
            "/api/auth/profile",
            json={"username": "updated-user"},
        )
        self.assertEqual(response.status_code, 200)
        writes = self.executed_queries()
        self.assertEqual(len(writes), 1)
        self.assertIn("UPDATE users SET username", writes[0][1])

    def test_invalid_preference_value_is_rejected_without_writes(self):
        response = self.client.patch(
            "/api/auth/profile",
            json={"favorite_stations": None},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])
        self.assertEqual(self.executed_queries(), [])

    def test_empty_payload_is_rejected(self):
        response = self.client.patch("/api/auth/profile", json={})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
