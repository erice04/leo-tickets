import pytest

from app.extensions import db
from app.models import YaleStudent
from app.services import database_browser

ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}
SCANNER_HEADERS = {"X-API-Key": "test-scanner-key"}


def _add_student(email, name, year="2026"):
    db.session.add(YaleStudent(email=email, name=name, year=year))


def test_browse_yale_students_excludes_updated_at(app):
    with app.app_context():
        _add_student("a@yale.edu", "A Student")
        db.session.commit()

        columns, items, total = database_browser.browse_yale_students()
        assert "updated_at" not in columns
        assert total == 1
        assert "updated_at" not in items[0]


def test_browse_yale_students_paginates_and_sorts(app):
    with app.app_context():
        _add_student("b@yale.edu", "B Student")
        _add_student("a@yale.edu", "A Student")
        db.session.commit()

        columns, items, total = database_browser.browse_yale_students(
            sort_by="email", sort_dir="asc", limit=10, offset=0
        )
        assert "email" in columns
        assert total == 2
        assert [row["email"] for row in items] == ["a@yale.edu", "b@yale.edu"]


def test_browse_yale_students_rejects_unknown_column(app):
    with app.app_context():
        with pytest.raises(ValueError):
            database_browser.browse_yale_students(sort_by="not_a_real_column")
        with pytest.raises(ValueError):
            database_browser.browse_yale_students(sort_by="updated_at")


def test_database_route_rejects_unauthenticated(app):
    client = app.test_client()
    resp = client.get("/api/v1/database/yale-students")
    assert resp.status_code == 401


def test_database_route_rejects_scanner_role(app):
    client = app.test_client()
    resp = client.get("/api/v1/database/yale-students", headers=SCANNER_HEADERS)
    assert resp.status_code == 403


def test_database_route_allows_admin_and_omits_updated_at(app):
    with app.app_context():
        _add_student("x@yale.edu", "X Student")
        db.session.commit()

    client = app.test_client()
    resp = client.get("/api/v1/database/yale-students", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) >= {"columns", "items", "total", "limit", "offset"}
    assert "updated_at" not in body["columns"]
    assert body["total"] == 1


def test_database_route_rejects_bad_sort(app):
    client = app.test_client()
    resp = client.get(
        "/api/v1/database/yale-students?sort_by=updated_at", headers=ADMIN_HEADERS
    )
    assert resp.status_code == 400


def test_browse_yale_students_search_matches_email_name_or_netid(app):
    with app.app_context():
        db.session.add(YaleStudent(email="jsmith@yale.edu", name="Jane Smith", netid="js123", year="2026"))
        db.session.add(YaleStudent(email="bwong@yale.edu", name="Bob Wong", netid="bw456", year="2027"))
        db.session.commit()

        _, items, total = database_browser.browse_yale_students(search="smith")
        assert total == 1
        assert items[0]["email"] == "jsmith@yale.edu"

        _, items, total = database_browser.browse_yale_students(search="BW456")
        assert total == 1
        assert items[0]["email"] == "bwong@yale.edu"

        _, items, total = database_browser.browse_yale_students(search="yale.edu")
        assert total == 2


def test_database_route_search_param(app):
    with app.app_context():
        db.session.add(YaleStudent(email="findme@yale.edu", name="Findable Person", year="2026"))
        db.session.add(YaleStudent(email="other@yale.edu", name="Other Person", year="2026"))
        db.session.commit()

    client = app.test_client()
    resp = client.get(
        "/api/v1/database/yale-students?search=findable", headers=ADMIN_HEADERS
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "findme@yale.edu"
