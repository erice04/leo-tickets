"""Read-only Yale directory browser for admins.

Deliberately scoped to just yale_students -- no other tables are exposed
here. updated_at is dropped since it's internal bookkeeping, not directory
data worth showing.
"""
from sqlalchemy import func, select

from app.extensions import db
from app.models import YaleStudent

_EXCLUDED_COLUMNS = frozenset({"updated_at"})


def _columns() -> list[str]:
    return [c.name for c in YaleStudent.__table__.columns if c.name not in _EXCLUDED_COLUMNS]


def browse_yale_students(
    *,
    search: str | None = None,
    sort_by: str | None = None,
    sort_dir: str = "asc",
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[str], list[dict], int]:
    columns = _columns()

    sort_by = sort_by or columns[0]
    if sort_by not in columns:
        raise ValueError(f"Unknown column: {sort_by}")
    if sort_dir not in ("asc", "desc"):
        raise ValueError("sort_dir must be 'asc' or 'desc'")

    table = YaleStudent.__table__
    order_column = table.c[sort_by]
    order = order_column.asc() if sort_dir == "asc" else order_column.desc()

    query = select(*(table.c[name] for name in columns))
    count_query = select(func.count()).select_from(table)

    search = (search or "").strip()
    if search:
        pattern = f"%{search}%"
        condition = (
            table.c.email.ilike(pattern)
            | table.c.name.ilike(pattern)
            | table.c.netid.ilike(pattern)
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.session.execute(count_query).scalar_one()
    rows = (
        db.session.execute(query.order_by(order).limit(limit).offset(offset)).mappings().all()
    )
    items = [dict(row) for row in rows]
    return columns, items, total
