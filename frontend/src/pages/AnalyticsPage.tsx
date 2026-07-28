import { FormEvent, useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { Pager, SortableHeader, buildQuery, formatTimestamp, type Sort } from "../components/SheetControls";
import {
  ApiClientError,
  apiGet,
  apiSend,
  type CategorySummary,
  type NightCountsResponse,
  type ScanCategory,
  type ScanDirectoryResponse,
  type SessionFrequencyResponse,
  type TimeBucketsResponse,
} from "../api/client";
import { ForbiddenPage } from "./ForbiddenPage";

const PAGE_SIZE = 100;

type Tab = "scans" | "sessions" | "nights" | "time";

interface Filters {
  search: string;
  start: string;
  end: string;
  grade: string;
  category: ScanCategory | "";
  sessionGapHours: string;
  minScansInSession: string;
  minNights: string;
  bucketMinutes: string;
}

// bucket_start is a "HH:MM" UTC time-of-day (not a date) -- scans from every
// date in the filtered range collapse into the same 24-hour cycle, so there's
// no calendar date to show here, only the recurring daily window.
function formatBucketRange(hhmm: string | null, bucketMinutes: number): string {
  if (!hhmm) return "—";
  const [hours, minutes] = hhmm.split(":").map(Number);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return hhmm;
  const startMinutes = hours * 60 + minutes;
  const endMinutes = (startMinutes + bucketMinutes) % (24 * 60);
  const fmt = (totalMinutes: number) => {
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    const period = h < 12 ? "AM" : "PM";
    const hour12 = h % 12 === 0 ? 12 : h % 12;
    return `${hour12}:${String(m).padStart(2, "0")} ${period}`;
  };
  return `${fmt(startMinutes)} – ${fmt(endMinutes)} UTC`;
}

const DEFAULT_FILTERS: Filters = {
  search: "",
  start: "",
  end: "",
  grade: "",
  category: "",
  sessionGapHours: "8",
  minScansInSession: "1",
  minNights: "1",
  bucketMinutes: "30",
};

export function AnalyticsPage() {
  const [forbidden, setForbidden] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("scans");

  const [filtersForm, setFiltersForm] = useState<Filters>(DEFAULT_FILTERS);
  const [applied, setApplied] = useState<Filters>(DEFAULT_FILTERS);

  const [summary, setSummary] = useState<CategorySummary | null>(null);

  const [scansSort, setScansSort] = useState<Sort>({ by: "scanned_at", dir: "desc" });
  const [scans, setScans] = useState<ScanDirectoryResponse | null>(null);

  const [sessionSort, setSessionSort] = useState<Sort>({ by: "scans_in_session", dir: "desc" });
  const [sessions, setSessions] = useState<SessionFrequencyResponse | null>(null);

  const [nightSort, setNightSort] = useState<Sort>({ by: "nights", dir: "desc" });
  const [nights, setNights] = useState<NightCountsResponse | null>(null);

  const [timeSort, setTimeSort] = useState<Sort>({ by: "bucket_start", dir: "asc" });
  const [timeBuckets, setTimeBuckets] = useState<TimeBucketsResponse | null>(null);

  const [rowActionError, setRowActionError] = useState<string | null>(null);
  const [rowActionBusy, setRowActionBusy] = useState(false);

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

  const loadSummary = async (filters: Filters) => {
    try {
      const data = await apiGet<CategorySummary>(
        `/api/v1/analytics/scan-summary${buildQuery({
          start: filters.start,
          end: filters.end,
        })}`,
      );
      setSummary(data);
    } catch (err) {
      if (!handleAuthError(err)) setError("Failed to load category summary.");
    }
  };

  const loadScans = async (filters: Filters, opts?: { sort?: Sort; offset?: number }) => {
    const sort = opts?.sort ?? scansSort;
    const offset = opts?.offset ?? scans?.offset ?? 0;
    try {
      const data = await apiGet<ScanDirectoryResponse>(
        `/api/v1/analytics/scans${buildQuery({
          search: filters.search,
          start: filters.start,
          end: filters.end,
          grade: filters.grade,
          category: filters.category,
          sort_by: sort.by,
          sort_dir: sort.dir,
          limit: PAGE_SIZE,
          offset,
        })}`,
      );
      setScansSort(sort);
      setScans(data);
    } catch (err) {
      if (!handleAuthError(err)) setError("Failed to load scanner log.");
    }
  };

  const loadSessions = async (filters: Filters, opts?: { sort?: Sort; offset?: number }) => {
    const sort = opts?.sort ?? sessionSort;
    const offset = opts?.offset ?? sessions?.offset ?? 0;
    try {
      const data = await apiGet<SessionFrequencyResponse>(
        `/api/v1/analytics/session-frequency${buildQuery({
          search: filters.search,
          start: filters.start,
          end: filters.end,
          grade: filters.grade,
          session_gap_hours: filters.sessionGapHours,
          min_scans_in_session: filters.minScansInSession,
          sort_by: sort.by,
          sort_dir: sort.dir,
          limit: PAGE_SIZE,
          offset,
        })}`,
      );
      setSessionSort(sort);
      setSessions(data);
    } catch (err) {
      if (!handleAuthError(err)) setError("Failed to load session frequency.");
    }
  };

  const loadNights = async (filters: Filters, opts?: { sort?: Sort; offset?: number }) => {
    const sort = opts?.sort ?? nightSort;
    const offset = opts?.offset ?? nights?.offset ?? 0;
    try {
      const data = await apiGet<NightCountsResponse>(
        `/api/v1/analytics/night-counts${buildQuery({
          search: filters.search,
          start: filters.start,
          end: filters.end,
          grade: filters.grade,
          session_gap_hours: filters.sessionGapHours,
          min_nights: filters.minNights,
          sort_by: sort.by,
          sort_dir: sort.dir,
          limit: PAGE_SIZE,
          offset,
        })}`,
      );
      setNightSort(sort);
      setNights(data);
    } catch (err) {
      if (!handleAuthError(err)) setError("Failed to load night counts.");
    }
  };

  const loadTimeBuckets = async (filters: Filters, opts?: { sort?: Sort; offset?: number }) => {
    const sort = opts?.sort ?? timeSort;
    const offset = opts?.offset ?? timeBuckets?.offset ?? 0;
    try {
      const data = await apiGet<TimeBucketsResponse>(
        `/api/v1/analytics/time-buckets${buildQuery({
          search: filters.search,
          start: filters.start,
          end: filters.end,
          grade: filters.grade,
          bucket_minutes: filters.bucketMinutes,
          sort_by: sort.by,
          sort_dir: sort.dir,
          limit: PAGE_SIZE,
          offset,
        })}`,
      );
      setTimeSort(sort);
      setTimeBuckets(data);
    } catch (err) {
      if (!handleAuthError(err)) setError("Failed to load time buckets.");
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        await Promise.all([
          loadSummary(DEFAULT_FILTERS),
          loadScans(DEFAULT_FILTERS, { offset: 0 }),
          loadSessions(DEFAULT_FILTERS, { offset: 0 }),
          loadNights(DEFAULT_FILTERS, { offset: 0 }),
          loadTimeBuckets(DEFAULT_FILTERS, { offset: 0 }),
        ]);
      } finally {
        setLoading(false);
      }
    })();
    // Load once on mount with default filters; load* below always read the
    // latest state/args directly, so they don't belong in a dependency array.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applyFilters = async (e: FormEvent) => {
    e.preventDefault();
    setApplied(filtersForm);
    setError(null);
    setLoading(true);
    try {
      await Promise.all([
        loadSummary(filtersForm),
        loadScans(filtersForm, { offset: 0 }),
        loadSessions(filtersForm, { offset: 0 }),
        loadNights(filtersForm, { offset: 0 }),
        loadTimeBuckets(filtersForm, { offset: 0 }),
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSort = (current: Sort, column: string): Sort =>
    current.by === column ? { by: column, dir: current.dir === "asc" ? "desc" : "asc" } : { by: column, dir: "desc" };

  const deleteRow = async (id: number, email: string, scannedAt: string | null) => {
    if (!window.confirm(`Delete scan for ${email} at ${formatTimestamp(scannedAt)}?`)) return;
    setRowActionError(null);
    setRowActionBusy(true);
    try {
      await apiSend(`/api/v1/scans/${id}`, "DELETE");
      await Promise.all([loadScans(applied, { offset: scans?.offset ?? 0 }), loadSummary(applied)]);
    } catch (err) {
      setRowActionError(err instanceof ApiClientError ? err.message : "Failed to delete row.");
    } finally {
      setRowActionBusy(false);
    }
  };

  if (forbidden) return <ForbiddenPage />;

  return (
    <Layout showLogout leftLink={{ to: "/admin", label: "← Admin Panel" }}>
      <div className="sheet-page analytics-fit">
        <div className="sheet-header">
          <div>
            <h1 className="display-title" style={{ margin: 0, fontSize: "1.4rem" }}>
              Scan Analytics
            </h1>
          </div>
          {summary && (
            <div className="sheet-summary">
              <span>
                Yale in directory: <strong>{summary.yale_in_directory}</strong>
              </span>
              <span>
                Yale not in directory: <strong>{summary.yale_not_in_directory}</strong>
              </span>
              <span>
                Non-Yale: <strong>{summary.non_yale}</strong>
              </span>
              <span>
                Total: <strong>{summary.total}</strong>
              </span>
            </div>
          )}
        </div>

        <div className="sheet-tabs">
          <button
            type="button"
            className={`sheet-tab${activeTab === "scans" ? " sheet-tab-active" : ""}`}
            onClick={() => setActiveTab("scans")}
          >
            Scanner Log
          </button>
          <button
            type="button"
            className={`sheet-tab${activeTab === "sessions" ? " sheet-tab-active" : ""}`}
            onClick={() => setActiveTab("sessions")}
          >
            Session Frequency
          </button>
          <button
            type="button"
            className={`sheet-tab${activeTab === "nights" ? " sheet-tab-active" : ""}`}
            onClick={() => setActiveTab("nights")}
          >
            Night Counts
          </button>
          <button
            type="button"
            className={`sheet-tab${activeTab === "time" ? " sheet-tab-active" : ""}`}
            onClick={() => setActiveTab("time")}
          >
            By Time
          </button>
        </div>

        {error && (
          <div className="banner-error" style={{ marginBottom: "0.5rem" }}>
            {error}
          </div>
        )}

        <form className="sheet-toolbar" onSubmit={applyFilters}>
          <div className="sheet-field">
            <label>Search (any column)</label>
            <input
              type="text"
              placeholder="email, name, year, category…"
              value={filtersForm.search}
              onChange={(e) => setFiltersForm((f) => ({ ...f, search: e.target.value }))}
            />
          </div>
          <div className="sheet-field">
            <label>Start (UTC)</label>
            <input
              type="datetime-local"
              value={filtersForm.start}
              onChange={(e) => setFiltersForm((f) => ({ ...f, start: e.target.value }))}
            />
          </div>
          <div className="sheet-field">
            <label>End (UTC)</label>
            <input
              type="datetime-local"
              value={filtersForm.end}
              onChange={(e) => setFiltersForm((f) => ({ ...f, end: e.target.value }))}
            />
          </div>
          <div className="sheet-field">
            <label>Year</label>
            <input
              type="text"
              placeholder="e.g. 2026"
              value={filtersForm.grade}
              onChange={(e) => setFiltersForm((f) => ({ ...f, grade: e.target.value }))}
            />
          </div>
          {activeTab === "scans" && (
            <div className="sheet-field">
              <label>Category</label>
              <select
                value={filtersForm.category}
                onChange={(e) => setFiltersForm((f) => ({ ...f, category: e.target.value as ScanCategory | "" }))}
              >
                <option value="">All</option>
                <option value="yale_in_directory">Yale — in directory</option>
                <option value="yale_not_in_directory">Yale — not in directory</option>
                <option value="non_yale">Non-Yale</option>
              </select>
            </div>
          )}
          {(activeTab === "sessions" || activeTab === "nights") && (
            <div className="sheet-field">
              <label>Session gap (hrs)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={filtersForm.sessionGapHours}
                onChange={(e) => setFiltersForm((f) => ({ ...f, sessionGapHours: e.target.value }))}
              />
            </div>
          )}
          {activeTab === "sessions" && (
            <div className="sheet-field">
              <label>Min scans/session</label>
              <input
                type="number"
                min="1"
                value={filtersForm.minScansInSession}
                onChange={(e) => setFiltersForm((f) => ({ ...f, minScansInSession: e.target.value }))}
              />
            </div>
          )}
          {activeTab === "nights" && (
            <div className="sheet-field">
              <label>Min nights</label>
              <input
                type="number"
                min="1"
                value={filtersForm.minNights}
                onChange={(e) => setFiltersForm((f) => ({ ...f, minNights: e.target.value }))}
              />
            </div>
          )}
          {activeTab === "time" && (
            <div className="sheet-field">
              <label>Bucket size (min)</label>
              <input
                type="number"
                min="1"
                value={filtersForm.bucketMinutes}
                onChange={(e) => setFiltersForm((f) => ({ ...f, bucketMinutes: e.target.value }))}
              />
            </div>
          )}
          <button type="submit" className="btn btn-primary">
            Search
          </button>
        </form>

        {loading ? (
          <p className="loading">Loading…</p>
        ) : (
          <div className="sheet-body">
            {rowActionError && (
              <div className="banner-error" style={{ marginBottom: "0.5rem" }}>
                {rowActionError}
              </div>
            )}

            {activeTab === "scans" && (
              <>
                <div className="sheet-grid-wrap">
                  <table className="sheet-table">
                    <thead>
                      <tr>
                        <SortableHeader width="20%" label="Email" column="email" sort={scansSort} onSort={(c) => loadScans(applied, { sort: toggleSort(scansSort, c), offset: 0 })} />
                        <SortableHeader width="17%" label="Name" column="name" sort={scansSort} onSort={(c) => loadScans(applied, { sort: toggleSort(scansSort, c), offset: 0 })} />
                        <SortableHeader width="16%" label="Scanned At" column="scanned_at" sort={scansSort} onSort={(c) => loadScans(applied, { sort: toggleSort(scansSort, c), offset: 0 })} />
                        <SortableHeader width="8%" label="Year" column="grade" sort={scansSort} onSort={(c) => loadScans(applied, { sort: toggleSort(scansSort, c), offset: 0 })} />
                        <SortableHeader width="16%" label="Category" column="category" sort={scansSort} onSort={(c) => loadScans(applied, { sort: toggleSort(scansSort, c), offset: 0 })} />
                        <th className="sheet-cell-actions" style={{ width: "56px" }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {!scans || scans.items.length === 0 ? (
                        <tr>
                          <td colSpan={6} style={{ color: "var(--text-muted)" }}>
                            No scans.
                          </td>
                        </tr>
                      ) : (
                        scans.items.map((row) => (
                          <tr key={row.id}>
                            <td title={row.email}>{row.email}</td>
                            <td title={row.name ?? ""}>{row.name ?? "—"}</td>
                            <td title={formatTimestamp(row.scanned_at)}>{formatTimestamp(row.scanned_at)}</td>
                            <td>{row.grade ?? "—"}</td>
                            <td>{row.category}</td>
                            <td className="sheet-cell-actions">
                              <button
                                type="button"
                                className="sheet-x-btn"
                                disabled={rowActionBusy}
                                title="Delete this scan"
                                onClick={() => deleteRow(row.id, row.email, row.scanned_at)}
                              >
                                ×
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {scans && (
                  <Pager
                    offset={scans.offset}
                    limit={scans.limit}
                    total={scans.total}
                    onPage={(offset) => loadScans(applied, { offset })}
                  />
                )}
              </>
            )}

            {activeTab === "sessions" && (
              <>
                <div className="sheet-grid-wrap">
                  <table className="sheet-table">
                    <thead>
                      <tr>
                        <SortableHeader width="18%" label="Email" column="email" sort={sessionSort} onSort={(c) => loadSessions(applied, { sort: toggleSort(sessionSort, c), offset: 0 })} />
                        <SortableHeader width="16%" label="Name" column="name" sort={sessionSort} onSort={(c) => loadSessions(applied, { sort: toggleSort(sessionSort, c), offset: 0 })} />
                        <SortableHeader width="8%" label="Year" column="grade" sort={sessionSort} onSort={(c) => loadSessions(applied, { sort: toggleSort(sessionSort, c), offset: 0 })} />
                        <SortableHeader width="16%" label="Scans in Session" column="scans_in_session" sort={sessionSort} onSort={(c) => loadSessions(applied, { sort: toggleSort(sessionSort, c), offset: 0 })} />
                        <SortableHeader width="21%" label="First Scan" column="session_start" sort={sessionSort} onSort={(c) => loadSessions(applied, { sort: toggleSort(sessionSort, c), offset: 0 })} />
                        <SortableHeader width="21%" label="Last Scan" column="session_end" sort={sessionSort} onSort={(c) => loadSessions(applied, { sort: toggleSort(sessionSort, c), offset: 0 })} />
                      </tr>
                    </thead>
                    <tbody>
                      {!sessions || sessions.items.length === 0 ? (
                        <tr>
                          <td colSpan={6} style={{ color: "var(--text-muted)" }}>
                            No sessions.
                          </td>
                        </tr>
                      ) : (
                        sessions.items.map((row, i) => (
                          <tr key={`${row.email}-${i}`}>
                            <td title={row.email}>{row.email}</td>
                            <td title={row.name ?? ""}>{row.name ?? "—"}</td>
                            <td>{row.grade ?? "—"}</td>
                            <td>{row.scans_in_session}</td>
                            <td title={formatTimestamp(row.session_start)}>{formatTimestamp(row.session_start)}</td>
                            <td title={formatTimestamp(row.session_end)}>{formatTimestamp(row.session_end)}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                {sessions && (
                  <Pager
                    offset={sessions.offset}
                    limit={sessions.limit}
                    total={sessions.total}
                    onPage={(offset) => loadSessions(applied, { offset })}
                  />
                )}
              </>
            )}

            {activeTab === "nights" && (
              <>
                <div className="sheet-grid-wrap">
                  <table className="sheet-table">
                    <thead>
                      <tr>
                        <SortableHeader width="22%" label="Email" column="email" sort={nightSort} onSort={(c) => loadNights(applied, { sort: toggleSort(nightSort, c), offset: 0 })} />
                        <SortableHeader width="19%" label="Name" column="name" sort={nightSort} onSort={(c) => loadNights(applied, { sort: toggleSort(nightSort, c), offset: 0 })} />
                        <SortableHeader width="9%" label="Year" column="grade" sort={nightSort} onSort={(c) => loadNights(applied, { sort: toggleSort(nightSort, c), offset: 0 })} />
                        <SortableHeader width="25%" label="Nights" column="nights" sort={nightSort} onSort={(c) => loadNights(applied, { sort: toggleSort(nightSort, c), offset: 0 })} />
                        <SortableHeader width="25%" label="Total Scans" column="total_scans" sort={nightSort} onSort={(c) => loadNights(applied, { sort: toggleSort(nightSort, c), offset: 0 })} />
                      </tr>
                    </thead>
                    <tbody>
                      {!nights || nights.items.length === 0 ? (
                        <tr>
                          <td colSpan={5} style={{ color: "var(--text-muted)" }}>
                            No data.
                          </td>
                        </tr>
                      ) : (
                        nights.items.map((row, i) => (
                          <tr key={`${row.email}-${i}`}>
                            <td title={row.email}>{row.email}</td>
                            <td title={row.name ?? ""}>{row.name ?? "—"}</td>
                            <td>{row.grade ?? "—"}</td>
                            <td>{row.nights}</td>
                            <td>{row.total_scans}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                {nights && (
                  <Pager
                    offset={nights.offset}
                    limit={nights.limit}
                    total={nights.total}
                    onPage={(offset) => loadNights(applied, { offset })}
                  />
                )}
              </>
            )}

            {activeTab === "time" && (
              <>
                <div className="sheet-grid-wrap">
                  <table className="sheet-table">
                    <thead>
                      <tr>
                        <SortableHeader width="70%" label="Time of Day (UTC)" column="bucket_start" sort={timeSort} onSort={(c) => loadTimeBuckets(applied, { sort: toggleSort(timeSort, c), offset: 0 })} />
                        <SortableHeader width="30%" label="Scans" column="scans" sort={timeSort} onSort={(c) => loadTimeBuckets(applied, { sort: toggleSort(timeSort, c), offset: 0 })} />
                      </tr>
                    </thead>
                    <tbody>
                      {!timeBuckets || timeBuckets.items.length === 0 ? (
                        <tr>
                          <td colSpan={2} style={{ color: "var(--text-muted)" }}>
                            No data.
                          </td>
                        </tr>
                      ) : (
                        (() => {
                          const maxScans = Math.max(...timeBuckets.items.map((row) => row.scans), 1);
                          const bucketMinutes = Number(applied.bucketMinutes) || 30;
                          return timeBuckets.items.map((row, i) => (
                            <tr key={`${row.bucket_start}-${i}`}>
                              <td title={row.bucket_start ?? ""}>
                                {formatBucketRange(row.bucket_start, bucketMinutes)}
                              </td>
                              <td>
                                <div className="sheet-bar-cell">
                                  <div className="sheet-bar" style={{ width: `${(row.scans / maxScans) * 100}%` }} />
                                  <span className="sheet-bar-label">{row.scans}</span>
                                </div>
                              </td>
                            </tr>
                          ));
                        })()
                      )}
                    </tbody>
                  </table>
                </div>
                {timeBuckets && (
                  <Pager
                    offset={timeBuckets.offset}
                    limit={timeBuckets.limit}
                    total={timeBuckets.total}
                    onPage={(offset) => loadTimeBuckets(applied, { offset })}
                  />
                )}
              </>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
