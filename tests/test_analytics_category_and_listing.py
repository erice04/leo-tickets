from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import ScanLog, YaleStudent
from app.services import analytics

BASE = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _add_scan(email, when=BASE):
    db.session.add(ScanLog(email=email, scanned_at=when))


def test_category_summary_matches_case_insensitively(app):
    db.session.add(YaleStudent(email="Foo@Yale.edu", year="2026"))
    _add_scan("foo@yale.edu")  # scan_logs is written lowercase; directory row is mixed-case
    _add_scan("bar@yale.edu")  # yale domain, no directory row
    _add_scan("guest@gmail.com")  # not yale at all
    db.session.commit()

    summary = analytics.get_category_summary()
    assert summary == {
        "yale_in_directory": 1,
        "yale_not_in_directory": 1,
        "non_yale": 1,
        "total": 3,
    }


def test_category_summary_day_filter(app):
    _add_scan("a@gmail.com", BASE)
    _add_scan("b@gmail.com", BASE + timedelta(days=1))
    db.session.commit()

    summary = analytics.get_category_summary(day=BASE.date())
    assert summary["total"] == 1


def test_category_summary_start_end_filter(app):
    _add_scan("a@gmail.com", BASE)
    _add_scan("b@gmail.com", BASE + timedelta(hours=5))
    db.session.commit()

    summary = analytics.get_category_summary(start=BASE, end=BASE + timedelta(hours=1))
    assert summary["total"] == 1


def test_list_scans_with_directory_sort_and_paginate(app):
    db.session.add(YaleStudent(email="a@yale.edu", year="2026"))
    _add_scan("a@yale.edu", BASE)
    _add_scan("b@gmail.com", BASE + timedelta(minutes=1))
    _add_scan("c@yale.edu", BASE + timedelta(minutes=2))
    db.session.commit()

    items, total = analytics.list_scans_with_directory(
        sort_by="scanned_at", sort_dir="asc", limit=2, offset=0
    )
    assert total == 3
    assert [item["email"] for item in items] == ["a@yale.edu", "b@gmail.com"]
    assert items[0]["category"] == "yale_in_directory"
    assert items[1]["category"] == "non_yale"


def test_list_scans_with_directory_category_and_grade_filter(app):
    db.session.add(YaleStudent(email="a@yale.edu", year="2026"))
    _add_scan("a@yale.edu", BASE)
    _add_scan("b@yale.edu", BASE)
    _add_scan("c@gmail.com", BASE)
    db.session.commit()

    items, total = analytics.list_scans_with_directory(category="yale_not_in_directory")
    assert total == 1
    assert items[0]["email"] == "b@yale.edu"

    items, total = analytics.list_scans_with_directory(grade="2026")
    assert total == 1
    assert items[0]["email"] == "a@yale.edu"


def test_list_scans_with_directory_rejects_unknown_sort_or_category(app):
    with pytest.raises(ValueError):
        analytics.list_scans_with_directory(sort_by="nope")
    with pytest.raises(ValueError):
        analytics.list_scans_with_directory(category="nope")


def test_list_scans_with_directory_includes_name_blank_when_not_in_directory(app):
    db.session.add(YaleStudent(email="a@yale.edu", name="Alice Yale", year="2026"))
    _add_scan("a@yale.edu", BASE)
    _add_scan("nobody@yale.edu", BASE)
    db.session.commit()

    items, total = analytics.list_scans_with_directory(sort_by="email", sort_dir="asc")
    assert total == 2
    by_email = {item["email"]: item["name"] for item in items}
    assert by_email["a@yale.edu"] == "Alice Yale"
    assert by_email["nobody@yale.edu"] is None


def test_list_scans_with_directory_search_matches_email_name_or_grade(app):
    db.session.add(YaleStudent(email="a@yale.edu", name="Alice Anderson", year="2026"))
    db.session.add(YaleStudent(email="b@yale.edu", name="Bob Brown", year="2027"))
    _add_scan("a@yale.edu", BASE)
    _add_scan("b@yale.edu", BASE)
    _add_scan("guest@gmail.com", BASE)
    db.session.commit()

    items, total = analytics.list_scans_with_directory(search="anderson")
    assert total == 1
    assert items[0]["email"] == "a@yale.edu"

    items, total = analytics.list_scans_with_directory(search="2027")
    assert total == 1
    assert items[0]["email"] == "b@yale.edu"

    items, total = analytics.list_scans_with_directory(search="guest")
    assert total == 1
    assert items[0]["email"] == "guest@gmail.com"
