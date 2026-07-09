import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { ApiClientError, apiGet, type ScansResponse } from "../api/client";
import { ForbiddenPage } from "./ForbiddenPage";

export function DisplayLogPage() {
  const [items, setItems] = useState<ScansResponse["items"]>([]);
  const [forbidden, setForbidden] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<ScansResponse>("/api/v1/scans?limit=500")
      .then((data) => setItems(data.items))
      .catch((err) => {
        if (err instanceof ApiClientError && err.status === 403) setForbidden(true);
      })
      .finally(() => setLoading(false));
  }, []);

  if (forbidden) return <ForbiddenPage />;

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  return (
    <Layout showLogout>
      <div className="page-content">
        <Link to="/admin" className="btn btn-secondary" style={{ marginBottom: "1rem" }}>
          ← Admin Panel
        </Link>
        <h1 className="display-title">Scanner Log</h1>
        {loading ? (
          <p className="loading">Loading…</p>
        ) : (
          <div className="table-wrap card" style={{ padding: 0, overflow: "hidden" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Scanned At</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={2} style={{ color: "var(--text-muted)" }}>
                      No scans yet.
                    </td>
                  </tr>
                ) : (
                  items.map((row) => (
                    <tr key={row.id}>
                      <td>{row.email}</td>
                      <td>{formatTime(row.scanned_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
