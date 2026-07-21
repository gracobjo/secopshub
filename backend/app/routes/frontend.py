import os

from flask import Blueprint, redirect, send_from_directory

frontend_bp = Blueprint("frontend", __name__)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
FRONTEND_DIST = os.path.join(BACKEND_DIR, "..", "frontend", "dist")
FRONTEND_PUBLIC = os.path.join(BACKEND_DIR, "..", "frontend", "public")
FRONTEND_DEV_URL = "http://localhost:5173"


def _dist_exists() -> bool:
    return os.path.isfile(os.path.join(FRONTEND_DIST, "index.html"))


@frontend_bp.route("/")
def index():
    if _dist_exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return redirect(FRONTEND_DEV_URL)


@frontend_bp.route("/favicon.ico")
def favicon():
    for folder, name in [
        (FRONTEND_DIST, "favicon.svg"),
        (FRONTEND_PUBLIC, "favicon.svg"),
        (FRONTEND_DIST, "favicon.ico"),
        (FRONTEND_PUBLIC, "favicon.ico"),
    ]:
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            return send_from_directory(folder, name)
    return "", 204


@frontend_bp.route("/<path:path>")
def spa_fallback(path: str):
    if path.startswith("api/"):
        return {"error": "Not found"}, 404

    file_path = os.path.join(FRONTEND_DIST, path)
    if _dist_exists() and os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIST, path)

    if _dist_exists():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return redirect(FRONTEND_DEV_URL)
