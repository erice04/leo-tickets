from datetime import datetime, timezone

from app.extensions import db
from app.models import ScanLog

HEADERS = {"X-API-Key": "test-scanner-key"}


def test_analytics_endpoints_require_auth(app):
    client = app.test_client()
    resp = client.get("/api/v1/analytics/scan-summary")
    assert resp.status_code == 401


def test_analytics_endpoints_return_expected_shapes(app):
    with app.app_context():
        db.session.add(
            ScanLog(email="a@yale.edu", scanned_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        )
        db.session.commit()

    client = app.test_client()

    resp = client.get("/api/v1/analytics/scan-summary", headers=HEADERS)
    assert resp.status_code == 200
    assert set(resp.get_json()) == {
        "yale_in_directory",
        "yale_not_in_directory",
        "non_yale",
        "total",
    }

    resp = client.get("/api/v1/analytics/scans", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) >= {"items", "total", "limit", "offset"}
    assert body["total"] == 1

    resp = client.get("/api/v1/analytics/session-frequency", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 1

    resp = client.get("/api/v1/analytics/night-counts", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 1


def test_analytics_scans_endpoint_rejects_bad_sort(app):
    client = app.test_client()
    resp = client.get("/api/v1/analytics/scans?sort_by=bogus", headers=HEADERS)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "BAD_REQUEST"


def test_analytics_endpoint_rejects_bad_date(app):
    client = app.test_client()
    resp = client.get("/api/v1/analytics/scan-summary?day=not-a-date", headers=HEADERS)
    assert resp.status_code == 400
