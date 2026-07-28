"""Scan log analytics.

Three kinds of reporting over ``scan_logs``, joined against ``yale_students``
on a case-insensitive email match:

- ``get_category_summary`` / ``list_scans_with_directory`` use the ordinary
  ``db.session.query`` style used elsewhere in ``app/services`` — they don't
  need anything SQL can't express through the ORM.
- ``get_session_frequency`` / ``get_night_counts`` sessionize scans with a
  gaps-and-islands pattern (a run of scans for one person becomes a single
  "session"/"night" as long as no gap between consecutive scans exceeds
  ``session_gap_hours``). That needs LAG() and a running SUM() OVER a window,
  which the ORM query builder can't express, so those two run hand-written
  SQL through ``text()``.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import case, func, text

from app.extensions import db
from app.models import ScanLog, YaleStudent

DEFAULT_SESSION_GAP_HOURS = 8

CATEGORY_YALE_IN_DIRECTORY = "yale_in_directory"
CATEGORY_YALE_NOT_IN_DIRECTORY = "yale_not_in_directory"
CATEGORY_NON_YALE = "non_yale"
CATEGORIES = frozenset(
    {CATEGORY_YALE_IN_DIRECTORY, CATEGORY_YALE_NOT_IN_DIRECTORY, CATEGORY_NON_YALE}
)

_LISTING_SORT_COLUMNS = frozenset({"scanned_at", "email", "name", "grade", "category"})
_SESSION_FREQUENCY_SORT_COLUMNS = {
    "email": "s.email",
    "name": "name",
    "grade": "grade",
    "scans_in_session": "s.scans_in_session",
    "session_start": "s.session_start",
    "session_end": "s.session_end",
}
_NIGHT_COUNT_SORT_COLUMNS = {
    "email": "p.email",
    "name": "name",
    "grade": "grade",
    "nights": "p.nights",
    "total_scans": "p.total_scans",
}
_TIME_BUCKET_SORT_COLUMNS = frozenset({"bucket_start", "scans"})
DEFAULT_BUCKET_MINUTES = 30


def _validate_sort_dir(sort_dir: str) -> str:
    if sort_dir not in ("asc", "desc"):
        raise ValueError("sort_dir must be 'asc' or 'desc'")
    return sort_dir


def _day_range(day: date) -> tuple[datetime, datetime]:
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def _apply_time_range(query, column, *, day: date | None, start: datetime | None, end: datetime | None):
    if day is not None:
        day_start, day_end = _day_range(day)
        query = query.filter(column >= day_start, column < day_end)
    if start is not None:
        query = query.filter(column >= start)
    if end is not None:
        query = query.filter(column <= end)
    return query


def _is_yale_email(column):
    """True if column, lowercased, ends in @yale.edu."""
    return func.lower(column).like("%@yale.edu")


def _directory_join(query):
    """Left join scan_logs -> yale_students, matching emails case-insensitively."""
    return query.outerjoin(
        YaleStudent, func.lower(YaleStudent.email) == func.lower(ScanLog.email)
    )


def get_category_summary(
    *,
    day: date | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict:
    """Count scans in three buckets: yale_in_directory, yale_not_in_directory, non_yale."""
    is_yale = _is_yale_email(ScanLog.email)
    in_directory = YaleStudent.email.isnot(None)

    query = db.session.query(
        func.count(ScanLog.id).filter(is_yale & in_directory).label("yale_in_directory"),
        func.count(ScanLog.id).filter(is_yale & ~in_directory).label("yale_not_in_directory"),
        func.count(ScanLog.id).filter(~is_yale).label("non_yale"),
    ).select_from(ScanLog)
    query = _directory_join(query)
    query = _apply_time_range(query, ScanLog.scanned_at, day=day, start=start, end=end)

    yale_in_directory, yale_not_in_directory, non_yale = query.one()
    yale_in_directory = yale_in_directory or 0
    yale_not_in_directory = yale_not_in_directory or 0
    non_yale = non_yale or 0
    return {
        "yale_in_directory": yale_in_directory,
        "yale_not_in_directory": yale_not_in_directory,
        "non_yale": non_yale,
        "total": yale_in_directory + yale_not_in_directory + non_yale,
    }


def list_scans_with_directory(
    *,
    grade: str | None = None,
    day: date | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "scanned_at",
    sort_dir: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Filtered, sorted, paginated scan_logs rows joined to yale_students."""
    if category is not None and category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}")
    if sort_by not in _LISTING_SORT_COLUMNS:
        raise ValueError(f"Unknown sort_by: {sort_by}")
    _validate_sort_dir(sort_dir)

    is_yale = _is_yale_email(ScanLog.email)
    in_directory = YaleStudent.email.isnot(None)
    category_expr = case(
        (is_yale & in_directory, CATEGORY_YALE_IN_DIRECTORY),
        (is_yale, CATEGORY_YALE_NOT_IN_DIRECTORY),
        else_=CATEGORY_NON_YALE,
    ).label("category")

    query = db.session.query(
        ScanLog.id,
        ScanLog.email,
        ScanLog.scanned_at,
        YaleStudent.name.label("name"),
        YaleStudent.year.label("grade"),
        category_expr,
    ).select_from(ScanLog)
    query = _directory_join(query)
    query = _apply_time_range(query, ScanLog.scanned_at, day=day, start=start, end=end)

    if grade is not None:
        query = query.filter(YaleStudent.year == grade)
    if category == CATEGORY_YALE_IN_DIRECTORY:
        query = query.filter(is_yale, in_directory)
    elif category == CATEGORY_YALE_NOT_IN_DIRECTORY:
        query = query.filter(is_yale, ~in_directory)
    elif category == CATEGORY_NON_YALE:
        query = query.filter(~is_yale)

    search = (search or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            ScanLog.email.ilike(pattern)
            | YaleStudent.name.ilike(pattern)
            | YaleStudent.year.ilike(pattern)
            | category_expr.ilike(pattern)
        )

    total = query.count()

    sort_columns = {
        "scanned_at": ScanLog.scanned_at,
        "email": ScanLog.email,
        "name": YaleStudent.name,
        "grade": YaleStudent.year,
        "category": category_expr,
    }
    sort_column = sort_columns[sort_by]
    query = query.order_by(sort_column.asc() if sort_dir == "asc" else sort_column.desc())

    rows = query.offset(offset).limit(limit).all()
    items = [
        {
            "id": row.id,
            "email": row.email,
            "name": row.name,
            "scanned_at": row.scanned_at.isoformat() if row.scanned_at else None,
            "grade": row.grade,
            "category": row.category,
        }
        for row in rows
    ]
    return items, total


