from flask import Blueprint, jsonify, request

from app.auth.decorators import get_auth_context, permission_required
from app.services import scans as scan_service

bp = Blueprint("main", __name__)


@bp.route("/scanner_result", methods=["POST"])
@permission_required("scans:write", api=True)
def save_scanned_data():
    data = request.get_json(silent=True) or {}
    decoded_text = data.get("data", "")
    ctx = get_auth_context()
    scanned_by = None if ctx and ctx.email == "api-key" else (ctx.email if ctx else None)
    return jsonify(scan_service.process_scan(decoded_text, scanned_by=scanned_by))
