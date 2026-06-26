from flask import Blueprint, jsonify, request

from app.auth.decorators import api_auth_required, get_auth_context, permission_required
from app.auth.rbac import is_attendee
from app.services import events as event_service
from app.services import scans as scan_service
from app.services import users as user_service
from app.services.qr import generate_qr, qr_encode

bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def _error(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.get("/me")
@api_auth_required
def me():
    ctx = get_auth_context()
    payload = ctx.to_dict()
    if ctx.auth_method == "session":
        payload["is_attendee"] = is_attendee(ctx.email)
    return jsonify(payload)


@bp.get("/event")
@permission_required("event:read", api=True)
def get_event():
    return jsonify(event_service.get_event_settings().to_dict())


@bp.patch("/event")
@permission_required("event:write", api=True)
def patch_event():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    image_visible = body.get("image_visible")

    if title is None and image_visible is None:
        return _error("BAD_REQUEST", "Provide title and/or image_visible", 400)

    settings = event_service.update_event_settings(
        title=title,
        image_visible=image_visible if image_visible is not None else None,
    )
    return jsonify(settings.to_dict())


@bp.get("/allowed-emails")
@permission_required("allowlist:read", api=True)
def get_allowed_emails():
    return jsonify({"emails": event_service.list_allowed_emails()})


@bp.put("/allowed-emails")
@permission_required("allowlist:write", api=True)
def put_allowed_emails():
    body = request.get_json(silent=True) or {}
    emails = body.get("emails")
    if not isinstance(emails, list):
        return _error("BAD_REQUEST", "emails must be a list of strings", 400)
    updated = event_service.replace_allowed_emails(emails)
    return jsonify({"emails": updated})


@bp.get("/blacklisted-emails")
@permission_required("allowlist:read", api=True)
def get_blacklisted_emails():
    return jsonify({"emails": event_service.list_blacklisted_emails()})


@bp.put("/blacklisted-emails")
@permission_required("allowlist:write", api=True)
def put_blacklisted_emails():
    body = request.get_json(silent=True) or {}
    emails = body.get("emails")
    if not isinstance(emails, list):
        return _error("BAD_REQUEST", "emails must be a list of strings", 400)
    updated = event_service.replace_blacklisted_emails(emails)
    return jsonify({"emails": updated})


@bp.get("/ticket")
@api_auth_required
def get_ticket():
    ctx = get_auth_context()
    if ctx.auth_method != "session":
        return _error("FORBIDDEN", "Ticket endpoint requires Google session login", 403)
    if not is_attendee(ctx.email):
        return _error("FORBIDDEN", "Email is not on the guest list", 403)

    settings = event_service.get_event_settings()
    qr_code = generate_qr(qr_encode(ctx.email))
    return jsonify(
        {
            "title": settings.title,
            "email": ctx.email,
            "qr_payload": qr_encode(ctx.email),
            "qr_code_base64": qr_code,
        }
    )


@bp.post("/scans")
@permission_required("scans:write", api=True)
def create_scan():
    body = request.get_json(silent=True) or {}
    payload = body.get("data") or body.get("payload")
    if not payload:
        return _error("BAD_REQUEST", "data or payload is required", 400)

    ctx = get_auth_context()
    scanned_by = None if ctx.email == "api-key" else ctx.email
    result = scan_service.process_scan(payload, scanned_by=scanned_by)
    return jsonify(result), 201


@bp.post("/scans/lookup")
@permission_required("scans:write", api=True)
def lookup_scan():
    body = request.get_json(silent=True) or {}
    payload = body.get("data") or body.get("payload")
    if not payload:
        return _error("BAD_REQUEST", "data or payload is required", 400)

    ctx = get_auth_context()
    scanned_by = None if ctx.email == "api-key" else ctx.email
    result = scan_service.process_scan(payload, scanned_by=scanned_by)
    return jsonify(result)


@bp.get("/scans")
@permission_required("scans:read", api=True)
def get_scans():
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = max(int(request.args.get("offset", 0)), 0)
    logs, total = scan_service.list_scans(limit=limit, offset=offset)
    return jsonify(
        {
            "items": [log.to_dict() for log in logs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


@bp.get("/users")
@permission_required("users:read", api=True)
def get_users():
    users = user_service.list_users()
    return jsonify({"items": [user.to_dict() for user in users]})


@bp.post("/users")
@permission_required("users:write", api=True)
def post_user():
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    roles = body.get("roles", [])
    if not email or not isinstance(roles, list):
        return _error("BAD_REQUEST", "email and roles[] are required", 400)

    user = user_service.create_or_update_user(
        email,
        roles,
        is_active=body.get("is_active", True),
    )
    return jsonify(user.to_dict()), 201


@bp.delete("/users/<int:user_id>")
@permission_required("users:write", api=True)
def delete_user(user_id: int):
    if not user_service.delete_user(user_id):
        return _error("NOT_FOUND", "User not found", 404)
    return "", 204
