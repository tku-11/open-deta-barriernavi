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

        metrics_response = self.client.get("/dist/metrics.js")
        self.assertEqual(metrics_response.status_code, 200)
        self.assertIn(b"BODY_METRICS", metrics_response.data)

        auth_response = self.client.get("/dist/auth.js")
        self.assertEqual(auth_response.status_code, 200)
        self.assertIn(b"clearClientAuthState", auth_response.data)

    def test_api_dependent_page_scripts_are_loaded_as_es_modules(self):
        expected_scripts = {
            "/": b'type="module" src="/dist/login.js"',
            "/login": b'type="module" src="/dist/login.js"',
            "/home": b'type="module" src="/dist/home.js"',
            "/hearing": b'type="module" src="/dist/index.js"',
            "/vision": b'type="module" src="/dist/index.js"',
            "/profile": b'type="module" src="/dist/profile.js"',
            "/detail": b'type="module" src="/dist/detail.js"',
        }
        for path, expected_script in expected_scripts.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(expected_script, response.data)


if __name__ == "__main__":
    unittest.main()
