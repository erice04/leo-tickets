from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request

from app.auth import google_auth
from app.auth.decorators import get_auth_context, login_required, permission_required
from app.auth.rbac import is_attendee
from app.services import events as event_service
from app.services import scans as scan_service
from app.services.qr import generate_qr, qr_encode

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    user_info = google_auth.get_user_info()
    user_email = user_info["email"]
    settings = event_service.get_event_settings()

    if not is_attendee(user_email):
        return render_template("email_error.html", email=user_email)

    qr_code = generate_qr(qr_encode(user_email))
    initial_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template(
        "index.html",
        title=settings.title,
        qr_code=qr_code,
        initial_time=initial_time,
    )


@bp.route("/scanner")
def scan():
    """Public scanner UI (legacy behavior). POST /scanner_result requires API key or scanner session."""
    scanner_api_key = current_app.config.get("SCANNER_API_KEY", "")
    return render_template(
        "scanner.html",
        scanner_api_key=scanner_api_key if scanner_api_key else "",
    )


@bp.route("/scanner_result", methods=["POST"])
@permission_required("scans:write", api=True)
def save_scanned_data():
    data = request.get_json(silent=True) or {}
    decoded_text = data.get("data", "")
    ctx = get_auth_context()
    scanned_by = None if ctx and ctx.email == "api-key" else (ctx.email if ctx else None)
    return jsonify(scan_service.process_scan(decoded_text, scanned_by=scanned_by))
