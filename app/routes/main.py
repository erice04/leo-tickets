from flask import Blueprint, jsonify, request

from app.auth.decorators import permission_required
from app.services import scans as scan_service

bp = Blueprint("main", __name__)


@bp.route("/scanner_result", methods=["POST"])
@permission_required("scans:write")
def save_scanned_data():
    data = request.get_json(silent=True) or {}
    decoded_text = data.get("data", "")
    return jsonify(scan_service.process_scan(decoded_text))
