"""静的ページ・フロントエンド配布物を提供するBlueprint。"""

from pathlib import Path

from flask import Blueprint, send_file, send_from_directory


def create_pages_blueprint(frontend_dir: Path, view_dir: Path, dist_dir: Path) -> Blueprint:
    """従来のページURLを保持するBlueprintを生成する。"""
    pages = Blueprint("pages", __name__)

    page_files = {
        "/": "login.html",
        "/login": "login.html",
        "/home": "home.html",
        "/index": "index.html",
        "/hearing": "hearing.html",
        "/vision": "vision.html",
        "/profile": "profile.html",
        "/detail": "detail.html",
    }

    for route, filename in page_files.items():
        endpoint = "page_" + ("root" if route == "/" else route.strip("/"))

        def page(filename: str = filename):
            return send_file(view_dir / filename)

        pages.add_url_rule(route, endpoint=endpoint, view_func=page)

    @pages.get("/styles.css")
    def styles_css():
        return send_file(frontend_dir / "styles.css")

    @pages.get("/dist/<path:filename>")
    def dist_files(filename: str):
        return send_from_directory(dist_dir, filename)

    return pages