def _seconds_since_prev_sql(dialect_name: str) -> str:
    """SQL fragment computing seconds between scanned_at and prev_scanned_at.

    Postgres has EXTRACT(EPOCH FROM interval); SQLite has neither EXTRACT nor
    an interval type, but strftime('%s', ...) gives integer Unix seconds for
    both operands, and since the two timestamps in a comparison always share
    the same sub-second offset when the gap is a whole number of seconds, the
    per-operand truncation cancels out in the subtraction.
    """
    if dialect_name == "sqlite":
        return (
            "(CAST(strftime('%s', scanned_at) AS FLOAT) - "
            "CAST(strftime('%s', prev_scanned_at) AS FLOAT))"
        )
    return "EXTRACT(EPOCH FROM (scanned_at - prev_scanned_at))"


def _sessionized_cte_sql(dialect_name: str) -> str:
    """CTE chain implementing gaps-and-islands sessionization.

    ``sessioned`` ends up with one row per scan, tagged with a session_number
    that increments each time the gap since that person's previous scan
    exceeds the configured threshold (LAG + a running SUM of the "new
    session" flag, per email, ordered by scanned_at with id as a tiebreaker
    for scans sharing an identical timestamp).
    """
    seconds_since_prev = _seconds_since_prev_sql(dialect_name)
    return f"""
    filtered_scans AS (
        SELECT id, email, scanned_at
        FROM scan_logs
        WHERE (:start IS NULL OR scanned_at >= :start)
          AND (:end IS NULL OR scanned_at <= :end)
    ),
    ordered AS (
        SELECT
            id,
            email,
            scanned_at,
            LAG(scanned_at) OVER (PARTITION BY email ORDER BY scanned_at, id) AS prev_scanned_at
        FROM filtered_scans
    ),
    flagged AS (
        SELECT
            id,
            email,
            scanned_at,
            CASE
                WHEN prev_scanned_at IS NULL THEN 1
                WHEN {seconds_since_prev} > :gap_seconds THEN 1
                ELSE 0
            END AS new_session_flag
        FROM ordered
    ),
    sessioned AS (
        SELECT
            id,
            email,
            scanned_at,
            SUM(new_session_flag) OVER (
                PARTITION BY email ORDER BY scanned_at, id
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS session_number
        FROM flagged
    )
    """


