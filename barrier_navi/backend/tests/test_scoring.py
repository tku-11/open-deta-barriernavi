"""スコア計算のP1契約テスト。"""

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from api_server import (  # noqa: E402
    BODY_METRIC_DEFINITIONS,
    HEARING_METRIC_DEFINITIONS,
    VISION_METRIC_DEFINITIONS,
    build_station_response,
    compute_score,
    evaluate_metric,
)


class ScoreContractTests(unittest.TestCase):
    def setUp(self):
        self.complete_row = {
            "id": 101,
            "station_name": "テスト駅",
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

    def test_category_item_counts_are_fixed(self):
        self.assertEqual(len(BODY_METRIC_DEFINITIONS), 12)
        self.assertEqual(len(HEARING_METRIC_DEFINITIONS), 4)
        self.assertEqual(len(VISION_METRIC_DEFINITIONS), 10)

    def test_flag_metric_accepts_only_status_one(self):
        definition = {"type": "flag", "required": 1}
        self.assertTrue(evaluate_metric("1", definition)["met"])
        self.assertEqual(evaluate_metric("1", definition)["processed_value"], "○")
        self.assertFalse(evaluate_metric(2, definition)["met"])
        self.assertEqual(evaluate_metric(2, definition)["processed_value"], "×")

    def test_number_metric_uses_required_threshold(self):
        definition = {"type": "number", "required": 2}
        below = evaluate_metric(1, definition)
        at_threshold = evaluate_metric(2, definition)

        self.assertFalse(below["met"])
        self.assertEqual(below["ratio"], 0.5)
        self.assertTrue(at_threshold["met"])
        self.assertEqual(at_threshold["ratio"], 1.0)

    def test_ratio_metric_handles_threshold_and_zero_denominator(self):
        definition = {
            "type": "ratio",
            "required": 0.8,
            "numerator": "numerator",
            "denominator": "denominator",
        }
        at_threshold = evaluate_metric(None, definition, {"numerator": 4, "denominator": 5})
        no_denominator = evaluate_metric(None, definition, {"numerator": 0, "denominator": 0})

        self.assertTrue(at_threshold["met"])
        self.assertEqual(at_threshold["processed_value"], "4/5 (80.0%)")
        self.assertFalse(no_denominator["met"])
        self.assertEqual(no_denominator["percentage"], 0.0)

    def test_complete_rows_score_full_points_for_each_category(self):
        self.assertEqual(compute_score(self.complete_row, BODY_METRIC_DEFINITIONS)["met_items"], 12)
        self.assertEqual(compute_score(self.complete_row, HEARING_METRIC_DEFINITIONS)["met_items"], 4)
        self.assertEqual(compute_score(self.complete_row, VISION_METRIC_DEFINITIONS)["met_items"], 10)

    def test_body_response_has_stable_summary_and_metric_details(self):
        response = build_station_response(self.complete_row, mode="body", include_details=True)

        self.assertEqual(response["score"], {
            "met_items": 12,
            "total_items": 12,
            "percentage": 100.0,
            "label": "12/12点",
        })
        self.assertEqual(len(response["metrics"]), 12)
        platform_metric = next(metric for metric in response["metrics"] if metric["key"] == "platform_ratio")
        self.assertEqual(platform_metric["numerator"], 8)
        self.assertEqual(platform_metric["denominator"], 10)
        self.assertTrue(platform_metric["met"])

    def test_vision_response_uses_ten_item_denominator(self):
        response = build_station_response(self.complete_row, mode="vision")
        self.assertEqual(response["score"]["total_items"], 10)
        self.assertEqual(response["score"]["label"], "10/10点")


if __name__ == "__main__":
    unittest.main()
