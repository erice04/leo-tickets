from datetime import datetime, timedelta, timezone

from flask import current_app

from app.extensions import db
from app.models import EventSettings, ScanLog, YaleStudent
from app.services.qr import qr_decode


def process_scan(payload: str, scanned_by: str | None = None) -> dict:
    email = qr_decode(payload).strip().lower()
    now = datetime.now(timezone.utc)
    dedup_seconds = current_app.config["SCAN_DEDUP_SECONDS"]

    recent = ScanLog.query.filter(
        ScanLog.email == email,
        ScanLog.scanned_at > now - timedelta(seconds=dedup_seconds),
    ).first()

    duplicate = recent is not None
    if not duplicate:
        db.session.add(ScanLog(email=email, scanned_at=now, scanned_by=scanned_by))
        db.session.commit()

    student = db.session.get(YaleStudent, email)
    settings = EventSettings.get()
    include_image = settings.image_visible

    if student and student.email != "none":
        result = student.to_public_dict(include_image=include_image)
        result["status"] = "success"
        result["duplicate"] = duplicate
        return result

    return {
        "status": "success",
        "email": email,
        "name": "N/A",
        "image_url": "",
        "duplicate": duplicate,
    }


def list_scans(*, limit: int = 100, offset: int = 0) -> tuple[list[ScanLog], int]:
    query = ScanLog.query.order_by(ScanLog.scanned_at.desc())
    total = query.count()
    logs = query.offset(offset).limit(limit).all()
    return logs, total
