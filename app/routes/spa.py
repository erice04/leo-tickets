import os

from flask import Blueprint, current_app, send_from_directory

bp = Blueprint("spa", __name__)

# Client-side routes handled by React Router (serve index.html).
_SPA_ROUTES = frozenset({"scanner", "admin"})


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def serve_spa(path: str):
    """Serve React build for UI routes and static assets from app/static."""
    if path.startswith("api/") or path.startswith("google/"):
        return {"error": "Not found"}, 404

    static_root = current_app.static_folder
    if not static_root:
        return _build_missing_message(), 503

    if path:
        disk_path = os.path.join(static_root, path)
        if os.path.isfile(disk_path):
            return send_from_directory(static_root, path)

        is_spa_route = path in _SPA_ROUTES or path.startswith("admin/")
        if not is_spa_route:
            return {"error": "Not found"}, 404

    index = os.path.join(static_root, "index.html")
    if not os.path.isfile(index):
        return _build_missing_message(), 503

    return send_from_directory(static_root, "index.html")


def _build_missing_message() -> str:
    return "Frontend not built. Run: cd frontend && npm install && npm run build"
