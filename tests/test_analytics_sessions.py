"""Tests for the gaps-and-islands sessionization in app.services.analytics.

A "session" is a run of scans for one person where no gap between
consecutive scans exceeds session_gap_hours (default 8). These tests focus
on the boundary conditions that are easy to get subtly wrong: a lone scan
with no prior session, a gap landing exactly on the threshold, and a gap
one second past it.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import ScanLog, YaleStudent
from app.services import analytics

BASE = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _add_scan(email, when):
    db.session.add(ScanLog(email=email, scanned_at=when))


def test_single_scan_has_no_prior_session_and_counts_as_one(app):
    _add_scan("solo@yale.edu", BASE)
    db.session.commit()

    freq_items, freq_total = analytics.get_session_frequency(min_scans_in_session=1)
    assert freq_total == 1
    assert freq_items[0]["email"] == "solo@yale.edu"
    assert freq_items[0]["scans_in_session"] == 1

    night_items, night_total = analytics.get_night_counts(min_nights=1)
    assert night_total == 1
    assert night_items[0]["nights"] == 1
    assert night_items[0]["total_scans"] == 1


def test_gap_exactly_at_threshold_stays_in_one_session(app):
    email = "exact@yale.edu"
    _add_scan(email, BASE)
    _add_scan(email, BASE + timedelta(hours=8))  # exactly session_gap_hours
    db.session.commit()

    items, total = analytics.get_session_frequency(session_gap_hours=8, min_scans_in_session=1)
    assert total == 1
    assert items[0]["scans_in_session"] == 2

    nights, _ = analytics.get_night_counts(session_gap_hours=8)
    assert nights[0]["nights"] == 1
    assert nights[0]["total_scans"] == 2


def test_gap_one_second_over_threshold_splits_into_two_sessions(app):
    email = "over@yale.edu"
    _add_scan(email, BASE)
    _add_scan(email, BASE + timedelta(hours=8, seconds=1))  # one second past the threshold
    db.session.commit()

    items, total = analytics.get_session_frequency(session_gap_hours=8, min_scans_in_session=1)
    assert total == 2
    assert {item["scans_in_session"] for item in items} == {1}

    nights, _ = analytics.get_night_counts(session_gap_hours=8)
    assert nights[0]["nights"] == 2
    assert nights[0]["total_scans"] == 2


def test_gap_one_second_under_threshold_stays_in_one_session(app):
    email = "under@yale.edu"
    _add_scan(email, BASE)
    _add_scan(email, BASE + timedelta(hours=7, minutes=59, seconds=59))
    db.session.commit()

    items, total = analytics.get_session_frequency(session_gap_hours=8, min_scans_in_session=1)
    assert total == 1
    assert items[0]["scans_in_session"] == 2


def test_min_scans_in_session_filters_out_quiet_sessions(app):
    quiet = "quiet@yale.edu"
    busy = "busy@yale.edu"
    _add_scan(quiet, BASE)
    _add_scan(busy, BASE)
    _add_scan(busy, BASE + timedelta(minutes=5))
    _add_scan(busy, BASE + timedelta(minutes=10))
    db.session.commit()

    items, total = analytics.get_session_frequency(min_scans_in_session=2)
    assert total == 1
    assert items[0]["email"] == busy
    assert items[0]["scans_in_session"] == 3


def test_min_nights_filters_people_with_few_sessions(app):
    once = "once@yale.edu"
    frequent = "frequent@yale.edu"
    _add_scan(once, BASE)
    _add_scan(frequent, BASE)
    _add_scan(frequent, BASE + timedelta(hours=9))  # >8h gap -> new session
    _add_scan(frequent, BASE + timedelta(hours=18))  # >8h gap from previous -> new session again
    db.session.commit()

    items, total = analytics.get_night_counts(min_nights=2)
    assert total == 1
    assert items[0]["email"] == frequent
    assert items[0]["nights"] == 3
    assert items[0]["total_scans"] == 3


def test_sessions_are_independent_per_person(app):
    a, b = "a@yale.edu", "b@yale.edu"
    _add_scan(a, BASE)
    _add_scan(b, BASE + timedelta(minutes=1))
    db.session.commit()

    items, total = analytics.get_session_frequency()
    assert total == 2
    assert {item["email"] for item in items} == {a, b}
    assert all(item["scans_in_session"] == 1 for item in items)


def test_custom_session_gap_hours_changes_the_boundary(app):
    email = "custom@yale.edu"
    _add_scan(email, BASE)
    _add_scan(email, BASE + timedelta(hours=2))
    db.session.commit()

    # With a 1-hour gap threshold, a 2-hour gap splits the visit in two.
    items, total = analytics.get_session_frequency(session_gap_hours=1, min_scans_in_session=1)
    assert total == 2

    # With the default 8-hour threshold, the same scans are one session.
    items, total = analytics.get_session_frequency(session_gap_hours=8, min_scans_in_session=1)
    assert total == 1
    assert items[0]["scans_in_session"] == 2


def test_grade_filter_uses_yale_students_year(app):
    db.session.add(YaleStudent(email="senior@yale.edu", year="2026"))
    db.session.add(YaleStudent(email="junior@yale.edu", year="2027"))
    _add_scan("senior@yale.edu", BASE)
    _add_scan("junior@yale.edu", BASE)
    db.session.commit()

    items, total = analytics.get_session_frequency(grade="2026")
    assert total == 1
    assert items[0]["email"] == "senior@yale.edu"
    assert items[0]["grade"] == "2026"

    night_items, night_total = analytics.get_night_counts(grade="2027")
    assert night_total == 1
    assert night_items[0]["email"] == "junior@yale.edu"


def test_start_end_filters_restrict_which_scans_are_considered(app):
    email = "ranged@yale.edu"
    _add_scan(email, BASE)
    _add_scan(email, BASE + timedelta(hours=1))
    _add_scan(email, BASE + timedelta(days=2))  # outside the window entirely
    db.session.commit()

    items, total = analytics.get_session_frequency(
        start=BASE - timedelta(minutes=1), end=BASE + timedelta(hours=2)
    )
    assert total == 1
    assert items[0]["scans_in_session"] == 2


def test_session_frequency_pagination_and_sort(app):
    for i, email in enumerate(["p1@yale.edu", "p2@yale.edu", "p3@yale.edu"]):
        for _ in range(i + 1):
            _add_scan(email, BASE)
    db.session.commit()
    # p1 -> 1 scan/session, p2 -> 2, p3 -> 3 (all same instant, so one session each)

    items, total = analytics.get_session_frequency(
        sort_by="scans_in_session", sort_dir="desc", limit=2, offset=0
    )
    assert total == 3
    assert [item["scans_in_session"] for item in items] == [3, 2]

    items, total = analytics.get_session_frequency(
        sort_by="scans_in_session", sort_dir="desc", limit=2, offset=2
    )
    assert [item["scans_in_session"] for item in items] == [1]


def test_invalid_sort_by_raises_value_error(app):
    with pytest.raises(ValueError):
        analytics.get_session_frequency(sort_by="not_a_column")
    with pytest.raises(ValueError):
        analytics.get_night_counts(sort_dir="sideways")


def test_session_frequency_and_night_counts_include_name(app):
    db.session.add(YaleStudent(email="named@yale.edu", name="Named Person", year="2026"))
    _add_scan("named@yale.edu", BASE)
    _add_scan("noname@yale.edu", BASE)
    db.session.commit()

    items, _ = analytics.get_session_frequency(sort_by="email", sort_dir="asc")
    by_email = {item["email"]: item["name"] for item in items}
    assert by_email["named@yale.edu"] == "Named Person"
    assert by_email["noname@yale.edu"] is None

    night_items, _ = analytics.get_night_counts(sort_by="email", sort_dir="asc")
    by_email = {item["email"]: item["name"] for item in night_items}
    assert by_email["named@yale.edu"] == "Named Person"
    assert by_email["noname@yale.edu"] is None


def test_session_frequency_and_night_counts_search(app):
    db.session.add(YaleStudent(email="findme@yale.edu", name="Findable Person", year="2028"))
    db.session.add(YaleStudent(email="other@yale.edu", name="Other Person", year="2026"))
    _add_scan("findme@yale.edu", BASE)
    _add_scan("other@yale.edu", BASE)
    db.session.commit()

    items, total = analytics.get_session_frequency(search="findable")
    assert total == 1
    assert items[0]["email"] == "findme@yale.edu"

    items, total = analytics.get_session_frequency(search="2028")
    assert total == 1
    assert items[0]["email"] == "findme@yale.edu"

    night_items, night_total = analytics.get_night_counts(search="findme")
    assert night_total == 1
    assert night_items[0]["email"] == "findme@yale.edu"
