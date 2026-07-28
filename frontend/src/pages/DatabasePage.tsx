import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { Pager, SortableHeader, buildQuery, type Sort } from "../components/SheetControls";
import { ApiClientError, apiGet, type YaleStudentsTableResponse } from "../api/client";
import { ForbiddenPage } from "./ForbiddenPage";

const PAGE_SIZE = 100;

const COLUMN_WIDTHS: Record<string, string> = {
  email: "18%",
  name: "15%",
  image_url: "17%",
  year: "7%",
  netid: "9%",
  birthday: "9%",
  major: "11%",
  address: "14%",
};

function formatCell(value: string | number | boolean | null): string {
  if (value === null) return "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}

export function DatabasePage() {
  const [forbidden, setForbidden] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<Sort>({ by: "", dir: "asc" });
  const [rows, setRows] = useState<YaleStudentsTableResponse | null>(null);
  const [searchForm, setSearchForm] = useState("");
  const [search, setSearch] = useState("");

  const handleAuthError = (err: unknown): boolean => {
    if (err instanceof ApiClientError) {
      if (err.status === 401) {
        window.location.href = "/google/login";
        return true;
      }
      if (err.status === 403) {
        setForbidden(true);
        return true;
      }
    }
    return false;
  };

  const loadRows = async (opts?: { sort?: Sort; offset?: number; search?: string }) => {
    const nextSort = opts?.sort ?? sort;
    const offset = opts?.offset ?? rows?.offset ?? 0;
    const nextSearch = opts?.search ?? search;
    try {
      const data = await apiGet<YaleStudentsTableResponse>(
        `/api/v1/database/yale-students${buildQuery({
          search: nextSearch || undefined,
          sort_by: nextSort.by || undefined,
          sort_dir: nextSort.dir,
          limit: PAGE_SIZE,
          offset,
        })}`,
      );
      setSort({ by: nextSort.by || data.columns[0], dir: nextSort.dir });
      setRows(data);
    } catch (err) {
      if (!handleAuthError(err)) setError("Failed to load Yale students.");
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        await loadRows({ offset: 0 });
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleSort = (column: string): Sort =>
    sort.by === column ? { by: column, dir: sort.dir === "asc" ? "desc" : "asc" } : { by: column, dir: "asc" };

  const runSearch = async (e: FormEvent) => {
    e.preventDefault();
    setSearch(searchForm);
    await loadRows({ offset: 0, search: searchForm });
  };

  if (forbidden) return <ForbiddenPage />;

  return (
    <Layout showLogout>
      <div className="sheet-page">
        <div className="sheet-header">
          <div>
            <Link to="/admin" className="btn btn-secondary" style={{ marginBottom: "0.5rem" }}>
              ← Admin Panel
            </Link>
            <h1 className="display-title" style={{ margin: "0.25rem 0 0" }}>
              Yale Students
            </h1>
          </div>
        </div>

        {error && (
          <div className="banner-error" style={{ marginBottom: "0.5rem" }}>
            {error}
          </div>
        )}

        <form className="sheet-toolbar" onSubmit={runSearch}>
          <div className="sheet-field">
            <label>Lookup (email, name, or NetID)</label>
            <input
              type="text"
              placeholder="e.g. jsmith or Jane Smith"
              value={searchForm}
              onChange={(e) => setSearchForm(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary">
            Search
          </button>
          {search && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setSearchForm("");
                setSearch("");
                loadRows({ offset: 0, search: "" });
              }}
            >
              Clear
            </button>
          )}
        </form>

        {loading ? (
          <p className="loading">Loading…</p>
        ) : (
          <>
            <div className="sheet-grid-wrap">
              <table className="sheet-table">
                <thead>
                  <tr>
                    {rows?.columns.map((col) => (
                      <SortableHeader
                        key={col}
                        label={col}
                        column={col}
                        sort={sort}
                        onSort={(c) => loadRows({ sort: toggleSort(c), offset: 0 })}
                        width={COLUMN_WIDTHS[col]}
                      />
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {!rows || rows.items.length === 0 ? (
                    <tr>
                      <td colSpan={rows?.columns.length || 1} style={{ color: "var(--text-muted)" }}>
                        No rows.
                      </td>
                    </tr>
                  ) : (
                    rows.items.map((row, i) => (
                      <tr key={i}>
                        {rows.columns.map((col) => (
                          <td key={col} title={formatCell(row[col])}>
                            {formatCell(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            {rows && (
              <Pager
                offset={rows.offset}
                limit={rows.limit}
                total={rows.total}
                onPage={(offset) => loadRows({ offset })}
              />
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
