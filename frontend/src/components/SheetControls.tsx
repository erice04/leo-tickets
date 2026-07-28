export type SortDir = "asc" | "desc";
export type Sort = { by: string; dir: SortDir };

export function buildQuery(params: Record<string, string | number | undefined>): string {
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    usp.set(key, String(value));
  }
  const qs = usp.toString();
  return qs ? `?${qs}` : "";
}

export function formatTimestamp(iso: string | null): string {
  if (!iso) return "—";
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime()) ? iso : parsed.toLocaleString();
}

export function SortableHeader({
  label,
  column,
  sort,
  onSort,
  width,
}: {
  label: string;
  column: string;
  sort: Sort;
  onSort: (column: string) => void;
  width?: string;
}) {
  const active = sort.by === column;
  return (
    <th onClick={() => onSort(column)} style={width ? { width } : undefined}>
      {label}
      <span className="sheet-sort-arrow">{active ? (sort.dir === "asc" ? "▲" : "▼") : ""}</span>
    </th>
  );
}

export function Pager({
  offset,
  limit,
  total,
  onPage,
}: {
  offset: number;
  limit: number;
  total: number;
  onPage: (offset: number) => void;
}) {
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));
  return (
    <div className="sheet-footer">
      <button
        type="button"
        className="btn btn-secondary"
        disabled={offset <= 0}
        onClick={() => onPage(Math.max(0, offset - limit))}
      >
        ← Prev
      </button>
      <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
        Page {page} of {pages} ({total} total)
      </span>
      <button
        type="button"
        className="btn btn-secondary"
        disabled={offset + limit >= total}
        onClick={() => onPage(offset + limit)}
      >
        Next →
      </button>
    </div>
  );
}
