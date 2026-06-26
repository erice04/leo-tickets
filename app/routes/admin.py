from flask import Blueprint, jsonify, render_template, request

from app.auth.decorators import admin_required
from app.services import events as event_service

bp = Blueprint("admin", __name__)
ADMIN_TEMPLATE = "admin_panel.html"


def _admin_context(**extra):
    settings = event_service.get_event_settings()
    context = {
        "image_visibility": settings.image_visible,
        "ticket_title": settings.title,
        "allowed_emails_text": "\n".join(event_service.list_allowed_emails()),
        "blacklist_text": "\n".join(event_service.list_blacklisted_emails()),
        "saved": extra.pop("saved", None),
    }
    context.update(extra)
    return context


@bp.route("/admin")
@admin_required
def admin():
    return render_template(ADMIN_TEMPLATE, **_admin_context())


@bp.route("/admin/emails", methods=["POST"])
@admin_required
def admin_emails():
    entered_text = request.form.get("email_text_box", "")
    lines = [line.strip() for line in entered_text.splitlines() if line.strip()]
    event_service.replace_allowed_emails(lines)
    return render_template(ADMIN_TEMPLATE, **_admin_context(saved="Guest list updated."))


@bp.route("/admin/ticket-info", methods=["POST"])
@admin_required
def admin_ticket_info():
    title = request.form.get("title_text_box", "").strip()
    event_service.update_event_settings(title=title or None)
    return render_template(ADMIN_TEMPLATE, **_admin_context(saved="Ticket info updated."))


@bp.route("/admin/blacklist/display")
@admin_required
def display_blacklist():
    text = "\n".join(event_service.list_blacklisted_emails())
    return render_template(
        "display_emails.html",
        title="Blacklist",
        heading="Blacklist",
        text=text or "(empty)",
    )


@bp.route("/admin/blacklist", methods=["POST"])
@admin_required
def admin_blacklist():
    entered_text = request.form.get("blacklist_text_box", "")
    lines = [line.strip() for line in entered_text.splitlines() if line.strip()]
    event_service.replace_blacklisted_emails(lines)
    return render_template(ADMIN_TEMPLATE, **_admin_context(saved="Blacklist updated."))


@bp.route("/admin/toggle_image", methods=["POST"])
@admin_required
def admin_toggle_image():
    settings = event_service.toggle_image_visibility()
    return jsonify({"status": "success", "visibility": settings.image_visible})


@bp.route("/admin/display")
@admin_required
def display_text():
    text = "\n".join(event_service.list_allowed_emails())
    return render_template(
        "display_emails.html",
        title="Guest List",
        heading="Email List",
        text=text,
    )


@bp.route("/admin/log")
@admin_required
def display_log():
    from app.services import scans as scan_service

    logs, _ = scan_service.list_scans(limit=500)
    rows = "".join(
        f"<tr><td>{log.email}</td><td>{log.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>"
        for log in logs
    )
    table = (
        "<table border='1' class='dataframe'>"
        "<thead><tr><th>Data</th><th>Timestamp</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )
    return render_template("display_log.html", table=table)
