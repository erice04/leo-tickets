from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import ScanLog, YaleStudent
from app.services import analytics

BASE = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}


def _add_scan(email, when):
    db.session.add(ScanLog(email=email, scanned_at=when))


def test_time_buckets_are_always_the_full_24_hour_cycle_zero_filled(app):
    _add_scan("a@yale.edu", BASE)
    db.session.commit()

    items, total = analytics.get_time_buckets(bucket_minutes=30)
    assert total == 48  # 24h / 30min, always present regardless of data
    assert sum(item["scans"] for item in items) == 1


def test_time_buckets_collapse_scans_from_different_dates_into_the_same_time_of_day(app):
    _add_scan("a@yale.edu", BASE)  # 2026-01-01 10:00 UTC
    _add_scan("b@yale.edu", BASE + timedelta(days=5))  # 2026-01-06 10:00 UTC -- same time of day
    db.session.commit()

    items, total = analytics.get_time_buckets(bucket_minutes=30)
    ten_am_bucket = next(item for item in items if item["bucket_start"] == "10:00")
    assert ten_am_bucket["scans"] == 2
    assert sum(item["scans"] for item in items) == 2


def test_time_buckets_stay_chronological_by_time_of_day_not_scan_order(app):
    _add_scan("a@yale.edu", BASE.replace(hour=13, minute=0))  # inserted first, later time-of-day
    _add_scan("b@yale.edu", BASE.replace(hour=10, minute=0))  # inserted second, earlier time-of-day
    db.session.commit()

    items, total = analytics.get_time_buckets(bucket_minutes=30, sort_by="bucket_start", sort_dir="asc")
    starts = [item["bucket_start"] for item in items]
    assert starts == sorted(starts)
    assert starts.index("10:00") < starts.index("13:00")


def test_time_buckets_custom_bucket_size(app):
    _add_scan("a@yale.edu", BASE)  # 10:00
    _add_scan("b@yale.edu", BASE + timedelta(minutes=45))  # 10:45

    db.session.commit()

    # With a 60-minute bucket, both scans land in the same hour-long window.
    items, total = analytics.get_time_buckets(bucket_minutes=60)
    assert total == 24
    ten_am_bucket = next(item for item in items if item["bucket_start"] == "10:00")
    assert ten_am_bucket["scans"] == 2


def test_time_buckets_respects_start_end_filters(app):
    _add_scan("a@yale.edu", BASE)  # inside the window
    _add_scan("b@yale.edu", BASE + timedelta(hours=5))  # outside the window

    db.session.commit()

    items, total = analytics.get_time_buckets(start=BASE, end=BASE + timedelta(hours=1))
    assert total == 48
    assert sum(item["scans"] for item in items) == 1


def test_time_buckets_grade_and_search_filters(app):
    db.session.add(YaleStudent(email="a@yale.edu", name="Alice", year="2026"))
    db.session.add(YaleStudent(email="b@yale.edu", name="Bob", year="2027"))
    _add_scan("a@yale.edu", BASE)
    _add_scan("b@yale.edu", BASE)
    db.session.commit()

    items, total = analytics.get_time_buckets(grade="2026")
    assert sum(item["scans"] for item in items) == 1

    items, total = analytics.get_time_buckets(search="alice")
    assert sum(item["scans"] for item in items) == 1


def test_time_buckets_rejects_bad_input(app):
    with pytest.raises(ValueError):
        analytics.get_time_buckets(sort_by="nope")
    with pytest.raises(ValueError):
        analytics.get_time_buckets(bucket_minutes=0)
    with pytest.raises(ValueError):
        analytics.get_time_buckets(bucket_minutes=7)  # doesn't divide evenly into 24h


def test_time_buckets_route(app):
    with app.app_context():
        _add_scan("a@yale.edu", BASE)
        _add_scan("b@yale.edu", BASE + timedelta(minutes=5))
        db.session.commit()

    client = app.test_client()
    resp = client.get("/api/v1/analytics/time-buckets", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 48
    assert sum(item["scans"] for item in body["items"]) == 2
