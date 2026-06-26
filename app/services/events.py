from app.extensions import db
from app.models import AllowedEmail, BlacklistedEmail, EventSettings


def get_event_settings() -> EventSettings:
    return EventSettings.get()


def update_event_settings(*, title: str | None = None, image_visible: bool | None = None) -> EventSettings:
    settings = EventSettings.get()
    if title is not None:
        settings.title = title
    if image_visible is not None:
        settings.image_visible = image_visible
    db.session.commit()
    return settings


def toggle_image_visibility() -> EventSettings:
    settings = EventSettings.get()
    settings.image_visible = not settings.image_visible
    db.session.commit()
    return settings


def list_allowed_emails() -> list[str]:
    rows = AllowedEmail.query.order_by(AllowedEmail.email.asc()).all()
    return [row.email for row in rows]


def list_blacklisted_emails() -> list[str]:
    rows = BlacklistedEmail.query.order_by(BlacklistedEmail.email.asc()).all()
    return [row.email for row in rows]


def replace_allowed_emails(emails: list[str]) -> list[str]:
    normalized = sorted({email.strip().lower() for email in emails if email.strip()})
    AllowedEmail.query.delete()
    for email in normalized:
        db.session.add(AllowedEmail(email=email))
    db.session.commit()
    return normalized


def replace_blacklisted_emails(emails: list[str]) -> list[str]:
    normalized = sorted({email.strip().lower() for email in emails if email.strip()})
    BlacklistedEmail.query.delete()
    for email in normalized:
        db.session.add(BlacklistedEmail(email=email))
    # Remove blacklisted addresses from the guest list if present
    if normalized:
        AllowedEmail.query.filter(AllowedEmail.email.in_(normalized)).delete(
            synchronize_session=False
        )
    db.session.commit()
    return normalized
