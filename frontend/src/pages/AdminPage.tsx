import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import {
  ApiClientError,
  apiGet,
  apiSend,
  apiUpload,
  type EventSettings,
  type StampPreset,
  type WatermarkPreset,
} from "../api/client";
import { ForbiddenPage } from "./ForbiddenPage";
import leoLogo from "../assets/leo-logo.png";
import rugbyLogo from "../assets/rugby-150-logo.png";
import inkLogo from "../assets/ink-logo.png";
import { useTheme } from "../theme/ThemeContext";

const PRESET_LOGOS = {
  leo: leoLogo,
  rugby: rugbyLogo,
  ink: inkLogo,
} as const;

const LOGO_PRESETS: { id: WatermarkPreset; label: string }[] = [
  { id: "none", label: "Default" },
  { id: "leo", label: "LEO" },
  { id: "rugby", label: "Rugby" },
  { id: "ink", label: "Ink & Needle" },
];

const STAMP_PRESETS: { id: StampPreset; label: string }[] = [
  { id: "yale_bowl", label: "Yale Bowl" },
  { id: "sterling", label: "Sterling" },
  { id: "leo", label: "LEO" },
  { id: "rugby", label: "Rugby" },
  { id: "ink", label: "Ink & Needle" },
  { id: "custom", label: "Custom" },
];

