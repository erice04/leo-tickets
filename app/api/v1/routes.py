import io

from flask import Blueprint, current_app, jsonify, request, send_file

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
    return jsonify({"status": "ok", "frontend": "react"})


@bp.get("/scanner/bootstrap")
def scanner_bootstrap():
    """Public config for scanner kiosks (mirrors legacy embedded API key)."""
    key = current_app.config.get("SCANNER_API_KEY", "")
    return jsonify({"scanner_api_key": key if key else ""})


@bp.get("/theme")
def get_theme():
    settings = event_service.get_event_settings()
    theme = settings.default_theme if settings.default_theme in ("light", "dark") else "light"
    return jsonify({"default_theme": theme})


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
    contact_email = body.get("contact_email")
    default_theme = body.get("default_theme")
    postcard_enabled = body.get("postcard_enabled")
    postcard_stamp_default = body.get("postcard_stamp_default")
    postcard_stamp_orientation = body.get("postcard_stamp_orientation")
    postcard_stamp_preset = body.get("postcard_stamp_preset")
    watermark_preset = body.get("watermark_preset")

    if (
        title is None
        and image_visible is None
        and contact_email is None
        and default_theme is None
        and postcard_enabled is None
        and postcard_stamp_default is None
        and postcard_stamp_orientation is None
        and postcard_stamp_preset is None
        and watermark_preset is None
    ):
        return _error(
            "BAD_REQUEST",
            "Provide title, image_visible, contact_email, default_theme, postcard_enabled, postcard_stamp_default, postcard_stamp_orientation, postcard_stamp_preset, and/or watermark_preset",
            400,
        )

    if default_theme is not None and default_theme not in ("light", "dark"):
        return _error("BAD_REQUEST", "default_theme must be light or dark", 400)

    if postcard_stamp_orientation is not None and postcard_stamp_orientation not in (
        "vertical",
        "horizontal",
    ):
        return _error(
            "BAD_REQUEST",
            "postcard_stamp_orientation must be vertical or horizontal",
            400,
        )

    if postcard_stamp_preset is not None:
        if postcard_stamp_preset not in (
            "yale_bowl",
            "sterling",
            "leo",
            "rugby",
            "ink",
            "custom",
        ):
            return _error("BAD_REQUEST", "Invalid postcard_stamp_preset", 400)
        settings = event_service.set_postcard_stamp_preset(postcard_stamp_preset)
        if (
            title is None
            and image_visible is None
            and contact_email is None
            and default_theme is None
            and postcard_enabled is None
            and postcard_stamp_default is None
            and postcard_stamp_orientation is None
            and watermark_preset is None
        ):
            return jsonify(settings.to_dict())

    if watermark_preset is not None:
        if watermark_preset not in ("none", "leo", "rugby", "ink"):
            return _error("BAD_REQUEST", "watermark_preset must be none, leo, rugby, or ink", 400)
        settings = event_service.set_watermark_preset(watermark_preset)
        if (
            title is None
            and image_visible is None
            and contact_email is None
            and default_theme is None
            and postcard_enabled is None
            and postcard_stamp_default is None
            and postcard_stamp_orientation is None
            and postcard_stamp_preset is None
        ):
            return jsonify(settings.to_dict())

    settings = event_service.update_event_settings(
        title=title,
        image_visible=image_visible if image_visible is not None else None,
        contact_email=contact_email if contact_email is not None else None,
        default_theme=default_theme if default_theme is not None else None,
        postcard_enabled=postcard_enabled if postcard_enabled is not None else None,
        postcard_stamp_default=postcard_stamp_default if postcard_stamp_default is not None else None,
        postcard_stamp_orientation=postcard_stamp_orientation
        if postcard_stamp_orientation is not None
        else None,
    )
    return jsonify(settings.to_dict())


@bp.put("/event/watermark")
@permission_required("event:write", api=True)
def upload_watermark():
    file = request.files.get("file")
    if not file or not file.filename:
        return _error("BAD_REQUEST", "file is required", 400)
    raw = file.read()
    try:
        settings = event_service.set_watermark_image(raw, file.content_type or "")
    except ValueError as exc:
        return _error("BAD_REQUEST", str(exc), 400)
    return jsonify(settings.to_dict())


@bp.delete("/event/watermark")
@permission_required("event:write", api=True)
def delete_watermark():
    settings = event_service.clear_watermark_image()
    return jsonify(settings.to_dict())


@bp.get("/event/watermark")
@permission_required("event:read", api=True)
def get_event_watermark():
    payload = event_service.get_watermark_payload()
    if payload is None:
        return _error("NOT_FOUND", "No custom watermark uploaded", 404)
    data, content_type = payload
    return send_file(
        io.BytesIO(data),
        mimetype=content_type,
        download_name="watermark.png",
        max_age=0,
    )


@bp.get("/ticket/watermark")
@api_auth_required
def get_ticket_watermark():
    ctx = get_auth_context()
    if ctx.auth_method != "session" or not is_attendee(ctx.email):
        return _error("FORBIDDEN", "Ticket watermark requires guest session", 403)
    payload = event_service.get_watermark_payload()
    if payload is None:
        return _error("NOT_FOUND", "No custom watermark uploaded", 404)
    data, content_type = payload
    return send_file(
        io.BytesIO(data),
        mimetype=content_type,
        download_name="watermark.png",
        max_age=300,
    )


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
        settings = event_service.get_event_settings()
        return (
            jsonify(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Email is not on the guest list",
                    },
                    "contact_email": settings.contact_email,
                }
            ),
            403,
        )

    settings = event_service.get_event_settings()
    logo_bytes = event_service.resolve_qr_logo_bytes(settings)
    qr_code = generate_qr(
        qr_encode(ctx.email),
        logo_bytes=logo_bytes,
        embed_logo=logo_bytes is not None,
    )
    return jsonify(
        {
            "title": settings.title,
            "email": ctx.email,
            "qr_payload": qr_encode(ctx.email),
            "qr_code_base64": qr_code,
            "postcard_enabled": settings.postcard_enabled,
            "postcard_stamp_preset": settings.postcard_stamp_preset,
            "watermark_preset": settings.watermark_preset,
            "has_custom_watermark": settings.watermark_image is not None,
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
