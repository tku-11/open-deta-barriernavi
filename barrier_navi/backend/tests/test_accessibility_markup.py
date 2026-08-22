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

    def test_detail_page_exposes_table_caption_status_and_textual_judgement_column(self):
        response = self.client.get("/detail")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="detail-status"', response.data)
        self.assertIn(b'role="status"', response.data)
        self.assertIn("達成判定".encode("utf-8"), response.data)
        self.assertIn("判定".encode("utf-8"), response.data)

    def test_accessibility_css_and_client_semantics_are_present(self):
        stylesheet = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")
        station_source = (FRONTEND_DIR / "src" / "index.ts").read_text(encoding="utf-8")
        detail_source = (FRONTEND_DIR / "src" / "detail.ts").read_text(encoding="utf-8")

        self.assertIn(":focus-visible", stylesheet)
        self.assertIn("prefers-reduced-motion", stylesheet)
        self.assertIn(".visually-hidden", stylesheet)
        self.assertIn("document.createElement('a')", station_source)
        self.assertIn("aria-busy", station_source)
        self.assertIn("announceResults", station_source)
        self.assertIn("metric-status", detail_source)
        self.assertIn("達成", detail_source)
        self.assertIn("未達", detail_source)


if __name__ == "__main__":
    unittest.main()
