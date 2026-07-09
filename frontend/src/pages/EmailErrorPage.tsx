import { Layout } from "../components/Layout";

interface EmailErrorPageProps {
  email: string;
  contactEmail: string;
}

export function EmailErrorPage({ email, contactEmail }: EmailErrorPageProps) {
  return (
    <Layout showLogout>
      <div className="page-center">
        <div className="card" style={{ maxWidth: 560 }}>
          <h1 className="display-title" style={{ fontSize: "1.5rem", marginTop: 0 }}>
            Restricted Access
          </h1>
          <p style={{ fontSize: "1.1rem", lineHeight: 1.6 }}>
            <strong>{email}</strong> is not on the guest list.
          </p>
          <p style={{ color: "var(--text-muted)" }}>
            Please use your Yale email, or contact{" "}
            <a href={`mailto:${contactEmail}`}>{contactEmail}</a>.
          </p>
        </div>
      </div>
    </Layout>
  );
}