def _format_timestamp(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def get_session_frequency(
    *,
    grade: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    search: str | None = None,
    session_gap_hours: float = DEFAULT_SESSION_GAP_HOURS,
    min_scans_in_session: int = 1,
    sort_by: str = "scans_in_session",
    sort_dir: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """How many times each person was scanned within a single session.

    One row per (person, session) — a person with several qualifying
    sessions appears once per session, not once overall (see
    get_night_counts for the per-person total). Use min_scans_in_session to
    surface people scanned unusually often in one visit.
    """
    if sort_by not in _SESSION_FREQUENCY_SORT_COLUMNS:
        raise ValueError(f"Unknown sort_by: {sort_by}")
    _validate_sort_dir(sort_dir)

    dialect_name = db.engine.dialect.name
    cte_sql = _sessionized_cte_sql(dialect_name)
    order_sql = f"{_SESSION_FREQUENCY_SORT_COLUMNS[sort_by]} {'ASC' if sort_dir == 'asc' else 'DESC'}"

    search = (search or "").strip()
    params = {
        "start": start,
        "end": end,
        "gap_seconds": float(session_gap_hours) * 3600.0,
        "min_scans_in_session": min_scans_in_session,
        "grade": grade,
        "search": search or None,
        "search_pattern": f"%{search}%",
        "limit": limit,
        "offset": offset,
    }

    base_sql = f"""
    WITH {cte_sql},
    sessions AS (
        SELECT
            email,
            session_number,
            COUNT(*) AS scans_in_session,
            MIN(scanned_at) AS session_start,
            MAX(scanned_at) AS session_end
        FROM sessioned
        GROUP BY email, session_number
    )
    SELECT
        s.email AS email,
        s.session_number AS session_number,
        s.scans_in_session AS scans_in_session,
        s.session_start AS session_start,
        s.session_end AS session_end,
        ys.year AS grade,
        ys.name AS name
    FROM sessions s
    LEFT JOIN yale_students ys ON LOWER(ys.email) = LOWER(s.email)
    WHERE s.scans_in_session >= :min_scans_in_session
      AND (:grade IS NULL OR ys.year = :grade)
      AND (
        :search IS NULL
        OR LOWER(s.email) LIKE LOWER(:search_pattern)
        OR LOWER(ys.name) LIKE LOWER(:search_pattern)
        OR LOWER(ys.year) LIKE LOWER(:search_pattern)
      )
    """

    total = db.session.execute(text(f"SELECT COUNT(*) FROM ({base_sql}) AS sub"), params).scalar_one()
    rows = db.session.execute(
        text(f"{base_sql} ORDER BY {order_sql} LIMIT :limit OFFSET :offset"), params
    ).mappings().all()

    items = [
        {
            "email": row["email"],
            "name": row["name"],
            "grade": row["grade"],
            "scans_in_session": row["scans_in_session"],
            "session_start": _format_timestamp(row["session_start"]),
            "session_end": _format_timestamp(row["session_end"]),
        }
        for row in rows
    ]
    return items, total


def get_night_counts(
    *,
    grade: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    search: str | None = None,
    session_gap_hours: float = DEFAULT_SESSION_GAP_HOURS,
    min_nights: int = 1,
    sort_by: str = "nights",
    sort_dir: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """How many distinct sessions ("nights") each person attended, plus total scans."""
    if sort_by not in _NIGHT_COUNT_SORT_COLUMNS:
        raise ValueError(f"Unknown sort_by: {sort_by}")
    _validate_sort_dir(sort_dir)

    dialect_name = db.engine.dialect.name
    cte_sql = _sessionized_cte_sql(dialect_name)
    order_sql = f"{_NIGHT_COUNT_SORT_COLUMNS[sort_by]} {'ASC' if sort_dir == 'asc' else 'DESC'}"

    search = (search or "").strip()
    params = {
        "start": start,
        "end": end,
        "gap_seconds": float(session_gap_hours) * 3600.0,
        "min_nights": min_nights,
        "grade": grade,
        "search": search or None,
        "search_pattern": f"%{search}%",
        "limit": limit,
        "offset": offset,
    }

    base_sql = f"""
    WITH {cte_sql},
    per_person AS (
        SELECT
            email,
            COUNT(DISTINCT session_number) AS nights,
            COUNT(*) AS total_scans
        FROM sessioned
        GROUP BY email
    )
    SELECT
        p.email AS email,
        p.nights AS nights,
        p.total_scans AS total_scans,
        ys.year AS grade,
        ys.name AS name
    FROM per_person p
    LEFT JOIN yale_students ys ON LOWER(ys.email) = LOWER(p.email)
    WHERE p.nights >= :min_nights
      AND (:grade IS NULL OR ys.year = :grade)
      AND (
        :search IS NULL
        OR LOWER(p.email) LIKE LOWER(:search_pattern)
        OR LOWER(ys.name) LIKE LOWER(:search_pattern)
        OR LOWER(ys.year) LIKE LOWER(:search_pattern)
      )
    """

    total = db.session.execute(text(f"SELECT COUNT(*) FROM ({base_sql}) AS sub"), params).scalar_one()
    rows = db.session.execute(
        text(f"{base_sql} ORDER BY {order_sql} LIMIT :limit OFFSET :offset"), params
    ).mappings().all()

    items = [
        {
            "email": row["email"],
            "name": row["name"],
            "grade": row["grade"],
            "nights": row["nights"],
            "total_scans": row["total_scans"],
        }
        for row in rows
    ]
    return items, total


SECONDS_PER_DAY = 24 * 60 * 60


def _format_time_of_day(seconds_of_day: int) -> str:
    hours, remainder = divmod(seconds_of_day, 3600)
    minutes = remainder // 60
    return f"{hours:02d}:{minutes:02d}"


def get_time_buckets(
    *,
    grade: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    search: str | None = None,
    bucket_minutes: int = DEFAULT_BUCKET_MINUTES,
    sort_by: str = "bucket_start",
    sort_dir: str = "asc",
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Scan counts grouped by time-of-day (UTC), collapsing across dates.

    Every scan within [start, end] is assigned to one of the fixed 24-hour
    cycle of bucket_minutes-sized windows (e.g. 00:00-00:30, 00:30-01:00, ...,
    23:30-00:00) based on its UTC time-of-day, regardless of which calendar
    date it actually fell on. All buckets in the cycle are always present
    (zero-filled), so this is a "what time of day do people usually show up"
    profile, not a per-date timeline.
    """
    if sort_by not in _TIME_BUCKET_SORT_COLUMNS:
        raise ValueError(f"Unknown sort_by: {sort_by}")
    _validate_sort_dir(sort_dir)
    if bucket_minutes <= 0 or SECONDS_PER_DAY % (bucket_minutes * 60) != 0:
        raise ValueError("bucket_minutes must be positive and divide evenly into 24 hours")
    bucket_seconds = bucket_minutes * 60

    query = db.session.query(ScanLog.scanned_at).select_from(ScanLog)
    query = _directory_join(query)
    query = _apply_time_range(query, ScanLog.scanned_at, day=None, start=start, end=end)
    if grade is not None:
        query = query.filter(YaleStudent.year == grade)

    search = (search or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            ScanLog.email.ilike(pattern)
            | YaleStudent.name.ilike(pattern)
            | YaleStudent.year.ilike(pattern)
        )

    timestamps = [row[0] for row in query.all() if row[0] is not None]

    num_buckets = SECONDS_PER_DAY // bucket_seconds
    counts = [0] * num_buckets
    for ts in timestamps:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_utc = ts.astimezone(timezone.utc)
        seconds_of_day = ts_utc.hour * 3600 + ts_utc.minute * 60 + ts_utc.second
        counts[seconds_of_day // bucket_seconds] += 1

    items_all = [
        {"bucket_start": _format_time_of_day(i * bucket_seconds), "scans": counts[i]}
        for i in range(num_buckets)
    ]

    reverse = sort_dir == "desc"
    sort_key = "scans" if sort_by == "scans" else "bucket_start"
    items_all.sort(key=lambda item: item[sort_key], reverse=reverse)

    total = len(items_all)
    items = items_all[offset : offset + limit]
    return items, total
