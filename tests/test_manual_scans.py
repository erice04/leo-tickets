import pytest

from app.extensions import db
from app.models import ScanLog
from app.services import scans as scan_service

ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}
SCANNER_HEADERS = {"X-API-Key": "test-scanner-key"}


def test_create_manual_scan_normalizes_and_defaults_time(app):
    with app.app_context():
        log = scan_service.create_manual_scan("Person@Yale.edu")
        assert log.email == "person@yale.edu"
        assert log.scanned_at is not None


def test_create_manual_scan_rejects_blank_email(app):
    with app.app_context():
        with pytest.raises(ValueError):
            scan_service.create_manual_scan("   ")


def test_delete_scan_removes_row_and_reports_missing(app):
    with app.app_context():
        log = scan_service.create_manual_scan("gone@yale.edu")
        scan_id = log.id
        assert scan_service.delete_scan(scan_id) is True
        assert db.session.get(ScanLog, scan_id) is None
        assert scan_service.delete_scan(scan_id) is False


def test_manual_scan_route_requires_manage_permission(app):
    client = app.test_client()
    resp = client.post("/api/v1/scans/manual", json={"email": "a@yale.edu"})
    assert resp.status_code == 401


def test_manual_scan_route_creates_and_deletes(app):
    client = app.test_client()
    resp = client.post(
        "/api/v1/scans/manual",
        json={"email": "Manual@Yale.edu", "scanned_at": "2026-04-25T10:00:00"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["email"] == "manual@yale.edu"

    resp = client.delete(f"/api/v1/scans/{body['id']}", headers=ADMIN_HEADERS)
    assert resp.status_code == 204

    resp = client.delete(f"/api/v1/scans/{body['id']}", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_manual_scan_route_rejects_missing_email(app):
    client = app.test_client()
    resp = client.post("/api/v1/scans/manual", json={}, headers=ADMIN_HEADERS)
    assert resp.status_code == 400


def test_scanner_role_cannot_manage_scans(app):
    client = app.test_client()
    resp = client.post(
        "/api/v1/scans/manual", json={"email": "a@yale.edu"}, headers=SCANNER_HEADERS
    )
    assert resp.status_code == 403