export function AdminPage() {
  const { applySiteDefault } = useTheme();
  const [allowed, setAllowed] = useState("");
  const [blacklist, setBlacklist] = useState("");
  const [title, setTitle] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [imageVisible, setImageVisible] = useState(true);
  const [hasCustomWatermark, setHasCustomWatermark] = useState(false);
  const [watermarkPreset, setWatermarkPreset] = useState<WatermarkPreset>("none");
  const [defaultTheme, setDefaultTheme] = useState<"light" | "dark">("light");
  const [postcardEnabled, setPostcardEnabled] = useState(false);
  const [postcardStampPreset, setPostcardStampPreset] = useState<StampPreset>("sterling");
  const [watermarkPreviewKey, setWatermarkPreviewKey] = useState(0);
  const [saved, setSaved] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [event, emails, blocked] = await Promise.all([
        apiGet<EventSettings>("/api/v1/event"),
        apiGet<{ emails: string[] }>("/api/v1/allowed-emails"),
        apiGet<{ emails: string[] }>("/api/v1/blacklisted-emails"),
      ]);
      setTitle(event.title);
      setContactEmail(event.contact_email);
      setImageVisible(event.image_visible);
      setHasCustomWatermark(event.has_custom_watermark);
      setWatermarkPreset(event.watermark_preset ?? "none");
      setDefaultTheme(event.default_theme === "dark" ? "dark" : "light");
      setPostcardEnabled(event.postcard_enabled);
      setPostcardStampPreset(event.postcard_stamp_preset ?? "sterling");
      setAllowed(emails.emails.join("\n"));
      setBlacklist(blocked.emails.join("\n"));
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 401) {
          window.location.href = "/google/login";
          return;
        }
        if (err.status === 403) setForbidden(true);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const flash = (msg: string) => {
    setSaved(msg);
    window.setTimeout(() => setSaved(null), 3500);
  };

  const saveEmails = async (e: FormEvent) => {
    e.preventDefault();
    const emails = allowed.split("\n").map((l) => l.trim()).filter(Boolean);
    await apiSend("/api/v1/allowed-emails", "PUT", { emails });
    flash("Guest list updated.");
  };

  const saveTitle = async (e: FormEvent) => {
    e.preventDefault();
    await apiSend("/api/v1/event", "PATCH", { title: title.trim() });
    flash("Ticket title updated.");
  };

  const saveContactEmail = async (e: FormEvent) => {
    e.preventDefault();
    await apiSend("/api/v1/event", "PATCH", {
      contact_email: contactEmail.trim(),
    });
    flash("Contact email updated.");
  };

  const saveBlacklist = async (e: FormEvent) => {
    e.preventDefault();
    const emails = blacklist.split("\n").map((l) => l.trim()).filter(Boolean);
    await apiSend("/api/v1/blacklisted-emails", "PUT", { emails });
    setAllowed((prev) =>
      prev
        .split("\n")
        .filter((line) => !emails.includes(line.trim().toLowerCase()))
        .join("\n"),
    );
    flash("Blacklist updated.");
  };

  const toggleImage = async () => {
    const next = !imageVisible;
    const event = await apiSend<EventSettings>("/api/v1/event", "PATCH", {
      image_visible: next,
    });
    setImageVisible(event.image_visible);
  };

  const togglePostcard = async () => {
    try {
      const next = !postcardEnabled;
      const event = await apiSend<EventSettings>("/api/v1/event", "PATCH", {
        postcard_enabled: next,
      });
      setPostcardEnabled(event.postcard_enabled);
      flash(`Postcard ticket ${event.postcard_enabled ? "enabled" : "disabled"}.`);
    } catch (err) {
      flash(err instanceof ApiClientError ? err.message : "Failed to update postcard setting.");
    }
  };

  const toggleDefaultTheme = async () => {
    const next = defaultTheme === "light" ? "dark" : "light";
    const event = await apiSend<EventSettings>("/api/v1/event", "PATCH", {
      default_theme: next,
    });
    const savedTheme = event.default_theme === "dark" ? "dark" : "light";
    setDefaultTheme(savedTheme);
    applySiteDefault(savedTheme);
    flash(`Default theme set to ${savedTheme}.`);
  };

  const onWatermarkUpload = async (file: File | undefined) => {
    if (!file) return;
    try {
      const event = await apiUpload<EventSettings>("/api/v1/event/watermark", file);
      setHasCustomWatermark(event.has_custom_watermark);
      setWatermarkPreset(event.watermark_preset);
      setWatermarkPreviewKey((k) => k + 1);
      flash("Custom logo uploaded.");
    } catch (err) {
      flash(err instanceof ApiClientError ? err.message : "Upload failed.");
    }
  };

  const selectStampPreset = async (preset: StampPreset) => {
    try {
      const event = await apiSend<EventSettings>("/api/v1/event", "PATCH", {
        postcard_stamp_preset: preset,
      });
      setPostcardStampPreset(event.postcard_stamp_preset);
      const label = STAMP_PRESETS.find((item) => item.id === preset)?.label ?? preset;
      flash(`${label} stamp selected.`);
    } catch (err) {
      flash(err instanceof ApiClientError ? err.message : "Failed to update stamp preset.");
    }
  };

  const selectLogoPreset = async (preset: WatermarkPreset) => {
    if (preset === "custom") return;
    try {
      const event = await apiSend<EventSettings>("/api/v1/event", "PATCH", {
        watermark_preset: preset,
      });
      setWatermarkPreset(event.watermark_preset);
      setHasCustomWatermark(event.has_custom_watermark);
      setWatermarkPreviewKey((k) => k + 1);
      const label = LOGO_PRESETS.find((item) => item.id === preset)?.label ?? preset;
      flash(`${label} logo selected.`);
    } catch (err) {
      flash(err instanceof ApiClientError ? err.message : "Failed to update logo preset.");
    }
  };

  const previewLogoSrc = hasCustomWatermark
    ? `/api/v1/event/watermark?k=${watermarkPreviewKey}`
    : watermarkPreset === "leo" || watermarkPreset === "rugby" || watermarkPreset === "ink"
      ? PRESET_LOGOS[watermarkPreset]
      : null;

  const activeLogoPreset = hasCustomWatermark ? null : watermarkPreset;

  if (loading) {
    return (
      <Layout showLogout>
        <div className="page-center loading">Loading admin panel…</div>
      </Layout>
    );
  }

  if (forbidden) return <ForbiddenPage />;

  return (
    <Layout showLogout>
      <div className="page-content">
        <h1 className="display-title" style={{ marginBottom: "0.25rem" }}>
          Admin Panel
        </h1>
        <p style={{ color: "var(--text-muted)", marginTop: 0 }}>
          Manage guest list, blacklist, and event settings.
        </p>

        {saved && <div className="banner-success">{saved}</div>}

        <div className="grid-2" style={{ marginTop: "1.5rem" }}>
          <div>
            <form className="card" onSubmit={saveEmails} style={{ marginBottom: "1rem" }}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Guest List</h2>
              <p className="form-hint">One email per line. These users can receive a ticket.</p>
              <textarea rows={8} value={allowed} onChange={(e) => setAllowed(e.target.value)} required />
              <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.5rem" }}>
                Save Guest List
              </button>
            </form>

            <form className="card" onSubmit={saveTitle} style={{ marginBottom: "1rem" }}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Ticket Title</h2>
              <p className="form-hint">Shown on the ticket page (e.g. LEO Spring Fling).</p>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required />
              <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.75rem" }}>
                Save Ticket Title
              </button>
            </form>

            <form className="card" onSubmit={saveContactEmail} style={{ marginBottom: "1rem" }}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Contact Email</h2>
              <p className="form-hint">
                Shown on the restricted access page for guests not on the list.
              </p>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                required
              />
              <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.75rem" }}>
                Save Contact Email
              </button>
            </form>

            <form className="card" onSubmit={saveBlacklist}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Blacklist</h2>
              <p className="form-hint">
                Blocked users see the same message as guests not on the list. Saving removes them from the guest list.
              </p>
              <textarea rows={8} value={blacklist} onChange={(e) => setBlacklist(e.target.value)} />
              <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.5rem" }}>
                Save Blacklist
              </button>
            </form>
          </div>

          <div>
            <div className="card" style={{ marginBottom: "1rem" }}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Views</h2>
              <div className="link-list">
                <Link to="/admin/display">View Guest List</Link>
                <Link to="/admin/blacklist/display">View Blacklist</Link>
                <Link to="/admin/log">View Scanner Log</Link>
                <Link to="/">Preview Ticket</Link>
                <Link to="/scanner">Open Scanner</Link>
              </div>
            </div>

            <div className="card" style={{ marginBottom: "1rem" }}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Logo</h2>
              <p className="form-hint">PNG/JPEG/WebP, max 512 KB.</p>
              <div className="watermark-preview">
                {previewLogoSrc ? (
                  <img src={previewLogoSrc} alt="Logo preview" />
                ) : null}
              </div>
              <div className="admin-stamp-layout" style={{ marginTop: "0.75rem" }}>
                <div className="admin-stamp-row">
                  <span className="admin-stamp-label">Presets:</span>
                  <div className="admin-stamp-buttons">
                    {LOGO_PRESETS.slice(0, 3).map(({ id, label }) => (
                      <button
                        key={id}
                        type="button"
                        className={`btn btn-secondary btn-preset${activeLogoPreset === id ? " btn-preset-active" : ""}`}
                        onClick={() => selectLogoPreset(id)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="admin-stamp-row">
                  <span className="admin-stamp-label admin-stamp-label-spacer" aria-hidden="true">
                    Presets:
                  </span>
                  <div className="admin-stamp-buttons">
                    {LOGO_PRESETS.slice(3).map(({ id, label }) => (
                      <button
                        key={id}
                        type="button"
                        className={`btn btn-secondary btn-preset${activeLogoPreset === id ? " btn-preset-active" : ""}`}
                        onClick={() => selectLogoPreset(id)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="admin-file-row">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(e) => {
                    onWatermarkUpload(e.target.files?.[0]);
                    e.target.value = "";
                  }}
                />
              </div>
            </div>

            <div className="card" style={{ marginBottom: "1rem" }}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Postcard Ticket</h2>
              <p className="form-hint">Vertical postcard layout.</p>
              <button
                type="button"
                className="btn btn-primary"
                style={{ width: "100%" }}
                onClick={togglePostcard}
              >
                Enable Postcard
              </button>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "0.75rem" }}>
                Postcard mode: <strong>{postcardEnabled ? "On" : "Off"}</strong>
              </p>

              {postcardEnabled && (
                <>
                  <h3 style={{ marginTop: "1rem", fontSize: "1rem" }}>Stamp</h3>
                  <div className="admin-stamp-layout">
                    <div className="admin-stamp-row">
                      <span className="admin-stamp-label">Presets:</span>
                      <div className="admin-stamp-buttons">
                        {STAMP_PRESETS.slice(0, 3).map(({ id, label }) => (
                          <button
                            key={id}
                            type="button"
                            className={`btn btn-secondary btn-preset${postcardStampPreset === id ? " btn-preset-active" : ""}`}
                            onClick={() => selectStampPreset(id)}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="admin-stamp-row">
                      <span className="admin-stamp-label admin-stamp-label-spacer" aria-hidden="true">
                        Presets:
                      </span>
                      <div className="admin-stamp-buttons">
                        {STAMP_PRESETS.slice(3).map(({ id, label }) => (
                          <button
                            key={id}
                            type="button"
                            className={`btn btn-secondary btn-preset${postcardStampPreset === id ? " btn-preset-active" : ""}`}
                            onClick={() => selectStampPreset(id)}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="card" style={{ marginBottom: "1rem" }}>
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Appearance</h2>
              <p className="form-hint">Default theme for all users on page load.</p>
              <button
                type="button"
                className="btn btn-primary"
                style={{ width: "100%" }}
                onClick={toggleDefaultTheme}
              >
                Switch Default to {defaultTheme === "light" ? "Dark" : "Light"} Mode
              </button>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "0.75rem" }}>
                Site default: <strong>{defaultTheme === "light" ? "Light" : "Dark"}</strong>
              </p>
            </div>

            <div className="card">
              <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Scanner</h2>
              <button type="button" className="btn btn-primary" style={{ width: "100%" }} onClick={toggleImage}>
                Toggle Yalies Image
              </button>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "0.75rem" }}>
                Yalies image visible: <strong>{imageVisible ? "Yes" : "No"}</strong>
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
