import io
from pathlib import Path

from PIL import Image

from app.extensions import db
from app.models import AllowedEmail, BlacklistedEmail, EventSettings

MAX_WATERMARK_BYTES = 512 * 1024
ALLOWED_WATERMARK_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})
MAX_WATERMARK_DIMENSION = 512
WATERMARK_PRESETS = frozenset({"none", "leo", "rugby", "ink", "custom"})
STAMP_PRESETS = frozenset({"yale_bowl", "sterling", "leo", "rugby", "ink", "custom"})
LOGO_PRESETS = frozenset({"none", "leo", "rugby", "ink"})
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
PRESET_LOGO_PATHS = {
    "leo": ASSETS_DIR / "leo-logo.png",
    "rugby": ASSETS_DIR / "rugby-150-logo.png",
    "ink": ASSETS_DIR / "ink-logo.png",
}


def get_event_settings() -> EventSettings:
    return EventSettings.get()


def update_event_settings(
    *,
    title: str | None = None,
    image_visible: bool | None = None,
    contact_email: str | None = None,
    default_theme: str | None = None,
    postcard_enabled: bool | None = None,
    postcard_stamp_default: bool | None = None,
    postcard_stamp_orientation: str | None = None,
    postcard_stamp_preset: str | None = None,
    watermark_preset: str | None = None,
) -> EventSettings:
    settings = EventSettings.get()
    if title is not None:
        settings.title = title
    if image_visible is not None:
        settings.image_visible = image_visible
    if contact_email is not None:
        settings.contact_email = contact_email.strip().lower()
    if default_theme is not None:
        settings.default_theme = default_theme
    if postcard_enabled is not None:
        settings.postcard_enabled = postcard_enabled
    if postcard_stamp_default is not None:
        settings.postcard_stamp_default = postcard_stamp_default
    if postcard_stamp_orientation is not None:
        settings.postcard_stamp_orientation = postcard_stamp_orientation
    if postcard_stamp_preset is not None:
        settings.postcard_stamp_preset = postcard_stamp_preset
    if watermark_preset is not None:
        settings.watermark_preset = watermark_preset
    db.session.commit()
    return settings


def _process_watermark(raw: bytes, content_type: str) -> tuple[bytes, str]:
    if len(raw) > MAX_WATERMARK_BYTES:
        raise ValueError(f"Image must be {MAX_WATERMARK_BYTES // 1024} KB or smaller.")

    if content_type not in ALLOWED_WATERMARK_TYPES:
        raise ValueError("Use PNG, JPEG, or WebP.")

    img = Image.open(io.BytesIO(raw))
    img.thumbnail((MAX_WATERMARK_DIMENSION, MAX_WATERMARK_DIMENSION), Image.Resampling.LANCZOS)

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue(), "image/png"


def set_watermark_image(raw: bytes, content_type: str) -> EventSettings:
    processed, mime = _process_watermark(raw, content_type)
    settings = EventSettings.get()
    settings.watermark_image = processed
    settings.watermark_content_type = mime
    settings.watermark_preset = "custom"
    db.session.commit()
    return settings


def set_postcard_stamp_preset(preset: str) -> EventSettings:
    if preset not in STAMP_PRESETS:
        raise ValueError("Invalid stamp preset.")
    settings = EventSettings.get()
    settings.postcard_stamp_preset = preset
    if preset == "yale_bowl":
        settings.postcard_stamp_orientation = "horizontal"
        settings.postcard_stamp_default = True
    elif preset == "sterling":
        settings.postcard_stamp_orientation = "vertical"
        settings.postcard_stamp_default = True
    elif preset in {"leo", "rugby", "ink"}:
        settings.postcard_stamp_orientation = "vertical"
        settings.postcard_stamp_default = True
    else:
        settings.postcard_stamp_default = False
    db.session.commit()
    return settings


def set_watermark_preset(preset: str) -> EventSettings:
    if preset not in LOGO_PRESETS:
        raise ValueError("Invalid watermark preset.")
    settings = EventSettings.get()
    settings.watermark_preset = preset
    settings.watermark_image = None
    settings.watermark_content_type = None
    db.session.commit()
    return settings


def clear_watermark_image() -> EventSettings:
    return set_watermark_preset("none")


def resolve_qr_logo_bytes(settings: EventSettings | None = None) -> bytes | None:
    settings = settings or EventSettings.get()
    if settings.postcard_enabled:
        return None
    if settings.watermark_image is not None:
        return settings.watermark_image
    if settings.watermark_preset in LOGO_PRESETS - {"none"}:
        path = PRESET_LOGO_PATHS.get(settings.watermark_preset)
        if path and path.is_file():
            return path.read_bytes()
    return None


def resolve_watermark_bytes(settings: EventSettings | None = None) -> bytes | None:
    settings = settings or EventSettings.get()
    if settings.watermark_image is not None:
        return settings.watermark_image
    return None


def get_watermark_payload() -> tuple[bytes, str] | None:
    data = resolve_watermark_bytes()
    if data is None:
        return None
    settings = EventSettings.get()
    if settings.watermark_preset == "custom" and settings.watermark_content_type:
        return data, settings.watermark_content_type
    return data, "image/png"


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
    if normalized:
        AllowedEmail.query.filter(AllowedEmail.email.in_(normalized)).delete(
            synchronize_session=False
        )
    db.session.commit()
    return normalized
