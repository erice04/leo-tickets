import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import { Layout } from "../components/Layout";
import {
  ApiClientError,
  apiGet,
  apiSend,
  type ScanResult,
  type ScannerBootstrap,
} from "../api/client";

type CornerState = "detected" | "error" | null;

const DEDUP_MS = 60_000;

function scanBoxSize(viewfinderWidth: number, viewfinderHeight: number) {
  // Leave >=11px margin on each side so html5-qrcode draws corner markers.
  const maxSide = Math.min(viewfinderWidth, viewfinderHeight) - 22;
  const side = Math.min(250, Math.max(120, Math.floor(maxSide * 0.85)));
  return { width: side, height: side };
}

export function ScannerPage() {
  const [name, setName] = useState("—");
  const [email, setEmail] = useState("—");
  const [status, setStatus] = useState("");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [cornerState, setCornerState] = useState<CornerState>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const apiKeyRef = useRef("");
  const lastScanRef = useRef({ payload: "", at: 0 });
  const inFlightRef = useRef(false);
  const cornerClearTimerRef = useRef<number | null>(null);

  const holdCornerState = (state: CornerState, ms: number) => {
    setCornerState(state);
    if (cornerClearTimerRef.current) {
      window.clearTimeout(cornerClearTimerRef.current);
    }
    cornerClearTimerRef.current = window.setTimeout(() => {
      setCornerState(null);
      cornerClearTimerRef.current = null;
    }, ms);
  };

  useEffect(() => {
    let scanner: Html5Qrcode | null = null;
    let mounted = true;

    (async () => {
      try {
        const boot = await apiGet<ScannerBootstrap>("/api/v1/scanner/bootstrap");
        apiKeyRef.current = boot.scanner_api_key || "";
      } catch {
        /* session auth may still work */
      }

      scanner = new Html5Qrcode("qr-reader", { verbose: false });
      const onScan = async (decodedText: string) => {
        const now = Date.now();
        if (inFlightRef.current) return;
        if (
          decodedText === lastScanRef.current.payload &&
          now - lastScanRef.current.at < DEDUP_MS
        ) {
          return;
        }

        inFlightRef.current = true;

        const headers: Record<string, string> = {};
        if (apiKeyRef.current) headers["X-API-Key"] = apiKeyRef.current;

        try {
          const body = await apiSend<ScanResult>(
            "/scanner_result",
            "POST",
            { data: decodedText },
            headers,
          );
          lastScanRef.current = { payload: decodedText, at: Date.now() };
          setName(body.name || "N/A");
          setEmail(body.email || "—");
          setImageUrl(body.image_url || null);
          setStatus(body.duplicate ? "(already scanned recently)" : "");
          holdCornerState("detected", 1000);
        } catch (err) {
          holdCornerState("error", 1000);
          const msg =
            err instanceof ApiClientError ? err.message : "Network error";
          setStatus(msg);
        } finally {
          inFlightRef.current = false;
        }
      };

      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: scanBoxSize },
        onScan,
        () => {
          if (cornerClearTimerRef.current !== null) return;
          setCornerState(null);
        },
      );
    })().catch(() => {
      if (mounted) setCameraError("Camera unavailable — allow access and reload.");
    });

    return () => {
      mounted = false;
      if (cornerClearTimerRef.current) {
        window.clearTimeout(cornerClearTimerRef.current);
      }
      if (scanner?.isScanning) {
        scanner.stop().catch(() => undefined);
      }
    };
  }, []);

  return (
    <Layout leftLink={{ to: "/", label: "Ticket" }}>
      <div className="page-center">
        <h2 className="display-title" style={{ marginBottom: "0.5rem" }}>
          Ticket Scanner
        </h2>
        <div
          className={`reader-container${cornerState ? ` scan-${cornerState}` : ""}`}
        >
          <div id="qr-reader" />
        </div>
        {cameraError && <div className="banner-error">{cameraError}</div>}
        <div className="card" style={{ maxWidth: 400, width: "100%", marginTop: "0.5rem" }}>
          <p style={{ margin: "0.35rem 0" }}>
            <strong>Name:</strong> {name}
          </p>
          <p style={{ margin: "0.35rem 0" }}>
            <strong>Email:</strong> {email}
          </p>
          {status && (
            <p style={{ margin: "0.5rem 0 0", color: "var(--text-muted)", fontSize: "0.9rem" }}>
              {status}
            </p>
          )}
          {imageUrl && (
            <img
              src={imageUrl}
              alt="Guest"
              style={{
                marginTop: "1rem",
                maxWidth: 220,
                maxHeight: 280,
                borderRadius: 10,
                border: "1px solid var(--border)",
              }}
            />
          )}
        </div>
      </div>
    </Layout>
  );
}
