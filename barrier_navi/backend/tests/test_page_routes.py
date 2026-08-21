"""静的ページBlueprintのP2回帰テスト。"""

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from api_server import app  # noqa: E402


class PageRoutesTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_existing_page_urls_return_html(self):
        for path in ("/", "/login", "/home", "/index", "/hearing", "/vision", "/profile", "/detail"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response.content_type)

    def test_frontend_es_modules_are_served_from_existing_dist_url(self):
        response = self.client.get("/dist/api.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"API_BASE_URL", response.data)


if __name__ == "__main__":
    unittest.main()
