"""P3で分離した生データ・統計APIの契約テスト。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from api_server import app  # noqa: E402


class FakeRawStationDatabaseConnection:
    def __init__(self, **_kwargs):
        pass

    def execute_query(self, query, params=None):
        if "COUNT(*) as total FROM stations" in query:
            return [{"total": 130}]
        if "GROUP BY prefecture" in query:
            return [{"prefecture": "東京都", "count": 130}]
        if "with_tactile_paving" in query:
            return [{"total_stations": 130, "with_tactile_paving": 100, "with_guidance_system": 120, "with_accessible_restroom": 110, "with_accessible_gate": 90, "with_elevators": 115}]
        if "WHERE id = %s" in query:
            return [{"id": params[0], "station_name": "テスト駅"}]
        if "SELECT * FROM stations WHERE 1=1" in query:
            return [{"id": 1, "station_name": "テスト駅"}]
        return []

    def close(self):
        return None


class RawStationRoutesTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.patcher = patch("api_server.DatabaseConnection", FakeRawStationDatabaseConnection)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_count_and_raw_list_keep_response_keys(self):
        count_response = self.client.get("/api/stations/count")
        list_response = self.client.get("/api/stations?limit=1&offset=0")

        self.assertEqual(count_response.status_code, 200)
        self.assertEqual(count_response.get_json(), {"success": True, "count": 130})
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.get_json()["count"], 1)
        self.assertEqual(list_response.get_json()["data"][0]["station_name"], "テスト駅")

    def test_prefectures_and_statistics_keep_response_keys(self):
        prefectures = self.client.get("/api/stations/prefectures")
        statistics = self.client.get("/api/stations/statistics")

        self.assertEqual(prefectures.status_code, 200)
        self.assertEqual(prefectures.get_json()["data"][0]["prefecture"], "東京都")
        self.assertEqual(statistics.status_code, 200)
        self.assertEqual(statistics.get_json()["data"]["total_stations"], 130)


if __name__ == "__main__":
    unittest.main()
