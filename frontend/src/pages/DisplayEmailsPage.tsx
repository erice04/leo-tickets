import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { ApiClientError, apiGet } from "../api/client";
import { ForbiddenPage } from "./ForbiddenPage";

interface DisplayEmailsPageProps {
  mode: "guest" | "blacklist";
}

export function DisplayEmailsPage({ mode }: DisplayEmailsPageProps) {
  const [lines, setLines] = useState<string[]>([]);
  const [forbidden, setForbidden] = useState(false);
  const [loading, setLoading] = useState(true);

  const heading = mode === "guest" ? "Guest List" : "Blacklist";
  const path =
    mode === "guest" ? "/api/v1/allowed-emails" : "/api/v1/blacklisted-emails";

  useEffect(() => {
    apiGet<{ emails: string[] }>(path)
      .then((data) => setLines(data.emails))
      .catch((err) => {
        if (err instanceof ApiClientError && err.status === 403) setForbidden(true);
      })
      .finally(() => setLoading(false));
  }, [path]);

  if (forbidden) return <ForbiddenPage />;

  return (
    <Layout showLogout>
      <div className="page-content">
        <Link to="/admin" className="btn btn-secondary" style={{ marginBottom: "1rem" }}>
          ← Admin Panel
        </Link>
        <h1 className="display-title">{heading}</h1>
        {loading ? (
          <p className="loading">Loading…</p>
        ) : (
          <div className="card">
            {lines.length === 0 ? (
              <p style={{ color: "var(--text-muted)", margin: 0 }}>(empty)</p>
            ) : (
              <pre
                style={{
                  margin: 0,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  fontFamily: "inherit",
                  lineHeight: 1.6,
                }}
              >
                {lines.join("\n")}
              </pre>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
