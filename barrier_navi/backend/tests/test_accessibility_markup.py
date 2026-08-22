"""UX-1のアクセシビリティ基盤に対する静的回帰テスト。"""

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
sys.path.insert(0, str(BACKEND_DIR))

from api_server import app  # noqa: E402


class AccessibilityMarkupTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_station_list_pages_provide_search_result_status_and_semantic_pagination(self):
        for path in ("/index", "/hearing", "/vision"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'id="results-status"', response.data)
                self.assertIn(b'role="status"', response.data)
                self.assertIn(b'<nav class="pagination" aria-label="', response.data)
                self.assertIn(b'aria-busy="false"', response.data)
                self.assertIn(b'aria-label="', response.data)

    def test_station_list_pages_expose_result_summary_and_mobile_filter_control(self):
        for path in ("/index", "/hearing", "/vision"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'id="result-summary"', response.data)
                self.assertIn(b'id="result-summary-text"', response.data)
                self.assertIn(b'id="filter-toggle"', response.data)
                self.assertIn(b'aria-controls="filter-panel"', response.data)
                self.assertIn(b'id="filter-panel"', response.data)

    def test_profile_page_exposes_keyboard_operable_station_combobox_and_save_confirmation(self):
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'role="combobox"', response.data)
        self.assertIn(b'aria-controls="station-search-results"', response.data)
        self.assertIn(b'role="listbox"', response.data)
        self.assertIn(b'id="station-search-status"', response.data)
        self.assertIn(b'id="favorite-stations-status"', response.data)
        self.assertIn(b'id="save-success"', response.data)
        self.assertIn(b'tabindex="-1"', response.data)

    def test_login_page_uses_a_semantic_signup_dialog_and_does_not_offer_unavailable_reset_submission(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'role="dialog"', response.data)
        self.assertIn(b'aria-modal="true"', response.data)
        self.assertIn(b'aria-labelledby="signup-modal-title"', response.data)
        self.assertIn("パスワードリセットは現在ご利用いただけません".encode("utf-8"), response.data)
        self.assertNotIn(b'reset-password-modal', response.data)
        self.assertNotIn("リセットリンクを送信".encode("utf-8"), response.data)

    def test_detail_page_exposes_table_caption_status_and_textual_judgement_column(self):
        response = self.client.get("/detail")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="detail-status"', response.data)
        self.assertIn(b'role="status"', response.data)
        self.assertIn(b'id="decision-summary"', response.data)
        self.assertIn(b'id="decision-summary-text"', response.data)
        self.assertIn(b'id="decision-summary-list"', response.data)
        self.assertIn("達成判定".encode("utf-8"), response.data)
        self.assertIn("判定".encode("utf-8"), response.data)

    def test_accessibility_css_and_client_semantics_are_present(self):
        stylesheet = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")
        station_source = (FRONTEND_DIR / "src" / "index.ts").read_text(encoding="utf-8")
        detail_source = (FRONTEND_DIR / "src" / "detail.ts").read_text(encoding="utf-8")
        profile_source = (FRONTEND_DIR / "src" / "profile.ts").read_text(encoding="utf-8")
        login_source = (FRONTEND_DIR / "src" / "login.ts").read_text(encoding="utf-8")

        self.assertIn(":focus-visible", stylesheet)
        self.assertIn("prefers-reduced-motion", stylesheet)
        self.assertIn(".visually-hidden", stylesheet)
        self.assertIn("document.createElement('a')", station_source)
        self.assertIn("aria-busy", station_source)
        self.assertIn("announceResults", station_source)
        self.assertIn("updateResultSummary", station_source)
        self.assertIn("profileFilterKeys", station_source)
        self.assertIn("条件をリセットして再検索", station_source)
        self.assertIn(".result-summary", stylesheet)
        self.assertIn(".mobile-filter-toggle", stylesheet)
        self.assertIn(".profile-filter-notice", stylesheet)
        self.assertIn("handleStationSearchKeydown", profile_source)
        self.assertIn("aria-activedescendant", profile_source)
        self.assertIn("プロフィールを保存しました。変更は次回の駅検索に反映されます。", profile_source)
        self.assertIn("handleModalKeydown", login_source)
        self.assertIn("modalOpener", login_source)
        self.assertNotIn("/auth/reset-password", login_source)
        self.assertIn(".search-result-item--active", stylesheet)
        self.assertIn("renderDecisionSummary", detail_source)
        self.assertIn("metricKeysForPreferredFeature", detail_source)
        self.assertIn("data-label=\"項目\"", detail_source)
        self.assertIn("達成（基準を満たす）", detail_source)
        self.assertIn(".decision-summary", stylesheet)
        self.assertIn("td::before", stylesheet)
        self.assertIn("metric-status", detail_source)
        self.assertIn("達成", detail_source)
        self.assertIn("未達", detail_source)


if __name__ == "__main__":
    unittest.main()
