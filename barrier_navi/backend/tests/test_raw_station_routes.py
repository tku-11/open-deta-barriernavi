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
        if "AVG(num_platforms)" in query:
            return [{
                "total_stations": 2,
                "avg_num_platforms": 4.0,
                "avg_num_step_free_platforms": 3.0,
                "avg_num_elevators": 2.0,
                "avg_num_compliant_elevators": 1.5,
                "avg_num_escalators": 2.0,
                "avg_num_compliant_escalators": 1.5,
                "avg_num_other_lifts": 1.0,
                "avg_num_slopes": 2.0,
                "avg_num_compliant_slopes": 1.5,
                "avg_num_wheelchair_accessible_platforms": 3.0,
                "avg_step_response_status": 1.0,
                "avg_has_tactile_paving": 0.5,
                "avg_has_guidance_system": 1.0,
                "avg_has_accessible_restroom": 1.0,
                "avg_has_accessible_gate": 0.5,
                "avg_has_fall_prevention": 1.0,
                "avg_platform_ratio": 0.75,
                "avg_elevator_ratio": 0.75,
                "avg_escalator_ratio": 0.75,
            }]
        if "step_response_status_flag" in query:
            return [
                {"num_platforms": 2, "num_step_free_platforms": 1, "num_elevators": 1, "num_compliant_elevators": 1, "num_escalators": 1, "num_compliant_escalators": 0, "num_other_lifts": 0, "num_slopes": 1, "num_compliant_slopes": 1, "num_wheelchair_accessible_platforms": 2, "step_response_status_flag": 1, "has_tactile_paving_flag": 0, "has_guidance_system_flag": 1, "has_accessible_restroom_flag": 1, "has_accessible_gate_flag": 0, "has_fall_prevention_flag": 1, "platform_ratio": 0.5, "elevator_ratio": 1.0, "escalator_ratio": 0.0},
                {"num_platforms": 6, "num_step_free_platforms": 5, "num_elevators": 3, "num_compliant_elevators": 2, "num_escalators": 3, "num_compliant_escalators": 3, "num_other_lifts": 2, "num_slopes": 3, "num_compliant_slopes": 2, "num_wheelchair_accessible_platforms": 4, "step_response_status_flag": 1, "has_tactile_paving_flag": 1, "has_guidance_system_flag": 1, "has_accessible_restroom_flag": 1, "has_accessible_gate_flag": 1, "has_fall_prevention_flag": 1, "platform_ratio": 0.833, "elevator_ratio": 0.667, "escalator_ratio": 1.0},
            ]
        if "GROUP BY prefecture" in query:
            return [{"prefecture": "東京都", "count": 130}]
        if "with_tactile_paving" in query:
            return [{"total_stations": 130, "with_tactile_paving": 100, "with_guidance_system": 120, "with_accessible_restroom": 110, "with_accessible_gate": 90, "with_elevators": 115}]
        if "SELECT DISTINCT line_name" in query:
            return [{"line_name": "テスト線・支線"}, {"line_name": "別路線"}]
        if "WHERE station_name LIKE %s" in query:
            return [{"id": 2, "station_name": "検索駅"}]
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

    def test_averages_and_medians_keep_metric_and_raw_values(self):
        averages = self.client.get("/api/stations/averages?mode=vision")
        medians = self.client.get("/api/stations/medians?mode=body")

        self.assertEqual(averages.status_code, 200)
        averages_data = averages.get_json()["data"]
        self.assertEqual(averages_data["mode"], "vision")
        self.assertEqual(averages_data["metric_averages"]["has_tactile_paving"]["percentage"], 50.0)
        self.assertEqual(averages_data["raw_averages"]["numeric_averages"]["num_platforms"], 4.0)

        self.assertEqual(medians.status_code, 200)
        medians_data = medians.get_json()["data"]
        self.assertEqual(medians_data["mode"], "body")
        self.assertEqual(medians_data["metric_medians"]["num_slopes"]["median"], 2.0)
        self.assertEqual(medians_data["raw_medians"]["ratio_medians"]["platform_ratio"], 0.666)

    def test_search_and_lines_keep_existing_contracts(self):
        missing_keyword = self.client.get("/api/stations/search")
        search = self.client.get("/api/stations/search?keyword=検索")
        lines = self.client.get("/api/lines")

        self.assertEqual(missing_keyword.status_code, 400)
        self.assertEqual(missing_keyword.get_json()["error"], "Keyword parameter is required")
        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.get_json()["count"], 1)
        self.assertEqual(search.get_json()["data"][0]["station_name"], "検索駅")
        self.assertEqual(lines.status_code, 200)
        self.assertEqual(lines.get_json()["data"], ["テスト線", "別路線", "支線"])


if __name__ == "__main__":
    unittest.main()
