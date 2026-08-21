"""スコア付き駅APIのP1契約テスト。"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from api_server import app  # noqa: E402


COMPLETE_STATION = {
    "id": 101,
    "station_name": "基準達成駅",
    "prefecture": "東京都",
    "city": "テスト市",
    "railway_operator": "テスト鉄道",
    "line_name": "テスト線",
    "step_response_status": 1,
    "has_tactile_paving": 1,
    "has_guidance_system": 1,
    "has_accessible_restroom": 1,
    "has_accessible_gate": 1,
    "has_fall_prevention": 1,
    "num_platforms": 10,
    "num_step_free_platforms": 8,
    "num_elevators": 5,
    "num_compliant_elevators": 4,
    "num_escalators": 5,
    "num_compliant_escalators": 4,
    "num_other_lifts": 2,
    "num_slopes": 2,
    "num_compliant_slopes": 2,
    "num_wheelchair_accessible_platforms": 6,
}

INCOMPLETE_STATION = {
    **COMPLETE_STATION,
    "id": 102,
    "station_name": "基準未達駅",
    "num_slopes": 1,
}


class FakeStationDatabaseConnection:
    rows = [COMPLETE_STATION, INCOMPLETE_STATION]

    def __init__(self, **_kwargs):
        self.queries = []

    def execute_query(self, query, params=None):
        self.queries.append((query, params))
        if "WHERE id = %s" in query:
            station_id = params[0]
            return [row.copy() for row in self.rows if row["id"] == station_id]
        if "FROM stations" in query:
            if "num_slopes >= %s" in query:
                return [row.copy() for row in self.rows if row["num_slopes"] >= params[-1]]
            return [row.copy() for row in self.rows]
        return []

    def close(self):
        return None


class StationApiContractTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.db_patcher = patch("api_server.DatabaseConnection", FakeStationDatabaseConnection)
        self.db_patcher.start()
        self.addCleanup(self.db_patcher.stop)

    def test_body_list_has_stable_score_contract(self):
        response = self.client.get("/api/body/stations")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertTrue(payload["success"])
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["total_count"], 2)
        self.assertEqual(payload["data"][0]["score"], {
            "met_items": 12,
            "total_items": 12,
            "percentage": 100.0,
            "label": "12/12点",
        })

    def test_number_filter_requires_same_threshold_as_score(self):
        response = self.client.get(
            "/api/body/stations",
            query_string={"filters": json.dumps(["num_slopes"])},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["total_count"], 1)
        self.assertEqual(payload["data"][0]["station_id"], 101)
        self.assertEqual(payload["data"][0]["score"]["met_items"], 12)

    def test_invalid_filter_is_ignored_and_pagination_is_bounded(self):
        response = self.client.get(
            "/api/body/stations",
            query_string={"filters": json.dumps(["unknown", 123]), "limit": 0, "offset": -1},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["total_count"], 2)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["data"][0]["station_id"], 101)

    def test_vision_detail_has_ten_metrics_and_score_label(self):
        response = self.client.get("/api/vision/stations/101")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["score"]["total_items"], 10)
        self.assertEqual(payload["data"]["score"]["label"], "10/10点")
        self.assertEqual(len(payload["data"]["metrics"]), 10)


if __name__ == "__main__":
    unittest.main()
