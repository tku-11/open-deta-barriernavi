"""P4のFlaskアプリケーションファクトリ回帰テスト。"""

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from api_server import app, create_app  # noqa: E402


class AppFactoryTests(unittest.TestCase):
    def test_create_app_registers_legacy_route_contracts(self):
        created_app = create_app()
        rules = {rule.rule for rule in created_app.url_map.iter_rules()}

        self.assertIsNot(created_app, app)
        self.assertTrue(app.config["SECRET_KEY"])
        self.assertTrue({
            "/api/auth/login",
            "/api/body/stations",
            "/api/stations",
            "/api/stations/averages",
            "/api/stations/medians",
            "/api/stations/search",
            "/api/lines",
        }.issubset(rules))


if __name__ == "__main__":
    unittest.main()
