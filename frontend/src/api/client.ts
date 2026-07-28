export interface ApiError {
  error?: { code?: string; message?: string };
}

export class ApiClientError extends Error {
  status: number;
  code?: string;
  extras?: Record<string, unknown>;

  constructor(
    status: number,
    message: string,
    code?: string,
    extras?: Record<string, unknown>,
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.extras = extras;
  }
}

async function parseJson<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const payload = data as ApiError & Record<string, unknown>;
    const { error, ...extras } = payload;
    throw new ApiClientError(
      response.status,
      error?.message || response.statusText,
      error?.code,
      Object.keys(extras).length ? extras : undefined,
    );
  }
  return data as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(path, { credentials: "include" });
  return parseJson<T>(response);
}

export async function apiSend<T>(
  path: string,
  method: string,
  body?: unknown,
  headers: Record<string, string> = {},
): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parseJson<T>(response);
}

export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(path, {
    method: "PUT",
    credentials: "include",
    body: form,
  });
  return parseJson<T>(response);
}

export type WatermarkPreset = "none" | "leo" | "rugby" | "ink" | "custom";
export type StampPreset = "yale_bowl" | "sterling" | "leo" | "rugby" | "ink" | "custom";

export interface TicketResponse {
  title: string;
  email: string;
  qr_payload: string;
  qr_code_base64: string;
  postcard_enabled: boolean;
  postcard_stamp_preset: StampPreset;
  watermark_preset: WatermarkPreset;
  has_custom_watermark: boolean;
}

export interface MeResponse {
  email: string;
  roles: string[];
  is_attendee?: boolean;
}

export interface EventSettings {
  title: string;
  image_visible: boolean;
  has_custom_watermark: boolean;
  watermark_preset: WatermarkPreset;
  contact_email: string;
  default_theme: "light" | "dark";
  postcard_enabled: boolean;
  postcard_stamp_preset: StampPreset;
}

export interface ScanResult {
  status: string;
  email: string;
  name: string;
  image_url: string;
  duplicate?: boolean;
}

export interface ScannerBootstrap {
  scanner_api_key: string;
}

export type ScanCategory = "yale_in_directory" | "yale_not_in_directory" | "non_yale";

export interface CategorySummary {
  yale_in_directory: number;
  yale_not_in_directory: number;
  non_yale: number;
  total: number;
}

export interface ScanDirectoryItem {
  id: number;
  email: string;
  name: string | null;
  scanned_at: string | null;
  grade: string | null;
  category: ScanCategory;
}

export interface ScanDirectoryResponse {
  items: ScanDirectoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface SessionFrequencyItem {
  email: string;
  name: string | null;
  grade: string | null;
  scans_in_session: number;
  session_start: string | null;
  session_end: string | null;
}

export interface SessionFrequencyResponse {
  items: SessionFrequencyItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface NightCountItem {
  email: string;
  name: string | null;
  grade: string | null;
  nights: number;
  total_scans: number;
}

export interface NightCountsResponse {
  items: NightCountItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface TimeBucketItem {
  bucket_start: string | null;
  scans: number;
}

export interface TimeBucketsResponse {
  items: TimeBucketItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface YaleStudentsTableResponse {
  columns: string[];
  items: Record<string, string | number | boolean | null>[];
  total: number;
  limit: number;
  offset: number;
}
