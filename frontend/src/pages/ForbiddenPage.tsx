import { Layout } from "../components/Layout";
import { Link } from "react-router-dom";

export function ForbiddenPage() {
  return (
    <Layout showLogout>
      <div className="page-center">
        <div className="card" style={{ maxWidth: 480 }}>
          <h1 className="display-title" style={{ marginTop: 0 }}>
            Restricted Access
          </h1>
          <p>Admin permissions are required to view this page.</p>
          <Link to="/" className="btn btn-primary" style={{ marginTop: "1rem" }}>
            Back to ticket
          </Link>
        </div>
      </div>
    </Layout>
  );
}
